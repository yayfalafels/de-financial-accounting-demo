# Assessment 2 - Accounting Mapping Validation

status: draft

**Task 2 - Validate Accounting Mapping**

See [overview](assessment-2-overview.md) for the scenario, table shapes, and the seeded-vs-production scale statement.

## Sources

- notebook: [assessment2_gl_reconciliation.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment2_gl_reconciliation.ipynb) -> "Task 2 - Accounting Mapping Validation" section
- unioned into the minimum-columns [exception dataset](assessment-2-exception-dataset.md)

## Checks

| task ref | check                                      | result                                |
| -------- | --------------------------------------------- | ----------------------------------------- |
| 02.01    | posted to expected GL account                 | 403 rows / 319 transactions - `GL_MISMATCH` |
| 02.02    | mapping effective-date validity               | 0 - `NO_EFFECTIVE_MAPPING`                |
| 02.03    | missing accounting mapping                    | 385 rows - `MAPPING_NOT_FOUND`            |
| 02.04    | overlapping effective-date mapping ranges     | 8 pairs, 6 (product, type) combos         |
| 02.05    | expired mapping still referenced              | 0 - `EXPIRED_MAPPING`                     |
| 02.06    | product mapped to multiple GL accounts        | 4 combos [01]                             |

01. **02.06** `P1/DEBIT`=3 accounts, `P1/CREDIT`=2, `P9/CREDIT`=2, `P5/DEBIT`=2.

## GL_MISMATCH traces mostly to mapping conflicts

Breaking the 403 `GL_MISMATCH` rows down by product and transaction type:

| product / type  | rows | distinct transactions | explained by a mapping conflict? |
| --------------- | ---- | ---------------------- | ----------------------------------- |
| P1 / DEBIT      | 167  | 83                      | yes - 3 conflicting mapping rows      |
| P1 / CREDIT     | 83   | 83                      | yes - 2 conflicting mapping rows      |
| P9 / CREDIT     | 80   | 80                      | yes - 2 conflicting mapping rows      |
| P5 / DEBIT      | 64   | 64                      | yes - 2 conflicting mapping rows      |
| P4 / DEBIT      | 4    | 4                       | yes - overlapping mapping window      |
| P8 / CREDIT     | 3    | 3                       | yes - overlapping mapping window      |
| P8 / DEBIT      | 1    | 1                       | no                                     |
| P3 / DEBIT      | 1    | 1                       | no                                     |

401 of the 403 rows (99.5%) sit on product/type pairs the overlapping-mapping and multi-GL-mapping checks independently flag as carrying conflicting mapping definitions - `P1/DEBIT`'s 167 rows over 83 distinct transactions is a join fan-out: a transaction matching more than one mapping row is evaluated against each match independently, so it can appear more than once. Only 2 rows (one each on two other product/type pairs) are not explained by a mapping conflict - a genuine per-transaction GL miscoding, an open residual for Task 3 - Investigate a Finance Variance.

## Missing accounting mapping

All 385 rows fall on five product/transaction-type pairs that have no row at all in the accounting mapping table (91, 85, 77, 74, and 58 transactions respectively) - the mapping table covers 15 of the 20 product/transaction-type combinations actually posted, so these five are structurally absent from it.

## Exception output

The assignment's shape - `Transaction, Product, Actual GL, Expected GL, Accounting Date, Exception` - applied to the four per-transaction checks (posted to expected GL account, mapping effective-date validity, missing accounting mapping, expired mapping still referenced); the overlapping-mapping and multi-GL-mapping checks are mapping-level findings with no `transaction_id` to key on, reported separately above. Full 788-row output is in the notebook's `exception_output` cell; a sample:

| Transaction  | Product | Actual GL  | Expected GL | Accounting Date | Exception         |
| ------------ | ------- | ---------- | ----------- | --------------- | ----------------- |
| FTX-0000008  | P1      | GL1007     | GL1014      | 2026-08-17      | GL_MISMATCH       |
| FTX-0000019  | P10     | GL9999     | -           | 2026-08-17      | MAPPING_NOT_FOUND |
