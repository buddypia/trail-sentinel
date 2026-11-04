"""Performance-first fast path contracts (no network).

The live loop re-scans continuously, so per-scan tail latency matters
more than one frame's extra reasoning: every bridge route must stay on
MINIMAL thinking, and the single-pass prompt must keep a small output
budget so generation time stays bounded.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vision_router import _BRIDGE_CONFIG


class FastBridgeConfigTests(unittest.TestCase):
    def test_all_routes_use_minimal_thinking(self):
        self.assertTrue(_BRIDGE_CONFIG)
        for model_id, (_bridge, thinking) in _BRIDGE_CONFIG.items():
            self.assertEqual(thinking, "MINIMAL", model_id)


if __name__ == "__main__":
    unittest.main()
