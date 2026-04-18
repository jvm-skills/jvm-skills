---
name: mutation-testing
description: Bootstrap pitest via the info.solidsoft.pitest Gradle plugin with Kotlin-sane defaults, run mutation tests scoped to changed classes, interpret surviving mutants from mutations.xml, triage likely-equivalent mutants out of the kill queue, and drive a kill-survivor workflow. Use when the user asks to add mutation testing, check mutation score, investigate surviving mutants, or strengthen test quality beyond line coverage.
---

# Mutation Testing (pitest)

Mutation testing for Kotlin/Java Gradle projects using **pitest** via the `info.solidsoft.pitest` plugin. Non-intrusive: mutates bytecode, requires no production-code changes.

## When to use this skill

- User asks: "add mutation testing", "check mutation score", "why does this mutant survive", "strengthen tests", "is this class well-tested".
- A survivor appeared in a pitest report and needs killing.
- A project wants a CI gate on mutation score.

## Prerequisites

- Gradle project (Kotlin DSL `build.gradle.kts` primary, Groovy `build.gradle` supported via analogous blocks).
- Tests already exist. If not, run `/ralph-coverage` or `/kotest-create` first — mutation testing on an empty suite only produces `NO_COVERAGE` noise.
- Clean or near-clean working tree.

## Preflight — run before any pitest invocation

Pitest fails cryptically (silent `UNKNOWN_ERROR` from the coverage minion) when the project itself doesn't compile or when the test runtime has misaligned JUnit jars. **Always run these checks before `./gradlew pitest`** so failures surface with their real cause, not pitest's.

```bash
# 1. Test sources must compile — pitest can't help if the project itself is broken.
./gradlew compileTestKotlin compileTestJava --quiet

# 2. Find the project's actual junit-platform-launcher version.
./gradlew dependencyInsight --configuration testRuntimeClasspath \
  --dependency org.junit.platform:junit-platform-launcher 2>/dev/null \
  | head -1

# 3. Check that Kotlin bytecode keeps line-number debug info (pitest needs it).
grep -RnE 'Xno-source-debug-extension|-g:none' build.gradle.kts settings.gradle.kts 2>/dev/null
```

If step 1 fails, **abort and surface the compile error** — do not attempt pitest. If step 2 reports a version, use it to pick `junit5PluginVersion` (see next section). If step 3 finds either flag set, pitest will produce bogus line numbers or silently fail on mutators that need source info — remove the flag or exclude those modules.

## Capabilities

### 1. Bootstrap

Detect whether pitest is already configured:

```bash
grep -n "info.solidsoft.pitest" build.gradle.kts settings.gradle.kts **/build.gradle.kts 2>/dev/null
```

If not configured, propose this diff to the root `build.gradle.kts`:

```kotlin
plugins {
    id("info.solidsoft.pitest") version "1.19.0"
}

pitest {
    pitestVersion.set("1.19.0")
    targetClasses.set(setOf("<group.package>.*"))          // derive from rootProject.group
    targetTests.set(setOf("<group.package>.*"))
    mutators.set(setOf("STRONGER"))                        // do NOT use ALL — NPE- and equivalent-mutation-prone
    features.set(listOf(
        "+FLOGCALL",                                       // built-in: silence many logger-call mutations
        // `+fkotlin` is auto-enabled by the junit5 plugin when detected — filters Kotlin bytecode-junk mutations
    ))
    avoidCallsTo.set(setOf(
        // FLOGCALL and avoidCallsTo overlap partially but neither fully covers the other on real Kotlin+SLF4J code.
        // Verified empirically: removing these re-introduces 7+ logger-call survivors per scoped run.
        "kotlin.jvm.internal", "kotlin.Metadata",
        "org.slf4j.Logger",
        "org.apache.logging.log4j.Logger",
        "java.util.logging.Logger",
    ))
    excludedMethods.set(setOf(
        // Kotlin data-class synthesized members — generated, behavior guaranteed
        "component*", "copy", "hashCode", "equals", "toString",
    ))
    junit5PluginVersion.set("1.2.1")                       // JUnit 5 projects only — pin to project's Platform version
    outputFormats.set(setOf("HTML", "XML"))
    threads.set(Runtime.getRuntime().availableProcessors())
    timestampedReports.set(false)                          // stable path for parsing
    fullMutationMatrix.set(true)                           // names covering tests for SURVIVED mutants too — see §3
    exportLineCoverage.set(true)                           // emits coverage.xml alongside mutations.xml
    historyInputLocation.set(file("build/pitest/history.bin"))     // incremental analysis — read + write same file to skip re-running killed/survived mutants on unchanged classes
    historyOutputLocation.set(file("build/pitest/history.bin"))    // the gradle-pitest-plugin exposes explicit paths, not the `withHistory` CLI flag
    jvmArgs.set(listOf("-Xmx2g"))                          // avoid MEMORY_ERROR noise on forked minion; raise to 4g for large classpaths
    mutationThreshold.set(60)
    coverageThreshold.set(60)
    testStrengthThreshold.set(60)
}
```

