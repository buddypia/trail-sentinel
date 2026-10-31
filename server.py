#!/usr/bin/env python3
"""Trail Sentinel mobile-web backend (stdlib only).

    python3 server.py                    # stub mode, http://localhost:8765
    TRAIL_SENTINEL_LIVE=1 python3 server.py   # live SAM 3.1 mode (spends credit)

Endpoints:
  GET  /              the web app (webapp/index.html)
  GET  /api/status    mode (stub|live), call budget, hazard concepts v1
  POST /api/scan      demo: {frame_index | timestamp, mode, scene?, reset?}
                      -> stub SAM + triage for one fixture frame
                      live: {image: data URL, concepts?: [hazard keys]}
                      -> real SAM 3.1 per concept (parallel) + triage

Live mode is OPT-IN ONLY (TRAIL_SENTINEL_LIVE=1). The default stays on the
stub so nothing can spend credit accidentally. The server never reads the
Meta credential: live calls go RealSAMClient -> MetaSAMTransport ->
connector helper subprocess, and every concept call is counted by the
shared CallBudget before it is sent.
"""
from __future__ import annotations

import base64
import binascii
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from trail_sentinel.config import (
    HAZARD_BY_KEY,
    HAZARDS,
    BudgetExceeded,
    CallBudget,
    register_custom_hazard,
)
from trail_sentinel.meta_transport import (
    MetaSAMTransport,
    ground_plane_distance_estimator,
    resolve_helper_path,
)
from trail_sentinel.sam_client import (
    Detection,
    HazardPrompt,
    RealSAMClient,
    SegmentRequest,
    StubSAMClient,
)
from trail_sentinel.triage import COOLDOWN_FRAMES, evaluate
from trail_sentinel.vision_router import (
    AVAILABLE_MODELS,
    DEFAULT_MODEL_ID,
    MODEL_BY_ID,
    get_adc_access_token,
    scan_with_vertex_vision,
)

ROOT = Path(__file__).parent
WEBAPP = ROOT / "webapp"
DEFAULT_SCENE = "hero_snake_leaves"
FPS = 10.0

# --- Live-mode guardrails ---------------------------------------------------
# One SAM call takes ~3s and costs USD 0.0025 per concept. The server-side
# minimum interval caps the live scan rate regardless of client behaviour;
# the per-call timeout follows PRD 9.4 (10s, the tick then fails honestly).
LIVE_ENABLED = os.environ.get("TRAIL_SENTINEL_LIVE", "1") == "1"
LIVE_MIN_INTERVAL_S = float(os.environ.get("LIVE_MIN_INTERVAL_S", "0.20"))
LIVE_CALL_TIMEOUT_S = 10.0
# Same span as the stub cooldown (COOLDOWN_FRAMES at FPS), in wall-clock
# seconds: repeat voice alerts for one track stay at least this far apart.
LIVE_ALERT_COOLDOWN_S = COOLDOWN_FRAMES / FPS
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_BODY_BYTES = 16 * 1024 * 1024
_IMAGE_MEDIA_TYPES = ("image/jpeg", "image/png", "image/webp")
_active_model_id = os.environ.get("TRAIL_SENTINEL_MODEL", DEFAULT_MODEL_ID)

_sam = StubSAMClient(ROOT / "fixtures")
_budget = CallBudget(
    counter_path=Path(
        os.environ.get("CALL_COUNTER_FILE", str(ROOT / ".call_counter.json"))
    )
)
_lock = threading.Lock()
_prev_by_track: dict[str, Detection] = {}
_last_alert_frame: dict[str, int] = {}


def _label(concept: str) -> str:
    return next(h.name_ko for h in HAZARDS if h.key == concept)


def _severity(concept: str) -> int:
    return next(h.severity for h in HAZARDS if h.key == concept)


def _detection_payload(d: Detection, verify_ko: str | None = None) -> dict:
    payload = {
        "concept": d.concept,
        "label_ko": _label(d.concept),
        "distance_m": d.distance_m,
        "clock_direction": d.clock_direction,
        "bbox_norm": d.bbox,
        "severity": _severity(d.concept),
        "confidence": d.confidence,
    }
    if verify_ko:
        payload["verify_ko"] = verify_ko
    if d.mask_png and d.mask_rect:
        payload["mask_png"] = d.mask_png
        payload["mask_rect"] = d.mask_rect
    return payload


