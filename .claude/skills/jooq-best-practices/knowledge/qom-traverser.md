# Query Object Model & Traverser API

## Pattern: Inspect query structure with QOM accessors
**Source**: [Traversing jOOQ Expression Trees with the new Traverser API](https://blog.jooq.org/traversing-jooq-expression-trees-with-the-new-traverser-api) (2022-02-02)
**Since**: jOOQ 3.16

The `org.jooq.impl.QOM` type exposes the internal query structure as a public API. Accessor methods prefixed with `$` let you inspect expression internals. Each accessor has a corresponding mutator returning a new immutable instance.

```java
// Inspect a SUBSTRING function's arguments
Substring s = (QOM.Substring) DSL.substring(BOOK.TITLE, 1, 10);
s.$string();            // BOOK.TITLE
s.$startingPosition();  // 1
s.$length();            // 10
```

---

## Pattern: Traverse expression trees to collect metadata
**Source**: [Traversing jOOQ Expression Trees with the new Traverser API](https://blog.jooq.org/traversing-jooq-expression-trees-with-the-new-traverser-api) (2022-02-02)
**Since**: jOOQ 3.16

The `Traverser` interface provides depth-first tree traversal with pre/post-visit events, recursive control (skip subtrees), and early termination.

```java
// Collect all tables referenced in a query
Set<Table<?>> tables = query
    .$traverse(Traversers.collecting(
        q -> q instanceof TableField ? Stream.of(((TableField<?,?>) q).getTable()) : Stream.empty(),
        Collectors.toSet()
    ));
```

---

## Pattern: Transform SQL with $replace()
**Source**: [Traversing jOOQ Expression Trees with the new Traverser API](https://blog.jooq.org/traversing-jooq-expression-trees-with-the-new-traverser-api) (2022-02-02)
**Since**: jOOQ 3.16

Use `$replace()` to transform expression trees — eliminate redundancies, inject predicates, or rewrite statements.

```java
// Eliminate double negation: NOT(NOT(x)) → x
query.$replace(q -> {
    if (q instanceof QOM.Not not && not.$arg1() instanceof QOM.Not inner)
        return inner.$arg1();
    return q;
});
```

**Use cases**:
- **Row-level security**: transparently add WHERE predicates to queries on restricted tables
- **Soft deletion**: rewrite DELETE → UPDATE with a deleted flag
- **Audit columns**: auto-inject updated_at/updated_by on DML
- **SQL optimization**: remove redundant function calls (`UPPER(UPPER(x))` → `UPPER(x)`)

---
