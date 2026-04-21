# Hierarchical Queries

## Pattern: Collect flat parent-child rows into a tree with `Records.intoHierarchy()`
**Source**: [How to Turn a List of Flat Elements into a Hierarchy in Java, SQL, or jOOQ](https://blog.jooq.org/how-to-turn-a-list-of-flat-elements-into-a-hierarchy-in-java-sql-or-jooq) (2023-03-24)
**Since**: jOOQ 3.19

Use the built-in `Records.intoHierarchy()` collector to turn a flat parent-child result set into a tree — no manual map-building needed.

```java
record Dir(long id, String label, List<Dir> children) {}

List<Dir> roots = ctx
    .select(T_DIRECTORY.ID, T_DIRECTORY.PARENT_ID, T_DIRECTORY.LABEL)
    .from(T_DIRECTORY)
    .collect(Records.intoHierarchy(
        r -> r.value1(),                          // key (id)
        r -> r.value2(),                          // parent key (parent_id)
        r -> new Dir(r.value1(), r.value3(), new ArrayList<>()),  // node mapper
        (parent, child) -> parent.children().add(child)           // linker
    ));
```

The collector returns only root nodes (those with `null` parent key). Children are attached via the linker function.

**Tip**: `ResultQuery` implements `Iterable`, so `.collect()` works directly on the query without calling `.fetch()` first.

---

## Pattern: Recursive CTE for hierarchy traversal in SQL
**Source**: [How to Turn a List of Flat Elements into a Hierarchy in Java, SQL, or jOOQ](https://blog.jooq.org/how-to-turn-a-list-of-flat-elements-into-a-hierarchy-in-java-sql-or-jooq) (2023-03-24)

When you need the hierarchy built in SQL (e.g., for JSON output), use a recursive CTE with bottom-up aggregation:

```sql
WITH RECURSIVE hierarchy (id, parent_id, label, level) AS (
    SELECT id, parent_id, label, 0
    FROM t_directory
    WHERE parent_id IS NULL
    UNION ALL
    SELECT d.id, d.parent_id, d.label, h.level + 1
    FROM t_directory d
    JOIN hierarchy h ON h.id = d.parent_id
)
SELECT * FROM hierarchy ORDER BY level, label;
```

**Trade-off**: The Java collector approach (`intoHierarchy`) is simpler when you already fetch flat rows and need an object tree. The SQL CTE approach is better when you need the hierarchy for further SQL processing or JSON aggregation in the database.

---
