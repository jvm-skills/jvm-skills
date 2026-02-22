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
| 24 | Why You Should Execute jOOQ Queries With jOOQ    | 2023-01-18 | jooq-api       | anti-patterns.md | merged  | Core anti-pattern: don't extract SQL for JDBC/JPA; new core rule added | | 6a9a02c |
| 25 | jOOQ's R2DBC LoggingConnection to log all SQL… | 2023-01-17 | jooq-api       | logging.md | added   | New topic file; R2DBC LoggingConnection proxy (since 3.18)            | | 45774fe |
| 26 | When to Use jOOQ and When to Use Native SQL      | 2022-12-08 | jooq-api       | native-sql-strategy.md | added   | New topic file; hybrid approach: views/functions for complex static SQL | | 358c6d4 |
| 27 | LATERAL is Your Friend to Create Local Column… | 2022-11-04 | sql-pattern    | derived-tables.md | merged  | LATERAL as local column variables; CROSS APPLY for SQL Server/Oracle  | | 87215bc |
| 28 | Calling Procedures with Default Parameters us… | 2022-10-21 | jooq-api       | stored-procedures.md | added   | New topic; named param syntax for default args across 5 dialects      | |
| 29 | Using jOOQ's Implicit Join From Within the JO… | 2022-09-13 | jooq-api       | implicit-joins.md | merged  | ON-clause implicit paths + synthetic FK config; complements 3.19 entries | | 8d59049 | 17a3ddf |
| 30 | A Brief Overview over the Most Common jOOQ Ty… | 2022-09-06 | jooq-api       | type-system.md | added   | New topic file; type hierarchy cheat sheet: Step types, DSL vs DSLContext, Result vs Cursor | | 685b558 |
| 31 | How to Plot an ASCII Bar Chart with SQL         | 2022-09-01 | skip           | -          | skipped | Novelty ASCII chart rendering; underlying SQL primitives already known | | cde8be2 |
| 32 | The Second Best Way to Fetch a Spring Data JP… | 2022-08-30 | jooq-api       | multiset.md | merged  | MULTISET+mapping() DTO projection & MULTISET_AGG pattern added       | | c61e6dc |
| 33 | Cannot resolve symbol 'VERSION_3_17' in jOOQ… | 2022-08-30 | jooq-api       | code-generator.md | merged  | Version compatibility check since 3.16; runtime >= codegen rule      | | cb39547 |
| 34 | jOOQ 3.17 Supports Implicit Join also in DML    | 2022-08-25 | jooq-api       | implicit-joins.md | merged  | DML path expressions in UPDATE/DELETE WHERE; correlated subquery emulation | | 6ee6ab3 |
| 35 | A Condition is a Field                           | 2022-08-24 | jooq-api       | type-system.md | merged  | Condition extends Field<Boolean> since 3.17; no DSL.field() wrapper needed | | a18713f |
| 36 | The Many Ways to Return Data From SQL DML        | 2022-08-23 | jooq-api       | dml-returning.md | added   | New topic file; RETURNING abstraction across 6+ dialects, delta tables | | c3ecc83 |
| 37 | How to Integration Test Stored Procedures wi… | 2022-08-22 | jooq-api       | stored-procedures.md | merged  | Routines class + Testcontainers for type-safe proc testing            | | 88936c8 |
| 38 | Using H2 as a Test Database Product with jOOQ | 2022-08-19 | jooq-api       | anti-patterns.md | merged  | Don't mix H2 compat modes with jOOQ; use Testcontainers; new core rule | | 554b158 |
| 39 | The Best Way to Call Stored Procedures from J… | 2022-07-28 | jooq-api       | stored-procedures.md | skipped | Patterns already covered by newer entries (#28, #37)                  | | cf96665 |
| 40 | Create Dynamic Views with jOOQ 3.17's new Vi… | 2022-06-30 | jooq-api       | computed-columns.md | added   | New topic file; virtual computed columns as reusable expression "variables" | | fe62ae1 |
| 41 | 3.17.0 Release with Computed Columns, Audit… | 2022-06-22 | skip           | -          | skipped | Release announcement; all features covered by dedicated articles (#34,#35,#40) | | d4fb0c5 |
| 42 | How to Filter a SQL Nested Collection by a … | 2022-06-10 | jooq-api       | multiset.md | merged  | HAVING + boolOr().filterWhere() to filter by nested collection contents | | 83e7708 |
| 43 | The Performance of Various To-Many Nesting … | 2022-06-09 | jooq-api       | multiset.md | merged  | MULTISET perf: correlated subqueries OK for filtered sets, not large scans | | ede8a4f |
| 44 | Changing SELECT .. FROM Into FROM .. SELECT… | 2022-05-31 | skip           | -          | skipped | jOOQ dev philosophy: why DSL keeps SQL's lexical order, not actionable | | 8ec68b1 |
| 45 | The Many Different Ways to Fetch Data in jOOQ | 2022-05-19 | jooq-api       | fetching-mapping.md | merged  | 3 new patterns: fetch method chooser, single-record semantics, reactive Publisher | | e5b9638 |
| 46 | Setting the JDBC Statement.setFetchSize() to… | 2022-05-11 | skip           | -          | skipped | jOOQ internals benchmark; concluded setFetchSize(1) hurts perf, not implemented | | aba8302 |
| 47 | How to Typesafely Map a Nested SQL Collection… | 2022-05-09 | jooq-api       | multiset.md | merged  | MULTISET into Map<K,V> via convertFrom + Records.intoMap() | | 9ba59a1 |
| 48 | A Quick and Dirty Way to Concatenate Two Vagu… | 2022-05-04 | skip           | -          | skipped | Novelty NATURAL FULL JOIN trick; "quick and dirty", not a production pattern | | 7a01712 |
| 49 | Nested Transactions in jOOQ                      | 2022-04-28 | jooq-api       | transactions.md | added   | New topic; NESTED savepoints, explicit API, R2DBC reactive transactions | | 5ec4f31 |

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

---
**Run summary** (2026-02-20 18:53):
- Iterations this run: 11
- Duration: 10m 615s total
- Articles processed so far: 24 / 747
- Topic files: 10
- Open uncertainties: 1

| 50 | How to Fetch Sequence Values with jOOQ           | 2022-03-01 | jooq-api       | sequences.md | added   | New topic file; nextval()/nextvals(n) across dialects, GENERATE_SERIES batch | | d8ddc5f |
| 51 | Various Meanings of SQL's PARTITION BY Syntax     | 2022-02-24 | skip           | -          | skipped | Educational taxonomy of 5 PARTITION BY contexts; no actionable patterns | | 924e03a |
| 52 | Use MULTISET Predicates to Compare Data Sets      | 2022-02-22 | jooq-api       | multiset.md | merged  | MULTISET equality predicates for set comparison; order-independent vs ARRAY_AGG | | 2e92c45 |
| 53 | Projecting Type Safe Nested TableRecords with… | 2022-02-21 | jooq-api       | fetching-mapping.md | merged  | Table as SelectField, ad-hoc ROW expressions, TABLE.* performance caveat | | df31418 |
| 54 | jOOQ 3.16 and Java EE vs Jakarta EE              | 2022-02-14 | skip           | -          | skipped | jOOQ internals: javax→jakarta migration process, not actionable patterns | | 1352b2c |

| 55 | No More MultipleBagFetchException Thanks to M… | 2022-02-08 | jooq-api       | multiset.md | merged  | Cartesian product anti-pattern from multiple to-many JOINs; MULTISET avoids M×N duplication | | 47e965e |
| 56 | Approximating e With SQL                         | 2022-02-04 | skip           | -          | skipped | Mathematical curiosity using recursive CTEs; no actionable patterns   | | 343eaad |
| 57 | Traversing jOOQ Expression Trees with the new… | 2022-02-02 | jooq-api       | qom-traverser.md | added   | New topic file; QOM accessors, Traverser API, $replace() for RLS/soft delete | | 6602da0 |

| 58 | Detect Accidental Blocking Calls when Using R… | 2022-01-28 | skip           | -          | skipped | jOOQ internals: @Blocking annotation for R2DBC IDE warnings          | | 5ff5cc8 |
| 59 | A Rarely Seen, but Useful SQL Feature: CORRE… | 2022-01-14 | skip           | -          | skipped | CORRESPONDING for set ops; only HSQLDB supports it, not actionable   | | 63ecb69 |

| 60 | Using jOOQ's DiagnosticsConnection to detect N… | 2022-01-11 | jooq-api       | logging.md | merged  | N+1 detection via DiagnosticsConnection; framework-agnostic            | | 39cab94 |

| 61 | The Useful BigQuery * EXCEPT Syntax               | 2022-01-07 | jooq-api       | derived-tables.md | merged  | asterisk().except() for column exclusion; jOOQ emulates across dialects | | 760544f |

| 62 | 3.16.0 Release with a new Public Query Object… | 2022-01-05 | skip           | -          | skipped | Release announcement; QOM already in qom-traverser.md (#57)          | | 024ac60 |

| 63 | How to customise a jOOQ Configuration that is… | 2021-12-16 | jooq-api       | spring-boot-config.md | added   | New topic file; DefaultConfigurationCustomizer since Spring Boot 2.5  | | 0f8a52b |

| 64 | Using JDK Collectors to De-duplicate parent/ch… | 2021-12-09 | jooq-api       | multiset.md | skipped | Pre-MULTISET join dedup; all patterns already covered by newer entries | | 898d455 |

| 65 | Why You Should Use jOOQ With Code Generation     | 2021-12-06 | jooq-api       | code-generator.md | merged  | Advocacy piece; extracted forced types, embedded types, schema mapping | | df2b678 |

| 66 | Fun with PostGIS: Mandelbrot Set, Game of Life… | 2021-11-15 | skip           | -          | skipped | Creative PostGIS demos (Mandelbrot, GoL); no actionable patterns     | | ecae24b |

| 67 | PostgreSQL 14's enable_memoize For Improved Pe… | 2021-11-05 | skip           | -          | skipped | PG optimizer internals (enable_memoize config flag); not actionable   | | 73b9892 |

| 68 | Java's Checked Exceptions Are Just Weird Unio… | 2021-11-01 | skip           | -          | skipped | Java language opinion piece about union types; no SQL/jOOQ content    | | 831dfe0 |

| 69 | Functional Dependencies in SQL GROUP BY          | 2021-10-29 | sql-pattern    | aggregate-functions.md | merged  | GROUP BY functional deps + jOOQ 3.16 table-level grouping            | | 10e3f9e |

| 70 | Write C-Style Local Static Variables in Java 16  | 2021-10-22 | skip           | -          | skipped | Java language feature (JEP 395); no SQL/jOOQ content                 | | 65598fe |

| 71 | The jOOQ Parser Ignore Comment Syntax            | 2021-10-19 | jooq-api       | parser.md  | added   | New topic file; ignore markers for unsupported vendor SQL in migrations | | 2e079ae |

| 72 | Use jOOλ's Sneaky Throw to Avoid Checked Excep… | 2021-10-07 | skip           | -          | skipped | Java utility piece about jOOλ Sneaky.supplier(); no SQL/jOOQ content | | e93802b |

| 73 | Using Testcontainers to Generate jOOQ Code       | 2021-08-27 | jooq-api       | code-generator.md | merged  | Testcontainers JDBC URL + Flyway for build-time code gen             | | c4fd099 |

| 74 | Using jOOQ to write vendor agnostic SQL with… | 2021-08-26 | jooq-api       | parser.md  | merged  | Parsing connection/data source for automatic dialect translation in JPA | |

---
**Run summary** (2026-02-20 18:59):
- Iterations this run: 2
- Duration: 0m 0s total
- Articles processed so far: 25 / 747
- Topic files: 10
- Open uncertainties: 1
| 75 | Vendor Agnostic, Dynamic Procedural Logic wi… | 2021-08-25 | jooq-api       | stored-procedures.md | merged  | Vendor-agnostic anonymous blocks, WHILE loops, CREATE PROCEDURE across dialects | | 09fe63b |
| 76 | MySQL's allowMultiQueries flag with JDBC and… | 2021-08-23 | jooq-api       | spring-boot-config.md | added  | MySQL/MariaDB must set allowMultiQueries=true for jOOQ multi-stmt features | | 7e3a39e |
| 77 | 10 Things You Didn't Know About jOOQ         | 2021-08-20 | jooq-api       | anti-patterns.md | added  | .eq() vs .equals() anti-pattern; noCondition() for dynamic SQL building | | 259914e |
| 78 | Formatting ASCII Charts With jOOQ            | 2021-08-19 | jooq-api       | result-formatting.md | added  | New topic: formatChart() for ASCII bar charts in console | | dbb5a51 |
| 79 | Standard SQL/JSON – The Sobering Parts       | 2021-07-27 | jooq-api       | sql-json.md (new) | added  | New topic: dialect pitfalls — MySQL type degradation, Oracle CLOB, GROUP_CONCAT truncation, NULL semantics | | 42d215e |
