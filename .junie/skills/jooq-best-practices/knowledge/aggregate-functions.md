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

## Pattern: Use PERCENTILE_DISC to detect data skew
**Source**: [Calculate Percentiles to Learn About Data Set Skew in SQL](https://blog.jooq.org/calculate-percentiles-to-learn-about-data-set-skew-in-sql) (2019-01-22)

Use `PERCENTILE_DISC` at regular intervals (0%, 25%, 50%, 75%, 100%) to reveal whether a column's data is uniformly distributed or skewed. Skewed distributions matter for query planning: a range predicate on a skewed column returns wildly different row counts depending on which part of the range is queried, making cardinality estimates unreliable and B-tree indexes less useful.

```sql
-- Profile distribution of a numeric column
SELECT
  percentile_disc(0.00) WITHIN GROUP (ORDER BY amount) AS "0%",
  percentile_disc(0.25) WITHIN GROUP (ORDER BY amount) AS "25%",
  percentile_disc(0.50) WITHIN GROUP (ORDER BY amount) AS "50%",
  percentile_disc(0.75) WITHIN GROUP (ORDER BY amount) AS "75%",
  percentile_disc(1.00) WITHIN GROUP (ORDER BY amount) AS "100%"
FROM payment;
-- Uniform: evenly spaced values → B-tree index efficient
-- Skewed: values cluster at one end → range queries vary wildly in row count
```

**Dialect**: Native aggregate form in Oracle, PostgreSQL. SQL Server supports only the window function form.

When skew is detected, consider histogram statistics, optimizer hints, or avoiding bind-variable reuse for that column.

---

## Pattern: Emulate PERCENTILE_DISC where not natively supported
**Source**: [How to Emulate PERCENTILE_DISC in MySQL and Other RDBMS](https://blog.jooq.org/how-to-emulate-percentile_disc-in-mysql-and-other-rdbms) (2019-01-28)
**Since**: jOOQ 3.11 (native support in some dialects)

`PERCENTILE_DISC` (inverse distribution / ordered-set aggregate) is not universally available. Native support as of jOOQ 3.11:

| Dialect | Aggregate | Window |
|---------|-----------|--------|
| MariaDB 10.3.3 | No | Yes |
| Oracle 18c | Yes | Yes |
| PostgreSQL 11 | Yes | No |
| SQL Server 2017 | No | Yes |

**Emulation using `PERCENT_RANK` + `FIRST_VALUE`**: Calculate percentile rank per group, then use `FIRST_VALUE` with a null-filtering sort to pick the matching value. Works across all RDBMS supporting window functions.

```sql
-- Window function form (e.g. PostgreSQL, MySQL)
SELECT DISTINCT rating,
  first_value(length) OVER (
    ORDER BY CASE WHEN p1 <= 0.5 THEN p1 END DESC NULLS LAST) AS median
FROM (
  SELECT rating, length,
    percent_rank() OVER (PARTITION BY rating ORDER BY length) p1
  FROM film
) t;
```

**Aggregate form** (MySQL — wrap with `MAX` and add outer `GROUP BY`):

```sql
SELECT rating, MAX(x1) AS median
FROM (
  SELECT rating,
    first_value(length) OVER (
      PARTITION BY rating
      ORDER BY CASE WHEN p1 <= 0.5 THEN p1 END DESC NULLS LAST) AS x1
  FROM (
    SELECT rating, length,
      percent_rank() OVER (PARTITION BY rating ORDER BY length) p1
    FROM film
  ) t
) t
GROUP BY rating;
```

**Key insight**: Null out ranks above the target threshold → sort nulls last → `FIRST_VALUE` picks the highest rank ≤ target, which is the `PERCENTILE_DISC` result.

---

## Pattern: Custom user-defined aggregate functions
**Source**: [Writing Custom Aggregate Functions in SQL Just Like a Java 8 Stream Collector](https://blog.jooq.org/writing-custom-aggregate-functions-in-sql) (2018-10-09)

When standard aggregates (COUNT, SUM, AVG, MIN, MAX) are insufficient, databases let you define custom aggregates — analogous to Java 8 `Stream.Collector` with supplier, accumulator, combiner, and finisher phases.

**PostgreSQL**: Use `CREATE AGGREGATE` with `SFUNC` (accumulator), `STYPE` (state type), and `FINALFUNC` (finisher):

```sql
-- State type tracking (max, second_max)
CREATE TYPE second_max_state AS (max NUMERIC, second_max NUMERIC);

CREATE FUNCTION second_max_accumulate(state second_max_state, val NUMERIC)
RETURNS second_max_state AS $$
  SELECT CASE
    WHEN val > state.max THEN ROW(val, state.max)
    WHEN val > state.second_max THEN ROW(state.max, val)
    ELSE state
  END
$$ LANGUAGE sql;

CREATE AGGREGATE second_max(NUMERIC) (
    SFUNC    = second_max_accumulate,
    STYPE    = second_max_state,
    FINALFUNC = (s) -> s.second_max
);
```

**Oracle**: Implement the `ODCIAggregate` interface (`ODCIAggregateInitialize`, `ODCIAggregateIterate`, `ODCIAggregateMerge`, `ODCIAggregateTerminate`). Oracle custom aggregates automatically work as window functions too.

Call via jOOQ using `DSL.aggregate()` or plain SQL templating:

```kotlin
// Call a custom aggregate via plain SQL
ctx.select(
    field("second_max({0})", Int::class.java, FILM.LENGTH)
).from(FILM).fetch()
```

---

## Pattern: Emulate PRODUCT() aggregate via EXP/LN
**Source**: [How to Write a Multiplication Aggregate Function in SQL](https://blog.jooq.org/how-to-write-a-multiplication-aggregate-function-in-sql) (2018-09-21)

SQL has no native `PRODUCT()` or `MUL()` aggregate. Emulate it using the logarithmic identity `x × y = e^(ln(x) + ln(y))`:

```sql
-- Basic (positive values only)
MUL(x) = EXP(SUM(LN(x)))

-- Full implementation: handles zeros, negatives, and works as a window function
SELECT i, j,
  CASE
    WHEN SUM(CASE WHEN j = 0 THEN 1 END) OVER (ORDER BY i) > 0 THEN 0
    WHEN SUM(CASE WHEN j < 0 THEN -1 END) OVER (ORDER BY i) % 2 < 0 THEN -1
    ELSE 1
  END * EXP(SUM(LN(ABS(NULLIF(j, 0)))) OVER (ORDER BY i)) AS multiplication
FROM v
```

Key edge cases:
- **Zero**: use `NULLIF(j, 0)` to exclude from LN; add a zero-check SUM to short-circuit to 0
- **Negatives**: count how many negatives are in the group; odd count → result is negative
- **Window variant**: add `OVER (ORDER BY ...)` to each SUM for cumulative running products

In jOOQ, compose with `DSL.exp()`, `DSL.ln()`, `DSL.nullif()`, and `DSL.sum()`.

**Dialect note (Oracle)**: Cast `NUMBER` columns to `BINARY_DOUBLE` before LN for ~100x faster execution.

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
