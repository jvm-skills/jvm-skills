# Implicit Joins

## Pattern: Implicit path joins with automatic join elimination
**Source**: [A Hidden Benefit of Implicit Joins: Join Elimination](https://blog.jooq.org/a-hidden-benefit-of-implicit-joins-join-elimination) (2024-01-10)
**Since**: jOOQ 3.19

Navigate foreign key relationships directly in expressions without explicit `JOIN` clauses. jOOQ generates LEFT JOINs automatically and eliminates intermediate tables whose columns aren't referenced anywhere in the query.

```java
// Navigate actor → film → category via implicit path joins
ctx.select(ACTOR, ACTOR.film().category().NAME)
   .from(ACTOR)
   .fetch();
```

jOOQ detects that `FILM` is only a pass-through (no columns projected, no conditions) and eliminates it:

```sql
-- FILM table removed; film_actor joins directly to film_category
FROM actor
  LEFT JOIN film_actor ON actor.actor_id = film_actor.actor_id
  LEFT JOIN film_category ON film_actor.film_id = film_category.film_id
  LEFT JOIN category ON film_category.category_id = category.category_id
```

If you later reference a column from the intermediate table (e.g., in a WHERE clause), it reappears automatically:

```java
ctx.select(ACTOR, ACTOR.film().category().NAME)
   .from(ACTOR)
   .where(ACTOR.film().TITLE.like("A%"))
   .fetch();
// FILM table now included because TITLE is referenced
```

---

## Pattern: To-many implicit path joins
**Source**: [A Hidden Benefit of Implicit Joins: Join Elimination](https://blog.jooq.org/a-hidden-benefit-of-implicit-joins-join-elimination) (2024-01-10)
**Since**: jOOQ 3.19

To-many path joins support many-to-many relationships, skipping relationship/bridge tables automatically. Controlled by `Settings.renderImplicitJoinToManyType` (not enabled by default).

**Why disabled by default**: Implicit to-many joins in projections create cartesian products silently — rows are generated through implicit joins rather than visibly in the FROM clause. Always use explicit `leftJoin(path)` in FROM for to-many relationships to make the row multiplication visible.

```java
// WRONG — implicit to-many in WHERE duplicates rows silently
ctx.select(ACTOR.FIRST_NAME, ACTOR.LAST_NAME)
   .from(ACTOR)
   .where(ACTOR.film().TITLE.like("A%"))
   .fetch();

// RIGHT — explicit join makes row multiplication visible
ctx.select(ACTOR.FIRST_NAME, ACTOR.LAST_NAME, ACTOR.film().TITLE)
   .from(ACTOR)
   .leftJoin(ACTOR.film())
   .fetch();
```

> **Supersedes**: older implicit to-many approach from [jOOQ 3.19's new Explicit and Implicit to-many path joins](https://blog.jooq.org/jooq-3-19s-new-explicit-and-implicit-to-many-path-joins) — the newer article reinforces that explicit joins are preferred

---

## Pattern: Explicit path joins (control join type)
**Source**: [jOOQ 3.19's new Explicit and Implicit to-many path joins](https://blog.jooq.org/jooq-3-19s-new-explicit-and-implicit-to-many-path-joins) (2023-12-28)
**Since**: jOOQ 3.19

Override the default LEFT JOIN by declaring path joins explicitly in the FROM clause. Useful when you need INNER JOIN or want to add ON conditions.

```java
// Explicit path join with controlled join type
ctx.select(CUSTOMER.FIRST_NAME, CUSTOMER.LAST_NAME,
           CUSTOMER.address().city().country().NAME)
   .from(CUSTOMER)
   .leftJoin(CUSTOMER.address().city().country())
   .fetch();

// Step-by-step explicit joins (same result)
ctx.select(CUSTOMER.FIRST_NAME, CUSTOMER.LAST_NAME,
           CUSTOMER.address().city().country().NAME)
   .from(CUSTOMER)
   .leftJoin(CUSTOMER.address())
   .leftJoin(CUSTOMER.address().city())
   .leftJoin(CUSTOMER.address().city().country())
   .fetch();

// With additional ON predicate
ctx.select(CUSTOMER.FIRST_NAME, CUSTOMER.address().city().NAME)
   .from(CUSTOMER)
   .leftJoin(CUSTOMER.address().city())
      .on(CUSTOMER.address().city().NAME.like("A%"))
   .fetch();
```

---

## Pattern: Implicit joins within explicit JOIN ON clauses
**Source**: [Using jOOQ's Implicit Join From Within the JOIN .. ON Clause](https://blog.jooq.org/using-jooqs-implicit-join-from-within-the-join-on-clause) (2022-09-13)
**Since**: jOOQ 3.11

Use implicit path expressions on a joined table's columns within the ON clause itself. jOOQ nests the implicit joins inside the explicit join structure, preserving SQL operator precedence.

```java
// Join pg_attribute explicitly, then use implicit paths in ON clause
// to navigate pg_attribute → pg_class → pg_namespace
Attributes isA = ATTRIBUTES.as("is_a");
PgAttribute pgA = PG_ATTRIBUTE.as("pg_a");

ctx.select(isA.UDT_SCHEMA, isA.UDT_NAME, isA.ATTRIBUTE_NAME, pgA.ATTNDIMS)
   .from(isA)
   .join(pgA)
     .on(isA.ATTRIBUTE_NAME.eq(pgA.ATTNAME))
     .and(isA.UDT_NAME.eq(pgA.pgClass().RELNAME))
     .and(isA.UDT_SCHEMA.eq(pgA.pgClass().pgNamespace().NSPNAME))
   .where(isA.DATA_TYPE.eq("ARRAY"))
   .fetch();
```

jOOQ generates nested joins to preserve precedence — implicit joins become sub-joins of the explicit join:

```sql
FROM information_schema.attributes AS is_a
  JOIN (
    pg_catalog.pg_attribute AS pg_a
      JOIN (pg_catalog.pg_class JOIN pg_catalog.pg_namespace
              ON pg_class.relnamespace = pg_namespace.oid)
        ON pg_a.attrelid = pg_class.oid
  ) ON (is_a.attribute_name = pg_a.attname
    AND is_a.udt_name = pg_class.relname
    AND is_a.udt_schema = pg_namespace.nspname)
```

Requires **synthetic foreign keys** when the schema lacks real FKs (e.g., `pg_catalog` views):

```xml
<syntheticObjects>
  <foreignKeys>
    <foreignKey>
      <tables>pg_attribute</tables>
      <fields><field>attrelid</field></fields>
      <referencedTable>pg_class</referencedTable>
    </foreignKey>
    <foreignKey>
      <tables>pg_class</tables>
      <fields><field>relnamespace</field></fields>
      <referencedTable>pg_namespace</referencedTable>
    </foreignKey>
  </foreignKeys>
</syntheticObjects>
```

---

## Pattern: Synthetic foreign keys with composite keys and unique key references
**Source**: [Using jOOQ 3.14 Synthetic Foreign Keys to Write Implicit Joins on Views](https://blog.jooq.org/using-jooq-3-14-synthetic-foreign-keys-to-write-implicit-joins-on-views) (2020-10-13)
**Since**: jOOQ 3.14

When views lack native FK constraints (e.g., `INFORMATION_SCHEMA` views), declare synthetic foreign keys in the code generator config to enable implicit joins. Supports composite keys and references to unique keys (not just primary keys).

```xml
<syntheticObjects>
  <primaryKeys>
    <primaryKey>
      <tables>DOMAIN_CONSTRAINTS</tables>
      <fields>
        <field>CONSTRAINT_CATALOG</field>
        <field>CONSTRAINT_SCHEMA</field>
        <field>CONSTRAINT_NAME</field>
      </fields>
    </primaryKey>
  </primaryKeys>
  <foreignKeys>
    <foreignKey>
      <tables>CHECK_CONSTRAINTS</tables>
      <fields>
        <field>CONSTRAINT_CATALOG</field>
        <field>CONSTRAINT_SCHEMA</field>
        <field>CONSTRAINT_NAME</field>
      </fields>
      <referencedTable>DOMAIN_CONSTRAINTS</referencedTable>
      <!-- Field order in <fields> must match referenced key column order -->
    </foreignKey>
  </foreignKeys>
</syntheticObjects>
```

This eliminates accidental cartesian products — jOOQ ensures all composite key columns are included automatically in the generated join predicates.

---

## Pattern: Implicit join path correlation (correlated subqueries)
**Source**: [jOOQ 3.19's new Explicit and Implicit to-many path joins](https://blog.jooq.org/jooq-3-19s-new-explicit-and-implicit-to-many-path-joins) (2023-12-28)
**Since**: jOOQ 3.19

Use path expressions in correlated subqueries — jOOQ auto-correlates the path to the outer query. Eliminates manual correlation predicates like `FILM_ACTOR.ACTOR_ID.eq(ACTOR.ACTOR_ID)`.

```java
// Correlated EXISTS with path correlation (no manual join predicates)
ctx.select(ACTOR.FIRST_NAME, ACTOR.LAST_NAME)
   .from(ACTOR)
   .where(exists(selectOne()
       .from(ACTOR.film())
       .where(ACTOR.film().TITLE.like("A%"))))
   .fetch();

// Same with semi-join syntax
ctx.select(ACTOR.FIRST_NAME, ACTOR.LAST_NAME)
   .from(ACTOR)
   .leftSemiJoin(ACTOR.film())
      .on(ACTOR.film().TITLE.like("A%"))
   .fetch();
```

---

## Pattern: Implicit joins in DML (UPDATE / DELETE)
**Source**: [jOOQ 3.17 Supports Implicit Join also in DML](https://blog.jooq.org/jooq-3-17-supports-implicit-join-also-in-dml) (2022-08-25)
**Since**: jOOQ 3.17

Use path expressions in WHERE clauses of UPDATE and DELETE statements. jOOQ translates them to correlated subqueries (universal) or DML JOIN syntax (MySQL/MariaDB).

```java
// Update books where the language code is "en"
ctx.update(BOOK)
   .set(BOOK.STATUS, SOLD_OUT)
   .where(BOOK.language().CD.eq("en"))
   .execute();

// Delete books by language
ctx.delete(BOOK)
   .where(BOOK.language().CD.eq("en"))
   .execute();
```

Generated SQL (correlated subquery — most dialects):

```sql
UPDATE book SET status = 'SOLD OUT'
WHERE (SELECT language.cd FROM language
       WHERE book.language_id = language.id) = 'en';
```

**Dialect**: MySQL/MariaDB use DML JOIN syntax instead; Oracle may use updatable inline views.

---

## Pattern: MULTISET with implicit path joins
**Source**: [jOOQ 3.19's new Explicit and Implicit to-many path joins](https://blog.jooq.org/jooq-3-19s-new-explicit-and-implicit-to-many-path-joins) (2023-12-28)
**Since**: jOOQ 3.19

Combine MULTISET correlated subqueries with path joins to collect nested to-many collections without manual correlation.

```java
ctx.select(
    ACTOR.FIRST_NAME, ACTOR.LAST_NAME,
    multiset(select(ACTOR.film().TITLE)
        .from(ACTOR.film())).as("films"),
    multiset(selectDistinct(ACTOR.film().category().NAME)
        .from(ACTOR.film().category())).as("categories"))
   .from(ACTOR)
   .fetch();
```

---
