# Assessment 1 - Reconciliation Results

**Task 2 - Source-to-Bronze Reconciliation**

See [overview](assessment-1-overview.md) for the scenario, source/Bronze table shapes, and the seeded-vs-production scale statement.

## Sources

- notebook: [assessment1_profiling.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment1_profiling.ipynb) -> "Task 2 - Source-to-Bronze Reconciliation" section
- batch: `reconciliation.rc_batch_control.batch_id = 9`
- ground-truth verification of every count below: [assessment-1-audit.md](assessment-1-audit.md)
- record-level classification and the exception dataset: [assessment-1-exception-dataset.md](assessment-1-exception-dataset.md)

## Level 1 - Batch Totals

| id       | check              | src         | bronze      | variance   | variance % | status  |
| -------- | ------------------ | ----------- | ----------- | ---------- | ---------- | ------- |
| 09.CK.11 | record count       | 2010        | 1993        | -17        | -0.8458%   | WARNING |
| 09.CK.12 | distinct count     | 2000        | 1975        | -25        | -1.25%     | FAIL    |
| 09.CK.13 | debit sum          | 24853095.67 | 24588770.69 | -264324.98 | -1.0635%   | FAIL    |
| 09.CK.14 | credit sum         | 24469169.68 | 24265754.53 | -203415.15 | -0.8313%   | WARNING |
| 09.CK.15 | net amount         | 383925.99   | 323016.16   | -60909.83  | -15.865%   | FAIL    |
| 09.CK.16 | local-currency sum | 56551777.54 | 56009111.70 | -542665.84 | -0.9596%   | WARNING |

Status: `PASS` if `|variance %| < 0.1`, `WARNING` if `< 1`, else `FAIL`. Every total disagrees beyond `PASS`; **net amount** is the most severe, off by nearly 16% - a batch-level total this sensitive to a handful of record-level differences is itself worth carrying into task 3, not just the totals themselves.

`09.CK.11` (record count) and `09.CK.14`+`09.CK.13` combined (`amount` = gross debit + credit) are written to `reconciliation.rc_reconciliation_results` under `batch_id=9` - the only two of these six totals the existing control-table schema supports (see the notebook's Level 1 markdown for why). The other four are reported here only.

## Level 2 - Dimensional Reconciliation

Reconciled independently by each of six dimensions; the three group values with the largest absolute local-currency amount variance per dimension are the "largest-variance combinations."

| id       | dimension        | distinct values | nonzero variance |
| -------- | ---------------- | --------------- | ---------------- |
| 09.CK.17 | transaction_date | 5               | 5 [01]           |
| 09.CK.18 | branch_code      | 20              | 16 [02]          |
| 09.CK.19 | currency_code    | 11              | 7 [03]           |
| 09.CK.20 | product_code     | 4               | 4 [04]           |
| 09.CK.21 | transaction_type | 5               | 2 [05]           |
| 09.CK.22 | ingestion_file   | 20              | 12 [06]          |

01. **09.CK.17** largest: `2026-08-21` (-260,658.90), `2026-08-19` (-168,711.69), `2026-08-18` (-57,386.91).
02. **09.CK.18** largest: `BR014` (-90,870.13), `BR013` (-80,605.10), `BR011` (-79,614.19) - variance is spread thinly rather than concentrated in one branch.
03. **09.CK.19** largest: `SGD` (-239,896.50), `GBP` (-207,902.80), `USD` (-159,037.76) - roughly proportional to each currency's share of volume, not concentrated in one currency.
04. **09.CK.20** largest: `CURRENT` (-232,715.39), `SAVINGS` (-181,472.23), `LOAN` (-92,556.26) - all four products show a variance, none disproportionately.
05. **09.CK.21** largest: `DEBIT` (-355,345.22), `CREDIT` (-187,320.62); the third value, `ADJUSTMENT`, has zero variance on a single matched row.
06. **09.CK.22** largest: `source_extract_260821_MIDNIGHT.dat` (-269,583.23, entirely absent from Bronze - 7 source rows, 0 Bronze rows), `source_extract_260817_MIDNIGHT.dat` (-161,975.39, same pattern, 5 rows), `source_extract_260817_02.dat` (+98,323.35, the only one of the three with *more* Bronze rows than source). This is the open question task 1's profiling raised, now answered at the dimensional level: the low-volume `*_MIDNIGHT.dat` files carry a disproportionate share of the missing-record variance relative to their size - worth carrying into task 3.

`transaction_date` and `currency_code` show variance spread broadly across nearly every value rather than concentrated in one, while `ingestion_file` shows the opposite - two files carry a variance far larger than their row count alone would suggest. That contrast is itself a finding: whatever is driving the gap correlates with `ingestion_file` more than with the other five dimensions.
