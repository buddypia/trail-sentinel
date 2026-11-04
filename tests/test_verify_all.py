"""The verification gate itself: formal checks must pass on this tree,
and the checkers must actually be able to fail (a gate that always
passes proves nothing). Empirical probes run without the unit suite
to avoid recursive discovery."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import verify_all


class FormalGateTests(unittest.TestCase):
    def test_formal_layer_passes_on_current_tree(self):
        results = verify_all.run_formal(ROOT)
        self.assertTrue(results)
        for r in results:
            self.assertTrue(r.ok, f"{r.name}: {r.detail}")

    def test_bridge_checker_rejects_slow_thinking(self):
        bad = '_BRIDGE_CONFIG = {"m": ("gemini", "LOW")}\n'
        self.assertFalse(verify_all.bridge_thinking_ok(bad))

    def test_js_checker_rejects_slow_constants(self):
        bad = "const CAPTURE_TARGET_LONG = 416;\n" \
              "const NEXT_LIVE_DELAY_MS = 160;\n" \
              "const FRAME_CACHE_MAX_MS = 2000;\n"
        self.assertFalse(verify_all.js_fast_constants_ok(bad))

    def test_secret_checker_finds_planted_key(self):
        hits = verify_all.find_secret_hits("api_key = 'abcdef0123456789'\n")
        self.assertTrue(hits)
        self.assertEqual(verify_all.find_secret_hits("token = get_token()\n"), [])


class EmpiricalGateTests(unittest.TestCase):
    def test_empirical_probes_pass_without_recursive_suite(self):
        results = verify_all.run_empirical(ROOT, include_unit_suite=False)
        self.assertTrue(results)
        for r in results:
            self.assertTrue(r.ok, f"{r.name}: {r.detail}")

    def test_frame_diff_rule(self):
        self.assertEqual(verify_all.frame_diff([7] * 4, [7] * 4), 0.0)
        self.assertGreater(verify_all.frame_diff([0] * 4, [90] * 4), 1.8)


if __name__ == "__main__":
    unittest.main()
