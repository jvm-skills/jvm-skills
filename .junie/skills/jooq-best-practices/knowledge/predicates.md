# Predicates

## Pattern: Quantified LIKE ANY / LIKE ALL
**Source**: [Quantified LIKE ANY predicates in jOOQ 3.12](https://blog.jooq.org/quantified-like-any-predicates-in-jooq-3-12) (2019-09-05)
**Since**: jOOQ 3.12

Replace verbose OR chains of LIKE conditions with `like(any(...))`. jOOQ emulates this across databases that lack native quantified LIKE syntax (PostgreSQL, Oracle, etc.).

```kotlin
// Instead of:
// WHERE last_name LIKE 'A%' OR last_name LIKE 'B%' OR last_name LIKE 'C%'
ctx.selectFrom(CUSTOMERS)
   .where(CUSTOMERS.LAST_NAME.like(any("A%", "B%", "C%")))
   .fetch()

// With a subquery (dynamic patterns from a table):
ctx.selectFrom(CUSTOMERS)
   .where(CUSTOMERS.LAST_NAME.like(any(
       select(PATTERNS.PATTERN)
           .from(PATTERNS)
           .where(PATTERNS.CUSTOMER_TYPE.eq(CUSTOMERS.CUSTOMER_TYPE))
   )))
   .fetch()

// LIKE ALL — must match all patterns:
ctx.selectFrom(CUSTOMERS)
   .where(CUSTOMERS.LAST_NAME.like(all("A%", "%son")))
   .fetch()
```

---
