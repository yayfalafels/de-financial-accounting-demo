# Assessment 2 - Accounting Mapping Validation

status: draft

**Task 2 - Accounting Mapping Validation**

See [overview](assessment-2-overview.md) for the scenario, table shapes, and the seeded-vs-production scale statement.

## Sources

- notebook: [assessment2_gl_reconciliation.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment2_gl_reconciliation.ipynb) -> "Task 2 - Accounting Mapping Validation" section
- cited by notebook section, not a `reconciliation.rc_batch_control.batch_id` - task 2 findings are not written to `reconciliation.rc_*` 
- unioned into the minimum-columns [exception dataset](assessment-2-exception-dataset.md)

## Checks

| id       | check                                     | result                               |
| -------- | ----------------------------------------- | ------------------------------------ |
| 10.CK.09 | posted to expected GL account             | 403 rows / 319 txns - `GL_MISMATCH`  |
| 10.CK.10 | mapping effective-date validity           | 0 - `NO_EFFECTIVE_MAPPING`           |
| 10.CK.11 | missing accounting mapping                | 385 rows - `MAPPING_NOT_FOUND`       |
| 10.CK.12 | overlapping effective-date mapping ranges | 8 pairs, 6 (product, type) combos    |
| 10.CK.13 | expired mapping still referenced          | 0 - `EXPIRED_MAPPING`                |
| 10.CK.14 | product mapped to multiple GL accounts    | 4 combos                             |

01. **10.CK.09** `GL_MISMATCH` - see the breakdown below.
02. **10.CK.12** `P1/CREDIT`, `P1/DEBIT`, `P4/DEBIT`, `P5/DEBIT`, `P8/CREDIT`, `P9/CREDIT`.
03. **10.CK.14** `P1/DEBIT`=3 accounts, `P1/CREDIT`=2, `P9/CREDIT`=2, `P5/DEBIT`=2.

## 10.CK.09 finding - GL_MISMATCH traces mostly to mapping conflicts, not transaction data

Breaking the 403 `GL_MISMATCH` rows down by `(product_code, debit_credit_indicator)`:

| product / type  | rows | distinct transactions | explained? |  check                              |
| --------------- | ---- | --------------------- | ---------- | ----------------------------------- |
| P1 / DEBIT      | 167  | 83                    | yes - 3    | conflicting mapping rows 10.CK.14   |
| P1 / CREDIT     | 83   | 83                    | yes - 2    | conflicting mapping rows 10.CK.14   |
| P9 / CREDIT     | 80   | 80                    | yes - 2    | conflicting mapping rows 10.CK.14   |
| P5 / DEBIT      | 64   | 64                    | yes - 2    | conflicting mapping rows 10.CK.14   |
| P4 / DEBIT      | 4    | 4                     | yes        | overlapping mapping window 10.CK.12 |
| P8 / CREDIT     | 3    | 3                     | yes        | overlapping mapping window 10.CK.12 |
| P8 / DEBIT      | 1    | 1                     | no         |                                     |
| P3 / DEBIT      | 1    | 1                     | no         |                                     |

401 of the 403 rows (99.5%) sit on `(product, type)` pairs `10.CK.12`/`10.CK.14` independently flag as carrying conflicting mapping definitions - `P1/DEBIT`'s 167 rows over 83 distinct transactions is the join-fanout the design predicted (a transaction matching more than one mapping row is evaluated against each match independently, so it can appear more than once). Only 2 rows (`P8/DEBIT`, `P3/DEBIT`, one transaction each) are **not** explained by a mapping conflict - a genuine per-transaction GL miscoding, carried forward as an open residual for task 3.

## 10.CK.11 finding - MAPPING_NOT_FOUND is a reference-table coverage gap

All 385 rows fall on five `(product_code, debit_credit_indicator)` pairs that have **no row at all** in `ref.accounting_mapping` (`P7/CREDIT`=91, `P4/CREDIT`=85, `P2/DEBIT`=77, `P10/CREDIT`=74, `P6/CREDIT`=58) - `ref.accounting_mapping`'s 22 rows cover 15 of the 20 `(product, type)` combinations actually posted in `bronze.finance_transactions`; these five are structurally absent from the reference table. This is a deliberately injected issue category, matched exactly against `issue-log.csv`'s `missing_accounting_mapping` tag (see [assessment-2-audit.md](assessment-2-audit.md)) - the assignment's own Task 2 checklist names this scenario explicitly ("identify transactions with missing accounting mappings").

## Exception output

The assignment's shape - `Transaction, Product, Actual GL, Expected GL, Accounting Date, Exception` - applied to the four per-transaction checks (`10.CK.09`, `10.CK.10`, `10.CK.11`, `10.CK.13`); `10.CK.12`/`10.CK.14` are mapping-level findings with no `transaction_id` to key on, reported separately above. Full 788-row output is in the notebook's `exception_output` cell; a sample:

| Transaction  | Product | Actual GL  | Expected GL | Accounting Date | Exception         |
| ------------ | ------- | ---------- | ----------- | --------------- | ----------------- |
| FTX-0000008  | P1      | GL1007     | GL1014      | 2026-08-17      | GL_MISMATCH       |
| FTX-0000019  | P10     | GL9999     | -           | 2026-08-17      | MAPPING_NOT_FOUND |
