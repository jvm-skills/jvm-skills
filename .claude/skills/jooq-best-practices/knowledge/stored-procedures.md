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
