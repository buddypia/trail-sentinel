# DEPLOY.md — Trail Sentinel Deployment Guide

_Last updated: 2026-11-03_

## 1. Local Execution

Start the web server locally (defaults to port `8765`):

```bash
# Live mode (enabled by default when TRAIL_SENTINEL_LIVE=1)
python3 server.py

# Explicit stub-only mode ($0 spend, uses recorded fixtures)
TRAIL_SENTINEL_LIVE=0 python3 server.py
```

Open `http://localhost:8765` in your browser:
- **Language Auto-Detection & Switcher**: The UI defaults to **English (`en`)**, automatically selects **English (`en`)**, **Korean (`ko`)**, or **Japanese (`ja`)** when detected from your browser/OS locale, and allows switching languages at any time via the top-bar `Lang` selector (`?lang=en|ko|ja`).
- **Mobile QR Access**: Click **Mobile QR** in the top bar (or scan the inline QR card on the standby screen) to open the current deployment URL directly on a smartphone.

---

## 2. Cloud Run Container Deployment

Trail Sentinel ships with a production `Dockerfile` that runs keyless on Google Cloud Run (`asia-northeast1`):

```bash
gcloud run deploy trail-sentinel \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated
```

- **Keyless Architecture**: No API keys are baked into the container image or environment variables.
- **Cost Guardrail**: `CallBudget` enforces a hard daily ceiling (`DAILY_CALL_CAP=200` calls/day) per instance.

---

## 3. Quick Tunnel (Local Network Sharing)

On a standard network with `cloudflared` installed:

```bash
./deploy/start_demo.sh
cat deploy/current_url.txt
./deploy/stop_demo.sh
```

- `start_demo.sh` launches the server in stub mode by default so a public tunnel URL cannot accidentally consume live API credits.

---

## 4. Local API Smoke Checks

```bash
# Check server status, models, hazards, and default language ("en")
curl -s http://localhost:8765/api/status

# Run one demo scan frame in English (default), Korean, or Japanese
curl -s -X POST http://localhost:8765/api/scan \
  -H 'Content-Type: application/json' \
  -d '{"frame_index": 45, "mode": "demo", "lang": "en", "reset": true}'
```
