# Code Generator Configuration

## Pattern: Package-private generated code
**Source**: [How to Generate Package Private Code with jOOQ's Code Generator](https://blog.jooq.org/how-to-generate-package-private-code-with-jooqs-code-generator) (2023-06-28)

Hide generated jOOQ code from client code using package-private visibility. Requires two steps:

1. **Custom strategy** — put all generated code in a single package:

```java
public class SinglePackageStrategy extends DefaultGeneratorStrategy {
    @Override
    public String getJavaPackageName(Definition definition, Mode mode) {
        return getTargetPackage();
    }
}
```

2. **Set visibility to NONE** in code generator config:

```xml
<generate>
  <visibilityModifier>NONE</visibilityModifier>
</generate>
```

Use `<clean>false</clean>` on the target to avoid deleting other files in the shared package. Strategy code can be declared inline in configuration since jOOQ 3.19.

**Since**: jOOQ 3.19 (inline strategy support)

---

## Pattern: Table-valued parameters via code generation
**Source**: [How to Pass a Table Valued Parameter to a T-SQL Function with jOOQ](https://blog.jooq.org/how-to-pass-a-table-valued-parameter-to-a-t-sql-function-with-jooq) (2023-04-25)
**Dialect**: SQL Server (T-SQL)

The code generator produces type-safe wrappers for T-SQL table-valued parameters (TVPs). For a user-defined table type and function:

```sql
CREATE TYPE u_number_table AS TABLE (column_value INTEGER);
CREATE FUNCTION f_cross_multiply (@numbers u_number_table READONLY)
RETURNS @result TABLE (i1 INTEGER, i2 INTEGER, product INTEGER) ...
```

jOOQ generates three artifacts:
- **Record type** (`UNumberTableRecord`) — represents the TVP
- **Element type** (`UNumberTableElementTypeRecord`) — models individual rows
- **Function wrapper** (`Routines.fCrossMultiply()`) — type-safe call

```java
List<Integer> l = List.of(1, 2, 3);
Result<FCrossMultiplyRecord> result = ctx
    .selectFrom(fCrossMultiply(new UNumberTableRecord(
        l.stream().map(UNumberTableElementTypeRecord::new).toList()
    )))
    .fetch();
```

This abstracts away native JDBC complexity (`SQLServerDataTable`) behind jOOQ's type-safe API.

---

## Pattern: Version compatibility between runtime and code generator
**Source**: [Cannot resolve symbol 'VERSION_3_17' in jOOQ generated code](https://blog.jooq.org/cannot-resolve-symbol-version_3_17-in-jooq-generated-code) (2022-08-30)
**Since**: jOOQ 3.16

Starting with jOOQ 3.16, generated code includes a version reference constant that triggers a compile-time error if the runtime version is older than the code generator version. This catches version mismatches early.

**Rules**:
- Generated code is **forward compatible** — older generators work with newer runtimes
- Runtime API is **backward compatible** — newer runtimes work with older generated code
- **Newer generators with older runtimes are NOT supported**

**Best practice**: always keep runtime version >= code generator version. Ideally, match both versions exactly.

To disable the check (not recommended):
```xml
<jooqVersionReference>false</jooqVersionReference>
```

---

## Pattern: Map MySQL TINYINT(1) to Boolean via forced types
**Source**: [How to Map MySQL's TINYINT(1) to Boolean in jOOQ](https://blog.jooq.org/how-to-map-mysqls-tinyint1-to-boolean-in-jooq) (2019-09-27)
**Since**: jOOQ 3.12
**Dialect**: MySQL / MariaDB

MySQL has no native `BOOLEAN` type — `BOOL` is an alias for `TINYINT(1)`. Use a forced type with `<includeTypes>` regex to rewrite `TINYINT(1)` columns to Java `boolean` during code generation:

```xml
<forcedTypes>
  <forcedType>
    <name>BOOLEAN</name>
    <includeTypes>(?i:TINYINT\(1\))</includeTypes>
  </forcedType>
</forcedTypes>
```

This enables type-safe predicates like `where(T.ACTIVE)` instead of treating the column as numeric.

---

## Pattern: Forced types for auto-applying converters
**Source**: [Why You Should Use jOOQ With Code Generation](https://blog.jooq.org/why-you-should-use-jooq-with-code-generation) (2021-12-06)

Instead of manually attaching converters to every column reference, configure them in the code generator via [forced types](https://www.jooq.org/doc/latest/manual/code-generation/codegen-advanced/codegen-config-database/codegen-database-forced-types/). The converter is then automatically applied to all matching columns across all generated code.

This is critical for converters implementing must-use logic (e.g., hashing, encryption) — the code generator guarantees no column is missed.

Without code gen, you'd manually declare each field:
```java
// Manual — error-prone, easy to forget
Field<LeFirstName> firstName = field("author.first_name",
    VARCHAR.asConvertedDataType(
        LeFirstName.class, LeFirstName::new, LeFirstName::firstName
    ));
```

With forced types in codegen config, you just use the generated field and the converter is applied automatically.

---

## Pattern: Embedded types for composite column groups
**Source**: [Why You Should Use jOOQ With Code Generation](https://blog.jooq.org/why-you-should-use-jooq-with-code-generation) (2021-12-06)

Embedded types combine multiple database columns into a single client-side value type, as if the database supported UDTs. Classic example: wrapping `AMOUNT` + `CURRENCY` columns into a `Money` type to prevent mixing `USD 1.00` with `EUR 1.00`.

Variants:
- **Embedded keys** — `BOOK.AUTHOR_ID` and `AUTHOR.ID` share a typed key, preventing comparison with unrelated ID columns
- **Embedded domains** — reuse semantic types declared via `CREATE DOMAIN` in client code

Embedded types are only available through the code generator, which produces the metadata needed for jOOQ's runtime to map/unmap flat result sets.

---

## Pattern: Testcontainers for code generation
**Source**: [Using Testcontainers to Generate jOOQ Code](https://blog.jooq.org/using-testcontainers-to-generate-jooq-code) (2021-08-27)

Use Testcontainers to spin up a real database during the build for jOOQ code generation — no pre-existing database required.

**Simple approach** — Testcontainers JDBC URL with init script:
```xml
<jdbc>
  <driver>org.testcontainers.jdbc.ContainerDatabaseDriver</driver>
  <url>jdbc:tc:postgresql:13:///mydb?TC_INITSCRIPT=file:${basedir}/src/main/resources/schema.sql</url>
</jdbc>
```

**Production approach** — Flyway + Testcontainers + jOOQ (Maven):
1. Start Testcontainers PostgreSQL via Groovy plugin, capture dynamic JDBC URL
2. Run Flyway migrations against the container
3. Run jOOQ code generation against the migrated schema
4. Optionally reuse the same container for integration tests

**Key advantages**: production-database parity, vendor-specific features work, reproducible CI builds. Eliminates the need for `DDLDatabase`, `JPADatabase`, or `XMLDatabase` workarounds.

> **Supersedes**: older `DDLDatabase`/`JPADatabase` approaches that couldn't leverage vendor-specific features

---

## Pattern: LiquibaseDatabase for code generation without a running database
**Source**: [jOOQ 3.13 Released with More API and Tooling for DDL Management](https://blog.jooq.org/jooq-3-13-released-with-more-api-and-tooling-for-ddl-management) (2020-02-14)
**Since**: jOOQ 3.13

Use `LiquibaseDatabase` to simulate Liquibase migrations in-memory for jOOQ code generation — no real database connection required. The database schema is derived directly from Liquibase changelogs at code-gen time.

```xml
<generator>
  <database>
    <name>org.jooq.meta.extensions.liquibase.LiquibaseDatabase</name>
    <properties>
      <property>
        <key>scripts</key>
        <value>src/main/resources/db/changelog/db.changelog-master.xml</value>
      </property>
    </properties>
  </database>
</generator>
```

Useful in CI or offline environments where spinning up a Testcontainers database is not feasible.

---

## Pattern: Programmatic schema diffing with Meta.migrateTo()
**Source**: [jOOQ 3.13 Released with More API and Tooling for DDL Management](https://blog.jooq.org/jooq-3-13-released-with-more-api-and-tooling-for-ddl-management) (2020-02-14)
**Since**: jOOQ 3.13

Use `Meta.migrateTo(Meta)` to compare two schema states and generate a migration script programmatically. Useful for custom migration tooling or schema drift detection.

```java
// Compare live database schema against target DDL
Meta current = DSL.using(connection).meta();
Meta target  = DSL.using(connection).meta(targetDDL); // or from another source
Queries migration = current.migrateTo(target);

// Render and execute the migration
for (Query q : migration) {
    System.out.println(ctx.renderInlined(q));
}
```

---

## Pattern: Schema mapping for multitenancy
**Source**: [Why You Should Use jOOQ With Code Generation](https://blog.jooq.org/why-you-should-use-jooq-with-code-generation) (2021-12-06)

jOOQ supports schema-level multitenancy via **schema mapping** — dynamically renaming catalogs, schemas, and table names at runtime per tenant. This requires generated code because:

1. Generated objects are fully qualified by default (catalog.schema.table)
2. Schema mapping intercepts these qualified names and remaps them at runtime
3. Plain SQL templates bypass this mechanism entirely

This enables porting a schema from one namespace to another via configuration, without rewriting queries.

---
