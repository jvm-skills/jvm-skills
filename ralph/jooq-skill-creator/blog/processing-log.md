# Ralph Processing Log

Auto-appended by each iteration. Captures data for the blog post.

| # | Article                                          | Date       | Classification | Topic File | Action  | Notes                                                                | Commit |
|---|--------------------------------------------------|------------|----------------|------------|---------|----------------------------------------------------------------------|--------|
| 1 | Consider using JSON arrays instead of JSON objec… | 2025-08-11 | jooq-api       | multiset.md | added   | Internal MULTISET serialization: arrays ~80% faster than objects      | |
| 2 | When SQL Meets Lambda Expressions                | 2025-03-27 | jooq-api       | array-operations.md | added   | Array lambdas (filter/map/match); PostgreSQL uses emulation          | |
| 3 | Think About SQL MERGE in Terms of a RIGHT JOIN   | 2025-03-13 | sql-pattern    | merge-upsert.md | added   | New topic file; MERGE as RIGHT JOIN mental model, PG17 BY SOURCE     | | 08b86c9 |
| 4 | Resisting the Urge to Document Everything Everyw… | 2025-02-28 | skip           | -          | skipped | Documentation philosophy / product management opinion piece          | | e476ffa |
| 5 | jOOQ 3.20 released with ClickHouse, Databricks,… | 2025-02-20 | skip           | -          | skipped | Release announcement; features listed without actionable code patterns | | a17231e |
| 6 | Emulating SQL FILTER with Oracle JSON Aggregate… | 2024-06-03 | skip           | -          | skipped | Oracle-specific FILTER emulation; PostgreSQL supports FILTER natively | | 3535c71 |
| 7 | Getting Top 1 Values Per Group in Oracle         | 2024-03-01 | skip           | -          | skipped | Oracle-specific KEEP syntax and OBJECT types; not applicable to PG   | | 5303663 |
| 8 | An Efficient Way to Check for Existence of Mult… | 2024-02-16 | sql-pattern    | anti-patterns.md | merged  | Extends EXISTS pattern: COUNT+LIMIT for N+ checks, ~2.5x on PG      | | 6ef9444 |
| 9 | A Hidden Benefit of Implicit Joins: Join Elimin… | 2024-01-10 | jooq-api       | implicit-joins.md | added   | New topic; path joins + auto join elimination (since 3.19)           | | 8abc86a |

| 10 | jOOQ 3.19's new Explicit and Implicit to-many… | 2023-12-28 | jooq-api       | implicit-joins.md | merged  | 3 new patterns: explicit path joins, path correlation, MULTISET+paths | 48005b6 |
| 11 | Workaround for MySQL's "can't specify target … | 2023-12-20 | skip           | -          | skipped | MySQL-only limitation; PostgreSQL not affected                        | | dd29204 |
| 12 | jOOQ 3.19.0 Released with DuckDB, Trino, Oracl… | 2023-12-15 | skip           | -          | skipped | Release announcement; join path features already in implicit-joins.md | | ac37ffc |

---
**Run summary** (2026-02-20 18:28):
- Iterations this run: 3
- Duration: 1m 90s total
- Articles processed so far: 4 / 747
- Topic files: 5
- Open uncertainties: 1
