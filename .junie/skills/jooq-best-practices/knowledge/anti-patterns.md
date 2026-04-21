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

## Pattern: Avoid N+1 queries — don't hide loops behind DAOs
**Source**: [jOOQ Official Docs — Don't do this](https://www.jooq.org/doc/3.20/manual/reference/dont-do-this/) (docs)
**Enriched by**: [To DAO or not to DAO](https://blog.jooq.org/to-dao-or-not-to-dao) (2023-12-06)

Don't execute queries in loops. Use joins, MULTISET, or batch fetching instead.

jOOQ's DAO API encourages N+1 patterns by making individual CRUD calls easy — the N+1 hides inside reusable `findByX()` methods called in loops. Prefer writing bulk SQL:

```kotlin
// BAD — DAO-style N+1: one query per account
for (account in accountDao.findAll()) {
    val txns = transactionDao.fetchByAccountId(account.id)
    // ...
}

// GOOD — single bulk update with EXISTS
dsl.update(TRANSACTION)
    .set(TRANSACTION.SOME_COUNTER, TRANSACTION.SOME_COUNTER.plus(1))
    .where(exists(
        selectOne().from(ACCOUNT)
            .where(ACCOUNT.ID.eq(TRANSACTION.ACCOUNT_ID))
            .and(ACCOUNT.SOME_CONDITION)
    ))
    .execute()
```

Use DAOs (if at all) only as base classes for specialized repositories that still write proper SQL.

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

## Pattern: DISTINCT is not a function — parentheses don't limit its scope
**Source**: [SQL DISTINCT is not a function](https://blog.jooq.org/sql-distinct-is-not-a-function) (2020-03-02)

A common misconception: `SELECT DISTINCT (col1), col2` looks like DISTINCT applies only to `col1`, but the parentheses are purely cosmetic. DISTINCT is a keyword that always applies to the **entire result set** — it deduplicates all columns combined. Both of these are identical:

```sql
SELECT DISTINCT (emp_id), fname, name FROM emp;
SELECT DISTINCT  emp_id,  fname, name FROM emp;
```

jOOQ's `selectDistinct()` enforces this correctly — no API exists to apply DISTINCT to a subset of columns (because SQL doesn't support it).

**PostgreSQL exception**: `DISTINCT ON (col)` is a vendor extension that keeps one row per distinct value of specific columns (requires `ORDER BY` to be deterministic):

```kotlin
// PostgreSQL only — keep one row per id, ordered by fname
dsl.selectDistinctOn(listOf(EMP.ID))
    .select(EMP.ID, EMP.FNAME, EMP.NAME)
    .from(EMP)
    .orderBy(EMP.ID, EMP.FNAME, EMP.NAME)
    .fetch()
```

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

> **Enriched by**: [The Cost of Useless Surrogate Keys in Relationship Tables](https://blog.jooq.org/the-cost-of-useless-surrogate-keys-in-relationship-tables) (2019-03-26)

For **relationship/junction tables** specifically, a surrogate key is almost always wasteful. Use a compound primary key from the FK columns instead:

```sql
-- BAD: unnecessary surrogate id on junction table
CREATE TABLE film_actor (
  id         INT NOT NULL PRIMARY KEY,
  actor_id   INT NOT NULL REFERENCES actor,
  film_id    INT NOT NULL REFERENCES film
);

-- GOOD: compound primary key is the natural identity
CREATE TABLE film_actor (
  actor_id   INT NOT NULL REFERENCES actor,
  film_id    INT NOT NULL REFERENCES film,
  PRIMARY KEY (actor_id, film_id)
);
```

**Dialect**: On **MySQL InnoDB** and **SQL Server** (clustered-index databases), the surrogate approach benchmarks ~50% slower for typical join queries because the natural compound key serves as a covering index. On **PostgreSQL** and **Oracle** (heap-table databases) the difference is negligible, but the compound key is still semantically correct and saves storage.

---

## Pattern: Use .eq() not .equals() for jOOQ comparisons
**Source**: [10 Things You Didn't Know About jOOQ](https://blog.jooq.org/10-things-you-didnt-know-about-jooq) (2021-08-20)

jOOQ fields have `.eq()`, `.ne()`, `.lt()`, `.le()`, `.gt()`, `.ge()` comparison methods. Using Java's `.equals()` compiles but calls the wrong overload (Java Object equality, not SQL comparison) and produces a `Boolean` not a `Condition`.

```kotlin
// BAD — compiles but wrong: .equals() is Java Object method, not SQL comparison
.where(USER.NAME.equals(userName))

// GOOD — SQL comparison returning a Condition
.where(USER.NAME.eq(userName))
```

---

## Pattern: Use noCondition() for dynamic SQL building
**Source**: [10 Things You Didn't Know About jOOQ](https://blog.jooq.org/10-things-you-didnt-know-about-jooq) (2021-08-20)

Build dynamic conditions functionally with `noCondition()` (a no-op condition). Avoid mutating intermediate query-builder step objects with `where()` after construction.

```kotlin
// BAD — mutable approach: mutates the step object
val s = dsl.select(T.A, T.B).from(T)
if (something) s.where(T.C.eq(1))  // mutation, easy to miss bugs

// GOOD — functional approach: compose conditions
var c: Condition = noCondition()
if (something) c = c.and(T.C.eq(1))
if (somethingElse) c = c.and(T.D.gt(0))
dsl.select(T.A, T.B).from(T).where(c).fetch()
```

---

## Pattern: Don't extract jOOQ SQL to execute via JDBC or JPA
**Source**: [Why You Should Execute jOOQ Queries With jOOQ](https://blog.jooq.org/why-you-should-execute-jooq-queries-with-jooq) (2023-01-18)

Building queries with jOOQ DSL but executing them via JDBC, JdbcTemplate, or JPA loses most of jOOQ's value:

- **Type-safe mapping**: `fetch(Records.mapping(MyDto::new))` with compile-time checked constructor refs
- **Execution emulations**: MULTISET, ROW expressions, and batched connections only work through jOOQ's executor
- **Stored procedures**: jOOQ generates type-safe wrappers — one call vs manual `CallableStatement` with positional parameter juggling
- **Identity fetching**: `RETURNING`, `OUTPUT`, `FINAL TABLE` — jOOQ handles dialect differences automatically
- **Import/Export**: built-in CSV, JSON, XML, HTML formatting
- **R2DBC**: reactive execution with the same DSL — `Flux.from(ctx.select(...)).map(Records.mapping(...))`

The only legitimate case for SQL extraction: using jOOQ for 2–3 dynamic queries in a JPA app where you need entity lifecycle management.

```kotlin
// BAD — loses type safety, emulations, mapping
val sql = dsl.select(FILM.TITLE, multiset(...)).from(FILM).getSQL()
jdbcTemplate.query(sql) { rs, _ -> ... } // manual mapping, MULTISET broken

// GOOD — full jOOQ execution
dsl.select(FILM.TITLE, multiset(...))
    .from(FILM)
    .fetch(Records.mapping(Film::new))
```

---

## Pattern: Never forget to call .execute() on DML/DDL
**Source**: [Never Again Forget to Call .execute() in jOOQ](https://blog.jooq.org/never-again-forget-to-call-execute-in-jooq) (2021-03-30)

jOOQ's fluent DSL makes it easy to build a complete DML/DDL statement without actually running it. The statement is only sent to the DB when you call the terminal method.

```kotlin
// BAD — builds the query but never executes it (silent no-op)
ctx.insertInto(T)
   .columns(T.A, T.B)
   .values(1, 2)

// GOOD — .execute() actually runs the statement
ctx.insertInto(T)
   .columns(T.A, T.B)
   .values(1, 2)
   .execute()
```

jOOQ annotates all relevant API methods with `@CheckReturnValue` (JSR-305 style). Enable IntelliJ IDEA's **"Result of method call ignored"** inspection to get IDE warnings whenever you forget the terminal method.

---

## Pattern: Don't map relational data to objects in middleware when the output is JSON/XML
**Source**: [Stop Mapping Stuff in Your Middleware. Use SQL's XML or JSON Operators Instead](https://blog.jooq.org/stop-mapping-stuff-in-your-middleware-use-sqls-xml-or-json-operators-instead) (2019-11-13)

When a service's sole purpose is producing JSON/XML from the database, avoid the pipeline: rows → entity objects → DTOs → JSON serialization. Each step adds code, error surface, and maintenance burden without adding value.

Instead, use SQL's native JSON/XML operators (via jOOQ's DSL) to build the nested structure directly in the query:

```kotlin
// BAD — unnecessary entity/DTO round-trip for JSON output
val actors = dsl.selectFrom(ACTOR).fetch().map { ActorDto(it.firstName, it.lastName,
    dsl.selectFrom(FILM_ACTOR).where(...).map { FilmDto(it.title) }) }
return ObjectMapper().writeValueAsString(actors) // N+1 + wasted allocations

// GOOD — JSON built entirely in SQL, one round-trip
dsl.select(
    jsonObject(
        key("firstName").value(ACTOR.FIRST_NAME),
        key("lastName").value(ACTOR.LAST_NAME),
        key("films").value(jsonArrayAgg(jsonObject("title", FILM.TITLE))
            .orderBy(FILM.TITLE))
    )
).from(ACTOR)
 .join(FILM_ACTOR).on(ACTOR.ACTOR_ID.eq(FILM_ACTOR.ACTOR_ID))
 .join(FILM).on(FILM_ACTOR.FILM_ID.eq(FILM.FILM_ID))
 .groupBy(ACTOR.ACTOR_ID)
 .fetch()
```

**Rule**: "Don't go mapping that stuff in the middleware if you're not consuming it in the middleware." If only the HTTP client consumes the final JSON, the database should produce it.

> Use jOOQ's `jsonObject`/`jsonArrayAgg` (3.14+) or `MULTISET` (3.15+, preferred) — see [sql-json.md](sql-json.md) and [multiset.md](multiset.md).

---

## Pattern: Don't use H2 compatibility modes with jOOQ
**Source**: [Using H2 as a Test Database Product with jOOQ](https://blog.jooq.org/using-h2-as-a-test-database-product) (2022-08-19)

H2's compatibility modes (e.g., `MODE=PostgreSQL`) are for **plain SQL only**. When using jOOQ, jOOQ already handles dialect translation — combining H2 compatibility modes with `SQLDialect.SQLSERVER` (or other non-H2 dialects) causes conflicts because jOOQ assumes actual vendor capabilities.

**Rules:**
- If you must use H2, configure `SQLDialect.H2` — never a different dialect on H2
- Do **not** use H2 compatibility modes alongside jOOQ's dialect emulation
- Prefer **Testcontainers** to run the actual target database for integration tests — eliminates compatibility issues entirely

```kotlin
// BAD — jOOQ assumes real SQL Server features on H2
val dsl = DSL.using(h2Connection, SQLDialect.SQLSERVER)

// GOOD — use the real dialect for H2
val dsl = DSL.using(h2Connection, SQLDialect.H2)

// BEST — use Testcontainers with the real database
@Testcontainers
class BookRepositoryTest {
    @Container
    val postgres = PostgreSQLContainer("postgres:16")
    // jOOQ configured with SQLDialect.POSTGRES against real PostgreSQL
}
```
