---
name: tdd-task
description: Implement a feature or fix a bug using TDD — write failing test first, then implement, refactor, verify, beautify. Use for any single code change that should be test-driven.
dependencies:
  - test
  - commit
  - restart
  - simplify
  - frontend
  - e2e-test
agents:
  - ui-review
---

# TDD Task

Implement a feature or fix a bug by writing a failing test first, then making it pass.

## Process

### 0. Plan — create a todolist

**MANDATORY** — before any other step, call `TaskCreate` once per step below so progress is visible. Mark each task `in_progress` when starting and `completed` the moment it's done — do not batch. Add extra tasks if the work uncovers sub-steps (e.g. a DB migration).

Default tasks:
1. Understand — trace code paths / find analog
2. Clarify — ask targeted questions before coding (skip if none)
3. Classify — pick test base class(es); decide if E2E Playwright is required (see Step 3 rule)
4. Red — write failing service/unit test; confirm RED
5. Green — make all failing tests pass
6. Refactor — /simplify pass
7. Verify — service tests + Playwright E2E (+ ui-review for UI changes)
8. Beautify — /frontend (UI changes only, delete task if backend-only)
9. Commit — /commit

### 1. Understand

Explore the codebase to find the relevant code paths.

- Search for existing implementations of the same concept — read the closest analog end-to-end (controller → service → template) before writing new code
- Find the relevant classes, controllers, and templates for this area
- Check if there's an existing test class for this area
- For features: determine where the new code should live following the project's package structure
- For bugs: trace the broken code path

### 2. Clarify — ask before coding

After exploration, before writing any test or code: if the task has real ambiguity, ask the user **targeted** questions via `AskUserQuestion`. Batch them into a single call (1–4 questions max, each with concrete options the user can click).

Ask only when the answer changes what you build. Good triggers:
- **Scope** — spec mentions feature X; is related feature Y also in scope?
- **Behaviour ambiguity** — two plausible behaviours for the same symptom (e.g. "reject task" — does it also affect the replacement pick order, or only exclude from future fills?)
- **Data model choice** — multiple reasonable schemas (junction table vs. soft-delete flag vs. status enum)
- **Backfill** — existing data that may or may not need migrating to the new behaviour
- **Edge cases worth locking in** — empty state, concurrent requests, deleted parent
- **Test seam** — extend existing `FooServiceTest` or create `FooServiceRejectionTest`?
- **User role** — Playwright test covers guest flow, manager flow, or both?

Do NOT ask:
- Trivial style/naming choices — decide yourself
- Things the codebase conventions already answer — read `CLAUDE.md` / `references/project.md` first
- "Should I do TDD?" — yes, that's why this skill is running
- Things you can resolve by reading one more file

If exploration answered everything, mark this task completed with a one-line note ("no ambiguity — proceeding") and move on. Don't fabricate questions to fill the step.

### 3. Classify — pick test type(s)

Choose the right test base class(es) for the change. Check `references/project.md` for the project's test base classes and when to use each.

Common categories:
- **Unit/service tests** — business logic, repository queries
- **Integration tests** — tests requiring external services (DB, storage, message queues)
- **End-to-end tests** — browser-visible UI, full user flows

**E2E coverage rule — MANDATORY when behaviour is user-observable.** If a user can trigger or see the change via the UI (any HTTP route, any rendered template, any HTMX/JS interaction), the task needs BOTH:
1. A unit/service/integration test that drives the change (fast feedback, drives implementation)
2. A Playwright E2E test that proves the user-facing path works end-to-end

Skip E2E only when the change is provably non-user-observable: background jobs with no UI surface, internal refactors with no behavioural delta, generated-code regeneration. "Only a service-layer bug" is NOT a valid skip — if the service powers a UI flow, the UI flow needs a Playwright test. Use `/e2e-test` for the Playwright test (page-object pattern, TestId constants) — or write one manually against your E2E harness if that skill isn't installed.

