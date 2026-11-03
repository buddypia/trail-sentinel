"""Tests for the live Meta SAM transport mapping.

The parser/mapping tests run against a REAL recorded provider response
(``tests/fixtures/sam_hero_snake_raw.txt``): the raw streamed body of the
2026-10-31 ``segment-image`` call on ``eval/data/hero_snake_leaves_01.jpg``
with prompt ``snake`` (1 image call, USD 0.0025 of the hackathon credit).
No network and no provider calls happen in these tests.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import CallBudget
from meta_transport import (
    DEFAULT_HELPER_PATH,
    HELPER_ENV_VAR,
    HelperNotConfiguredError,
    MetaSAMTransport,
    ground_plane_distance_estimator,
    load_helper_parser,
    normalize_record,
    records_from_helper_output,
    resolve_helper_path,
)
from sam_client import RealSAMClient, SegmentRequest

RAW_FIXTURE = Path(__file__).parent / "fixtures" / "sam_hero_snake_raw.txt"


def parsed_hero_records():
    helper = load_helper_parser()
    raw = RAW_FIXTURE.read_text(encoding="utf-8")
    return helper.parse_sam_output(helper.extract_output_text(raw))


def image_request() -> SegmentRequest:
    return SegmentRequest.for_image(
        b"mock-image-bytes",
        frame_idx=0,
        image_media_type="image/jpeg",
    )


class RealResponseParserTests(unittest.TestCase):
    def test_real_response_parses_to_one_snake_box_with_mask(self):
        records = parsed_hero_records()

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record["frame"], 0)
        self.assertEqual(record["object_id"], "0")
        # Pixel space of the 2048x1365 hero still.
        self.assertEqual(record["x1"], 288.0)
        self.assertEqual(record["y1"], 526.0)
        self.assertEqual(record["x2"], 1441.0)
        self.assertEqual(record["y2"], 962.0)
        self.assertEqual(record["w"], 2048.0)
        self.assertEqual(record["h"], 1365.0)
        self.assertTrue(record["mask_present"])
        self.assertGreater(record["mask_data_len"], 0)

    def test_normalize_uses_frame_dimensions_not_box_size(self):
        record = normalize_record(parsed_hero_records()[0], concept="snake")

        self.assertEqual(record["concept"], "snake")
        self.assertEqual(record["track_id"], "0")
        self.assertEqual(record["bbox"], [0.1406, 0.3853, 0.563, 0.3194])
        self.assertEqual(record["clock_direction"], 12)
        self.assertTrue(record["mask_present"])
        # SAM provides neither: both keys must be absent, never invented.
        self.assertNotIn("confidence", record)
        self.assertNotIn("distance_m", record)


class HelperOutputMappingTests(unittest.TestCase):
    def test_records_from_helper_output_maps_records(self):
        payload = {"provider_request_sent": True, "records": parsed_hero_records()}
        mapped = records_from_helper_output(payload, concept="snake")
        self.assertEqual(len(mapped), 1)
        self.assertEqual(mapped[0]["concept"], "snake")

    def test_records_from_helper_output_rejects_unsent_or_failed(self):
        with self.assertRaises(RuntimeError):
            records_from_helper_output(
                {"provider_request_sent": False, "records": []}, concept="snake"
            )
        with self.assertRaises(RuntimeError):
            records_from_helper_output(
                {"provider_request_sent": True, "error": "HTTP 500"},
                concept="snake",
            )


class DistanceEstimatorTests(unittest.TestCase):
    def test_hero_box_estimates_a_few_metres(self):
        record = normalize_record(parsed_hero_records()[0], concept="snake")
        distance = ground_plane_distance_estimator(record, image_request())
        self.assertEqual(distance, 2.71)

    def test_bottom_of_frame_is_close_and_horizon_is_far(self):
        close = {"bbox": [0.3, 0.9, 0.4, 0.08]}   # bottom 0.98
        far = {"bbox": [0.3, 0.2, 0.4, 0.1]}      # bottom 0.30 = horizon
        self.assertLess(
            ground_plane_distance_estimator(close, image_request()), 1.2
        )
        self.assertEqual(
            ground_plane_distance_estimator(far, image_request()), 12.0
        )

    def test_tall_box_is_capped(self):
        tall = {"bbox": [0.0, 0.0, 1.0, 0.6]}     # fills 60% of frame height
        self.assertEqual(
            ground_plane_distance_estimator(tall, image_request()), 2.0
        )


class RealSAMClientWithRecordedResponseTests(unittest.TestCase):
    def test_recorded_response_flows_to_detection(self):
        payload = {"provider_request_sent": True, "records": parsed_hero_records()}

        class RecordedTransport:
            def segment(self, request):
                return records_from_helper_output(payload, concept="snake")

        with tempfile.TemporaryDirectory() as directory:
            budget = CallBudget(
                daily_cap=5, counter_path=Path(directory) / "counter.json"
            )
            client = RealSAMClient(
                transport=RecordedTransport(),
                budget=budget,
                enabled=True,
                distance_estimator=ground_plane_distance_estimator,
            )

            detections = client.segment_request(image_request())

            self.assertEqual(budget.used_today(), 1)
            self.assertEqual(len(detections), 1)
            det = detections[0]
            self.assertEqual(det.concept, "snake")
            self.assertIsNone(det.confidence)  # SAM returns no confidence
            self.assertEqual(det.distance_m, 2.71)  # labelled estimate
            self.assertEqual(det.bbox, [0.1406, 0.3853, 0.563, 0.3194])
            self.assertEqual(det.track_id, "0")
            self.assertEqual(det.clock_direction, 12)


class MetaSAMTransportGuardTests(unittest.TestCase):
    def test_video_ref_request_is_rejected_without_any_call(self):
        transport = MetaSAMTransport()
        request = SegmentRequest.for_video_ref("unused", frame_idx=0)
        with self.assertRaises(ValueError):
            transport.segment(request)


class HelperPathResolutionTests(unittest.TestCase):
    def test_default_is_builtin_path_when_env_unset(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(HELPER_ENV_VAR, None)
            self.assertEqual(resolve_helper_path(), DEFAULT_HELPER_PATH)
            self.assertEqual(MetaSAMTransport().helper_path, DEFAULT_HELPER_PATH)

    def test_env_var_overrides_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "meta_model_api.py"
            with mock.patch.dict(os.environ, {HELPER_ENV_VAR: str(fake)}):
                self.assertEqual(resolve_helper_path(), fake)
                self.assertEqual(MetaSAMTransport().helper_path, fake)

    def test_explicit_argument_beats_env_var(self):
        explicit = Path("/somewhere/explicit.py")
        with mock.patch.dict(
            os.environ, {HELPER_ENV_VAR: "/somewhere/from-env.py"}
        ):
            self.assertEqual(resolve_helper_path(explicit), explicit)
            self.assertEqual(
                MetaSAMTransport(helper_path=explicit).helper_path, explicit
            )

    def test_missing_helper_fails_with_clear_not_configured_error(self):
        transport = MetaSAMTransport(helper_path="/nonexistent/meta_model_api.py")
        with self.assertRaises(HelperNotConfiguredError) as ctx:
            transport.segment(image_request())
        message = str(ctx.exception)
        self.assertIn("not configured", message)
        self.assertIn(HELPER_ENV_VAR, message)

    def test_env_pointing_at_missing_helper_also_fails_clearly(self):
        with mock.patch.dict(
            os.environ, {HELPER_ENV_VAR: "/nonexistent/env_helper.py"}
        ):
            transport = MetaSAMTransport()
            with self.assertRaises(HelperNotConfiguredError):
                transport.segment(image_request())


if __name__ == "__main__":
    unittest.main()
