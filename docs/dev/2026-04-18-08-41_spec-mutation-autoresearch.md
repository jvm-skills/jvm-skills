# Spec: `mutation-autoresearch` skill

**Skill path (generalized):** `jvm-skills/.claude/skills/mutation-autoresearch/SKILL.md`
**Project overlay (battle-test):** `PhotoQuest/.claude/skills/mutation-autoresearch/references/project.md`
**Evals:** `PhotoQuest/.claude/skills/mutation-autoresearch/evals/evals.json` → `jvm-skills/evals/mutation-autoresearch/benchmark.json`
**Registry listing:** `jvm-skills/skills/testing/mutation-autoresearch.yaml`
**Category:** `testing`
**Trust:** `official`
**Depends on:** `mutation-testing` ≥ v0.3 (mandatory — **triage output is a required input**), `tdd-task`, `commit`, `test-gradle`. Integrates with `/loop` as a convenience wrapper but does not require it.

## 1. Purpose

Wrap the `mutation-testing` skill in a **Ralph-style autoresearch ratchet** (Karpathy/Shopify pattern): an unattended, shell-driven loop that iterates **one test at a time**, strengthens or adds assertions until the test kills its covered-but-surviving mutants, and **commits only if the class's mutation score improved and the full existing test suite is still green** — otherwise `git reset --hard HEAD`.

The loop is designed for overnight runs. It trades exhaustiveness for safety and auditability: every successful iteration is a signed commit with a single test's changes; every rejected iteration leaves no trace.

## 2. Why Ralph (not `/loop`)

This skill follows the same pattern as `ralph-coverage`: a shell script spawns a **fresh `claude` CLI invocation per iteration**, reads state from a persistent progress file, and stops when the agent emits `<promise>COMPLETE</promise>` or the iteration budget is spent.

| Dimension | Ralph (shell-driven) | `/loop` (in-session, self-paced) |
|---|---|---|
| Context per iteration | Fresh — no drift across iterations | Persistent — prone to drift |
| Prompt cache | Cold per iteration | Warm within 5-min windows |
| Crash resilience | Shell restarts, agent resumes from `progress.txt` | Dies with the session |
| Proven here | `ralph-coverage` uses it | Unproven for overnight workloads |
| Composability | Shell-level | Slash-command level |

Ralph wins for overnight unattended runs because fresh context beats warm cache when iterations are expensive and independent, and the shell script is the only thing that has to stay alive. `/loop` stays as a convenience wrapper for interactive, in-session single-iteration kicks.

## 3. Why test-by-test (not mutant-by-mutant)

Pitest's `mutations.xml` already groups survivors by their covering test via `killingTest` / `coveringTests`. That makes the **test** a more natural iteration unit than the **mutant**:

- **Matches real code-review shape.** "Here's a test; here are N behaviors it should have caught but didn't" is how a senior engineer reviews a weak test. The agent's job maps cleanly onto this.
- **Better throughput.** One strengthened test often kills several mutants in one commit; ratchet still holds (strict `killed_count` improvement).
- **Cleaner commits.** One commit per test, not per mutant. `git log` reads as "strengthened this test" not "N cryptic per-mutant entries".
- **Natural dedup.** A mutant covered by 3 tests costs 1 iteration, not 3.

Branches of the loop:

1. **Strengthen branch (primary).** Pick one test that has covering-but-surviving mutants. Add/strengthen assertions until those mutants die.
2. **Add-new-test branch (fallback).** `NO_COVERAGE` mutants have no covering test. Pick one such mutant, write a new test that exercises the line, and kill it add-only style.

Both branches share the same ratchet (§8.3) and the same guards (§9).

## 4. Scope

**In scope:**
- Ralph loop scaffolding (shell scripts, PRD.md, progress.txt, progress.json).
- Test-by-test strengthen branch and NO_COVERAGE add-new-test branch.
- Two edit modes layered on the strengthen branch: `add-sibling` (default, additive-only) and `append-assertions` (opt-in, append-only to chosen test).
- Metric-gaming guards: tautology detection, assertion-weakening detection, full-suite-green requirement.
- Progress persistence so an interrupted session can resume.

**Out of scope:**
- Production-code changes. Loop only writes tests.
- Refactoring existing tests beyond appending assertions in `append-assertions` mode.
- Dependency upgrades, build-config changes.
- Whole-codebase pitest runs inside the loop (scope-picker rotates class-by-class).

## 5. Roles

| Role | Interacts via |
|---|---|
| **Developer** | Starts the loop via shell script or `/mutation-autoresearch`, reviews the commit log + progress files the next morning. |
| **Claude CLI (Ralph iteration)** | Fresh invocation per iteration; reads `PRD.md` + `progress.txt`, runs one iteration, commits or reverts, updates progress. |
| **Skill author / maintainer** | Tunes guards, runs evals comparing strengthen modes. |
| **CI system** | Not directly involved; loop commits flow through normal CI. |