Key points when proposing:
- **Derive `targetClasses`** from `rootProject.group` (e.g. `com.example.foo` → `"com.example.foo.*"`), show the detected value in the diff and ask for confirmation.
- **Omit `junit5PluginVersion`** for JUnit 4–only projects. Detect by searching for `junit-jupiter` in dependencies.
- **Pin `junit5PluginVersion` to the project's JUnit Platform line.** Pitest-junit5-plugin bundles its own `junit-platform-launcher`. If it targets a different Platform than the one in `testRuntimeClasspath`, the minion dies with `OutputDirectoryCreator not available` (a silent `UNKNOWN_ERROR` at the plugin level). Rough matrix (verify against the plugin's release notes before pinning):
  | Project `junit-platform-launcher` | Safe `junit5PluginVersion` |
  |---|---|
  | 1.8.x | `1.0.0` |
  | 1.9.x | `1.1.0` |
  | 1.10.x | `1.2.0` |
  | 1.11.x | `1.2.1` |
  | 1.12.x | `1.2.2` |
  Newer Platform / Jupiter (6.x / Platform 2.x) may require the `pitest` configuration to also pin a matching launcher explicitly:
  ```kotlin
  dependencies { pitest("org.junit.platform:junit-platform-launcher:<version>") }
  ```
- **Respect existing config** — if a `pitest { }` block already exists, only patch missing fields (e.g. add `XML` to `outputFormats` if only `HTML` is set). Never overwrite thresholds or `targetClasses`.
- **Groovy DSL** — emit the equivalent `pitest { ... }` using `=` assignment instead of `.set()`.
- **Forward `tasks.test` settings.** Pitest's minion **does not inherit** `jvmArgs`, `systemProperty(...)`, `systemProperties(...)`, `minHeapSize`, or `maxHeapSize` from `tasks.test`. Inspect the test task and mirror whatever it sets into `pitest { jvmArgs = [...] }` — system properties become `-D` entries, heap becomes `-Xmx`/`-Xms`. Missing this often manifests as the silent `UNKNOWN_ERROR` (e.g. JUnit can't instantiate a custom `@TestClassOrder` because the test task sets it via system property and the minion doesn't see it).
  ```kotlin
  // If tasks.test has:
  //   maxHeapSize = "4096m"
  //   systemProperty("junit.jupiter.testclass.order.default", "com.example.MyOrderer")
  //
  // Then pitest needs:
  pitest {
      jvmArgs.set(listOf(
          "-Xmx4g",
          "-Dkotlin.jupiter.testclass.order.default=com.example.MyOrderer",
      ))
  }
  ```
- **Turn on `verbose.set(true)` during bootstrap.** Silent minion crashes produce actionable output only when verbose is on. Can be switched off after the first clean run.

After applying the diff, run `./gradlew pitest` once to generate the baseline. **First-run failure modes and what they usually mean:**
| Symptom | Likely cause |
|---|---|
| `OutputDirectoryCreator not available ... unaligned versions of the junit-platform-engine and junit-platform-launcher` | `junit5PluginVersion` doesn't match the project's `junit-platform-launcher` — see matrix above |
| Silent `UNKNOWN_ERROR` with no stack | Enable `verbose.set(true)` and rerun — real cause will then surface in `PIT >> SEVERE : MINION` lines |
| `NoClassDefFoundError` / custom orderer / listener fails | `tasks.test` system property or jvmArg not forwarded to pitest |
| `Unresolved reference` in test sources | Pre-existing compile error — run the preflight `compileTestKotlin` check first |

### 2. Scoped run (on a change)

Derive target classes from `git diff`:

