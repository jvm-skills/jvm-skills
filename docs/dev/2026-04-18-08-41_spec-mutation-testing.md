# Spec: `mutation-testing` skill

**Skill path (generalized):** `jvm-skills/.claude/skills/mutation-testing/SKILL.md`
**Project overlay (battle-test):** `PhotoQuest/.claude/skills/mutation-testing/references/project.md`
**Evals:** `PhotoQuest/.claude/skills/mutation-testing/evals/evals.json` → benchmarks land in `jvm-skills/evals/mutation-testing/benchmark.json`
**Registry listing:** `jvm-skills/skills/testing/mutation-testing.yaml`
**Category:** `testing`
**Trust:** `official`

## 1. Purpose

Give JVM developers and AI agents a reliable, non-intrusive way to run mutation testing on Kotlin/Java code with **pitest** via the `info.solidsoft.pitest` Gradle plugin. The skill bootstraps the plugin with Kotlin-sensible defaults, runs pitest scoped to changed classes (not the whole suite), parses surviving mutants from the XML report, and drives a tight kill-survivor loop that hands each survivor to `/tdd-task` or `/fix`.

The skill is the **foundation** for the separately-specced `mutation-autoresearch` skill, which wraps it in a Karpathy/Shopify-style ratchet loop.

## 2. Why pitest (not mutflow, not rogervinas/mutation-testing)

| Option | Verdict | Reason |
|---|---|---|
| **pitest + `info.solidsoft.pitest`** | ✅ **Chosen** | 10+ years mature, bytecode-level (zero production-code changes), structured HTML+XML reports, Kotlin+Java, any JUnit version, SonarQube-compatible, multi-module aggregation, large mutator library. |
| mutflow (anschnapp) | ❌ Rejected | 17 stars, actively evolving but young. Requires `@MutationTarget` on production code and wrapping code under test in `MutFlow.underTest {}` blocks — intrusive. Kotlin 2.3.0+ and JUnit 6 only. Only tests code reached inside `underTest` blocks, easy to miss coverage. |
| rogervinas/mutation-testing | ❌ Not a tool | Demo repo, not a skill. Useful as **reference material** for Kotlin-specific pitest config (`avoidCallsTo = kotlin.jvm.internal`, etc.). |

The mutflow design may be revisited once it reaches ~1.0 and the project has standardized on Kotlin 2.3+/JUnit 6 — a future sibling skill, not a replacement.

## 3. Scope

**In scope:**
- Kotlin/JVM and Java/JVM projects using Gradle (Kotlin DSL primary; Groovy DSL supported via analogous snippets).
- Bootstrap of `info.solidsoft.pitest` plugin with sane Kotlin defaults.
- Scoped mutation runs derived from `git diff`.
- Survivor interpretation from `mutations.xml`.
- Driving the kill-survivor workflow via `/tdd-task` or `/fix`.
- Thresholds (`mutationThreshold`, `coverageThreshold`) guidance and CI wiring.
- `pitestReportAggregate` for multi-module builds.

**Out of scope:**
- Non-Gradle build systems (Maven pitest plugin exists but is a separate skill if ever needed).
- Mutation testing for languages outside the JVM.
- The autoresearch loop (separate skill: `mutation-autoresearch`).
- Tooling for mutflow (future sibling skill).

## 4. Roles

| Role | Interacts via |
|---|---|
| **Developer** | `/mutation-testing` in an AI coding tool (Claude Code, Cursor, etc.) or by reading the SKILL.md and running commands manually. |
| **AI agent** (Claude Code, Cursor, Copilot, Windsurf, aider) | Consumes `SKILL.md` as context, executes the capabilities. |
| **Skill author / maintainer** | Owns `SKILL.md`, evals, and benchmark results. |
| **CI system** | Runs `./gradlew pitest` or an aggregated task as a gate. |

