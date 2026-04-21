# Client-Side Computed Columns

## Pattern: Virtual client-side computed columns as reusable expressions
**Source**: [Create Dynamic Views with jOOQ 3.17's new Virtual Client Side Computed Columns](https://blog.jooq.org/create-dynamic-views-with-jooq-3-17s-new-virtual-client-side-computed-columns) (2022-06-30)
**Since**: jOOQ 3.17

Declare synthetic columns that don't exist in the database but are computed by jOOQ at query time. They act as reusable expression "variables" expanded transparently into SQL.

**Step 1** — Declare the synthetic column in code generator config:

```xml
<syntheticObjects>
    <columns>
        <column>
            <tables>customer|staff|store</tables>
            <name>full_name</name>
            <type>text</type>
        </column>
    </columns>
</syntheticObjects>
```

**Step 2** — Define the generator expression via `forcedTypes`:

```xml
<forcedTypes>
    <forcedType>
        <generator>ctx -> DSL.concat(
            FIRST_NAME, DSL.inline(" "), LAST_NAME)
        </generator>
        <includeExpression>full_name</includeExpression>
    </forcedType>
</forcedTypes>
```

**Usage** — reference like any real column:

```java
ctx.select(CUSTOMER.FULL_NAME, CUSTOMER.FULL_ADDRESS)
   .from(CUSTOMER)
   .fetch();
```

jOOQ expands computed columns into their underlying expressions and only includes necessary joins when the column is actually selected.

---

## Pattern: Computed columns with implicit joins
**Source**: [Create Dynamic Views with jOOQ 3.17's new Virtual Client Side Computed Columns](https://blog.jooq.org/create-dynamic-views-with-jooq-3-17s-new-virtual-client-side-computed-columns) (2022-06-30)
**Since**: jOOQ 3.17

Generator expressions can use implicit join paths to traverse relationships:

```xml
<generator>ctx -> DSL.concat(
    address().ADDRESS_,
    DSL.inline(", "), address().POSTAL_CODE,
    DSL.inline(", "), address().city().CITY_,
    DSL.inline(", "), address().city().country().COUNTRY_
)</generator>
```

jOOQ resolves the joins automatically. When the column isn't selected, those joins are eliminated entirely.

---

## Pattern: Context-aware computed columns via Configuration.data()
**Source**: [Create Dynamic Views with jOOQ 3.17's new Virtual Client Side Computed Columns](https://blog.jooq.org/create-dynamic-views-with-jooq-3-17s-new-virtual-client-side-computed-columns) (2022-06-30)
**Since**: jOOQ 3.17

The `ctx` parameter in generators provides access to runtime configuration data, enabling dynamic computation based on session context:

```xml
<generator>ctx -> AMOUNT.times(DSL.field(
    DSL.select(CONVERSION.RATE)
       .from(CONVERSION)
       .where(CONVERSION.FROM_CURRENCY.eq(CURRENCY))
       .and(CONVERSION.TO_CURRENCY.eq(
           (String) ctx.configuration().data("USER_CURRENCY")))))
</generator>
```

Set the context before querying:

```java
ctx.configuration().data("USER_CURRENCY", "CHF");
ctx.select(TRANSACTION.AMOUNT, TRANSACTION.AMOUNT_USER_CURRENCY)
   .from(TRANSACTION)
   .fetch();
```

This creates dynamic "views" that adapt to user preferences without database-side changes.

---

## Pattern: Database-side generated columns for constant values in composite foreign keys
**Source**: [Having "constant" columns in foreign keys](https://blog.jooq.org/having-constant-columns-in-foreign-keys) (2020-09-10)
**Dialect**: DB2, MySQL, Oracle, PostgreSQL 12+, SQL Server

When a referencing table always uses a fixed value for one column of a composite foreign key (e.g., a discriminator in single-table inheritance), use a `GENERATED ALWAYS AS` column to enforce that constraint at the database level:

```sql
-- Parent table with composite PK
CREATE TABLE t1 (
  a INT,
  b INT,
  PRIMARY KEY (a, b)
);

-- Child table always references b = 1
CREATE TABLE t2 (
  a INT,
  b INT GENERATED ALWAYS AS (1) STORED,
  FOREIGN KEY (a, b) REFERENCES t1
);
```

Advantages over `DEFAULT 1 CHECK (b = 1)`:
- Database guarantees the value is immutable — cannot be changed even with an explicit UPDATE
- Cleaner intent: the column is definitionally constant, not just defaulted

> **Note**: PostgreSQL 12+ only supports `STORED` generated columns (materialized on disk). `VIRTUAL` (computed on read) is not yet available as of PostgreSQL 16.

---

## Pattern: Computed columns are projections, not predicates
**Source**: [Create Dynamic Views with jOOQ 3.17's new Virtual Client Side Computed Columns](https://blog.jooq.org/create-dynamic-views-with-jooq-3-17s-new-virtual-client-side-computed-columns) (2022-06-30)

Computed columns cannot be indexed. Use them for SELECT projections and aggregations, not in WHERE clauses where performance matters.

---
