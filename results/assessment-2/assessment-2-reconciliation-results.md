# Assessment 2 - Reconciliation Results

status: draft

**Task 1 - Validate Accounting Integrity**

See [overview](assessment-2-overview.md) for the scenario, table shapes, and the seeded-vs-production scale statement.

## Sources

- notebook: [assessment2_gl_reconciliation.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment2_gl_reconciliation.ipynb) -> "Task 1 - GL Integrity and Reconciliation" section
- batch: `reconciliation.rc_batch_control.batch_id = 12`

## Arithmetic integrity

`opening_balance + debit_movement - credit_movement = closing_balance` checked on every `finance.gl_balance` row, exact equality (no rounding tolerance - all four columns are `decimal(20,2)` and the expression is pure addition/subtraction).

| check                | rows checked | violations |
| ----------------------- | ------------ | ---------- |
| arithmetic integrity     | 589          | 5          |

## Independent movement recomputation

Expected debit/credit movements independently recomputed from `bronze.finance_transactions`, grouped on the same five-key grain as `finance.gl_balance` (`accounting_date, legal_entity, gl_account, cost_center, currency`), joining `posting_date` to `accounting_date` - the GL is dated by *posting*, not by `transaction_date`. Tolerance: `0.01` (one minor-currency-unit) applied independently to each side, via a full outer join so a key present on only one side still surfaces as a variance.

| check                     | keys compared | keys with a variance beyond tolerance |
| ---------------------------- | -------------- | ---------------------------------------- |
| debit/credit movement recompute | 589            | 284                                       |

## Dimensional reconciliation

The same recomputation rolled up to one dimension at a time. Status: `PASS` if `\|variance %\| < 0.1`, `WARNING` if `< 1`, else `FAIL`.

| dimension       | distinct values | worst variance %      | status |
| ----------------- | ---------------- | ------------------------ | ------ |
| legal entity        | 4                 | 12.2325% (LE4)             | FAIL   |
| GL account           | 15                | 14.3507% (GL1009)          | FAIL   |
| cost center          | 10                | 14.3507% (CC10)            | FAIL   |
| currency             | 3                 | 45.7804% (EUR)             | FAIL   |
| accounting date       | 5                 | 11.8745% (2026-08-19)      | FAIL   |

**currency finding** - `SGD` reconciles exactly (`0.0%` variance), while `EUR` (45.78%) and `USD` (34.12%) both fail by a wide margin. Every other dimension's variance is spread broadly across most of its values (e.g. all four legal entities and all five accounting dates FAIL in a similar 9-12% band) rather than concentrated in one or two outliers - currency is the one dimension where the finding is a clean split rather than a spread.

**findings** - every dimension fails the reconciliation status threshold except `currency=SGD`; this is the batch-level symptom the scenario describes (platform closing balance materially disagreeing with the expected/recomputed figure), not a narrow one-record miss. Decomposing why is the subject of Task 3 - Investigate a Finance Variance.

## write-back to `reconciliation.rc_*`

`reconciliation.rc_reconciliation_results.dimension` is a closed set (`row_count`, `amount`); the fine-grained per-dimension detail above is reported in the notebook and this deliverable only.

| dimension | source [01] | target [02]  | variance    | variance % | status |
| --------- | ----------- | ------------ | ------------- | ---------- | ------ |
| row_count | 1523        | 589          | -934           | -61.3263%  | FAIL   |
| amount    | 16999151.01 | 12996847.89  | -4002303.12    | -23.5441%  | FAIL   |

01. `source` = `bronze.finance_transactions` (`COUNT(*)` / `SUM(local_amount)`).
02. `target` = `finance.gl_balance` (`COUNT(*)` / `SUM(closing_balance)`).

Overall batch status: `FAIL`.
