# Assessment 2 - Reconciliation Results

status: draft

**Task 1 - Validate Accounting Integrity**

See [overview](assessment-2-overview.md) for the scenario, table shapes, and the seeded-vs-production scale statement.

## Sources

- notebook: [assessment2_gl_reconciliation.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment2_gl_reconciliation.ipynb) -> "Task 1 - GL Integrity and Reconciliation" section
- batch: `reconciliation.rc_batch_control.batch_id = 18`

## Arithmetic integrity

`opening_balance + debit_movement - credit_movement = closing_balance` checked on every `finance.gl_balance` row, exact equality (no rounding tolerance - all four columns are `decimal(20,2)` and the expression is pure addition/subtraction).

| check                | rows checked | violations |
| ----------------------- | ------------ | ---------- |
| arithmetic integrity     | 589          | 5          |

## Independent movement recomputation

Expected debit/credit movements independently recomputed from `bronze.finance_transactions`, grouped on the same five-key grain as `finance.gl_balance` (`accounting_date, legal_entity, gl_account, cost_center, currency`), joining `posting_date` to `accounting_date` - the Ledger is dated by *posting*, not by `transaction_date`. Recomputed on `transaction_amount` (the transaction's native-currency value) - the column the Ledger's own `debit_movement`/`credit_movement` are themselves aggregated from, not `local_amount` (the currency-converted value the Ledger does not use for this purpose). Tolerance: `0.01` (one minor-currency-unit) applied independently to each side, via a full outer join so a key present on only one side still surfaces as a variance.

| check                     | keys compared | keys with a variance beyond tolerance |
| ---------------------------- | -------------- | ---------------------------------------- |
| debit/credit movement recompute | 589            | 0                                       |

## Dimensional reconciliation

The same recomputation rolled up to one dimension at a time. Status: `PASS` if `\|variance %\| < 0.1`, `WARNING` if `< 1`, else `FAIL`.

| dimension       | distinct values | worst variance %      | status |
| ----------------- | ---------------- | ------------------------ | ------ |
| legal entity        | 4                 | 0.0%                       | PASS   |
| GL account           | 15                | 0.0%                       | PASS   |
| cost center          | 10                | 0.0%                       | PASS   |
| currency             | 3                 | 0.0%                       | PASS   |
| accounting date       | 5                 | 0.0%                       | PASS   |

**findings** - the General Ledger reconciles exactly against the independently recomputed transaction data, at the full five-key grain and at every dimensional roll-up, with no exception. The eight data-quality categories the scenario names (duplicate entries, incorrect debit/credit indicator, FX conversion, missing mappings, late posting, misallocated legal entity/cost center) are investigated in Task 3 - Investigate a Finance Variance on their own merits; none of them causes the Ledger to disagree with a correctly-computed recomputation, since the Ledger's own movement figures are generated from the same transaction data these checks read.

## write-back to `reconciliation.rc_*`

`reconciliation.rc_reconciliation_results.dimension` is a closed set (`row_count`, `amount`); the fine-grained per-dimension detail above is reported in the notebook and this deliverable only. `amount` compares gross transaction value (`transaction_amount`) against gross Ledger movement value (`debit_movement + credit_movement`) - not `closing_balance`, which carries forward across accounting dates for the same key and so cannot be summed across dates without double-counting prior periods.

| dimension | source [01] | target [02]  | variance    | variance % | status |
| --------- | ----------- | ------------ | ------------- | ---------- | ------ |
| row_count | 1523        | 589          | -934           | -61.3263%  | FAIL [03] |
| amount    | 15307336.09 | 15307336.09  | 0.00           | 0.0000%    | PASS   |

01. `source` = `bronze.finance_transactions` (`COUNT(*)` / `SUM(transaction_amount)`).
02. `target` = `finance.gl_balance` (`COUNT(*)` / `SUM(debit_movement + credit_movement)`).
03. **row_count** compares two different grains by construction - 1523 individual transactions against 589 unique `(accounting_date, legal_entity, gl_account, cost_center, currency)` Ledger keys - not a reconciliation break; the `amount` dimension is the one that measures whether the Ledger's recorded value agrees with the transaction data, and it is exact.

Overall batch status: `FAIL` (`row_count` only - see note 03; `amount` is a clean `PASS`).
