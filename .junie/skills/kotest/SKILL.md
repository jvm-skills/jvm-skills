---
name: kotest
description: Write a new Kotlin test, or modernize an existing one, using Kotest matchers and idiomatic Kotlin test style — backticked names, apply/assertSoftly blocks, and existing object mothers and helpers. Use when adding a test for behavior that does not yet have one, or when improving a Kotlin test that still uses JUnit assertions or AssertJ chains. Assumes project test infrastructure exists; flag missing factories or helpers rather than building them here.
---

# Kotest

Produce one high-quality Kotlin test in idiomatic style with Kotest matchers.

Two tracks, one skill:

- **Create** — write a new test for described behavior.
- **Modernize** — rewrite an existing Kotlin test to Kotest + idiomatic style.

Pick the track at step 1 based on inputs. The rest of the skill is the same
knowledge applied to either starting point.

## Non-negotiables

- Do not build broad new test infrastructure inside this skill. If a needed
  factory / helper / DSL is missing, add a minimal inline fallback and tell
  the user that extraction may be warranted separately.
- Do not change production code to make a test easier, unless the user asks.
- **Modernize track only**: preserve assertion semantics exactly. Order
  sensitivity, nullability, and exception types must not change.
- Follow project overlay (`references/project.md`) if present — it overrides
  shared defaults. The overlay is where framework-specific context lives
  (base classes, test annotations, single-test command, factory locations).

## Step 1 — Pick the track

- **Modernize** if a specific Kotlin test file/class was named, or the user
  said "improve / rewrite / migrate / modernize this test".
- **Create** if the user described a behavior to cover, or pointed at
  production code without an existing test.

If input is a Java test file, this skill does not port it. Suggest the user
either (a) describe the behavior so we run the Create track, or (b) manually
stage a skeleton Kotlin test for us to run the Modernize track on.

Once the track is picked, follow the corresponding procedure below.

---

## Create track

### 1. Understand the behavior

Read the production code the test will exercise:

- The class/method under test and its collaborators.
- Any validation, exception branches, or ordering guarantees that shape
  assertions.
- Existing tests nearby — use them as style reference and to avoid
  duplicating coverage.

If the behavior is ambiguous, ask the user before writing the test.

### 2. Scan for reusable infrastructure

Before writing, search for what to reuse:

- Object-mother / factory functions (typically `*ObjectMother.kt`, `TestData.kt`).
- Kotlin extensions on domain types (`toDto()`, `Iterable<T>.names()`).
- Test helpers for setup/teardown or I/O wiring.
- DSLs for object-graph assembly.
- Project base classes for tests (see `references/project.md` overlay).

If required infra is missing, add a minimal inline fallback or stop and flag
it to the user. Do not quietly grow shared infra here.

### 3. Write the class header

- Pick the test base class or annotations indicated by the project overlay.
  If there is no overlay, use a plain class with collaborators wired via
  constructor parameters.
- Follow `references/idiomatic-patterns.md` for collaborator wiring and
  naming.

### 4. Write each test method

For each scenario:

1. **Name** — backticked sentence: `` `should reject duplicate tag names`() ``.
2. **Arrange** — call existing factories; pass only arguments that matter.
3. **Act** — invoke the behavior.
4. **Assert** — Kotest matchers (`references/kotest-matchers.md`).

Assertion style:

- Scalar: `actual shouldBe expected`.
- Non-null: `value.shouldNotBeNull()` (smart-casts).
- Collection sizing: `list shouldHaveSize n`.
- Ordered: `list shouldContainInOrder listOf(...)`.
- Any-order: `list shouldContainAllInAnyOrder listOf(...)`.
- Field projection: `items.map { it.name } shouldContainInOrder listOf(...)`.
- Exceptions: `shouldThrow<X> { ... }.message.shouldContain("...")`.
- Multiple fields on one object: `result.apply { ... }`.
- Several related checks reporting together: `assertSoftly { ... }`.

Each assertion must add independent semantic coverage. Do not restate fields
already proven by a full-object equality. Do not wrap conditions in
`assertTrue` — use a matcher that describes what the condition means.

### 5. Run the focused test

Use the single-test command defined in the project overlay. If none is
specified, the project's usual test runner with a class-name filter is the
right default.

If it fails: first confirm the assertion is correct for the behavior. A green
test with the wrong assertion is worse than a red one. If production code is
wrong, flag to the user — do not weaken the test.

### 6. Report

- New file path.
- Which existing infrastructure was reused.
- Any inline fallbacks added (and whether shared extraction is warranted).
- Scenarios covered / intentionally out of scope.
- Exact verification command.

---

## Modernize track

### 1. Read the source test

Record the existing:

- Test framework hooks and annotations — preserve them verbatim.
- Collaborator wiring style (fields vs constructor).
- Any setup/teardown behavior.

These must not drift during modernization. Changing them silently is a bug.

