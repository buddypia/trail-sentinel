# Trail Sentinel — Meta Global AI Developer Hackathon

**Real-Time Optical Trail Hazard Segmentation, Semantic Verification, and Proactive Voice Triage HUD**
Built with **Meta SAM 3.1** and the **Meta Muse** multimodal family (`Muse Spark 1.3`, `Muse Wonder 1.0`, `Muse Glimmer 30B`) for the **Meta Global AI Developer Hackathon** (Indie Track · *Push the Frontier*).

**A real-time, proactive optical HUD and voice warning system for trail hazards.**
Walk with your phone camera pointed at the path ahead—or run the built-in multi-hazard verification videos directly in your browser. Trail Sentinel continuously scans frames, segments prompt-defined hazards at the pixel level with **Meta SAM 3.1** and the **Meta Muse** multimodal family, tracks them across frames, ranks them by **severity × proximity × approach speed**, and—only when a hazard enters the danger radius—triggers an immediate directional voice alert and haptic vibration.

No extra hardware and no native app installation required: it runs directly in any desktop or mobile browser.

> **Safety Positioning:** Trail Sentinel is an **assistive tool, not a safety guarantee**. False positives or missed detections can occur depending on lighting, camouflage, and network latency. Always watch the trail with your own eyes.

---

## Repository Structure

| Path | Description |
| :--- | :--- |
| [`server.py`](./server.py) | Zero-dependency Python HTTP backend (`/api/status`, `/api/scan`, `/api/concepts`) |
| [`webapp/`](./webapp/) | Responsive optical HUD (`index.html`, `app.js`, `style.css`, `videos/`) |
| Root `.py` modules (`config.py`, `vision_router.py`, `triage.py`, `sam_client.py`, `meta_transport.py`, `pipeline.py`, `alerts.py`) | Core backend modules (flat layout, no package dir) |
| [`tests/`](./tests/) | Offline unit test suite (`unittest`) |
| [`eval/`](./eval/) | Scoring harness (`score.py`) and media license ledger (`data/SOURCES.md`) |
| [`FEATURE_MAP.md`](./FEATURE_MAP.md) | Full-stack feature index (`[FEAT:F1]`–`[FEAT:F12]`) and file/symbol reference map |
| [`videos/`](./videos/README.md) | Rights-cleared master verification videos (`individual/01..08`, combined multi-speed clips `1.0x`–`0.2x`, and `hero_how_it_works.mp4`) |
| [`docs/`](./docs/README.md) | Hackathon rules, Meta AI model specifications, architecture notes, and compliance audit |

---

## Hero Scenario

Autumn, peak leaf-fall. A venomous pit viper lies camouflaged among layers of fallen leaves on the trail—easy for a hiker's eye to miss. Trail Sentinel segments the snake's contour on the optical HUD, highlights its bounding box and bearing, and speaks a concise directional warning before you step within strike range:

> *"Underfoot ahead, 3 meters, Snake"*

Built for the **Meta Global AI Developer Hackathon** (Cerebral Valley) · **Indie Track** · Theme: **Push the Frontier** (October 26 – November 5, 2026).

---

## Key Capabilities (`F1`–`F12`)

