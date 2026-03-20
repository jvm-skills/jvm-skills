# R2DBC Reactive SQL

## Pattern: DSLContext with R2DBC ConnectionFactory
**Source**: [Reactive SQL with jOOQ 3.15 and R2DBC](https://blog.jooq.org/reactive-sql-with-jooq-3-15-and-r2dbc) (2021-07-15)
**Since**: jOOQ 3.15

Configure `DSLContext` with an R2DBC `ConnectionFactory` instead of a JDBC `DataSource`. The API is otherwise identical to JDBC setup.

```java
ConnectionFactory connectionFactory = ConnectionFactories.get(
    ConnectionFactoryOptions
        .parse("r2dbc:postgresql://localhost/mydb")
        .mutate()
        .option(ConnectionFactoryOptions.USER, "user")
        .option(ConnectionFactoryOptions.PASSWORD, "password")
        .build()
);

DSLContext ctx = DSL.using(connectionFactory);
```

Supported drivers: PostgreSQL, MySQL, MariaDB, H2, MSSQL, Oracle.

---

## Pattern: Reactive query execution with Flux
**Source**: [Reactive SQL with jOOQ 3.15 and R2DBC](https://blog.jooq.org/reactive-sql-with-jooq-3-15-and-r2dbc) (2021-07-15)
**Since**: jOOQ 3.15

Queries return `Publisher<R>` — wrap in `Flux` (or `Mono`) for reactive-streams integration. Do not call blocking `.execute()` / `.fetch()`.

```java
Flux.from(ctx
    .select(BOOK.TITLE, AUTHOR.FIRST_NAME, AUTHOR.LAST_NAME)
    .from(BOOK)
    .join(AUTHOR).on(BOOK.AUTHOR_ID.eq(AUTHOR.ID)))
    .map(Records.mapping(Book::new))
    .subscribe(System.out::println);
```

DML queries return `Publisher<Integer>` (rows affected):

```java
Mono.from(ctx
    .insertInto(AUTHOR)
    .columns(AUTHOR.FIRST_NAME, AUTHOR.LAST_NAME)
    .values("Jane", "Doe"))
    .subscribe();
```

---

## Pattern: Automatic R2DBC connection lifecycle management
**Source**: [Reactive SQL with jOOQ 3.15 and R2DBC](https://blog.jooq.org/reactive-sql-with-jooq-3-15-and-r2dbc) (2021-07-15)
**Since**: jOOQ 3.15

jOOQ automatically acquires a connection from the `ConnectionFactory` when the publisher is subscribed to, and releases it on completion or error. No need for manual `Flux.usingWhen()` connection management.

For reactive transactions, see [transactions.md](transactions.md) — use `transactionPublisher()` (available since jOOQ 3.17).

---
