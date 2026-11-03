"""Live Meta SAM 3.1 transport for ``RealSAMClient`` (subprocess boundary).

Architecture rule: the Meta Model API credential never enters this project.
It lives only in the Secure Vault connection ``custom.meta-model-api``. This
module therefore never builds a provider request itself. For live work it
shells out to the connector helper
(``~/workspace/custom-connectors/custom.meta-model-api/bin/meta_model_api.py``),
which attaches an ``hsurr:`` surrogate to its own requests. This module only
maps the helper's JSON output into the project-normalized records that
``RealSAMClient`` consumes.

Verified live on 2026-10-31 (see the connector's API_RESEARCH.md):

- ``GET /v1/models`` lists ``sam-3.1`` (auth OK).
- One ``segment-image`` call on the hero copperhead still with prompt
  ``snake`` returned one box + mask record in 3.0 s.

Wire facts that shape the mapping below:

- SAM returns boxes in the image's own pixel space. The record's ``w``/``h``
  fields are the FRAME (image) dimensions, not the box size, so the
  normalized bbox is ``[x1/w, y1/h, (x2-x1)/w, (y2-y1)/h]``.
- SAM returns NO confidence and NO distance. Records produced here omit
  ``confidence`` (``Detection.confidence`` becomes ``None``; nothing is
  invented) and omit ``distance_m`` — pair this transport with
  :func:`ground_plane_distance_estimator` on ``RealSAMClient``.

Cost note: SAM takes one concept prompt per provider request, so
``MetaSAMTransport.segment`` makes one helper call (one image charge,
USD 2.50 / 1,000 images) per prompt in the request. ``RealSAMClient`` spends
one ``CallBudget`` unit per ``segment_request`` invocation, so callers that
need per-concept accounting should issue one request per concept (the web
server's live path does exactly that).

Masks: when Meta's ``meta-sam-parser`` package is importable (installed
into ``tools/pylibs``), the transport also decodes each record's one-bit
mask from the helper's raw stream (``--save-raw``) into a small RGBA PNG
data URL plus its normalised frame rect, attached to the record as
``mask_png`` / ``mask_rect``. Mask decoding is best-effort: any failure
falls back to bbox-only records, never to a failed scan.
"""
from __future__ import annotations

import base64
import importlib.util
import json
import math
import os
import re
import struct
import subprocess
import sys
import tempfile
import zlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .config import HAZARD_BY_KEY
from .sam_client import SegmentRequest

#: Built-in location of the connector helper on the development VM. The
#: credential lives in that connector's Secure Vault connection, never in
#: this project, so a fresh clone has NO live path until the helper is
#: present (or pointed to) — live mode then still defaults to off.
DEFAULT_HELPER_PATH = (
    Path.home()
    / "workspace/custom-connectors/custom.meta-model-api/bin/meta_model_api.py"
)

#: Backwards-compatible alias for the built-in default helper location.
HELPER_PATH = DEFAULT_HELPER_PATH

#: Environment variable that overrides the connector helper location.
HELPER_ENV_VAR = "TRAIL_SENTINEL_META_HELPER"


class HelperNotConfiguredError(RuntimeError):
    """The Meta connector helper is missing: live SAM is not configured."""


def resolve_helper_path(explicit: Path | str | None = None) -> Path:
    """Helper path precedence: explicit argument > $TRAIL_SENTINEL_META_HELPER
    > built-in default. The path is returned as-is; existence is checked by
    :func:`require_helper` so the failure message names the remedy."""

    if explicit is not None:
        return Path(explicit)
    env_value = os.environ.get(HELPER_ENV_VAR, "").strip()
    if env_value:
        return Path(env_value).expanduser()
    return DEFAULT_HELPER_PATH


def require_helper(path: Path) -> Path:
    """Return ``path`` if the helper exists, else fail with a clear
    "not configured" error (live SAM stays unusable, never half-wired)."""

    if not path.is_file():
        raise HelperNotConfiguredError(
            f"Meta connector helper not configured: {path} does not exist. "
            f"Live SAM requires the custom.meta-model-api connector helper; "
            f"set {HELPER_ENV_VAR} to its meta_model_api.py path. "
            "Demo/stub mode works without it."
        )
    return path

_MEDIA_SUFFIXES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

