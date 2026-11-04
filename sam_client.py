"""SAM 3.1 clients: interface, stub fixtures and a guarded live adapter.

The Meta wire format was confirmed live on 2026-10-31 (see the connector's
API_RESEARCH.md): base ``https://api.meta.ai/v1``, ``POST /v1/responses``
with model ``sam-3.1``, streamed structured box/mask text. The wire call
itself lives outside this package, in the connector helper, so no credential
ever enters the project. ``RealSAMClient`` accepts an injected transport
that returns project-normalized detection records;
``meta_transport`` provides the live transport (subprocess to
the helper) plus the parser-based record mapping and the ground-plane
distance estimator. SAM returns no confidence and no distance, so
``Detection.confidence`` may be ``None`` and live distances are estimates.
"""
from __future__ import annotations

import json
import math
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from config import HAZARD_BY_KEY, HAZARDS, CallBudget


@dataclass
class Detection:
    concept: str          # hazard key, see config.HAZARDS
    frame_idx: int
    confidence: float | None  # None for live SAM: the API returns no score
    distance_m: float     # estimated distance to the hazard
    clock_direction: int  # 12 = straight ahead, 1-11 around the clock face
    track_id: str
    bbox: list[float]     # [x, y, w, h] normalised 0..1
    # Optional decoded mask overlay (live SAM only): an RGBA PNG data URL of
    # the mask crop plus its normalised frame rect [x, y, w, h]. None when
    # the transport did not decode a mask — the UI then draws the bbox only.
    mask_png: str | None = None
    mask_rect: list[float] | None = None


class SAMClient(Protocol):
    def segment(self, scene: str, frame_idx: int) -> list[Detection]:
        """Return hazard detections for one frame of a scene/clip."""
        ...


@dataclass(frozen=True)
class HazardPrompt:
    key: str
    text: str


@dataclass(frozen=True)
class SegmentRequest:
    """Transport-neutral input for one live segmentation operation."""

    frame_idx: int
    prompts: tuple[HazardPrompt, ...]
    image_bytes: bytes | None = field(default=None, repr=False)
    image_media_type: str | None = None
    video_ref: str | None = None
    source_ref: str | None = None

    def __post_init__(self) -> None:
        sources = sum(
            value is not None
            for value in (self.image_bytes, self.video_ref, self.source_ref)
        )
        if sources != 1:
            raise ValueError(
                "SegmentRequest needs exactly one of image_bytes, video_ref "
                "or source_ref"
            )
        if self.image_bytes is not None and not self.image_media_type:
            raise ValueError("image_media_type is required with image_bytes")
        unknown = [prompt.key for prompt in self.prompts if prompt.key not in HAZARD_BY_KEY]
        if unknown:
            raise ValueError(f"unknown hazard prompt keys: {unknown}")

    @classmethod
    def for_image(
        cls,
        image_bytes: bytes,
        *,
        frame_idx: int,
        image_media_type: str,
        prompts: tuple[HazardPrompt, ...] | None = None,
    ) -> "SegmentRequest":
        return cls(
            frame_idx=frame_idx,
            prompts=prompts or default_prompts(),
            image_bytes=image_bytes,
            image_media_type=image_media_type,
        )

    @classmethod
    def for_video_ref(
        cls,
        video_ref: str,
        *,
        frame_idx: int,
        prompts: tuple[HazardPrompt, ...] | None = None,
    ) -> "SegmentRequest":
        return cls(
            frame_idx=frame_idx,
            prompts=prompts or default_prompts(),
            video_ref=video_ref,
        )


def default_prompts() -> tuple[HazardPrompt, ...]:
    return tuple(HazardPrompt(key=hazard.key, text=hazard.prompt) for hazard in HAZARDS)


class SAMTransport(Protocol):
    """Boundary implemented outside this project package.

    Implementations own the provider request and any credential surrogate
    handling. They return normalized mappings with these keys:

    ``concept``, ``bbox``, ``track_id`` and, unless a distance estimator is
    configured on ``RealSAMClient``, ``distance_m``. ``confidence`` is
    optional — live SAM records omit it and the resulting
    ``Detection.confidence`` is ``None``. ``clock_direction`` is optional
    and defaults to 12.
    """

    def segment(self, request: SegmentRequest) -> Iterable[Mapping[str, Any]]:
        ...


class LiveInferenceDisabledError(RuntimeError):
    pass


class TransportNotConfiguredError(RuntimeError):
    pass


class BudgetNotConfiguredError(RuntimeError):
    pass


DistanceEstimator = Callable[[Mapping[str, Any], SegmentRequest], float]


