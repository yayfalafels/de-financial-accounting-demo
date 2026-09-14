# Assessment 3 - Performance-Optimization Notes

**Technical Optimization Question**

See [overview](assessment-3-overview.md) for the scenario, the four dataset shapes, and the seeded-vs-production scale statement.

## Sources

- notebook: [assessment3_regulatory_dashboard.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment3_regulatory_dashboard.ipynb) -> "Performance-Optimization Demonstration" section

## Question

Keeping a reconciliation query against a five-billion-row Bronze payment table under a forty-minute baseline requires a small set of Spark techniques applied at the query's own join and aggregation shape, demonstrated here against the seeded volume budget with the resulting scale delta stated explicitly.

## Techniques

**Partition strategy and pruning** - `payment_transactions` partitioned by `payment_date` matches every date-scoped query's own filter and grouping axis. A query filtered to one `payment_date` reads only that partition's files. Demonstrated by writing the seeded data to a `payment_date`-partitioned layout and comparing the physical plan of a date-filtered read against an unfiltered one: the filtered plan's file scan carries `PartitionFilters: [isnotnull(payment_date), (payment_date = 2026-08-19)]`, confirming the date predicate is pushed to the partition layer itself; the unfiltered plan carries no partition filters and scans every partition.

**Broadcast joins** - the customer reference table is small relative to the payment table at any scale this pipeline runs at. Broadcasting it to every executor avoids shuffling the much larger payment table to perform the reference-integrity and cross-border joins every check in this assessment relies on. Demonstrated by three variants of the same join against the seeded data: a naive full scan with a shuffle join (auto-broadcast explicitly disabled to isolate the technique), the same full scan with an explicit broadcast join, and a combined query applying both partition pruning and a broadcast join together. The broadcast-only run's physical plan carries `BroadcastHashJoin`/`BroadcastExchange` in place of the naive run's `SortMergeJoin`/`Exchange hashpartitioning` - the shuffle the broadcast join removes.

| run                                  | rows scanned | wall-clock |
| --------------------------------------- | -------------- | ------------ |
| naive - full scan, shuffle join          | 2,025           | 1.60s         |
| broadcast-only - full scan, broadcast join | 2,025         | 0.47s         |
| combined - partition-pruned scan, broadcast join | 442      | 0.35s         |

**Incremental processing** - reprocessing only rows newer than the last batch's ingestion timestamp avoids a full-table rescan on every run. Demonstrated against the seeded data's own ingestion-timestamp range: a filter at the midpoint of that range selects 1,010 of 2,025 rows (50%), illustrating the row-count reduction the same filter pattern applies against a real prior-batch watermark.

**Pre-aggregated tables** - the reconciliation control schema's own design already carries this pattern: measured results are written once and read many times, avoiding recomputation from row-level data on every query.

**Explained, not demonstrated at this scale** - Delta Lake `OPTIMIZE`/Z-ORDER compaction, data skipping via file-level statistics, and predicate pushdown into a Delta transaction log are Databricks-runtime features a plain Parquet-on-Postgres Spark setup does not stand up. Each still applies conceptually at production scale: `OPTIMIZE` compacts the small files a daily partition strategy would otherwise accumulate, Z-ORDER co-locates rows by a query's most selective filter column, data skipping reads file-level min/max statistics before opening a file at all, and predicate pushdown moves a filter into the source read itself - the same role the partition filter plays in the demonstration above.

## Scale note

The seeded row count (2,025 payment rows) sits far below the assignment's five-billion-row, forty-minute baseline. The timings above demonstrate each technique's direction at seeded scale - a broadcast join and a partition-pruned scan both measurably reduce wall-clock time here - not the magnitude of time saved at production scale.
