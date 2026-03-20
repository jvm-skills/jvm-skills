# Fetching & Result Mapping

## Pattern: Use RecordMapper for custom projections
**Source**: [jOOQ Official Docs — Fetching](https://www.jooq.org/doc/3.20/manual/sql-execution/fetching/) (docs)

Use lambda-based RecordMapper for transforming query results to domain objects.

```kotlin
data class AuthorDto(val name: String, val bookCount: Int)

val authors = dsl.select(AUTHOR.FIRST_NAME, count())
    .from(AUTHOR)
    .join(BOOK).on(BOOK.AUTHOR_ID.eq(AUTHOR.ID))
    .groupBy(AUTHOR.FIRST_NAME)
    .fetch { record -> AuthorDto(record[AUTHOR.FIRST_NAME]!!, record[count()]) }
```

---

## Pattern: fetchMap / fetchGroups for indexed results
**Source**: [jOOQ Official Docs — Fetching](https://www.jooq.org/doc/3.20/manual/sql-execution/fetching/) (docs)

Use `fetchMap()` for unique key lookups and `fetchGroups()` for one-to-many.

```kotlin
// Key → single record
val bookById: Map<Long, BookRecord> = dsl.selectFrom(BOOK).fetchMap(BOOK.ID)

// Key → list of records
val booksByAuthor: Map<Long, List<BookRecord>> = dsl.selectFrom(BOOK).fetchGroups(BOOK.AUTHOR_ID)
```

---

## Pattern: Ad-hoc converters for field-level transformation
**Source**: [jOOQ Official Docs — Ad-hoc Converter](https://www.jooq.org/doc/3.20/manual/sql-execution/fetching/) (docs)
**Since**: jOOQ 3.15

Convert individual fields inline without a global converter.

```kotlin
dsl.select(BOOK.TITLE, BOOK.PUBLISHED_IN.convertFrom { Year.of(it) })
    .from(BOOK)
    .fetch()
```

---

## Pattern: Directional ad-hoc converters — convertFrom / convertTo / convert
**Source**: [Ad-hoc Data Type Conversion with jOOQ 3.15](https://blog.jooq.org/ad-hoc-data-type-conversion-with-jooq-3-15) (2021-07-20)
**Since**: jOOQ 3.15

Choose the right direction when you don't need a full code-generation `Converter`:

- **`convertFrom`** — read-only, for SELECT projections
- **`convertTo`** — write-only, for DML values and WHERE predicates
- **`convert`** — bidirectional, when the field appears in both directions

Ideal for dynamic schemas where code generation configuration isn't available.

```kotlin
val height: Field<BigDecimal> = field(name("furniture", "height"), NUMERIC)

// SELECT — transform DB value to domain type
val result = ctx.select(height.convertFrom(::Dimension)).from(furniture).fetch()

// INSERT — convert domain type back to DB type
ctx.insertInto(furniture)
    .columns(height.convertTo(Dimension::value))
    .values(Dimension(BigDecimal.ONE))
    .execute()

// Bidirectional — field used in both SELECT and WHERE
val dimField = height.convert(Dimension.class, ::Dimension, Dimension::value)
```

---

## Pattern: Choose the right fetch method for your use case
**Source**: [The Many Different Ways to Fetch Data in jOOQ](https://blog.jooq.org/the-many-different-ways-to-fetch-data-in-jooq) (2022-05-19)

| Method | When to use |
|--------|-------------|
| `fetch()` | Default — loads all rows into memory, closes JDBC resources immediately |
| `fetchLazy()` | Large result sets — returns a `Cursor<R>` wrapping the JDBC ResultSet (must close via try-with-resources) |
| `fetchStream()` | Like `fetchLazy()` but returns a `Stream<R>` (must close via try-with-resources) |
| `collect(collector)` | Transform results directly with a JDK `Collector` — no intermediate `Result` object |
| `fetch().stream()` | Eager fetch + stream — safe (no resource leak) but materializes all rows first |

```kotlin
// Lazy cursor for large result sets
dsl.selectFrom(BOOK).fetchLazy().use { cursor ->
    for (record in cursor) { /* process one at a time */ }
}

// Stream with resource management
dsl.selectFrom(BOOK).fetchStream().use { stream ->
    stream.forEach { /* process */ }
}

// Direct collect — no intermediate Result
val bookMap: Map<Int, String> = dsl.select(BOOK.ID, BOOK.TITLE)
    .from(BOOK)
    .collect(Records.intoMap())
```

---

## Pattern: Single-record fetch methods — fetchOne vs fetchOptional vs fetchSingle
**Source**: [The Many Different Ways to Fetch Data in jOOQ](https://blog.jooq.org/the-many-different-ways-to-fetch-data-in-jooq) (2022-05-19)

| Method | Returns | 0 rows | 2+ rows |
|--------|---------|--------|---------|
| `fetchOne()` | `R?` (nullable) | `null` | throws `TooManyRowsException` |
| `fetchOptional()` | `Optional<R>` | `Optional.empty()` | throws `TooManyRowsException` |
| `fetchSingle()` | `R` (non-null) | throws `NoDataFoundException` | throws `TooManyRowsException` |

Use `fetchSingle()` when exactly one row is expected (e.g., lookup by PK). Use `fetchOptional()` for nullable lookups. Avoid `fetchOne()` in Kotlin — prefer `fetchOptional()` or `fetchSingle()` for clearer intent.

---

## Pattern: Reactive streams from ResultQuery
**Source**: [The Many Different Ways to Fetch Data in jOOQ](https://blog.jooq.org/the-many-different-ways-to-fetch-data-in-jooq) (2022-05-19)
**Since**: jOOQ 3.15

`ResultQuery<R>` implements `Publisher<R>`, so any jOOQ query can be wrapped directly by Project Reactor or RxJava:

```kotlin
val flux: Flux<Record1<String>> = Flux.from(
    dsl.select(BOOK.TITLE).from(BOOK)
)
```

---

## Pattern: Project table references as nested TableRecords
**Source**: [Projecting Type Safe Nested TableRecords with jOOQ 3.17](https://blog.jooq.org/projecting-type-safe-nested-tablerecords-with-jooq-3-17) (2022-02-21)
**Since**: jOOQ 3.17

Project entire table expressions directly in SELECT — `Table<R>` implements `SelectField<R>`. Results are fully typed `Record2<ActorRecord, CategoryRecord>` with getter/setter access.

```java
Result<Record2<ActorRecord, CategoryRecord>> result =
ctx.selectDistinct(ACTOR, CATEGORY)
   .from(ACTOR)
   .join(FILM_ACTOR).using(FILM_ACTOR.ACTOR_ID)
   .join(FILM_CATEGORY).using(FILM_CATEGORY.FILM_ID)
   .join(CATEGORY).using(CATEGORY.CATEGORY_ID)
   .fetch();
```

For granular control (project only specific columns as a nested record), use ad-hoc `row()` expressions:

```java
Result<Record2<Record3<Long, String, String>, Record2<Long, String>>> result =
ctx.selectDistinct(
       row(ACTOR.ACTOR_ID, ACTOR.FIRST_NAME, ACTOR.LAST_NAME).as("actor"),
       row(CATEGORY.CATEGORY_ID, CATEGORY.NAME).as("category"))
   .from(ACTOR)
   .join(FILM_ACTOR).using(FILM_ACTOR.ACTOR_ID)
   .join(FILM_CATEGORY).using(FILM_CATEGORY.FILM_ID)
   .join(CATEGORY).using(CATEGORY.CATEGORY_ID)
   .fetch();
```

Combines elegantly with implicit joins:

```java
ctx.select(CUSTOMER, CUSTOMER.address().city().country())
   .from(CUSTOMER)
   .fetch();
```

**Caveat**: Projecting a table reference translates to `TABLE.*` — all columns are fetched regardless of need. For frequently used projections, consider database views or explicit column selection with `row()`.

---

## Pattern: Don't use ad-hoc converters with UNION — move logic server-side
**Source**: [How to use jOOQ's Converters with UNION Operations](https://blog.jooq.org/how-to-use-jooqs-converters-with-union-operations) (2023-03-02)
**Since**: jOOQ 3.15 (ad-hoc converters)

Ad-hoc converters are **client-side post-fetch** transformations. In a UNION, jOOQ only considers the row type of the **first subquery** when fetching results, and the DB doesn't know about converters during deduplication. Converters on non-first subqueries silently do nothing.

```kotlin
// BAD — converter on second subquery never executes
dsl.select(BOOK.ID)
    .from(BOOK)
    .union(
        select(AUTHOR.ID.convertFrom { -it })
            .from(AUTHOR)
    )
    .fetch()

// GOOD — use a server-side function instead
dsl.select(BOOK.ID)
    .from(BOOK)
    .union(
        select(AUTHOR.ID.neg())
            .from(AUTHOR)
    )
    .fetch()
```

If you must use a converter with UNION, apply it to **all subqueries** (at minimum the first one).

---
