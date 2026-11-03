# Trail Sentinel — Technology Selection Document

> Basis: spec (scope frozen 2026-10-28), platform decision (confirmed by Jun on 2026-10-28: mobile web app), current code (`server.py`, `*.py`, `webapp/`, `eval/`).
> Status notation: **Confirmed/Implemented** vs **Open/Risk** are kept separate.

## 1. Selection Table

| Area | Selected Technology | Reason for Selection | Alternatives Considered and Reasons for Rejection |
| --- | --- | --- | --- |
| Frontend | Mobile web app — vanilla JS + `getUserMedia` (rear camera) + Canvas overlay + Web Speech API TTS + `navigator.vibrate` | Runs immediately in the phone browser with no install; camera, speech, and vibration are covered by browser standard APIs alone; demo-video screen recording is easy; the submission is public-repo-plus-video based, so judges cannot be expected to install an app | Native app (Android): excessive development effort, low likelihood judges would install it → rejected (settled in the platform decision). Keeping the CLI: weak for the Demo score (25%) → rejected. Frameworks (React etc.): small benefit relative to build tooling and dependencies → rejected for v1 |
| Backend | Python, currently standard-library `http.server` (`ThreadingHTTPServer`) | Zero dependencies, so `python3 server.py` runs anywhere; reuses the triage logic (root `.py` modules) as-is; the short schedule leaves no time to spend on the server itself | FastAPI/Flask: not currently installed, overkill for a single-endpoint scale → conditionally deferred (see migration conditions below) |
| Model — segmentation & tracking | **SAM 3.1** via the Meta Model API (text-prompt concept segmentation + tracking, single detect+segment+track call) | Concept-level segmentation robust to camouflage patterns; adding hazard concepts with text prompts alone (zero-retraining) is the key differentiator; the API approach avoids running a model too large for the phone (~840M parameters) on-device | On-device inference: the model is too large to run on a phone → rejected. Generic object detection (YOLO-class): fixed classes cannot add custom concepts and are weak against camouflage → rejected |
| Model — priority triage | **Muse Wonder** (priority, distance/direction phrasing, false-alarm suppression) — however, the v1 real-time path is implemented in parallel with deterministic logic (`triage.py`) | The 2-model pipeline with SAM is central to the "Use of Meta AI Tooling" judging score; keeping the triage logic deterministic makes the demo and eval reproducible regardless of API status | Sole real-time dependence on Wonder: availability risk since the API is in preview → run the logic fallback in parallel (see Risks section). Delegating every-frame triage to an LLM: latency, cost, and reproducibility problems → rejected |
| Model — auxiliary | Muse Spark (hazard reports, supporting explanations for species identification — post-hoc path), Muse Image (supplementing demo/test images — excluded from the real-time path) | Follows the spec's division of model roles as-is; keeps the real-time path lightweight | Including them in the real-time path: increases latency and cost → rejected |
| Speech | Web Speech API (`speechSynthesis`, ko-KR) | Built into the phone browser, no added cost or latency, with some offline capability; alert sentences are short so quality requirements are low | Server-side TTS synthesis: round-trip latency plus cost, network-dependent → rejected. The backend `alerts.speak()` stays a placeholder (output only); the browser handles actual speech |
| Hosting | Local execution (`localhost:8765`) — deployment for phone preview is **open** (Risks section) | Local is sufficient for the current stage (stub validation); the camera constraint (HTTPS/localhost) will be resolved at deployment time | Decision deferred — candidates and conditions are stated in the Risks section |
| Data | Fixture JSON (stub responses), eval label manifest JSON, call-counter JSON file | Version-controllable with no dependencies or DB; ensures eval reproducibility; managed together with the rule to use only rights-cleared test videos | Introducing a DB: overkill at this scale (tens of clips, one counter) → rejected |
| Spending guard | Client-side counter (`CallBudget`, JSON file, daily cap default of 200 calls) | Confirmed that Meta Billing's Spend Limit is notification-only with no enforced cap → physical blocking via the client-side counter plus, if needed, a low-limit card is the only means | Relying on Billing notifications alone: not an enforced block, only post-incident awareness → rejected as the sole measure (using both is acceptable) |
| eval | Local Python script (`eval/score.py`) | Automatically computes detection rate, alert lead time, and false-alarm rate against clip labels (manifest); no external service needed | Manual evaluation: no reproducibility or comparability → rejected |

