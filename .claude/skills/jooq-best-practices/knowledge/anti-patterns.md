# Anti-Patterns (Don't Do This)

## Pattern: Don't implement DSL types
**Source**: [jOOQ Official Docs — Don't do this](https://www.jooq.org/doc/3.20/manual/reference/dont-do-this/) (docs)

Never directly implement jOOQ's DSL type interfaces. Use the provided abstractions.

---

## Pattern: Don't reference Step types
**Source**: [jOOQ Official Docs — Don't do this](https://www.jooq.org/doc/3.20/manual/reference/dont-do-this/) (docs)

Don't depend on intermediate query-building step types (e.g., `SelectConditionStep`) in your API signatures. Use the final result types.

---

## Pattern: Use EXISTS() instead of COUNT(*)
**Source**: [jOOQ Official Docs — Don't do this](https://www.jooq.org/doc/3.20/manual/reference/dont-do-this/) (docs)

For existence checks, use `EXISTS()` not `COUNT(*) > 0`. The DB can short-circuit with EXISTS.

```kotlin
// BAD
val exists = dsl.selectCount().from(BOOK).where(BOOK.ID.eq(id)).fetchOne(0, Int::class.java)!! > 0

// GOOD
val exists = dsl.fetchExists(selectFrom(BOOK).where(BOOK.ID.eq(id)))
```

---

## Pattern: Use COUNT(*) with LIMIT when checking for N+ rows
**Source**: [An Efficient Way to Check for Existence of Multiple Values in SQL](https://blog.jooq.org/an-efficient-way-to-check-for-existence-of-multiple-values-in-sql) (2024-02-16)

When you need `COUNT(*) >= N` (not just existence), wrap the query in a derived table with `LIMIT N` so the DB stops early. ~2.5x faster on PostgreSQL.

```kotlin
// BAD — scans all matching rows to count them
dsl.select(
    field(select(count()).from(ACTOR)
        .join(FILM_ACTOR).using(ACTOR.ACTOR_ID)
        .where(ACTOR.LAST_NAME.eq("WAHLBERG"))).ge(2))

// GOOD — stops after finding N rows
dsl.select(
    field(select(count()).from(
        select().from(ACTOR)
            .join(FILM_ACTOR).using(ACTOR.ACTOR_ID)
            .where(ACTOR.LAST_NAME.eq("WAHLBERG"))
            .limit(2)
    )).ge(2))
```

---

## Pattern: Avoid N+1 queries
**Source**: [jOOQ Official Docs — Don't do this](https://www.jooq.org/doc/3.20/manual/reference/dont-do-this/) (docs)

Don't execute queries in loops. Use joins, MULTISET, or batch fetching instead.

---

## Pattern: Use NOT EXISTS instead of NOT IN
**Source**: [jOOQ Official Docs — Don't do this](https://www.jooq.org/doc/3.20/manual/reference/dont-do-this/) (docs)

`NOT IN` with nullable columns produces unexpected results (NULL propagation). Use `NOT EXISTS`.

```kotlin
// BAD — breaks if subquery returns NULL
dsl.selectFrom(AUTHOR).where(AUTHOR.ID.notIn(select(BOOK.AUTHOR_ID).from(BOOK)))

// GOOD
dsl.selectFrom(AUTHOR).whereNotExists(
    selectOne().from(BOOK).where(BOOK.AUTHOR_ID.eq(AUTHOR.ID))
)
```

---

## Pattern: Don't use SELECT *
**Source**: [jOOQ Official Docs — Don't do this](https://www.jooq.org/doc/3.20/manual/reference/dont-do-this/) (docs)

Select only needed columns. Improves performance and makes intent clear. Use `selectFrom()` only when you need the full record.

---

## Pattern: Use UNION ALL over UNION
**Source**: [jOOQ Official Docs — Don't do this](https://www.jooq.org/doc/3.20/manual/reference/dont-do-this/) (docs)

`UNION` deduplicates (sorts), `UNION ALL` doesn't. Use `UNION ALL` unless you explicitly need deduplication.

---

## Pattern: Don't rely on implicit ordering
**Source**: [jOOQ Official Docs — Don't do this](https://www.jooq.org/doc/3.20/manual/reference/dont-do-this/) (docs)

Always add explicit `ORDER BY`. Query results without it have no guaranteed order, even if they appear consistent.

---

## Pattern: Avoid SELECT DISTINCT as a fix
**Source**: [jOOQ Official Docs — Don't do this](https://www.jooq.org/doc/3.20/manual/reference/dont-do-this/) (docs)

If you need DISTINCT, it often means a missing join condition or a flawed query. Fix the root cause.

---

## Pattern: Avoid NATURAL JOIN and JOIN USING
**Source**: [jOOQ Official Docs — Don't do this](https://www.jooq.org/doc/3.20/manual/reference/dont-do-this/) (docs)

Use explicit `ON` clauses. NATURAL JOIN/USING break silently when columns are renamed.

---

## Pattern: Don't ORDER BY column index
**Source**: [jOOQ Official Docs — Don't do this](https://www.jooq.org/doc/3.20/manual/reference/dont-do-this/) (docs)

Use column references, not numeric positions. Column indices are fragile and hard to read.

---

## Schema: Name your constraints
**Source**: [jOOQ Official Docs — Don't do this](https://www.jooq.org/doc/3.20/manual/reference/dont-do-this/) (docs)

Always name constraints explicitly. Auto-generated names are hard to reference in migrations and error messages.

---

## Schema: Use NOT NULL by default
**Source**: [jOOQ Official Docs — Don't do this](https://www.jooq.org/doc/3.20/manual/reference/dont-do-this/) (docs)

Columns should be NOT NULL unless NULL has a specific meaning. Unnecessary nullability complicates queries and Kotlin type mappings.

---

## Schema: Use correct data types
**Source**: [jOOQ Official Docs — Don't do this](https://www.jooq.org/doc/3.20/manual/reference/dont-do-this/) (docs)

Don't store dates as strings, money as floats, or IPs as integers. Use the proper SQL types.

---

## Schema: Don't add unnecessary surrogate keys
**Source**: [jOOQ Official Docs — Don't do this](https://www.jooq.org/doc/3.20/manual/reference/dont-do-this/) (docs)

If a natural key exists and is stable, use it. Not every table needs a serial/UUID primary key.
