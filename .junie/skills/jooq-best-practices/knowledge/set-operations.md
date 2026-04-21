# Set Operations & Table Comparison

## Pattern: Compare two tables with EXCEPT/UNION

**Source**: [Use NATURAL FULL JOIN to compare two tables in SQL](https://blog.jooq.org/use-natural-full-join-to-compare-two-tables-in-sql) (2020-08-05)

Find rows that exist in one table but not the other using set operators. `EXCEPT` treats NULLs as not distinct (NULL = NULL).

```sql
(TABLE t1 EXCEPT TABLE t2)
UNION ALL
(TABLE t2 EXCEPT TABLE t1)
ORDER BY a, b, c
```

In jOOQ:

```kotlin
ctx.select()
    .from(
        T1.except(T2)
            .unionAll(T2.except(T1))
    )
    .fetch()
```

**Trade-off**: Scans each table twice (once per set operation).

---

## Pattern: Single-scan table diff with FULL JOIN ... USING

**Source**: [Use NATURAL FULL JOIN to compare two tables in SQL](https://blog.jooq.org/use-natural-full-join-to-compare-two-tables-in-sql) (2020-08-05)

Access each table only once by adding a discriminator column and doing a FULL JOIN with USING on the data columns:

```sql
SELECT *
FROM (SELECT 't1' AS t1, t1.* FROM t1) t1
FULL JOIN (SELECT 't2' AS t2, t2.* FROM t2) t2
USING (a, b, c)
WHERE t1 IS NULL OR t2 IS NULL;
```

Rows where `t1 IS NULL` → only in t2; rows where `t2 IS NULL` → only in t1.

**Caveat**: Can produce a cartesian product on duplicate rows — slower than EXCEPT/UNION when duplicates are common.

---

## Pattern: NULL-safe FULL JOIN comparison with IS NOT DISTINCT FROM

**Source**: [Use NATURAL FULL JOIN to compare two tables in SQL](https://blog.jooq.org/use-natural-full-join-to-compare-two-tables-in-sql) (2020-08-05)

When tables contain NULL values, `USING` and `=` won't match NULL to NULL. Use `IS NOT DISTINCT FROM` on a JOIN ON clause instead:

```sql
SELECT
  COALESCE(t1.a, t2.a) AS a,
  COALESCE(t1.b, t2.b) AS b,
  COALESCE(t1.c, t2.c) AS c,
  t1.t1, t2.t2
FROM (SELECT 't1' AS t1, t1.* FROM t1) t1
FULL JOIN (SELECT 't2' AS t2, t2.* FROM t2) t2
ON (t1.a, t1.b, t1.c) IS NOT DISTINCT FROM (t2.a, t2.b, t2.c)
WHERE t1 IS NULL OR t2 IS NULL;
```

In jOOQ use `isNotDistinctFrom()`:

```kotlin
.fullJoin(t2Alias)
.on(
    row(t1Alias.A, t1Alias.B, t1Alias.C)
        .isNotDistinctFrom(t2Alias.A, t2Alias.B, t2Alias.C)
)
```

**Note**: `EXCEPT`/`UNION` already treat NULLs as not distinct — this workaround is only needed for JOIN-based approaches.

---

## Pattern: INTERSECT has higher precedence than UNION/EXCEPT

**Source**: [5 Ways to Better Understand SQL by Adding Optional Parentheses](https://blog.jooq.org/better-understand-sql-by-adding-optional-parentheses) (2020-03-03)

INTERSECT binds more tightly than UNION and EXCEPT. This SQL:

```sql
SELECT a UNION SELECT b INTERSECT SELECT c
-- Executes as:
SELECT a UNION (SELECT b INTERSECT SELECT c)
```

In jOOQ, use explicit parentheses via `intersect()` chaining order to control evaluation:

```kotlin
// Explicit grouping: b INTERSECT c first, then UNION a
selectFrom(A)
    .union(
        selectFrom(B).intersect(selectFrom(C))
    )
```

**Dialect note**: Not all databases implement set-operation precedence identically — always use explicit grouping for clarity.

---

## Pattern: Multi-column row value expressions in IN predicates

**Source**: [5 Ways to Better Understand SQL by Adding Optional Parentheses](https://blog.jooq.org/better-understand-sql-by-adding-optional-parentheses) (2020-03-03)

SQL allows comparing multiple columns at once using row value expressions:

```sql
WHERE (first_name, last_name) IN (
  ('SUSAN', 'DAVIS'),
  ('NICK', 'WAHLBERG')
)
```

In jOOQ use `row()` with `in()`:

```kotlin
.where(
    row(ACTOR.FIRST_NAME, ACTOR.LAST_NAME)
        .`in`(row("SUSAN", "DAVIS"), row("NICK", "WAHLBERG"))
)
```

More concise and avoids multiple OR conditions. jOOQ emulates this for databases that don't natively support row value expressions in IN.

---

## Pattern: Row value expression NULL logic

**Source**: [Use NATURAL FULL JOIN to compare two tables in SQL](https://blog.jooq.org/use-natural-full-join-to-compare-two-tables-in-sql) (2020-08-05)

For multi-column row value expressions, `R IS NULL` and `NOT (R IS NOT NULL)` are NOT equivalent when only some columns are NULL:

| Row state             | `R IS NULL` | `R IS NOT NULL` |
|-----------------------|-------------|-----------------|
| All columns NULL      | true        | false           |
| Some columns NULL     | false       | false           |
| No columns NULL       | false       | true            |

Use this to discriminate between "row not found" (all NULL from outer join) vs "row with nullable columns".

---
