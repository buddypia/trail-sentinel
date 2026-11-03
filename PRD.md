# Trail Sentinel — PRD (Product Requirements Document)

## 0. Document Meta

| Item | Content |
| --- | --- |
| Document version | v0.4 (2026-10-31) |
| Status | Current — Single Source of Truth for requirements |
| Entry | Meta Global AI Developer Hackathon (Cerebral Valley, Remote), Indie track, theme Push the Frontier |
| Status notation rule | Each requirement states its **implementation status** — Implemented = works in current code / Partial = stub/skeleton stage / Planned = not implemented. Pre-measurement figures are explicitly labeled **target** |

### 0.1 Purpose — Why This Document Exists

- **Basis for scope agreement**: fixes in one place what we build (v1 in-scope) and what we don't (v1 out-of-scope), so scope doesn't drift during the remaining period (submission 2026-11-05 11:00 JST).
- **Contract for implementation and verification**: the acceptance criteria of the functional requirements (F1–F11) and the quantitative SLOs of the non-functional requirements (§9) are the conditions under which code may be called "done." Completion is judged against this document's criteria, not gut feel.
- **Basis for judging and submission materials**: demo video structure, submission write-up, and eval metric presentation all come from this document and eval measurements. Do not claim in the demo any feature not in this document.

### 0.2 Audience

- Jun (developer and entrant) — scope decisions and prioritization.
- Implementing AI agents/developers — entry point is `AGENTS.md`; requirement details are in this document.
- (Indirect) Judges — the criterion for whether submission materials stay within this document's claimed scope.

### 0.3 Authorship, Maintenance, and Precedence Rules

- When requirements change, **change the code and this document in the same unit of work**, and leave the date and reason in §14 Change History. Never leave the document stale.
- Precedence when documents conflict:
  1. **Rules** (`../files/meta-hackathon-rules.md`) — avoiding disqualification always wins.
  2. **This PRD** — the baseline for current scope, requirements, and figures.
  3. **Spec** (`../files/meta-hackathon-trail-sentinel-spec/…`) — decision record frozen 2026-10-28. When it differs from the PRD, follow the PRD, leave the reason in Change History, and annotate the spec. Do not change frozen-scope essentials (hero scene, 6-concept cap, theme) without Jun's confirmation.
  4. **TECH.md** — implementation-means choices. If a technology choice can't satisfy the PRD's requirements, fix toward satisfying the requirement rather than toward TECH.

### 0.4 Definitions

| Term | Meaning |
| --- | --- |
| Hazard concept | A detection target defined as a text prompt given to SAM 3.1. Managed as prompts, not code classes |
| Hero scene | The demo's centerpiece — the app catching a snake camouflaged in fallen leaves before the human does (§6.1) |
| Scan tick | One cycle of capturing a frame at a fixed interval (~1.2s) and sending it to `/api/scan` |
| Alert lead time | How many seconds before hazard arrival the first alert fired (measured by eval) |
| Baseline | The first measured result. Per the spec policy of not asserting accuracy figures before measurement, accuracy metrics judge success by before/after improvement comparison once the baseline is secured |
| SLO | Quantitative targets for non-functional requirements (§9). All are pre-measurement **targets**; claim achievement only with measurement records |
| `"확인 불가"` ("verification unavailable") | Display state shown when frame safety cannot be judged due to delay or failure. The substitute for late alerts or silent failure |

### 0.5 Related Documents

| Document | Role |
| --- | --- |
| `AGENTS.md` (this repo) | Entry point for AI agents — doc map, current status, guardrails |
| `TECH.md` (this repo) | Technology choices and architecture, open items and risks |
| `../files/meta-hackathon-trail-sentinel-spec/meta-hackathon-trail-sentinel-spec.md` | Scope-freeze original (2026-10-28) |
| `../files/meta-hackathon-rules.md` | Official rules — including disqualification conditions; always highest precedence |
| `README.md` (this repo) | How to run and structure summary |
| `eval/` | Measurement harness and data — the measured basis for metrics |

## 1. Product Overview

- **One-line definition**: a personal outdoor hazard sentinel — point a smartphone camera at your feet and ahead while walking, and SAM 3.1 segments and tracks hazard concepts defined as text prompts in real time, while Muse Wonder prioritizes by distance and approach speed and briefly warns by voice and vibration only when dangerous. Phone only, no extra hardware.
- **Entry**: Meta Global AI Developer Hackathon (Cerebral Valley, Remote), **Indie track**, theme **Push the Frontier** — a project giving the phone camera a new capability: "finding camouflaged hazards as concepts and warning ahead."
- **Positioning**: neither "discriminate after discovery" (snake ID apps) nor "describe the scene" (scene-description apps for the blind), but a personal sentinel that **scans multiple hazards before approach and warns ahead**.
- **Honesty principle**: an assistive tool, not a safety guarantee. The premise that false positives and misses exist is not hidden; it is disclosed with measured metrics.

## 2. Problem Definition and Background

