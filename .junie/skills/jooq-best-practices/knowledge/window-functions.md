# Window Functions

## Pattern: Emulate DISTINCT ON with FIRST_VALUE for portability
**Source**: [Using DISTINCT ON in Non-PostgreSQL Databases](https://blog.jooq.org/using-distinct-on-in-non-postgresql-databases) (2019-09-09)

PostgreSQL's `DISTINCT ON (col)` keeps the first row per group ordered by an `ORDER BY` clause. The portable equivalent uses `FIRST_VALUE` window functions, which jOOQ supports across all modern dialects.

```kotlin
// PostgreSQL-only: DISTINCT ON
// SELECT DISTINCT ON (location) location, time, report
// FROM weather_reports ORDER BY location, time DESC

// Portable: FIRST_VALUE window function
ctx.select(
    WEATHER_REPORTS.LOCATION.`as`("location"),
    DSL.firstValue(WEATHER_REPORTS.TIME)
        .over(DSL.partitionBy(WEATHER_REPORTS.LOCATION)
                  .orderBy(WEATHER_REPORTS.TIME.desc()))
        .`as`("time"),
    DSL.firstValue(WEATHER_REPORTS.REPORT)
        .over(DSL.partitionBy(WEATHER_REPORTS.LOCATION)
                  .orderBy(WEATHER_REPORTS.TIME.desc()))
        .`as`("report")
)
.from(WEATHER_REPORTS)
.orderBy(WEATHER_REPORTS.LOCATION)
.fetch()
```

Add `DSL.selectDistinct()` on the outer query to collapse duplicate rows produced by the window functions across the full result set.

**Dialect**: PostgreSQL supports native `DISTINCT ON`; for all other databases use `FIRST_VALUE` + `DISTINCT`.
**Note**: jOOQ supports PostgreSQL's `DISTINCT ON` natively via `selectDistinct(...).on(...)` for PostgreSQL targets. Use the `FIRST_VALUE` approach when targeting multiple dialects.

---

## Pattern: Forward-fill gaps with LAST_VALUE IGNORE NULLS
**Source**: [Using IGNORE NULLS With SQL Window Functions to Fill Gaps](https://blog.jooq.org/using-ignore-nulls-with-sql-window-functions-to-fill-gaps) (2019-04-24)

To forward-fill missing values in sparse time-series data, generate the full date range and join it with the sparse data, then use `LAST_VALUE(col) IGNORE NULLS` to carry forward the most recent non-null value.

```kotlin
// Generate date range (PostgreSQL: use generate_series; Oracle: CONNECT BY)
// Then left-join and use lastValue with ignoreNulls

ctx.select(
    dates.VALUE_DATE,
    DSL.lastValue(T.VALUE).ignoreNulls()
        .over(DSL.orderBy(dates.VALUE_DATE))
)
.from(dates)
.leftJoin(T).on(dates.VALUE_DATE.eq(T.VALUE_DATE))
.orderBy(dates.VALUE_DATE)
.fetch()
```

`IGNORE NULLS` skips null values in the window, so the function returns the last seen non-null value rather than null for gap rows.

**Dialect**: Supported in DB2, H2, Informix, Oracle, Redshift, Sybase SQL Anywhere, Teradata. For PostgreSQL/SQL Server, use recursive CTEs as fallback.

---

## Pattern: Cumulative percentage with nested window aggregates
**Source**: [How to Calculate a Cumulative Percentage in SQL](https://blog.jooq.org/how-to-calculate-a-cumulative-percentage-in-sql) (2019-02-14)

Compute what percentage of total revenue (or any metric) has accumulated by each row using two window functions: a running `SUM OVER (ORDER BY ...)` for the cumulative total and an unbounded `SUM OVER ()` for the grand total. The ratio × 100 gives the cumulative percentage.

A concise version uses **nested aggregate-inside-window** syntax — `sum(sum(amount)) OVER (...)` — which works because aggregates logically execute before window functions:

```kotlin
ctx.select(
    PAYMENT.PAYMENT_DATE.cast(SQLDataType.LOCALDATE).`as`("payment_date"),
    sum(PAYMENT.AMOUNT).`as`("amount"),
    (sum(sum(PAYMENT.AMOUNT))
        .over(DSL.orderBy(PAYMENT.PAYMENT_DATE.cast(SQLDataType.LOCALDATE)))
        .divide(sum(sum(PAYMENT.AMOUNT)).over())
        .times(inline(BigDecimal(100))))
        .cast(SQLDataType.NUMERIC(10, 2))
        .`as`("percentage")
)
.from(PAYMENT)
.groupBy(PAYMENT.PAYMENT_DATE.cast(SQLDataType.LOCALDATE))
.orderBy(PAYMENT.PAYMENT_DATE.cast(SQLDataType.LOCALDATE))
.fetch()
```

Or as a two-step approach with a derived table:

```kotlin
val p = ctx.select(
    PAYMENT.PAYMENT_DATE.cast(SQLDataType.LOCALDATE).`as`("payment_date"),
    sum(PAYMENT.AMOUNT).`as`("amount")
)
.from(PAYMENT)
.groupBy(PAYMENT.PAYMENT_DATE.cast(SQLDataType.LOCALDATE))
.asTable("p")

val paymentDate = p.field("payment_date", SQLDataType.LOCALDATE)!!
val amount = p.field("amount", SQLDataType.DECIMAL)!!

ctx.select(
    paymentDate,
    amount,
    (sum(amount).over(DSL.orderBy(paymentDate))
        .divide(sum(amount).over())
        .times(inline(BigDecimal(100))))
        .cast(SQLDataType.NUMERIC(10, 2))
        .`as`("percentage")
)
.from(p)
.orderBy(paymentDate)
.fetch()
```

**Key insight**: `SUM(col) OVER (ORDER BY ...)` = running total; `SUM(col) OVER ()` = grand total. Nested aggregates (`sum(sum(...))`) eliminate the subquery when already in a `GROUP BY` query.

---
