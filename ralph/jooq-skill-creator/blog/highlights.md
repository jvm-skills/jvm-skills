# Processing Highlights

Noteworthy events during blog article processing — good anecdotes for the blog post.

- **#1**: First blog article processed! "Consider using JSON arrays instead of JSON objects for serialisation" (2025-08-11) — enriched existing doc-seeded `multiset.md` with internal serialization performance details (~80% speedup with arrays vs objects for 10k rows).
- **#2**: New topic file created: `array-operations.md` — "When SQL Meets Lambda Expressions" (2025-03-27). jOOQ brings functional array operations (arrayFilter, arrayMap, etc.) to SQL, with PostgreSQL emulation via unnest/reaggregate.
- **#3**: New topic file created: `merge-upsert.md` — "Think About SQL MERGE in Terms of a RIGHT JOIN" (2025-03-13). First pure SQL pattern (no jOOQ-specific API). Mental model: MERGE = RIGHT JOIN, with PostgreSQL 17's `NOT MATCHED BY SOURCE` turning it into a FULL JOIN for complete staging table sync.
