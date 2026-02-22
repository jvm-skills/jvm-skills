# Stored Procedures

## Pattern: Default parameters with named parameter syntax
**Source**: [Calling Procedures with Default Parameters using JDBC or jOOQ](https://blog.jooq.org/calling-procedures-with-default-parameters-using-jdbc-or-jooq) (2022-10-21)

When a stored procedure has parameters with default values, instantiate the generated procedure class directly instead of using the static `Routines` shortcut. Set only the parameters you need, then call `execute()`:

```java
// Instead of Routines.p(configuration, 1, "A") which requires ALL params:
P p = new P();
p.setPI1(2);       // only set what you need
p.execute(configuration);
// p.getPO1() / p.getPO2() for OUT params
```

jOOQ renders an anonymous block with **named parameter syntax** instead of JDBC escape syntax, allowing defaulted parameters to be omitted:

```sql
begin
  "TEST"."P" ("P_I1" => ?, "P_O1" => ?, "P_O2" => ?)
end;
```

**Dialect**: Db2, Informix, Oracle, PostgreSQL (PL/pgSQL), SQL Server — all support named parameter calls with defaults.

---

## Pattern: Integration testing stored procedures with Routines + Testcontainers
**Source**: [How to Integration Test Stored Procedures with jOOQ](https://blog.jooq.org/how-to-integration-test-stored-procedures-with-jooq) (2022-08-22)

Use jOOQ's code-generated `Routines` class for type-safe, one-liner invocations of stored procedures in integration tests, replacing verbose JDBC `CallableStatement` boilerplate:

```java
// Type-safe — generated from the DB schema
assertEquals(3, Routines.add(ctx.configuration(), 1, 2));
```

Pair with Testcontainers for a fully automated test lifecycle (container startup → schema migration → code generation → test execution). Reuse the same Testcontainers instance between jOOQ code generation and test execution to avoid duplicate infrastructure.

---

## Pattern: Vendor-agnostic anonymous blocks and procedural logic
**Source**: [Vendor Agnostic, Dynamic Procedural Logic with jOOQ](https://blog.jooq.org/vendor-agnostic-dynamic-procedural-logic-with-jooq) (2021-08-25)
**Since**: jOOQ 3.12

jOOQ can generate and execute anonymous procedural blocks across Db2, Firebird, MariaDB, Oracle, PostgreSQL, and SQL Server — each with different native syntax, all abstracted away.

Use `DSLContext.begin(statements...)` to execute an anonymous block. jOOQ translates to the appropriate dialect (`DO $$...$$` for PostgreSQL, `BEGIN...END` for Oracle, etc.):

```java
Variable<Integer> i = variable(unquotedName("i"), INTEGER);
ctx.begin(
    declare(i).set(1),
    while_(i.le(10)).loop(
        insertInto(T).columns(C).values(i),
        i.set(i.plus(1))
    )
).execute();
```

Create vendor-agnostic stored procedures dynamically:

```java
ctx.createProcedure(p)
   .modifiesSQLData()
   .as(declare(i).set(1), while_(i.le(10)).loop(...))
   .execute();

// Call via anonymous block
ctx.begin(call(unquotedName("p"))).execute();
```

**Key rule**: Prefer SQL (4GL) over procedural logic where possible. Use anonymous blocks only when the algorithm genuinely requires procedural constructs (loops, variables, conditional branching).

**Use cases**: multi-vendor product deployments, runtime-generated procedural logic, environments with limited DDL privileges.

---
