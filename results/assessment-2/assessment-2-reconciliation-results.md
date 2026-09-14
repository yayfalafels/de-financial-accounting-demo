# Assessment 2 - Reconciliation Results

status: draft

**Task 1 - Validate Accounting Integrity**

See [overview](assessment-2-overview.md) for the scenario, table shapes, and the seeded-vs-production scale statement.

## Sources

- notebook: [assessment2_gl_reconciliation.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment2_gl_reconciliation.ipynb) -> "Task 1 - GL Integrity and Reconciliation" section
- batch: `reconciliation.rc_batch_control.batch_id = 36`

## Arithmetic integrity

`opening_balance + debit_movement - credit_movement = closing_balance` checked on every `finance.gl_balance` row, exact equality (no rounding tolerance - all four columns are `decimal(20,2)` and the expression is pure addition/subtraction).

| check                | rows checked | violations |
| ----------------------- | ------------ | ---------- |
| arithmetic integrity     | 589          | 5          |

## Independent movement recomputation

Expected debit/credit movements independently recomputed from `bronze.finance_transactions`, on each transaction's *expected* classification - the Ledger is itself built by aggregating actual, possibly-misclassified values, so grouping by those same values would make this check tautological. GL account and cost center use `ref.accounting_mapping`'s expected values wherever a transaction matches exactly one active mapping row; legal entity uses the majority-vote value for the transaction's account (the mapping table carries no legal-entity field). The mapping lookup itself is keyed on the transaction's own posted debit/credit indicator, so a transaction carrying the wrong indicator is looked up under the opposite indicator instead, wherever its actual classification matches a valid mapping row there. Six product/transaction-type combinations carry more than one currently-active, conflicting mapping row - there is no single unambiguous expected value for these, so they keep their actual classification. Recomputed on `local_amount` and compared to the Ledger's local-SGD movement fields, so the single aggregate is a valid SGD amount.

| check                      | keys compared | keys w/ variance | total variance |
| ------------------------------ | -------------- | ------------------ | ----------------- |
| debit/credit movement recompute | 589            | 30                  | 297,137.40           |

## Dimensional reconciliation

The same recomputation rolled up to one dimension at a time. Status: `PASS` if `\|variance %\| < 0.1`, `WARNING` if `< 1`, else `FAIL`.

| dimension       | distinct values | worst variance %      | status |
| ----------------- | ---------------- | ------------------------ | ------ |
| legal entity        | 4                 | 0.7482% (LE1)              | WARNING |
| GL account           | 16                | 4.6907% (GL1005)           | FAIL   |
| cost center          | 11                | 2.2957% (CC09)             | FAIL   |
| currency             | 3                 | 0.0%                       | PASS   |
| accounting date       | 5                 | 0.0%                       | PASS   |

**findings** - currency and accounting date reconcile exactly; legal entity, GL account, and cost center each show a real, material variance once transactions are classified against their expected value. Decomposing which named issue drives each is the subject of Task 3 - Investigate a Finance Variance.

## write-back to `reconciliation.rc_*`

`reconciliation.rc_reconciliation_results.dimension` is a closed set (`row_count`, `amount`). This batch persists `amount`, carrying the movement variance above against a zero baseline, as a percentage of GL SGD movement value (`local_sgd_debit_movement + local_sgd_credit_movement`); the fine-grained per-dimension detail is reported in the notebook and this deliverable only.

| dimension | source [01] | target [02] | variance   | variance % | status |
| --------- | ----------- | ----------- | ---------- | ---------- | ------ |
| amount    | 0.00        | 297137.40   | 297137.40  | 1.7480%    | FAIL   |

01. `source` = the zero baseline (no per-key movement mismatch).
02. `target` = the movement recomputation's own total variance, from the table above.

Overall batch status: `FAIL` - the same classification-driven variance the dimensional reconciliation above traces by dimension.