## 6. Entry points

1. **Shell script, foreground (trial run).** `.claude/skills/mutation-autoresearch/scripts/mutation-ar-once.sh` runs one iteration with visible output.
2. **Shell script, headless (overnight).** `.claude/skills/mutation-autoresearch/scripts/afk-mutation-ar.sh <iterations>` runs N iterations with retry-on-error and stops early on `<promise>COMPLETE</promise>`.
3. **Slash command.** `/mutation-autoresearch` invokes `mutation-ar-once.sh` or documents both scripts.
4. **Composition with `/loop`.** `/loop 90s /mutation-autoresearch` delegates pacing to `/loop` if the developer wants interactive pacing rather than a fire-and-forget script.
5. **Scheduled runs.** `/schedule` can fire `afk-mutation-ar.sh N` on a cron.

First-run preconditions — the shell script aborts unless all are true:
- `mutation-testing` skill (≥ v0.3) is installed and a baseline pitest report exists.
- **Triage output exists and is current** (`build/reports/pitest/triage.md` newer than `mutations.xml`). If missing or stale, the shell script invokes `/mutation-testing` triage and exits; next run starts the loop.
- Working tree is clean.
- Current branch matches `progress.json` (if resuming).
- `claude` CLI is on `PATH`.

## 7. User journey

### 7.1 Happy path — overnight run

1. Before EOD: `./.claude/skills/mutation-autoresearch/scripts/afk-mutation-ar.sh 40`.
2. Shell script loops; each iteration spawns fresh `claude --permission-mode acceptEdits` with a prompt that `@`-includes `PRD.md` + `progress.txt` + `progress.json`.
3. Ralph iteration (inside `claude`):
   1. Read `PRD.md`, `progress.txt`, `progress.json`.
   2. **Scope picker** (§8.1) selects one test with surviving covered mutants, OR (fallback) one `NO_COVERAGE` mutant.
   3. Read source class, read covering test file.
   4. **Strengthen branch**: append assertions (opt-in) or add a sibling `@Test` in the same class (default). **Add-new-test branch**: create a new test for the uncovered line.
   5. Run `/test-gradle` filtered to the affected test class — verify green locally.
   6. Run the **full** existing suite (`./gradlew test`). Red → `git reset --hard HEAD`; append reason to `progress.txt`; emit `<iteration>rejected</iteration>`.
   7. Run pitest scoped to the one class (`mutation-testing` provides the capability).
   8. **Ratchet** (§8.3): accept iff class killed-count strictly improved AND the targeted mutants moved SURVIVED → KILLED AND no previously-killed mutant regressed AND all guards (§9) pass. Else `git reset --hard HEAD`.
   9. On accept: `/commit` with message `test(mutation): strengthen <TestClass> — killed <mutator> x N at <file>:<line>,...`. Append to `progress.txt`, update `progress.json`.
   10. Emit `<promise>COMPLETE</promise>` if the queue is empty globally; otherwise exit cleanly.
4. Shell loop continues until iteration budget spent or `<promise>COMPLETE</promise>` seen.
5. Morning: developer reviews `git log` (one commit per successful iteration) and `progress.txt` (append-only log readable top-to-bottom).

### 7.2 Happy path — resume after interruption

1. Laptop slept mid-loop at iteration 17 of 40.
2. Developer reruns `afk-mutation-ar.sh 23` (remaining budget).
3. Each iteration reads `progress.json`, verifies `git rev-parse HEAD` matches `last_committed_rev`, branch matches, working tree clean.
4. If state drifted: iteration aborts early with a message in `progress.txt`; developer must reconcile or force-restart.
5. Otherwise resumes from the next un-queued test.

### 7.3 Happy path — strengthen with append-assertions mode

1. Developer sets `MODE=append-assertions` in the shell invocation.
2. Ralph iteration prompt instructs: "Append assertions to the existing covering test. Do not rename, do not delete assertions, do not touch fixtures, do not modify tests authored in the last 14 days."
3. **Post-edit diff guard** (§9.7) runs before commit. Any trip → revert.

### 7.4 Edge cases

