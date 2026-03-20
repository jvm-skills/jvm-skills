---
name: jooq-best-practices
description: Comprehensive jOOQ DSL best practices for Kotlin/Java. Use when writing jOOQ queries, mapping results, handling transactions, or designing repository layers.
---

# jOOQ Best Practices

Expert knowledge base for jOOQ 3.20 DSL usage, SQL patterns, and Kotlin integration.
Built from official docs + 783 blog articles (progressively updated).

## How to use

1. Reference the knowledge files below for patterns, best practices, and real-world examples
2. If you hit a compile error or conflict with a knowledge entry, use the **jOOQ MCP server** to check current syntax

## Knowledge base

<!-- This section is auto-updated by the Ralph processing loop -->
- [anti-patterns.md](knowledge/anti-patterns.md) — 20 "don't do this" rules: schema, SQL, jOOQ API, H2 compatibility modes; .eq() vs .equals(); noCondition() for dynamic SQL; always call .execute(); don't map relational→objects→JSON when SQL can produce JSON directly
- [multiset.md](knowledge/multiset.md) — Nested collections with MULTISET, JSON emulation
- [fetching-mapping.md](knowledge/fetching-mapping.md) — RecordMapper, fetchMap, fetchGroups, collect() with JDK Collectors, ad-hoc converters, dot-notation alias for nested class mapping, fetchSize() for JDBC fetch size
- [array-operations.md](knowledge/array-operations.md) — Array lambda functions (filter, map, match) with PostgreSQL emulation
- [merge-upsert.md](knowledge/merge-upsert.md) — SQL MERGE as RIGHT JOIN mental model, full sync with FULL JOIN in USING clause, AND conditions in WHEN clauses, Oracle/SQL Server dialect variants
- [implicit-joins.md](knowledge/implicit-joins.md) — Implicit/explicit path joins, join elimination, path correlation, to-many joins, ON-clause paths, synthetic FKs
- [code-generator.md](knowledge/code-generator.md) — Code generator configuration: visibility modifiers, custom strategies, TVP wrappers, version compatibility, forced types (incl. MySQL TINYINT(1)→Boolean), embedded types, schema mapping, Testcontainers code generation, LiquibaseDatabase, Meta.migrateTo() schema diffing
- [hierarchical-queries.md](knowledge/hierarchical-queries.md) — Records.intoHierarchy() collector, recursive CTEs for tree structures
- [derived-tables.md](knowledge/derived-tables.md) — Derived table declaration, type-safe column refs, simplification, LATERAL as local variables, asterisk().except()
- [aggregate-functions.md](knowledge/aggregate-functions.md) — FILTER vs CASE in aggregates, COUNT(*) vs COUNT(1), functional dependencies in GROUP BY, table-level grouping, REDUCE simulation via recursive CTE
- [logging.md](knowledge/logging.md) — LoggingConnection for SQL logging, DiagnosticsConnection for N+1 detection, ExecuteListener/CallbackExecuteListener for lifecycle hooks, DefaultConnection as JDBC proxy
- [native-sql-strategy.md](knowledge/native-sql-strategy.md) — When to use jOOQ DSL vs views/functions for complex static SQL
- [stored-procedures.md](knowledge/stored-procedures.md) — Calling procedures with default/named parameters; vendor-agnostic anonymous blocks, while_/for_ loops, and cross-dialect procedural logic
- [type-system.md](knowledge/type-system.md) — jOOQ type hierarchy: DSLContext vs DSL, Result vs Cursor, Converter vs Binding, AlwaysInlineBinding for skewed enums, Condition as Field<Boolean>; Oracle BINARY_DOUBLE vs NUMBER performance
- [dml-returning.md](knowledge/dml-returning.md) — RETURNING data from INSERT/UPDATE/DELETE across dialects, data change delta tables
- [computed-columns.md](knowledge/computed-columns.md) — Virtual client-side computed columns as reusable expressions, context-aware projections; DB-side GENERATED ALWAYS AS columns for constant FK values
- [transactions.md](knowledge/transactions.md) — Explicit programmatic transactions, NESTED savepoints, R2DBC reactive transactions
- [sequences.md](knowledge/sequences.md) — Fetching single/batch sequence values across dialects
- [qom-traverser.md](knowledge/qom-traverser.md) — Query Object Model inspection, expression tree traversal, SQL transformation with $replace()
- [spring-boot-config.md](knowledge/spring-boot-config.md) — DefaultConfigurationCustomizer for Spring Boot jOOQ config; MySQL allowMultiQueries flag; switching to commercial editions (exclude OSS, add org.jooq.pro)
- [parser.md](knowledge/parser.md) — Parser ignore comments, parsing connection for dialect translation, IN list padding, Oracle implicit-join-to-ANSI-JOIN transformation, online SQL translation tool
- [result-formatting.md](knowledge/result-formatting.md) — ASCII chart output, formatChart() for console visualization
- [sql-json.md](knowledge/sql-json.md) — jsonObject/jsonArrayAgg nesting pattern (3.14, superseded by MULTISET 3.15+); dialect pitfalls: MySQL type degradation, Oracle CLOB, GROUP_CONCAT truncation, NULL semantics
- [r2dbc-reactive.md](knowledge/r2dbc-reactive.md) — R2DBC setup, reactive query execution with Flux/Mono, automatic connection lifecycle management
- [pagination.md](knowledge/pagination.md) — Single-query pagination metadata (total rows, page number, last-page flag) via COUNT(*) OVER() in nested derived tables; deterministic ordering requirement
- [set-operations.md](knowledge/set-operations.md) — Table diff with EXCEPT/UNION vs FULL JOIN USING; NULL-safe comparison with IS NOT DISTINCT FROM; row value expression NULL semantics; INTERSECT precedence over UNION/EXCEPT; multi-column row() IN predicates
- [plain-sql-templating.md](knowledge/plain-sql-templating.md) — val() vs inline() (bind vs literal), plain SQL field/table/condition templates with SQL injection safety, name() for identifiers, keyword() for consistent rendering, text blocks for multi-line plain SQL, custom DSL wrapper helpers to encapsulate plain SQL templates
- [dynamic-sql.md](knowledge/dynamic-sql.md) — noCondition/trueCondition/falseCondition for optional predicates, conditional SELECT fields, conditional JOINs, conditional UNION branches
- [naming-conventions.md](knowledge/naming-conventions.md) — Table aliasing algorithm, semantic type prefixes, singular/plural consistency
- [window-functions.md](knowledge/window-functions.md) — DISTINCT ON emulation with FIRST_VALUE; LAST_VALUE IGNORE NULLS for gap-filling
- [predicates.md](knowledge/predicates.md) — Quantified LIKE ANY / LIKE ALL predicates replacing verbose OR chains