- **Problem**: a large share of real injury patterns on autumn trails is "unseen underfoot/ahead hazards." Snakes camouflaged in fallen leaves, pits, hidden roots, and wet leaves under leaf cover are indistinguishable to the eye, and hornet nests, bears, boars, and rockfall zones are noticed only after approach. Hazards must be judged "while approaching," not "after discovery."
- **Gaps in existing alternatives** (spec's market-research conclusion): snake ID apps (SnakeSnap et al.) are for post-discovery species ID. Bear tools are sighting-data maps (Kumamap) and municipal fixed AI cameras — not things a person carries around. Scene-description apps for the blind (Be My AI, Seeing AI, etc.) are in the "shoot-then-describe" layer, not active alerting. Obstacle-warning hardware is effectively a single commercial product — a thin field. **"Many products describe; no personal product warns ahead"** is this product's slot.
- **Why now**: timing (autumn foliage peak season; pre-hibernation activity period for snakes and bears) and model (SAM 3.1's text-prompt concept segmentation — strong on camouflage patterns and custom concepts) coincide.

## 3. Goals and Non-Goals

### 3.1 Goals

- G1. In the hero scene (snake camouflaged in leaves), demonstrate with a real SAM integration that the app warns before arrival about a hazard a human missed.
- G2. Show live that hazard concepts can be added with text prompts only, without retraining (F7).
- G3. Back claims with numbers — measure detection rate, alert lead time, false-alarm rate, and latency with eval, and publish including failure clips (F9).
- G4. Finish demo and evaluation within the $150 credit — a spending guard physically enforces it (F8).
- G5. Submit without rule violations — public repo, 3-minute demo video, new work only, only data with rights (see §11).

### 3.2 Non-Goals

- Guaranteeing safety or accident prevention. This product is an assistive tool and is never presented otherwise.
- Making post-discovery species ID a core feature (species notes go only as far as F11's supplementary info).
- Describing the whole scene, or narrowing to the blind-only use case.
- Community hazard maps / sharing between users (out of v1; outside F10's scope).
- Wearables / dedicated hardware, offline on-device inference.

## 4. Stakeholders

| Stakeholder | Role | What they get from this document |
| --- | --- | --- |
| Jun | Developer and entrant (solo). Only Jun can issue API keys, register a card, and submit | The baseline for scope, priorities, and milestones |
| Judges | Stage 1 theme/model-use check, stage 2 scored judging (Impact 30 / Tooling 25 / Demo 25 / Technical 20), stage 3 live finals | Assurance that demo and submission write-up don't exceed this document's claimed scope |
| Hiker users | Autumn hikers (primary). In-motion use where the screen can't be watched continuously | The bar for alert quality — short, rare, directional alerts (F4·F5, §9) |
| Cerebral Valley / Meta | Organizer/platform (rules, credits, API) | Rule compliance (§11), credit usage limits (§9.5) |

## 5. Target Users

- Autumn foliage-season hiking hikers (primary target). Extensions: trail runners, outdoor workers.
- Usage context: walking a trail with the phone pointed at feet (downward) and ahead. Since the screen can't be watched continuously, alerts are voice + vibration first; the screen is for confirmation.

## 6. Key Scenarios

### 6.1 Hero Scene — Snake Camouflaged in Autumn Fallen Leaves (fixed)

Autumn mountains; the trail is layered deep with fallen leaves. A hiker walks with the phone pointed at their feet. A snake (Japanese mamushi / Korean salmosa pit viper) hides camouflaged among the leaves. To the human eye it blends with the leaf pattern and is indistinguishable until just before stepping on it. At that moment the app surfaces the snake's shape as a mask first, and warns briefly with vibration.

> "발 앞 2미터, 뱀" ("Snake, 2 meters ahead at your feet")

### 6.2 Live Expansion Scene

When a judge (or user) proposes a new hazard concept by voice (e.g. "전동 킥보드" ("electric kick scooter"), "쓰러진 나무" ("fallen tree")), detection starts immediately with text prompts alone, without model retraining (zero-retraining custom hazard).

### 6.3 Other Everyday Scenarios

- When a hornet nest, bear, boar, or rockfall zone appears ahead, warn before approach.
- Hidden pits, protruding roots, and wet leaves underfoot warn at a low level just before stepping.

## 7. Functional Requirements

### F1. Live Scan (camera → frame upload)

- **Definition**: captures the phone browser's rear-camera video at fixed intervals, uploads it to the backend, and overlays results on screen.
- **Input**: `getUserMedia` rear-camera stream, scan interval ~1.2s.
- **Output**: detection boxes + labels (concept name, distance) overlaid on camera video; status line (mode, today's call count/cap).
- **Acceptance criteria**: when camera permission is granted, scanning starts; when denied, the reason and alternatives (demo mode, HTTPS/localhost requirement) are shown. Each scan tick's `/api/scan` response is reflected in the overlay.
- **v1 exclusions**: background (screen-off) scanning, on-device inference.
- **Implementation status**: **Implemented (server-local only)** — camera mode captures real frames (long edge ≤1024px, JPEG data URL) and sends them to `/api/scan` with the selected concept list; the server answers with real SAM 3.1 only when `TRAIL_SENTINEL_LIVE=1` (default is stub — prevents accidental spend). Server-side minimum scan interval 2.5s, per-call timeout 10s, and `"확인 불가"` display on failure are implemented and verified (2026-10-31 snake detection on the hero still via a real server-mediated call). But the server still runs only on this VM; deployment (HTTPS) openable from a phone is a separate unfinished step.

### F2. SAM 3.1 Concept Segmentation (hazard concepts v1)

- **Definition**: segments hazard concepts defined as text prompts using SAM 3.1 on the Meta Model API. The concept list is managed as prompts, not code.
- **Input**: frame image + active concept prompt list.
- **Output**: per-concept masks/bboxes, confidence, track_id.
- **Hazard concepts v1 (6 frozen)**:

| # | Concept | Prompt direction | Zone | Severity |
| ---: | --- | --- | --- | ---: |
| 1 | Snake ("뱀") | Including snakes camouflaged on leaves/soil | Underfoot | 3 |
| 2 | Hornet nest ("말벌집") | Nests attached to trees, rocks, structures | Ahead | 3 |
| 3 | Bear ("곰") | Large animal ahead | Ahead | 3 |
| 4 | Boar ("멧돼지") | Medium animal ahead | Ahead | 2 |
| 5 | Rockfall zone ("낙석 구간") | Rock piles on the trail, collapsed sections | Ahead | 2 |
| 6 | Slippery zone ("미끄러운 구간", underfoot bundle) | Hidden pits, protruding roots, wet leaves | Underfoot | 1 |

  The underfoot bundle measures with internally separate prompts but never exceeds the 6-concept cap.
- **Acceptance criteria**: per-concept detection results pass to F3 tracking in track_id units. Concept add/remove takes effect via prompt change alone.
- **v1 exclusions**: 7+ concepts, retraining on user data.
- **Implementation status**: **Implemented (image path)** — endpoint/schema fixed by the 2026-10-31 real call (`POST /v1/responses`, model `sam-3.1`, one prompt per concept, streaming structured text). `meta_transport` makes real calls via a connector helper subprocess, with box normalization and `meta-sam-parser`-based mask decoding (PNG overlay) wired into the server live path. The response carries no confidence/distance, so confidence is `None` and distance is a ground-plane estimate. Video path unmeasured.

### F3. Tracking and Distance Estimation

- **Definition**: tracks the same object across frames via track_id, and estimates distance to the hazard and approach speed from mask size/position changes.
- **Input**: F2's per-frame detection results.
- **Output**: per-object distance (m), approach speed (m/s; positive = approaching).
- **Acceptance criteria**: the same object's distance updates continuously across the frame flow, and approach speed feeds the F4 score.
- **v1 exclusions**: precise ranging (stereo/LiDAR); refining area-based estimation when real SAM responses lack distance values.
- **Implementation status**: **Partial** — the stub interpolates the fixture's distance range frame by frame, and approach speed is computed against the previous frame (`triage.approach_speed_mps`). The distance-estimation method for real SAM integration needs finalizing.
- **Known limitation**: the stub/demo path computes approach speed on a 10fps virtual-time basis (figures are in fixture time). Since 2026-10-31 the live path passes fps converted from the wall-clock interval measured between consecutive scans to `triage.evaluate`, resolving this — the judging logic itself is unchanged.

### F4. Wonder Priority Judgment

- **Definition**: scores detected hazards by severity, distance (proximity), and approach speed, and picks only the single highest-worth warning. This is Muse Wonder's role; the v1 realtime path implements it as reproducible deterministic logic.
- **Input**: F3's per-object distance/approach speed, per-concept severity, confidence.
- **Output**: alert decision (1 target, score, alert sentence) or no alert.
- **Judgment rules (per current code)**:
  - Per-severity alert distances — severity 3: within 3.0m, 2: within 2.5m, 1: within 1.0m are alert candidates only.
  - Score = severity × 2 × proximity (0 at 10m, 1 at 0m) + approach speed (capped at 2.0) + confidence. Only the top scorer alerts.
- **Acceptance criteria**: distant low-severity hazards (e.g. wet leaves beyond 1.4m) don't alert, while approaching high-severity hazards alert once on entering alert range.
- **v1 exclusions**: simultaneous multi-alerts, per-user threshold learning.
- **Implementation status**: **Implemented (logic)** — `triage.evaluate()`. Direct Wonder API integration is planned pending API preview-status confirmation.

### F5. Voice + Vibration Alerts

- **Definition**: when F4 decides to alert, notifies via Korean voice and vibration alongside an on-screen banner. Assumes a usage environment where the user isn't watching the screen.
- **Input**: F4's alert sentence, alert level (`danger`/`caution`).
- **Output**: red banner (separate color for caution level), Web Speech API ko-KR voice, vibration patterns (danger: strong repeat; caution: short).
- **Alert sentence rules**: short one-liners of "direction + distance + target." Direction is "발 앞" ("ahead at your feet") for the underfoot zone, "전방" ("ahead") for forward, plus clock direction ("3시 방향" ("3 o'clock direction")) on lateral bias. Distance is rounded to integer meters. Examples follow fixed patterns such as **"발 앞 3미터, 뱀"** ("Snake, 3 meters ahead at your feet"), "전방, 말벌집" ("Hornet nest ahead"), "전방, 곰 — 접근 금지" ("Bear ahead — do not approach").
- **Acceptance criteria**: the same alert sentence is never replayed (sentence-level dedup), and banner, voice, and vibration fire simultaneously with the alert.
- **v1 exclusions**: multilingual voice, earphone-only mode, voice tone personalization.
- **Implementation status**: **Implemented (web)** — `fireAlert()` in `webapp/app.js`. Note the backend `alerts.py` TTS/vibration is a CLI placeholder (output only); the browser does the actual voicing.

### F6. Demo Mode (recorded-video playback)

- **Definition**: replays a recorded scene (currently the hero fixture sequence) frame by frame without a camera, demonstrating the full pipeline. For demo-video shooting and desktop checks.
- **Input**: scene identifier (default: hero scene), play/stop.
- **Output**: box display and alert reproduction as frames progress, with a persistent "데모 장면 재생 중 (카메라 아님)" ("replaying demo scene — not camera") badge.
- **Acceptance criteria**: the hero scene plays to the end in a desktop browser without camera permission, and the snake alert fires once. The badge persists so it can't be mistaken for live.
- **v1 exclusions**: arbitrary video-file upload playback (the recorded-video real pipeline is covered under F1/F2 live-integration scope).
- **Implementation status**: **Implemented** — both web demo mode and CLI demo (`main.py`) work.

### F7. Adding New Hazard Concepts by Voice (live)

- **Definition**: when the user adds a new hazard concept by voice (or text), it is immediately reflected in the SAM 3.1 text prompt list without retraining, and detection starts.
- **Input**: new concept name + prompt sentence (e.g. "쓰러진 나무" ("fallen tree") → "a fallen tree or log blocking the trail").
- **Output**: added to the concept list as active; included in detection targets from the next frame.
- **Acceptance criteria**: from the scan right after adding, the new concept appears in the `/api/status` concept list and detection results. The demo shows this flow live with a judge-proposed concept.
- **v1 exclusions**: concept sharing/marketplace.
- **Implementation status**: **Implemented** — `config.register_custom_hazard()`, `POST /api/concepts` in `server.py`, and the frontend `＋ 개념 추가` ("Add concept") control in `webapp/` (Web Speech Recognition `ko-KR` voice input 🎙 and text input) implemented and verified by unit tests (`CustomConceptTests`) (2026-10-31).

### F8. Spending Guard (daily call cap)

- **Definition**: since Meta Billing has no enforced spend cap and Spend Limits are notifications only, the client self-enforces a daily API call cap.
- **Input**: call attempts, daily cap (default 200, env var `DAILY_CALL_CAP`).
- **Output**: counter (JSON file) update; on reaching the cap, call blocking with a `daily_call_cap_reached` response.
- **Acceptance criteria**: scan requests past the cap don't call the API, and the blocked state shows in the on-screen status line. The counter resets on date change.
- **v1 exclusions**: per-concept/per-feature budget splits, remote counter sync.
- **Implementation status**: **Implemented** — `config.CallBudget`, in use on both server and pipeline. (Note: currently stub calls are counted too. Before live integration, decide whether to count only actually-billed calls.)

### F9. Eval Measurement

- **Definition**: runs the pipeline over a labeled test-clip set to verify claims with numbers. Failure clips are included in results — never cherry-picking good clips.
- **Input**: per-clip label manifest (clip, hazard concept, ground-truth frame range, arrival frame).
- **Output**: detection rate, alert lead time (s), false-alarm rate (per minute), (planned) latency distribution.
- **Acceptance criteria**: `eval/score.py` computes the three metrics from an example manifest/results. The first measured result becomes the baseline.
- **v1 exclusions**: auto-labeling, operating a large clip set (hundreds).
- **Implementation status**: **Partial** — the scoring skeleton and format examples work; `eval/data/` holds 14 files with per-file source/license records (`eval/data/SOURCES.md`), and `eval/clips_manifest.json` is written. `score.py`'s false-alarm-rate denominator is unified to output hazard-free clip minutes as the primary metric with whole-video minutes as auxiliary (2026-10-31).

### F10. Remembering Hazards on Frequent Routes (Active Memory direction)

- **Definition**: remembers locations of repeatedly detected hazards on frequent routes, and reminds earlier — before approach — on revisit.
- **Input**: detection history (location, concept, time).
- **Output**: reminder on revisit, location list on the history screen.
- **Acceptance criteria (v1 scope)**: location records persist, and re-entering the same segment shows a reminder grounded in the prior record.
- **v1 exclusions**: community sharing, map-service features.
- **Implementation status**: **Planned** — including the history screen, unimplemented.

### F11. Hazard Report (Muse Spark, auxiliary/post-hoc)

- **Definition**: after a hike, Muse Spark summarizes detection history into a short hazard report. Species ID is offered only as auxiliary notes.
- **Input**: detection history.
- **Output**: report text on the history screen.
- **Acceptance criteria**: the report contains no species assertions or safety verdicts.
- **v1 exclusions**: realtime route integration.
- **Implementation status**: **Planned**.

## 8. Screen Layout (per spec)

- **Live screen** (implemented): camera video, detection box overlay, top-hazard banner, status line, concept chip list.
- **Concept list** (partial): displaying the 6 active concepts implemented. On/off toggles and voice-add input are planned with F7.
- **History screen** (planned): detection history, frequent-route hazard locations, Spark report.
- **Evaluation screen** (dev/submission use): harness results used as submission material. No separate UI; `eval/` script output is the current form.

## 9. Non-Functional Requirements (quantitative SLOs)

This product's essence is "does the alert arrive in time." A late alert equals no product, and a late alert is more dangerous than none. So non-functional requirements including speed are specified not as prose but as **SLO-form targets + measurement methods + below-target responses**.

### 9.1 How to Read

- All figures below are **pre-measurement design targets**. Claiming achievement requires measurement records per the §12 measurement plan.
- Accuracy metrics (detection rate, false-alarm rate) differ — per spec policy, no target figures are asserted before measurement; the first measurement is the baseline (§12).
- The Current-status column states code-based facts only (Implemented/Partial/Planned, including Unmeasured).

### 9.2 End-to-End Latency Budget (per scan: frame capture → alert)

| Step | Target | Notes | Current status |
| --- | --- | --- | --- |
| 1. Frame capture + JPEG encode (browser) | p95 ≤ 100ms | Assumes uploaded image long edge ≤1280px, ≤200KB | Implemented (captures at long edge ≤1024px, unmeasured) |
| 2. Upload (phone → backend) | p95 ≤ 300ms | Assumes 4G or HTTPS-tunnel environment | Unmeasured |
| 3. Backend preprocess + budget check | p95 ≤ 50ms | Includes `CallBudget` check | Implemented (stub path, unmeasured) |
| 4. SAM 3.1 API round trip | p50 ≤ 800ms, p95 ≤ 1,800ms | **Dominant segment.** Most of total latency is here; if this target breaks, the total target breaks | Measured (2026-10-31): helper-only round trip 3.0s, full server-mediated scan 6.1s (1 concept, incl. subprocess spawn + mask decode) — **below target**. Single sample, so distribution unmeasured |
| 5. Priority judgment (`triage.evaluate`) | p95 ≤ 20ms | Deterministic logic, local compute | Implemented (unmeasured) |
| 6. Response rendering (box/banner display) | p95 ≤ 50ms | Canvas overlay | Implemented (unmeasured) |
| 7. TTS utterance start | p95 ≤ 200ms | `speechSynthesis.speak()` call → voice start | Implemented (unmeasured) |
| **Total: capture → banner + voice start** | **p50 ≤ 1.5s, p95 ≤ 2.5s** | Per-step p95s sum to ≈ 2.5s | **Unmeasured — measurement itself is planned** |

- **Alert validity window**: responses arriving more than **3.0s** after capture time are discarded without voicing that frame's alert. On consecutive lates, transition to the §9.4 `"확인 불가"` state. (Unimplemented — the 2026-10-31 measurement showed 6.1s full-scan latency, so enforcing this now would discard nearly all live alerts. Latency reduction or validity-window redefinition must come first; until then live alerts are voiced with a latency indication.)

### 9.3 Scan Interval, Throughput, Concurrency

| Item | Requirement / target | Measurement | Below-target response | Current status |
| --- | --- | --- | --- | --- |
| Scan interval | Live 1.2s interval (frame step 5 @ virtual 10fps) | Client tick log | If the interval slips, raise frame step to lower call frequency | Partial — demo runs a fixed 1.2s interval. Live runs frontend 5s ticks + server-side 2.5s minimum interval due to real-call latency (~3–6s/scan) and cost (1.2s interval infeasible at measured latency). Widening the interval when motionless is planned |
| In-flight requests | Max 1 per session — ticks before the previous response are skipped | Client measurement | — (guard against late-response pileup) | Implemented — `app.js` keeps only 1 in-flight scan and skips overlapping ticks |
| Throughput | Single-user premise. ≤ 50/min per session (ceiling derived from interval) | `/api/status` counter | N/A (not a multi-user service) | Implemented (ThreadingHTTPServer + global-lock serialization) |
| Concurrent sessions | Target 1 (developer + demo-shoot environment) | — | If multi-session demand arises, redesign starting with state separation | Shared-global-state structure |

### 9.4 Reliability — Failure Behavior

| Item | Requirement / target | Measurement | Below-target response | Current status |
| --- | --- | --- | --- | --- |
| API timeout | 10s cap per request. Past it, the tick fails | Real-call log | That frame shows `"확인 불가"`; next tick proceeds | Implemented (live path: transport timeout 10s + frontend `"확인 불가"` badge) |
| Retry policy | No immediate resend of failed frames. Natural retry with a fresh frame on the next scan tick | Code review | — | Structurally compliant (tick-based) |
| Consecutive failures | On 3 consecutive API/network failures, `"확인 불가"` badge + reason on the status line. **No silent failure** — never a state that quietly stops | Fault-injection test (network cut) | Switch to cache fallback honoring the display duty below | Implemented — `"확인 불가"` badge from the first failure, reason appended to the status line on 3 consecutive, held until success (2026-10-31) |
| Cache-fallback display | While replaying fallback, persistent "데모/캐시 재생 중" ("replaying demo/cache") badge. Never pose as live | Screen check | — | Partial — demo-mode badge implemented; cache fallback itself planned |
| Spending-guard block | On daily-cap reach, don't call the API; return `daily_call_cap_reached` (HTTP 429) + status-line display | Force-reach test with lowered cap | — | Implemented |
| Latency overrun | Responses past the §9.2 validity window (3.0s) are not used as alerts | Confirm no alert after latency injection | `"확인 불가"` display | Planned |

### 9.5 Cost Cap

| Item | Requirement / target | Measurement | Below-target response | Current status |
| --- | --- | --- | --- | --- |
| Daily call cap | Default 200/day (`DAILY_CALL_CAP`) — the physically enforced ceiling in code. Meta Billing's Spend Limit is notification-only, so this is the only real block | `.call_counter.json` + `/api/status` | Cap reached = real calls stop that day (§9.4) | Implemented (stub calls also counted) |
| Unit-cost premise | SAM 3.1: images $2.50/1k, video frames $0.20/1k frames (listed rates) | Cross-check against Meta Model API Billing page | If rates differ, recompute from the frame budget | Premise only; actual billing unconfirmed |
| Total spend | Whole-hackathon cumulative within **$150 credit**. In image-path terms daily cap 200 ≈ $0.50/day, so the cap is the budget wall | After credit reflects, cross-check Billing before/after first real call (weekly) | If burn is faster than expected, cut eval frame budget and live interval first | Credit receipt confirmed (2026-10-31, Jun). Real calls started: 2 verification calls (1 image each, $0.005 total). Live scans cost 1 call per concept, so a full 6-concept scan = $0.015/run — see TECH.md for cost structure |
| Eval frame budget | Target cap of ≤ 20,000 frames per full eval run (≈ $4 at video rates); fix total frames before running | Sum manifest frame counts | Past budget, widen frame sampling interval rather than cutting clips | Planned (finalize after real manifest) |

### 9.6 Security — API Keys

| Item | Requirement | Current status |
| --- | --- | --- |
| Key storage | Only in Secure Vault's `custom.meta-model-api` connection. Project server and frontend never read or receive the key directly. Connector helper handles only `hsurr:` surrogates | Structure changed — removed the project's env-var key loader; verified surrogate attachment only in the connector local probe. No provider requests sent |
| No recording | Never write key values in code, docs, logs, chats, or screenshots. `.env` files are in `.gitignore` | Reflected in `.gitignore` |
| Pre-public check | Before switching the repo to public, pass a secret-string sweep over the entire git history (§13 milestone gate) | Planned |
| On leak | Immediate key revocation/reissue is the only instant brake. Billing alerts are after-the-fact awareness only | Procedure only |

### 9.7 Compatibility

| Item | Requirement / target | Current status |
| --- | --- | --- |
| Android Chrome (latest 2 versions) | Camera, Canvas, TTS, vibration all work | Unverified (real-device testing needed) |
| iOS Safari 16.4+ | Camera and TTS work. **No vibration on iOS Safari** — `navigator.vibrate` is a no-op, so voice + banner are the fallback channels | Unverified |
| Desktop Chrome | Works as demo-mode-only (demo-video shooting path) | Implemented |
| Camera premise | `getUserMedia` works only on HTTPS or localhost — HTTPS deploy/tunnel is a precondition for real-phone use | Local only; deploy undecided (TECH.md risk) |
| Backend runtime | Runs on Python 3.10+ stdlib only (currently verified on 3.12) | Implemented |

### 9.8 Accessibility and Safety Notice

| Item | Requirement | Current status |
| --- | --- | --- |
| Multi-channel alerts | Never warn by color alone — banner text + voice + vibration together | Implemented (vibration except iOS, §9.7) |
| Safety notice | Fixed notice at the bottom of the live screen: "보조 도구이며 안전을 보장하지 않습니다" ("an assistive tool; safety is not guaranteed"). Same intent in submission materials and README | **Implemented** — reflected in README, this document, and the fixed webapp screen-bottom notice |
| No species assertions | No screen or report may carry safety verdicts grounded in species ID | Requirement only (F11 acceptance criteria) |
| Positioning red line | Reading as a "simple image analyzer" is rulebook demerit/disqualification territory. All materials present it only as a realtime active-alert system (continuous scan, tracking, prioritization, voice alerts) | Applied throughout docs |

## 10. Assumptions, Constraints, Risks

### 10.1 Assumptions

- A1. SAM 3.1 provides text-prompt concept segmentation/tracking via the Meta Model API as announced, and the unit-cost premise (images $2.50/1k, video frames $0.20/1k) doesn't change materially.
- A2. Either the Muse Wonder API preview opens in time, or, if closed, the deterministic-logic fallback keeps the Tooling-score core (SAM + priority judgment).
- A3. The $150 credit reflects in Billing before submission (submitted 2026-10-28, reflection check ~10/30).
- A4. Judges evaluate via demo video and public repo without installing the app — so the demo video is the product's primary evidence.

### 10.2 Constraints

- C1. **Time**: only work produced 2026-10-26 – 11-04 may be presented as new work; submission deadline is Nov 4 21:00 ET (= Nov 5 11:00 JST).
- C2. **People**: solo developer. Steps needing Jun's own account (key issuance, card, submission) bottleneck the schedule.
- C3. **Cost**: a billing structure with no enforced spend cap — the client spending guard (F8) is the only physical wall.
- C4. **Physics**: SAM scale rules out on-device phone inference, and the camera works only on HTTPS/localhost. Live mode carries network round-trip latency (§9.2).
- C5. **Data**: only test footage with rights may be used — self-shot or license-verified sources only.

### 10.3 Risks

| Risk | Impact | Response |
| --- | --- | --- |
| R1. Credit reflection delay | Smaller real-SAM measurement/eval scale | Verify the full pipeline on stubs before reflection; start measuring immediately on reflection. Budget only confirmed partner credits |
| R2. Wonder API unopened | Weaker Tooling score | Keep realtime judgment as deterministic logic; use Muse Spark as the Wonder-role substitute and state so in submission materials |
| R3. API round-trip latency past SLO | Late warnings collapse product value itself | Shrink frame size / adjust interval; handle honestly with the 3.0s validity window and `"확인 불가"` display. Never emit late alerts |
| R4. Camouflage-pattern misses | Hero-scene failure = demo failure | Prompt tuning and per-concept detection-rate disclosure. Never hide failure clips; state them as limits |
| R5. Read as "simple image analyzer" | Rulebook demerit/disqualification territory | Position as a realtime alert system in all materials (§9.8). Don't lead with species-ID / image-analysis framing |
| R6. Using data without rights | Disqualification cause | Self-shot / license-verified sources only. Never use in submission materials before recording per-file source/license in `eval/data/SOURCES.md` |
| R7. Mistaken for out-of-window work | Disqualification if contribution is unidentifiable | Keep commit history identifying the production window; distinguish new implementation from existing assets (browser APIs, Meta models) in docs |
| R8. Mistaken for a banned category (medical/health advice, etc.) | Disqualification cause | Fix scope at hazard "warning," not safety advice; use no health/medical-advisory wording |

## 11. Submission Requirements Trace (rule basis)

| Rule (`../files/meta-hackathon-rules.md`) | Product response |
| --- | --- |
| New work only (only Oct 26 – Nov 4 production presented) | All code written in-window. Commit history keeps new work identifiable |
| Contribution must be identifiable (disqualification if judges can't tell what's new) | Demo/docs distinguish in-window production from existing assets (phone OS, browser APIs, Meta models) |
| Public repo required | Repo goes public at submission (after passing the §9.6 secret sweep) |
| 3-min demo video required; major judging item | Demo structure: problem 0:00–0:30 / hero scene 0:30–1:30 / live concept add 1:30–2:20 / metrics + structure 2:20–3:00. Hero scene in the first half |
| No code/data/assets without rights | Test clips are self-shot or license-verified footage only. No unauthorized downloaded footage |
| Theme fit (Push the Frontier) | Demo states SAM 3 used as a new physical-world capability (camouflaged-hazard advance warning) |
| Deadline Wed Nov 4 21:00 ET (= Nov 5 11:00 JST); portal submission with repo + video links + all members registered | Internal deadline 11-04 for buffer (§13 milestones) |

## 12. Success Metrics and Measurement Plan

Spec policy: **accuracy-metric targets are never asserted before measurement.** The first measurement is the baseline, and before/after improvement comparisons go in submission materials. (§9 performance SLOs are separate design targets.)

| Metric | Definition | Success criterion |
| --- | --- | --- |
| Detection rate | Share of labeled hazard segments where an alert fired (split per concept) | Secure the baseline in the hero scene (snake), then present the improvement trend in submission materials. Never hide per-concept figures |
| Alert lead time | How many seconds before hazard arrival the first alert fired | Demonstrate positive (+) lead time in the hero scene (stub verification: alert fired at frame 45 before arrival). Aim for hero-scene ≥ 2.0s as a design goal, but claim nothing pre-measurement |
| False-alarm rate | Alert frequency in hazard-free segments (per minute) | After baseline measurement, before/after comparison via cooldown/alert-distance tuning. Denominator definition finalized after F9's known limitation is resolved |
| Latency | Frame-shoot → alert-output round-trip distribution | Measured against §9.2 SLOs. Building the measurement rig comes first (measurement plan below) |

**Measurement plan**

- **Tools**: `eval/score.py` (detection rate, lead time, false-alarm rate). No latency instrumentation yet — client `performance.now()` instrumentation and server processing-time logging during the live-integration stage are the prerequisite.
- **Data**: real clips in `eval/data/` + per-file `SOURCES.md`, label manifest. Humans set hazard segments and arrival frames for labels.
- **Timing**: first baseline = right after real SAM integration (§13 11-01 – 11-02 window). Tune (prompts, cooldown, alert distances), then measure again for before/after.
- **Records**: keep result JSON with measurement conditions (model, prompts, clipset version). Never cherry-pick good clips; include failure clips in results.
- Judging-score mapping: Impact 30% (real autumn hazards, phone-only reach), Use of Meta AI Tooling 25% (SAM 3.1 + Wonder + Spark + Active Memory), Demo 25% (hero scene, live concept add, metric presentation completed in 3 minutes), Technical Depth & Execution 20% (tracking, distance estimation, false-alarm suppression, eval harness, fallbacks).

## 13. Milestones (countdown to submission)

| Date (JST) | Goal | Status |
| --- | --- | --- |
| 10-28 | Scope freeze + spec finalized, skeleton + webapp stub, PRD v0.2 | Done (stub level) |
| 10-29 – 10-31 | Real SAM integration immediately on API key receipt (incl. real frame upload), recorded-video pipeline end-to-end, test-clip labeling + `SOURCES.md` cleanup, latency instrumentation | Scheduled |
| 11-01 – 11-02 | Phone live-mode real-device check, eval harness first-baseline measurement (numbers for metrics) | Scheduled |
| 11-03 | Demo shoot/edit (per 3-min structure), metrics finalized, repo public switch + secret sweep (§9.6 gate) | Scheduled |
| 11-04 | Submission materials deadline + submit, credit claim deadline (21:00 ET) check | Scheduled |
| 11-05 11:00 | Official submission deadline (Nov 4 21:00 ET) | — |

## 14. Change History

| Version | Date | Change |
| --- | --- | --- |
| v0.1 | 2026-10-28 | Draft — product overview, scenarios, feature definitions F1–F11, non-functional requirements (prose), submission trace, success metrics |
| v0.2 | 2026-10-28 | Expanded to industry-standard PRD structure — new doc meta (purpose, audience, maintenance rules, precedence, definitions, related docs), problem definition and background, goals and non-goals, stakeholders, assumptions/constraints/risks. Non-functional requirements converted to quantitative SLO tables (latency budget breakdown, reliability failure behavior, cost cap, security, compatibility matrix, accessibility/safety notice — each with requirement/target/measurement/below-target-response/current-status). New measurement plan, milestones, change history. Folded in 3 inconsistencies found by code cross-check (F3 frame-time model, F9 false-alarm-rate denominator and missing eval/data source records, §9.8 missing on-screen safety notice) |
| v0.3 | 2026-10-31 | Corrected Meta Model API connection status — credentials stay only in the Secure Vault connection; project server no longer reads them directly. Separated officially confirmed SAM models/features/pricing from unconfirmed endpoint/schema, and reflected `RealSAMClient`'s default-inactive adapter state in F2 and cost status. Stated no real calls before credit-reflection confirmation or paid smoke-test approval |
| v0.4 | 2026-10-31 | F1 live wiring complete — webapp real-frame upload, server opt-in live mode (`TRAIL_SENTINEL_LIVE=1`), per-concept parallel calls, 2.5s minimum interval, 10s per-call timeout, frontend `"확인 불가"` state, mask PNG overlay, live approach-speed wall-clock conversion. Updated F1/F2/F3/9.2/9.4/9.5 current status from measurements (incl. 6.1s measured scan latency; 3.0s alert validity window explicitly unimplemented) |
| v0.5 | 2026-10-31 | F7 (voice/text realtime custom hazard-concept add `POST /api/concepts`), §9.2 client round-trip instrumentation and 3.0s alert validity window (`ALERT_VALIDITY_MS`), F9 `eval/score.py` false-alarm-rate denominator unification (hazard-free clip minutes basis), mobile fullscreen tactical HUD revamp, and hackathon requirements compliance audit doc (`HACKATHON_REQUIREMENTS.md`) |