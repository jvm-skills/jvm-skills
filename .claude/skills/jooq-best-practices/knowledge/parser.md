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

## Pattern: Parsing connection for automatic dialect translation
**Source**: [Using jOOQ to write vendor agnostic SQL with JPA's native query or @Formula](https://blog.jooq.org/using-jooq-to-write-vendor-agnostic-sql-with-jpas-native-query-or-formula) (2021-08-26)

jOOQ's parsing connection/data source is a JDBC proxy that intercepts SQL statements and translates them between dialects automatically. Useful for legacy JPA/Hibernate applications with vendor-specific native SQL.

```java
// Wrap any DataSource to get automatic dialect translation
DataSource parsingDataSource = DSL
    .using(originalDataSource, targetDialect)
    .parsingDataSource();
```

Translates automatically:
- `NVL()` → `IFNULL()` (MySQL) / `COALESCE()` (SQL Server)
- Removes unsupported `AS` for table aliases (Oracle)
- Converts `BOOLEAN` expressions to `CASE` where needed (SQL Server)

**Caching**: `Settings.cacheParsingConnectionLRUCacheSize` (default 8192) avoids repeated parse overhead.

**ParseListener SPI**: extend translation for custom functions:
```java
configuration.derive(ParseListener.onParseCondition(ctx -> {
    if (ctx.parseFunctionNameIf("LOGICAL_XOR")) {
        // Custom dialect-specific translation
    }
}));
```

**Use cases**: JPA `createNativeQuery()`, Hibernate `@Formula`, Spring Data `@Query(nativeQuery = true)` — all get dialect translation without changing application code.

---