| Situation | Behavior |
|---|---|
| Dirty working tree at start | Abort. Ralph never mixes user work with loop commits. |
| `mutation-testing` not installed | Abort with install instruction. |
| No baseline pitest report | Shell script invokes `mutation-testing` once to bootstrap + generate baseline, then exits. Next script run begins the loop. |
| Strengthen-branch queue empty | Advance to add-new-test branch (NO_COVERAGE mutants). |
| Both queues empty for current class | Advance to next class in the package. |
| Both queues globally empty | Emit `<promise>COMPLETE</promise>`; shell loop exits. |
| Pitest scoped rerun fails (compile error / flake) | Retry once; on second failure, revert iteration with reason. |
| Pitest scoped rerun exits non-zero because of coverage/mutation/test-strength thresholds, but `mutations.xml` was written and parses | Proceed with ratchet. Thresholds are calibrated for module-wide runs; narrow single-class reruns often trip them. See §8.3. |
| Both queues empty across the entire initial scope at session start | Abort with "no work to do — expand scope or relax archetypes". Do not iterate through empty packages. See §8.1 pre-loop viability check. |
| Flaky test fails green suite | Retry suite once; on second failure, revert. Flakes tracked in `progress.json`; >3 flakes → quarantine test for session. |
| Guard trips (tautology / weakening) | Revert iteration. Do not retry same target this session. |
| `git reset --hard HEAD` would discard user work | Can't happen — clean-start precondition. Script still double-checks `git status` before every reset. |
| Budget exhausted mid-iteration | Finish current iteration cleanly (commit-or-revert), then exit. |
| `/tdd-task` not installed | Use inline TDD checklist in SKILL.md. |
| `/loop` not installed | N/A — Ralph is primary, `/loop` is optional. |
| Suspected equivalent mutant | After 3 cross-session failed attempts, mark `SUSPECTED_EQUIVALENT` in `progress.json` and skip in future iterations; summarized in generated `SUSPECTED_EQUIVALENT.md`. |
| Multiple mutants killed by one strengthened test | Count all as killed; single commit. |
| Multi-module project | Loop operates per-class within a single module; `pitestReportAggregate` runs at session start/end only. |
| Selected test is a `@ParameterizedTest` | Treat the function as a single unit; append new `@MethodSource` case is considered additive (sibling-add), not assertion-append. |
| Selected test is in a Kotest `StringSpec`/`ShouldSpec`/`DescribeSpec` | Sibling-add = new leaf (`"should ..." { }`); append-assertions = add matchers inside the existing leaf. Overlay guides detection per-style. |

## 8. Capabilities in detail

### 8.1 Scope picker

Two queues, populated from the **triage output** (`build/reports/pitest/triage.json` — machine-readable, preferred over `triage.md`), filtered to `LIKELY_KILLABLE` only:

- **Strengthen queue**: LIKELY_KILLABLE tests with ≥1 surviving covered mutant. Ordered by (a) number of LIKELY_KILLABLE survivors the test covers (desc), (b) class name.
- **Add-new-test queue**: LIKELY_KILLABLE mutants with `status=NO_COVERAGE`. Ordered by (a) number of such mutants in the class (desc), (b) line number.

**Input requirement — `mutation-testing` v0.5+.** The strengthen queue's primary key is `test:<FQN>`, built by inverting the `coveringTests` list on each survivor. Requires triage output to name covering tests per survivor (emitted when `fullMutationMatrix=true` is set in `pitest {}`; triage.py exposes them in `triage.json.covering_tests` as of `mutation-testing` v0.5). If the triage output was produced against a pitest run with `fullMutationMatrix=false`, the strengthen queue cannot be built — **abort with instructions to re-run pitest with the flag on**, rather than fall through to add-new-test and silently skip the higher-leverage queue.

`LIKELY_EQUIVALENT` mutants are **never** fed to the loop — they're an input to `suspected-equivalent.md`, not a target. `AMBIGUOUS` mutants are deferred to human review; the loop does not touch them either.

Ralph iteration drains the strengthen queue first (higher leverage, safer). Falls through to the add-new-test queue when strengthen is empty for the current package, then advances packages.

The picker skips:
- Tests/mutants already tried this session (from `progress.json` `attempts`).
- Tests in `blacklisted_flakes`.
- Mutants in `equivalent_candidates` with ≥3 cross-session failures.

**Pre-loop viability check.** If every class in the initial scope has zero `LIKELY_KILLABLE` survivors (strengthen AND add-new-test queues empty globally), abort with a "no work to do — expand scope or relax archetypes" message rather than iterate through empty packages. Overnight loops must fail-fast on this, not burn hours re-running a picker that can never find work.

**`targetClasses` scoping rule.** The loop passes scope via **`-PpitestScope=<FQN>`** (or equivalent) on the gradle CLI — it does NOT edit `build.gradle.kts` between iterations. Per-iteration edits to the build file pollute git state, defeat the clean-tree precondition, and make rollback-on-reject non-trivial.