def _alert_payload(decision) -> dict:
    sev = _severity(decision.detection.concept)
    return {
        "text_ko": decision.phrase,
        "level": "danger" if sev == 3 else "caution",
        "concept": decision.detection.concept,
        "score": decision.score,
    }


def scan_frame(scene: str, frame_idx: int, reset: bool = False) -> dict:
    """One frame through stub SAM -> triage. Adapter over the package logic."""
    with _lock:
        if reset:
            _prev_by_track.clear()
            _last_alert_frame.clear()
        try:
            _budget.spend(1)
        except BudgetExceeded:
            return {"error": "daily_call_cap_reached", "detections": [],
                    "alert": None, "calls_today": _budget.used_today(),
                    "cap": _budget.daily_cap}
        detections = _sam.segment(scene, frame_idx)
        decision = evaluate(detections, _prev_by_track, fps=FPS)
        for det in detections:
            _prev_by_track[det.track_id] = det

        alert = None
        if decision is not None:
            track = decision.detection.track_id
            if frame_idx - _last_alert_frame.get(track, -10**9) >= COOLDOWN_FRAMES:
                _last_alert_frame[track] = frame_idx
                alert = _alert_payload(decision)

        return {
            "frame_index": frame_idx,
            "detections": [_detection_payload(d) for d in detections],
            "alert": alert,
            "calls_today": _budget.used_today(),
            "cap": _budget.daily_cap,
        }


# --- Live path ---------------------------------------------------------------

def filter_concepts(concepts) -> list[str]:
    """Restrict requested concepts to the frozen v1 hazard set.

    Missing/empty means "all six". Unknown keys are dropped silently here
    and the scan simply covers fewer concepts; the response shows which
    concepts actually produced detections.
    """
    if not concepts:
        return [h.key for h in HAZARDS]
    wanted = {c for c in concepts if isinstance(c, str)}
    return [h.key for h in HAZARDS if h.key in wanted]


def decode_image_data_url(value) -> tuple[bytes, str]:
    """Decode a base64 image data URL -> (bytes, media type)."""
    if not isinstance(value, str) or ";base64," not in value:
        raise ValueError("image must be a base64 data URL")
    header, _, encoded = value.partition(";base64,")
    media_type = header.removeprefix("data:")
    if media_type not in _IMAGE_MEDIA_TYPES:
        raise ValueError(f"unsupported image media type: {media_type or '?'}")
    try:
        data = base64.b64decode(encoded, validate=True)
    except binascii.Error as exc:
        raise ValueError("image is not valid base64") from exc
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError(f"image size out of range ({len(data)} bytes)")
    return data, media_type


