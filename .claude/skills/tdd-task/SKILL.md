---
name: tdd-task
description: Implement a feature or fix a bug using TDD — write failing test first, then implement, refactor, verify, beautify. Use for any single code change that should be test-driven.
dependencies:
  - test
  - commit
  - restart
  - simplify
  - frontend
agents:
  - ui-review
---

# TDD Task

Implement a feature or fix a bug by writing a failing test first, then making it pass.

## Process

### 1. Understand

Explore the codebase to find the relevant code paths.

- Search for existing implementations of the same concept — read the closest analog end-to-end (controller → service → template) before writing new code
- Find the relevant classes, controllers, and templates for this area
- Check if there's an existing test class for this area
- For features: determine where the new code should live following the project's package structure
- For bugs: trace the broken code path

### 2. Classify — pick test type

Choose the right test base class or test style for the change. Check `references/project.md` for the project's test base classes and when to use each.

Common categories:
- **Unit/service tests** — business logic, repository queries
- **Integration tests** — tests requiring external services (DB, storage, message queues)
- **End-to-end tests** — browser-visible UI, full user flows

### 3. Red — write a failing test

**MANDATORY GATE — do NOT write any implementation code until this step is complete.**

The goal is a test that **compiles, runs, and fails with an assertion error** — not a compile error. A compile error proves the code doesn't exist yet; an assertion error proves the current behavior is wrong.

**Unit/integration tests:**
1. **Create a stub** — write the new method/class with a minimal implementation (return null, return a hardcoded wrong value, throw `TODO()`). Just enough to compile.
2. **Write assertions** — add tests that assert the correct behavior against the stub. They compile and run but FAIL with assertion errors.
3. **Run** `/test *FilterPattern` and confirm RED (test must fail with an assertion error).

**Playwright/E2E tests:**
1. **Write the test** directly — it runs against the full app, no stub needed. Navigate, interact, assert on expected UI state.
2. **Run the test** — it fails because the UI/behavior doesn't exist yet. That's RED.
3. Confirm RED (test must fail).

<rules>
- If you cannot write a test, you MUST use AskUserQuestion to explain why and get explicit approval before skipping. Do not rationalize the skip yourself.
- Template/view changes often have testable service or controller behavior behind them — don't use "it's just a template change" as a reason to skip.
- The test name should describe the expected behavior (e.g. `Should transition to REVEAL when voting ends` not `Fix end button`)
- If the change requires a DB migration, run the migration and codegen first (check `references/project.md` for the exact commands)
</rules>

### 4. Green — make the test pass

Write the minimum code to make the test pass.

1. Compile the project (check `references/project.md` for the compile command)
2. Run `/test *FilterPattern` — confirm GREEN. If tests fail, fix inline (you have full context of what you just wrote) and re-run.

### 5. Refactor

Run `/simplify` (or review manually) to check changed code for reuse, quality, and efficiency. Then clean up anything remaining: remove duplication, extract methods if needed, ensure naming is consistent with surrounding code.

Run `/test *FilterPattern` — confirm still green after refactoring.

### 6. Verify

- **Backend-only changes** (no template/view files modified): test output is sufficient proof.
- **UI changes** (any template created or modified): verify that the UX works and the UI looks good. Spawn the `ui-review` subagent on the screenshot folder from the Playwright tests you ran. Provide the expected user flow so it knows what to check. Fix any issues it reports before proceeding. If you modified a template file, it IS a UI change — do not classify it as "backend-only".

### 7. Beautify (UI changes only)

If the change introduced new UI elements:

Use `/frontend` (or apply the project's design system manually) to refine, then re-run Playwright tests and verify with `ui-review` subagent.

### 8. Commit

**MANDATORY — commit your changes. Do not skip or defer this step.**

Use `/commit` (or commit manually). Every TDD task ends with a commit.

## Project Customization

Read `references/project.md` in this skill's directory if it exists. It provides project-specific context:
- Test base classes and when to use each
- Build, compile, and migration commands
- Package structure conventions
- Any other project-specific patterns
