# Assessment 1 - Ground-Truth Audit

Cross-checks every measured count published in this assessment's deliverables against `data/mock/issue-log.csv` (gitignored, generated locally by the seed run - not a repo path), organized by assignment task and subtask rather than by deliverable, so one task's full evidence trail reads in one place.

## Sources

- notebook: [assessment1_profiling.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment1_profiling.ipynb)
- deliverable audited: [assessment-1-profiling-summary.md](assessment-1-profiling-summary.md)

## Task 1 - Data Profiling

| task ref | check                    | expected (issue-log)              | measured              | match |
| -------- | ------------------------ | --------------------------------- | --------------------- | ----- |
| 01.01    | record/distinct counts   | n/a [01]                          | see profiling summary | n/a   |
| 01.02    | duplicate ids            | `duplicate_transaction_id`=10     | 10 groups [02]         | yes   |
| 01.03    | null account_id          | `null_account_id`=5               | 5                      | yes   |
| 01.03    | null currency_code       | `null_currency_code`=5            | 5                      | yes   |
| 01.04    | date ranges              | n/a [01]                          | see profiling summary | n/a   |
| 01.05    | invalid currency_code    | `invalid_currency_code`=8         | 8                      | yes   |
| 01.05    | invalid transaction_type | `invalid_transaction_type`=5      | 5                      | yes   |
| 01.06    | negative/zero amounts    | `negative_or_zero_amount`=12      | 12                     | yes   |
| 01.07    | distributions            | `utc_sgt_midnight_boundary`=20 [03] | 5 files [03]         | yes   |
| 01.08    | late-arriving            | `late_arriving`=10                | 10                     | yes   |
| 01.09    | posting before txn       | `posting_before_transaction`=6    | 6                      | yes   |
| 01.10    | FX tolerance             | `fx_mismatch`=15                  | 27 / 37 [04][05]       | yes   |

01. **01.01/01.04** are descriptive baselines with no single injected-issue tag of their own; 01.01's src/bronze gap is explained by 01.02's duplicate counts plus Bronze-only drops, not an independent ground truth.
02. **01.02** bronze's 18 duplicate groups (not directly comparable to a single issue-log tag) split into 10 inherited from source plus 8 seeded `duplicate_in_bronze_reprocessed` rows - see the profiling summary for the row-level split.
03. **01.07** the 20 `utc_sgt_midnight_boundary` rows are Task 3's root-cause subject, not a Task 1 injected-issue count in the strict sense - listed here because 01.07's distribution is the check that first surfaces them visually, as 5 `*_MIDNIGHT.dat` files present in source and entirely absent from Bronze.
04. **01.10** src's 27 breaches are 15 genuine `fx_mismatch` rows plus 12 rows that separately carry `negative_or_zero_amount` (flipping the amount's sign without recomputing `local_currency_amount` mechanically breaches tolerance too) - confirmed by exact `transaction_id` overlap with 01.06.
05. **01.10** bronze's 37 breaches are the 27 inherited from source plus rows carrying `bronze_amount_mismatch` (10) and `bronze_currency_mismatch` (4), net of overlaps and rows dropped from Bronze - full row-level attribution belongs to task 2 level 3 / the exception dataset.

All measured values are read live via PySpark JDBC against postgres in the notebook section cited above, not hand-typed against the ground truth.

## Task 2 - Source-to-Bronze Reconciliation

| task ref    | check                 | expected (issue-log)              | measured                   | match |
| ----------- | --------------------- | --------------------------------- | --------------------------- | ----- |
| 02.01.01-06 | batch totals          | n/a [01]                          | see reconciliation-results | n/a   |
| 02.02.01-06 | dimensional variance  | n/a [01]                          | see reconciliation-results | n/a   |
| 02.03.01    | exact match           | n/a                               | 1940                       | n/a   |
| 02.03.02    | missing in Bronze     | 25 [02]                           | 33 [02]                    | yes   |
| 02.03.03    | unexpected in Bronze  | 0                                 | 0                           | yes   |
| 02.03.04    | amount mismatch       | `bronze_amount_mismatch`=10 [03]  | 9 [03]                      | yes   |
| 02.03.05    | currency mismatch     | `bronze_currency_mismatch`=4      | 4                           | yes   |
| 02.03.06    | posting-date mismatch | `bronze_posting_date_mismatch`=5 [04] | 4 [04]                  | yes   |
| 02.03.07    | duplicate in source   | `duplicate_transaction_id`=10 ids | 10 ids / 20 rows            | yes   |
| 02.03.08    | duplicate in Bronze   | 10 inherited + 8 reprocessed [05] | 18 ids / 36 rows            | yes   |

01. **02.01/02.02** batch totals and dimensional variance are aggregate measures with no single injected-issue tag of their own; they are the mechanical consequence of every level-3 record class below plus ordinary rounding, not independently seeded.
02. **02.03.02** issue-log's `utc_sgt_midnight_boundary` (20) + `missing_in_bronze_unrelated` (5) = 25 rows genuinely absent from Bronze under any classification. The measured 33 includes those 25 plus 8 more `transaction_id`s that are unique in source but duplicated in Bronze - excluded from the level-3 join by the decision order's own stated caveat (already counted under `duplicate_in_bronze`), not a second population of genuinely missing rows.
03. **02.03.04** of the 10 `bronze_amount_mismatch` rows, 1 (`TXN-0001449`) is also a duplicate on both sides and is excluded from the level-3 join entirely (counted under `duplicate_in_source`/`duplicate_in_bronze` instead), leaving 9 reaching the `amount_mismatch` class - exactly the measured count.
04. **02.03.06** of the 5 `bronze_posting_date_mismatch` rows, 1 (`TXN-0001985`) also carries an amount difference and is classified `amount_mismatch` under the decision order's amount-before-posting-date priority, leaving 4 in `posting_date_mismatch` - exactly the measured count.
05. **02.03.08** bronze's 18 duplicated `transaction_id`s split into the 10 inherited from source's own `duplicate_transaction_id` rows (carried through unchanged) plus the 8 seeded `duplicate_in_bronze_reprocessed` rows unique to Bronze.

Every level-3 count reconciles exactly to the injected catalog once the decision order's own documented exclusions are accounted for - no unexplained residual.

## Task 3 - Root-Cause Investigation

pending - not yet implemented (09.07).
