#!/usr/bin/env python3
"""Eval scoring skeleton.

Inputs:
  --manifest  JSON list: {clip, hazard, ground_truth_frame_range, reach_frame, notes}
  --results   JSON dict: {clip: [alert_frame, ...]} as emitted by the pipeline
  --fps       frames per second of the source clips (default 10)

Metrics (per spec — measured, never cherry-picked; failed clips stay in):
  detection rate    labelled hazard clips with >=1 alert inside the GT range / all hazard clips
  warning lead time (reach_frame - first_in_range_alert_frame) / fps, seconds
  false-alarm rate  alerts outside any GT range (incl. all alerts on no-hazard clips)
                    per no-hazard clip-minute; also reported as a raw count
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Trail Sentinel eval scoring (skeleton)")
    ap.add_argument("--manifest", default="clips_manifest.example.json")
    ap.add_argument("--results", default="results.example.json")
    ap.add_argument("--fps", type=float, default=10.0)
    ap.add_argument("--clip-frames", type=int, default=60,
                    help="frames per clip, for the false-alarm rate denominator")
    args = ap.parse_args()

    here = Path(__file__).parent
    manifest = json.loads((here / args.manifest).read_text())
    results = json.loads((here / args.results).read_text())

    hazard_clips = [m for m in manifest if m["hazard"]]
    detected, lead_times, false_alarms = 0, [], 0

    for entry in manifest:
        alerts = sorted(results.get(entry["clip"], []))
        gt = entry["ground_truth_frame_range"]
        if gt is None:
            false_alarms += len(alerts)
            continue
        in_range = [f for f in alerts if gt[0] <= f <= gt[1]]
        false_alarms += len(alerts) - len(in_range)
        if in_range:
            detected += 1
            reach = entry.get("reach_frame") or gt[1]
            lead_times.append((reach - in_range[0]) / args.fps)

    n = len(hazard_clips)
    no_hazard_clips = [m for m in manifest if not m["hazard"]]
    no_hazard_minutes = max(len(no_hazard_clips), 1) * args.clip_frames / args.fps / 60.0
    total_minutes = max(len(manifest), 1) * args.clip_frames / args.fps / 60.0
    print(f"clips: {len(manifest)} (hazard: {n}, no-hazard: {len(no_hazard_clips)})")
    print(f"detection rate:    {detected}/{n} = {detected / n:.0%}" if n else "detection rate: n/a")
    if lead_times:
        print(f"warning lead time: avg {sum(lead_times) / len(lead_times):.1f}s "
              f"({', '.join(f'{t:.1f}s' for t in lead_times)})")
    print(
        f"false alarms:      {false_alarms} total, "
        f"{false_alarms / no_hazard_minutes:.2f}/min of no-hazard footage "
        f"({false_alarms / total_minutes:.2f}/min of all footage)"
    )


if __name__ == "__main__":
    main()
