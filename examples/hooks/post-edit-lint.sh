#!/bin/bash
# post-edit-lint.sh — Claude Code PostToolUse hook
# Lints .html files after Edit/Write tool use.
# .kt rules are handled by `./gradlew lint` (config/lint/ inspections).
# Reads tool input JSON from stdin, extracts file_path, runs matching lint rules.
set -uo pipefail
trap 'echo "[post-edit-lint] ERROR on line $LINENO (exit $?): $(sed -n "${LINENO}p" "$0" 2>/dev/null)" >&2' ERR

# Extract file_path from stdin JSON
FILE=$(python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('tool_input', {}).get('file_path', ''))
" 2>/dev/null || true)

[[ -z "$FILE" ]] && exit 0
[[ ! -f "$FILE" ]] && exit 0

# --- HTML template lint rules ---
if [[ "$FILE" == *.html ]]; then
  errors=0

  # No [[${...}]] inline expressions in Alpine attributes
  inline_matches=$(grep -nE '(:|@|x-)[a-zA-Z-]+="[^"]*\[\[\$\{' "$FILE" 2>/dev/null || true)
  if [ -n "$inline_matches" ]; then
    echo "  [NO_INLINE_EXPR_IN_ALPINE] Use th:data-* attributes instead of \[\[\${...}\]\] in Alpine attrs"
    echo "$inline_matches" | head -5 | sed 's/^/    /'
    errors=1
  fi

  # No htmx.ajax() — use <form> + hx-post
  ajax_matches=$(grep -nE 'htmx\.ajax\(' "$FILE" 2>/dev/null || true)
  if [ -n "$ajax_matches" ]; then
    echo "  [NO_HTMX_AJAX] Use <form> + hx-post instead of htmx.ajax()"
    echo "$ajax_matches" | head -5 | sed 's/^/    /'
    errors=1
  fi

  # No hx-vals — use hidden <input> fields
  hxvals_matches=$(grep -nE 'hx-vals' "$FILE" 2>/dev/null || true)
  if [ -n "$hxvals_matches" ]; then
    echo "  [NO_HX_VALS] Use hidden <input> fields instead of hx-vals"
    echo "$hxvals_matches" | head -5 | sed 's/^/    /'
    errors=1
  fi

  if [ "$errors" -ne 0 ]; then
    echo "LINT FAIL: $FILE"
  fi
fi

# --- Kotlin compile+lint reminder ---
if [[ "$FILE" == *.kt ]]; then
  echo "REMINDER: Run ./gradlew compileKotlin compileTestKotlin detekt after .kt changes"
fi

# Feedback only — never block
exit 0
