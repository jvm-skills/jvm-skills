# Sequences

## Pattern: Fetch a single sequence value
**Source**: [How to Fetch Sequence Values with jOOQ](https://blog.jooq.org/how-to-fetch-sequence-values-with-jooq) (2022-03-01)

Use the code-generated `Sequences` class with `nextval()` and `fetchValue()`:

```java
// import static com.example.generated.Sequences.*;
Long next = ctx.fetchValue(S.nextval());
```

jOOQ translates to dialect-specific syntax automatically:
- **PostgreSQL, CockroachDB, YugabyteDB**: `nextval('s')`
- **Oracle, Db2, HANA, Informix, Snowflake**: `s.nextval`
- **Derby, Firebird, H2, HSQLDB, MariaDB, SQL Server**: `NEXT VALUE FOR s`

---

## Pattern: Fetch multiple sequence values in one round-trip
**Source**: [How to Fetch Sequence Values with jOOQ](https://blog.jooq.org/how-to-fetch-sequence-values-with-jooq) (2022-03-01)

Use `nextvals(n)` with `fetchValues()` to get N values in a single query instead of N round-trips:

```java
List<Long> ids = ctx.fetchValues(S.nextvals(10));
// [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
```

Internally uses jOOQ's `GENERATE_SERIES` emulation to produce all values in one statement.

---
