# Pagination

## Pattern: Single-query pagination metadata with window functions
**Source**: [Calculating Pagination Metadata Without Extra Roundtrips in SQL](https://blog.jooq.org/calculating-pagination-metadata-without-extra-roundtrips-in-sql) (2021-03-11)

Avoid a second `SELECT COUNT(*)` roundtrip by embedding metadata into the paginated query using `COUNT(*) OVER()` and `ROW_NUMBER() OVER()` in nested derived tables.

Architecture:
1. **Inner layer**: original query
2. **Middle layer**: add `COUNT(*) OVER()` (total rows) and `ROW_NUMBER() OVER(ORDER BY ...)`
3. **Pagination layer**: apply `OFFSET ... FETCH`
4. **Outer layer**: compute `COUNT(*) OVER()` for actual page size, page number, and last-page flag

```java
// Reusable jOOQ utility: wraps any Select with pagination metadata
static <R extends Record> ResultQuery<Record> paginated(
    DSLContext ctx, Select<R> query, SortField<?>[] sort, int limit, int offset
) {
    // Middle layer: total count + row numbers
    Table<R> u = query.asTable("u");
    Field<Integer> totalRows = count().over().as("total_rows");
    Field<Integer> rowNum    = rowNumber().over().orderBy(sort).as("rn");

    Table<?> t = ctx.select(u.fields())
                    .select(totalRows, rowNum)
                    .from(u)
                    .asTable("t");

    // Pagination + metadata layer
    Field<Integer> totalField      = t.field("total_rows", Integer.class);
    Field<Integer> rnField         = t.field("rn", Integer.class);
    Field<Integer> actualPageSize  = count().over().as("actual_page_size");
    Field<Integer> currentPage     = field("{0} / {1} + 1", Integer.class, val(offset), val(limit)).as("current_page");
    Field<Boolean> lastPage        = field("{0} + {1} >= {2}", Boolean.class, val(offset), actualPageSize, totalField).as("last_page");

    return ctx.select(t.fields())
              .select(actualPageSize, currentPage, lastPage)
              .from(t)
              .orderBy(sort)
              .offset(offset)
              .limit(limit);
}
```

**Result**: every returned row includes `total_rows`, `actual_page_size`, `current_page`, and `last_page` — no second query needed.

---

## Pattern: Deterministic ordering is mandatory for keyset/offset pagination
**Source**: [Calculating Pagination Metadata Without Extra Roundtrips in SQL](https://blog.jooq.org/calculating-pagination-metadata-without-extra-roundtrips-in-sql) (2021-03-11)

Always ensure the `ORDER BY` criteria is fully deterministic (e.g., include the primary key as a tiebreaker). Non-deterministic ordering produces random page boundaries when rows tie on the sort column.

```java
// BAD: ties on last_name produce unstable pages
.orderBy(ACTOR.LAST_NAME)

// GOOD: tiebreaker makes order stable
.orderBy(ACTOR.LAST_NAME, ACTOR.ACTOR_ID)
```

---

## Pattern: Re-apply ORDER BY after every pagination wrapper
**Source**: [Calculating Pagination Metadata Without Extra Roundtrips in SQL](https://blog.jooq.org/calculating-pagination-metadata-without-extra-roundtrips-in-sql) (2021-03-11)

SQL provides no ordering guarantee when wrapping a sorted query in an outer `SELECT`. Always re-state `ORDER BY` in the outermost query that returns rows to the application.

---
