# Meta Global AI Developer Hackathon — Official Requirements and Trail Sentinel Compliance Audit Report

> **Last updated**: 2026-10-31
> **Sources**:
> 1. Official event page: <https://cerebralvalley.ai/e/meta-ai-developer-hackathon> (`meta-ai-developer-hackathon.md`)
> 2. Official rules and waiver: <https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver> (including `Credit Terms`)
> 3. Meta AI developer portal: <https://dev.meta.ai/docs/overview>
> 4. Internal project reference docs: [`PRD.md`](./PRD.md) (v0.5), [`AGENTS.md`](./AGENTS.md), [`TECH.md`](./TECH.md), [`DEPLOY.md`](./DEPLOY.md)

---

## Part 1. Meta Global AI Developer Hackathon Official Requirements

### 1. Event overview and schedule
- **Hosts**: Meta & Cerebral Valley
- **Format**: 100% online (Worldwide Virtual)
- **Hackathon build period**: **2026-10-26 12:00 PM EDT ~ 2026-11-04 09:00 PM EST**
  - Deadline in Korea/Japan Standard Time (KST/JST): **2026-11-05 (Thu) 11:00 AM KST/JST**
- **Submission portal**: <https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit>
- **Tracks and prizes (total $1,000,000)**:
  - **Indie Developer Track ($400,000)**: individual builders, students, and teams of up to 4 (1st $150k, 2nd $100k, 3rd $75k, 4th $50k, 5th $25k) — emphasis on *Creativity, Technical Ambition, and Whether it works*
  - **Startup Track ($550,000)**: technical founders and startup teams (1st $250k, etc.)
  - **Bonus Prizes ($50,000)**: Community Vote Award, Most Viral Project Award, etc.
- **Trail Sentinel's track and theme**:
  - **Track**: **Indie Developer Track** (solo developer: Jun)
  - **Theme**: **Push the Frontier** (*"Give a machine a new capability... Show us what becomes possible when these models meet the real world."*)

---

### 2. Official judging criteria and weights (Judging Criteria — 100%)

| Criterion | Weight | Official detailed criteria |
| :--- | :---: | :--- |
| **1. Impact** | **30%** | Real-world potential, clarity of beneficiaries, importance of the problem, whether people can actually use the product, and fit with the chosen theme (`Push the Frontier`) |
| **2. Use of Meta AI Tooling** | **25%** | **How creatively the project uses Meta's AI models (`SAM 3.1`, `Muse Wonder`, `Muse Spark`, `Muse Image`, `Muse Voice Transcribe`, `Muse Glimmer`, etc.) and tools**, and whether it draws out unexpected new capabilities beyond basic integration |
| **3. Demo** | **25%** | Whether there is an impressive, actually working demo, **whether the product holds up live**, and the quality of the 3-minute demo video |
| **4. Technical Depth & Execution** | **20%** | Whether the engineering is solid and thoughtfully polished, and whether the project shows real craft |

---

### 3. Mandatory deliverables and disqualification gates (Mandatory Rules & Disqualification Gates)

1. **Mandatory use of Meta AI models (Core Tooling Requirement)**
   - Submitted projects must use the Meta Model API (`SAM 3.1`, `Muse Wonder`, `Muse Spark 1.3`, `Muse Image`, `Muse Voice Transcribe`) or Meta open-weight models (`Muse Spark Open`, `Muse Glimmer`) as a core feature.
2. **Build-period compliance & contribution identifiability (New Work Only)**
   - Only work created within the official hackathon period (**2026-10-26 ~ 2026-11-04**) is eligible for judging.
   - Judges must be able to clearly distinguish pre-existing open source, browser standard APIs, and external assets from code newly written during the hackathon period (failure to distinguish means disqualification).
3. **Public GitHub repository required (Public Repository)**
   - On submission, the GitHub repository containing the full source code must be **Public**, and judges must be able to clone it to inspect and run the project.
   - The repository and commit history must **never contain API keys or secrets**.
