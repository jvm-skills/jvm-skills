# Processing Highlights

Noteworthy events during blog article processing — good anecdotes for the blog post.

- **#1**: First blog article processed! "Consider using JSON arrays instead of JSON objects for serialisation" (2025-08-11) — enriched existing doc-seeded `multiset.md` with internal serialization performance details (~80% speedup with arrays vs objects for 10k rows).
- **#2**: New topic file created: `array-operations.md` — "When SQL Meets Lambda Expressions" (2025-03-27). jOOQ brings functional array operations (arrayFilter, arrayMap, etc.) to SQL, with PostgreSQL emulation via unnest/reaggregate.
- **#3**: New topic file created: `merge-upsert.md` — "Think About SQL MERGE in Terms of a RIGHT JOIN" (2025-03-13). First pure SQL pattern (no jOOQ-specific API). Mental model: MERGE = RIGHT JOIN, with PostgreSQL 17's `NOT MATCHED BY SOURCE` turning it into a FULL JOIN for complete staging table sync.
- **#8**: Doc-seeded entry enriched: "An Efficient Way to Check for Existence of Multiple Values in SQL" (2024-02-16) extends the existing EXISTS vs COUNT(*) anti-pattern. When you *do* need COUNT >= N, wrapping in LIMIT N gives ~2.5x speedup on PostgreSQL by stopping early.
- **#9**: New topic file created: `implicit-joins.md` — "A Hidden Benefit of Implicit Joins: Join Elimination" (2024-01-10). jOOQ 3.19 introduced automatic join elimination for implicit path joins — intermediate tables with no referenced columns are removed from the generated SQL. First version-gated feature (Since: 3.19) in the knowledge base.
- **#10**: Older article enriched newer topic: "jOOQ 3.19's new Explicit and Implicit to-many path joins" (2023-12-28) added 3 patterns to `implicit-joins.md` that the newer #9 article didn't cover — explicit path joins (control join type), implicit join path correlation (auto-correlated subqueries), and MULTISET+path combos. Also enriched the to-many section with the cartesian product warning. First "Supersedes" note added to the knowledge base.
