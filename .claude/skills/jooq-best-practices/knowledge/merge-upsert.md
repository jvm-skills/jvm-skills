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

## Pattern: Full Sync with FULL JOIN in USING Clause
**Source**: [The Many Flavours of the Arcane SQL MERGE Statement](https://blog.jooq.org/the-many-flavours-of-the-arcane-sql-merge-statement) (2020-04-10)

Use a FULL JOIN in the USING clause to expose all three row states (insert/update/delete) in a single MERGE, making the full sync pattern fully explicit:

```sql
MERGE INTO prices AS p
USING (
  SELECT COALESCE(p.product_id, s.product_id) AS product_id, s.price
  FROM prices AS p
  FULL JOIN staging AS s ON p.product_id = s.product_id
) AS s
ON (p.product_id = s.product_id)
WHEN MATCHED AND s.price IS NULL THEN DELETE
WHEN MATCHED AND p.price != s.price THEN UPDATE SET
  price = s.price,
  price_date = CURRENT_DATE,
  update_count = update_count + 1
WHEN NOT MATCHED THEN INSERT (product_id, price, price_date, update_count)
  VALUES (s.product_id, s.price, CURRENT_DATE, 0)
```

Each source row matches exactly one WHEN clause (evaluated in order). Structure conditions to be mutually exclusive for correctness.

---

## Pattern: AND Conditions in WHEN Clauses (Dialect Emulation)
**Source**: [The Many Flavours of the Arcane SQL MERGE Statement](https://blog.jooq.org/the-many-flavours-of-the-arcane-sql-merge-statement) (2020-04-10)

Most dialects support `WHEN MATCHED AND <predicate>` for conditional updates. For databases without AND support, jOOQ emulates with CASE:

```sql
-- Emulated for dialects without AND support:
WHEN MATCHED THEN UPDATE SET
  price = CASE WHEN p.price != s.price THEN s.price ELSE p.price END,
  update_count = CASE WHEN p.price != s.price THEN update_count + 1 ELSE update_count END
```

**Dialects with native AND**: Db2, Derby, Firebird, H2, HSQLDB, Oracle, SQL Server, Sybase SQL Anywhere, Teradata, Vertica.

---

## Pattern: Oracle ORA-38104 — Updating ON Clause Columns
**Source**: [How to Work Around ORA-38104](https://blog.jooq.org/how-to-work-around-ora-38104-columns-referenced-in-the-on-clause-cannot-be-updated) (2019-01-02)
**Dialect**: Oracle

Oracle forbids updating columns referenced in the MERGE ON clause (`ORA-38104`). Workarounds (prefer #1 or #2 for production; avoid #3):

**1. Row value expression** — wrap in a row tuple with a dummy literal (preserves index usage):
```sql
ON (t.id = s.id OR (t.user_name, 'dummy') = (s.user_name, 'dummy'))
WHEN MATCHED THEN UPDATE SET t.user_name = s.user_name
```

**2. NVL() derived table** — alias the column via NVL so the parser doesn't see the link:
```sql
MERGE INTO (
  SELECT id, nvl(user_name, null) n, score FROM person
) t
USING source s
ON (t.id = s.id OR t.n = s.user_name)
WHEN MATCHED THEN UPDATE SET t.user_name = s.user_name
```

**3. WHERE clause** (changes semantics, fewer indexes used):
```sql
ON (t.id = s.id)
WHEN MATCHED THEN UPDATE SET t.user_name = s.user_name
WHERE t.user_name = s.user_name
```

> These exploit Oracle parser limitations; reserve for one-off migrations, not steady-state production code, as Oracle may close these loopholes.

---

## Pattern: Oracle MERGE — WHERE Instead of AND, Combined UPDATE+DELETE
**Source**: [The Many Flavours of the Arcane SQL MERGE Statement](https://blog.jooq.org/the-many-flavours-of-the-arcane-sql-merge-statement) (2020-04-10)
**Dialect**: Oracle

Oracle uses `WHERE` instead of `AND` in WHEN clauses and combines UPDATE and DELETE:

```sql
WHEN MATCHED THEN
  UPDATE SET price = s.price WHERE p.price != s.price
  DELETE WHERE s.price IS NULL
```

The DELETE fires only on rows that were just updated (not on other matched rows). Vertica omits DELETE support entirely.

---
