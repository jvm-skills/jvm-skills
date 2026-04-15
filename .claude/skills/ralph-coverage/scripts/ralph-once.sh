#!/bin/bash
cd "$(dirname "$0")/../../../.." || exit

SKILL_DIR=".claude/skills/ralph-coverage"

claude --permission-mode acceptEdits \
  "@$SKILL_DIR/PRD.md @$SKILL_DIR/progress.txt \
  1. Read the PRD and progress file. \
  2. Run the /coverage skill to get current coverage data. \
  3. Find the highest-priority untested class and write tests for it. \
  4. Commit your changes. \
  5. Update $SKILL_DIR/progress.txt with what you did. \
  ONLY DO ONE CLASS AT A TIME."
