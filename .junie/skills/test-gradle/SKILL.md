---
name: test-gradle
description: Run tests headless and return only failing test output. Accepts optional test filter patterns like gradle (e.g. /test *RankingGameTest)
context: fork
---

# Run Tests Skill

Run tests and report results. Does NOT fix failures — fix them inline in the calling context.

## Argument handling

**CRITICAL**: Only add `--tests` flags if the user explicitly passed filter patterns. `/test` with NO arguments MUST run ALL tests — do NOT infer filters from branch name, recent changes, or context.

Examples:
- `/test` → `./scripts/run-tests.sh` (ALL tests, no filters)
- `/test *RankingGameSetupTest` → `./scripts/run-tests.sh --tests "*RankingGameSetupTest"`
- `/test *SetupTest *LobbyTest` → `./scripts/run-tests.sh --tests "*SetupTest" --tests "*LobbyTest"`

If the argument already contains `--tests`, pass it through as-is.

## Instructions

1. **Run the test script** (Bash tool, timeout 600000):
   ```bash
   ./scripts/run-tests.sh [--tests "pattern"]...
   ```

2. **Report the output as-is**:
   - If output says "All tests passed." → report success, done.
   - If output shows "## Failed Tests" → report the failures verbatim. Do NOT fix them. Do NOT launch subagents. Return the raw failure output to the caller.
