"""Live /api/scan path tests with a fake transport client (no network).

Covers F1 server behaviour: image scans fan out one call per concept,
concepts are filtered to the frozen v1 set, the CallBudget pre-flight
refuses before any provider call, transport failures become an honest
live_scan_failed response, and the server-side minimum interval blocks
back-to-back scans without spending.
"""
from __future__ import annotations

import base64
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import server
from config import CallBudget, reset_custom_hazards
from sam_client import Detection

JPEG_BYTES = b"\xff\xd8\xff\xe0fake-jpeg-payload"


class FakeClient:
    """Stands in for RealSAMClient: spends 1 budget unit per request."""

    def __init__(self, budget: CallBudget, fail_keys=()):
        self.budget = budget
        self.fail_keys = set(fail_keys)
        self.calls: list[str] = []

    def segment_request(self, request):
        key = request.prompts[0].key
        self.calls.append(key)
        self.budget.spend(1)
        if key in self.fail_keys:
            raise RuntimeError(f"boom:{key}")
        if key == "snake":
            return [Detection(
                concept="snake", frame_idx=request.frame_idx, confidence=None,
                distance_m=0.8, clock_direction=12, track_id="snake-0",
                bbox=[0.1, 0.4, 0.5, 0.55],
            )]
        return []


def make_scanner(tmpdir: str, cap: int = 50, fail_keys=(), **kwargs):
    budget = CallBudget(daily_cap=cap, counter_path=Path(tmpdir) / "c.json")
    client = FakeClient(budget, fail_keys=fail_keys)
    scanner = server.LiveScanner(client, budget, **kwargs)
    return scanner, client, budget


