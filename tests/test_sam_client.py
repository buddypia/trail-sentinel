from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import CallBudget
from sam_client import (
    BudgetNotConfiguredError,
    LiveInferenceDisabledError,
    RealSAMClient,
    SegmentRequest,
    TransportNotConfiguredError,
)


class MockTransport:
    def __init__(self, records):
        self.records = records
        self.requests = []

    def segment(self, request):
        self.requests.append(request)
        return self.records


def image_request() -> SegmentRequest:
    return SegmentRequest.for_image(
        b"mock-image-bytes",
        frame_idx=45,
        image_media_type="image/jpeg",
    )


def snake_record(**overrides):
    record = {
        "concept": "snake",
        "confidence": 0.91,
        "distance_m": 2.4,
        "clock_direction": 12,
        "track_id": "snake-track-1",
        "bbox": [0.4, 0.6, 0.2, 0.1],
    }
    record.update(overrides)
    return record


class RealSAMClientTests(unittest.TestCase):
    def make_budget(self, directory: str) -> CallBudget:
        return CallBudget(daily_cap=2, counter_path=Path(directory) / "counter.json")

    def test_disabled_by_default_and_does_not_spend_or_call(self):
        transport = MockTransport([snake_record()])
        with tempfile.TemporaryDirectory() as directory:
            budget = self.make_budget(directory)
            client = RealSAMClient(transport=transport, budget=budget)

            with self.assertRaises(LiveInferenceDisabledError):
                client.segment_request(image_request())

            self.assertEqual(transport.requests, [])
            self.assertEqual(budget.used_today(), 0)

    def test_enabled_requires_budget(self):
        transport = MockTransport([snake_record()])
        client = RealSAMClient(transport=transport, enabled=True)

        with self.assertRaises(BudgetNotConfiguredError):
            client.segment_request(image_request())

        self.assertEqual(transport.requests, [])

    def test_enabled_requires_transport_and_does_not_spend(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = self.make_budget(directory)
            client = RealSAMClient(budget=budget, enabled=True)

            with self.assertRaises(TransportNotConfiguredError):
                client.segment_request(image_request())

            self.assertEqual(budget.used_today(), 0)

    def test_mock_transport_maps_normalized_record_and_spends_once(self):
        transport = MockTransport([snake_record()])
        with tempfile.TemporaryDirectory() as directory:
            budget = self.make_budget(directory)
            client = RealSAMClient(
                transport=transport,
                budget=budget,
                enabled=True,
            )

            detections = client.segment_request(image_request())

            self.assertEqual(len(transport.requests), 1)
            self.assertEqual(budget.used_today(), 1)
            self.assertEqual(len(detections), 1)
            self.assertEqual(detections[0].concept, "snake")
            self.assertEqual(detections[0].frame_idx, 45)
            self.assertEqual(detections[0].distance_m, 2.4)
            self.assertEqual(detections[0].track_id, "snake-track-1")
            self.assertEqual(detections[0].bbox, [0.4, 0.6, 0.2, 0.1])

    def test_distance_estimator_can_supply_missing_distance(self):
        record = snake_record()
        del record["distance_m"]
        transport = MockTransport([record])
        with tempfile.TemporaryDirectory() as directory:
            budget = self.make_budget(directory)
            client = RealSAMClient(
                transport=transport,
                budget=budget,
                enabled=True,
                distance_estimator=lambda _record, _request: 3.25,
            )

            detections = client.segment_request(image_request())

            self.assertEqual(detections[0].distance_m, 3.25)

    def test_missing_distance_without_estimator_is_rejected(self):
        record = snake_record()
        del record["distance_m"]
        transport = MockTransport([record])
        with tempfile.TemporaryDirectory() as directory:
            budget = self.make_budget(directory)
            client = RealSAMClient(
                transport=transport,
                budget=budget,
                enabled=True,
            )

            with self.assertRaisesRegex(ValueError, "no distance_m"):
                client.segment_request(image_request())


if __name__ == "__main__":
    unittest.main()
