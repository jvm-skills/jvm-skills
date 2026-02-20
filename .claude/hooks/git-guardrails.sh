#!/bin/bash
# git-guardrails.sh — PreToolUse hook that blocks destructive git commands
# Blocks: force push, reset --hard, clean -f, branch -D, checkout ., restore .
# Allows: regular git push (needed for branch workflow)
set -euo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || true)

[ -z "$COMMAND" ] && exit 0

DANGEROUS_PATTERNS=(
  "push --force"
  "push -f "
  "git reset --hard"
  "git clean -fd"
  "git clean -f"
  "git branch -D"
  "git checkout \."
  "git restore \."
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qE "$pattern"; then
    echo "BLOCKED: '$COMMAND' matches dangerous pattern '$pattern'. The user has prevented you from doing this." >&2
    exit 2
  fi
done

exit 0