If E2E is required, add `4b. Red — write failing Playwright E2E test; confirm RED` to the todolist.

### 4. Red — write a failing test

**MANDATORY GATE — do NOT write any implementation code until this step is complete.**

The goal is a test that **compiles, runs, and fails with an assertion error** — not a compile error. A compile error proves the code doesn't exist yet; an assertion error proves the current behavior is wrong.

**Unit/integration tests:**
1. **Create a stub** — write the new method/class with a minimal implementation (return null, return a hardcoded wrong value, throw `TODO()`). Just enough to compile.
2. **Write assertions** — add tests that assert the correct behavior against the stub. They compile and run but FAIL with assertion errors.
3. **Run** `/test *FilterPattern` (or your build tool's test runner) and confirm RED (test must fail with an assertion error).

**Playwright/E2E tests:**
1. **Write the test** directly — it runs against the full app, no stub needed. Navigate, interact, assert on expected UI state.
2. **Run the test** — it fails because the UI/behavior doesn't exist yet. That's RED.
3. Confirm RED (test must fail).

**When Step 3 required BOTH a service test AND an E2E test:** write the service/unit test first and get it RED, then write the Playwright test and get it RED too. Both must be failing before you start Step 5.

<rules>
- If you cannot write a test, you MUST use AskUserQuestion to explain why and get explicit approval before skipping. Do not rationalize the skip yourself.
- Template/view changes often have testable service or controller behavior behind them — don't use "it's just a template change" as a reason to skip.
- If the change is user-observable, a service/unit test alone is NOT sufficient — you also need a Playwright E2E test per the rule in Step 3.
- The test name should describe the expected behavior (e.g. `Should transition to REVEAL when voting ends` not `Fix end button`)
- If the change requires a DB migration, run the migration and codegen first (check `references/project.md` for the exact commands)
</rules>

### 5. Green — make the test(s) pass

Write the minimum code to make the failing test(s) pass.

1. Compile the project (check `references/project.md` for the compile command)
2. Run `/test *FilterPattern` — confirm GREEN on the service/unit test. Fix inline and re-run if needed.
3. If Step 3 required a Playwright E2E test: run it too and confirm GREEN. For a UI-wiring change, you may need to restart the app (`/restart`, or rebuild your app manually) before the Playwright run picks up backend changes.
4. Do not proceed to Step 6 until every test you wrote in Step 4 is green.

### 6. Refactor

Run `/simplify` (or review manually) to check changed code for reuse, quality, and efficiency. Then clean up anything remaining: remove duplication, extract methods if needed, ensure naming is consistent with surrounding code.

Run `/test *FilterPattern` — confirm still green after refactoring.

### 7. Verify

- **Non-user-observable changes** (background jobs, internal refactors, generated code): service/unit test output is sufficient proof.
- **User-observable changes** (any route, template, or HTMX/JS flow a user can hit): the Playwright E2E test you wrote in Step 4 must be green — that is the proof the fix works end-to-end. A passing service test alone is NOT sufficient.
- **UI changes** (any template file created or modified): in addition to the above, spawn the `ui-review` subagent on the screenshot folder from the Playwright run. Provide the expected user flow so it knows what to check. Fix any issues it reports before proceeding. If you modified a template file, it IS a UI change — do not classify it as "backend-only".

### 8. Beautify (UI changes only)

If the change introduced new UI elements:

Use `/frontend` (or apply the project's design system manually) to refine, then re-run Playwright tests and verify with `ui-review` subagent.

### 9. Commit

**MANDATORY — commit your changes. Do not skip or defer this step.**

Use `/commit` (or commit manually). Every TDD task ends with a commit.

## Project Customization

Read `references/project.md` in this skill's directory if it exists. It provides project-specific context:
- Test base classes and when to use each
- Build, compile, and migration commands
- Package structure conventions
- Any other project-specific patterns