### 2. Scan for reusable infrastructure

Same scan as the Create track. Existing factories / extensions / helpers are
almost always underused in pre-Kotest tests — swap them in during this pass.

### 3. Modernize structure first, style second

Work in this order — the class must compile between each step:

1. Switch mutable collaborator fields to constructor parameters where the
   test framework allows it. Keep `lateinit var` for fields that a framework
   mechanism requires (consult project overlay).
2. Rename camelCase test methods to backticked sentences, preserving intent:
   `shouldCreateTalk` → `` `should create talk` ``.
3. Leave assertions untouched for now. Only after compilation is clean, move
   on to the assertion rewrite.

### 4. Rewrite assertions to Kotest matchers

Apply the rewrite tables in `references/kotest-matchers.md`. Key rules:

- `assertEquals(expected, actual)` → `actual shouldBe expected`
- `assertNotNull(v)` → `v.shouldNotBeNull()`
- `assertNull(v)` → `v.shouldBeNull()`
- `assertEquals(n, list.size)` → `list shouldHaveSize n`
- `assertTrue("x" in msg)` → `msg shouldContain "x"`
- `assertThrows<X> { ... }` → `shouldThrow<X> { ... }`
- `assertThat(x).isNotNull()` → `x.shouldNotBeNull()`
- `assertThat(list).containsExactly(...)` → `list shouldContainInOrder listOf(...)`
- `assertThat(list).containsExactlyInAnyOrder(...)` → `list shouldContainAllInAnyOrder listOf(...)`
- `assertThat(items).extracting("name")...` → `items.map { it.name } shouldContain...`
- `assertThatThrownBy { ... }.isInstanceOf(X::class.java).hasMessageContaining("y")`
  → `shouldThrow<X> { ... }.message.shouldContain("y")`

Do not translate long AssertJ chains 1:1. Prefer explicit property assertions
with `apply { }`.

### 5. Apply idiomatic blocks

For multiple field checks on one result, group with `result.apply { ... }`
(`references/idiomatic-patterns.md`). Wrap in `assertSoftly { ... }` when
all failures should be reported together. Don't wrap sequential dependent
assertions in `assertSoftly` — earlier failures should stop the test there.

### 6. Simplify factory calls

Revisit DTO/entity construction:

- Prefer zero-arg when defaults suffice: `createSpeakerRequest()`.
- Pass only assertion-relevant or uniqueness-critical arguments.
- Do not restate default values just because the pre-modernization test
  spelled them out.

If the test hand-constructs objects and no factory exists, leave the
construction inline. Do not create factories inside this skill — flag it to
the user as a follow-up.

### 7. Remove redundant assertions

If a full-object equality already proves a field, drop the per-field check.
Keep only assertions that add independent semantic coverage (ordering,
exception details, nullability, values not otherwise covered).

### 8. Clean up imports

Remove:

- `org.assertj.core.api.Assertions.*`
- `org.junit.jupiter.api.Assertions.*`
- Helpers that are no longer referenced.

Add the Kotest imports listed in `references/kotest-matchers.md`.

### 9. Run the focused test

Use the single-test command defined in the project overlay.

Iterate until green. Common causes of failure:

- Order-sensitive matcher where an any-order matcher was needed, or vice versa.
- Nullability mismatch between original Java-sourced types and Kotlin
  non-null types.
- Missing Kotest matcher import.
- Backticked name not escaped properly.

### 10. Report

- File modernized.
- Track taken (Modernize).
- What changed at the structure level (wiring, naming).
- Which existing infrastructure was newly adopted.
- Semantics-sensitive decisions (ordering / exceptions / nullability).
- Exact verification command.

---

## Common pitfalls (both tracks)

- **Hand-building DTOs when a factory exists**: scan for `create*Request`,
  `*Dto.toEntity()`, etc. before constructing manually.
- **Restating factory defaults**: if the factory defaults
  `email = "ada@example.com"`, do not re-pass it named-argument-style.
- **`assertTrue(cond)` wrappers**: always replace with a specific matcher.
- **Assertion inflation**: adding field-level checks that duplicate what a
  full-object equality already proves.
- **Wrong `assertSoftly` scope**: it is for "report all related failures
  together", not for sequential dependent assertions.
- **Coroutine tests without `runTest`**: suspend functions must run inside
  `runTest { ... }` (or the project's test-dispatcher wrapper).
- **Silently dropping framework hooks** (Modernize track): setup/teardown
  annotations, transaction boundaries, and active profiles must carry over
  verbatim. Dropping them can cause intermittent pollution that only fails
  under certain run orders.

## Project overlay

If `references/project.md` exists in this skill's directory after install, it
overrides the shared defaults. This is where framework-specific context
belongs (e.g. Spring Boot test types, base classes, single-test command,
mocking library, factory locations). The skill itself stays framework-neutral.
