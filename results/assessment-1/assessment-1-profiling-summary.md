# Assessment 1 - Data Profiling Summary

**Task 1 - Data Profiling**

See [overview](assessment-1-overview.md) for the scenario, source/Bronze table shapes, and the seeded-vs-production scale statement. This analysis assumes that the reported high-level local currency gap has already been reproduced and confirmed direct query of the databases.

## Sources

- notebook: [assessment1_profiling.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment1_profiling.ipynb) -> "Task 1 - Data Profiling" section
- checks implemented: all ten task 1 checks
- ground-truth verification of every count below: [assessment-1-audit.md](assessment-1-audit.md)

## Definitions

- **valid currency codes**: `SGD, USD, EUR, GBP, JPY`
- **valid transaction types**: `CREDIT, DEBIT`
- **FX tolerance**: `abs(local_currency_amount - transaction_amount * exchange_rate) > 0.01` (absolute, cents)
- **late-arriving**: `date(source_extract_ts) > transaction_date`

## Findings

| check                                  | src                     | bronze                  |
| --------------------------------------- | ----------------------- | ----------------------- |
| record / distinct transaction_id       | 2010 / 2000 (gap 10)    | 1993 / 1975 (gap 18)    |
| duplicate id groups                    | 10 / 10 extra           | 18 / 18 extra [01]      |
| null account_id / currency_code        | 5 (0.25%) / 5 (0.25%)   | 5 (0.25%) / 5 (0.25%)   |
| currency_code distinct / invalid       | 10 / 8                  | 10 / 8                  |
| transaction_type distinct / invalid    | 5 / 5                   | 5 / 5                   |
| negative/zero amount count             | 12                      | 12                      |
| branch/product/file distribution       | see notebook [02]       | see notebook [02]       |
| late-arriving records                  | 10                      | 10                      |
| posting before transaction date        | 6                       | 6                       |
| FX tolerance breach                    | 27 [03]                 | 37 [04]                 |

**date ranges** transaction_date range 2026-08-17 to 2026-08-21, posting_date range 2026-08-15 to 2026-08-23 - identical on both tables.

Notes below report what this level of analysis can deduce and the open question it raises for the next level.

01. bronze shows 18 duplicate `transaction_id` groups (18 extra rows) against source's 10. At this profiling stage that is only a count difference on each table taken alone; whether the same IDs are duplicated in both tables, Bronze carries additional duplicates of its own, or both, is an open question for task 2's source-to-Bronze record-level comparison.
02. source's `ingestion_file` distribution shows five low-volume files (2-7 rows each, named with a `MIDNIGHT` suffix) well below the other fifteen files' 120-150 row range - a distributional outlier worth flagging. Bronze shows only fifteen distinct `ingestion_file` values against source's twenty. Whether Bronze's five missing values are those same five low-volume files, and why, is an open question for task 2's reconciliation.
03. source: 27 rows breach the FX tolerance, of which 12 also fail the negative/zero amount check on the same `transaction_id` - two independent checks flagging the same rows is worth carrying forward as one population. The remaining 15 raise no other flag in this profiling pass.
04. bronze: 37 rows breach the same tolerance, more than source's 27. Whether this is the source rows carrying through plus additional Bronze-only breaches, or a different population, is an open question for task 2's reconciliation.

## Critical data elements

Nominated against the checks and joins actually exercised by this assessment's three tasks - a column earns the label when a specific check, reconciliation cut, or root-cause step depends on it.

| id | column                | why critical                                                    |
| -- | --------------------- | ----------------------------------------------------------------- |
| 01 | transaction_id        | business key - drives duplicate-id detection and the source-to-Bronze join |
| 02 | transaction_amount    | feeds task 2 level 1 batch totals and the sign check               |
| 03 | local_currency_amount | the balance Finance reported broken - task 2's reconciled measure  |
| 04 | exchange_rate         | ties amount to local_currency_amount - the FX tolerance check      |
| 05 | currency_code         | dimensional reconciliation cut plus the currency validity check    |
| 06 | transaction_type      | debit/credit split for level 1 totals plus the transaction-type validity check |
| 07 | transaction_date      | task 2 dimensional cut and task 3's business-date boundary          |
| 08 | posting_date          | posting-order check plus accounting-date reconciliation             |
| 09 | branch_code           | task 2 level 2 dimensional reconciliation cut                       |
| 10 | product_code          | task 2 level 2 dimensional reconciliation cut                       |
| 11 | ingestion_file        | source-file distribution and task 3's root-cause trace              |
| 12 | source_extract_ts     | late-arriving check and task 3's UTC/SGT boundary evidence          |

`account_id` and `source_system` are excluded - neither is read by any Task 1-3 check, reconciliation cut, or root-cause step in this assessment's scope.
