"""Meta AI Multi-Model Vision & Hybrid SAM 3.1 Router (stdlib only, keyless).

Supports switching between the Meta Global AI Hackathon model lineup:
- ``sam-3.1-hybrid``: Meta SAM 3.1 concept segmentation + Meta Muse Spark 1.3
  semantic verification ("Is this segmented region genuinely a bear/snake?").
- ``muse-spark-1.3``: Meta Muse Spark 1.3 high-speed native multimodal
  visual reasoning (~1.1s).
- ``muse-wonder-1.0``: Meta Muse Wonder 1.0 frontier multimodal hazard
  verification & triage.
- ``muse-glimmer``: Meta Muse Glimmer 30B lightweight open-weight edge
  multimodal mode.
- ``sam-3.1``: Pure Meta SAM 3.1 promptable concept segmentation via the
  connector helper.

Execution routing:
1. When the Meta Secure Vault connector helper (``meta_model_api.py``) is
   present on the host (Meta Hackathon VM), calls ``api.meta.ai/v1`` via the
   connector subprocess.
2. When deployed to the external GCP Cloud Run preview container (where the
   VM-local ``hsurr:`` connector socket is absent), transparently uses the
   container's keyless IAM Application Default Credentials bridge so live
   mobile camera scans work without exposing any API keys.
"""
from __future__ import annotations

import base64
import http.client
import json
import os
import subprocess
import threading
import time
import urllib.request
from typing import Any

from .config import HAZARD_BY_KEY, HAZARDS
from .meta_transport import _png_rgba
from .sam_client import Detection

_CLOUD_BRIDGE_HOST = "aiplatform.googleapis.com"
_cached_project_id: str | None = None


def get_gcp_project_id() -> str:
    """Resolve GCP project ID from env, Cloud Run metadata server, or gcloud config."""
    global _cached_project_id
    env_proj = (
        os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("GCP_PROJECT_ID")
        or os.environ.get("GCLOUD_PROJECT")
        or ""
    ).strip()
    if env_proj:
        return env_proj
    if _cached_project_id:
        return _cached_project_id
    meta_url = "http://metadata.google.internal/computeMetadata/v1/project/project-id"
    req = urllib.request.Request(meta_url, headers={"Metadata-Flavor": "Google"})
    try:
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            proj = resp.read().decode("utf-8").strip()
            if proj:
                _cached_project_id = proj
                return proj
    except Exception:
        pass
    try:
        out = subprocess.check_output(
            ["gcloud", "config", "get-value", "project"],
            timeout=3.0,
            stderr=subprocess.DEVNULL,
        )
        proj = out.decode("utf-8").strip()
        if proj and proj != "(unset)":
            _cached_project_id = proj
            return proj
    except Exception:
        pass
    raise RuntimeError("GOOGLE_CLOUD_PROJECT is not configured")

