# Assessment 1 - Exception Dataset

**Task 2 - Source-to-Bronze Reconciliation (Level 3)**

See [overview](assessment-1-overview.md) for the scenario, source/Bronze table shapes, and the seeded-vs-production scale statement. See [assessment-1-reconciliation-results.md](assessment-1-reconciliation-results.md) for levels 1-2.

## Sources

- notebook: [assessment1_profiling.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment1_profiling.ipynb) -> "Level 3 - Record-Level Classification" section
- batch: `reconciliation.rc_batch_control.batch_id = 9`
- ground-truth verification of every count below: [assessment-1-audit.md](assessment-1-audit.md)

## Classification method

Business key: `transaction_id`. Decision order, applied so every row lands in exactly one of the eight classes below:

1. **duplicate in source** - `transaction_id` appears more than once in `src_transaction_daily`; every row sharing that id is flagged, excluded from the comparison below since there is no single source row to compare against
2. **duplicate in Bronze** - same rule, applied to `bronze.transaction_daily`
3. for `transaction_id`s not a duplicate on either side, a full outer join classifies by the first rule that applies: **missing in Bronze** -> **unexpected in Bronze** -> **amount mismatch** (`transaction_amount` or `local_currency_amount` differs beyond 0.01) -> **currency mismatch** -> **posting-date mismatch** -> **exact match**

Caveat: a `transaction_id` unique in source but duplicated in Bronze is excluded from step 3 (already counted under duplicate in Bronze), so its source row classifies as *missing in Bronze* here even though Bronze does hold a (duplicated) row for it - "missing in Bronze" means "no single canonical Bronze row," not necessarily "zero Bronze rows total."

## Record classes

| id       | record class          | count            | materialisation    |
| -------- | ---------------------- | ---------------- | ------------------- |
| 09.CK.23 | exact match            | 1940             | -                   |
| 09.CK.24 | missing in Bronze      | 33 [01]          | see exception rows  |
| 09.CK.25 | unexpected in Bronze   | 0                | -                   |
| 09.CK.26 | amount mismatch        | 9 [02]           | see exception rows  |
| 09.CK.27 | currency mismatch      | 4                | see exception rows  |
| 09.CK.28 | posting-date mismatch  | 4                | see exception rows  |
| 09.CK.29 | duplicate in source    | 20 rows / 10 ids | see exception rows  |
| 09.CK.30 | duplicate in Bronze    | 36 rows / 18 ids | see exception rows  |

01. **09.CK.24** 8 of these 33 are the "excluded because Bronze-duplicated" case the caveat above describes - see the notebook section for the exact `transaction_id` overlap with `09.CK.30`. The remaining 25 have no Bronze row under any classification.
02. **09.CK.26** all 9 differ on `transaction_amount`, none on `local_currency_amount` alone - the two fields disagree with each other for these rows on the Bronze side, worth carrying into task 3.

## Exception dataset schema

Minimum columns per the assignment: `transaction_id`, `issue_type`, `source_value`, `bronze_value`, `variance`, `batch_id`. `issue_type` uses the eight record-class names above (snake_case). `source_value`/`bronze_value` hold whichever field the classification rule actually compared (the amount, currency code, or posting date); `variance` is populated only for `amount_mismatch`.

**Materialisation**: the full 106-row exception dataset lives in the notebook's own cell output (`exception_dataset`, cached and printed in full by class), git-tracked as part of the committed, executed notebook. This deliverable embeds only representative rows below, grouped by class - see the notebook section cited above for every row.

| transaction_id | issue_type            | source_value | bronze_value | variance |
| -------------- | ---------------------- | ------------- | ------------- | -------- |
| TXN-0000010    | amount mismatch         | 6990.12        | 6992.03        | 1.91     |
| TXN-0000031    | amount mismatch         | 475.68         | 478.76         | 3.08     |
| TXN-0000856    | currency mismatch       | GBP            | EUR            | -        |
| TXN-0000971    | currency mismatch       | SGD            | JPY            | -        |
| TXN-0000068    | duplicate in Bronze     | -              | 48039.77       | -        |
| TXN-0000090    | duplicate in Bronze     | -              | 33260.17       | -        |

Full per-class counts and the remaining rows (25 genuinely absent, 32 more duplicates, 2 more currency mismatches, 4 posting-date mismatches, and 20 duplicate-in-source rows) are in the notebook output, not reproduced here.