#!/bin/bash
# Headless coverage-improvement loop. Runs N iterations, stopping early on
# <promise>COMPLETE</promise>. Depends on a `run_claude` helper and a
# `ralph_duration` helper — install a `ralph-plan` skill alongside this one
# that ships `scripts/ralph-lib.sh`, or inline the helpers below.
cd "$(dirname "$0")/../../../.." || exit

# Inline a minimal ralph-lib if you don't have the ralph-plan skill:
if [ -f ".claude/skills/ralph-plan/scripts/ralph-lib.sh" ]; then
  source ".claude/skills/ralph-plan/scripts/ralph-lib.sh"
else
  run_claude() {
    local progress="$1"; shift
    RALPH_STDOUT=$(claude "$@" 2>&1 | tee -a "$progress")
  }
  ralph_duration() {
    local start="$1"
    local elapsed=$(( $(date +%s) - start ))
    printf '%dh%02dm' $((elapsed/3600)) $(( (elapsed%3600)/60 ))
  }
fi

# Kill entire process group on Ctrl+C (claude -p in pipelines ignores SIGINT)
trap 'echo "[ralph] Interrupted"; kill 0; exit 130' INT TERM

if [ -z "$1" ]; then
  echo "Usage: $0 <iterations>"
  exit 1
fi

SKILL_DIR=".claude/skills/ralph-coverage"
PROGRESS="$SKILL_DIR/progress.txt"
START_TIME=$(date +%s)
START_DISPLAY=$(date '+%Y-%m-%d %H:%M:%S')

echo "" >> "$PROGRESS"
echo "=== Coverage run started: $START_DISPLAY ===" >> "$PROGRESS"

for ((i=1; i<=$1; i++)); do
  echo "=== Ralph iteration $i of $1 ==="

  if ! run_claude "$PROGRESS" -p --permission-mode acceptEdits \
    "@$SKILL_DIR/PRD.md @$SKILL_DIR/progress.txt \
    1. Read the PRD and progress file. \
    2. Run the /coverage skill to get current coverage data. \
    3. Find the highest-priority untested class and write tests for it. \
    4. Commit your changes. \
    5. Update $SKILL_DIR/progress.txt with what you did. \
    ONLY DO ONE CLASS AT A TIME. \
    If all priority classes are above 80% coverage, output <promise>COMPLETE</promise>."; then
    echo "[ralph] Iteration $i FAILED, continuing" | tee -a "$PROGRESS"
    continue
  fi

  result="$RALPH_STDOUT"
  echo "$result"

  if [[ "$result" == *"<promise>COMPLETE</promise>"* ]]; then
    echo "=== Coverage run completed: $(date '+%Y-%m-%d %H:%M:%S') ($(ralph_duration $START_TIME), $i iterations) ===" >> "$PROGRESS"
    echo "Coverage target reached after $i iterations."
    exit 0
  fi
done

echo "=== Coverage run finished: $(date '+%Y-%m-%d %H:%M:%S') ($(ralph_duration $START_TIME), $1 iterations, target NOT reached) ===" >> "$PROGRESS"
echo "Completed $1 iterations."