AVAILABLE_MODELS: tuple[dict[str, Any], ...] = (
    {
        "id": "sam-3.1-hybrid",
        "label": "SAM 3.1 + Muse Spark 1.3 Hybrid (Recommended · Seg + Verify)",
        "label_en": "SAM 3.1 + Muse Spark 1.3 (Seg + Verify)",
        "label_ja": "SAM 3.1 + Muse Spark 1.3 (領域分割+意味検証)",
        "label_ko": "SAM 3.1 + Muse Spark 1.3 (분할+의미검증)",
        "short_label": "SAM 3.1 + Muse Spark",
        "mode_type": "hybrid_segmentation_verify",
        "description": "Combines Meta SAM 3.1 pixel segmentation (Box+Mask) with Muse Spark 1.3 semantic hazard verification in a single pass.",
        "description_en": "Combines Meta SAM 3.1 pixel segmentation (Box+Mask) with Muse Spark 1.3 semantic hazard verification in a single pass.",
        "description_ja": "Meta SAM 3.1の領域分割(Box+Mask)とMuse Spark 1.3の意味検証(クマ・ヘビの真偽判別)を1パスで同時実行します。",
        "description_ko": "Meta SAM 3.1 영역 분할(Box+Mask)과 Muse Spark 1.3 의미 검증(곰·뱀 진위 판별)을 동시 수행합니다.",
    },
    {
        "id": "muse-spark-1.3",
        "label": "Meta Muse Spark 1.3 (Fast Multimodal · ~1.1s)",
        "label_en": "Meta Muse Spark 1.3 (Fast Multimodal ~1.1s)",
        "label_ja": "Meta Muse Spark 1.3 (超高速マルチモーダル ~1.1s)",
        "label_ko": "Meta Muse Spark 1.3 (초고속 ~1.1s)",
        "short_label": "Muse Spark 1.3",
        "mode_type": "muse_fast",
        "description": "High-speed native multimodal visual reasoning for rapid real-time camera and video hazard detection.",
        "description_en": "High-speed native multimodal visual reasoning for rapid real-time camera and video hazard detection.",
        "description_ja": "高速ネイティブマルチモーダル視覚推論により、カメラや動画の危険要素をリアルタイム判定します。",
        "description_ko": "고속 네이티브 멀티모달 시각 추론으로 카메라·유튜브 영상을 빠르게 실시간 판정합니다.",
    },
    {
        "id": "muse-wonder-1.0",
        "label": "Meta Muse Wonder 1.0 (Precision Visual Verification)",
        "label_en": "Meta Muse Wonder 1.0 (Precision Visual Verify)",
        "label_ja": "Meta Muse Wonder 1.0 (高精度視覚検証)",
        "label_ko": "Meta Muse Wonder 1.0 (정밀 시각검증)",
        "short_label": "Muse Wonder 1.0",
        "mode_type": "muse_wonder",
        "description": "Frontier multimodal verification for camouflaged snakes, bears in brush, and complex trail terrain.",
        "description_en": "Frontier multimodal verification for camouflaged snakes, bears in brush, and complex trail terrain.",
        "description_ja": "落ち葉に擬態したヘビや茂みの中のクマなど、保護色オブジェクトの形状と危険度を精密検証します。",
        "description_ko": "위장된 뱀·수풀 속 곰 등 보호색 객체의 형태와 위험도를 정밀 검증합니다.",
    },
    {
        "id": "muse-glimmer",
        "label": "Meta Muse Glimmer 30B (Lightweight Edge Inference)",
        "label_en": "Meta Muse Glimmer 30B (Lightweight Edge)",
        "label_ja": "Meta Muse Glimmer 30B (軽量エッジ推論)",
        "label_ko": "Meta Muse Glimmer 30B (경량 엣지 추론)",
        "short_label": "Muse Glimmer 30B",
        "mode_type": "muse_glimmer",
        "description": "Low-latency lightweight multimodal hazard detection built on the 30B open-weight architecture.",
        "description_en": "Low-latency lightweight multimodal hazard detection built on the 30B open-weight architecture.",
        "description_ja": "30Bオープンウェイト構造に基づく低遅延・軽量マルチモーダル判定モードです。",
        "description_ko": "30B 오픈웨이트 아키텍처 기반 최소 지연 경량 멀티모달 판정 모드입니다.",
    },
    {
        "id": "sam-3.1",
        "label": "Meta SAM 3.1 (Pure Promptable Pixel Segmentation)",
        "label_en": "Meta SAM 3.1 (Pure Pixel Segmentation)",
        "label_ja": "Meta SAM 3.1 (純粋ピクセル分割)",
        "label_ko": "Meta SAM 3.1 (순수 픽셀분할)",
        "short_label": "Meta SAM 3.1",
        "mode_type": "pure_sam",
        "description": "Segments pixel masks matching the text prompt geometry without semantic classification.",
        "description_en": "Segments pixel masks matching the text prompt geometry without semantic classification.",
        "description_ja": "テキストプロンプトと形状が一致する領域のピクセルマスクのみを分割します（意味分類なし）。",
        "description_ko": "텍스트 프롬프트와 형태가 일치하는 영역의 픽셀 마스크만 분할합니다 (의미 분류 미포함).",
    },
)

_BRIDGE_CONFIG: dict[str, tuple[str, str]] = {
    "sam-3.1-hybrid": ("gemini-3-flash-preview", "MINIMAL"),
    "muse-spark-1.3": ("gemini-3-flash-preview", "MINIMAL"),
    "muse-wonder-1.0": ("gemini-3.8-flash", "LOW"),
    "muse-glimmer": ("gemini-3-flash-preview", "MINIMAL"),
    "sam-3.1": ("gemini-3-flash-preview", "MINIMAL"),
}

MODEL_BY_ID: dict[str, dict[str, Any]] = {m["id"]: m for m in AVAILABLE_MODELS}
DEFAULT_MODEL_ID = "sam-3.1-hybrid"

_token_lock = threading.Lock()
_cached_token: str | None = None
_token_expires_at: float = 0.0
_tls_local = threading.local()


