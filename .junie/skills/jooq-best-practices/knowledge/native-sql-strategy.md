# Native SQL Strategy

## Pattern: Hybrid approach — jOOQ DSL + database views/functions
**Source**: [When to Use jOOQ and When to Use Native SQL](https://blog.jooq.org/when-to-use-jooq-and-when-to-use-native-sql) (2022-12-08)

When a query is too complex or static for jOOQ DSL (e.g., large CTEs, deeply nested derived tables), **don't fall back to plain SQL strings**. Instead, extract the logic into a **SQL view** or **table-valued function** in your migration (Flyway/Liquibase), then regenerate jOOQ code. The view/function becomes a first-class jOOQ table with full type safety.

**Use jOOQ DSL when**:
- Query is **dynamic** (conditionally built at runtime)
- You need **multi-dialect** portability
- **Type safety** from code generation adds value
- Using **MULTISET** or other jOOQ-specific features
- Calling **stored procedures** (code-generated bindings)
- You want built-in **SQL injection** protection

**Use views/functions when**:
- Query is **large and static** (many CTEs, deeply nested)
- You prefer writing SQL in a **dedicated SQL editor** first
- The query won't change at runtime

```kotlin
// Instead of a 100-line jOOQ DSL query, create a view:
// CREATE VIEW v_author_stats AS SELECT ... (complex SQL)
// Then in jOOQ after code-gen:
ctx.selectFrom(V_AUTHOR_STATS)
   .where(V_AUTHOR_STATS.COUNTRY.eq("US"))
   .fetch()
```

**Key**: both approaches keep queries inside jOOQ's ecosystem — never extract SQL to run via plain JDBC/JPA (see anti-patterns.md).

---
