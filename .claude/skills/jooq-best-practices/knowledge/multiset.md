# MULTISET & Nested Collections

## Pattern: Use MULTISET for nested collections instead of N+1
**Source**: [jOOQ Official Docs — MULTISET value constructor](https://www.jooq.org/doc/3.20/manual/sql-building/column-expressions/multiset-value-constructor/) (docs)
**Since**: jOOQ 3.15

Collect correlated subquery results into nested collections in a single query. Replaces N+1 patterns.

```kotlin
dsl.select(
    AUTHOR.FIRST_NAME,
    AUTHOR.LAST_NAME,
    multiset(
        selectDistinct(BOOK.TITLE, BOOK.PUBLISHED_IN)
            .from(BOOK)
            .where(BOOK.AUTHOR_ID.eq(AUTHOR.ID))
    ).`as`("books")
).from(AUTHOR)
    .fetch()
```

Most databases emulate MULTISET via JSON/JSONB serialization under the hood.

---

## Pattern: MULTISET uses JSON arrays (not objects) internally
**Source**: [Consider using JSON arrays instead of JSON objects for serialisation](https://blog.jooq.org/consider-using-json-arrays-instead-of-json-objects-for-serialisation) (2025-08-11)

jOOQ serializes MULTISET results as arrays of arrays, not arrays of objects. Since jOOQ controls the SQL and knows column positions, it uses positional access rather than name-based lookup.

**Benefits**:
- ~80% faster for large result sets (10k rows: 2932 vs 1643 ops/s in benchmarks)
- Avoids duplicate column name conflicts (e.g., two tables both having `ID`) — JSON objects can't have duplicate keys, arrays can
- Smaller payload: no repeated key names

**Implication**: Don't try to manually parse jOOQ's internal JSON serialization — use the type-safe MULTISET API and let jOOQ handle deserialization.

---

## Pattern: Type-safe DTO projection with MULTISET + mapping()
**Source**: [The Second Best Way to Fetch a Spring Data JPA DTO Projection](https://blog.jooq.org/the-second-best-way-to-fetch-a-spring-data-jpa-dto-projection) (2022-08-30)
**Since**: jOOQ 3.15

Use `convertFrom` with `mapping()` to map MULTISET results directly into nested DTOs/records with compile-time type safety. The constructor reference defines the mapping — change the schema, regenerate code, and mismatches become compile errors.

```java
record PostCommentDTO(Long id, String review) {}
record PostDTO(Long id, String title, List<PostCommentDTO> comments) {}

List<PostDTO> result = ctx.select(
        POST.ID,
        POST.TITLE,
        multiset(
            select(POST_COMMENT.ID, POST_COMMENT.REVIEW)
            .from(POST_COMMENT)
            .where(POST_COMMENT.POST_ID.eq(POST.ID))
        ).convertFrom(r -> r.map(mapping(PostCommentDTO::new)))
    )
    .from(POST)
    .where(POST.TITLE.like(postTitle))
    .fetch(mapping(PostDTO::new));
```

---

## Pattern: MULTISET_AGG for flat-to-nested without correlated subquery
**Source**: [The Second Best Way to Fetch a Spring Data JPA DTO Projection](https://blog.jooq.org/the-second-best-way-to-fetch-a-spring-data-jpa-dto-projection) (2022-08-30)
**Since**: jOOQ 3.15

`multisetAgg()` aggregates columns from a joined table into a nested collection, avoiding the correlated subquery of `multiset()`. Combine with implicit joins for concise syntax.

```java
List<PostDTO> result = ctx.select(
        POST_COMMENT.post().ID,
        POST_COMMENT.post().TITLE,
        multisetAgg(POST_COMMENT.ID, POST_COMMENT.REVIEW)
            .convertFrom(r -> r.map(mapping(PostCommentDTO::new)))
    )
    .from(POST_COMMENT)
    .where(POST_COMMENT.post().TITLE.like(postTitle))
    .groupBy(POST_COMMENT.post().ID, POST_COMMENT.post().TITLE)
    .fetch(mapping(PostDTO::new));
```

---

## Pattern: Filter by nested collection contents using HAVING + boolOr
**Source**: [How to Filter a SQL Nested Collection by a Value](https://blog.jooq.org/how-to-filter-a-sql-nested-collection-by-a-value) (2022-06-10)

When using `multisetAgg()`, you can't filter in `WHERE` because the collection isn't formed yet. Instead, use `HAVING` with `boolOr().filterWhere()` to keep only groups where the nested collection contains a specific value.

```java
ctx.select(
        FILM_ACTOR.film().TITLE,
        multisetAgg(
            FILM_ACTOR.actor().ACTOR_ID,
            FILM_ACTOR.actor().FIRST_NAME,
            FILM_ACTOR.actor().LAST_NAME))
    .from(FILM_ACTOR)
    .groupBy(FILM_ACTOR.film().TITLE)
    .having(boolOr(trueCondition())
        .filterWhere(FILM_ACTOR.actor().ACTOR_ID.eq(1)))
    .orderBy(FILM_ACTOR.film().TITLE)
    .fetch();
```

The SQL `HAVING bool_or(TRUE) FILTER (WHERE condition)` checks if any row in the group matches. This can be simplified to `HAVING bool_or(condition)`.

---

## Pattern: Configure MULTISET emulation
**Source**: [jOOQ Official Docs — MULTISET value constructor](https://www.jooq.org/doc/3.20/manual/sql-building/column-expressions/multiset-value-constructor/) (docs)
**Since**: jOOQ 3.15

The `Settings.emulateMultiset` option controls serialization format: `DEFAULT`, `JSON`, `JSONB`, `XML`, or `NATIVE`. For PostgreSQL, `JSONB` is a good choice.

---