# === [FEAT:F3] Ground-plane distance heuristic ===============================
# --- Ground-plane distance heuristic (ESTIMATE — read before trusting) ------
#
# SAM gives no distance, so live detections need an estimated one. Model: the
# phone is held about 1.3 m above the trail, pitched down; hazards rest on
# the ground plane, so the image row where a box meets the ground (its bottom
# edge) moves monotonically toward the frame bottom as the hazard gets
# closer. We map the normalized bottom position ``b`` through
#
#     distance = D_MIN + (D_MAX - D_MIN) * ((1 - b) / (1 - HORIZON)) ** 2
#
# with HORIZON the row where the ground visually vanishes and D_MIN/D_MAX
# clamping the range. A very tall box (relative height) is additionally
# capped, because a ground object filling half the frame height cannot be
# far away. These constants are UNCALIBRATED placeholders chosen to be
# plausible for a downward phone camera — they are an estimate for triage
# prioritisation, not a measurement, and must be calibrated against ranged
# test shots before any number is quoted as accuracy.
_HORIZON_BOTTOM = 0.30
_D_MIN_M = 0.7
_D_MAX_M = 12.0
_TALL_BOX_HEIGHT = 0.5
_TALL_BOX_MAX_M = 2.0


def ground_plane_distance_estimator(
    record: Mapping[str, Any], request: SegmentRequest
) -> float:
    """Estimate distance_m from a normalized record's bbox (see module note).

    Matches the ``DistanceEstimator`` signature used by ``RealSAMClient``.
    """

    _x, y, _w, h = (float(v) for v in record["bbox"])
    bottom = min(1.0, max(0.0, y + h))
    span = max(1e-6, 1.0 - _HORIZON_BOTTOM)
    ratio = min(1.0, max(0.0, (1.0 - bottom) / span))
    distance = _D_MIN_M + (_D_MAX_M - _D_MIN_M) * ratio * ratio
    if h >= _TALL_BOX_HEIGHT:
        distance = min(distance, _TALL_BOX_MAX_M)
    return round(distance, 2)


_SAM_RECORD_RE = re.compile(
    r"<(\d+)f>([^<]+)<\|box;([^|]+)\|>(?:<\|mask;([^|]+)\|>)?",
)


