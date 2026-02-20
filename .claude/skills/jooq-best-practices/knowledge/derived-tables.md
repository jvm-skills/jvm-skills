# Derived Tables

## Pattern: Declare derived table before use
**Source**: [How to Write a Derived Table in jOOQ](https://blog.jooq.org/how-to-write-a-derived-table-in-jooq) (2023-02-24)

Java requires variable declaration before use, so declare your derived table as a `Table<?>` first, then reference it in the outer query.

```java
Table<?> nested =
    select(BOOK.AUTHOR_ID, count().as("books"))
    .from(BOOK)
    .groupBy(BOOK.AUTHOR_ID).asTable("nested");

ctx.select(nested.fields())
   .from(nested)
   .orderBy(nested.field("books"))
   .fetch();
```

---

## Pattern: Extract fields for type-safe derived table columns
**Source**: [How to Write a Derived Table in jOOQ](https://blog.jooq.org/how-to-write-a-derived-table-in-jooq) (2023-02-24)

Derived tables lose generated-code type safety. Recover it by extracting `Field<T>` references and passing them to `nested.field(fieldRef)`:

```java
Field<Integer> count = count().as("books");

Table<?> nested =
    select(BOOK.AUTHOR_ID, count)
    .from(BOOK)
    .groupBy(BOOK.AUTHOR_ID).asTable("nested");

ctx.select(nested.fields())
   .from(nested)
   .orderBy(nested.field(count))
   .fetch();
```

---

## Pattern: LATERAL derived tables as local column variables
**Source**: [LATERAL is Your Friend to Create Local Column Variables in SQL](https://blog.jooq.org/lateral-is-your-friend-to-create-local-column-variables-in-sql) (2022-11-04)

Use `CROSS JOIN LATERAL` to compute expressions once and reuse them throughout the query — like local variables in the `FROM` clause. Each LATERAL subquery can reference columns from preceding tables.

```sql
SELECT actor_id, name, name_length, COUNT(*)
FROM actor
CROSS JOIN LATERAL (
  SELECT first_name || ' ' || last_name AS name
) AS t1
CROSS JOIN LATERAL (
  SELECT length(name) AS name_length
) AS t2
JOIN film_actor AS fa USING (actor_id)
GROUP BY actor_id, name, name_length
ORDER BY COUNT(*) DESC
```

This avoids repeating the same expression in `SELECT`, `GROUP BY`, and `ORDER BY`. Variables declared in `FROM` are visible to all subsequent clauses.

**Dialect**: Standard SQL (Db2, Firebird, MySQL, PostgreSQL, Snowflake). SQL Server and Oracle use `CROSS APPLY` instead of `CROSS JOIN LATERAL`.

---

## Pattern: Exclude columns with asterisk().except()
**Source**: [The Useful BigQuery * EXCEPT Syntax](https://blog.jooq.org/the-useful-bigquery-except-syntax) (2022-01-07)

Use `asterisk().except(field)` to select all columns except specific ones. jOOQ emulates BigQuery's `* EXCEPT` syntax by expanding it to an explicit column list on databases that don't support it natively.

Particularly useful when `LAST_UPDATE` or other audit columns interfere with `NATURAL JOIN`:

```java
Actor a = ACTOR.as("a");
FilmActor fa = FILM_ACTOR.as("fa");

ctx.select(a.ACTOR_ID, a.FIRST_NAME, a.LAST_NAME, count(fa.FILM_ID))
   .from(select(asterisk().except(a.LAST_UPDATE)).from(a).asTable(a))
   .naturalLeftOuterJoin(
       select(asterisk().except(fa.LAST_UPDATE)).from(fa).asTable(fa))
   .groupBy(a.ACTOR_ID, a.FIRST_NAME, a.LAST_NAME)
   .fetch();
```

jOOQ resolves column references at render time and expands `* EXCEPT` into the full column list for dialects that lack native support.

---

## Pattern: Simplify away unnecessary derived tables
**Source**: [How to Write a Derived Table in jOOQ](https://blog.jooq.org/how-to-write-a-derived-table-in-jooq) (2023-02-24)

Many derived tables are unnecessary — flattening the query restores full type safety from generated code. Always evaluate whether you actually need the subquery.

```java
// Before: unnecessary derived table
// After: flat query with full type safety
Field<Integer> count = count().as("books");

ctx.select(BOOK.AUTHOR_ID, count)
   .from(BOOK)
   .groupBy(BOOK.AUTHOR_ID)
   .orderBy(count)
   .fetch();
```

---
