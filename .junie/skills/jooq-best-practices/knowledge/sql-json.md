# SQL/JSON Dialect Patterns & Pitfalls

## Pattern: Use jsonObject() + jsonArrayAgg() for server-side nested collection building
**Source**: [Nesting Collections With jOOQ 3.14's SQL/XML or SQL/JSON support](https://blog.jooq.org/nesting-collections-with-jooq-3-14s-sql-xml-or-sql-json-support) (2020-10-09)
**Since**: jOOQ 3.14

Build nested JSON structures entirely server-side to avoid N+1 and cartesian products. `jsonArrayAgg()` aggregates rows into a JSON array per group; `jsonObject()` shapes each row.

```kotlin
ctx.select(
    jsonObject(
        key("tableSchema").value(COLUMNS.TABLE_SCHEMA),
        key("tableName").value(COLUMNS.TABLE_NAME),
        key("columns").value(jsonArrayAgg(
            jsonObject(
                key("columnName").value(COLUMNS.COLUMN_NAME),
                key("type").value(jsonObject("name", COLUMNS.DATA_TYPE))
            )
        ).orderBy(COLUMNS.ORDINAL_POSITION))
    )
).from(COLUMNS)
 .groupBy(COLUMNS.TABLE_SCHEMA, COLUMNS.TABLE_NAME)
 .fetchInto(Table::class.java)
```

> **Supersedes**: For jOOQ 3.15+, prefer `MULTISET` ([multiset.md](multiset.md)) — it provides type-safe mapping without manual `key()/value()` wiring and handles dialect quirks automatically. Use `jsonArrayAgg()` directly only when targeting 3.14 or when you need fine-grained JSON key naming control.

---

## Pattern: SQL Server FOR XML / FOR JSON — jOOQ translates to other RDBMS
**Source**: [Using SQL Server FOR XML and FOR JSON Syntax on Other RDBMS With jOOQ](https://blog.jooq.org/using-sql-server-for-xml-and-for-json-syntax-on-other-rdbms-with-jooq) (2020-05-05)
**Since**: jOOQ 3.14
**Dialect**: SQL Server / PostgreSQL / Oracle / DB2 / MySQL / MariaDB

SQL Server's `FOR XML` (RAW, AUTO, PATH modes) and `FOR JSON PATH` syntaxes are proprietary, but jOOQ 3.14 can parse them and emit equivalent standard SQL/XML or SQL/JSON for other databases — enabling cross-database portability.

**FOR XML modes:**
- `RAW` — flat XML with one element per row, columns as attributes
- `AUTO` — hierarchy inferred from join order (tables become nested elements)
- `PATH` — explicit XML paths via slash-separated column aliases (`a.first_name AS [author/first_name]`)

**FOR JSON PATH** — same as PATH mode but produces JSON; use dot-notation for nesting (`a.first_name AS [author.first_name]`)

**Modifiers** (portable via jOOQ DSL):
- `ROOT('name')` — wraps output in a named root element/object
- `ELEMENTS` — XML: emit child elements instead of attributes
- `INCLUDE_NULL_VALUES` — JSON: include null keys instead of omitting them
- `WITHOUT_ARRAY_WRAPPER` — JSON: emit object(s) without outer array

Use the **jOOQ DSL** to write these queries — jOOQ emits the correct native syntax per dialect, or falls back to standard `XMLAGG(XMLELEMENT(...))` / `JSON_ARRAYAGG(JSON_OBJECT(...))` equivalents.

---

## Pattern: SQL/JSON support is highly inconsistent across vendors — prefer jOOQ DSL
**Source**: [Standard SQL/JSON – The Sobering Parts](https://blog.jooq.org/standard-sql-json-the-sobering-parts) (2021-07-27)
**Since**: jOOQ 3.14

SQL/JSON functions (`JSON_ARRAY`, `JSON_OBJECT`, `JSON_ARRAYAGG`) are part of the SQL standard but are implemented inconsistently across databases. Use jOOQ's SQL/JSON DSL instead of native SQL to get cross-database portability without writing dialect-specific workarounds.

**PostgreSQL**: Most robust implementation with native `JSON`/`JSONB` types — preferred target for SQL/JSON work.

**Dialect**: PostgreSQL / MySQL / MariaDB / Oracle / Db2 / SQL Server

---

## Pattern: MySQL/MariaDB JSON type degradation in nested derived tables
**Source**: [Standard SQL/JSON – The Sobering Parts](https://blog.jooq.org/standard-sql-json-the-sobering-parts) (2021-07-27)
**Dialect**: MySQL / MariaDB

MySQL and MariaDB lose the JSON type when JSON values come from derived tables — nested arrays become string representations: `["[1,2]",3]` instead of `[[1,2],3]`. This is a database bug, not a jOOQ issue.

**Implication**: Prefer MULTISET (jOOQ 3.15+) over raw SQL/JSON aggregation on MySQL/MariaDB — jOOQ's MULTISET emulation handles these quirks internally.

---

## Pattern: Oracle SQL/JSON requires RETURNING CLOB for large results
**Source**: [Standard SQL/JSON – The Sobering Parts](https://blog.jooq.org/standard-sql-json-the-sobering-parts) (2021-07-27)
**Dialect**: Oracle

Oracle defaults JSON to `VARCHAR2` (4000 bytes), causing `output value too large` errors on non-trivial aggregations. When writing raw SQL on Oracle, append `RETURNING CLOB` to every JSON function. jOOQ handles this automatically when using the DSL.

---

## Pattern: MySQL GROUP_CONCAT truncates silently — corrupts JSON
**Source**: [Standard SQL/JSON – The Sobering Parts](https://blog.jooq.org/standard-sql-json-the-sobering-parts) (2021-07-27)
**Dialect**: MySQL

MySQL uses `GROUP_CONCAT` to emulate `JSON_ARRAYAGG` internally, and `group_concat_max_len` defaults to a low system limit. Silent truncation produces invalid JSON with no error. Set the session variable before aggregating large JSON arrays:

```sql
SET SESSION group_concat_max_len = 18446744073709551615;
```

When using jOOQ's MULTISET emulation on MySQL, verify this is configured at the connection level (e.g., via a `ConnectionProvider` that sets the variable).

---

## Pattern: SQL NULL vs JSON null semantics differ across vendors
**Source**: [Standard SQL/JSON – The Sobering Parts](https://blog.jooq.org/standard-sql-json-the-sobering-parts) (2021-07-27)

SQL `NULL` and JSON `null` are distinct concepts. Behavior varies:
- Oracle may collapse JSON null values to SQL NULL through certain operations
- `JSON_ARRAYAGG` excludes SQL NULLs by default; use `NULL ON NULL` (Oracle syntax) to include them
- Use jOOQ's DSL to express null handling rather than relying on vendor defaults

---