There is no end-user UI; "screens" in this spec are CLI output, Gradle reports, and the parsed survivor summary.

## 5. Entry points

The skill is entered in four ways:

1. **Invocation by name** — user or agent types `/mutation-testing` (or Cursor/Windsurf equivalent).
2. **Triggered by description match** — AI tool auto-activates when the user asks "check mutation testing", "add mutation tests", "why does this mutant survive", etc.
3. **Referenced by `mutation-autoresearch`** — the loop skill depends on this one.
4. **Discovered via jvmskills.com** — listed under `skills/testing/mutation-testing.yaml`.

The first time the skill runs in a project, it detects whether pitest is already configured in `build.gradle.kts` (or `settings.gradle.kts` / `*.gradle` / root build for multi-module). If not, the Bootstrap capability runs before anything else.

## 6. User journey

### 6.1 Happy path — first run

1. Developer asks "let's add mutation testing to this project".
2. Agent invokes `/mutation-testing`.
3. Skill reads `build.gradle.kts`, sees no `info.solidsoft.pitest` plugin.
4. Skill proposes a minimal block with Kotlin defaults (see §8 Bootstrap). Developer confirms the diff.
5. Skill runs `./gradlew pitest` once on the full project (only the first run; later runs are scoped).
6. Skill opens `build/reports/pitest/index.html` and prints a compact CLI summary: total mutants, killed, survived, no-coverage, timed-out.
7. Skill writes `progress.md` (or analogous) noting starting thresholds.
8. Terminal state: developer has a baseline. Forward action: either iterate survivors now, or set CI thresholds and come back later.

### 6.2 Happy path — scoped run after changes

1. Developer changes a handful of files and asks "mutation-check my changes".
2. Skill runs `git diff --name-only <base>..HEAD` (or `--staged`, or worktree — scope is configurable, default is "changed vs merge-base of current branch and main").
3. Skill maps changed `*.kt` / `*.java` files to fully-qualified class names.
4. Skill runs `./gradlew pitest -PtargetClasses=<csv> -PtargetTests=<csv>` (or equivalent via a dedicated task).
5. Skill parses `mutations.xml`, prints a CLI table of survivors with: file:line, mutator, status, covering tests, and a plain-English description of the behavior that slipped through.
6. Terminal state: zero or more survivors listed. Forward action: kill-one or commit-as-is.

### 6.3 Happy path — kill a survivor

1. Developer picks a survivor (or runs "kill all survivors").
2. Skill invokes `/tdd-task` with a prompt containing: file path, line number, mutator description, the covering test class (if any), the mutated behavior in English.
3. `/tdd-task` writes a failing test that exercises the mutated behavior, watches it fail, implements/strengthens, sees it pass.
4. Skill reruns pitest scoped to the single class (`targetClasses=<fqn>`).
5. If the mutant is now killed and no previously-killed mutants regressed: skill invokes `/commit`. Else: skill surfaces the failure for manual decision.
6. Terminal state: survivor killed or escalated. Forward action: next survivor.

### 6.4 CI wiring

1. Developer asks "wire mutation testing into CI".
2. Skill proposes thresholds (`mutationThreshold=60`, `coverageThreshold=60` starting; ratchet up to 75/80 later).
3. Skill adds a step to the project's CI YAML that runs `./gradlew pitest` and uploads `build/reports/pitest/` as an artifact.
4. For multi-module: skill uses `pitestReportAggregate`.

### 6.5 Edge cases & error states

