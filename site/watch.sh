#!/usr/bin/env bash
set -euo pipefail

# ══════════════════════════════════════════════
# watch.sh — Live-reload dev server for jvmskills.com
#
# Watches site/template.html, skills/**/*.yaml
# Rebuilds on change, serves on http://localhost:8080
# ══════════════════════════════════════════════

SITE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SITE_DIR")"
PORT="${1:-8080}"
DIST_DIR="$ROOT_DIR/dist"

# Check for fswatch or fall back to polling
if command -v fswatch &>/dev/null; then
  WATCHER="fswatch"
elif command -v inotifywait &>/dev/null; then
  WATCHER="inotifywait"
else
  WATCHER="poll"
fi

build() {
  if command -v kotlin &>/dev/null; then
    kotlin "$SITE_DIR/build.main.kts" 2>&1
  else
    echo "ERROR: kotlin is required. Install via: sdk install kotlin" >&2
    return 1
  fi
}

# Initial build
echo "Building..."
build

# Start HTTP server
echo "Serving on http://localhost:$PORT"
python3 -m http.server "$PORT" --directory "$DIST_DIR" &>/dev/null &
HTTP_PID=$!
trap "kill $HTTP_PID 2>/dev/null" EXIT

echo "Watching for changes... (Ctrl+C to stop)"

if [[ "$WATCHER" == "fswatch" ]]; then
  fswatch -o \
    "$SITE_DIR/template.html" \
    "$ROOT_DIR/skills/" \
  | while read -r; do
    echo ""
    echo "Change detected, rebuilding..."
    build
  done
elif [[ "$WATCHER" == "inotifywait" ]]; then
  while true; do
    inotifywait -q -r -e modify,create,delete \
      "$SITE_DIR/template.html" \
      "$ROOT_DIR/skills/" 2>/dev/null
    echo ""
    echo "Change detected, rebuilding..."
    build
  done
else
  # Polling fallback
  get_hash() {
    find "$SITE_DIR/template.html" "$ROOT_DIR/skills" \
      \( -name '*.yaml' -o -name '*.html' \) 2>/dev/null | \
      xargs stat -f '%m' 2>/dev/null || \
      xargs stat -c '%Y' 2>/dev/null || echo ""
  }
  LAST_HASH="$(get_hash)"
  while true; do
    sleep 1
    CURRENT_HASH="$(get_hash)"
    if [[ "$CURRENT_HASH" != "$LAST_HASH" ]]; then
      echo ""
      echo "Change detected, rebuilding..."
      build
      LAST_HASH="$CURRENT_HASH"
    fi
  done
fi
