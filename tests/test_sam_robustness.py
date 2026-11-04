"""Regression tests: one bad SAM/model record must never lose the frame.

Root causes covered (each used to fail the whole scan, so a judged
snake/bear got no tint at all):

- the single-pass bridge caps output at 160 tokens, so multi-hazard
  frames can end mid-JSON; fences/prose also broke strict ``json.loads``
- one malformed / NaN ``box_2d`` raised and discarded valid detections
- a transport drop was masked as a misleading ``HTTP 0`` error
- the pure-SAM stream parser died on the first malformed record, and
  inverted boxes produced negative w/h bboxes that paint no tint
- a malformed mask_rect killed an otherwise valid RealSAMClient detection
- the HUD dropped every late mask decode (generation guard), so unique
  per-scan SAM masks never tinted the screen
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import meta_transport
import vision_router
from config import CallBudget
from meta_transport import (
    _BuiltinHelperParser,
    normalize_record,
    records_from_helper_output,
)
from sam_client import RealSAMClient

SNAKE = {"concept": "snake", "confidence": 0.9, "distance_m": 1.5,
         "box_2d": [400, 100, 700, 600], "verify_ko": "snake"}
BEAR = {"concept": "bear", "confidence": 0.95, "distance_m": 2.0,
        "box_2d": [100, 500, 600, 950], "verify_ko": "bear"}


class _Resp:
    status = 200

    def __init__(self, body: bytes):
        self._body = body

    def read(self) -> bytes:
        return self._body


class _Conn:
    def __init__(self, text: str | None = None, exc: Exception | None = None):
        self._text, self._exc = text, exc

    def request(self, *args, **kwargs):
        if self._exc is not None:
            raise self._exc

    def getresponse(self):
        body = json.dumps(
            {"candidates": [{"content": {"parts": [{"text": self._text}]}}]}
        ).encode()
        return _Resp(body)


def scan(text: str | None = None, exc: Exception | None = None):
    with mock.patch.object(vision_router, "get_adc_access_token", lambda: "t"), \
            mock.patch.object(vision_router, "get_gcp_project_id", lambda: "p"), \
            mock.patch.object(
                vision_router, "_get_https_connection", lambda: _Conn(text, exc)
            ), \
            mock.patch.object(vision_router, "_reset_https_connection", lambda: None):
        return vision_router.scan_with_vertex_vision(
            b"img", "image/jpeg", ["snake", "bear"],
            frame_idx=1, model_id="sam-3.1-hybrid",
        )


class VisionSalvageTests(unittest.TestCase):
    def test_truncated_json_keeps_complete_bear_drops_cut_tail(self):
        full = json.dumps({"detections": [BEAR, SNAKE]})
        dets, _ = scan(full[:-30])  # 160-token cap cut the tail object
        self.assertEqual([d.concept for d in dets], ["bear"])
        self.assertTrue(dets[0].mask_png.startswith("data:image/png;base64,"))
        self.assertEqual(dets[0].mask_rect, dets[0].bbox)

    def test_truncated_after_two_complete_keeps_both(self):
        text = json.dumps({"detections": [BEAR, SNAKE]}) + ""
        cut = text[: text.rfind("}")]  # drop only the final closing brace
        dets, _ = scan(cut)
        self.assertEqual({d.concept for d in dets}, {"bear", "snake"})
        self.assertTrue(all(d.mask_png for d in dets))

    def test_fenced_json_parses(self):
        dets, _ = scan("```json\n" + json.dumps({"detections": [BEAR]}) + "\n```")
        self.assertEqual([d.concept for d in dets], ["bear"])
        self.assertTrue(dets[0].mask_png)

    def test_malformed_box_skips_only_that_detection(self):
        bad = dict(SNAKE, box_2d=["x", 0, 10, 10])
        dets, _ = scan(json.dumps({"detections": [BEAR, bad]}))
        self.assertEqual([d.concept for d in dets], ["bear"])
        self.assertTrue(dets[0].mask_png)

    def test_nan_box_is_skipped_not_corrupted(self):
        dets, _ = scan('{"detections":[{"concept":"bear","box_2d":[NaN,0,500,500]}]}')
        self.assertEqual(dets, [])

    def test_connection_drop_surfaces_as_itself_not_http_0(self):
        with self.assertRaises(ConnectionResetError):
            scan(exc=ConnectionResetError("stale keep-alive closed"))


class SamStreamRobustnessTests(unittest.TestCase):
    def test_parser_skips_malformed_record_keeps_good(self):
        text = (
            "<0f>0<|box;x1=10;y1=10;x2=100;y2=100;w=200;h=200|>"
            "<1f>1<|box;x1=10;y1=10;y2=100;w=200;h=200|>"
        )
        records = _BuiltinHelperParser.parse_sam_output(text)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["object_id"], "0")

    def test_inverted_box_is_normalized_not_negative(self):
        record = normalize_record(
            {"object_id": "0", "x1": 100, "y1": 100, "x2": 10, "y2": 10,
             "w": 200, "h": 200},
            concept="bear",
        )
        self.assertEqual(record["bbox"], [0.05, 0.05, 0.45, 0.45])

    def test_helper_output_drops_degenerate_keeps_valid(self):
        payload = {
            "provider_request_sent": True,
            "records": [
                {"object_id": "0", "x1": 10, "y1": 10, "x2": 100, "y2": 100,
                 "w": 200, "h": 200},
                {"object_id": "1", "x1": 50, "y1": 50, "x2": 50, "y2": 50,
                 "w": 200, "h": 200},
            ],
        }
        mapped = records_from_helper_output(payload, concept="snake")
        self.assertEqual(len(mapped), 1)
        self.assertEqual(mapped[0]["track_id"], "0")

    def test_parser_lib_dir_points_inside_repo(self):
        root = Path(__file__).resolve().parent.parent
        self.assertEqual(meta_transport._PARSER_LIB_DIR, root / "tools" / "pylibs")


class RealSAMClientMaskTests(unittest.TestCase):
    def test_bad_mask_rect_drops_mask_not_detection(self):
        record = {
            "concept": "snake", "distance_m": 2.0, "track_id": "snake-0",
            "bbox": [0.1, 0.2, 0.3, 0.4],
            "mask_png": "data:image/png;base64,AAAA", "mask_rect": "bogus",
        }

        class Transport:
            def segment(self, request):
                return [record]

        with tempfile.TemporaryDirectory() as tmp:
            budget = CallBudget(daily_cap=5, counter_path=Path(tmp) / "c.json")
            client = RealSAMClient(transport=Transport(), budget=budget, enabled=True)
            from sam_client import SegmentRequest

            dets = client.segment_request(
                SegmentRequest.for_image(
                    b"img", frame_idx=0, image_media_type="image/jpeg"
                )
            )
        self.assertEqual(len(dets), 1)
        self.assertIsNone(dets[0].mask_png)
        self.assertIsNone(dets[0].mask_rect)


class HudMaskRepaintTests(unittest.TestCase):
    def test_late_mask_decode_repaints_current_hud(self):
        src = (Path(__file__).resolve().parent.parent / "webapp" / "app.js").read_text()
        start = src.index("function cachedMaskImage")
        block = src[start:src.index("function drawBoxes", start)]
        self.assertIn("drawBoxes(lastDetections)", block)
        self.assertNotIn("gen === drawBoxesGen", block)


if __name__ == "__main__":
    unittest.main()
