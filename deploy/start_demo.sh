#!/usr/bin/env bash
# Start the Trail Sentinel demo: stub-mode web server + Cloudflare quick tunnel.
#
# The server ALWAYS runs in stub/demo mode here (TRAIL_SENTINEL_LIVE is
# explicitly unset) so a public URL can never spend Meta API credit.
# The quick-tunnel URL is EPHEMERAL: it changes every time this script runs
# (and dies with the VM). The current URL is written to deploy/current_url.txt.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOY_DIR="$PROJECT_DIR/deploy"
LOG_DIR="$DEPLOY_DIR/logs"
PORT="${PORT:-8765}"
mkdir -p "$LOG_DIR"

CLOUDFLARED="${CLOUDFLARED:-}"
if [ -z "$CLOUDFLARED" ]; then
  if [ -x "$HOME/workspace/bin/cloudflared" ]; then
    CLOUDFLARED="$HOME/workspace/bin/cloudflared"
  elif command -v cloudflared >/dev/null 2>&1; then
    CLOUDFLARED="$(command -v cloudflared)"
  else
    echo "cloudflared not found. Install the official binary, e.g.:" >&2
    echo "  curl -sL -o ~/workspace/bin/cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 && chmod +x ~/workspace/bin/cloudflared" >&2
    exit 1
  fi
fi

# Stop any previous demo processes first (idempotent restart).
"$DEPLOY_DIR/stop_demo.sh" >/dev/null 2>&1 || true

echo "Starting stub server on port $PORT ..."
(
  cd "$PROJECT_DIR"
  env -u TRAIL_SENTINEL_LIVE PORT="$PORT" \
    nohup python3 server.py >"$LOG_DIR/server.log" 2>&1 &
  echo $! >"$DEPLOY_DIR/server.pid"
)

for _ in $(seq 1 30); do
  if curl -sf "http://localhost:$PORT/api/status" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
curl -sf "http://localhost:$PORT/api/status" >/dev/null || {
  echo "server did not come up; see $LOG_DIR/server.log" >&2
  exit 1
}

echo "Starting Cloudflare quick tunnel ..."
: >"$LOG_DIR/tunnel.log"
(
  nohup "$CLOUDFLARED" tunnel --url "http://localhost:$PORT" --no-autoupdate \
    >"$LOG_DIR/tunnel.log" 2>&1 &
  echo $! >"$DEPLOY_DIR/tunnel.pid"
)

URL=""
for _ in $(seq 1 45); do
  # The log also mentions https://api.trycloudflare.com (the API host, NOT
  # the tunnel URL) — exclude it explicitly.
  URL="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG_DIR/tunnel.log" | grep -v '^https://api\.trycloudflare\.com$' | head -1 || true)"
  [ -n "$URL" ] && break
  # Fail fast if cloudflared already exited (e.g. tunnel request rejected).
  TUNNEL_PID="$(cat "$DEPLOY_DIR/tunnel.pid" 2>/dev/null || true)"
  if [ -n "$TUNNEL_PID" ] && ! kill -0 "$TUNNEL_PID" 2>/dev/null; then
    break
  fi
  sleep 1
done
if [ -z "$URL" ]; then
  echo "tunnel URL not found; see $LOG_DIR/tunnel.log" >&2
  exit 1
fi

printf '%s\n' "$URL" >"$DEPLOY_DIR/current_url.txt"
echo "Demo is live (stub mode): $URL"
echo "URL saved to deploy/current_url.txt (ephemeral — changes on restart)."
