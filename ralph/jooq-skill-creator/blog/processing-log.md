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
| 13 | Maven Coordinates of the most popular JDBC Dri… | 2023-12-13 | skip           | -          | skipped | Reference list of JDBC driver Maven coords; no patterns              | | 2493bdd |
| 14 | To DAO or not to DAO                             | 2023-12-06 | jooq-api       | anti-patterns.md | merged  | Enriched N+1 entry: DAOs hide loops, prefer bulk SQL                 | | f063a3a |
| 15 | JDBC Connection URLs of the Most Popular RDBMS   | 2023-12-01 | skip           | -          | skipped | Reference lookup table of JDBC URLs/drivers; no patterns             | | bdcfec0 |
| 16 | How to Generate Package Private Code with jOOQ… | 2023-06-28 | jooq-api       | code-generator.md | added   | New topic file; visibility modifiers + custom generator strategies    | | 1e0329a |
| 17 | How to Pass a Table Valued Parameter to a T-SQ… | 2023-04-25 | jooq-api       | code-generator.md | merged  | SQL Server TVP wrappers via code generator; dialect-specific          | | e4cdde9 |
| 18 | How to Turn a List of Flat Elements into a Hie… | 2023-03-24 | jooq-api       | hierarchical-queries.md | added   | New topic; Records.intoHierarchy() collector (since 3.19)            | | 5959a3f |
| 19 | 3.18.0 Release with Support for more Diagnosti… | 2023-03-08 | skip           | -          | skipped | Release announcement; no actionable code patterns                    | | 9895c96 |
| 20 | How to use jOOQ's Converters with UNION Operat… | 2023-03-02 | jooq-api       | fetching-mapping.md | merged  | Converter+UNION pitfall: client-side vs server-side transforms       | | 5a1ec5f |

| 21 | How to Write a Derived Table in jOOQ             | 2023-02-24 | jooq-api       | derived-tables.md | added   | New topic; declare-before-use, field extraction for type safety       | | 3198aee |
| 22 | The Performance Impact of SQL's FILTER Clause    | 2023-02-06 | sql-pattern    | aggregate-functions.md | added   | New topic; FILTER ~8% faster than CASE on PG 15                      | | ed1afbd |
| 23 | Emulating Window Functions in MySQL 5.7          | 2023-01-20 | skip           | -          | skipped | MySQL 5.7 EOL workarounds; not relevant for modern databases         | | 24b28a4 |

---
**Run summary** (2026-02-20 18:28):
- Iterations this run: 3
- Duration: 1m 90s total
- Articles processed so far: 4 / 747
- Topic files: 5
- Open uncertainties: 1

---
**Run summary** (2026-02-20 18:40):
- Iterations this run: 11
- Duration: 9m 541s total
- Articles processed so far: 14 / 747
- Topic files: 6
- Open uncertainties: 1