class LiveScanner:
    """Live scans: supports both multi-model single-pass vision and per-concept SAM.

    When ``vision_fn`` is configured (production server), scans run in a
    single fast pass for the selected Meta AI model (``sam-3.1-hybrid``,
    ``muse-spark-1.3``, ``muse-wonder-1.0``, ``muse-glimmer``) spending
    1 CallBudget unit per scan, or fan out per concept via ``self._client``
    when ``model == 'sam-3.1'`` and the local connector helper is present
    (or when ``vision_fn`` is ``None`` in unit tests).
    """

    def __init__(self, client, budget: CallBudget, *,
                 min_interval_s: float = LIVE_MIN_INTERVAL_S,
                 vision_fn=None):
        self._client = client
        self._budget = budget
        self._min_interval_s = min_interval_s
        self._vision_fn = vision_fn
        self._lock = threading.Lock()
        self._last_start: float | None = None
        self._prev_scan_start: float | None = None
        self._prev: dict[str, Detection] = {}
        self._last_alert_at: dict[str, float] = {}
        self._seq = 0

    def scan(self, image_bytes: bytes, media_type: str, concepts, *,
             model: str | None = None) -> dict:
        keys = filter_concepts(concepts)
        chosen_model = (
            model if model in MODEL_BY_ID else _active_model_id
        )
        base = {"mode": "live", "model": chosen_model,
                "calls_today": self._budget.used_today(),
                "cap": self._budget.daily_cap}
        if not keys:
            return {**base, "error": "no_valid_concepts",
                    "detections": [], "alert": None}

        now = time.monotonic()
        with self._lock:
            if (self._last_start is not None
                    and now - self._last_start < self._min_interval_s):
                retry_ms = int(
                    (self._min_interval_s - (now - self._last_start)) * 1000
                )
                return {**base, "error": "scan_too_soon",
                        "retry_after_ms": retry_ms,
                        "detections": [], "alert": None}
            self._last_start = now

        use_single_pass_vision = (
            self._vision_fn is not None
            and not (
                chosen_model == "sam-3.1" and resolve_helper_path().is_file()
            )
        )
        needed_budget = 1 if use_single_pass_vision else len(keys)

        # Pre-flight: refuse before any provider call if the whole scan
        # cannot fit in today's cap. Mid-scan races still hard-stop in
        # CallBudget.spend per concept call.
        if self._budget.used_today() + needed_budget > self._budget.daily_cap:
            return {**base, "error": "daily_call_cap_reached",
                    "detections": [], "alert": None}

        started = time.monotonic()
        self._seq += 1
        seq = self._seq

        detections: list[Detection] = []
        verify_notes: dict[str, str] = {}
        errors: list[str] = []
        budget_hit = False

        if use_single_pass_vision:
            try:
                self._budget.spend(1)
                detections, verify_notes = self._vision_fn(
                    image_bytes,
                    media_type,
                    keys,
                    frame_idx=seq,
                    model_id=chosen_model,
                )
            except BudgetExceeded:
                budget_hit = True
            except Exception as exc:
                errors.append(f"{chosen_model}: {exc}")
        else:
            def run_concept(key: str) -> list[Detection]:
                hazard = HAZARD_BY_KEY[key]
                request = SegmentRequest.for_image(
                    image_bytes,
                    frame_idx=seq,
                    image_media_type=media_type,
                    prompts=(HazardPrompt(key=key, text=hazard.prompt),),
                )
                return self._client.segment_request(request)

            with ThreadPoolExecutor(max_workers=len(keys)) as pool:
                futures = {pool.submit(run_concept, key): key for key in keys}
                for future in as_completed(futures):
                    key = futures[future]
                    try:
                        detections.extend(future.result())
                    except BudgetExceeded:
                        budget_hit = True
                    except Exception as exc:  # timeout, helper or API failure
                        errors.append(f"{key}: {exc}")

        latency_ms = int((time.monotonic() - started) * 1000)
        model_info = MODEL_BY_ID.get(chosen_model, MODEL_BY_ID[DEFAULT_MODEL_ID])
        base = {"mode": "live", "model": chosen_model,
                "model_label": model_info["short_label"],
                "frame_index": seq, "latency_ms": latency_ms,
                "calls_today": self._budget.used_today(),
                "cap": self._budget.daily_cap}

        if not detections:
            if errors:
                return {**base, "error": "live_scan_failed",
                        "detail": "; ".join(errors),
                        "detections": [], "alert": None}
            if budget_hit:
                return {**base, "error": "daily_call_cap_reached",
                        "detections": [], "alert": None}

        detections.sort(key=lambda d: (-_severity(d.concept), d.concept))

        # Approach speed from the measured wall-clock interval between
        # scans: consecutive live frame indices differ by 1, so the
        # equivalent fps is 1 / dt (triage itself is unchanged).
        with self._lock:
            if self._prev_scan_start is None:
                fps = FPS
            else:
                fps = 1.0 / max(0.1, started - self._prev_scan_start)
            decision = evaluate(detections, self._prev, fps=fps)
            for det in detections:
                self._prev[det.track_id] = det
            self._prev_scan_start = started

            alert = None
            if decision is not None:
                track = decision.detection.track_id
                last = self._last_alert_at.get(track)
                if last is None or started - last >= LIVE_ALERT_COOLDOWN_S:
                    self._last_alert_at[track] = started
                    alert = _alert_payload(decision)

        result = {
            **base,
            "detections": [
                _detection_payload(d, verify_notes.get(d.track_id))
                for d in detections
            ],
            "alert": alert,
        }
        if errors:
            result["partial_errors"] = errors
        return result


def _make_live_scanner() -> LiveScanner:
    transport = MetaSAMTransport(timeout=LIVE_CALL_TIMEOUT_S)
    client = RealSAMClient(
        transport=transport,
        budget=_budget,
        enabled=True,
        distance_estimator=ground_plane_distance_estimator,
    )
    return LiveScanner(client, _budget, vision_fn=scan_with_vertex_vision)


