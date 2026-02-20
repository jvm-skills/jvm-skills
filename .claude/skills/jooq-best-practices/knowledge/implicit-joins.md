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

---
