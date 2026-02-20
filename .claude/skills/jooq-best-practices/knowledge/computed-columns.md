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

## Pattern: Computed columns are projections, not predicates
**Source**: [Create Dynamic Views with jOOQ 3.17's new Virtual Client Side Computed Columns](https://blog.jooq.org/create-dynamic-views-with-jooq-3-17s-new-virtual-client-side-computed-columns) (2022-06-30)

Computed columns cannot be indexed. Use them for SELECT projections and aggregations, not in WHERE clauses where performance matters.

---
