"""Trail Sentinel configuration: hazards and spending guard."""
from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

# Registered Meta Model API host. Base URL https://api.meta.ai/v1 was
# confirmed live on 2026-10-31 (models list + SAM segmentation); the wire
# calls themselves live in the connector helper, not in this package.
META_MODEL_API_HOST = "api.meta.ai"

# --- Hazard concepts v1 (frozen by spec, 2026-10-28). Max 6. ---
# zone: "feet" (발밑/발 앞) or "front" (전방). severity: 1 (caution) .. 3 (stop).
@dataclass(frozen=True)
class Hazard:
    key: str
    name_ko: str
    prompt: str
    zone: str
    severity: int

HAZARDS: list[Hazard] = [
    Hazard("snake", "뱀", "a snake camouflaged among fallen leaves and soil", "feet", 3),
    Hazard("wasp_nest", "말벌집", "a wasp nest attached to a tree, rock or structure", "front", 3),
    Hazard("bear", "곰", "a bear on or near the trail", "front", 3),
    Hazard("boar", "멧돼지", "a wild boar on or near the trail", "front", 2),
    Hazard("rockfall", "낙석 구간", "a pile of fallen rocks or a collapsed trail section", "front", 2),
    Hazard("slippery", "미끄러운 구간", "a hidden hole, protruding root or wet slippery fallen leaves underfoot", "feet", 1),
]
HAZARD_BY_KEY = {h.key: h for h in HAZARDS}


# --- Spending guard: no hard cap exists on Meta billing, so the client
# enforces its own daily call budget with a JSON counter file. ---
class BudgetExceeded(RuntimeError):
    pass


@dataclass
class CallBudget:
    daily_cap: int = field(default_factory=lambda: int(os.environ.get("DAILY_CALL_CAP", "200")))
    counter_path: Path = field(
        default_factory=lambda: Path(os.environ.get("CALL_COUNTER_FILE", ".call_counter.json"))
    )

    def __post_init__(self) -> None:
        # Live scans fan out per-concept calls in parallel threads; the
        # counter file read-modify-write must stay atomic across them.
        self._lock = threading.Lock()

    def _read(self) -> dict:
        if self.counter_path.exists():
            return json.loads(self.counter_path.read_text())
        return {"date": str(date.today()), "calls": 0}

    def _used_today_unlocked(self) -> int:
        data = self._read()
        return data["calls"] if data["date"] == str(date.today()) else 0

    def used_today(self) -> int:
        with self._lock:
            return self._used_today_unlocked()

    def spend(self, n: int = 1) -> int:
        """Record n API calls; raise BudgetExceeded once the daily cap is hit."""
        with self._lock:
            used = self._used_today_unlocked()
            if used + n > self.daily_cap:
                raise BudgetExceeded(f"daily call cap reached ({used}/{self.daily_cap})")
            self.counter_path.write_text(json.dumps({"date": str(date.today()), "calls": used + n}))
            return used + n
