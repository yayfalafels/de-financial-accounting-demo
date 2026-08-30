# Assessment 1 - Data Profiling Summary

status: draft

Answers Task 1 - Data Profiling. See [overview](assessment-1-overview.md) for the scenario,
source/Bronze table shapes, and the seeded-vs-production scale statement.

## Sources

- notebook: `notebooks/assessment1_profiling.ipynb` -> "Task 1 - Data Profiling" section
- checks implemented: `09.CK.01` only (task ref `01.01`) - profiling statistics stop at the
  notebook-cell stage (no `rc_*` control-table write for this deliverable type)

## Scope

This deliverable currently covers only `09.CK.01` (task ref `01.01` - record/distinct counts)
of the ten task 1 checks. `09.CK.02`-`09.CK.10` and the critical-data-element nomination remain
pending and will be added in a later pass.

## Findings

### 09.CK.01 - record / distinct counts (task ref 01.01)

| table                    | record count | distinct transaction_id | gap |
| ------------------------ | ------------- | ------------------------ | --- |
| src_transaction_daily    | 2010          | 2000                     | 10  |
| bronze.transaction_daily | 1993          | 1975                     | 18  |

- `src_transaction_daily`'s 10-row gap matches the 10 seeded `duplicate_transaction_id` rows in
  `data/mock/issue-log.csv` exactly.
- `bronze.transaction_daily`'s 18-row gap is larger than source's: 10 of those groups are the
  same source duplicates carrying through Bronze unchanged, and 8 are seeded
  `duplicate_in_bronze_reprocessed` rows unique to Bronze. Classifying which rows fall into
  which group is `09.CK.02` (task ref `01.02` - duplicate transaction ids), not yet implemented
  in this slice.
- both counts are read live via PySpark JDBC against postgres, not hand-typed - see the notebook
  section cited above for the exact query.