4. **3-minute demo video required (3-Minute Demo Video)**
   - As the key evidence for judging rounds 1–2, a working demo video of up to 3 minutes must be submitted.
5. **Data, code, and media copyright/license compliance (Authorized Assets Only)**
   - Including unlicensed code, unauthorized downloaded YouTube videos, or license-unverified images/datasets in the submission materials or repo means disqualification.
   - Only self-recorded footage or media with verified and documented licenses (Public Domain, CC0, CC BY, Pexels License, etc.) may be used.
6. **Patterns to avoid / prohibited (Prohibited / Low-Score Patterns)**
   - Avoid a **"simple image analyzer / basic wrapper"**: the project must be a real-time system performing continuous scanning, tracking, priority triage, and proactive alerts — not a simple wrapper that takes one photo and outputs a description.
   - **No safety/medical/legal guarantee claims**: do not claim to prevent accidents or guarantee safety 100%, or to judge safety via venomous/non-venomous species identification (state that it is an "assistive tool").

---

## Part 2. Trail Sentinel compliance check and remediation results (all items pass ✅)

| # | Check area | Status | Remediation and verification |
| :---: | :--- | :---: | :--- |
| **1** | **Meta AI model centrality (`Use of Meta AI Tooling`, 25%)** | ✅ **Compliant** | Removed all third-party model references from [`meta_transport.py`](./meta_transport.py), [`server.py`](./server.py), [`webapp/index.html`](./webapp/index.html), and [`webapp/app.js`](./webapp/app.js), aligning them into the single official pipeline of **Meta SAM 3.1 (concept segmentation & tracking) + deterministic triage in the Muse Wonder role (`triage.py`)** |
| **2** | **API key & security architecture (`PRD.md` §9.6 & `AGENTS.md`)** | ✅ **Compliant** | `secret audit` passed with **0 findings**. The project code contains no environment-variable key loaders (`*_API_KEY`); `MetaSAMTransport` operates only across the external connector helper (`$TRAIL_SENTINEL_META_HELPER`) subprocess boundary |
| **3** | **Public-repo credit protection (`PRD.md` §9.5 & `DEPLOY.md`)** | ✅ **Compliant** | Removed the hard-coded Cloud Run URL string from [`webapp/index.html`](./webapp/index.html), switching to dynamic `window.location.origin` binding; kept the default daily call cap `DAILY_CALL_CAP=200` |
| **4** | **Live camera (F1) + demo mode (F6) + stub compatibility** | ✅ **Compliant** | The full-screen tactical HUD supports both **`📷 실시간 스캔 시작`** ("Start live scan") and **`▶ 데모`** ("Demo"); even a plain `python3 server.py` run with no API key works without errors — stub simulation, hero-scene replay, and the honesty badge (`#demoBadge`) all function normally |
| **5** | **Real-time custom hazard-concept creation without retraining (F7)** | ✅ **Implemented & verified** | `POST /api/concepts` ([`server.py`](./server.py), [`config.py`](./config.py)) and the frontend `＋ 개념 추가` ("Add concept") control (Web Speech Recognition `ko-KR` voice input 🎙 + text input) implemented |
| **6** | **Latency measurement & 3.0 s alert validity window (`PRD.md` §9.2) & honesty** | ✅ **Implemented & verified** | [`webapp/app.js`](./webapp/app.js) measures round-trip latency against capture time; responses exceeding `ALERT_VALIDITY_MS = 3000` have their alerts discarded and show the `"확인 불가"` ("unable to verify") badge. Artificial distance clamping removed |
| **7** | **Eval false-alarm-rate denominator alignment (`PRD.md` F9) & data licensing** | ✅ **Compliant** | [`eval/score.py`](./eval/score.py) now reports both the per-minute false-alarm rate over hazard-free clips and over total video minutes. `eval/data/SOURCES.md` documents all 14 media licenses |
| **8** | **New-work period (10/26~11/04), safety notice, unit tests** | ✅ **Compliant** | All commits dated 2026-10-31, MIT license stated, assistive-tool notice always shown at the bottom of the screen, unit tests **34/34 passing** |