class _BuiltinHelperParser:
    """Built-in pure-text fallback when the external helper script is absent."""

    @staticmethod
    def extract_output_text(raw: str) -> str:
        deltas: list[str] = []
        for line in raw.splitlines():
            line = line.strip()
            if not line.startswith("data:"):
                continue
            payload_str = line[5:].strip()
            if not payload_str or payload_str == "[DONE]":
                continue
            try:
                event = json.loads(payload_str)
            except json.JSONDecodeError:
                continue
            etype = event.get("type")
            if etype == "response.output_text.done" and isinstance(event.get("text"), str):
                return event["text"]
            if etype == "response.output_text.delta" and isinstance(event.get("delta"), str):
                deltas.append(event["delta"])
            if etype == "response.completed":
                for item in (event.get("response") or {}).get("output") or []:
                    for part in item.get("content") or []:
                        if isinstance(part.get("text"), str) and part["text"]:
                            return part["text"]
        if deltas:
            return "".join(deltas)
        return raw

    @staticmethod
    def parse_sam_output(output_text: str) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for match in _SAM_RECORD_RE.finditer(output_text):
            frame_str, object_id, box_body, mask_body = match.groups()
            box_kv: dict[str, float] = {}
            for pair in box_body.split(";"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    box_kv[k.strip()] = float(v.strip())
            mask_data = ""
            if mask_body:
                for pair in mask_body.split(";"):
                    if pair.startswith("data="):
                        mask_data = pair[5:]
                        break
            records.append(
                {
                    "frame": int(frame_str),
                    "object_id": object_id.strip(),
                    "x1": box_kv["x1"],
                    "y1": box_kv["y1"],
                    "x2": box_kv["x2"],
                    "y2": box_kv["y2"],
                    "w": box_kv.get("w"),
                    "h": box_kv.get("h"),
                    "mask_present": bool(mask_body),
                    "mask_data_len": len(mask_data),
                }
            )
        return records


def load_helper_parser() -> Any:
    """Import the connector helper module to reuse its SAM output parser.

    Importing the helper does not touch the credential: authd is only
    contacted when the helper builds a request, and the parser functions
    (``extract_output_text`` / ``parse_sam_output``) are pure text work.
    Falls back to the built-in pure-text parser when the external helper
    script is not installed on the current machine.
    """

    candidate = resolve_helper_path()
    if not candidate.is_file():
        return _BuiltinHelperParser
    helper = require_helper(candidate)
    spec = importlib.util.spec_from_file_location(
        "meta_model_api_helper", helper
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load connector helper at {helper}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_helper_parser_cache: Any = None


def _helper_parser() -> Any:
    global _helper_parser_cache
    if _helper_parser_cache is None:
        _helper_parser_cache = load_helper_parser()
    return _helper_parser_cache


# --- Mask decoding (best-effort; bbox-only fallback) -------------------------
#
# The helper's JSON summary reports masks by length only, so the transport
# asks the helper to save the raw streamed body (--save-raw) and decodes the
# one-bit masks here with Meta's meta-sam-parser, vendored into
# tools/pylibs. Each mask raster is a crop sized to its record bounds; the
# PNG returned is downscaled to <= _MASK_MAX_DIM px and tinted with the
# concept's severity colour at _MASK_ALPHA, so the frontend can draw it
# directly over the bounds rect.
_PARSER_LIB_DIR = Path(__file__).resolve().parent.parent / "tools" / "pylibs"
_MASK_MAX_DIM = 256
_MASK_ALPHA = 170
_SEVERITY_RGB = {3: (255, 59, 48), 2: (255, 149, 0), 1: (255, 214, 10)}

_sam_parser_cache: Any = None
_sam_parser_tried = False


def _load_sam_parser() -> Any:
    global _sam_parser_cache, _sam_parser_tried
    if _sam_parser_tried:
        return _sam_parser_cache
    _sam_parser_tried = True
    try:
        if _PARSER_LIB_DIR.is_dir() and str(_PARSER_LIB_DIR) not in sys.path:
            sys.path.insert(0, str(_PARSER_LIB_DIR))
        import meta_sam_parser

        _sam_parser_cache = meta_sam_parser
    except Exception:
        _sam_parser_cache = None
    return _sam_parser_cache


def _png_rgba(width: int, height: int, rows: list[bytes]) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    raw = b"".join(b"\x00" + row for row in rows)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def masks_from_output_text(
    output_text: str,
    *,
    concept: str,
    frame_w: float | None,
    frame_h: float | None,
) -> dict[str, dict[str, Any]]:
    """Decode masks from SAM output text -> {object_id: mask_png/mask_rect}.

    Returns {} when the parser package is unavailable, the frame size is
    unknown, or parsing fails — masks are decoration on top of the boxes,
    never a reason to fail a scan.
    """

    msp = _load_sam_parser()
    if msp is None or not frame_w or not frame_h:
        return {}
    try:
        parser = msp.image_segmentation_format().create_parser()
        parser.push(output_text)
        finish = parser.finish(msp.CompletedOutcome())
        result = getattr(finish, "result", finish)
        red, green, blue = _SEVERITY_RGB[HAZARD_BY_KEY[concept].severity]
        out: dict[str, dict[str, Any]] = {}
        for record in result.records:
            if not isinstance(record, msp.SegmentationMaskRecord):
                continue
            mask = record.mask
            mw, mh = int(mask.width), int(mask.height)
            raster = msp.decode_mask_to_raster(mask)
            if mw <= 0 or mh <= 0 or len(raster) != mw * mh:
                continue
            step = max(1, math.ceil(max(mw, mh) / _MASK_MAX_DIM))
            dw, dh = math.ceil(mw / step), math.ceil(mh / step)
            rows: list[bytes] = []
            for yy in range(dh):
                sampled = raster[yy * step * mw : yy * step * mw + mw : step]
                row = bytearray()
                for value in sampled:
                    row += bytes((red, green, blue, _MASK_ALPHA if value else 0))
                rows.append(bytes(row))
            bounds = record.bounds
            out[str(record.object_id)] = {
                "mask_png": "data:image/png;base64,"
                + base64.b64encode(_png_rgba(dw, dh, rows)).decode("ascii"),
                "mask_rect": [
                    round(bounds.left / frame_w, 4),
                    round(bounds.top / frame_h, 4),
                    round((bounds.right - bounds.left) / frame_w, 4),
                    round((bounds.bottom - bounds.top) / frame_h, 4),
                ],
            }
        return out
    except Exception:
        return {}


def normalize_record(
    record: Mapping[str, Any], *, concept: str
) -> dict[str, Any]:
    """Map one parsed SAM box record to a project-normalized record.

    Uses the record's ``w``/``h`` as frame dimensions (see module docstring).
    Falls back to a 0..1000 space, then to already-normalized coordinates,
    when frame dimensions are missing. No ``confidence`` and no
    ``distance_m`` are set — SAM does not provide them.
    """

    x1 = float(record["x1"])
    y1 = float(record["y1"])
    x2 = float(record["x2"])
    y2 = float(record["y2"])
    frame_w = record.get("w")
    frame_h = record.get("h")
    if frame_w and frame_h and float(frame_w) > 0 and float(frame_h) > 0:
        scale_x, scale_y = float(frame_w), float(frame_h)
    elif max(x1, y1, x2, y2) > 1.0:
        scale_x = scale_y = 1000.0
    else:
        scale_x = scale_y = 1.0
    nx, ny = x1 / scale_x, y1 / scale_y
    nw, nh = (x2 - x1) / scale_x, (y2 - y1) / scale_y
    center_x = nx + nw / 2.0
    clock_direction = 11 if center_x <= 0.4 else (1 if center_x >= 0.6 else 12)
    return {
        "concept": concept,
        "bbox": [round(nx, 4), round(ny, 4), round(nw, 4), round(nh, 4)],
        "track_id": str(record["object_id"]),
        "clock_direction": clock_direction,
        "frame": int(record.get("frame", 0)),
        "mask_present": bool(record.get("mask_present")),
    }


def records_from_helper_output(
    payload: Mapping[str, Any], *, concept: str
) -> list[dict[str, Any]]:
    """Map a helper ``segment-image`` JSON payload to normalized records."""

    if payload.get("provider_request_sent") is not True:
        raise RuntimeError(f"helper did not send a provider request: {payload}")
    if "error" in payload:
        raise RuntimeError(f"helper segment-image failed: {payload['error']}")
    return [
        normalize_record(record, concept=concept)
        for record in payload.get("records", [])
    ]


class MetaSAMTransport:
    """``SAMTransport`` implementation backed by the connector helper.

    Live path only: each prompt in the request costs one provider image
    call through the helper subprocess. ``timeout`` bounds one helper call.
    Used by ``server.py``'s opt-in live mode.
    """

    def __init__(
        self,
        helper_path: Path | str | None = None,
        timeout: float = 330.0,
    ):
        # Precedence: explicit argument > $TRAIL_SENTINEL_META_HELPER >
        # built-in default (see resolve_helper_path).
        self.helper_path = resolve_helper_path(helper_path)
        self.timeout = timeout

    def segment(self, request: SegmentRequest) -> list[dict[str, Any]]:
        if request.image_bytes is None:
            raise ValueError(
                "MetaSAMTransport supports image_bytes requests only; "
                "video and source references are not wired"
            )
        require_helper(self.helper_path)
        suffix = _MEDIA_SUFFIXES.get(request.image_media_type or "", ".img")
        records: list[dict[str, Any]] = []
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(request.image_bytes)
            tmp_path = Path(tmp.name)
        try:
            for prompt in request.prompts:
                with tempfile.NamedTemporaryFile(
                    suffix=".sse", delete=False
                ) as raw_tmp:
                    raw_path = Path(raw_tmp.name)
                try:
                    payload = self._run_helper(tmp_path, prompt.text, raw_path)
                    mapped = records_from_helper_output(
                        payload, concept=prompt.key
                    )
                    masks = self._masks_for(payload, raw_path, prompt.key)
                    for record in mapped:
                        mask = masks.get(record["track_id"])
                        if mask:
                            record.update(mask)
                        # Object ids repeat across separate per-prompt
                        # requests; prefix with the concept so tracks
                        # stay distinct.
                        record["track_id"] = f"{prompt.key}-{record['track_id']}"
                    records.extend(mapped)
                finally:
                    raw_path.unlink(missing_ok=True)
        finally:
            tmp_path.unlink(missing_ok=True)
        return records

    def _masks_for(
        self, payload: Mapping[str, Any], raw_path: Path, concept: str
    ) -> dict[str, dict[str, Any]]:
        """Best-effort mask decode from the helper's saved raw stream."""

        try:
            raw_text = raw_path.read_text(encoding="utf-8", errors="replace")
            if not raw_text:
                return {}
            output_text = _helper_parser().extract_output_text(raw_text)
            payload_records = payload.get("records") or []
            frame_w = payload_records[0].get("w") if payload_records else None
            frame_h = payload_records[0].get("h") if payload_records else None
            return masks_from_output_text(
                output_text,
                concept=concept,
                frame_w=frame_w,
                frame_h=frame_h,
            )
        except Exception:
            return {}

    def _run_helper(
        self, image_path: Path, prompt_text: str, raw_path: Path
    ) -> dict[str, Any]:
        completed = subprocess.run(
            [
                sys.executable,
                str(self.helper_path),
                "segment-image",
                str(image_path),
                prompt_text,
                "--timeout",
                str(self.timeout),
                "--save-raw",
                str(raw_path),
            ],
            capture_output=True,
            text=True,
            timeout=self.timeout + 5.0,
            check=False,
        )
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"connector helper returned non-JSON output "
                f"(exit {completed.returncode}): {completed.stdout[:500]}"
            ) from exc
        if completed.returncode != 0:
            raise RuntimeError(f"connector helper failed: {payload}")
        return payload