class LiveScannerTests(unittest.TestCase):
    def test_image_scan_returns_detection_alert_and_latency(self):
        with tempfile.TemporaryDirectory() as tmp:
            scanner, client, budget = make_scanner(tmp)
            result = scanner.scan(JPEG_BYTES, "image/jpeg", ["snake"])
            self.assertEqual(result["mode"], "live")
            self.assertIn("latency_ms", result)
            self.assertEqual(len(result["detections"]), 1)
            det = result["detections"][0]
            self.assertEqual(det["concept"], "snake")
            self.assertEqual(det["label_ko"], "뱀")
            self.assertIsNone(det["confidence"])  # SAM returns no confidence
            self.assertIsNotNone(result["alert"])
            self.assertEqual(result["alert"]["text_ko"], "발 앞 1미터, 뱀")
            self.assertEqual(budget.used_today(), 1)  # one concept = one call
            self.assertEqual(result["calls_today"], 1)

    def test_concepts_filtered_to_v1_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            scanner, client, _ = make_scanner(tmp)
            result = scanner.scan(
                JPEG_BYTES, "image/jpeg", ["snake", "ufo", "bear", 42]
            )
            self.assertEqual(sorted(client.calls), ["bear", "snake"])
            self.assertNotIn("error", result)
            self.assertEqual(
                [d["concept"] for d in result["detections"]], ["snake"]
            )

    def test_default_concepts_cover_all_six(self):
        with tempfile.TemporaryDirectory() as tmp:
            scanner, client, budget = make_scanner(tmp)
            scanner.scan(JPEG_BYTES, "image/jpeg", None)
            self.assertEqual(len(client.calls), 6)
            self.assertEqual(budget.used_today(), 6)

    def test_budget_preflight_refuses_without_any_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            scanner, client, _ = make_scanner(tmp, cap=1)
            result = scanner.scan(JPEG_BYTES, "image/jpeg", ["snake", "bear"])
            self.assertEqual(result["error"], "daily_call_cap_reached")
            self.assertEqual(client.calls, [])  # nothing was sent
            self.assertEqual(result["detections"], [])
            self.assertIsNone(result["alert"])

    def test_transport_failure_is_honest_error_not_fake_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            scanner, _, _ = make_scanner(tmp, fail_keys={"snake"})
            result = scanner.scan(JPEG_BYTES, "image/jpeg", ["snake"])
            self.assertEqual(result["error"], "live_scan_failed")
            self.assertIn("boom:snake", result["detail"])
            self.assertEqual(result["detections"], [])
            self.assertIsNone(result["alert"])

    def test_partial_failure_still_returns_successful_concepts(self):
        with tempfile.TemporaryDirectory() as tmp:
            scanner, _, _ = make_scanner(tmp, fail_keys={"bear"})
            result = scanner.scan(JPEG_BYTES, "image/jpeg", ["snake", "bear"])
            self.assertNotIn("error", result)
            self.assertEqual(len(result["detections"]), 1)
            self.assertEqual(len(result["partial_errors"]), 1)
            self.assertIn("bear", result["partial_errors"][0])

    def test_min_interval_blocks_second_scan_without_spending(self):
        with tempfile.TemporaryDirectory() as tmp:
            scanner, client, budget = make_scanner(tmp, min_interval_s=60.0)
            first = scanner.scan(JPEG_BYTES, "image/jpeg", ["snake"])
            self.assertNotIn("error", first)
            second = scanner.scan(JPEG_BYTES, "image/jpeg", ["snake"])
            self.assertEqual(second["error"], "scan_too_soon")
            self.assertGreater(second["retry_after_ms"], 0)
            self.assertEqual(client.calls, ["snake"])  # no second call
            self.assertEqual(budget.used_today(), 1)

    def test_pure_sam_detection_gets_light_sam_tint_mask(self):
        # Per-concept SAM path (no vision_fn): even when the transport
        # returns no pixel mask, the UI payload must carry a tintable
        # SAM 3.1 mask so the judged area is light-filled on screen.
        with tempfile.TemporaryDirectory() as tmp:
            scanner, _, _ = make_scanner(tmp)
            result = scanner.scan(JPEG_BYTES, "image/jpeg", ["snake"])
            det = result["detections"][0]
            self.assertEqual(det["segmentation"], "sam-3.1")
            self.assertEqual(det["mask_source"], "bbox-contour")
            self.assertTrue(det["mask_png"].startswith("data:image/png;base64,"))
            self.assertEqual(det["mask_rect"], [0.1, 0.4, 0.5, 0.55])

    def test_no_valid_concepts(self):
        with tempfile.TemporaryDirectory() as tmp:
            scanner, client, _ = make_scanner(tmp)
            result = scanner.scan(JPEG_BYTES, "image/jpeg", ["ufo"])
            self.assertEqual(result["error"], "no_valid_concepts")
            self.assertEqual(client.calls, [])

    def test_single_pass_vision_router_model_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            budget = CallBudget(daily_cap=50, counter_path=Path(tmp) / "c.json")
            client = FakeClient(budget)
            called_models: list[str] = []

            def fake_vision(image_bytes, media_type, keys, *, frame_idx, model_id):
                called_models.append(model_id)
                det = Detection(
                    concept="bear",
                    frame_idx=frame_idx,
                    confidence=0.97,
                    distance_m=1.6,
                    clock_direction=12,
                    track_id="bear-0",
                    bbox=[0.2, 0.25, 0.5, 0.55],
                )
                return [det], {"bear-0": "불곰 체형·얼굴 확인"}

            scanner = server.LiveScanner(
                client, budget, min_interval_s=0.0, vision_fn=fake_vision
            )
            res = scanner.scan(
                JPEG_BYTES,
                "image/jpeg",
                ["bear", "snake"],
                model="muse-spark-1.3",
            )
            self.assertEqual(res["model"], "muse-spark-1.3")
            self.assertEqual(called_models, ["muse-spark-1.3"])
            self.assertEqual(budget.used_today(), 1)
            self.assertEqual(len(res["detections"]), 1)
            self.assertEqual(res["detections"][0]["concept"], "bear")
            self.assertEqual(res["detections"][0]["label_en"], "Bear")
            self.assertEqual(res["detections"][0]["label_ja"], "クマ")
            self.assertEqual(res["detections"][0]["label_ko"], "곰")
            self.assertEqual(res["detections"][0]["verify_ko"], "불곰 체형·얼굴 확인")
            self.assertIsNotNone(res["alert"])
            self.assertEqual(res["alert"]["text_en"], "Ahead, 2 meters, Bear")
            self.assertEqual(res["alert"]["text_ja"], "前方 2メートル、クマ")
            self.assertEqual(res["alert"]["text_ko"], "전방 2미터, 곰")
            # Muse-only route: no SAM mask may be fabricated for it.
            self.assertNotIn("mask_png", res["detections"][0])
            self.assertNotIn("segmentation", res["detections"][0])

    def test_single_pass_sam_hybrid_gets_sam_tint_mask(self):
        with tempfile.TemporaryDirectory() as tmp:
            budget = CallBudget(daily_cap=50, counter_path=Path(tmp) / "c.json")
            client = FakeClient(budget)

            def fake_vision(image_bytes, media_type, keys, *, frame_idx, model_id):
                return [Detection(
                    concept="snake", frame_idx=frame_idx, confidence=0.9,
                    distance_m=1.2, clock_direction=12, track_id="snake-0",
                    bbox=[0.2, 0.3, 0.4, 0.4],
                )], {}

            scanner = server.LiveScanner(
                client, budget, min_interval_s=0.0, vision_fn=fake_vision
            )
            res = scanner.scan(
                JPEG_BYTES, "image/jpeg", ["snake"], model="sam-3.1-hybrid"
            )
            det = res["detections"][0]
            self.assertEqual(det["segmentation"], "sam-3.1")
            self.assertTrue(det["mask_png"].startswith("data:image/png;base64,"))
            self.assertEqual(det["mask_rect"], [0.2, 0.3, 0.4, 0.4])


