"""The status/scan payload must say which backend actually served a model."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import server


class BackendBadgeTests(unittest.TestCase):
    def test_vertex_bridge_when_helper_missing(self):
        with mock.patch.object(server, "LIVE_ENABLED", True), mock.patch.object(
            server, "resolve_helper_path", return_value=Path("/nonexistent/helper.py")
        ):
            for model_id in server.MODEL_BY_ID:
                self.assertEqual(server.backend_for(model_id), "vertex-bridge")

    def test_meta_sam_only_for_pure_route_with_helper(self):
        with mock.patch.object(server, "LIVE_ENABLED", True), mock.patch.object(
            server, "resolve_helper_path", return_value=Path(__file__)
        ):
            self.assertEqual(server.backend_for("sam-3.1"), "meta-sam-3.1")
            self.assertEqual(server.backend_for("sam-3.1-hybrid"), "vertex-bridge")

    def test_stub_mode(self):
        with mock.patch.object(server, "LIVE_ENABLED", False):
            self.assertEqual(server.backend_for("sam-3.1"), "stub")

    def test_status_exposes_backend(self):
        s = server.status()
        self.assertIn("backend", s)
        self.assertEqual(set(s["backend_by_model"]), set(server.MODEL_BY_ID))


if __name__ == "__main__":
    unittest.main()
