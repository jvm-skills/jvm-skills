# SQL/JSON Dialect Patterns & Pitfalls

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
