# UpdatableRecord CRUD

## Pattern: Delta updates via changed() tracking
**Source**: [How to Use jOOQ's UpdatableRecord for CRUD to Apply a Delta](https://blog.jooq.org/how-to-use-jooqs-updatablerecord-for-crud-to-apply-a-delta) (2018-11-05)

`UpdatableRecord` tracks which fields were explicitly set via `Record.changed()`. Only changed fields are included in INSERT/UPDATE statements, allowing:
- SQL `DEFAULT` values to apply for unset INSERT columns
- Partial updates without overwriting untouched columns
- Semantic distinction between explicit `NULL` and absent/undefined values

```kotlin
val customer = ctx.newRecord(CUSTOMER)
customer.firstName = "John"
customer.lastName = "Doe"
customer.store()
// INSERT INTO customer (first_name, last_name) VALUES (?, ?)
// Omits unset columns — DB DEFAULTs apply
```

---

## Pattern: Avoid POJO round-trips for partial updates
**Source**: [How to Use jOOQ's UpdatableRecord for CRUD to Apply a Delta](https://blog.jooq.org/how-to-use-jooqs-updatablerecord-for-crud-to-apply-a-delta) (2018-11-05)

Loading a POJO into a record via `ctx.newRecord(TABLE, pojo)` sets **all** `changed()` flags to true, forcing all fields into the UPDATE — even null ones. This loses the null-vs-undefined distinction.

```kotlin
// Bad: POJO loses delta semantics — all fields included in UPDATE
val record = ctx.newRecord(CUSTOMER, customerPojo)
record.update() // UPDATE customer SET first_name=?, last_name=?, email=?, ... WHERE id=?

// Good: load only the fields you have, keep others unchanged
val record = ctx.fetchOne(CUSTOMER, CUSTOMER.ID.eq(id))!!
record.firstName = incoming.firstName
record.store() // Only updates fields you touched
```

---

## Pattern: Respect DB DEFAULT values on INSERT
**Source**: [How to Use jOOQ's UpdatableRecord for CRUD to Apply a Delta](https://blog.jooq.org/how-to-use-jooqs-updatablerecord-for-crud-to-apply-a-delta) (2018-11-05)

Using `UpdatableRecord.store()` on a freshly created record (not fetched from DB) omits unset columns from the INSERT, so database `DEFAULT` expressions (timestamps, sequences, generated values) apply naturally. No need to manually set columns that have DB defaults.

```kotlin
val order = ctx.newRecord(ORDER)
order.customerId = 42
// order.createdAt NOT set — DB DEFAULT NOW() will be applied
order.store()
```

---
