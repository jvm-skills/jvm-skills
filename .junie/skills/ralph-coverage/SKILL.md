---
name: ralph-coverage
description: Run Ralph in coverage mode — iteratively write tests for untested classes until coverage targets are met. Use when user wants to improve test coverage autonomously.
---

# Ralph Coverage

Autonomously improve test coverage by iterating through untested classes, writing tests, and committing. Each iteration picks one class, writes meaningful tests for it, runs them, and commits.

## Prerequisites

- A coverage skill that generates a prioritized improvement plan (e.g. `coverage-kover-gradle`)
- `claude` CLI on PATH
- Clean working tree (the loop commits after every iteration)

## Scripts (`scripts/` subfolder)

| Script | Purpose |
|--------|---------|
| `ralph-once.sh` | Single iteration, foreground. Use to try the loop before committing to a long run. |
| `afk-ralph.sh <iterations>` | Headless loop with retry and error handling. Stops early on `<promise>COMPLETE</promise>`. Depends on `ralph-lib.sh` from a `ralph-plan` skill if you use one — otherwise inline the helpers. |

Both scripts `cd` to the project root and read `PRD.md` + `progress.txt` inside this skill's directory.

## Files

- `PRD.md` — coverage priorities, target thresholds, rules, and which test base classes / skip patterns to follow. Customize per project.
- `progress.txt` — append-only log of completed coverage iterations. Created on first run.

## Process (each iteration)

1. Run the coverage skill to generate coverage report and improvement plan
2. Read the generated improvement document
3. Read `progress.txt` to see which classes already have tests written
4. Pick the highest-priority untested class (lowest coverage, not already in progress.txt)
5. Read the source class and any existing tests for it
6. Write meaningful tests — not just line coverage, but real behavior/edge case tests
7. Run the test filter for the new test class to verify tests pass
8. Compile to check for syntax errors
9. Commit: `git add -A && git commit -m "test: add tests for ClassName"`
10. Update `progress.txt` with class name, previous coverage %, and what was tested

## Rules

- ONLY ONE CLASS PER ITERATION
- Follow the project's existing test patterns (see `PRD.md`)
- Use descriptive test names (e.g. `` `should do something specific` ``)
- Skip generated code and framework boilerplate (see `PRD.md`)
- If all priority classes are covered above the target threshold, output `<promise>COMPLETE</promise>`

## Project Customization

Customize `PRD.md` in this skill's directory:
- Test base classes and when to use each (e.g. `DataBaseTest`, `S3Test`)
- Skip patterns (generated code, view-context data classes, etc.)
- Coverage target threshold (e.g. 80%)
- Commit message style
- Project-specific exclusions