**Required wiring.** The `info.solidsoft.pitest` plugin does NOT read `-Ppitest.targetClasses` natively — CLI flags with that name are silently ignored. The `pitest { }` block must explicitly read a project property (name suggestion: `pitestScope`) and auto-expand each FQN to `{FQN, FQN$*}` before setting `targetClasses`. `mutation-testing` v0.5+ ships a wiring snippet in SKILL.md §5; autoresearch v0.1 documents it as a setup precondition and aborts if the `pitest { }` block doesn't honor the override. First-run check: invoke with an obviously-wrong `pitestScope` value and assert pitest's logged `ReportOptions[... targetClasses=[...]]` reflects the override. If not, surface a "your `pitest {}` block needs wiring — see mutation-testing SKILL.md §5" error.

**Scope-set expansion.** The wired block auto-expands `FQN` to `{FQN, FQN$*}`: Kotlin emits synthetic classes for nested data classes (`Foo$Page`) and lambdas (`Foo$methodName$1`), and the bare FQN alone won't match them. A trailing `*` on the prefix (`Foo*`) is the opposite mistake — it matches sibling top-level classes (`FooService`) and inflates scope. The loop never passes prefix-globs on the CLI; it always passes exact FQNs and lets the wiring handle expansion.

### 8.2 Ralph iteration prompt (shell-composed)

The shell script composes a prompt similar to:

```bash
claude --permission-mode acceptEdits \
  "@$SKILL_DIR/PRD.md @$SKILL_DIR/progress.txt @$SKILL_DIR/progress.json \
   1. Read the PRD, progress.txt, progress.json. \
   2. Run /mutation-testing to get the current survivor list. \
   3. Follow the scope picker rules to select one TEST (or one NO_COVERAGE mutant if strengthen queue is empty). \
   4. Based on MODE=$MODE, strengthen (append-assertions) or add a sibling @Test (add-sibling) \
      or create a new test (add-new-test branch). \
   5. Run /test-gradle filtered to the test class. Must be green. \
   6. Run the full test suite. Must be green. \
   7. Rerun pitest scoped to the affected class. \
   8. Apply all guards (§9). \
   9. On accept: /commit with the skill's commit-message template. On reject: git reset --hard HEAD. \
   10. Update progress.txt + progress.json. \
   11. If no survivors remain globally, emit <promise>COMPLETE</promise>. \
   ONLY DO ONE TEST PER ITERATION."
```

### 8.3 Ratchet

Per iteration, record `baseline_killed_count` for the class from the latest pitest report. After the edit:

1. Full existing suite green? (green fail → revert)
2. Class-scoped pitest rerun `new_killed_count > baseline_killed_count`? (no → revert)
3. The mutant the iteration specifically targeted moved SURVIVED → KILLED? (no → revert)
4. Any previously-killed mutant now surviving? (yes → revert — regression)
5. All guards (§9) pass? (no → revert)

Only on all-yes: `/commit`.

**Partial kills are expected and acceptable.** A single strengthened test often moves several covered mutants from SURVIVED to KILLED — the ratchet counts every one. Conversely, a well-written test may kill _some_ mutants on a line (e.g. `EQUAL_ELSE`) but leave others (`EQUAL_IF`) surviving because the IF-branch is observably identical to the ELSE-branch on the existing test's input space. That's archetype D (branch-identity) surfacing dynamically — the remaining mutant is a strong candidate for `LIKELY_EQUIVALENT`. The ratchet still accepts the iteration as a win: rule #3 only requires the **targeted** mutant to die, not every mutant on the line.

**Promote partial-kill residuals to `SUSPECTED_EQUIVALENT` faster.** US-30 promotes after 3 cross-session failed kill attempts. For mutants that survived a sibling kill on the same line (one EQUAL_ELSE killed, the EQUAL_IF survived), use a stricter 2-attempt threshold — the signal is already stronger than blind failure. Record the sibling-kill event in `progress.json.attempts` for the surviving mutant so the threshold logic can detect it.

