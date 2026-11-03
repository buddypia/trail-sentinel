"""Priority triage (the Muse Wonder role, as deterministic logic for v1).

Scores each tracked hazard by severity, proximity and approach speed, and
decides whether it crosses the alert threshold. Only the top hazard alerts —
the design rule is: warn rarely, briefly, with direction.
"""
from __future__ import annotations

from dataclasses import dataclass

from config import HAZARD_BY_KEY
from sam_client import Detection

# === [FEAT:F4] [FEAT:F5] [FEAT:F10] Priority Triage & Localized Spoken Phrase
# Alert distance by severity: a low-severity hazard (wet leaves underfoot)
# only alerts when it is imminent, otherwise it would fire constantly and
# drown out real dangers. Severity 3 stops you at 3 metres.
ALERT_DISTANCE_M = {3: 3.0, 2: 2.5, 1: 1.0}
COOLDOWN_FRAMES = 30       # min frames between repeat alerts for one track


@dataclass
class AlertDecision:
    detection: Detection
    score: float
    phrase: str


def approach_speed_mps(prev: Detection | None, cur: Detection, fps: float) -> float:
    """Positive = getting closer, metres per second."""
    if prev is None or cur.frame_idx <= prev.frame_idx:
        return 0.0
    dt = (cur.frame_idx - prev.frame_idx) / fps
    return max(0.0, (prev.distance_m - cur.distance_m) / dt)


def score(det: Detection, speed_mps: float) -> float:
    hazard = HAZARD_BY_KEY[det.concept]
    proximity = max(0.0, 1.0 - det.distance_m / 10.0)   # 0 at 10m, 1 at 0m
    # Live SAM detections carry no confidence (None): they contribute 0.0
    # rather than an invented score. Stub detections carry a real float.
    confidence = det.confidence if det.confidence is not None else 0.0
    return hazard.severity * 2.0 * proximity + min(speed_mps, 2.0) + confidence


def phrase_for(det: Detection, lang: str = "en") -> str:
    """Short spoken warning: direction + distance + hazard in en / ko / ja."""
    hazard = HAZARD_BY_KEY[det.concept]
    dist = max(1, round(det.distance_m))
    code = (lang or "en").lower()[:2]
    if code == "ja":
        if hazard.zone == "feet":
            where = (
                "足元前方"
                if det.clock_direction == 12
                else f"{det.clock_direction}時方向の足元"
            )
        else:
            where = (
                "前方"
                if det.clock_direction == 12
                else f"{det.clock_direction}時方向"
            )
        return f"{where} {dist}メートル、{hazard.label_for('ja')}"
    if code == "ko":
        if hazard.zone == "feet":
            where = "발 앞" if det.clock_direction == 12 else f"{det.clock_direction}시 방향 발 앞"
        else:
            where = "전방" if det.clock_direction == 12 else f"{det.clock_direction}시 방향"
        return f"{where} {dist}미터, {hazard.label_for('ko')}"
    if hazard.zone == "feet":
        where = (
            "Underfoot ahead"
            if det.clock_direction == 12
            else f"{det.clock_direction} o'clock underfoot"
        )
    else:
        where = (
            "Ahead"
            if det.clock_direction == 12
            else f"{det.clock_direction} o'clock"
        )
    unit = "meter" if dist == 1 else "meters"
    return f"{where}, {dist} {unit}, {hazard.label_for('en')}"


def evaluate(detections: list[Detection],
             prev_by_track: dict[str, Detection],
             fps: float = 10.0,
             lang: str = "en") -> AlertDecision | None:
    """Return an alert for the single highest-priority hazard, or None."""
    best: AlertDecision | None = None
    for det in detections:
        if det.distance_m > ALERT_DISTANCE_M[HAZARD_BY_KEY[det.concept].severity]:
            continue
        s = score(det, approach_speed_mps(prev_by_track.get(det.track_id), det, fps))
        if best is None or s > best.score:
            best = AlertDecision(
                detection=det,
                score=round(s, 2),
                phrase=phrase_for(det, lang=lang),
            )
    return best
