#!/usr/bin/env bash
# Restart helper for the app on port 8443.
# Usage:
#   ./scripts/restart-app.sh          # stop + wait (full restart, needs external start)
#   ./scripts/restart-app.sh stop     # kill process on port 8443
#   ./scripts/restart-app.sh wait     # poll until app is ready
# Exit code: 0 if success, 1 if timeout/failure

set -uo pipefail

PORT=8443
URL="http://localhost:$PORT/dev/login"
MAX_ATTEMPTS=20
SLEEP_INTERVAL=2

stop_app() {
  local pids
  pids=$(lsof -ti tcp:$PORT 2>/dev/null || true)
  if [ -z "$pids" ]; then
    echo "No process on port $PORT."
    return 0
  fi

  echo "Stopping PIDs on port $PORT: $(echo $pids | tr '\n' ' ')"
  echo "$pids" | xargs kill 2>/dev/null || true

  # Wait for port to be free
  for i in $(seq 1 10); do
    if ! lsof -ti tcp:$PORT >/dev/null 2>&1; then
      echo "Port $PORT released."
      return 0
    fi
    sleep 1
  done

  # Force kill anything still holding the port
  echo "WARN: Force killing remaining processes..."
  lsof -ti tcp:$PORT 2>/dev/null | xargs kill -9 2>/dev/null || true

  # Wait again after force kill
  for i in $(seq 1 5); do
    if ! lsof -ti tcp:$PORT >/dev/null 2>&1; then
      echo "Port $PORT released after force kill."
      return 0
    fi
    sleep 1
  done

  echo "ERROR: Port $PORT still in use."
  return 1
}

wait_ready() {
  echo "Waiting for app to become ready..."
  for i in $(seq 1 $MAX_ATTEMPTS); do
    code=$(curl -s -o /dev/null -w "%{http_code}" "$URL" 2>/dev/null)
    if [ "$code" = "200" ] || [ "$code" = "302" ]; then
      echo "App ready (HTTP $code) after ~$((i * SLEEP_INTERVAL))s"
      return 0
    fi
    echo "  Attempt $i/$MAX_ATTEMPTS - HTTP $code"
    sleep $SLEEP_INTERVAL
  done
  echo "ERROR: App not ready after $((MAX_ATTEMPTS * SLEEP_INTERVAL))s"
  return 1
}

case "${1:-all}" in
  stop)  stop_app ;;
  wait)  wait_ready ;;
  all)   stop_app && wait_ready ;;
  *)     echo "Usage: $0 [stop|wait]"; exit 1 ;;
esac
