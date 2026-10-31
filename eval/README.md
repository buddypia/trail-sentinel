# Evaluation harness

Claims are backed by numbers. A test-clip set is labelled per clip, and the
harness measures the pipeline against the labels — including clips where it
fails. Well-performing clips are never cherry-picked.

## Files

- `clips_manifest.example.json` — label format. One entry per clip:
  `clip`, `hazard` (hazard key or `null`), `ground_truth_frame_range`
  (`[start, end]` or `null`), `reach_frame` (frame at which the walker would
  reach the hazard; used for lead time), `notes`.
- `results.example.json` — pipeline output format: `{clip: [alert frames]}`.
- `score.py` — scoring skeleton (see below).

## Metrics

- **Detection rate** — share of labelled hazard clips with at least one alert
  inside the ground-truth frame range (reported per concept in the full run).
- **Warning lead time** — seconds between the first in-range alert and the
  frame where the walker reaches the hazard.
- **False-alarm rate** — alerts outside any ground-truth range, per minute of
  footage.
- **Latency** (planned) — frame capture → alert output round-trip distribution.

No target numbers are written before the first real measurement; the first
run becomes the baseline and before/after improvements go into the submission.

## Run the skeleton

```bash
cd eval
python score.py            # uses the example manifest + results
```
