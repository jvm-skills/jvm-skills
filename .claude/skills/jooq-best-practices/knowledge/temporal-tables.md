# Temporal Tables & Historical Data Patterns

## Pattern: Reconstruct snapshot from archive log deltas using ROW_NUMBER
**Source**: [How to Aggregate an Archive Log's Deltas into a Snapshot with SQL](https://blog.jooq.org/how-to-aggregate-an-archive-logs-deltas-into-a-snapshot-with-sql) (2018-11-16)

When an audit/archive log stores only changed attributes (deltas) rather than full snapshots, reconstruct the state at any point in time using `ROW_NUMBER` to rank deltas per attribute by recency, then keep only rank 1.

```kotlin
// Conceptual jOOQ pattern for delta-to-snapshot reconstruction
val ranked = ctx.select(
    ARCHIVE_LOG.ENTITY_ID,
    ARCHIVE_LOG.ATTR_KEY,
    ARCHIVE_LOG.ATTR_VALUE,
    DSL.rowNumber()
        .over(DSL.partitionBy(ARCHIVE_LOG.ENTITY_ID, ARCHIVE_LOG.ATTR_KEY)
                  .orderBy(ARCHIVE_LOG.TS.desc()))
        .`as`("rn")
)
.from(ARCHIVE_LOG)
.where(ARCHIVE_LOG.TS.le(targetTimestamp))
.asTable("ranked")

// Then select where rn = 1 to get the most recent delta per attribute
ctx.select(ranked.field(ARCHIVE_LOG.ENTITY_ID), ranked.field(ARCHIVE_LOG.ATTR_KEY), ranked.field(ARCHIVE_LOG.ATTR_VALUE))
    .from(ranked)
    .where(ranked.field("rn", Int::class.java).eq(1))
    .fetch()
```

**Algorithm**:
1. Filter deltas to those occurring before the target timestamp
2. `PARTITION BY entity_id, attribute` → rank by `timestamp DESC`
3. Keep only `rank = 1` — the most recent delta per attribute

This avoids storing full snapshots while still enabling point-in-time queries.

---

## Pattern: SQL:2011 Temporal Tables as native alternative to manual deltas
**Source**: [How to Aggregate an Archive Log's Deltas into a Snapshot with SQL](https://blog.jooq.org/how-to-aggregate-an-archive-logs-deltas-into-a-snapshot-with-sql) (2018-11-16)

Native temporal table support eliminates the need for manual delta aggregation:
- **SQL Server 2016+**: `SYSTEM_TIME` temporal tables with `FOR SYSTEM_TIME AS OF <timestamp>`
- **Oracle**: Flashback queries (`AS OF TIMESTAMP`) — requires Flashback Data Archive configured
- **MariaDB 10.3.4+**: `FOR SYSTEM_TIME AS OF`

**Dialect**: SQL Server / Oracle / MariaDB

Use native temporal tables when available — they are optimized and handle concurrency correctly. The manual `ROW_NUMBER` delta approach is a fallback for databases without native support or when using an EAV schema.

---
