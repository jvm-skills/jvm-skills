# Test Coverage Ralph Loop

## Goal
Increase test coverage by writing tests for the least-covered classes, one at a time, until the target threshold is reached across priority packages.

## Process (each iteration)

1. Run the coverage skill (e.g. `/coverage`) to generate coverage report and improvement plan
2. Read the generated improvement document (e.g. `docs/dev/YYYY-MM-DD_test-improvements.md`)
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
- Follow existing test patterns — pick the appropriate base class per scenario (see project conventions)
- Use descriptive test names: `` fun `should do something specific`() ``
- Skip generated code (e.g. jOOQ generated sources, ORM stubs) and view-context data classes
- Skip Playwright/E2E tests — focus on unit and integration tests
- If all priority classes are covered above the target threshold (e.g. 80%), output `<promise>COMPLETE</promise>`

## Coverage target
Default: 80% line coverage across priority packages. Adjust per project.
