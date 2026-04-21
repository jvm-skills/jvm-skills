# Dynamic SQL

## Pattern: noCondition() / trueCondition() / falseCondition() for optional predicates
**Source**: [Create Empty Optional SQL Clauses with jOOQ](https://blog.jooq.org/create-empty-optional-sql-clauses-with-jooq) (2020-03-06)

Three no-op condition constants for dynamic WHERE/HAVING clauses:

- `DSL.noCondition()` — emits **no SQL**; if it's the only predicate, the WHERE clause is omitted entirely
- `DSL.trueCondition()` — emits `TRUE` / `1 = 1`
- `DSL.falseCondition()` — emits `FALSE` / `1 = 0`

Prefer `noCondition()` for optional filters; `falseCondition()` to short-circuit an entire subquery.

```kotlin
// Inline conditional predicate
ctx.select(T.A, T.B)
   .from(T)
   .where(T.C.eq(1))
   .and(if (something) T.D.eq(2) else DSL.noCondition())
   .fetch()

// Functional accumulation (recommended for multiple optional filters)
var where: Condition = DSL.noCondition()
if (filterByC) where = where.and(T.C.eq(1))
if (filterByD) where = where.and(T.D.gt(0))
ctx.select(T.A, T.B).from(T).where(where).fetch()
```

---

## Pattern: Conditional SELECT fields with inline fallback
**Source**: [Create Empty Optional SQL Clauses with jOOQ](https://blog.jooq.org/create-empty-optional-sql-clauses-with-jooq) (2020-03-06)

To conditionally include a column in the projection, use `DSL.inline("")` (or another typed literal) as a placeholder with `.as()` aliased to the column reference.

```kotlin
ctx.select(T.A, if (something) T.B else DSL.inline("").`as`(T.B))
   .from(T)
   .where(T.C.eq(1))
   .fetch()
```

---

## Pattern: Conditional JOIN with fallback to base table
**Source**: [Create Empty Optional SQL Clauses with jOOQ](https://blog.jooq.org/create-empty-optional-sql-clauses-with-jooq) (2020-03-06)

Use a ternary in the FROM clause to conditionally join a table. When the join is skipped, project a typed `inline()` literal for the joined column.

```kotlin
ctx.select(T.A, T.B, if (something) U.X else DSL.inline(""))
   .from(if (something) T.join(U).on(T.Y.eq(U.Y)) else T)
   .where(T.C.eq(1))
   .fetch()
```

---

## Pattern: Conditional UNION branch with falseCondition()
**Source**: [Create Empty Optional SQL Clauses with jOOQ](https://blog.jooq.org/create-empty-optional-sql-clauses-with-jooq) (2020-03-06)

To optionally include a UNION branch, use a literal-only SELECT with `falseCondition()` so the branch produces zero rows when not needed.

```kotlin
ctx.select(T.A, T.B)
   .union(
       if (something)
           select(U.A, U.B).from(U)
       else
           select(DSL.inline(""), DSL.inline(""))
               .where(DSL.falseCondition())
   )
   .fetch()
```

---
