---
name: fix-spring-tdd
description: Fix a bug or missing feature using TDD — write failing test first, then fix, refactor, verify, beautify. Use when a bug is discovered or a feature doesn't work as expected.
---

# Fix with TDD

Fix a bug or missing feature by writing a failing test first, then making it pass.

## Process

### 1. Understand

Describe the bug or missing behavior. Explore the codebase to find the relevant code paths.

- If UI-related: screenshot the current broken state (if browser automation is available)
- Find the relevant service, controller, and template/view files
- Check if there's an existing test class for this area

### 2. Classify — pick test approach

| Scenario                                   | Test approach          |
|--------------------------------------------|------------------------|
| Service/repository logic, DB queries       | Integration tests with real DB |
| File uploads, external storage             | Integration tests with mocks/stubs |
| Browser-visible UI, full user flows        | End-to-end browser tests |

### 3. Red — write a failing test

⛔ **MANDATORY GATE — do NOT write any fix code until this step is complete.**

Write a test that reproduces the bug or asserts the missing behavior. Add to an existing test class if one covers this area, otherwise create a new one.

Run `/test *FilterPattern` and **paste the failure output** to confirm the test fails for the right reason.

<rules>
- If you cannot write a test, you MUST use AskUserQuestion to explain why and get explicit approval before skipping. Do not rationalize the skip yourself.
- "It's just a template change" is NOT a valid reason to skip — template bugs often have testable service/controller behavior behind them.
- The test name should describe the expected behavior, not the bug (e.g. `Should transition to REVEAL when voting ends` not `Fix end button`)
- If the fix requires a DB migration, do that first: migration → run codegen → then write test
</rules>

### 4. Green — make the test pass

Write the minimum code to make the test pass.

1. Compile the code
2. Run the test — **paste the green output** to confirm pass

### 5. Refactor

Run `/simplify` to review changed code for reuse, quality, and efficiency. Then clean up anything remaining: remove duplication, extract methods if needed, ensure naming is consistent with surrounding code.

Run the test again — confirm still green after refactoring.

### 6. Verify

- **UI fixes**: `/restart-spring-boot` → verify the fix (screenshot or browser automation) → compare with the broken state from step 1
- **Backend fixes**: test output is sufficient proof

### 7. Beautify (UI fixes only)

If the fix introduced new UI elements:

design skill → refine → verify the UI

### 8. Commit

`/commit`