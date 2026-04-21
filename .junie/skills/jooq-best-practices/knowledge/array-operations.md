# Array Operations

## Pattern: Array lambda functions (filter, map, match)
**Source**: [When SQL Meets Lambda Expressions](https://blog.jooq.org/when-sql-meets-lambda-expressions) (2025-03-27)

jOOQ provides functional-style array operations using Java/Kotlin lambdas that translate to native SQL lambdas on supporting databases (ClickHouse, Databricks, DuckDB, Snowflake, Trino). On PostgreSQL, jOOQ **emulates** these via subquery-based unnesting and reaggregation.

**Available functions**:
- `arrayFilter` — filter array elements by predicate
- `arrayMap` — transform each element
- `arrayAllMatch` — true if all elements match
- `arrayAnyMatch` — true if any element matches
- `arrayNoneMatch` — true if no elements match

```kotlin
// Filter even numbers from an array
arrayFilter(array(1, 2, 2, 3), { e -> e.mod(2).eq(0) })
// Result: [2, 2]
```

The jOOQ API uses `Function1<Field<T>, Condition>` (or `Field<T>` for map) as the lambda parameter:

```java
public static <T> Field<T[]> arrayFilter(
    Field<T[]> array,
    Function1<? super Field<T>, ? extends Condition> predicate
)
```

**PostgreSQL note**: Since PostgreSQL lacks native lambda syntax for arrays, jOOQ emulates by unnesting the array into rows, applying the filter/map as a WHERE/SELECT clause, and reaggregating. This works but may be less performant than native implementations on other databases.

---
