# Parser

## Pattern: Ignore comment syntax for unsupported SQL
**Source**: [The jOOQ Parser Ignore Comment Syntax](https://blog.jooq.org/the-jooq-parser-ignore-comment-syntax) (2021-10-19)

When jOOQ's parser encounters vendor-specific SQL it can't handle (e.g., `ALTER SYSTEM RESET ALL`), wrap it in ignore markers. The RDBMS sees normal comments and executes everything; jOOQ skips the marked sections.

Enable with `Settings.parseIgnoreComments`, then use:

```sql
CREATE TABLE a (i int);

/* [jooq ignore start] */
ALTER SYSTEM RESET ALL;
/* [jooq ignore stop] */

CREATE TABLE b (i int);
```

Works at expression level too — useful for vendor-specific DEFAULT clauses:

```sql
CREATE TABLE t (
  a int
    /* [jooq ignore start] */
    DEFAULT some_fancy_expression()
    /* [jooq ignore stop] */
);
```

Customize markers via `Settings.parseIgnoreCommentStart` and `Settings.parseIgnoreCommentStop`.

**Use case**: DDL migration scripts processed by jOOQ's `DDLDatabase` or parser-based code generation that contain unsupported vendor syntax.

---
