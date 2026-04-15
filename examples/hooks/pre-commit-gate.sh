#!/bin/bash
# pre-commit-gate.sh — Claude Code PreToolUse hook (Bash matcher)
# Blocks `git commit` if staged files have lint violations or Kotlin doesn't compile.
# Kotlin lint rules live in config/lint/ and run via `./gradlew detekt` (which depends on `lint`).
# HTML template rules are grep-based (no AST parser for HTML).
# Exit 0 + allow JSON = pass, Exit 2 = hard block.
set -uo pipefail
trap 'echo "[pre-commit-gate] ERROR on line $LINENO (exit $?): $(sed -n "${LINENO}p" "$0" 2>/dev/null)" >&2' ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
ALLOW='{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'

# Extract command from stdin JSON
CMD=$(python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('tool_input', {}).get('command', ''))
" 2>/dev/null || true)

# Only gate on git commit commands (handles `git add ... && git commit ...`)
if ! echo "$CMD" | grep -qE '(^|&&\s*|;\s*)git commit'; then
  echo "$ALLOW"
  exit 0
fi

# Resolve git repo root (may differ from PROJECT_DIR in test environments)
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PROJECT_DIR")

# Collect staged files as absolute paths (excluding deleted)
STAGED=$(git -C "$GIT_ROOT" diff --cached --name-only --diff-filter=d 2>/dev/null || true)
[ -z "$STAGED" ] && { echo "$ALLOW"; exit 0; }

# Convert relative staged paths to absolute
ABS_STAGED=""
while IFS= read -r f; do
  [ -n "$f" ] && ABS_STAGED="${ABS_STAGED}${GIT_ROOT}/${f}"$'\n'
done <<< "$STAGED"

ERRORS=""

# --- HTML template lint rules on staged .html files (grep-based) ---
HTML_FILES=$(echo "$ABS_STAGED" | grep '\.html$' || true)
if [ -n "$HTML_FILES" ]; then
  HTML_LINT=""
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    file_errors=""

    inline_matches=$(grep -nE '(:|@|x-)[a-zA-Z-]+="[^"]*\[\[\$\{' "$f" 2>/dev/null || true)
    if [ -n "$inline_matches" ]; then
      file_errors="${file_errors}  [NO_INLINE_EXPR_IN_ALPINE] Use th:data-* instead of \[\[\${...}\]\]\n$(echo "$inline_matches" | head -5 | sed 's/^/    /')\n"
    fi

    ajax_matches=$(grep -nE 'htmx\.ajax\(' "$f" 2>/dev/null || true)
    if [ -n "$ajax_matches" ]; then
      file_errors="${file_errors}  [NO_HTMX_AJAX] Use <form> + hx-post instead\n$(echo "$ajax_matches" | head -5 | sed 's/^/    /')\n"
    fi

    hxvals_matches=$(grep -nE 'hx-vals' "$f" 2>/dev/null || true)
    if [ -n "$hxvals_matches" ]; then
      file_errors="${file_errors}  [NO_HX_VALS] Use hidden <input> fields instead\n$(echo "$hxvals_matches" | head -5 | sed 's/^/    /')\n"
    fi

    if [ -n "$file_errors" ]; then
      HTML_LINT="${HTML_LINT}LINT FAIL: $f\n${file_errors}\n"
    fi
  done <<< "$HTML_FILES"

  if [ -n "$HTML_LINT" ]; then
    ERRORS="${ERRORS}${HTML_LINT}"
  fi
fi

# Compile + lint + detekt if .kt files are staged (only in real project, not test repos)
# `detekt` depends on `lint` task, so config/lint/ inspections run automatically
KT_FILES=$(echo "$ABS_STAGED" | grep '\.kt$' | grep -v '/jooq/' || true)
if [ -n "$KT_FILES" ] && [ "$GIT_ROOT" = "$PROJECT_DIR" ]; then
  COMPILE_OUT=$("$PROJECT_DIR/gradlew" -p "$PROJECT_DIR" compileKotlin compileTestKotlin detekt --no-configuration-cache 2>&1) || \
    ERRORS="${ERRORS}Compilation/lint/detekt failed:\n$(echo "$COMPILE_OUT" | tail -30)\n"
fi

if [ -n "$ERRORS" ]; then
  echo -e "[pre-commit-gate] BLOCKED — fix before committing:\n$ERRORS" >&2
  exit 2
fi

echo "$ALLOW"
exit 0