### FastAPI migration conditions

Migrate from the standard-library server to FastAPI if any of the following becomes necessary.

- When handling real frame-image uploads (multipart/large base64) becomes complex
- When concurrent connections or async API calls (SAM/Wonder in parallel) become a bottleneck
- When the deployment environment assumes an ASGI server

## 2. Confirmed items (including implemented)

- **Platform**: mobile web app (confirmed 2026-10-28). Phone browser camera → backend → SAM API → on-screen display + voice/vibration.
- **Frontend**: `webapp/index.html`, `app.js`, `style.css` (vanilla). Full-screen rear camera, bbox+label overlay on Canvas (currently bbox, not mask polygons), alert banner, ko-KR TTS, vibration patterns (danger `[250,100,250]`, caution `[150]`), ~1.2 s scan interval, demo mode (replays hero fixture frames 0–60).
- **Backend**: `server.py` — `GET /` (serves the web app), `GET /api/status` (mode, call counter, concept list), `POST /api/scan` (triages a single frame). Reuses the existing `config.py`/`sam_client.py`/`triage.py` and adds only a frame adapter.
- **Triage logic**: `triage.py` — per-severity alert distances {3: 3.0m, 2: 2.5m, 1: 1.0m}; score = severity×2×proximity + approach speed (capped at 2.0) + confidence; per-track cooldown of 30 frames. Alert sentence rule "direction + distance + target" (e.g. "발 앞 3미터, 뱀" — "snake, 3 meters ahead at your feet" in Korean).
- **SAM 3.1 billing assumptions**: images $2.50 / 1k images, video frames $0.20 / 1k video frames (listed unit prices). Frame extraction interval equals cost — live scans limit the scan interval, and the total frame budget is fixed first to operate within the $150 credit.
- **Spending guard**: `CallBudget.spend()` raises on exceeding the cap; when the cap is reached the server returns `daily_call_cap_reached` and blocks scanning.
- **Meta connector status (live-verified 2026-10-31)**: base URL `https://api.meta.ai/v1`, `POST /v1/responses` + model `sam-3.1` (note: differs from the product page spelling `sam-3-1`), stream + `mask_encoding=one_bit`, one prompt per concept. Authentication verified via `GET /v1/models` (9 models, including `sam-3.1`). A live hero-still segmentation call returned 1 box+mask in 3.0 s at $0.0025 (within Jun's $150 credit). Coordinates are in image pixel space, and each record's `w`/`h` is the frame size. The output has no confidence or distance — confidence is treated as `None` and distance as a ground-plane heuristic estimate. The verification source and call log are in `~/workspace/custom-connectors/custom.meta-model-api/API_RESEARCH.md`.
- **Fallback principle**: on API/network failure, replay a cached response and always indicate it on screen (never pretend to be live); on excessive latency, display "확인 불가" ("unable to verify" in Korean).
- **Live scan wiring (2026-10-31, F1)**: the server starts in live mode only when `TRAIL_SENTINEL_LIVE=1` (stub by default — prevents accidental spending). In camera mode the web app captures real frames as JPEG data URLs with the long side ≤1024 px and sends them with the selected concepts (chip toggles, all selected by default). The server-side `LiveScanner` splits one `SegmentRequest` per concept and runs them in parallel, so `CallBudget` counts exactly per concept call. Server-side minimum scan interval 2.5 s, per-call timeout 10 s (transport), budget pre-check (if the whole scan does not fit in the cap, return `daily_call_cap_reached` without calling), and on total failure it honestly returns `live_scan_failed`. The frontend shows the "확인 불가" ("unable to verify") badge from the first failure and keeps it until success (on 3 consecutive failures it also notes the reason in the status line). Live approach speed is passed to `triage.evaluate` as fps converted from the wall-clock measured interval between consecutive scans (no triage-logic change). Masks are decoded on the server with `meta-sam-parser` (installed in tools/pylibs) and served as severity-colored RGBA PNGs (≤256 px); on failure it falls back to drawing bbox only. Measured: one server-mediated scan (1 concept) takes 6.1 s — below the PRD 9.2 target, so enforcing the 3.0 s alert validity window is on hold (enforcing it would discard most live alerts).
- **Live cost structure (at measured unit prices)**: 1 call per concept = 1 image = $0.0025. One 6-concept full scan = **$0.015**. Running the server minimum interval of 2.5 s at the theoretical maximum (24 scans/min) could reach $21.60/hour for 6 concepts, but the daily cap of 200 calls hits first — 200 calls ≈ 33 full scans = **at most $0.50/day**. At the frontend default cadence (5 s tick + 1 concurrent request) the maximum is 12 scans/hour (equivalent to $10.80/hour), but again the cap is exhausted first. In other words, in the current design the physical upper bound on spending is the `CallBudget` cap, not the unit price.

## 3. Open / Risks

| Item | Status | Response |
| --- | --- | --- |
| Muse Wonder API availability | API in preview; actual callability unconfirmed | Keep real-time triage working on deterministic logic (`triage.py`). If Wonder integration is blocked, **substitute Muse Spark** for triage phrasing and report generation, and state that fact in the submission materials |
| Actual SAM endpoint & schema | **Resolved (live-verified 2026-10-31)**: `POST /v1/responses`, model `sam-3.1`, confirmed by live calls through to structured text output. Remaining risk is operational, not the schema itself — distance is absent from the output so estimates rely on a heuristic, and one call per concept prompt makes per-frame cost proportional to the prompt count | Fill distance with the ground-plane estimator but label it an "estimate" and calibrate it with measured photos. For live scans, reduce the prompt count or widen the frame interval to keep total calls within `CallBudget`. The video path has only wire documentation and is unmeasured — verify it separately when image budget allows |
| Real frame transport path | **Resolved (2026-10-31)**: the web app sends real frames (JPEG data URLs) and the server live mode answers with real SAM. base64 JSON transport proved sufficient, so no FastAPI migration was needed | Remaining risks are latency (6.1 s measured per scan) and deployment — see the deployment row below |
| Deployment for phone preview | Open. The camera works only on HTTPS or localhost | Candidates: Cloudflare Tunnel (exposes the local server, fast), a PaaS such as Render (always-on, watch for cold starts). To be finalized later based on the demo-recording environment, separately from the public submission repo |
| API credential | Issued by Jun and registered in the Secure Vault `custom.meta-model-api` connection. Passed `models` and `segment-image` live verification on 2026-10-31 | The project server never reads the credential directly. The connector helper uses only the `hsurr:` surrogate from `dynamic_credentials.py`, and the project's live transport reaches the API only by invoking the helper as a subprocess |
| Credit applied | **Confirmed (2026-10-31)**: Jun confirmed receipt of the $150 credit. Verification runs actually spent $0.0025 | All subsequent live calls also operate only within the credit + `CallBudget` + per-task call limits |
| Test video rights | Real footage of the hero scene (snake in fallen leaves) not yet secured | Use only self-recorded footage or license-verified sources (rule: using uncleared data means disqualification) |

## 4. Architecture

```
┌───────────────────────── Phone browser (webapp/) ────────────────────────┐
│  getUserMedia rear camera ──▶ <video> fullscreen                         │
│  Scan tick (demo 1.2s / live 5s) ──▶ POST /api/scan {frame_index | frame image + concept list} │
│  Receive response ──▶ Canvas overlay (bbox + "뱀 2.6m" label)            │
│  On alert ──▶ red banner + speechSynthesis(ko-KR) + navigator.vibrate    │
│  Demo mode ──▶ replay hero frames 0..60 with no camera                   │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │ HTTP (local: localhost / HTTPS when deployed)
┌──────────────────────────────▼──────────── Backend (server.py, Python) ──┐
│  GET /api/status · POST /api/scan                                       │
│  CallBudget.spend() ── daily call-cap check (JSON counter)               │
│        │                                                                │
│        ▼                                                                │
│  SAMClient.segment()                                                    │
│    ├─ StubSAMClient  (current: fixtures/*.json canned responses)         │
│    └─ RealSAMClient (created only in server live mode) ──▶ meta_transport (+ mask decoding) ──▶ connector helper subprocess ──▶ Meta Model API (api.meta.ai/v1, sam-3.1) │
│        │ Detection[] (concept, distance, confidence, track_id, bbox)     │
│        ▼                                                                │
│  triage.evaluate() ─ severity×proximity+approach-speed score, alert distance, cooldown │
│    (Muse Wonder role — v1 is deterministic logic; Wonder/Spark integration is planned) │
│        │ AlertDecision (single highest-risk item only)                   │
│        ▼                                                                │
│  JSON response {detections, alert{text_ko, level}, calls_today, cap}     │
└──────────────────────────────────────────────────────────────────────────┘

  Parallel paths (not real-time):
    eval/score.py ── clips_manifest(labels) + results ──▶ detection rate, lead time, false-alarm rate
    Muse Spark* ── hazard report generation (log screen, planned)
    Muse Image* ── demo/test image supplementation (planned)

  * = planned/unimplemented. Unmarked items work in the current code.
```

## 5. File map

| File | Role |
| --- | --- |
| `server.py` | Web backend (standard-library http.server), `/api/scan` and `/api/status`. Stub demo path + opt-in live path (`LiveScanner`: per-concept parallel calls, 2.5 s minimum interval, budget pre-check) |
| `webapp/index.html`, `app.js`, `style.css` | Mobile web frontend (real-frame capture, concept chip selection, "확인 불가" ("unable to verify") state, mask overlay) |
| `config.py` | Hazard concepts v1 (6), registered host constants, `CallBudget` spending guard (thread-safe). Does not read credentials |
| `sam_client.py` | `SAMClient` interface, `StubSAMClient`, injectable `RealSAMClient` adapter (disabled by default). Optional mask PNG/rect fields on `Detection` |
| `meta_transport.py` | Live SAM transport (connector helper subprocess), real-response mapping, ground-plane distance estimation, `meta-sam-parser`-based mask decoding (best-effort) |
| `tools/pylibs/` | Install location for `meta-sam-parser` (pip --target). If absent, only masks are disabled and rendering falls back to bbox |
| `tests/test_sam_client.py`, `tests/test_meta_transport.py`, `tests/test_server_live.py` | Unit tests based on mocks / real-response fixtures / fake clients (`tests/fixtures/sam_hero_snake_raw.txt` is the verbatim real-response source) |
| `~/workspace/custom-connectors/custom.meta-model-api/` | Connector docs, surrogate helper, official research record `API_RESEARCH.md` |
| `triage.py` | Priority triage, alert sentence generation |
| `pipeline.py` | Recorded-video path (frame → SAM → triage → alert; for CLI/eval use) |
| `alerts.py` | CLI-path alert output (includes a placeholder separate from browser TTS) |
| `fixtures/hero_snake_leaves.json` | Hero-scene stub response |
| `eval/score.py`, `*.example.json` | Eval harness and label/result format examples |
| `main.py` | CLI stub demo |
