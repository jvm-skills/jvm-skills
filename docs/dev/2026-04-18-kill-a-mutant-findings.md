# Findings: killing one mutant end-to-end (capability #5 validation)

**Session date**: 2026-04-18
**Outcome**: SUCCESS — one mutant moved SURVIVED → KILLED. Committed as PhotoQuest `695c3d2c8`.

## Target picked and why

`ConditionalsBoundary` at `MediaSubmission.kt:34` in `MediaSubmission.getPolaroidObjectName()`.

Mutation: flipped `if (lastSlash >= 0)` to `if (lastSlash > 0)`.

Why: matched priority #1 from SKILL.md §5 (ConditionalsBoundary on real branching logic). Behavioral divergence at the boundary (`lastSlash == 0`, i.e. object name starting with `/`) is trivially provable without test infra changes. The covering test file (`MediaSubmissionTest`) already existed with 4 tests — a sibling case fit naturally.

## Package pivot

The handoff recommended `core/pricing` — **that package does not exist in PhotoQuest**. Only `core/payment` (mostly Stripe boilerplate) is pricing-adjacent.

Pivoted twice:

1. First tried `core.task.*` — `WeddingTask` has regex + `when` + null-elvis logic AND a 15-test suite. But pitest showed **0 SURVIVED / 16 KILLED / 40 NO_COVERAGE**. The existing tests are perfect; no survivors to kill. All 40 uncovered mutations were in untested siblings (`CustomTask`, `TaskRepository`).
2. Then `core.submission.MediaSubmission*` — 96 mutations, 13 survivors, 10 triaged LIKELY_KILLABLE. Good target.

**Lesson for SKILL.md v0.5**: add a step between "pick package" and "run pitest" that grep-checks for existing tests covering the branching-heavy classes. A package with branching logic AND existing but incomplete tests is the goldilocks zone. Packages with _no_ tests yield NO_COVERAGE (wasted pitest time), packages with _perfect_ tests yield 0 survivors (nothing to do).

## `/tdd-task` behavior

**First-try kill: yes.** One iteration. Added a single sibling test case, ran `MediaSubmissionTest` (green), reran scoped pitest (target mutation KILLED, no regressions).

The prompt template in SKILL.md §5 worked well. My one addition that helped a lot: spelling out the **expected outputs under both original and mutated code** ("yielding `"" + "/polaroid/" + "photo.jpg"` … under the mutation returns `"polaroid//photo.jpg"`"). That removes ambiguity about which behavior to assert on.

The tdd-task skill's classic "write failing test first" RED gate doesn't apply cleanly to mutation-testing kills — the production code is already correct, so the test goes write→green directly. RED proof comes from the pitest re-run showing the mutant transitioned SURVIVED→KILLED. Worth documenting this in SKILL.md v0.5 as a tdd-task mode note.

## Is the test behavioral or tautological?

Behavioral. The assertion `getPolaroidObjectName() == "/polaroid/photo.jpg"` tests the observable result of the method on a specific input; it doesn't reference the `>=` operator, doesn't check internal state, doesn't spy on `lastIndexOf`. A human code reviewer would read it as "leading-slash edge case" without suspecting it was generated to kill a mutant. Would approve in review.

## Surprises / gaps

1. **`coreageThreshold` blocks report generation but doesn't prevent XML write.** Pitest exits non-zero when line coverage < 60%, but `mutations.xml` and `triage.md` are already written. Triage + kill workflow still works. SKILL.md should call this out ("build failure is expected when scoping narrowly — the XML is still valid").

2. **Attribute quoting in `mutations.xml`.** pitest 1.19.0 writes `status='SURVIVED'` (single quotes). A naive `grep 'status="SURVIVED"'` finds 0 results. `triage.py` parses XML so it's fine, but any ad-hoc grep in docs / debugging should use single quotes or regex.

3. **`targetClasses` glob pitfall.** `core.submission.MediaSubmission*` matches both `MediaSubmission` and `MediaSubmissionService`. Dropping the `*` scopes to the single class for regression checks. Worth documenting the glob semantics in SKILL.md §6 (Verify).

4. **Incremental history at cross-package pivots.** Changing `targetClasses` across unrelated packages and rerunning pitest was fast (~5s) on subsequent runs — the per-class history cache works as advertised. First run on a new package was ~20s.

5. **`triage.json` schema doesn't expose covering tests.** Had to re-parse `mutations.xml` to find out which existing tests covered the mutation. SKILL.md §5 template asks for "covering tests (from triage.md)" but triage.md only names the file, not the individual test methods. Either extend triage.py to extract `coveringTests` per survivor, or update the template to say "parse from mutations.xml directly".

## Rerun verification

Scoped to `de.tschuehly.photoquest.core.submission.MediaSubmission` (single class, MediaSubmissionTest only):

```
KILLED=4 SURVIVED=0 NO_COVERAGE=32 OTHER=0
Target mutation (MediaSubmission.kt:34 ConditionalsBoundary) status: KILLED
```

No previously-KILLED mutant regressed. (The 32 NO_COVERAGE are pre-existing — MediaSubmission has `getSanitizedFileName`, `getPolaroidFileName`, `isPotentialPolaroid`, `convert` with no unit coverage. Orthogonal to this session.)

## v0.5 recommendations

1. Add "check for existing tests before picking target" step.
2. Document the "production correct, test goes write→green, RED via pitest rerun" mode for `/tdd-task` delegation.
3. Extend `triage.py` to emit `coveringTests` per survivor in triage.md / triage.json.
4. Add a `Verify` troubleshooting note: "coverage-threshold build failure is expected and does not block mutation verification — parse mutations.xml."
5. Call out attribute-quote convention in mutations.xml (single quotes in pitest 1.19).
