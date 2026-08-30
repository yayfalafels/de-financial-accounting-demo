# Assessment 1 - Data Profiling Summary

status: draft

**Task 1 - Data Profiling**

See [overview](assessment-1-overview.md) for the scenario, source/Bronze table shapes, and the seeded-vs-production scale statement.

## Sources

- notebook: `notebooks/assessment1_profiling.ipynb` -> "Task 1 - Data Profiling" section
- checks implemented: `09.CK.01`-`09.CK.10` (task refs `01.01`-`01.10`) - all ten task 1 checks. Profiling statistics stop at the notebook-cell stage (no `rc_*` control-table write for this deliverable type)

## Definitions

- **valid currency codes**: `SGD, USD, EUR, GBP, JPY`
- **valid transaction types**: `CREDIT, DEBIT`
- **FX tolerance (09.CK.10)**: `abs(local_currency_amount - transaction_amount * exchange_rate) > 0.01` (absolute, cents)
- **late-arriving (09.CK.08)**: `date(source_extract_ts) > transaction_date`

## Findings

| id       | check                                | src                    | bronze                 |
| -------- | -------------------------------------- | ----------------------- | ----------------------- |
| 09.CK.01 | record / distinct transaction_id       | 2010 / 2000 (gap 10)    | 1993 / 1975 (gap 18)    |
| 09.CK.02 | duplicate id groups                    | 10 / 10 extra           | 18 / 18 extra [01]      |
| 09.CK.03 | null account_id / currency_code        | 5 (0.25%) / 5 (0.25%)   | 5 (0.25%) / 5 (0.25%)   |
| 09.CK.05 | currency_code distinct / invalid       | 10 / 8                  | 10 / 8                  |
| 09.CK.05 | transaction_type distinct / invalid    | 5 / 5                   | 5 / 5                   |
| 09.CK.06 | negative/zero amount count             | 12                      | 12                      |
| 09.CK.07 | branch/product/file distribution       | see notebook [02]       | see notebook [02]       |
| 09.CK.08 | late-arriving records                  | 10                      | 10                      |
| 09.CK.09 | posting before transaction date        | 6                       | 6                       |
| 09.CK.10 | FX tolerance breach                    | 27 [03]                 | 37 [04]                 |

**09.CK.04** transaction_date range 2026-08-17 to 2026-08-21, posting_date range 2026-08-15 to 2026-08-23 - identical on both tables.

01. **09.CK.02** bronze's 18 duplicate groups split into 10 inherited from source (same `transaction_id`s as source's own 10 duplicates, carried through unchanged) plus 8 seeded `duplicate_in_bronze_reprocessed` rows unique to Bronze. Full record-level classification is task 2 level 3, not this deliverable.
02. **09.CK.07** src's 20 near-midnight rows sit in five `*_MIDNIGHT.dat` files (2-7 rows each); none of those five files appear in Bronze's distribution at all - the visible fingerprint of the `utc_sgt_midnight_boundary` issue this assessment's Task 3 investigates.
03. **09.CK.10** src's 27 breaches split into the 15 seeded `fx_mismatch` rows plus 12 rows that also carry the `negative_or_zero_amount` mutation - flipping `transaction_amount`'s sign without recomputing `local_currency_amount` mechanically breaches the tolerance too, confirmed by exact `transaction_id` overlap with the 09.CK.06 rows.
04. **09.CK.10** bronze's 37 breaches include the 27 inherited from source plus rows carrying the seeded `bronze_amount_mismatch` (10) and `bronze_currency_mismatch` (4) issues, net of overlaps and the rows dropped from Bronze entirely - full row-level attribution is task 2 level 3 / the exception dataset, not this deliverable.

## Critical data elements

Nominated against the checks and joins actually exercised by this assessment's three tasks - a column earns the label because a specific check, reconciliation cut, or root-cause step depends on it, not because it appears in the schema.

| id | column                | why critical                                                    |
| -- | --------------------- | ----------------------------------------------------------------- |
| 01 | transaction_id        | business key - drives 09.CK.02 dedup and the source-to-Bronze join |
| 02 | transaction_amount    | feeds task 2 level 1 batch totals and the sign check 09.CK.06      |
| 03 | local_currency_amount | the balance Finance reported broken - task 2's reconciled measure  |
| 04 | exchange_rate         | ties amount to local_currency_amount - the 09.CK.10 tolerance check |
| 05 | currency_code         | dimensional reconciliation cut plus the 09.CK.05 validity check    |
| 06 | transaction_type      | debit/credit split for level 1 totals plus the 09.CK.05 validity check |
| 07 | transaction_date      | task 2 dimensional cut and task 3's business-date boundary          |
| 08 | posting_date          | 09.CK.09 ordering check plus accounting-date reconciliation         |
| 09 | branch_code           | task 2 level 2 dimensional reconciliation cut                       |
| 10 | product_code          | task 2 level 2 dimensional reconciliation cut                       |
| 11 | ingestion_file        | 09.CK.07 source-file distribution and task 3's root-cause trace     |
| 12 | source_extract_ts     | 09.CK.08 late-arriving check and task 3's UTC/SGT boundary evidence  |

`account_id` and `source_system` are excluded - neither is read by any Task 1-3 check, reconciliation cut, or root-cause step in this assessment's scope.

## Ground-truth cross-check

Every count above reproduces its expected value from `data/mock/issue-log.csv` exactly: `duplicate_transaction_id`=10, `null_account_id`=5, `null_currency_code`=5, `invalid_currency_code`=8, `invalid_transaction_type`=5, `negative_or_zero_amount`=12, `posting_before_transaction`=6, `fx_mismatch`=15 (within the 27 total breaches), `late_arriving`=10. All counts are read live via PySpark JDBC against postgres, not hand-typed - see the notebook section cited above.
