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

## Pattern: JDBC RETURN_GENERATED_KEYS limitations
**Source**: [The Many Ways to Return Data From SQL DML](https://blog.jooq.org/the-many-ways-to-return-data-from-sql-dml) (2022-08-23)

When jOOQ falls back to JDBC's `RETURN_GENERATED_KEYS`:
- Only works for single-row `INSERT` (not bulk, not `UPDATE`/`DELETE`)
- Only returns identity/auto-increment columns
- Oracle/HSQLDB support specifying column names for broader retrieval

**Best practice**: Let jOOQ handle the abstraction — don't use JDBC directly for RETURNING. jOOQ picks the best strategy per dialect automatically.

---
