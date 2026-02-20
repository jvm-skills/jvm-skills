# Transactions

## Pattern: Explicit programmatic transactions
**Source**: [Nested Transactions in jOOQ](https://blog.jooq.org/nested-transactions-in-jooq) (2022-04-28)
**Since**: jOOQ 3.4 (JDBC), jOOQ 3.17 (R2DBC)

jOOQ provides explicit, API-based transaction management. Blocks commit on normal completion, rollback on uncaught exceptions.

```java
ctx.transaction(trx -> {
    trx.dsl()
       .insertInto(AUTHOR)
       .columns(AUTHOR.ID, AUTHOR.FIRST_NAME, AUTHOR.LAST_NAME)
       .values(1, "Tayo", "Koleoso")
       .execute();

    trx.dsl()
       .insertInto(BOOK)
       .columns(BOOK.ID, BOOK.AUTHOR_ID, BOOK.TITLE)
       .values(1, 1, "Beginning jOOQ")
       .execute();
});
```

**Key**: Always use `trx.dsl()` inside the lambda, not the outer `ctx` — `trx.dsl()` carries the transactional connection.

---

## Pattern: Nested transactions with savepoints
**Source**: [Nested Transactions in jOOQ](https://blog.jooq.org/nested-transactions-in-jooq) (2022-04-28)
**Since**: jOOQ 3.4

jOOQ uses `Propagation.NESTED` by default (not `REQUIRED` like Spring). Nested `transaction()` calls create savepoints, so a failed inner block only rolls back to its savepoint.

```java
ctx.transaction(trx -> {
    trx.dsl().transaction(trx1 -> {
        // trx1 work — committed to savepoint
    });

    try {
        trx.dsl().transaction(trx2 -> {
            // trx2 fails — only this savepoint rolls back
            throw new RuntimeException("oops");
        });
    } catch (Exception e) {
        log.info("trx2 failed, trx1 preserved", e);
    }

    // trx1's work is still intact
    continueWork(trx);
});
```

**Why NESTED over REQUIRED**: Explicit nesting reflects programmer intent. If you nest transactions, you want savepoint isolation — not silent merging into the parent.

---

## Pattern: Exception handling within transactions
**Source**: [Nested Transactions in jOOQ](https://blog.jooq.org/nested-transactions-in-jooq) (2022-04-28)

Caught exceptions do NOT trigger rollback. Only uncaught exceptions propagating out of the `transaction()` lambda cause rollback.

```java
ctx.transaction(trx -> {
    try {
        trx.dsl().insertInto(AUTHOR).columns(...).values(...).execute();
    } catch (DataAccessException e) {
        if (e.sqlStateClass() != C23_INTEGRITY_CONSTRAINT_VIOLATION)
            throw e;
        // Constraint violation handled — no rollback
    }

    // Subsequent work continues normally
    trx.dsl().insertInto(BOOK).columns(...).values(...).execute();
});
```

---

## Pattern: R2DBC reactive transactions
**Source**: [Nested Transactions in jOOQ](https://blog.jooq.org/nested-transactions-in-jooq) (2022-04-28)
**Since**: jOOQ 3.17

Reactive transactions use `transactionPublisher()` with the same NESTED semantics:

```java
Flux<?> flux = Flux.from(ctx.transactionPublisher(trx -> Flux
    .from(trx.dsl()
        .insertInto(AUTHOR).columns(...).values(...))
    .thenMany(trx.dsl()
        .insertInto(BOOK).columns(...).values(...))
));
```

Nested reactive transactions compose via `thenMany()`:

```java
Flux.from(ctx.transactionPublisher(trx -> Flux
    .from(trx.dsl().transactionPublisher(trx1 -> { /* ... */ }))
    .thenMany(Flux
        .from(trx.dsl().transactionPublisher(trx2 -> { /* ... */ }))
        .onErrorContinue((e, t) -> log.info(e)))
));
```

---
