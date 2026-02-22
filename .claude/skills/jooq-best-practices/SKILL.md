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
- [anti-patterns.md](knowledge/anti-patterns.md) — 18 "don't do this" rules: schema, SQL, jOOQ API, H2 compatibility modes; .eq() vs .equals(); noCondition() for dynamic SQL
- [multiset.md](knowledge/multiset.md) — Nested collections with MULTISET, JSON emulation
- [fetching-mapping.md](knowledge/fetching-mapping.md) — RecordMapper, fetchMap, fetchGroups, ad-hoc converters
- [array-operations.md](knowledge/array-operations.md) — Array lambda functions (filter, map, match) with PostgreSQL emulation
- [merge-upsert.md](knowledge/merge-upsert.md) — SQL MERGE as RIGHT JOIN mental model, staging table sync patterns
- [implicit-joins.md](knowledge/implicit-joins.md) — Implicit/explicit path joins, join elimination, path correlation, to-many joins, ON-clause paths, synthetic FKs
- [code-generator.md](knowledge/code-generator.md) — Code generator configuration: visibility modifiers, custom strategies, TVP wrappers, version compatibility, forced types, embedded types, schema mapping, Testcontainers code generation
- [hierarchical-queries.md](knowledge/hierarchical-queries.md) — Records.intoHierarchy() collector, recursive CTEs for tree structures
- [derived-tables.md](knowledge/derived-tables.md) — Derived table declaration, type-safe column refs, simplification, LATERAL as local variables, asterisk().except()
- [aggregate-functions.md](knowledge/aggregate-functions.md) — FILTER vs CASE in aggregates, functional dependencies in GROUP BY, table-level grouping
- [logging.md](knowledge/logging.md) — LoggingConnection for SQL logging, DiagnosticsConnection for N+1 detection
- [native-sql-strategy.md](knowledge/native-sql-strategy.md) — When to use jOOQ DSL vs views/functions for complex static SQL
- [stored-procedures.md](knowledge/stored-procedures.md) — Calling procedures with default/named parameters; vendor-agnostic anonymous blocks and procedural logic
- [type-system.md](knowledge/type-system.md) — jOOQ type hierarchy: DSLContext vs DSL, Result vs Cursor, Converter vs Binding, Condition as Field<Boolean>
- [dml-returning.md](knowledge/dml-returning.md) — RETURNING data from INSERT/UPDATE/DELETE across dialects, data change delta tables
- [computed-columns.md](knowledge/computed-columns.md) — Virtual client-side computed columns as reusable expressions, context-aware projections
- [transactions.md](knowledge/transactions.md) — Explicit programmatic transactions, NESTED savepoints, R2DBC reactive transactions
- [sequences.md](knowledge/sequences.md) — Fetching single/batch sequence values across dialects
- [qom-traverser.md](knowledge/qom-traverser.md) — Query Object Model inspection, expression tree traversal, SQL transformation with $replace()
- [spring-boot-config.md](knowledge/spring-boot-config.md) — DefaultConfigurationCustomizer for Spring Boot jOOQ config; MySQL allowMultiQueries flag
- [parser.md](knowledge/parser.md) — Parser ignore comments, parsing connection for automatic dialect translation
- [result-formatting.md](knowledge/result-formatting.md) — ASCII chart output, formatChart() for console visualization
- [sql-json.md](knowledge/sql-json.md) — SQL/JSON dialect pitfalls: MySQL type degradation, Oracle CLOB, GROUP_CONCAT truncation, NULL semantics

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
- Use `NOT EXISTS` instead of `NOT IN` with nullable columns
- Prefer `UNION ALL` over `UNION` unless dedup is needed
- Prefer `FILTER (WHERE ...)` over `CASE` in aggregates — more readable and faster on PostgreSQL
- Always execute jOOQ queries through jOOQ — don't extract SQL for JDBC/JPA (loses MULTISET emulation, type-safe mapping, R2DBC)
- Test against the real target database (via Testcontainers), not H2 with compatibility modes
