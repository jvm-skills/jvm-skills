# MERGE / Upsert Patterns

## Pattern: Think of MERGE as a RIGHT JOIN
**Source**: [Think About SQL MERGE in Terms of a RIGHT JOIN](https://blog.jooq.org/think-about-sql-merge-in-terms-of-a-right-join) (2025-03-13)

MERGE performs a RIGHT JOIN between target (left) and source (right):
- **MATCHED** → row exists in both → UPDATE
- **NOT MATCHED** → row only in source → INSERT
- **NOT MATCHED BY SOURCE** → row only in target → DELETE (turns it into a FULL JOIN)

```sql
MERGE INTO book_to_book_store AS t
USING book_to_book_store_staging AS s
ON t.book_id = s.book_id AND t.name = s.name
WHEN MATCHED THEN UPDATE SET stock = s.stock
WHEN NOT MATCHED THEN INSERT (book_id, name, stock)
  VALUES (s.book_id, s.name, s.stock)
```

With `NOT MATCHED BY SOURCE` (PostgreSQL 17+, SQL Server, Databricks, Firebird 5):

```sql
WHEN NOT MATCHED BY TARGET THEN INSERT ...
WHEN NOT MATCHED BY SOURCE THEN DELETE
```

This full-sync pattern replaces DELETE + INSERT or complex upsert logic for staging table scenarios.

---
