---
name: test-gradle
description: Run tests headless and return only failing test output. Accepts optional test filter patterns like gradle (e.g. /test *RankingGameTest)
context: fork
---

# Run Tests Skill

Run tests via script, fix any failures, repeat until green.

## Argument handling

The user may pass test filter patterns after `/test`. Pass them directly to the script as `--tests` arguments.

Examples:
- `/test` → `./scripts/run-tests.sh` (all tests)
- `/test *RankingGameSetupTest` → `./scripts/run-tests.sh --tests "*RankingGameSetupTest"`
- `/test *SetupTest *LobbyTest` → `./scripts/run-tests.sh --tests "*SetupTest" --tests "*LobbyTest"`

If the argument already contains `--tests`, pass it through as-is.

## Instructions

1. **Open a Kitty tab for live output**, then run the test script:
   ```bash
   kitty @ launch --type=tab --title "Test Output" tail -f build/gradle-test-out.txt
   ```
   Then run the tests (Bash tool, timeout 600000):
   ```bash
   ./scripts/run-tests.sh [--tests "pattern"]...
   ```

2. **When complete, check the output**:
   - If output says "All tests passed." → report success, done.
   - If output shows "## Failed Tests" → proceed to step 3.

3. **Group failures by unique exception**: Parse the failure output and group test failures that share the same root exception type/message. Each unique exception becomes one analysis+fix unit.

4. **Launch parallel subagents**: For each unique exception group, launch an Agent (subagent_type: "general-purpose") **in parallel** (single message, multiple tool calls). Each subagent prompt MUST include:
   - The full failure output for that exception group (all affected test classes, methods, messages, stack frames)
   - Instruction to:
     1. Read the failing test code to understand what it expects
     2. Read the production code at the stack trace locations
     3. Determine the root cause
     4. Fix the code (`./gradlew compileKotlin compileTestKotlin` after any .kt changes)
     5. Run `./scripts/run-tests.sh --tests "*FailingClassName"` for each affected test class to verify the fix
   - **Never dismiss a failure as "pre-existing" or "not my problem"** — always attempt to fix it
   - Instruction to return a structured report:
     - **Exception**: the exception type and message
     - **Affected tests**: list of `ClassName > methodName`
     - **Code location**: file path + line number where the error originates
     - **Root cause**: concise explanation of why it fails
     - **Fix applied**: what was changed

5. **Compile report and verify**: After all subagents complete, present a consolidated failure report:

   ```
   ## Test Failure Report

   ### 1. [ExceptionType]: [short message]
   **Affected tests**: ClassName > method1, ClassName > method2
   **Code location**: `path/to/File.kt:42`
   **Root cause**: [explanation]
   **Fix**: [what was changed]

   ### 2. ...

   Summary: X unique failure(s) across Y test(s)
   ```

   Then re-run the original full test command from step 1 to confirm all green. If new failures appear, repeat from step 3.

6. **Done when all tests pass.** Report final status with the consolidated report.