```bash
BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD main)
CHANGED=$(git diff --name-only "$BASE" HEAD -- '*.kt' '*.java' \
  | grep '^src/main/' \
  | sed -E 's#^src/main/(kotlin|java)/##; s#\.(kt|java)$##; s#/#.#g' \
  | paste -sd, -)

if [ -z "$CHANGED" ]; then
  echo "No production classes changed — aborting scoped run."
  exit 1
fi

./gradlew pitest \
  -Ppitest.targetClasses="$CHANGED" \
  -Ppitest.targetTests="$CHANGED"
```

Aborting on empty match is deliberate — **never silently fall back to whole-codebase** on a scoped run.

For Groovy-DSL projects, the command flags are identical.

For multi-module, prefix with the module path: `./gradlew :module-name:pitest -P...`.

### 3. Interpret survivors

Pitest writes `build/reports/pitest/mutations.xml` (stable path because `timestampedReports.set(false)`). Parse it:

```bash
# Quick survivor extraction
xmllint --xpath '//mutation[@status="SURVIVED"]' build/reports/pitest/mutations.xml 2>/dev/null
```

Each `<mutation>` element carries:
- `status` — `SURVIVED` / `KILLED` / `NO_COVERAGE` / `TIMED_OUT` / `MEMORY_ERROR` / `RUN_ERROR` / `NON_VIABLE`
- `<sourceFile>`, `<mutatedClass>`, `<mutatedMethod>`, `<lineNumber>`, `<mutator>`, `<description>`
- `<killingTest>` — present and populated only for KILLED mutants
- `numberOfTestsRun` (attribute) — how many tests reached this line

**Important:** with the default pitest configuration, SURVIVED mutants **do not list the names of the tests that reached them** — only a count via `numberOfTestsRun`. The killing-test field in the XML is empty for anything that survived. To identify *which* test to strengthen, the bootstrap sets `fullMutationMatrix.set(true)`, which adds a `<killingTests>` / `<succeedingTests>` matrix to each `<mutation>` element. Without this flag, the skill can only say "2 tests ran against this line and missed" — it cannot name them.

Side-effect: `fullMutationMatrix = true` increases report size and slightly increases runtime. Acceptable on scoped runs (one package / one class); consider turning off for whole-codebase CI runs where survivor diagnosis isn't the goal.

`exportLineCoverage.set(true)` emits a separate `coverage.xml` listing which tests reach each line. Combined with `mutations.xml`, you can reconstruct the covering-test set even without `fullMutationMatrix`, but it requires joining two files. Enabled by default in the bootstrap because it is cheap and useful for the aggregator.

Print a compact table:

```
STATUS       FILE:LINE              MUTATOR                   DESCRIPTION
SURVIVED     Calculator.kt:42       MATH                      replaced + with -
             covered by: CalculatorTest.`positive number is positive`
SURVIVED     Calculator.kt:43       CONDITIONALS_BOUNDARY     changed > to >=
             covered by: CalculatorTest.`zero is not positive`
NO_COVERAGE  PriceCalc.kt:88        VOID_METHOD_CALLS         removed call to log.debug
```

