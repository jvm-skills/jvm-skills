# Aggregate Functions

## Pattern: Prefer FILTER over CASE in aggregates
**Source**: [The Performance Impact of SQL's FILTER Clause](https://blog.jooq.org/the-performance-impact-of-sqls-filter-clause) (2023-02-06)

Use `FILTER (WHERE ...)` instead of `CASE WHEN ... END` inside aggregate functions. They are semantically equivalent, but FILTER is more readable and ~8% faster on PostgreSQL (benchmarked on PG 15).

```kotlin
// Prefer: FILTER syntax
ctx.select(
    sum(FILM.LENGTH).filterWhere(FILM.RATING.eq("R")),
    sum(FILM.LENGTH).filterWhere(FILM.RATING.eq("PG"))
)

// Avoid: CASE syntax (slower on PostgreSQL, less readable)
ctx.select(
    sum(case_().when(FILM.RATING.eq("R"), FILM.LENGTH)),
    sum(case_().when(FILM.RATING.eq("PG"), FILM.LENGTH))
)
```

**Dialect note**: Native FILTER support in CockroachDB, Firebird, H2, HSQLDB, PostgreSQL, SQLite, YugabyteDB. For other databases, jOOQ automatically emulates FILTER as CASE.

---

## Pattern: Functional dependencies in GROUP BY
**Source**: [Functional Dependencies in SQL GROUP BY](https://blog.jooq.org/functional-dependencies-in-sql-group-by) (2021-10-29)
**Since**: jOOQ 3.16 (table-level grouping)

When a primary or unique key is in the `GROUP BY` clause, columns functionally dependent on that key can be projected without listing them in `GROUP BY`. This reduces boilerplate and maintenance burden.

```kotlin
// Instead of listing every column in GROUP BY:
ctx.select(AUTHOR.ID, AUTHOR.NAME, count(BOOK.ID))
    .from(AUTHOR)
    .leftJoin(BOOK).on(BOOK.AUTHOR_ID.eq(AUTHOR.ID))
    .groupBy(AUTHOR.ID)  // NAME is functionally dependent on ID
    .fetch()

// Since jOOQ 3.16: group by table (uses primary key automatically)
ctx.select(AUTHOR.ID, AUTHOR.NAME, count(BOOK.ID))
    .from(AUTHOR)
    .leftJoin(BOOK).on(BOOK.AUTHOR_ID.eq(AUTHOR.ID))
    .groupBy(AUTHOR)  // table-level grouping
    .fetch()
```

**Dialect note**: Functional dependency recognition supported in CockroachDB, H2, HSQLDB, MariaDB, MySQL, PostgreSQL, SQLite, YugabyteDB. Other dialects (Db2, Oracle, SQL Server, Firebird) require all projected columns in GROUP BY explicitly — jOOQ handles this transparently when using table-level grouping.

---

## Pattern: Prefer COUNT(*) over COUNT(1)
**Source**: [What's Faster? COUNT(*) or COUNT(1)?](https://blog.jooq.org/whats-faster-count-or-count1) (2019-09-19)

Always use `COUNT(*)` rather than `COUNT(1)`. They produce identical results, but `COUNT(*)` is slightly faster on PostgreSQL (~10%) and equal on MySQL/Oracle/SQL Server. The difference: `COUNT(expr)` checks each argument for NULL, adding overhead that `COUNT(*)` avoids via optimization.

Critical semantic difference: `COUNT(column)` counts only non-NULL rows — useful when LEFT JOINing or counting conditional subsets:

```kotlin
// COUNT(*) counts all rows including NULL-filled LEFT JOIN rows
// COUNT(column) returns 0 for actors with no films (correct behavior)
ctx.select(ACTOR.FIRST_NAME, count(FILM.FILM_ID))
    .from(ACTOR)
    .leftJoin(FILM_ACTOR).on(FILM_ACTOR.ACTOR_ID.eq(ACTOR.ACTOR_ID))
    .leftJoin(FILM).on(FILM.FILM_ID.eq(FILM_ACTOR.FILM_ID))
    .groupBy(ACTOR.ACTOR_ID)
    .fetch()

// Conditional counts in a single query
ctx.select(
    count(),  // COUNT(*)
    count(case_().when(ACTOR.FIRST_NAME.like("A%"), inline(1))),
    count(case_().when(ACTOR.FIRST_NAME.like("%A"), inline(1)))
).from(ACTOR).fetch()
```

> **Note**: In jOOQ, `count()` (no argument) generates `COUNT(*)`.

---

## Pattern: Simulate REDUCE aggregation via recursive CTE
**Source**: [Implementing a generic REDUCE aggregate function with SQL](https://blog.jooq.org/implementing-a-generic-reduce-aggregate-function-with-sql) (2021-02-08)
**Dialect**: PostgreSQL (uses `ARRAY_AGG`, `UNNEST ... WITH ORDINALITY`)

SQL has no built-in REDUCE/fold aggregate (like Java's `Stream.reduce()`). Emulate it with `ARRAY_AGG` to preserve ordered values, `UNNEST ... WITH ORDINALITY` to generate stable row indexes, then a recursive CTE to fold left across the indexed elements.

```sql
-- Multiply all values in a group: equivalent to Stream.reduce((i, j) -> i * j)
WITH t(grp, i) AS (VALUES ('A', 2), ('A', 4), ('A', 3))
SELECT grp, (
    WITH u AS (
        SELECT i, o FROM UNNEST(ARRAY_AGG(t.i)) WITH ORDINALITY AS u(i, o)
    ),
    RECURSIVE r(i, o) AS (
        SELECT i, o FROM u WHERE o = 1
        UNION ALL
        SELECT r.i * u.i, u.o FROM u JOIN r ON u.o = r.o + 1
    )
    SELECT i FROM r ORDER BY o DESC LIMIT 1
)
FROM t
GROUP BY grp;
```

Key building blocks:
- `ARRAY_AGG(col)` — collects group values into an array
- `UNNEST(...) WITH ORDINALITY AS u(val, pos)` — expands array to rows with 1-based index; avoids window functions for ordering
- Recursive CTE with `UNION ALL` — applies the binary operation step-by-step, seeding from `pos = 1`

Wrap in a correlated subquery in `FROM` to allow `GROUP BY` in the outer query and return per-group results.

---

## Pattern: Weighted averages to fix join-multiplication distortion
**Source**: [Calculating Weighted Averages When Joining Tables in SQL](https://blog.jooq.org/calculating-weighted-averages-when-joining-tables-in-sql) (2019-03-15)

When joining a one-to-many relationship (e.g. transactions → line items), the "one" side rows are duplicated for each matching row on the "many" side. Plain `AVG()` on a duplicated column is incorrect — transactions with more line items get over-weighted.

**Fix option 1**: Divide by the duplication factor (when row count is known):

```sql
-- t.lines stores the line count per transaction
SELECT
  sum(l.profit)                                  AS total_profit,
  sum(t.price / t.lines) / count(DISTINCT t.id)  AS avg_price_per_transaction
FROM lines l
JOIN transactions t ON t.id = l.transaction_id
```

**Fix option 2**: Pre-aggregate the many side first, then join 1-to-1:

```sql
SELECT
  sum(l.profit_per_transaction) AS total_profit,
  avg(t.price)                  AS avg_price_per_transaction
FROM (
  SELECT transaction_id, sum(profit) AS profit_per_transaction
  FROM lines
  GROUP BY transaction_id
) l
JOIN transactions t ON t.id = l.transaction_id
```

Option 2 is generally safer — it produces a true 1-to-1 join, so all standard aggregates work correctly without adjustment.

---
