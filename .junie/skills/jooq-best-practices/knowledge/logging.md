# Logging & Diagnostics

## Pattern: R2DBC LoggingConnection for reactive SQL logging
**Source**: [jOOQ's R2DBC LoggingConnection to log all SQL statements](https://blog.jooq.org/jooqs-r2dbc-loggingconnection-to-log-all-sql-statements) (2023-01-17)
**Since**: jOOQ 3.18

Use `LoggingConnection` to wrap an R2DBC `Connection` and log all SQL statements at DEBUG level. Works as a proxy — intercepts `createStatement()`, `execute()`, `add()`, and `close()` calls.

Useful when the R2DBC driver doesn't provide its own DEBUG logging. Can also be used standalone (without jOOQ as query builder) by copying the source.

JDBC equivalent (`LoggingConnection` for JDBC) has existed longer — same concept, different SPI.

---

## Pattern: DiagnosticsConnection for N+1 query detection
**Source**: [Using jOOQ's DiagnosticsConnection to detect N+1 Queries](https://blog.jooq.org/using-jooqs-diagnosticsconnection-to-detect-n1-queries) (2022-01-11)

Wrap a JDBC connection (or DataSource) with jOOQ's `DiagnosticsConnection` to detect repeated SQL statements at runtime — the hallmark of N+1 problems. Framework-agnostic: works with jOOQ, Hibernate, JdbcTemplate, or raw JDBC.

The diagnostics listener fires after the **first repetition** of any normalised statement within a transaction, assuming that repeating the same query is generally unnecessary.

```java
// Per-connection setup
DSLContext ctx = DSL.using(connection);
ctx.configuration().set(new DefaultDiagnosticsListener() {
    @Override
    public void repeatedStatements(DiagnosticsContext c) {
        System.out.println("Repeated: " + c.normalisedStatement());
    }
});
Connection diagConn = ctx.diagnosticsConnection();
// Pass diagConn to any framework (JPA, Spring JDBC, etc.)
```

For broader coverage, use `DiagnosticsDataSource` to wrap an entire `DataSource`.

**Best practice**: Enable in dev/test environments — there is some overhead. Pair with the N+1 avoidance patterns in [anti-patterns.md](anti-patterns.md).

---

## Pattern: ExecuteListener / CallbackExecuteListener for lifecycle hooks
**Source**: [Simulating Latency with SQL / JDBC](https://blog.jooq.org/simulating-latency-with-sql-jdbc) (2021-02-15)

Use `CallbackExecuteListener` (or implement `ExecuteListener`) to hook into every jOOQ statement execution. Useful for latency simulation, metrics, auditing, or any cross-cutting concern at the SQL execution boundary.

```kotlin
val ctx = DSL.using(
    DefaultConfiguration()
        .set(connection)
        .set(
            CallbackExecuteListener()
                .onExecuteStart { Thread.sleep(1000L) }
        )
)
```

Fires uniformly for all statement types (SELECT, INSERT, UPDATE, DELETE, DDL) — no query modification required.

**Best practice**: Use `onExecuteStart` for pre-execution hooks. Use `onExecuteEnd` for post-execution hooks (timing, metrics). Enable only in dev/test profiles — never in production.

---

## Pattern: DefaultConnection / DefaultPreparedStatement as JDBC proxy
**Source**: [Simulating Latency with SQL / JDBC](https://blog.jooq.org/simulating-latency-with-sql-jdbc) (2021-02-15)

jOOQ ships `DefaultConnection` and `DefaultPreparedStatement` convenience classes that delegate all methods to an underlying `Connection`/`PreparedStatement`. Override only the methods you need — useful for JDBC-level interceptors without a full proxy implementation.

```kotlin
val proxied = object : DefaultConnection(realConnection) {
    override fun prepareStatement(sql: String): PreparedStatement {
        Thread.sleep(1000L)
        return super.prepareStatement(sql)
    }
}
```

Works independently of jOOQ's query building — can wrap any JDBC `Connection` regardless of ORM.

---
