# Assessment 1 - Root-Cause Analysis

**Task 3 - Root-Cause Investigation**

See [overview](assessment-1-overview.md) for the scenario, source/Bronze table shapes, and the seeded-vs-production scale statement. See [task 1 reconciliation](assessment-1-reconciliation-results.md) and [task 2 exceptions](assessment-1-exception-dataset.md) for the two open questions investigated below.

## Sources

- notebook: [assessment1_profiling.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment1_profiling.ipynb) -> "Task 3 - Root-Cause Investigation" section
- batch: `reconciliation.rc_batch_control.batch_id = 9` (same measured totals as levels 1-2)
- ground-truth verification of every count below: [assessment-1-audit.md](assessment-1-audit.md)

## Hypothesis 1 - near-UTC-midnight extraction timing

`source_extract_ts`'s schema documentation notes source timestamps are UTC while ingestion buckets by a Singapore (UTC+8) business date. **Hypothesis**: rows missing from Bronze concentrate among source rows extracted in the last 15 minutes before UTC midnight, since that window falls at 07:45-08:00 the *next* Singapore calendar day - a plausible business-date boundary mismatch.

**Evidence**: flagging every source row by `source_extract_ts` in `[23:45, 23:59]` UTC and crossing it against Bronze presence:

| id | near-UTC-midnight | in Bronze | rows |
| -- | -------------------- | --------- | ---- |
| 01 | no                    | yes       | 1985 |
| 02 | no                    | no        | 5    |
| 03 | yes                   | no        | 20   |
| 04 | yes                   | yes       | 0    |

Every one of the 20 near-UTC-midnight rows is absent from Bronze, and no near-UTC-midnight row is present - a perfect split. All 20 sit in the five `*_MIDNIGHT.dat`-suffixed files already flagged by task 2's dimensional reconciliation as the two largest `ingestion_file` variances. **Confirmed** for these 20 rows; 5 further missing rows do not fit this pattern (see [Unexplained residual](#unexplained-residual)).

## Hypothesis 2 - Bronze-only duplicates trace to a reprocessing batch

Of the 18 `transaction_id`s duplicated in Bronze, 10 are also duplicated in source (Bronze mirroring source) - the other 8 are unique in source but appear twice in Bronze, unexplained by task 2's business-column comparison. Bronze carries its own `batch_id` column. **Hypothesis**: these 8 are two loads of the same file under two different batch runs.

**Evidence**: all 8 have one row under a plain daily `batch_id` (e.g. `BATCH-20260817`) and a second under the same date with a `-R` suffix (`BATCH-20260817-R`):

| id | business date | plain batch rows | `-R` batch rows |
| -- | -------------- | ------------------ | ------------------ |
| 01 | 2026-08-17      | 395                 | 4                   |
| 02 | 2026-08-18      | 398                 | 1                   |
| 03 | 2026-08-19      | 397                 | 2                   |
| 04 | 2026-08-20      | 400                 | 0                   |
| 05 | 2026-08-21      | 395                 | 1                   |

A `-R` batch exists for 4 of the 5 business dates, each reloading only a handful of rows (1-4) rather than the whole day's file. **Confirmed**: a small partial reprocessing event recurs on nearly every business date.

## Financial impact

`local_currency_amount` is already normalised to one currency, so it sums directly regardless of `currency_code`. The two hypotheses above, taken together as a bridge from the source total to the Bronze total, close the entire level 1 local-currency variance:

| id | step                                       | amount        |
| -- | ------------------------------------------- | -------------- |
| 01 | source total `local_currency_amount`         | 56,551,777.54  |
| 02 | less: genuinely missing from Bronze (25 rows) | -810,694.96   |
| 03 | plus: Bronze reprocessing-batch extra (8 rows) | +268,029.12  |
| 04 | = bridge estimate                            | 56,009,111.70  |
| 05 | actual Bronze total `local_currency_amount`  | 56,009,111.70  |
| 06 | **unexplained residual**                     | **0.00**       |

No further mechanism is needed to explain task 2's level 1 local-currency variance - it is fully accounted for by the missing-record and reprocessing-batch populations above.

## Affected dimensions

| id | population                    | branches | products | currencies | dates |
| -- | -------------------------------- | -------- | -------- | ---------- | ----- |
| 01 | genuinely missing (25 rows)       | 14       | 4        | 5          | 5     |
| 02 | reprocessing-batch extra (8 rows) | 6        | 3        | n/a [01]   | 4     |

01. reprocessing-batch rows were not broken out by currency; both populations otherwise span nearly every branch, product, and business date rather than concentrating in one - the near-UTC-midnight timing and the `-R` batch tag are the only dimensions found to correlate.

## Unexplained residual

5 of the 33 "missing in Bronze" rows fit neither hypothesis: not near-UTC-midnight (extracted between 00:42 and 10:51 UTC), not in a `*_MIDNIGHT.dat` file, and spread across 5 different branches, dates, and ingestion files with no value shared by more than one row. Their combined `local_currency_amount` is 192,165.88 - remains open, not resolved by this investigation.

## Remediation

Reload the 25 genuinely-missing rows into Bronze from source, keyed by `transaction_id`. For the 8 reprocessing-batch duplicates, remove the extra `-R` row for each affected `transaction_id` once its content is confirmed identical to the original load.

## Permanent preventive controls

- convert `source_extract_ts` to the ingestion business timezone (or derive the business date from `transaction_date` directly) before assigning a record to a daily ingestion file, so a UTC timestamp in the last minutes of the day is no longer bucketed under the wrong Singapore business date
- add a same-day source-file-to-Bronze row-count check per `ingestion_file`, alerting when Bronze's count for a file is lower than source's - this would have caught both `*_MIDNIGHT.dat` files immediately
- make Bronze ingestion idempotent on `transaction_id` (upsert rather than append) so a reprocessing run cannot introduce a second row for an already-loaded id
- tag every Bronze batch load with a reason code (initial vs. reprocess), and alert when a reprocess batch's row count for a file doesn't match the original - the `-R` suffix already present in this data shows the signal exists, it just isn't monitored
