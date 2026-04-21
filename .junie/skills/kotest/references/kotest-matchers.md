# Kotest matcher reference

Shared between `kotest-migrate` and `kotest-create`. Keep in sync if edited.

Kotest is the default assertion style for both skills. Prefer matcher infix form
(`actual shouldBe expected`) over boolean wrappers (`assertTrue(x == y)`).

## Scalar and null checks

| Intent                | Kotest                              |
|-----------------------|-------------------------------------|
| Equality              | `actual shouldBe expected`          |
| Inequality            | `actual shouldNotBe other`          |
| Null                  | `value shouldBe null`               |
| Non-null              | `value.shouldNotBeNull()`           |
| Boolean true/false    | `flag shouldBe true` / `false`      |

`shouldNotBeNull()` smart-casts to the non-null type, so a chained access works
without `!!`.

## Collection checks

| Intent                        | Kotest                                         |
|-------------------------------|------------------------------------------------|
| Size                          | `items shouldHaveSize n`                       |
| Empty                         | `items.shouldBeEmpty()`                        |
| Exact elements, ordered       | `items shouldContainInOrder listOf(...)`       |
| Exact elements, any order     | `items shouldContainAllInAnyOrder listOf(...)` |
| Contains one element          | `items shouldContain element`                  |

Order sensitivity is load-bearing — `containsExactly` is ordered,
`containsExactlyInAnyOrder` is not. Do not collapse these.

## Field projection on collections

Prefer `map { }` + collection matcher over AssertJ-style `extracting` chains.

```kotlin
talks.map { it.title } shouldContainAllInAnyOrder listOf("a", "b")
```

## String checks

| Intent                    | Kotest                                  |
|---------------------------|-----------------------------------------|
| Contains substring        | `text shouldContain "x"`                |
| Contains in order         | `text shouldContainInOrder listOf(...)` |
| Starts / ends with        | `text shouldStartWith "x"`              |

Note: `shouldContainInOrder` works on both `String` and `Collection`.

## Exception checks

```kotlin
shouldThrow<IllegalArgumentException> {
    service.create(invalid)
}.message.shouldContain("invalid")
```

- `shouldThrow<T>` returns the caught exception; chain `.message`, `.cause`, etc.
- Use `shouldThrowExactly<T>` when subtype must not match.

## Grouping assertions on one object

Prefer `apply { ... }` to assert multiple fields on one receiver without
repeating the variable name:

```kotlin
result.apply {
    id.shouldNotBeNull()
    name shouldBe "Ada"
    tags shouldHaveSize 2
}
```

Wrap in `assertSoftly { ... }` when you want every failure reported, not just
the first:

```kotlin
assertSoftly {
    result.apply {
        id.shouldNotBeNull()
        name shouldBe "Ada"
    }
    otherResult shouldBe expected
}
```

## AssertJ → Kotest (migration only)

| AssertJ                                                      | Kotest                                          |
|--------------------------------------------------------------|-------------------------------------------------|
| `assertThat(x).isEqualTo(y)`                                 | `x shouldBe y`                                  |
| `assertThat(x).isNotEqualTo(y)`                              | `x shouldNotBe y`                               |
| `assertThat(x).isNull()`                                     | `x shouldBe null`                               |
| `assertThat(x).isNotNull()`                                  | `x.shouldNotBeNull()`                           |
| `assertThat(flag).isTrue()`                                  | `flag shouldBe true`                            |
| `assertThat(list).hasSize(n)`                                | `list shouldHaveSize n`                         |
| `assertThat(list).containsExactly(a, b)`                     | `list shouldContainInOrder listOf(a, b)`        |
| `assertThat(list).containsExactlyInAnyOrder(a, b)`           | `list shouldContainAllInAnyOrder listOf(a, b)`  |
| `assertThat(items).extracting("name").containsExactly(...)`  | `items.map { it.name } shouldContainInOrder ...`|
| `assertThatThrownBy { ... }.isInstanceOf(X::class.java)`     | `shouldThrow<X> { ... }`                        |
| `...hasMessageContaining("x")`                               | `...message.shouldContain("x")`                 |

## JUnit assertions → Kotest (migration only)

| JUnit                                       | Kotest                                 |
|---------------------------------------------|----------------------------------------|
| `assertEquals(expected, actual)`            | `actual shouldBe expected`             |
| `assertNotNull(v)`                          | `v.shouldNotBeNull()`                  |
| `assertNull(v)`                             | `v.shouldBeNull()`                     |
| `assertEquals(n, list.size)`                | `list shouldHaveSize n`                |
| `assertTrue("x" in msg)`                    | `msg shouldContain "x"`                |
| `assertTrue(cond)` / `assertFalse(cond)`    | pick a specific matcher for the value  |
| `assertThrows<X> { ... }`                   | `shouldThrow<X> { ... }`               |

Do not keep generic `assertTrue(cond)` — always replace with a matcher that
describes what is being checked.

## Imports

Common Kotest imports used by these patterns:

```kotlin
import io.kotest.assertions.assertSoftly
import io.kotest.assertions.throwables.shouldThrow
import io.kotest.matchers.collections.shouldContainAllInAnyOrder
import io.kotest.matchers.collections.shouldContainInOrder
import io.kotest.matchers.collections.shouldHaveSize
import io.kotest.matchers.nulls.shouldNotBeNull
import io.kotest.matchers.shouldBe
import io.kotest.matchers.shouldNotBe
import io.kotest.matchers.string.shouldContain
import io.kotest.matchers.string.shouldContainInOrder
```

Remove AssertJ and `org.junit.jupiter.api.Assertions` imports when migrating.

## Anti-patterns

- Restating assertions already covered by full-object equality. If
  `result shouldBe expected` passes, do not then assert each field again.
- Long AssertJ-style chains translated literally into Kotest — prefer explicit
  property checks over multi-line fluent reconstructions.
- Dense one-liners that hide failure diagnostics. Readability > brevity.
