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

## Pattern: jOOQ SQL Translation Tool for static SQL
**Source**: [Translating Stored Procedures Between Dialects](https://blog.jooq.org/translating-stored-procedures-between-dialects) (2021-02-10)

For one-off or static SQL/procedural translation between dialects, use the online tool at **https://www.jooq.org/translate/** instead of the programmatic parsing API. Useful for migrating legacy stored procedures or ad-hoc dialect conversion without writing Java code.

The standalone CLI/parser can also be integrated with legacy JDBC applications for batch SQL migration.

---

## Pattern: IN list padding to reduce execution plan cache contention
**Source**: [Use IN List Padding to Your JDBC Application to Avoid Cursor Cache Contention Problems](https://blog.jooq.org/use-in-list-padding-to-your-jdbc-application-to-avoid-cursor-cache-contention-problems) (2021-04-22)
**Dialect**: Oracle, SQL Server (most critical; helps any DB with query plan caching)

When an application generates IN list queries with varying parameter counts, each distinct count produces a separate cache entry. Under high load this causes **cursor cache contention** and can saturate execution plan caches.

**Solution**: pad IN lists to the nearest power of 2, repeating the last value. Reduces distinct query shapes from N to log₂(N).

**Enable globally in jOOQ DSL**:
```java
DSLContext ctx = DSL.using(connection, dialect, new Settings().withInListPadding(true));
```

**Retrofit existing JDBC code** using `parsingConnection()` — no application changes needed:
```java
DSLContext ctx = DSL.using(connection, dialect);
ctx.settings().setInListPadding(true);
Connection paddedConnection = ctx.parsingConnection();
// hand paddedConnection to legacy JDBC code — padding applied transparently
```

> **Note**: Padding is a workaround. Prefer array types or temporary tables when the database supports them — they avoid the variable-length bind parameter problem entirely.

---