| ID | Capability | Status | Implementation Highlights |
| :---: | :--- | :---: | :--- |
| **`F1`** | **Live Camera Scan** | ✅ Built | Captures live WebRTC camera frames (`webapp/app.js` → `POST /api/scan`) with rate-limiting and 10s timeout guardrails (`server.py`). |
| **`F2`** | **Meta AI Multi-Model Switcher & SAM 3.1 Segmentation** | ✅ Built | Switch in real time between `SAM 3.1 + Muse Spark 1.3 (Hybrid Seg + Verify)`, `Meta Muse Spark 1.3`, `Meta Muse Wonder 1.0`, `Meta Muse Glimmer 30B`, and pure `Meta SAM 3.1` (`vision_router.py`, `sam_client.py`, `meta_transport.py`). |
| **`F3`** | **Distance & Clock-Bearing Estimation + 4-KPI Strip** | ✅ Built | Ground-plane + bounding-box visual distance heuristic (`estimate_visual_distance_m`, `ground_plane_distance_estimator`) and clock-face bearing (`11` / `12` / `1 o'clock`). |
| **`F4`** | **Priority Triage (Muse Wonder Role)** | ✅ Built | Deterministic severity × proximity + approach speed scoring (`triage.py`) with severity-gated alert radii (`3.0m` / `2.5m` / `1.0m`) and 3.0s per-track anti-chatter cooldown. |
| **`F5`** | **Localized Voice Alerts (TTS), Haptics & Optical HUD** | ✅ Built | Pixel mask overlay + corner-bracket bounding boxes on HTML5 Canvas, Web Speech API (`speechSynthesis`) voice warnings, and mobile `navigator.vibrate` patterns. |
| **`F6`** | **Hero Demo Replay & Honesty Badges** | ✅ Built | Replays recorded fixture frames `0..60` (`fixtures/hero_snake_leaves.json`) with explicit `#demoBadge` and `#unknownBadge` latency/failure indicators. |
| **`F7`** | **Zero-Retraining Custom Hazard Concepts** | ✅ Built | Add new trail hazards on the fly via text or Web Speech API voice input (`POST /api/concepts` → `register_custom_hazard` in `config.py`). |
| **`F8`** | **Daily Call Budget Guard (`CallBudget`)** | ✅ Built | Atomic JSON counter (`CallBudget`, default `DAILY_CALL_CAP=200` calls/day) prevents accidental API overspend before any provider request is sent. |
| **`F9`** | **Evaluation Harness & Rights-Cleared Media** | ✅ Built | Reproducible scoring script (`eval/score.py`) measuring detection rate, warning lead time, and false-alarm rate; all media sources and open licenses documented in `eval/data/SOURCES.md`. |
| **`F10`** | **Multi-Language i18n (`EN` / `KO` / `JA`)** | ✅ Built | **English (`en`) default** across backend, CLI, API, and UI; automatic Browser/OS locale detection (`en`, `ko`, `ja`); instant UI switcher (`#langSelect`) and localized TTS. |
| **`F11`** | **Verification Video Scan & "How It Works" Showcase** | ✅ Built | Top-screen live HUD preview video (`hero_how_it_works.mp4`) plus 8-scene combined verification video scanner (`hazard_verification_combined*.mp4`) with `1.0x`, `0.5x`, `0.33x`, `0.25x`, and `0.2x` playback speeds. |
| **`F12`** | **Instant Mobile QR Access & Cloud Run Deployment** | ✅ Built | In-app QR drawer and inline QR card dynamically bound to `window.location.origin` for instant smartphone testing, backed by a keyless `Dockerfile` for Cloud Run. |

---

## Multi-Language Support (`F10`: English Default + Browser/OS Auto-Detection)

Trail Sentinel uses **English (`en`)** as its universal default across the backend, CLI, API responses, and documentation, while providing full first-class support for **English (`en`)**, **Korean (`ko`)**, and **Japanese (`ja`)**:

1. **Default Language (`en`)**: All backend modules (`triage.py`, `config.py`, `server.py`, `main.py`) and static HTML (`webapp/index.html`) default to English.
2. **Automatic Browser & OS Detection**: On initial load, the web app inspects:
   - Explicit URL parameter (`?lang=en`, `?lang=ko`, `?lang=ja`)
   - Saved user preference in `localStorage` (`trail_sentinel_lang`)
   - Browser and OS locale settings (`navigator.languages`, `navigator.language`, and `Intl.DateTimeFormat().resolvedOptions().locale`)
   - If the browser or OS locale matches English (`en`), Korean (`ko`), or Japanese (`ja`), that language is automatically selected; otherwise, it falls back to **English (`en`)**.
3. **Interactive UI Switcher**: Users can switch languages at any time using the top HUD selector (`Lang`: `English (EN)` / `한국어 (KO)` / `日本語 (JA)`). Switching immediately updates all UI labels, concept filter chips, model descriptions, AI verification notes, and Web Speech API voice alerts (`en-US`, `ko-KR`, `ja-JP`).

---

## Quickstart

### 1. Run the Web App (`http://localhost:8765`)

```bash
python3 server.py
```

Open `http://localhost:8765` in your browser:
- **Start Camera Scan**: Streams your device camera and segments hazards in real time.
- **Scan Verification Video (Snake · Boar · Bear)**: Streams the built-in 8-scene wildlife verification video through the live AI pipeline (with selectable `0.2x` to `1.0x` speed and automatic frame freeze on detection).
- **Play Hero Demo Scene (Frames 0..60)**: Replays the recorded camouflaged snake scenario with zero network or API calls.

### 2. Run the CLI Demo (No API Key, No Network)

```bash
python3 main.py
# Optional language flag (default: en):
python3 main.py --lang en
python3 main.py --lang ko
python3 main.py --lang ja
```

### 3. Run Unit Tests & Evaluation Harness

```bash
# Run all unit tests (no network or external API calls)
python3 -m unittest discover -s tests -v

# Run evaluation scoring harness
python3 eval/score.py
```