**Coverage-threshold exit is not a pitest failure.** Pitest exits non-zero when `coverageThreshold` / `mutationThreshold` / `testStrengthThreshold` aren't met — common on narrow single-class reruns since the thresholds are calibrated for whole-module runs. **The XML is still written and valid in this case.** The ratchet must gate on parsing `mutations.xml` and comparing killed-counts, not on the Gradle exit code. §7.4 edge case table updated accordingly: "scoped pitest exits non-zero but `mutations.xml` is newer than the iteration start and parses cleanly → proceed with ratchet". Only treat the rerun as a true failure when (a) the XML is missing, (b) it's older than the iteration start (pitest didn't write it), or (c) it doesn't parse.

### 8.4 Mode: `add-sibling` (strengthen branch default)

Prompt constraint: "Add a new `@Test` method (or Kotest `it`/`should` leaf) to the existing covering test class. Do not modify any existing test body. Place in the class conventionally — follow patterns in `references/project.md` if present."

Guard: git diff must consist only of **added** lines in `src/test/`. Modified or deleted lines anywhere in `src/test/` → revert.

### 8.5 Mode: `append-assertions` (strengthen branch, opt-in)

Prompt constraint: "Append assertions inside the existing covering test. May not rename tests, delete/weaken assertions, modify fixtures, or edit tests authored within the last 14 days."

Guard (runs before commit):
1. Diff confined to `src/test/`.
2. No removed lines matching `(^|\s)(assert|verify|expect|require|check|should|shouldBe|shouldNot|must)[A-Za-z\w]*` (regex tuned per assertion library — AssertJ, JUnit, Kotest, MockK). Overlay may extend.
3. No test renames. Detected by verifying the set of `fun (\`[^\`]+\`|\w+)\s*\(` declarations post-edit is a superset of pre-edit.
4. No edits to `@BeforeEach|@AfterEach|@BeforeAll|@AfterAll|@TestFactory|@ParameterizedTest`-annotated function bodies. Approximation: reject if any modified hunk overlaps one of those annotated blocks.
5. No edits to tests whose earliest-authored commit (via `git log --follow --diff-filter=A`) is within N days (default 14).

Any trip → `git reset --hard HEAD`.

### 8.6 Branch: `add-new-test` (NO_COVERAGE fallback)

Prompt constraint: "Create a new test for the uncovered line. Follow project test conventions. Add-only: no edits to existing tests."

Guard: same as `add-sibling` — only added lines in `src/test/`.

### 8.7 Metric-gaming guards (all branches, all modes)

| # | Guard | Check |
|---|---|---|
| 9.1 | Tautology | Diff must not contain assertion comparing to the mutated constant or operator-inverse named in the survivor metadata (heuristic regex + literal-value check). |
| 9.2 | Diff confinement | Only `src/test/` files. No production-code edits. |
| 9.3 | Full suite green | `./gradlew test` exits 0. |
| 9.4 | Mutant-moved | All targeted mutants go SURVIVED → KILLED in the rerun; class `killed_count` strictly improves. |
| 9.5 | No regressions | No previously-killed mutant flips to SURVIVED. |
| 9.6 | Add-sibling diff | Zero removed lines in `src/test/` (add-sibling + add-new-test branches only). |
| 9.7 | Append-only assertions | See §8.5 (append-assertions mode only). |
| 9.8 | Suspected-equivalent (cross-session) | Skip mutants with ≥3 cross-session failed attempts — these get promoted to LIKELY_EQUIVALENT in the triage output. Runs in addition to, not instead of, the static pre-triage in `mutation-testing` §4. |
| 9.9 | Clean start | Working tree clean before any iteration. |
| 9.10 | Flake quarantine | Tests that flake >3 times in a session are blacklisted for the session. |
| 9.11 | Behavior assertion | The new/strengthened assertion must call at least one method other than a getter on the mutated class. Pure-getter assertions usually indicate duplication. |

### 8.8 Shared infrastructure with `ralph-coverage`

Both skills are Ralph-style and share scaffolding. Candidate shared pieces (extract after both skills have shipped):

| Piece | Where it could live |
|---|---|
| `afk-*.sh` loop scaffold (retry, budget, early-exit on `<promise>COMPLETE</promise>`) | `.claude/skills/_lib/` or `ralph-lib` skill |
| `ralph-once.sh` harness | Same |
| `progress.txt` append-only log convention | Same |
| `progress.json` state schema + drift check | Same |
| Clean-tree / branch-match preconditions | Same |

v1 duplicates to keep dependency surface minimal; consolidate once both stabilize.

### 8.9 Resume

Every iteration's first step:
1. Load `progress.json`.
2. Verify `git rev-parse HEAD == last_committed_rev` (if `iterations` non-empty).
3. Verify branch matches.
4. Verify working tree clean.
5. If any check fails: abort iteration, append reason to `progress.txt`. Developer decides next.

## 9. State

### 9.1 `progress.txt` (append-only, human-readable)

Ralph-style log. One block per iteration:

```
## 2026-04-18 02:34:17 — iteration 3
target: test = CalculatorTest.`positive number is positive` (covers 3 survivors)
mode: append-assertions
outcome: committed (commit a3f2c19)
killed: Calculator.kt:42 MATH, Calculator.kt:42 CONDITIONALS_BOUNDARY, Calculator.kt:43 RETURN_VALS
duration: 47s

## 2026-04-18 02:35:11 — iteration 4
target: test = CalculatorTest.`zero is not positive` (covers 1 survivor)
mode: append-assertions
outcome: rejected (reason: guard 9.1 tautology — assertion literally compared to the mutated operator)
duration: 31s
```

### 9.2 `progress.json` (structured state for resume + queues)

```json
{
  "session_id": "2026-04-18-0230",
  "started_at": "2026-04-18T02:30:11Z",
  "branch": "mutation/autoresearch/2026-04-18",
  "base_commit": "05e764b",
  "last_committed_rev": "a3f2c19",
  "mode": "append-assertions",
  "budget": 40,
  "iterations_completed": 17,
  "attempts": {
    "test:CalculatorTest.`positive number is positive`": {"outcomes": ["committed"]},
    "mutant:Calculator.kt:42:MATH": {"outcomes": ["killed-as-part-of-test"]}
  },
  "equivalent_candidates": {
    "mutant:PriceCalculator.kt:88:VOID_METHOD_CALLS": {"failures": 3, "last_session": "2026-04-17"}
  },
  "blacklisted_flakes": ["FooIntegrationTest.`happy path`"]
}
```

Primary key for attempts: `test:<fully-qualified>` or `mutant:<file>:<line>:<mutator>`. Same mutant reached via different covering tests is still one entry.

## 10. Evals

Evals compare **add-sibling vs append-assertions** on a fixed seed of real PhotoQuest tests-with-survivors plus a seed of NO_COVERAGE mutants.

Benchmark dimensions:
1. **Throughput**: mutants killed per iteration (single strengthened test often kills many).
2. **Kill-rate per unit wall-time**.
3. **Quality regression**: human-review rubric on commits. Tautologies, weakenings (append-assertions only), and non-behavioral-assertion tests count.

Seed size: 30 tests with survivors across ≥5 classes, 10 NO_COVERAGE mutants.

Representative tasks:
1. **Add-sibling baseline** — budget 30, seed 30 tests. Measure kill rate, inspect every commit, count tautologies.
2. **Append-assertions baseline** — same seed, append-assertions mode. Additional check: any weakening regressions.
3. **NO_COVERAGE fallback** — drain strengthen queue, verify loop pivots to NO_COVERAGE queue and kills with add-new-test branch.
4. **Anti-reward: deliberate tautology** — adversarial seed that nudges toward tautological assertions; guard 9.1 must trip.
5. **Anti-reward: weakening** — append-assertions seed that invites weakening a sibling assertion; guard 9.7 must trip.
6. **Resume correctness** — kill shell script at iteration 10; rerun; verify final state matches uninterrupted run.
7. **Equivalent-mutant handling** — inject known equivalent mutant; verify `SUSPECTED_EQUIVALENT` marker after 3 attempts.
8. **Budget respected** — budget 5; loop stops at 5 regardless of remaining queue.
9. **State drift** — mid-session `git commit` by hand; next iteration must abort cleanly with reason.

Binary pass/fail per task. Benchmarks → `jvm-skills/evals/mutation-autoresearch/benchmark.json`.

## 11. Open design questions

1. **Commit granularity.** One commit per iteration (= per test). Pre-pivot this was per-mutant; test-by-test is cleaner. Confirmed.
2. **Default mode.** `add-sibling` (safe, pure-additive) is default. `append-assertions` is opt-in. Confirmed in §8.4 / §8.5.
3. **Strengthen reviewer pass.** Should `append-assertions` commits be automatically sent to `/review` or `/simplify` before landing? Recommendation: not in v1, but cheap to add in v2.
4. **`/fix` escalation.** Survivor that indicates a real production bug — loop should never auto-patch, just report. Recommendation: emit a `PRODUCTION_BUG_SUSPECTED.md` with the mutant + failing-test pair; skip that mutant's queue entry.
5. **Branch strategy.** Run on a dedicated `mutation/autoresearch/<date>` branch by default; open a PR at session end. Recommendation: confirmed.
6. **Cost cap.** Overnight loop can burn API budget. Recommendation: defer hard cap until observed usage justifies it; `--budget N` already bounds it.
7. **Equivalent-mutant escalation format.** Generated `SUSPECTED_EQUIVALENT.md` at session end, entries in `progress.json`. Confirmed.
8. **Picker heuristic.** "Test with most surviving covered mutants first" is one option. Alternative: "test with highest line-coverage first". Recommendation: start with survivor-count; eval may refine.
9. **Regex tuning for guard 9.7.** AssertJ, JUnit, Kotest, MockK each have distinct assertion vocabularies. Recommendation: generalized regex in SKILL.md, overlay extends per project.
10. **Tautology detection fidelity.** Heuristic-based, will have false positives/negatives. Recommendation: bias toward false positives (reject) in v1; evals measure rate.
11. **Picker honoring package boundaries.** Should the picker finish all tests in a package before advancing? Recommendation: yes — improves locality for the developer reviewing the diff.

## 12. Skill registry YAML

```yaml
# skills/testing/mutation-autoresearch.yaml
name: Mutation Autoresearch Loop (Ralph)
description: >-
  Ralph-style overnight ratchet loop that wraps the mutation-testing skill.
  Iterates test-by-test: picks a covering test with surviving mutants,
  strengthens or adds sibling assertions via /tdd-task, and commits only if
  class mutation score improved and the existing suite stayed green. Falls
  back to add-new-test for NO_COVERAGE mutants. Metric-gaming guards block
  tautologies and assertion weakening.
repo: jvm-skills/jvm-skills
skill_path: ".claude/skills/mutation-autoresearch/SKILL.md"
category: testing
languages:
  - kotlin
  - java
trust: official
author: jvm-skills
version: "0.1.0"
last_updated: "2026-04-18"
scope: focused
tech:
  - gradle
  - pitest
  - claude-code
  - ralph
tags:
  - mutation-testing
  - autoresearch
  - ralph
  - autonomous
  - test-quality
```

## 13. Success criteria

- Overnight Ralph run of 40 iterations on PhotoQuest produces ≥20 committed iterations (test strengthenings or new tests) with zero production-code changes, zero weakened assertions, and zero tautology commits (human-audited).
- Eval quantifies the add-sibling vs append-assertions tradeoff: throughput vs quality-regression rate.
- Resume after mid-session interruption reaches the same final state as an uninterrupted run.
- No iteration exceeds `test_suite_time + scoped_pitest_time + one /tdd-task invocation + small overhead`. No runaway retries.
- `progress.txt` is sufficient for a developer to review the morning after without re-running anything. `progress.json` is sufficient for a fresh `claude` CLI to resume correctly.
- `<promise>COMPLETE</promise>` is emitted when both queues are empty globally, and the shell script exits cleanly.

## User Stories

- **US-1**: As a **developer** before EOD, I run `afk-mutation-ar.sh 40` and the Ralph loop begins iterating after verifying clean working tree, installed dependencies, and an existing baseline pitest report.
- **US-2**: As a **developer** with no baseline pitest report, the shell script refuses to loop and instead invokes `mutation-testing` once to generate the baseline, then exits — I rerun to actually start the loop.
- **US-3**: As a **developer** with a dirty working tree, the shell script aborts so it cannot clobber my work with `git reset`.
- **US-4**: As a **developer** reviewing git log the next morning, I see one commit per successful iteration with a message like `test(mutation): strengthen CalculatorTest — killed MATH, CONDITIONALS_BOUNDARY, RETURN_VALS at Calculator.kt:42-43`.
- **US-5**: As a **developer**, I open `progress.txt` and read a human-friendly append-only log of every iteration's target, outcome, killed mutants, and duration — no JSON parsing needed.
- **US-6**: As a **developer**, I inspect `progress.json` to understand which tests/mutants have been attempted, which are blacklisted as flakes, and which mutants are suspected-equivalent.
- **US-7**: As a **Ralph iteration (fresh Claude CLI)**, I read `PRD.md` + `progress.txt` + `progress.json`, pick one target via the scope picker, execute one iteration, commit-or-revert, and update both progress files before exiting.
- **US-8**: As a **Ralph iteration**, I drain the strengthen queue (tests with covered survivors) before pivoting to the NO_COVERAGE queue (add-new-test branch).
- **US-9**: As a **Ralph iteration in strengthen branch / add-sibling mode (default)**, I add a new `@Test` (or Kotest leaf) to the existing covering test class — purely additive — and reject any diff that modifies existing `src/test/` lines.
- **US-10**: As a **Ralph iteration in strengthen branch / append-assertions mode**, I append assertions to the existing test and reject any diff that removes assertions, renames tests, edits fixtures, or touches tests authored within 14 days.
- **US-11**: As a **Ralph iteration in add-new-test branch** (NO_COVERAGE fallback), I create a new test for an uncovered line following project conventions, add-only.
- **US-12**: As a **Ralph iteration**, I detect a tautological assertion (literally compares to the mutated constant/operator-inverse) via guard 9.1 and revert the iteration even if the suite is green.
- **US-13**: As a **Ralph iteration**, I rerun pitest scoped to the single class and commit only if (a) all targeted mutants went SURVIVED → KILLED, (b) class killed_count strictly improved, (c) no previously-killed mutant regressed.
- **US-14**: As a **Ralph iteration**, when a single strengthened test kills multiple mutants, I count all kills and commit once.
- **US-15**: As a **developer**, the shell loop stops exactly at the `--budget N` iterations regardless of remaining survivors, finishing the current iteration cleanly before exiting.
- **US-16**: As a **developer**, when my laptop sleeps and interrupts the loop, I rerun the shell script; each Ralph iteration verifies state matches `progress.json` and continues from the next un-attempted target.
- **US-17**: As a **Ralph iteration**, if `git rev-parse HEAD` does not match `progress.json.last_committed_rev` (state drifted), I abort the iteration with a reason logged to `progress.txt` rather than proceed blindly.
- **US-18**: As a **Ralph iteration**, I retry a failed scoped-pitest run once to absorb flakes, but revert the iteration on a second failure rather than loop.
- **US-19**: As a **Ralph iteration**, I track flaky tests in `progress.json` and after 3 flakes in one session I quarantine that test for the remainder of the session.
- **US-20**: As a **Ralph iteration**, I mark a mutant `SUSPECTED_EQUIVALENT` after 3 cross-session failed attempts and skip it in future iterations; a `SUSPECTED_EQUIVALENT.md` is generated at session end for developer review.
- **US-21**: As a **developer**, the loop runs on a dedicated branch (`mutation/autoresearch/<date>`) by default and opens a PR at session end, respecting required-review protections on `main`.
- **US-22**: As a **developer**, I compose `/loop 90s /mutation-autoresearch` as an alternative when I want interactive pacing rather than fire-and-forget shell loop.
- **US-23**: As a **skill author**, I run the eval suite comparing add-sibling vs append-assertions modes on a 30-test + 10-NO_COVERAGE seed and get a benchmark JSON with throughput, kill-rate-per-minute, and human-rubric regression counts.
- **US-24**: As a **skill author**, the adversarial evals confirm the tautology guard and the weakening guard trip on deliberately-weak survivors.
- **US-25**: As a **Ralph iteration**, I never invoke `/fix` — a survivor that indicates a real production bug is surfaced via `PRODUCTION_BUG_SUSPECTED.md` for manual decision, not auto-patched.
- **US-26**: As a **Ralph iteration without `/tdd-task` installed**, I follow the inline inverted-TDD checklist in SKILL.md — the test passes against current-correct production code; the RED→GREEN proof comes from the scoped pitest rerun flipping the mutant from SURVIVED to KILLED, not from an initial red state.
- **US-27**: As a **developer**, when both queues are globally empty, the iteration emits `<promise>COMPLETE</promise>` and the shell loop exits early with a "no survivors remaining" summary.
- **US-28**: As a **Ralph iteration**, I read `build/reports/pitest/triage.md` (the `mutation-testing` v0.3 triage output) and iterate **only** over `LIKELY_KILLABLE` targets — `LIKELY_EQUIVALENT` and `AMBIGUOUS` mutants are never picked.
- **US-29**: As a **developer** with no triage output (or one staler than `mutations.xml`), the shell script refuses to loop and invokes `/mutation-testing` triage first, then exits so I can review `triage.md` before kicking off autoresearch.
- **US-30**: As a **Ralph iteration** that fails to kill a `LIKELY_KILLABLE` mutant three times across sessions, I promote it to `LIKELY_EQUIVALENT` by appending it to `suspected-equivalent.md` with the reason "no killing test found after 3 attempts"; the next triage run pre-excludes it.
- **US-31**: As a **developer starting an overnight run whose triage output was produced with `fullMutationMatrix=false`**, the shell script aborts with instructions to rerun pitest with the flag on, rather than silently fall back to the add-new-test queue and skip the strengthen branch entirely.
- **US-32**: As a **Ralph iteration**, I gate the ratchet on parsing `mutations.xml` (killed-count delta, target status transition, no regressions), not on pitest's Gradle exit code — because narrow single-class reruns legitimately trip `coverageThreshold` / `mutationThreshold` on valid, well-scoped kills.
- **US-33**: As a **developer starting a session where every class in the initial scope already has zero `LIKELY_KILLABLE` survivors**, the shell script aborts with "no work to do — expand scope or relax archetypes" rather than iterate through empty packages burning API budget.
- **US-34**: As a **Ralph iteration**, I scope pitest via `-PpitestScope=<FQN>` on the gradle CLI — never by editing `build.gradle.kts` between iterations (pollutes git state, breaks the clean-tree precondition). The `pitest { }` block wires this property and auto-expands each FQN to `{FQN, FQN$*}` so Kotlin-emitted synthetic lambda and inner-data-class bytecode are analyzed alongside the outer class.
- **US-35**: As a **developer starting autoresearch on a project whose `pitest { }` block doesn't wire the `pitestScope` property**, the preflight detects it (by invoking pitest with a fake scope and reading the logged `ReportOptions.targetClasses`) and aborts with a pointer to mutation-testing SKILL.md §5 for the wiring snippet — the `info.solidsoft.pitest` plugin does NOT honor `-Ppitest.targetClasses` natively.
- **US-36**: As a **Ralph iteration**, I accept a partial-kill outcome (the targeted mutant moved SURVIVED→KILLED but a sibling mutant on the same line survived) as a successful iteration and commit, rather than requiring every mutant on the line to die. Sibling survivors are recorded with a `partial_kill_sibling` marker in `progress.json.attempts` so the equivalent-promotion threshold (US-30) can drop to 2 attempts for them — a survivor on the same line as a successful kill is strong evidence of archetype D (branch-identity equivalence).
