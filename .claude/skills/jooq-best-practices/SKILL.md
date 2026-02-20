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
- [anti-patterns.md](knowledge/anti-patterns.md) — 15 "don't do this" rules from official docs (schema + SQL + jOOQ API)
- [multiset.md](knowledge/multiset.md) — Nested collections with MULTISET, JSON emulation
- [fetching-mapping.md](knowledge/fetching-mapping.md) — RecordMapper, fetchMap, fetchGroups, ad-hoc converters
- [array-operations.md](knowledge/array-operations.md) — Array lambda functions (filter, map, match) with PostgreSQL emulation
- [merge-upsert.md](knowledge/merge-upsert.md) — SQL MERGE as RIGHT JOIN mental model, staging table sync patterns
- [implicit-joins.md](knowledge/implicit-joins.md) — Implicit/explicit path joins, join elimination, path correlation, to-many joins

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
