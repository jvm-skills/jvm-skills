# Join Patterns

## Pattern: ON clause vs WHERE clause with outer joins
**Source**: [The Difference Between SQL's JOIN .. ON Clause and the Where Clause](https://blog.jooq.org/the-difference-between-sqls-join-on-clause-and-the-where-clause) (2019-04-09)

Placing a predicate in the `ON` clause vs the `WHERE` clause produces identical results for INNER JOINs, but critically different results for OUTER JOINs.

- **ON clause**: filters rows *during* the join — determines which right-table rows match. Non-matching left rows are kept with NULLs.
- **WHERE clause**: filters rows *after* the join — removes entire rows from the result. This effectively converts an OUTER JOIN into an INNER JOIN.

```sql
-- Returns all actors; NULL film columns for actors with film_id >= 10
SELECT a.*, f.*
FROM actor a
LEFT JOIN film_actor fa ON a.actor_id = fa.actor_id AND fa.film_id < 10

-- Returns ONLY actors with film_id < 10 (WHERE turns LEFT JOIN into INNER JOIN)
SELECT a.*, f.*
FROM actor a
LEFT JOIN film_actor fa ON a.actor_id = fa.actor_id
WHERE fa.film_id < 10
```

**Rule**: Put predicates where they belong *logically*. If the predicate governs which rows participate in the join (right-table filter), use `ON`. If it applies to the entire result set, use `WHERE`.

In jOOQ:

```kotlin
// ON-clause predicate (join filter)
ctx.select(ACTOR.asterisk(), FILM_ACTOR.asterisk())
   .from(ACTOR)
   .leftJoin(FILM_ACTOR)
   .on(ACTOR.ACTOR_ID.eq(FILM_ACTOR.ACTOR_ID)
       .and(FILM_ACTOR.FILM_ID.lt(10)))
   .fetch()

// WHERE predicate (result filter — converts LEFT JOIN to INNER JOIN semantics)
ctx.select(ACTOR.asterisk(), FILM_ACTOR.asterisk())
   .from(ACTOR)
   .leftJoin(FILM_ACTOR).on(ACTOR.ACTOR_ID.eq(FILM_ACTOR.ACTOR_ID))
   .where(FILM_ACTOR.FILM_ID.lt(10))
   .fetch()
```

---
