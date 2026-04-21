# DML RETURNING — Returning Data from INSERT/UPDATE/DELETE

## Pattern: Basic RETURNING with jOOQ
**Source**: [The Many Ways to Return Data From SQL DML](https://blog.jooq.org/the-many-ways-to-return-data-from-sql-dml) (2022-08-23)

Use `.returning().fetchOne()` to get the full record back from an INSERT:

```java
ActorRecord actor = ctx.insertInto(ACTOR, ACTOR.FIRST_NAME, ACTOR.LAST_NAME)
    .values("John", "Doe")
    .returning()
    .fetchOne();
```

Use `returningResult()` for arbitrary column projections instead of the full record.

---

## Pattern: Dialect emulation — jOOQ abstracts RETURNING across databases
**Source**: [The Many Ways to Return Data From SQL DML](https://blog.jooq.org/the-many-ways-to-return-data-from-sql-dml) (2022-08-23)

jOOQ generates different SQL depending on the dialect:

| Dialect | Native syntax |
|---------|--------------|
| **PostgreSQL, MariaDB, Firebird** | `RETURNING` clause |
| **Db2, H2** | `SELECT ... FROM FINAL TABLE (INSERT ...)` (data change delta table) |
| **SQL Server** | `OUTPUT INSERTED.* INTO @result` |
| **Oracle** | PL/SQL `FORALL` + `RETURNING BULK COLLECT INTO` |
| **Others (JDBC fallback)** | `Statement.RETURN_GENERATED_KEYS` (identity columns only) |

You write the same jOOQ code; the dialect-specific translation is automatic.

---

## Pattern: Data change delta table (SQL standard)
**Source**: [The Many Ways to Return Data From SQL DML](https://blog.jooq.org/the-many-ways-to-return-data-from-sql-dml) (2022-08-23)
**Dialect**: Db2, H2

Wrap DML in `FINAL TABLE (...)` to query the result like a regular SELECT:

```sql
SELECT id, last_update
FROM FINAL TABLE (
  INSERT INTO actor (first_name, last_name) VALUES ('John', 'Doe')
) a
```

Modifiers: `OLD TABLE` (pre-modification), `NEW TABLE` (post-modification, pre-trigger), `FINAL TABLE` (post-trigger). Also works with `MERGE`.

---

## Pattern: RETURNING in CTEs (PostgreSQL)
**Source**: [The Many Ways to Return Data From SQL DML](https://blog.jooq.org/the-many-ways-to-return-data-from-sql-dml) (2022-08-23)
**Dialect**: PostgreSQL

PostgreSQL allows DML with `RETURNING` inside a CTE, enabling post-insert processing:

```sql
WITH inserted AS (
  INSERT INTO actor (first_name, last_name)
  VALUES ('John', 'Doe')
  RETURNING id, last_update
)
SELECT * FROM inserted
```

---

## Pattern: Set-based UPDATE instead of row-by-row loops
**Source**: [How to Use SQL UPDATE .. RETURNING to Run DML More Efficiently](https://blog.jooq.org/how-to-use-sql-update-returning-to-run-dml-more-efficiently) (2018-09-26)

Avoid iterating rows and updating one-by-one ("slow-by-slow"). A single set-based UPDATE is ~2.5–7x faster and creates less lock contention:

```sql
-- BAD: row-by-row loop (PL/SQL / application-side)
FOR r IN (SELECT * FROM t WHERE category = 1) LOOP
  UPDATE t SET counter = counter + 1 WHERE id = r.id;
END LOOP;

-- GOOD: single set-based UPDATE
UPDATE t SET counter = NVL(counter, 0) + 1 WHERE category = 1;
```

In jOOQ:
```kotlin
ctx.update(T)
   .set(T.COUNTER, nvl(T.COUNTER, 0).plus(1))
   .where(T.CATEGORY.eq(1))
   .execute()
```

**Caveat**: When many concurrent processes read the same rows, row-by-row may reduce lock contention. Prefer set-based by default; benchmark before choosing row-by-row.

---

## Pattern: Aggregate functions inside RETURNING (Oracle)
**Source**: [How to Use SQL UPDATE .. RETURNING to Run DML More Efficiently](https://blog.jooq.org/how-to-use-sql-update-returning-to-run-dml-more-efficiently) (2018-09-26)
**Dialect**: Oracle, Firebird

Oracle allows aggregate functions in the `RETURNING` clause of a DML statement, letting you capture summary info without a follow-up SELECT:

```sql
UPDATE t
SET counter = NVL(counter, 0) + 1
WHERE category = 1
RETURNING
  LISTAGG(text, ', ') WITHIN GROUP (ORDER BY text),
  COUNT(*)
INTO v_text, v_updated_count;
```

PostgreSQL achieves the same via a CTE with `RETURNING` + aggregation in the outer query. SQL Server's `OUTPUT` clause does **not** support aggregates.

---

## Pattern: JDBC RETURN_GENERATED_KEYS limitations
**Source**: [The Many Ways to Return Data From SQL DML](https://blog.jooq.org/the-many-ways-to-return-data-from-sql-dml) (2022-08-23)

When jOOQ falls back to JDBC's `RETURN_GENERATED_KEYS`:
- Only works for single-row `INSERT` (not bulk, not `UPDATE`/`DELETE`)
- Only returns identity/auto-increment columns
- Oracle/HSQLDB support specifying column names for broader retrieval

**Best practice**: Let jOOQ handle the abstraction — don't use JDBC directly for RETURNING. jOOQ picks the best strategy per dialect automatically.

---
