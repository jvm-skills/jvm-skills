# jOOQ Type System

## Pattern: Never reference Step types in user code
**Source**: [A Brief Overview over the Most Common jOOQ Types](https://blog.jooq.org/a-brief-overview-over-the-most-common-jooq-types) (2022-09-06)

Step types like `SelectFromStep`, `SelectWhereStep` are internal fluent API artifacts. Never use them in variable declarations or method signatures — use `Select`, `ResultQuery`, or `Query` instead.

```kotlin
// WRONG — leaks internal step type
val query: SelectWhereStep<Record> = dsl.select().from(TABLE)

// RIGHT — use the stable result type
val query: ResultQuery<Record> = dsl.select().from(TABLE).where(condition)
```

---

## Pattern: DSLContext vs static DSL
**Source**: [A Brief Overview over the Most Common jOOQ Types](https://blog.jooq.org/a-brief-overview-over-the-most-common-jooq-types) (2022-09-06)

- **`DSL` (static)**: Creates expression tree nodes (fields, conditions, tables) without a Configuration — use for building reusable query fragments
- **`DSLContext`**: Creates executable queries attached to a Configuration — use when you want to `fetch()` or `execute()` directly

```kotlin
// Static DSL — reusable expression, no execution
val isActive = DSL.field("active", Boolean::class.java).isTrue

// DSLContext — executable query
val users = dsl.selectFrom(USERS).where(isActive).fetch()
```

---

## Pattern: Result vs Cursor for fetch sizing
**Source**: [A Brief Overview over the Most Common jOOQ Types](https://blog.jooq.org/a-brief-overview-over-the-most-common-jooq-types) (2022-09-06)

- **`Result<R>`**: Eagerly fetched `List<Record>` — fine for moderate result sets
- **`Cursor<R>`**: Lazy `Iterable<Record>` keeping JDBC ResultSet open — use for huge result sets to avoid OOM

```kotlin
// Eager — loads all rows into memory
val all: Result<UsersRecord> = dsl.selectFrom(USERS).fetch()

// Lazy — streams rows one at a time
dsl.selectFrom(USERS).fetchLazy().use { cursor ->
    for (record in cursor) { /* process */ }
}
```

---

## Pattern: Converter vs Binding for custom types
**Source**: [A Brief Overview over the Most Common jOOQ Types](https://blog.jooq.org/a-brief-overview-over-the-most-common-jooq-types) (2022-09-06)

- **`Converter<T, U>`**: Simple bidirectional mapping between JDBC type `T` and user type `U` — covers most cases
- **`Binding<T, U>`**: Full control over JDBC get/set interactions — use only when you need to override how jOOQ talks to JDBC (e.g., custom `PreparedStatement.setObject()` calls)

Choose `Converter` by default; only escalate to `Binding` when `Converter` isn't enough.

---

## Pattern: Select as subquery, derived table, or union part
**Source**: [A Brief Overview over the Most Common jOOQ Types](https://blog.jooq.org/a-brief-overview-over-the-most-common-jooq-types) (2022-09-06)

A `Select` can be used in four contexts without transformation:
1. **Top-level query** — `dsl.select(...).from(...).fetch()`
2. **Scalar subquery** — `DSL.field(select)` in a SELECT or WHERE clause
3. **Derived table** — `select.asTable("alias")` in a FROM clause
4. **Union operand** — `select1.unionAll(select2)`

---

## Pattern: Row value expressions for multi-column operations
**Source**: [A Brief Overview over the Most Common jOOQ Types](https://blog.jooq.org/a-brief-overview-over-the-most-common-jooq-types) (2022-09-06)

Use `Row` types for tuple comparisons and multi-column predicates:

```kotlin
// Compare multiple columns at once
dsl.selectFrom(ORDERS)
    .where(DSL.row(ORDERS.YEAR, ORDERS.MONTH).eq(2024, 6))
    .fetch()
```

---

## Pattern: Condition extends Field<Boolean> — use conditions as fields
**Source**: [A Condition is a Field](https://blog.jooq.org/a-condition-is-a-field) (2022-08-24)
**Since**: jOOQ 3.17

Since jOOQ 3.17, `Condition` extends `Field<Boolean>`, matching the SQL standard where predicates are boolean value expressions. This means conditions can be used directly in SELECT, GROUP BY, ORDER BY, and PARTITION BY — no wrapping needed.

```kotlin
// Before 3.17 — required DSL.field() wrapper
ctx.select(BOOK.ID, DSL.field(BOOK.ID.gt(2)).`as`("big_id"))
   .from(BOOK)
   .fetch()

// Since 3.17 — condition used directly as a field
ctx.select(BOOK.ID, BOOK.ID.gt(2).`as`("big_id"))
   .from(BOOK)
   .fetch()

// Conditions in ORDER BY and GROUP BY
ctx.selectFrom(BOOK)
   .orderBy(BOOK.PUBLISHED.isTrue.desc())  // booleans first
   .fetch()
```

Non-boolean-supporting dialects (e.g., Oracle) get automatic `CASE` emulation preserving three-valued logic.

---
