# Trail Sentinel

**A real-time, proactive warning system for trail hazards.** Walk with your
phone camera pointed at your feet and the path ahead: the app continuously
scans each frame, segments hazards defined by plain-text prompts with
Meta's SAM 3.1, tracks them across scans, ranks them by severity ×
proximity × approach speed, and — only when one is actually dangerous —
warns you with a short voice alert and vibration before you reach it.
No extra hardware, no app install: it runs in the phone browser.

> **Safety positioning:** Trail Sentinel is an **assistive tool, not a
> safety guarantee** (보조 도구 — 안전 보장 안 함). It can miss hazards and
> can raise false alarms. Always watch the trail yourself.

**Hero scenario:** autumn, peak leaf-fall. A mamushi (pit viper) lies
camouflaged between layers of fallen leaves on the trail — the hiker's eye
slides right over it. Trail Sentinel masks it on screen and warns:
*"발 앞 3미터, 뱀"* ("3 metres ahead of your feet: a snake").

Built for the **Meta Global AI Developer Hackathon** (Cerebral Valley) ·
Indie track · Theme: **Push the Frontier**. All code in this repository was
built during the hackathon event window, **October 26 – November 4, 2026**.

## Feature status (honest)

| Capability | Status |
| --- | --- |
| Continuous scan loop, priority triage, voice + vibration alerts | ✅ Built (deterministic triage in `trail_sentinel/triage.py`) |
| SAM 3.1 segmentation via Meta Model API | ✅ **Verified live on 2026-10-31** — `sam-3.1` confirmed in the models list; hero snake still segmented (1 box + mask, ~3.0 s, $0.0025 within the hackathon credit) |
| Live camera frames → real SAM → overlay (F1) | ✅ Built — webapp sends real frames; server calls SAM per concept in parallel, decodes masks to PNG overlays; opt-in via `TRAIL_SENTINEL_LIVE=1` only |
| End-to-end live latency | ⚠️ **Measured 6.1 s per scan** (1 concept) vs the PRD target of p50 ≤ 1.5 s — a known miss, recorded in `PRD.md` §9.2; the 3 s alert-validity discard is deliberately not enforced yet |
| Distance to hazard | ⚠️ Estimate only — SAM returns no distance; a documented, uncalibrated ground-plane heuristic is used. SAM also returns no confidence score (shown as none, never invented) |
| Voice-added custom hazards (F7), route memory (F10), reports (F11) | ❌ Not built — hazard set is the fixed 6 concepts in `trail_sentinel/config.py` |
| Deployment | ⚠️ Server runs on the dev machine; `deploy/start_demo.sh` serves it behind a Cloudflare quick tunnel where network policy allows (see `DEPLOY.md`) |

## Quickstart — demo mode (no API key, no network)

```bash
cd trail-sentinel
python3 main.py        # CLI: hero scene frames 0..60, one snake alert + cooldown
python3 server.py      # web app on http://localhost:8765
```

Open the URL in a browser and choose **데모 모드** (demo mode): it replays
the recorded hero scene and shows the full scan → triage → alert flow,
clearly badged as a replay. Or allow the camera and scan in stub mode —
the status line always says which mode is active; stub results are never
presented as live analysis.

Run the tests (no network, no provider calls):

```bash
python3 -m unittest discover -s tests
```

## Live mode (real SAM 3.1)

Live inference is **off by default** and deliberately hard to enable
accidentally:

1. The Meta Model API credential must live in the Secure Vault connection
   of the companion connector (`custom.meta-model-api`). **No credential is
   ever stored in this project** — the transport shells out to the
   connector's helper script, which is the only component that talks to
   the API.
2. Point the transport at the helper (defaults to the dev-machine path):
   `export TRAIL_SENTINEL_META_HELPER=/path/to/meta_model_api.py`
   If the helper is missing, live mode fails with a clear
   "not configured" error instead of half-working.
3. Start the server with `TRAIL_SENTINEL_LIVE=1 python3 server.py`.

**Cost guardrails.** Meta's Spend Limit is a notification, not a cap, so
this project enforces its own: every concept call passes through
`CallBudget` (daily cap 200 calls, JSON counter). At $0.0025 per image
call, the worst case is **$0.50/day** — the cap, not the price, is the
physical spend ceiling. Budget pre-flight refuses a scan before any spend
if it would exceed the cap.

## Architecture

```
phone browser (webapp/: getUserMedia camera, canvas overlay,
               ko-KR TTS, vibration, demo replay mode)
  → POST /api/scan  (frame image or demo frame index)
server.py (Python stdlib only)
  → StubSAMClient (demo/stub)  OR  LiveScanner (live, opt-in)
      → RealSAMClient → MetaSAMTransport → connector helper subprocess
        → Meta Model API, POST /v1/responses, model "sam-3.1"
          (one short noun-phrase prompt per request, streamed
           box + one-bit mask records; masks decoded with meta-sam-parser)
  → triage.evaluate(): severity × proximity + approach speed,
    cooldown, one top alert ("11시 방향 발 앞 3미터, 뱀")
  → browser draws mask + box, red banner, speaks, vibrates
```

Hazard concepts v1 (frozen): snake, wasp nest, bear, boar, rockfall,
underfoot bundle (roots / wet leaves / holes) — `trail_sentinel/config.py`.
New hazards need **no retraining**: a concept is just a text prompt to
SAM 3.1.

## Evaluation data

`eval/` contains the scoring harness (`score.py`: detection rate, warning
lead time, false-alarm rate), the clip manifest
(`eval/clips_manifest.json`), and still images. Per-file sources and
licences are recorded in **`eval/data/SOURCES.md`** — only self-shot or
verifiably licensed media is used. Video files are excluded from git by
`.gitignore` (size); they are listed in the manifest with their licences.

## Documents

- `PRD.md` — requirements, functions F1–F11, acceptance criteria, SLOs
- `TECH.md` — technology choices and rationale
- `AGENTS.md` — project entry point, current status, guardrails
- `DEPLOY.md` — running the public demo, live-mode warnings

## License

MIT — see `LICENSE`.