| Situation | Behavior |
|---|---|
| Project has no tests at all | Skill warns, runs pitest anyway so developer sees "no coverage" mutants as a baseline. Recommends `/ralph-coverage` or `/kotest-create` first. |
| JUnit 4 project | Skill omits `junit5PluginVersion` and notes that default pitest JUnit support handles it. |
| JUnit 5 project | Skill sets `junit5PluginVersion` to a known-compatible release. |
| Mix of JUnit 4 and JUnit 5 | Skill sets `junit5PluginVersion` and notes that vintage engine is required; surfaces the dependency check. |
| Kotlin inline classes / value classes | Skill adds `avoidCallsTo = kotlin.jvm.internal` and flags any known-problematic mutators for inline-heavy code in the overlay. |
| Kotlin coroutines / suspend funs | Skill notes that some suspend state-machine bytecode produces noisy mutants; developer can narrow `mutators` if survivors are all generated-bridge mutations. |
| Compose / ksp-heavy modules | Skill recommends excluding generated classes via `excludedClasses`. |
| Groovy-DSL project | Skill emits the equivalent `build.gradle` block instead of `build.gradle.kts`. |
| `build/reports/pitest/` missing after a supposed-successful run | Skill surfaces the actual Gradle failure rather than claiming success — never fabricate a result. |
| `targetClasses` glob matches nothing | Skill aborts with a clear message; does not silently run on the whole project. |
| Multi-module project, pitest configured only in leaf modules | Skill proposes the `subprojects { apply plugin: "info.solidsoft.pitest" }` pattern plus an aggregator module using `pitestReportAggregate`. |
| Multi-module project, pitest configured at root | Skill respects existing structure and only runs on the module containing changed files. |
| Pitest takes >60s on a scoped run | Skill reports runtime and suggests narrowing `targetClasses` further (single class) or reducing `mutators` to `DEFAULTS`. |
| Infinite-loop mutants (timeouts) | Skill surfaces them distinctly in the summary — they are not "survivors", they are "timed out" and usually indicate pitest's own timeout heuristic working correctly. Developer may add `// pitest:ignore` or refine the target. |
| No survivors | Skill congratulates and suggests ratcheting the threshold up. |
| Existing pitest config present | Skill respects it; only patches gaps (e.g. adds `outputFormats` if missing). Never silently overwrites. |

## 7. State / resources

The skill itself is stateless per-invocation. Persistent artifacts it relies on or produces:

| Artifact | Location | Owner |
|---|---|---|
| Plugin config | `build.gradle.kts` (root or per-module) | Project |
| Pitest reports | `build/reports/pitest/<timestamp>/` | Project, gitignored |
| `mutations.xml` | `build/reports/pitest/<timestamp>/mutations.xml` | Project, consumed by skill |
| Aggregated report | `build/reports/pitest-aggregate/` | Project |
| Skill overlay | `.claude/skills/mutation-testing/references/project.md` | Per-project |
| Evals | `.claude/skills/mutation-testing/evals/evals.json` | Per-project |
| Benchmark | `jvm-skills/evals/mutation-testing/benchmark.json` | jvm-skills |

## 8. Capabilities in detail

### 8.1 Bootstrap

Detect current state, then propose a minimal `build.gradle.kts` diff:

```kotlin
plugins {
    id("info.solidsoft.pitest") version "1.19.0"
}

pitest {
    targetClasses.set(setOf("<group-package>.*"))
    targetTests.set(setOf("<group-package>.*"))
    mutators.set(setOf("STRONGER"))
    avoidCallsTo.set(setOf("kotlin.jvm.internal", "kotlin.Metadata"))
    junit5PluginVersion.set("1.2.1")          // only for JUnit 5 projects
    outputFormats.set(setOf("HTML", "XML"))
    threads.set(Runtime.getRuntime().availableProcessors())
    timestampedReports.set(false)             // stable path for parsing
    mutationThreshold.set(60)
    coverageThreshold.set(60)
    testStrengthThreshold.set(60)
    verbose.set(false)
}
```

Open design question: **should `timestampedReports` be `false` (easier parsing) or `true` (historical record)?** Recommendation: `false`, because the skill parses the report programmatically and CI artifact upload handles history.

### 8.2 Scoped run

