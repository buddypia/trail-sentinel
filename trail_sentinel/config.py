"""Trail Sentinel configuration: hazards and spending guard."""
from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

# Registered Meta Model API host. Base URL https://api.meta.ai/v1 was
# confirmed live on 2026-10-31 (models list + SAM segmentation); the wire
# calls themselves live in the connector helper, not in this package.
META_MODEL_API_HOST = "api.meta.ai"

# --- Hazard concepts v1 (frozen by spec, 2026-10-28). Max 6 baseline + F7 live custom concepts. ---
# zone: "feet" (발밑/발 앞) or "front" (전방). severity: 1 (caution) .. 3 (stop).
@dataclass(frozen=True)
class Hazard:
    key: str
    name_ko: str
    prompt: str
    zone: str
    severity: int
    name_en: str = ""
    name_ja: str = ""

    def label_for(self, lang: str = "en") -> str:
        code = (lang or "en").lower()[:2]
        if code == "ja":
            return self.name_ja or self.name_en or self.name_ko
        if code == "ko":
            return self.name_ko or self.name_en or self.name_ja
        return self.name_en or self.name_ko or self.name_ja


DEFAULT_HAZARDS: tuple[Hazard, ...] = (
    Hazard("snake", "뱀", "a snake camouflaged among fallen leaves and soil", "feet", 3, "Snake", "ヘビ"),
    Hazard("wasp_nest", "말벌집", "a wasp nest attached to a tree, rock or structure", "front", 3, "Wasp nest", "スズメバチの巣"),
    Hazard("bear", "곰", "a bear on or near the trail", "front", 3, "Bear", "クマ"),
    Hazard("boar", "멧돼지", "a wild boar on or near the trail", "front", 2, "Wild boar", "イノシシ"),
    Hazard("rockfall", "낙석 구간", "a pile of fallen rocks or a collapsed trail section", "front", 2, "Rockfall zone", "落石区間"),
    Hazard("slippery", "미끄러운 구간", "a hidden hole, protruding root or wet slippery fallen leaves underfoot", "feet", 1, "Slippery path", "滑りやすい路面"),
)

HAZARDS: list[Hazard] = list(DEFAULT_HAZARDS)
HAZARD_BY_KEY: dict[str, Hazard] = {h.key: h for h in HAZARDS}
_hazard_lock = threading.Lock()

_KO_PROMPT_PRESETS: dict[str, str] = {
    "쓰러진 나무": "a fallen tree or log blocking the trail",
    "전동 킥보드": "an electric scooter on the trail",
    "자전거": "a bicycle or mountain bike approaching on the trail",
    "절벽": "a steep cliff edge or drop-off beside the trail",
    "웅덩이": "a deep water puddle or mud hole on the trail",
    "얼음": "black ice or frozen slippery patch on the trail",
    "개": "an unleashed dog on the trail",
    "사슴": "a deer or elk on the trail",
    "倒木": "a fallen tree or log blocking the trail",
    "自転車": "a bicycle or mountain bike approaching on the trail",
    "崖": "a steep cliff edge or drop-off beside the trail",
    "水たまり": "a deep water puddle or mud hole on the trail",
    "凍結": "black ice or frozen slippery patch on the trail",
    "犬": "an unleashed dog on the trail",
    "シカ": "a deer or elk on the trail",
    "fallen tree": "a fallen tree or log blocking the trail",
    "bicycle": "a bicycle or mountain bike approaching on the trail",
    "cliff": "a steep cliff edge or drop-off beside the trail",
    "puddle": "a deep water puddle or mud hole on the trail",
    "black ice": "black ice or frozen slippery patch on the trail",
}


def register_custom_hazard(
    name_ko: str,
    prompt: str | None = None,
    *,
    key: str | None = None,
    zone: str = "front",
    severity: int = 2,
    name_en: str | None = None,
    name_ja: str | None = None,
) -> Hazard:
    """Register a zero-retraining custom hazard concept at runtime (PRD F7)."""
    clean_name = (name_ko or name_en or name_ja or "").strip()
    if not clean_name:
        raise ValueError("name_ko is required")
    clean_prompt = (prompt or "").strip()
    if not clean_prompt:
        clean_prompt = _KO_PROMPT_PRESETS.get(
            clean_name, _KO_PROMPT_PRESETS.get(clean_name.lower(), clean_name)
        )
    if zone not in ("feet", "front"):
        zone = "front"
    sev = max(1, min(3, int(severity)))
    with _hazard_lock:
        for existing in HAZARDS:
            if (
                existing.name_ko == clean_name
                or existing.name_en.lower() == clean_name.lower()
                or existing.name_ja == clean_name
                or (key and existing.key == key)
            ):
                return existing
        slug = re.sub(r"[^a-z0-9_]+", "_", (key or clean_prompt).lower()).strip("_")
        if not slug or slug in HAZARD_BY_KEY:
            slug = f"custom_{len(HAZARDS) + 1}"
        hazard = Hazard(
            key=slug,
            name_ko=clean_name,
            prompt=clean_prompt,
            zone=zone,
            severity=sev,
            name_en=(name_en or clean_name).strip(),
            name_ja=(name_ja or clean_name).strip(),
        )
        HAZARDS.append(hazard)
        HAZARD_BY_KEY[hazard.key] = hazard
        return hazard


def reset_custom_hazards() -> None:
    """Restore HAZARDS and HAZARD_BY_KEY to the frozen 6 v1 concepts."""
    with _hazard_lock:
        HAZARDS.clear()
        HAZARDS.extend(DEFAULT_HAZARDS)
        HAZARD_BY_KEY.clear()
        for h in DEFAULT_HAZARDS:
            HAZARD_BY_KEY[h.key] = h


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
