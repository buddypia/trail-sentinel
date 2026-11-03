# AGENTS.md — Meta Global AI Developer Hackathon & Trail Sentinel

> **For per-feature implementation locations and reverse-lookup recipes, read [`FEATURE_MAP.md`](./FEATURE_MAP.md) first.**
> Search the `[FEAT:F1]`–`[FEAT:F12]` tags in code with `rg -n "\[FEAT:" .` to jump to the matching lines in one second.

**Overview**: Continuously scan hiking trails with a smartphone camera (or verification videos), detect hazards with Meta SAM 3.1 (text-prompt concept segmentation) + Muse (semantic verification / priority triage), and fire trilingual (EN/JA/KO) voice + vibration alerts only when a hazard enters the danger radius — a real-time trail hazard detection HUD. Meta Global AI Developer Hackathon (Indie Track / Push the Frontier), submission deadline **2026-11-05 11:00 JST**.

## 1. Workspace Layout (Where Everything Lives)

| Purpose | Files |
| :--- | :--- |
| **Where to fix which feature (feature IDs, functions, DOM IDs, reverse-lookup recipes)** | **[`FEATURE_MAP.md`](./FEATURE_MAP.md)** |
| App core (web backend, HUD, CLI, root `.py` modules) | `server.py`, `main.py`, `config.py`, `vision_router.py`, `triage.py`, `sam_client.py`, `meta_transport.py`, `pipeline.py`, `alerts.py`, `webapp/` |
| Unit tests, evaluation harness, license ledger | `tests/`, `eval/score.py`, `eval/data/SOURCES.md` |
| Product requirements, tech choices, eligibility requirements, deploy procedures | `PRD.md`, `TECH.md`, `HACKATHON_REQUIREMENTS.md`, `DEPLOY.md` |
| Hackathon official rules & prize split (`01`), new Meta AI model specs (`02`), idea proposals (`03`), application answers (`04`), conformance audit reports (`05`) | [`docs/`](./docs/README.md) |
| Verification video masters (`individual/01..08` — 8 individual clips, combined `hazard_verification_combined*.mp4`, hero-screen demo `hero_how_it_works.mp4`) | [`videos/`](./videos/README.md) |
| Compressed videos for web delivery (referenced relatively from `webapp/`) | `webapp/videos/` |

## 2. Feature ID Quick Summary (`F1`–`F12`)

| ID | Feature | Primary frontend (`webapp/`) | Primary backend (`server.py` + root `.py`) | Status |
| :---: | :--- | :--- | :--- | :---: |
| **`F1`** | Live Camera Scan | `app.js`: `startLiveScan`, `captureFrame`, `scanOnce` | `server.py`: `LiveScanner.scan`, `Handler._scan_live` | ✅ Implemented |
| **`F2`** | Meta AI Multi-Model Switcher & SAM 3.1 Segmentation | `index.html`: `#modelSelect`<br>`app.js`: `syncModelOptionsUI` | `vision_router.py`: `AVAILABLE_MODELS`, `scan_with_vertex_vision`<br>`sam_client.py`, `meta_transport.py` | ✅ Implemented |
| **`F3`** | Distance & Clock-Bearing Estimation + 4-KPI Strip | `index.html`: `#kpiDistance`, `#kpiDirection`<br>`app.js`: `updateTelemetryKpis` | `vision_router.py`: `estimate_visual_distance_m`<br>`meta_transport.py`: `ground_plane_distance_estimator` | ✅ Implemented |
| **`F4`** | Priority Triage (Muse Wonder Role) | `app.js`: `data.alert` handling | `triage.py`: `evaluate`, `score`, `ALERT_DISTANCE_M`, `COOLDOWN_FRAMES` | ✅ Implemented |
| **`F5`** | Localized Voice Alerts (TTS), Haptics & Optical HUD | `index.html`: `#overlay`, `#alertBanner`, `#btnAudio`<br>`app.js`: `drawBoxes`, `fireAlert`, `speakAlert`/`pickAlertAudio`/`playAlertAudio`, `speakText` (fallback)<br>`webapp/audio/` (126 pre-generated MP3) | `vision_router.py`: `synthesize_contour_mask_png`<br>`triage.py`: `phrase_for`<br>`tools/make_voice.py` (neural fragment generator) | ✅ Implemented |
| **`F6`** | Hero Demo Replay & Honesty Badges | `index.html`: `#btnDemoHero`, `#demoBadge`, `#unknownBadge`<br>`app.js`: `startDemoMode`, `registerFailure` | `server.py`: `scan_frame`<br>`sam_client.py`: `StubSAMClient`<br>`fixtures/hero_snake_leaves.json` | ✅ Implemented |
| **`F7`** | Zero-Retraining Custom Hazard Concepts | `index.html`: `#btnAddConcept`, `#conceptForm`, `#btnVoiceConcept` | `server.py`: `add_concept` (`POST /api/concepts`)<br>`config.py`: `register_custom_hazard` | ✅ Implemented |
| **`F8`** | Daily Call Budget Guard (CallBudget) | `index.html`: `#kpiBudget` | `config.py`: `CallBudget`, `.call_counter.json` (cap 200/day) | ✅ Implemented |
| **`F9`** | Evaluation Harness & Rights-Cleared Media | — | `eval/score.py`, `eval/clips_manifest.json`, `eval/data/SOURCES.md` | ✅ Implemented |
| **`F10`** | Multi-Language i18n (EN/KO/JA) | `index.html`: `#langSelect`<br>`app.js`: `I18N`, `applyLanguage` | `config.py`: `Hazard.label_for`<br>`triage.py`: `phrase_for(det, lang)` | ✅ Implemented |
| **`F11`** | Verification Video Scan & How-It-Works Showcase | `index.html`: `#heroShowcaseVideo`, `#btnVerifyVideoHero`<br>`app.js`: `startVerificationVideoScan` | `webapp/videos/hero_how_it_works.mp4`<br>`webapp/videos/hazard_verification_combined*.mp4` | ✅ Implemented |
| **`F12`** | Instant Mobile QR Access & Cloud Run Deployment | `index.html`: `#btnQrModal`, `#qrPanel`<br>`app.js`: `loadStatus` (`window.location.origin`) | `Dockerfile`, `DEPLOY.md` | ✅ Implemented |

## 3. Run & Verify Commands

```bash
# 1. Feature-tag search (instantly locate edit points)
rg -n "\[FEAT:" .

# 2. Run all unit tests (no network needed, 0.02 s)
python3 -m unittest discover -s tests -v

# 3. CLI stub demo & evaluation harness
python3 main.py
python3 eval/score.py

# 4. Start the web app (default: port 8765)
python3 server.py
```

## 4. Absolute Rules (Hackathon Disqualification-Prevention Guardrails)

- **Zero secrets**: never write API keys or tokens in code, config files, git history, or logs.
- **Budget guard required (`F8`)**: route every scan call through `CallBudget` (default `DAILY_CALL_CAP=200`).
- **Rights-cleared media only (`F9`)**: use only self-shot or open-license (Pexels / Wikimedia CC) images and videos for tests and verification, and cite sources in `eval/data/SOURCES.md`.
- **Honesty display (`F6`) & assistive-tool labeling**: always disclose demo/stub/verification-video playback with `#demoBadge`, and show `#unknownBadge` ("確認不可") when live latency is exceeded. Never claim safety guarantees (label it an assistive tool).