```bash
# Generalized form (skill composes this from git diff)
./gradlew :<module>:pitest \
  -Ppitest.targetClasses=com.example.Foo,com.example.Bar \
  -Ppitest.targetTests=com.example.*
```

The skill reads `git merge-base HEAD <default-branch>` → `git diff --name-only <base> HEAD` → maps paths to FQNs → builds the CSV. Only files under `src/main/kotlin` or `src/main/java` become `targetClasses`.

### 8.3 Interpret survivors

Parse `mutations.xml`, which has one `<mutation>` element per mutant. Relevant attributes: `status` (SURVIVED, KILLED, NO_COVERAGE, TIMED_OUT, MEMORY_ERROR, RUN_ERROR, NON_VIABLE), `sourceFile`, `mutatedClass`, `mutatedMethod`, `lineNumber`, `mutator`, `killingTest`, `description`.

Output: compact table + one-line English explanation per surviving mutant derived from `mutator` and `description`. Example:

```
SURVIVED  Calculator.kt:42  MATH                isPositive() → swapped + for -
          covering tests: CalculatorTest.`positive number is positive`
```

### 8.4 Kill survivors

For each survivor:

1. Compose a prompt for `/tdd-task` with: survivor metadata, the mutator's behavior, the existing covering test, and the constraint "write a test that fails when the described mutation is applied and passes otherwise. Do not assert the raw mutated value; assert the observable behavior."
2. Delegate to `/tdd-task` (fallback inline if unavailable).
3. Rerun pitest scoped to the single class.
4. If mutant killed and no regressions: delegate to `/commit`.
5. If killed but another previously-killed mutant now survives: do not commit; report regression.
6. If still surviving: surface the full test + mutant detail for human decision.

### 8.5 Threshold guidance

- **Starting**: `mutationThreshold=60`, `coverageThreshold=60`.
- **Ratcheting rule**: raise by 5 when the actual score has been ≥ target + 10 for two consecutive CI runs. Skill implements this as a one-shot "check-and-ratchet" capability, not an auto-edit during every run.
- **Ceiling**: skill advises against going above `mutationThreshold=85` without a deliberate investment decision — the last 15% is disproportionately expensive and often hits equivalent mutants.

### 8.6 CI wiring

Emit a patch for the detected CI platform (GitHub Actions detected by `.github/workflows/`). Uploads `build/reports/pitest/` as an artifact and fails the build on threshold breach.

### 8.7 Multi-module aggregation

If `settings.gradle.kts` declares multiple modules, propose:

```kotlin
// root build.gradle.kts
plugins {
    id("info.solidsoft.pitest.aggregator") version "1.19.0"
}
dependencies {
    pitestReport(project(":module-a"))
    pitestReport(project(":module-b"))
}
```

And run `./gradlew pitestReportAggregate`.

## 9. Dependencies

| Dependency | Why |
|---|---|
| `/tdd-task` | Primary driver for killing survivors. |
| `/fix` | Alternative when the survivor indicates a real bug (test missing AND implementation wrong). |
| `/test-gradle` | Filtered test runs between mutant-kill attempts. |
| `/commit` | Commits after each killed survivor. |

**Inline fallbacks** must exist for every dependency. If `/tdd-task` isn't installed, SKILL.md contains a 5-step TDD checklist the agent follows directly.

## 10. Kotlin-specific gotchas to document

| Gotcha | Mitigation |
|---|---|
| `kotlin.jvm.internal` noise | `avoidCallsTo.set(setOf("kotlin.jvm.internal", "kotlin.Metadata"))` |
| Data class `component*`/`copy`/`equals`/`hashCode` mutants | Usually excluded via `excludedMethods` or accepted as low-value. |
| Inline classes / value classes | `excludedClasses` for the wrapper; test against the underlying type. |
| `when` exhaustiveness | Pitest mutates conditional boundaries; many survive as equivalent. Note in overlay. |
| Extension functions compiling to static methods | Ensure `targetClasses` glob covers the file-level class (`FooKt`). |
| Coroutines state-machine mutants | Consider narrower mutators (DEFAULTS) for coroutine-heavy modules. |
| IntelliJ Gradle DSL warning on lazy-property assignment | Use `.set()` explicitly. |