## Core rules (always apply)

- Target version: **jOOQ 3.20** on PostgreSQL
- Use jOOQ DSL in repository classes, never raw SQL in controllers/services
- Map results to Kotlin data classes
- Use `record.FIELD` not `record.get(field)` for type safety
- Use jOOQ-generated enums, don't replicate DB enums in Kotlin
- Prefer `fetchMap(KEY, VALUE)` with `coerceTo()` for aggregates
- Wrap multi-step DB operations in `@Transactional`
- Use `DSL.name("cte").as(select...)` for CTEs
- Use `EXISTS()` not `COUNT(*) > 0` for existence checks
- Prefer `COUNT(*)` over `COUNT(1)` — identical semantics but ~10% faster on PostgreSQL; use `count()` (no argument) in jOOQ DSL
- Use `NOT EXISTS` instead of `NOT IN` with nullable columns
- Prefer `UNION ALL` over `UNION` unless dedup is needed
- Prefer `FILTER (WHERE ...)` over `CASE` in aggregates — more readable and faster on PostgreSQL
- Always execute jOOQ queries through jOOQ — don't extract SQL for JDBC/JPA (loses MULTISET emulation, type-safe mapping, R2DBC)
- Test against the real target database (via Testcontainers), not H2 with compatibility modes
- Always call `.execute()` on DML/DDL — jOOQ's fluent API builds silently without it; use IntelliJ's `@CheckReturnValue` inspection to catch this
