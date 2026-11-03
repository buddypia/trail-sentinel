# 05. Meta Global AI Developer Hackathon Requirements and Trail Sentinel Compliance Audit Report

> **Sync source**: [`../HACKATHON_REQUIREMENTS.md`](../HACKATHON_REQUIREMENTS.md)
> **Reference documents**:
> - [`01-hackathon-overview-and-rules.md`](./01-hackathon-overview-and-rules.md)
> - [`02-meta-ai-models-and-tooling.md`](./02-meta-ai-models-and-tooling.md)
> - [`../PRD.md`](../PRD.md) (v0.5)
> - [`../AGENTS.md`](../AGENTS.md)

---

## 1. Official Hackathon Mandatory Requirements Checklist

1. **Core use of Meta AI models (`Use of Meta AI Tooling` — 25% of judging score & first-pass eligibility criterion)**
   - Must use Meta Model API (`SAM 3.1`, `Muse Wonder`, `Muse Spark 1.3`, `Muse Image`, `Muse Voice Transcribe`) or Meta open-weight models (`Muse Spark Open 816B`, `Muse Glimmer 30B`) as a core feature of the project.
2. **Strictly observe the new-work period (2026-10-26 – 2026-11-04)**
   - Only code written during the hackathon period is eligible for evaluation; commit history and documentation must clearly distinguish newly implemented scope from pre-existing assets.
3. **Public GitHub repository required & zero secrets**
   - Public GitHub repository submission required.
   - No API keys or secrets anywhere in code, commit history, frontend, or logs.
4. **3-minute demo video & reproducible demo (F6)**
   - Demo video of max 3 minutes required.
   - Judges must be able to clone the repo and verify the full pipeline with a basic keyless run (`python3 server.py`).
5. **Data/media license eligibility (`eval/data/SOURCES.md`)**
   - Only self-recorded or license-verified (Public Domain, CC0, CC BY, Pexels, etc.) media may be used; using unauthorized downloaded videos results in disqualification.
6. **Safety notice and positioning rules**
   - Position as a realtime active warning system (continuous scanning + tracking + priority judgment + voice/vibration alerts), not a "simple image analyzer."
   - Banned: "guarantees/prevents safety" claims and definitive species-level safety judgments (must state it is an "assistive tool").

---

## 2. Trail Sentinel Hackathon Compliance Inspection and Completed Fixes (All Items Passed ✅)

| # | Inspection Item | Compliance | Completed Actions |
| :---: | :--- | :---: | :--- |
| 1 | **Meta AI model centrality (`Tooling` 25%)** | ✅ **Pass** | Removed all third-party model references from `meta_transport.py`, `server.py`, and `webapp/`, and restored the official **Meta SAM 3.1 (concept segmentation/tracking) + Muse Wonder role-decisive judgment (`triage.py`)** architecture |
| 2 | **No direct env-var key loading (`PRD.md` §9.6)** | ✅ **Pass** | Completely removed direct env-var API key loaders (`*_API_KEY`) from `meta_transport.py`, keeping only the `$TRAIL_SENTINEL_META_HELPER` subprocess boundary |
| 3 | **Protect live Cloud Run URL in public repo** | ✅ **Pass** | Removed the hardcoded Cloud Run URL from `webapp/index.html` in favor of dynamic `window.location.origin` display; kept default `DAILY_CALL_CAP=200` |
| 4 | **Realtime scan (F1) + demo/stub reproducibility (F6)** | ✅ **Pass** | Fullscreen tactical HUD supports both `📷 실시간 스캔 시작` ("Start Live Scan") and `▶ 데모` ("Demo"), and works perfectly with the honesty badge (`#demoBadge`) even in default `python3 server.py` (stub mode) |
| 5 | **Realtime custom hazard concept addition (F7)** | ✅ **Pass** | Implemented `POST /api/concepts` and the frontend `＋ 개념 추가` ("Add Concept") control (Korean voice recognition 🎙 + text input), verified by unit tests (`CustomConceptTests`) |
| 6 | **3.0-second alert validity period (§9.2) & honesty principle** | ✅ **Pass** | Implemented discarding of responses exceeding `ALERT_VALIDITY_MS = 3000` with fallback to the `"확인 불가"` ("Unable to verify") badge; artificial distance clamping removed |
| 7 | **Unified eval false-alarm-rate denominator (F9) & data copyright** | ✅ **Pass** | Unified `eval/score.py` to output the false-alarm rate on both the safe-clip minute basis and the full-video minute basis; `eval/data/SOURCES.md` completed |
| 8 | **Secret audit (`secret audit`) & unit tests (`34/34`)** | ✅ **Pass** | `secret audit` 0 findings, unit tests `34/34` all passing |
