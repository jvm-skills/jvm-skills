# SQL Naming Conventions

## Pattern: Table aliasing algorithm
**Source**: [A Guide to SQL Naming Conventions](https://blog.jooq.org/a-guide-to-sql-naming-conventions) (2019-10-29)

Use a deterministic aliasing algorithm to generate consistent table aliases. This prevents alias collisions and makes column prefixing predictable across views and derived tables:

- No underscores → first 4 letters: `CUSTOMER` → `CUST`
- 1 underscore → first 2 letters of each word: `FILM_ACTOR` → `FIAC`
- 2+ underscores → first letter of each word: `FILM_CATEGORY_DETAILS` → `FICD`

Prefix column aliases with the table alias to avoid ambiguity in joins and views:

```sql
SELECT
  cust.first_name AS cust_first_name,
  addr.city       AS addr_city
FROM customer cust
JOIN address addr ON cust.id = addr.customer_id
```

In jOOQ this maps naturally — when generating column aliases, apply the same prefix:

```kotlin
val cust = CUSTOMER.`as`("cust")
val addr = ADDRESS.`as`("addr")

dsl.select(
    cust.FIRST_NAME.`as`("cust_first_name"),
    addr.CITY.`as`("addr_city")
)
.from(cust)
.join(addr).on(cust.ID.eq(addr.CUSTOMER_ID))
```

---

## Pattern: Semantic type prefixes for stored objects
**Source**: [A Guide to SQL Naming Conventions](https://blog.jooq.org/a-guide-to-sql-naming-conventions) (2019-10-29)

Use prefixes/suffixes to encode object type into the name, avoiding namespace conflicts between tables, views, procedures, and parameters:

| Prefix/Suffix | Meaning |
|---|---|
| `V_` prefix | View |
| `_R` suffix | Read-only view |
| `_W` suffix | Updatable view |
| `P_` prefix | Procedure/function parameter |
| `L_` prefix | Local variable |

This prevents collisions where a parameter named `id` conflicts with a column named `id` inside a stored procedure body.

---

## Pattern: Singular vs. plural table names
**Source**: [A Guide to SQL Naming Conventions](https://blog.jooq.org/a-guide-to-sql-naming-conventions) (2019-10-29)

No universal standard. Choose one convention (singular `CUSTOMER` or plural `CUSTOMERS`) and apply it consistently across the entire schema. Mixing conventions causes confusion.

---
