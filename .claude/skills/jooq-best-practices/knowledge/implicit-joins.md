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
