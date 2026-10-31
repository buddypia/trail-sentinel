#!/usr/bin/env bash
# Stop the Trail Sentinel demo (server + tunnel started by start_demo.sh).
set -uo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for name in tunnel server; do
  pidfile="$DEPLOY_DIR/$name.pid"
  if [ -f "$pidfile" ]; then
    pid="$(cat "$pidfile")"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      echo "stopped $name (pid $pid)"
    fi
    rm -f "$pidfile"
  fi
done

rm -f "$DEPLOY_DIR/current_url.txt"
echo "demo stopped"
