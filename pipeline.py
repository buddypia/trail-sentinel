"""End-to-end pipeline: frames -> SAM -> triage -> alert.

Works on a clip/scene identifier. With StubSAMClient the scene name selects
a fixture; with the real client it will be a video file path whose frames
are sampled and sent to SAM 3.1.
"""
from __future__ import annotations

from alerts import EmittedAlert, emit
from config import CallBudget
from sam_client import Detection, SAMClient
from triage import COOLDOWN_FRAMES, evaluate


def run_pipeline(scene: str, sam: SAMClient, budget: CallBudget | None = None,
                 total_frames: int = 60, frame_step: int = 5,
                 fps: float = 10.0, verbose: bool = True,
                 lang: str = "en") -> list[EmittedAlert]:
    alerts: list[EmittedAlert] = []
    prev_by_track: dict[str, Detection] = {}
    last_alert_frame: dict[str, int] = {}

    for frame_idx in range(0, total_frames, frame_step):
        if budget is not None:
            budget.spend(1)  # one (stubbed) SAM call per sampled frame
        detections = sam.segment(scene, frame_idx)
        decision = evaluate(detections, prev_by_track, fps=fps, lang=lang)
        for det in detections:
            prev_by_track[det.track_id] = det
        if decision is None:
            continue
        track = decision.detection.track_id
        if frame_idx - last_alert_frame.get(track, -10**9) < COOLDOWN_FRAMES:
            continue  # suppress repeats: warn once, not every frame
        alerts.append(emit(decision) if verbose else EmittedAlert(
            frame_idx=decision.detection.frame_idx, concept=decision.detection.concept,
            phrase=decision.phrase, score=decision.score))
        last_alert_frame[track] = frame_idx
    return alerts