_live_scanner = _make_live_scanner() if LIVE_ENABLED else None
if LIVE_ENABLED:
    threading.Thread(target=lambda: get_adc_access_token(), daemon=True).start()


def status() -> dict:
    return {
        "mode": "live" if LIVE_ENABLED else "stub",
        "engine": _active_model_id if LIVE_ENABLED else "stub",
        "live_enabled": LIVE_ENABLED,
        "calls_today": _budget.used_today(),
        "daily_cap": _budget.daily_cap,
        "default_model": _active_model_id,
        "models": list(AVAILABLE_MODELS),
        "hazards": [
            {
                "key": h.key,
                "label_ko": h.name_ko,
                "prompt": h.prompt,
                "zone": h.zone,
                "severity": h.severity,
            }
            for h in HAZARDS
        ],
    }


def add_concept(body: dict) -> tuple[dict, int]:
    """Register a custom hazard concept at runtime without retraining (PRD F7)."""
    try:
        hazard = register_custom_hazard(
            name_ko=str(body.get("name_ko") or body.get("label_ko") or ""),
            prompt=body.get("prompt"),
            key=body.get("key"),
            zone=str(body.get("zone") or "front"),
            severity=int(body.get("severity") or 2),
        )
    except (ValueError, TypeError) as exc:
        return {"error": "bad_concept", "detail": str(exc)}, 400
    return {
        "added": {
            "key": hazard.key,
            "label_ko": hazard.name_ko,
            "prompt": hazard.prompt,
            "zone": hazard.zone,
            "severity": hazard.severity,
        },
        "hazards": status()["hazards"],
    }, 200


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEBAPP), **kwargs)

    def log_message(self, *args):  # keep the console quiet
        pass

    def _json(self, payload: dict, code: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/status":
            self._json(status())
        elif self.path == "/hero_snake_leaves_01.jpg":
            hero_img = ROOT / "eval" / "data" / "hero_snake_leaves_01.jpg"
            if hero_img.is_file():
                data = hero_img.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_error(404)
        else:
            super().do_GET()

    def do_POST(self):
        if self.path not in ("/api/scan", "/api/concepts"):
            self._json({"error": "not_found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > MAX_BODY_BYTES:
                self._json({"error": "body_too_large"}, 413)
                return
            body = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._json({"error": "bad_json"}, 400)
            return
        if self.path == "/api/concepts":
            payload, code = add_concept(body)
            self._json(payload, code)
            return
        if "image" in body:
            self._scan_live(body)
            return
        frame_idx = body.get("frame_index")
        if frame_idx is None:  # derive from timestamp: 5 virtual fps, loop 0..60
            frame_idx = int(float(body.get("timestamp", 0)) * 5) % 61
        scene = body.get("scene", DEFAULT_SCENE)
        if scene not in _sam.scenes():
            self._json({"error": f"unknown_scene: {scene}"}, 400)
            return
        result = scan_frame(scene, int(frame_idx), reset=bool(body.get("reset")))
        self._json(result, 429 if "error" in result else 200)

    def _scan_live(self, body: dict) -> None:
        if _live_scanner is None:
            self._json({
                "error": "live_not_enabled", "mode": "stub",
                "detail": "server is in stub mode; start it with "
                          "TRAIL_SENTINEL_LIVE=1 for live SAM scans",
                "detections": [], "alert": None,
                "calls_today": _budget.used_today(), "cap": _budget.daily_cap,
            }, 503)
            return
        try:
            image_bytes, media_type = decode_image_data_url(body.get("image"))
        except ValueError as exc:
            self._json({"error": "bad_image", "detail": str(exc),
                        "detections": [], "alert": None}, 400)
            return
        result = _live_scanner.scan(
            image_bytes,
            media_type,
            body.get("concepts"),
            model=body.get("model"),
        )
        code = 200
        if result.get("error") in ("daily_call_cap_reached", "scan_too_soon"):
            code = 429
        elif result.get("error") == "live_scan_failed":
            code = 502
        elif result.get("error") == "no_valid_concepts":
            code = 400
        self._json(result, code)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8765"))
    mode = "live (real SAM 3.1)" if LIVE_ENABLED else "stub"
    print(f"Trail Sentinel web app → http://localhost:{port}  (mode: {mode})")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