These live in `SKILL.md` at the jvm-skills level (generic) and are extended in the project overlay with project-specific patterns (base test classes, shared mothers, skip list).

## 11. Evals

Evals follow the PhotoQuest pattern: `evals/evals.json` with real tasks pulled from Linear. Representative tasks:

1. **Bootstrap from zero** — clean Kotlin + Spring Boot project with JUnit 5; add pitest, run once, report survivors.
2. **Scoped run on a real change** — check out a real PhotoQuest PR branch, skill should only mutation-test the changed files.
3. **Kill a specific survivor** — deterministic seed: a known `MATH` survivor in a known file; skill must kill it via `/tdd-task`.
4. **Handle a no-coverage class** — class exists, no tests; skill surfaces "NO_COVERAGE" and recommends `/kotest-create` first.
5. **Threshold ratchet** — current score is 72%, threshold 60; skill proposes raising to 65.
6. **Multi-module aggregation** — modular project; skill proposes aggregator config and runs it.
7. **Anti-reward: tautological assertion** — skill must NOT propose a test that asserts the exact mutated operator/value; evaluated by human-readable rubric.

Binary pass/fail rubric per eval. Benchmarks (pass rate across tasks) flow back to `jvm-skills/evals/mutation-testing/benchmark.json`.

## 12. Open design questions

1. **Default `targetClasses` on bootstrap.** Derive from `rootProject.group` or require explicit user input? Recommendation: derive but show the detected value for confirmation.
2. **`timestampedReports`.** Default `false` for parseability (proposed) vs `true` for history.
3. **Default `mutators` set.** `STRONGER` (proposed) vs `DEFAULTS` (faster) vs `ALL` (noisy). Recommendation: `STRONGER`, fall back to `DEFAULTS` if runtime exceeds a budget.
4. **Scope boundary of "changed".** `HEAD..merge-base origin/main` vs `--staged` vs worktree. Recommendation: merge-base with the default branch, overridable.
5. **Should the skill ever modify production code?** Recommendation: no. The skill only writes tests (and build config during bootstrap). Fixes to production code go through `/fix` explicitly.
6. **Interaction with existing thresholds.** If a project has stricter thresholds, never loosen them. Recommendation: treat existing config as a floor.
7. **Pitest version pinning.** Pin to 1.19.0 in the SKILL.md or always "latest known"? Recommendation: pin, with a note to update periodically.
8. **JUnit plugin version matrix.** Maintain a known-compatible matrix in `references/` or trust the plugin's defaults? Recommendation: matrix.

## 13. Skill registry YAML

```yaml
# skills/testing/mutation-testing.yaml
name: Mutation Testing (pitest)
description: >-
  Bootstrap pitest via the info.solidsoft.pitest Gradle plugin with Kotlin-sane
  defaults, run scoped mutation tests on changed classes, interpret surviving
  mutants from mutations.xml, and drive a kill-survivor workflow via /tdd-task.
repo: jvm-skills/jvm-skills
skill_path: ".claude/skills/mutation-testing/SKILL.md"
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
  - junit5
tags:
  - mutation-testing
  - pitest
  - test-quality
  - tdd
```

## 14. Success criteria

- Bootstrap diff is minimal, idempotent, and passes `./gradlew pitest` on the first run in a greenfield Kotlin+Spring Boot project.
- Scoped run on a typical PR-sized change (<10 files) completes in under 60 seconds on developer hardware.
- Survivor output is readable without opening the HTML report — the English one-liner per mutant is enough to decide.
- At least 5 of 7 evals pass on first benchmark.
- Skill is unsurprising in the presence of existing pitest config — never overwrites, only gap-fills.

