#!/bin/bash
# stop-uncommitted-check.sh — Stop hook
# Warns if there are uncommitted changes when Claude stops.
# Rule: "Commit after each phase"
set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Check for uncommitted changes (staged + unstaged + untracked in project)
CHANGES=$(cd "$PROJECT_DIR" && git status --porcelain 2>/dev/null | head -20)

if [[ -n "$CHANGES" ]]; then
  COUNT=$(echo "$CHANGES" | wc -l | tr -d ' ')
  echo "[stop-check] WARNING: $COUNT uncommitted change(s) detected. Consider committing before stopping."
fi

# Warn-only: always exit 0
exit 0