class SamMaskTintTests(unittest.TestCase):
    def test_synthesized_sam_mask_is_light_not_opaque(self):
        from vision_router import synthesize_contour_mask_png

        mask_png, mask_rect = synthesize_contour_mask_png([0.1, 0.2, 0.5, 0.5], 3)
        self.assertEqual(mask_rect, [0.1, 0.2, 0.5, 0.5])
        raw = base64.b64decode(mask_png.split(",", 1)[1])
        idat = b""
        pos = 8
        width = height = None
        while pos < len(raw):
            (length,) = struct.unpack(">I", raw[pos:pos + 4])
            tag, data = raw[pos + 4:pos + 8], raw[pos + 8:pos + 8 + length]
            if tag == b"IHDR":
                width, height = struct.unpack(">II", data[:8])
            elif tag == b"IDAT":
                idat += data
            pos += 12 + length
        pixels = zlib.decompress(idat)
        stride = 1 + width * 4
        alphas = [
            pixels[row * stride + 1 + x * 4 + 3]
            for row in range(height) for x in range(width)
        ]
        self.assertGreater(max(alphas), 0)
        self.assertLessEqual(max(alphas), 92)  # light tint, never opaque


class DataUrlTests(unittest.TestCase):
    def test_roundtrip(self):
        url = "data:image/jpeg;base64," + base64.b64encode(JPEG_BYTES).decode()
        data, media_type = server.decode_image_data_url(url)
        self.assertEqual(data, JPEG_BYTES)
        self.assertEqual(media_type, "image/jpeg")

    def test_rejects_non_image_and_garbage(self):
        with self.assertRaises(ValueError):
            server.decode_image_data_url("data:text/html;base64,AAAA")
        with self.assertRaises(ValueError):
            server.decode_image_data_url("not-a-data-url")
        with self.assertRaises(ValueError):
            server.decode_image_data_url({"not": "a string"})


class FilterConceptsTests(unittest.TestCase):
    def test_order_follows_config(self):
        self.assertEqual(
            server.filter_concepts(["boar", "snake"]), ["snake", "boar"]
        )

    def test_empty_means_all(self):
        self.assertEqual(len(server.filter_concepts([])), 6)
        self.assertEqual(len(server.filter_concepts(None)), 6)


class CustomConceptTests(unittest.TestCase):
    def tearDown(self):
        reset_custom_hazards()

    def test_add_concept_registers_zero_retraining_hazard(self):
        payload, code = server.add_concept({"name_ko": "쓰러진 나무"})
        self.assertEqual(code, 200)
        self.assertEqual(payload["added"]["label"], "Fallen tree")
        self.assertEqual(payload["added"]["label_en"], "Fallen tree")
        self.assertEqual(payload["added"]["label_ko"], "쓰러진 나무")
        self.assertEqual(payload["added"]["label_ja"], "倒木")
        self.assertEqual(
            payload["added"]["prompt"], "a fallen tree or log blocking the trail"
        )
        self.assertEqual(len(payload["hazards"]), 7)
        self.assertIn(payload["added"]["key"], server.filter_concepts(None))

    def test_add_concept_from_english_populates_all_three_languages(self):
        payload, code = server.add_concept({"name": "Fallen tree", "lang": "en"})
        self.assertEqual(code, 200)
        self.assertEqual(payload["added"]["label_en"], "Fallen tree")
        self.assertEqual(payload["added"]["label_ko"], "쓰러진 나무")
        self.assertEqual(payload["added"]["label_ja"], "倒木")

    def test_default_language_is_english_with_ko_and_ja_supported(self):
        st = server.status()
        self.assertEqual(st["default_lang"], "en")
        self.assertEqual(st["supported_langs"], ["en", "ko", "ja"])
        self.assertEqual(st["hazards"][0]["label"], "Snake")

    def test_add_concept_rejects_empty_name(self):
        payload, code = server.add_concept({"name_ko": "   "})
        self.assertEqual(code, 400)
        self.assertEqual(payload["error"], "bad_concept")


if __name__ == "__main__":
    unittest.main()