## User Stories

- **US-1**: As a **developer**, I type `/mutation-testing` in my AI coding tool so the skill detects whether pitest is configured and proposes a bootstrap diff if not.
- **US-2**: As a **developer** on a Kotlin + JUnit 5 + Spring Boot project, I accept the bootstrap diff and `./gradlew pitest` runs cleanly on the first try with the Kotlin-sane defaults (`avoidCallsTo`, `junit5PluginVersion`, `STRONGER` mutators, `HTML+XML` outputs).
- **US-3**: As a **developer** with existing pitest config, I invoke the skill and it respects my config, only gap-filling missing fields (e.g. adding `XML` output if only `HTML` is set) and never overwriting my thresholds.
- **US-4**: As a **developer** who just made changes to a few files, I ask the skill to "mutation-check my changes" and it derives `targetClasses` from `git diff` against the default branch, running only on those classes and completing in under a minute.
- **US-5**: As a **developer**, I read the skill's CLI survivor summary and can identify each survivor's file:line, mutator, and a plain-English description of the behavior that slipped through — without opening the HTML report.
- **US-6**: As a **developer**, I ask the skill to "kill this survivor" and it delegates to `/tdd-task` with enough context (file, line, mutator, covering test) that the resulting test actually kills the mutant on rerun, not just passes in isolation.
- **US-7**: As a **developer**, I see that a proposed killing test would assert the exact mutated value (tautology); the skill refuses and retries with a behavior-based assertion instead.
- **US-8**: As a **developer**, after a killing test is written, the skill reruns pitest on only the one class and confirms both the target mutant is killed AND no previously-killed mutants regressed before invoking `/commit`.
- **US-9**: As a **developer**, when a survivor actually indicates a production bug (mutant survives because implementation is wrong, not because test is weak), I can route the kill through `/fix` instead of `/tdd-task`.
- **US-10**: As a **developer** on a project with no existing tests, I run the skill and it surfaces "NO_COVERAGE" distinctly from "SURVIVED" and recommends running `/ralph-coverage` or `/kotest-create` first.
- **US-11**: As a **developer** on a multi-module Gradle build, the skill proposes `pitestReportAggregate` config and runs aggregation across modules.
- **US-12**: As a **developer**, I ask the skill to wire mutation testing into CI; it patches my GitHub Actions workflow with a `./gradlew pitest` step, artifact upload, and thresholds of 60/60 to start.
- **US-13**: As a **developer**, after two green CI runs at ≥70% mutation score with a 60% threshold, the skill proposes ratcheting the threshold up by 5.
- **US-14**: As a **developer**, I see pitest timed out on a mutant; the skill distinguishes "TIMED_OUT" from "SURVIVED" in the summary and explains this usually means pitest's loop-timeout heuristic worked correctly.
- **US-15**: As a **developer** with a JUnit 4 + JUnit 5 mixed project, the skill sets `junit5PluginVersion`, confirms vintage engine dependency is present, and flags if it isn't.
- **US-16**: As an **AI agent** with `/tdd-task`, `/fix`, `/test-gradle`, and `/commit` all installed, I execute the full kill-a-survivor cycle via delegated skills.
- **US-17**: As an **AI agent** without any of the dependency skills installed, I follow the inline fallback instructions in SKILL.md and still complete the kill-a-survivor cycle.
- **US-18**: As a **skill author / maintainer**, I run the eval suite on PhotoQuest and receive a benchmark JSON with pass/fail per task, including the anti-reward tautology-rejection check.
- **US-19**: As a **CI system**, I fail the build when mutation score dips below `mutationThreshold`, and the uploaded `build/reports/pitest/` artifact contains both `index.html` and `mutations.xml`.
- **US-20**: As a **developer** whose scoped run matched zero classes (changes only in test files), the skill aborts with a clear "no target classes to mutate" message instead of silently running on the whole project.
