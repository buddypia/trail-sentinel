#!/usr/bin/env python3
"""Trail Sentinel stub demo.

Runs the full pipeline (SAM stub -> triage -> voice/vibration alert) on a
fixture scene. No API key and no network needed.

    python main.py                      # hero scene: snake in fallen leaves
    python main.py --frames 60 --step 5
"""
from __future__ import annotations

import argparse
from pathlib import Path

from config import CallBudget
from pipeline import run_pipeline
from sam_client import StubSAMClient

ROOT = Path(__file__).parent


def main() -> None:
    ap = argparse.ArgumentParser(description="Trail Sentinel stub demo")
    ap.add_argument("--scene", default="hero_snake_leaves")
    ap.add_argument("--frames", type=int, default=60, help="total frames to simulate")
    ap.add_argument("--step", type=int, default=5, help="sample every Nth frame")
    ap.add_argument("--lang", default="en", choices=("en", "ko", "ja"), help="output language (default: en)")
    args = ap.parse_args()

    print("Trail Sentinel — mode: STUB (fixtures, $0 spend)")
    print(f"Scene: {args.scene} | frames 0..{args.frames} step {args.step} | lang: {args.lang}\n")

    budget = CallBudget(counter_path=ROOT / ".call_counter.json")
    sam = StubSAMClient(ROOT / "fixtures")
    alerts = run_pipeline(args.scene, sam, budget=budget,
                          total_frames=args.frames, frame_step=args.step,
                          lang=args.lang)

    print(f"\nDone. {len(alerts)} alert(s) emitted, "
          f"{budget.used_today()} stub SAM call(s) counted today "
          f"(daily cap {budget.daily_cap}).")
    for a in alerts:
        print(f"  - frame {a.frame_idx}: {a.phrase}")


if __name__ == "__main__":
    main()
