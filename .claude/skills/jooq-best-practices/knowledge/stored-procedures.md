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
