"""Alert output: voice + vibration. Stub prints; TTS hook is a TODO."""
from __future__ import annotations

from dataclasses import dataclass

from triage import AlertDecision


@dataclass
class EmittedAlert:
    frame_idx: int
    concept: str
    phrase: str
    score: float


def speak(text: str) -> None:
    """TODO: hook a real TTS engine here (device TTS / Meta voice).

    Placeholder only — prints what would be spoken so the stub demo and the
    eval harness can run with no audio stack.
    """
    print(f"  🔊 (TTS) {text}")


def vibrate(pattern: str = "strong") -> None:
    """TODO: hook the phone vibration API in the live app."""
    print(f"  📳 (vibrate: {pattern})")


def emit(decision: AlertDecision) -> EmittedAlert:
    det = decision.detection
    print(f"[frame {det.frame_idx}] ⚠️  {decision.phrase}  (score {decision.score})")
    vibrate()
    speak(decision.phrase)
    return EmittedAlert(frame_idx=det.frame_idx, concept=det.concept,
                         phrase=decision.phrase, score=decision.score)