# === [FEAT:F6] StubSAMClient (Hero Replay Fixtures) ==========================
class StubSAMClient:
    """Returns canned detections from fixture JSON files (no API calls).

    Fixture format: {"scene": str, "detections": [{concept, track_id,
    frame_start, frame_end, confidence, distance_start_m, distance_end_m,
    clock_direction, bbox}]}. Distance is linearly interpolated per frame.
    """

    def __init__(self, fixtures_dir: Path):
        self._scenes: dict[str, dict] = {}
        for path in Path(fixtures_dir).glob("*.json"):
            data = json.loads(path.read_text())
            self._scenes[data["scene"]] = data

    def scenes(self) -> list[str]:
        return sorted(self._scenes)

    def segment(self, scene: str, frame_idx: int) -> list[Detection]:
        data = self._scenes[scene]
        out: list[Detection] = []
        for d in data["detections"]:
            if not (d["frame_start"] <= frame_idx <= d["frame_end"]):
                continue
            span = max(1, d["frame_end"] - d["frame_start"])
            t = (frame_idx - d["frame_start"]) / span
            distance = d["distance_start_m"] + t * (d["distance_end_m"] - d["distance_start_m"])
            out.append(Detection(
                concept=d["concept"], frame_idx=frame_idx,
                confidence=d["confidence"], distance_m=round(distance, 2),
                clock_direction=d.get("clock_direction", 12),
                track_id=d["track_id"], bbox=d["bbox"],
            ))
        return out


# === [FEAT:F2] RealSAMClient (Guarded Live SAM 3.1 Adapter) ==================
class RealSAMClient:
    """Guarded adapter for the verified Meta SAM transport.

    Live inference is off by default. A caller must provide all three of:

    - ``enabled=True``
    - a ``CallBudget`` instance
    - an injected ``SAMTransport`` (``meta_transport.MetaSAMTransport`` for
      live calls, which reaches the API only through the connector helper)

    The project server does not construct this client and never reads the
    Secure Vault credential.
    """

    def __init__(
        self,
        *,
        transport: SAMTransport | None = None,
        budget: CallBudget | None = None,
        enabled: bool = False,
        distance_estimator: DistanceEstimator | None = None,
    ):
        self.transport = transport
        self.budget = budget
        self.enabled = enabled
        self.distance_estimator = distance_estimator

    def segment(self, scene: str, frame_idx: int) -> list[Detection]:
        """Legacy scene based entry point backed by a source reference."""

        request = SegmentRequest(
            frame_idx=frame_idx,
            prompts=default_prompts(),
            source_ref=scene,
        )
        return self.segment_request(request)

    def segment_request(self, request: SegmentRequest) -> list[Detection]:
        if not self.enabled:
            raise LiveInferenceDisabledError(
                "live SAM inference is disabled by default"
            )
        if self.transport is None:
            raise TransportNotConfiguredError(
                "no verified SAM transport is configured"
            )
        if self.budget is None:
            raise BudgetNotConfiguredError(
                "live SAM inference requires a CallBudget"
            )

        self.budget.spend(1)
        records = self.transport.segment(request)
        return [self._to_detection(record, request) for record in records]

    def _to_detection(
        self,
        record: Mapping[str, Any],
        request: SegmentRequest,
    ) -> Detection:
        concept = str(record["concept"])
        if concept not in HAZARD_BY_KEY:
            raise ValueError(f"transport returned unknown concept: {concept}")

        bbox_value = record["bbox"]
        if not isinstance(bbox_value, Iterable) or isinstance(bbox_value, (str, bytes)):
            raise ValueError("transport bbox must be a four item sequence")
        bbox = [float(value) for value in bbox_value]
        if len(bbox) != 4:
            raise ValueError("transport bbox must contain x, y, width and height")

        if "distance_m" in record:
            distance_m = float(record["distance_m"])
        elif self.distance_estimator is not None:
            distance_m = float(self.distance_estimator(record, request))
        else:
            raise ValueError(
                "transport record has no distance_m and no distance estimator "
                "is configured"
            )

        confidence_value = record.get("confidence")
        # A malformed mask must not kill an otherwise valid detection:
        # drop the mask pair instead (the server synthesizes a tint
        # fallback for SAM routes when no pixel mask survives).
        mask_png = record.get("mask_png")
        mask_rect: list[float] | None = None
        mask_rect_value = record.get("mask_rect")
        if mask_png is not None and mask_rect_value is not None:
            try:
                parsed_rect = [float(v) for v in mask_rect_value]
            except (TypeError, ValueError):
                parsed_rect = []
            if len(parsed_rect) == 4 and all(
                math.isfinite(v) for v in parsed_rect
            ):
                mask_rect = parsed_rect
            else:
                mask_png = None
        else:
            mask_png = None
        return Detection(
            concept=concept,
            frame_idx=request.frame_idx,
            confidence=(
                float(confidence_value) if confidence_value is not None else None
            ),
            distance_m=distance_m,
            clock_direction=int(record.get("clock_direction", 12)),
            track_id=str(record["track_id"]),
            bbox=bbox,
            mask_png=mask_png,
            mask_rect=mask_rect,
        )