Distinguish `SURVIVED` (test exists but missed the behavior) from `NO_COVERAGE` (no test reaches the line) and `TIMED_OUT` (loop mutant caught by pitest's timeout heuristic — not a real survivor).

### 4. Triage — classify survivors before trying to kill them

**This step runs between interpretation and kill-a-survivor.** Its job: separate real test-quality gaps from *equivalent mutants* — mutations that change the bytecode but not the observable behavior in any test a human would reasonably write. Without triage, a kill-a-survivor loop wastes iterations (and, under unattended automation, produces tautological tests) trying to kill things that shouldn't be killed.

Classify each SURVIVED mutant into one of three buckets:

| Bucket | Meaning | Fed to kill-survivor / autoresearch? |
|---|---|---|
| `LIKELY_KILLABLE` | Behavioral change a sensible test could catch | Yes |
| `LIKELY_EQUIVALENT` | No realistic test can distinguish mutant from original | **No.** Written to `suspected-equivalent.md` for the record |
| `AMBIGUOUS` | Can't tell without reading more context | Surface for human decision; do not auto-feed to autoresearch |

Read the source line at `file:line` for each survivor and match against these archetypes (expand via the project overlay):

**Archetype A — logger-gate conditionals.** The line is an `if (<numeric> <comparator> <constant>) { ... }` whose body contains only calls to loggers (`logger.info`, `.warn`, `.error`, `.debug`, `.trace`) or trace/metric sinks. Any `ConditionalsBoundary` / `RemoveConditional_ORDER_*` / `RemoveConditional_EQUAL_*` survivor on such a line is `LIKELY_EQUIVALENT`.

```kotlin
if (deleted > 0) {          // <— mutations on `> 0` all survive
    logger.info("...")      //   because tests don't capture log output
}
```

**Archetype B — unreachable loop bounds.** The line is inside a `while` / `do..while` / `for` condition whose opposing operand is a constant larger than any realistic test input (threshold: default 1000; configurable via overlay). `ConditionalsBoundary` / `RemoveConditional_ORDER_*` survivors on such lines are `LIKELY_EQUIVALENT` — the mutation is theoretically killable but only with infeasible data volumes.

```kotlin
} while (batch.isNotEmpty() && batchCount < maxBatches)  // maxBatches = 10, batch = 10000 rows
```

**Archetype C — null-elvis on non-nullable-in-practice values.** The line is a `<value> ?: throw <X>` pattern where `<value>` is the non-nullable-by-contract result of a DB primary-key fetch, an `Optional.get()`, or similar. `RemoveConditional_EQUAL_IF` / `RemoveConditional_EQUAL_ELSE` survivors are `LIKELY_EQUIVALENT` — null is unreachable in any test a DB schema permits.

Kotlin-specific note: pitest's `NULL_RETURNS` mutator already skips `@NotNull`-annotated methods, and Kotlin compiles non-nullable return types to `@NotNull` in bytecode. So null-return mutants only surface on **nullable Kotlin returns** (`Foo?`) — archetype C is tuned to that reality and does not over-trigger on plain non-nullable returns.

```kotlin
eventCleanup.hardDeleteEvent(eventId ?: throw IllegalStateException("eventId is null"))
//                           ^-- eventId is jOOQ-fetched primary key, never null in practice
```

Anything that matches no archetype is `AMBIGUOUS` by default — **bias toward ambiguity, not toward equivalence**, so real gaps don't get silently excluded.

**Implementation.** A ready-to-use triage script lives at `scripts/triage.py` in this skill directory. Run:

```bash
python3 .claude/skills/mutation-testing/scripts/triage.py \
  build/reports/pitest/mutations.xml \
  .
```

It reads the mutations XML, opens each survivor's source line, applies archetypes A/B/C, and writes `triage.md` + `triage.json` next to the mutations file.

**Output:** write to `build/reports/pitest/triage.md` (or stdout) in this shape:

```markdown
# Triage of <N> survivors

## LIKELY_KILLABLE (<count>)
- UserCleanupService.kt:58 VoidMethodCall — removed call to deleteS3Files
  covering tests: UserCleanupServiceTest.`hardDeleteUser removes user and all owned data`
  archetype: none matched

## LIKELY_EQUIVALENT (<count>)
- AnonymousUserCleanupJob.kt:70 ConditionalsBoundary — changed > to >=
  archetype: A (logger-gate) — body is only `logger.info(...)`
- AnonymousUserCleanupJob.kt:68 ConditionalsBoundary — changed < to <=
  archetype: B (unreachable loop bound, maxBatches=10 × 10000-row limit)

## AMBIGUOUS (<count>)
- SomeClass.kt:42 MATH — replaced + with -
  covering tests: SomeClassTest.`...`
  reason: no archetype matched; needs human review
```

The `suspected-equivalent.md` set is **durable** — it accumulates across sessions, not per-run. A mutant that's triaged as equivalent once stays in that list unless the source line changes (detected by re-running triage when the line's content differs).

**Project overlay extensions.** `references/project.md` can add project-specific archetypes:
- Custom logger types beyond the stdlib set
- Known-non-null value types beyond DB primary keys (e.g. "values returned from `MyContext.requireUser()`")
- Loop-bound constants specific to the project
- Explicit allowlist of mutants always classified as equivalent (by file:line:mutator key)

**Do not skip triage before autoresearch.** The `mutation-autoresearch` skill requires a current triage output as its input — it only iterates `LIKELY_KILLABLE`. Running autoresearch on the raw survivor list would burn iterations on equivalents and produce tautological tests under pressure.

### 5. Kill a survivor

For each survivor, delegate to `/tdd-task` with a prompt like:

> Kill mutation: `<mutator>` at `<file>:<line>` in `<mutatedClass>.<mutatedMethod>`.
> Description: `<description>`.
> Currently covered by: `<coveringTests>`.
> Write a test that fails when the described mutation is applied to the original code, and passes otherwise. **Do not assert the raw mutated value or operator** — assert the observable behavior. Prefer strengthening assertions in the covering test; if that isn't natural, add a new sibling test case.

