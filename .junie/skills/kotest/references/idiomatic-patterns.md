# Idiomatic Kotlin test patterns

Shared between `kotest-migrate` and `kotest-create`. Keep in sync if edited.

These are the house style conventions both skills produce. If a project overlay
(`references/project.md`) contradicts anything here, the overlay wins.

## Test names

Write test names as human sentences inside backticks, not camelCase.

```kotlin
// Java
void shouldCreateTalkAndSpeakerCorrectly() { ... }

// Kotlin
@Test
fun `should create talk and speaker correctly`() { ... }
```

Use real spaces. Preserve the intent of the Java name — do not paraphrase
behavior differently.

## Collaborator wiring

Prefer constructor parameters over mutable fields for the class under test
and its collaborators:

```kotlin
class TagServiceTest {
    private val tagRepository = mockk<TagRepository>()
    private val tagService = TagService(tagRepository)

    // tests
}
```

Use `lateinit var` only where a framework requires it (e.g. DI container
field injection that has no constructor hook).

## Multiple assertions on one object

Use `apply { ... }` to assert several fields on the same receiver without
repeating its name:

```kotlin
result.apply {
    id.shouldNotBeNull()
    name shouldBe "Ada"
    tags shouldHaveSize 2
}
```

Wrap in `assertSoftly { ... }` when the test should report every failing
assertion in one run, not stop at the first:

```kotlin
assertSoftly {
    result.apply {
        id.shouldNotBeNull()
        name shouldBe "Ada"
    }
    savedCount shouldBe 1
}
```

Rule of thumb: use `assertSoftly` when several related checks together describe
one conclusion; skip it when assertions are sequential and later ones depend on
earlier ones holding.

## Object mothers and test factories

Check for existing factory functions before constructing DTOs/entities by hand.
They usually live in test-scope files like `ObjectMother.kt`, `TestData.kt`,
or next to the test package.

Default-value shorthand when calling factories:

- Call with zero args when defaults suffice: `createSpeakerRequest()`.
- Pass only assertion-relevant or uniqueness-relevant arguments: `createSpeakerRequest(name = "Ada")`.
- Do not restate arguments that match the factory's default — it's noise.

```kotlin
// Avoid: restates defaults
val req = createSpeakerRequest(
    name = "Ada",
    email = "ada@example.com",
    company = "Analytical Engines",
)

// Prefer: override only what matters
val req = createSpeakerRequest(name = "Ada")
```

If no factory exists and the same construction repeats 3+ times, that's a
signal to extract one — but do not speculatively build factories for a single
test.

## Reusing extension functions and test helpers

Prefer existing Kotlin extensions over inline duplication. Typical candidates:

- `toDto()` / `toEntity()` conversions on domain types
- MockMvc helpers for headers / JSON body / typed response parsing
- Transactional / cleanup wrappers (`withNewTransaction { ... }`, `testDataScope { ... }`)
- Projection helpers (`Iterable<TagDto>.names()`)

When both an extension and a static helper do the same thing, use the form
nearby Kotlin tests already use.

## Collection projections before matching

When asserting a field across a collection, project first with `map`, then
match — do not reach for AssertJ-style `extracting`:

```kotlin
tags.map { it.name } shouldContainAllInAnyOrder listOf("java", "kotlin")
```

## Coroutines

For suspending code, use `runTest { ... }` from `kotlinx-coroutines-test` and
call suspend functions directly inside the block. Virtual time advances
through `advanceUntilIdle()`, `advanceTimeBy(...)`.

## Data-class DTOs and `@JvmRecord`

When porting or creating Kotlin DTOs that Java code must consume, use
`data class` with `@JvmRecord`. Keep primary-constructor properties as `val`,
preserve validation annotations with `@field:`, and only add defaults where
the domain treats the field as optional (`emptyList()` for collections, `null`
for nullables). Never invent defaults like `""`, `"N/A"`, or `0`.

## Anti-patterns

- `lateinit var` fields when constructor parameters would work.
- camelCase test names when backticked sentences are supported.
- Re-asserting fields already proven by a full-object equality check.
- Hand-constructing DTOs when a factory exists nearby.
- Dense matcher one-liners that hide which field failed.