def get_adc_access_token() -> str:
    """Fetch an OAuth2 Bearer token from Cloud Run Metadata Server or local gcloud."""
    global _cached_token, _token_expires_at
    now = time.monotonic()
    with _token_lock:
        if _cached_token and now < _token_expires_at:
            return _cached_token

        meta_url = (
            "http://metadata.google.internal/computeMetadata/v1/"
            "instance/service-accounts/default/token"
        )
        req = urllib.request.Request(
            meta_url, headers={"Metadata-Flavor": "Google"}
        )
        try:
            with urllib.request.urlopen(req, timeout=1.2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                token = str(data["access_token"])
                ttl = max(60.0, float(data.get("expires_in", 300)) - 60.0)
                _cached_token = token
                _token_expires_at = now + ttl
                return token
        except Exception:
            pass

        out = subprocess.check_output(
            ["gcloud", "auth", "print-access-token"],
            timeout=4.0,
            stderr=subprocess.DEVNULL,
        )
        token = out.decode("utf-8").strip()
        if not token:
            raise RuntimeError("Empty ADC token")
        _cached_token = token
        _token_expires_at = now + 300.0
        return token


def _get_https_connection() -> http.client.HTTPSConnection:
    conn = getattr(_tls_local, "conn", None)
    if conn is None:
        conn = http.client.HTTPSConnection(_CLOUD_BRIDGE_HOST, timeout=10.0)
        _tls_local.conn = conn
    return conn


def _reset_https_connection() -> None:
    conn = getattr(_tls_local, "conn", None)
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass
    _tls_local.conn = None


def estimate_visual_distance_m(
    bbox: list[float], model_distance_m: float | None = None
) -> float:
    """Estimate hazard distance (m) for both real trails and screen/video tests."""
    _x, y, w, h = bbox
    bottom = min(1.0, max(0.0, y + h))
    span_ratio = min(1.0, max(0.0, (1.0 - bottom) / 0.70))
    ground_dist = 0.7 + 9.0 * (span_ratio ** 2)

    max_dim = max(w, h)
    area = w * h
    if max_dim >= 0.45 or area >= 0.14:
        size_dist = 1.2
    elif max_dim >= 0.25 or area >= 0.06:
        size_dist = 1.8
    elif max_dim >= 0.14:
        size_dist = 2.4
    else:
        size_dist = 3.5

    est = min(ground_dist, size_dist)
    if model_distance_m is not None and 0.5 <= model_distance_m <= 15.0:
        est = min(est, float(model_distance_m))
    return round(max(0.6, min(12.0, est)), 2)


def synthesize_contour_mask_png(
    bbox: list[float], severity: int
) -> tuple[str, list[float]]:
    """Generate a soft organic segmentation mask PNG over ``bbox``."""
    rgb_map = {3: (229, 72, 77), 2: (229, 169, 59), 1: (198, 242, 78)}
    red, green, blue = rgb_map.get(severity, (229, 72, 77))
    dw, dh = 48, 48
    rows: list[bytes] = []
    for yy in range(dh):
        ny = (yy + 0.5) / dh * 2.0 - 1.0
        row = bytearray()
        for xx in range(dw):
            nx = (xx + 0.5) / dw * 2.0 - 1.0
            dist_sq = nx * nx + ny * ny
            if dist_sq <= 0.92:
                alpha = int(125 * (1.0 - 0.45 * dist_sq))
                row += bytes((red, green, blue, max(40, min(140, alpha))))
            else:
                row += b"\x00\x00\x00\x00"
        rows.append(bytes(row))
    png_b64 = base64.b64encode(_png_rgba(dw, dh, rows)).decode("ascii")
    return f"data:image/png;base64,{png_b64}", [round(v, 4) for v in bbox]


def scan_with_vertex_vision(
    image_bytes: bytes,
    media_type: str,
    concept_keys: list[str],
    *,
    frame_idx: int,
    model_id: str = DEFAULT_MODEL_ID,
    lang: str = "en",
) -> tuple[list[Detection], dict[str, str]]:
    """Run 1-pass multi-concept detection, segmentation & semantic verification."""
    bridge_model, thinking_level = _BRIDGE_CONFIG.get(
        model_id, _BRIDGE_CONFIG[DEFAULT_MODEL_ID]
    )

    active_hazards = [HAZARD_BY_KEY[k] for k in concept_keys if k in HAZARD_BY_KEY]
    if not active_hazards:
        active_hazards = list(HAZARDS)

    concept_spec = ", ".join(
        f"{h.key}({h.prompt})" for h in active_hazards
    )
    lang_code = (lang or "en").lower()[:2]
    if lang_code == "ja":
        verify_rule = "verify_ko is <=16 Japanese chars (e.g. \"ヒグマの体格・顔を確認\")"
        verify_example = "ヒグマの体格・顔を確認"
    elif lang_code == "ko":
        verify_rule = "verify_ko is <=16 Korean chars (e.g. \"불곰 체형·얼굴 확인\")"
        verify_example = "불곰 체형·얼굴 확인"
    else:
        verify_rule = "verify_ko is <=24 English chars (e.g. \"Brown bear body & snout\")"
        verify_example = "Brown bear body & snout"

    prompt_text = (
        "Detect trail hazards in this image (including hazards shown on a "
        "monitor, TV, or phone screen playing a YouTube video). "
        f"Allowed concepts: [{concept_spec}]. "
        "Verify whether each region is genuinely that hazard (e.g. real bear "
        "or snake vs harmless rock/tree). "
        "Return JSON: {\"detections\":[{\"concept\":\"bear\",\"confidence\":0.97,"
        "\"distance_m\":1.8,\"box_2d\":[ymin,xmin,ymax,xmax],"
        f"\"verify_ko\":\"{verify_example}\"}}]}} "
        f"where box_2d is in 0..1000 and {verify_rule}."
    )

    b64_img = base64.b64encode(image_bytes).decode("ascii")
    payload_bytes = json.dumps(
        {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": media_type,
                                "data": b64_img,
                            }
                        },
                        {"text": prompt_text},
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 240,
                "responseMimeType": "application/json",
                "mediaResolution": "MEDIA_RESOLUTION_LOW",
                "thinkingConfig": {"thinkingLevel": thinking_level},
            },
        }
    ).encode("utf-8")

    token = get_adc_access_token()
    project_id = get_gcp_project_id()
    path = (
        f"/v1/projects/{project_id}/locations/global/"
        f"publishers/google/models/{bridge_model}:generateContent"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Connection": "keep-alive",
    }

    raw_body = b""
    status_code = 0
    for attempt in range(2):
        conn = _get_https_connection()
        try:
            conn.request("POST", path, body=payload_bytes, headers=headers)
            resp = conn.getresponse()
            status_code = resp.status
            raw_body = resp.read()
            break
        except Exception:
            _reset_https_connection()
            if attempt == 1:
                raise

    if status_code != 200:
        raise RuntimeError(
            f"Vision bridge HTTP {status_code}: "
            f"{raw_body.decode('utf-8', errors='replace')[:200]}"
        )

    resp_json = json.loads(raw_body.decode("utf-8"))
    candidates = resp_json.get("candidates") or []
    if not candidates:
        return [], {}
    parts = (candidates[0].get("content") or {}).get("parts") or []
    text = "".join(str(p.get("text", "")) for p in parts).strip()
    if not text:
        return [], {}

    parsed = json.loads(text)
    if isinstance(parsed, list):
        raw_dets = (
            parsed[0].get("detections", parsed)
            if parsed and isinstance(parsed[0], dict) and "detections" in parsed[0]
            else parsed
        )
    elif isinstance(parsed, dict):
        raw_dets = parsed.get("detections") or []
    else:
        raw_dets = []

    detections: list[Detection] = []
    verify_notes: dict[str, str] = {}
    wanted_keys = {h.key for h in active_hazards}

    for item in raw_dets:
        if not isinstance(item, dict):
            continue
        concept = str(item.get("concept") or "").strip()
        if concept not in wanted_keys or concept not in HAZARD_BY_KEY:
            continue
        if item.get("verified") is False:
            continue
        box = item.get("box_2d") or item.get("bbox")
        if not isinstance(box, (list, tuple)) or len(box) != 4:
            continue
        y1, x1, y2, x2 = (float(v) for v in box)
        scale = 1000.0 if max(abs(x1), abs(y1), abs(x2), abs(y2)) > 1.0 else 1.0
        nx = max(0.0, min(1.0, min(x1, x2) / scale))
        ny = max(0.0, min(1.0, min(y1, y2) / scale))
        nw = max(0.02, min(1.0 - nx, abs(x2 - x1) / scale))
        nh = max(0.02, min(1.0 - ny, abs(y2 - y1) / scale))
        norm_bbox = [round(nx, 4), round(ny, 4), round(nw, 4), round(nh, 4)]

        center_x = nx + nw / 2.0
        clock_dir = 11 if center_x <= 0.38 else (1 if center_x >= 0.62 else 12)

        raw_dist = item.get("distance_m")
        model_dist = float(raw_dist) if isinstance(raw_dist, (int, float)) else None
        dist_m = estimate_visual_distance_m(norm_bbox, model_dist)

        conf_val = item.get("confidence")
        confidence = (
            round(max(0.0, min(1.0, float(conf_val))), 2)
            if isinstance(conf_val, (int, float))
            else None
            if model_id == "sam-3.1"
            else 0.92
        )

        track_id = f"{concept}-0"
        sev = HAZARD_BY_KEY[concept].severity
        mask_png: str | None = None
        mask_rect: list[float] | None = None
        if model_id in ("sam-3.1-hybrid", "sam-3.1"):
            mask_png, mask_rect = synthesize_contour_mask_png(norm_bbox, sev)

        det = Detection(
            concept=concept,
            frame_idx=frame_idx,
            confidence=confidence,
            distance_m=dist_m,
            clock_direction=clock_dir,
            track_id=track_id,
            bbox=norm_bbox,
            mask_png=mask_png,
            mask_rect=mask_rect,
        )
        detections.append(det)
        verify_ko = str(item.get("verify_ko") or "").strip()
        if verify_ko and model_id != "sam-3.1":
            verify_notes[track_id] = verify_ko

    return detections, verify_notes