After `/tdd-task` returns, verify:

```bash
./gradlew pitest -Ppitest.targetClasses=<single-fqn> -Ppitest.targetTests=<single-fqn>
```

The target mutant should flip to `KILLED`, and no previously-killed mutant in the same class should regress. If both hold, delegate to `/commit`. If the new test asserts a tautology (literally references the mutated operator/constant), reject and retry with a stronger prompt.

### Fallbacks when dependencies aren't installed

- **No `/tdd-task`**: follow inline TDD — (1) write a failing test that targets the behavior, (2) run `/test-gradle --tests <pattern>` or `./gradlew test --tests ...` to confirm red, (3) the test should already pass against unmutated code, so run once more and confirm green, (4) run scoped pitest to confirm the mutant died.
- **No `/commit`**: `git add src/test && git commit -m "test(mutation): kill <mutator> at <file>:<line>"`.
- **No `/test-gradle`**: `./gradlew test --tests <fully-qualified-test-pattern>`.

## Kotlin-specific gotchas

| Gotcha | Mitigation |
|---|---|
| `kotlin.jvm.internal` null-check noise | `avoidCallsTo.set(setOf("kotlin.jvm.internal", "kotlin.Metadata"))` (already in bootstrap) |
| Logger call survivors (`org.slf4j.Logger::info/debug/warn`) | Already in bootstrap via `avoidCallsTo`. These are noise unless logging itself is the feature under test |
| Data class `component*` / `copy` / `equals` / `hashCode` / `toString` mutants | Already in bootstrap via `excludedMethods`. Generated methods, semantics guaranteed by Kotlin |
| Inline classes / value classes | Add to `excludedClasses`; test against the underlying type |
| Extension functions (compile to `FileNameKt`) | Ensure `targetClasses` glob covers the file-level class (e.g. `com.example.UtilsKt`) |
| Coroutines state-machine bytecode | Noisy generated-bridge mutants. If survivors are all synthetic, narrow `mutators` to `DEFAULTS` for coroutine-heavy modules |
| Generated code (ksp, jOOQ, Dagger) | Exclude via `excludedClasses.set(setOf("com.example.generated.*"))` |
| Mixed JUnit 4 + JUnit 5 | Set `junit5PluginVersion` **and** verify `junit-vintage-engine` is on the test classpath |
| IntelliJ Gradle DSL warnings | Prefer `.set(...)` over direct `=` assignment to silence lazy-property warnings |
| History cache poisoning (incremental analysis) | `withHistory = true` reads `java.io.tmpdir`; bust it after dependency bumps, kapt/ksp config changes, Spring AOT changes, and across branches. In CI, key history per-branch (e.g. archive `build/pitest/history.bin` with the branch name) — **dependency changes are invisible to pitest's dep graph, so a stale cache silently reports wrong results**. |
| Pitest mutator groups | Default is `STRONGER`. **Do not use `ALL`** — includes `CONSTRUCTOR_CALLS`, `NON_VOID_METHOD_CALLS`, UOI, ROR, AOR/AOD, CRCR; docs flag them as "fairly unstable" and equivalent-prone, producing false survivor noise |
| `+FLOGCALL` feature | Built into pitest via the feature language. Already in the bootstrap block. If the project uses a custom logger type not auto-detected by FLOGCALL, supplement via `avoidCallsTo` |

## Status-symbol legend for summaries

| Symbol | Status |
|---|---|
| ✓ | KILLED |
| ✗ | SURVIVED |
| ○ | NO_COVERAGE |
| ⏱ | TIMED_OUT |
| ⚠ | MEMORY_ERROR / RUN_ERROR / NON_VIABLE |

## What this skill does NOT do (v0.1.0)

- Does not modify production code. Survivors that indicate a real bug are surfaced for manual decision; route through `/fix` explicitly.
- Does not run unattended overnight — that's the `mutation-autoresearch` skill.
- Does not auto-ratchet thresholds. Ratcheting is a separate capability; this skill only advises on values.
- Does not patch CI. CI wiring is documented but not automated in v0.1.0.
- Does not handle Maven. Pitest has a Maven plugin; this skill is Gradle-only.

## Project overlay

Read `references/project.md` in this skill's directory if it exists. The overlay provides:
- Project-specific `targetClasses` / `excludedClasses` patterns
- Base test classes and when to use each
- Known-equivalent mutants to skip
- Preferred commit-message style