---

## Live Mode & Cost Guardrails

1. **Zero Credentials in Code**: No API keys or secrets are stored in this repository. On the Meta Hackathon VM, `MetaSAMTransport` invokes the Secure Vault connector helper (`custom.meta-model-api`) via subprocess (`TRAIL_SENTINEL_META_HELPER`). On Cloud Run, `vision_router.py` uses keyless IAM Application Default Credentials.
2. **Hard Daily Call Cap (`CallBudget`)**: Every scan passes through `CallBudget` (`.call_counter.json`, default `DAILY_CALL_CAP=200`). Pre-flight checks refuse any scan that would exceed the daily cap before making a provider call.

---

## Architecture

```text
Browser HUD (webapp/index.html, app.js, style.css)
  ├─ Input: Live Camera (getUserMedia) | Verification Video (0.2x..1.0x) | Hero Demo (Frames 0..60)
  ├─ Locale: Auto-detects Browser/OS (en / ko / ja, default en) + Top-bar UI Switcher (#langSelect)
  └─ Output: Canvas pixel mask + bracket bbox, 4-KPI telemetry strip, localized TTS & vibration
        │
        ▼  POST /api/scan  |  POST /api/concepts  |  GET /api/status
Backend Server (server.py — Python stdlib only)
  ├─ CallBudget (.call_counter.json, 200 calls/day cap)
  ├─ LiveScanner (vision_router.py, sam_client.py, meta_transport.py)
  │    ├─ Single-pass Hybrid Segmentation + Semantic Verification (SAM 3.1 + Muse Spark / Wonder / Glimmer)
  │    └─ Pure SAM 3.1 per-concept connector subprocess (Meta Model API /v1/responses)
  ├─ Distance & Bearing Estimator (ground_plane_distance_estimator / estimate_visual_distance_m)
  └─ Priority Triage (triage.py: severity × proximity + approach speed, 3s cooldown)
       └─ Emits localized alert payload:
          • EN: "Underfoot ahead, 3 meters, Snake"
          • KO: "발 앞 3미터, 뱀"
          • JA: "足元前方 3メートル、ヘビ"
```

### Baseline Hazard Concepts (`config.py`)

| Key | English (`en`) | Korean (`ko`) | Japanese (`ja`) | Zone | Severity | Default Prompt |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| `snake` | Snake | 뱀 | ヘビ | `feet` | `3` (Danger) | `a snake camouflaged among fallen leaves and soil` |
| `wasp_nest` | Wasp nest | 말벌집 | スズメバチの巣 | `front` | `3` (Danger) | `a wasp nest attached to a tree, rock or structure` |
| `bear` | Bear | 곰 | クマ | `front` | `3` (Danger) | `a bear on or near the trail` |
| `boar` | Wild boar | 멧돼지 | イノシシ | `front` | `2` (Caution) | `a wild boar on or near the trail` |
| `rockfall` | Rockfall zone | 낙석 구간 | 落石区間 | `front` | `2` (Caution) | `a pile of fallen rocks or a collapsed trail section` |
| `slippery` | Slippery path | 미끄러운 구간 | 滑りやすい路面 | `feet` | `1` (Notice) | `a hidden hole, protruding root or wet slippery fallen leaves underfoot` |

Additional custom concepts (e.g., *Fallen tree*, *Cliff edge*, *Bicycle*, *Black ice*) can be added at runtime without retraining via the **+ Add Concept** bar or `POST /api/concepts`.

---

## Documentation

- [`AGENTS.md`](./AGENTS.md) — Agent working agreements, workspace map, and compliance guardrails
- [`FEATURE_MAP.md`](./FEATURE_MAP.md) — Full-stack feature map (`F1`–`F12`) and quick-lookup modification guide
- [`PRD.md`](./PRD.md) — Product requirements, functional scope, acceptance criteria, and SLOs
- [`TECH.md`](./TECH.md) — Architecture and technology decisions
- [`DEPLOY.md`](./DEPLOY.md) — Local server, Cloud Run container, and tunnel deployment guide
- [`HACKATHON_REQUIREMENTS.md`](./HACKATHON_REQUIREMENTS.md) — Hackathon eligibility rules and compliance checklist
- [`docs/`](./docs/README.md) — Hackathon rules, Meta AI model specs, application drafts, and audit reports
- [`videos/`](./videos/README.md) — Master verification video assets and scene catalog
- [`eval/data/SOURCES.md`](./eval/data/SOURCES.md) — Per-file media sources and open-license attributions

## License

MIT — see [`LICENSE`](./LICENSE).
