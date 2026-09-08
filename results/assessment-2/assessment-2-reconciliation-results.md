# Assessment 2 - Reconciliation Results

status: draft

**Task 1 - GL Integrity and Reconciliation**

See [overview](assessment-2-overview.md) for the scenario, table shapes, and the seeded-vs-production scale statement.

## Sources

- notebook: [assessment2_gl_reconciliation.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment2_gl_reconciliation.ipynb) -> "Task 1 - GL Integrity and Reconciliation" section
- batch: `reconciliation.rc_batch_control.batch_id = 12`
- ground-truth verification of the arithmetic-integrity count: [assessment-2-audit.md](assessment-2-audit.md)

## 10.CK.01 - arithmetic integrity

`opening_balance + debit_movement - credit_movement = closing_balance` checked on every `finance.gl_balance` row, exact equality (no rounding tolerance - all four columns are `decimal(20,2)` and the expression is pure addition/subtraction).

| check    | rows checked | violations |
| -------- | ------------ | ---------- |
| 10.CK.01 | 589          | 5          |

**implementation note** - the first pass of this check cast the four decimal columns to `double` before comparing, which introduced floating-point rounding noise (`~1e-12`) and inflated the count to 203 false violations; fixed by keeping the comparison in native `decimal(20,2)` arithmetic. The corrected count (5) matches the ground-truth audit exactly.

## 10.CK.02 / 10.CK.03 - independent movement recomputation

Expected debit/credit movements independently recomputed from `bronze.finance_transactions`, grouped on the same five-key grain as `finance.gl_balance` (`accounting_date, legal_entity, gl_account, cost_center, currency`), joining `posting_date` to `accounting_date` - the GL is dated by *posting*, not by `transaction_date`. Tolerance: `0.01` (one minor-currency-unit) applied independently to each side, via a full outer join so a key present on only one side still surfaces as a variance.

| check              | keys compared | keys with a variance beyond tolerance |
| -------------------- | -------------- | ---------------------------------------- |
| 10.CK.02 / 10.CK.03 | 589            | 284                                       |

## 10.CK.04 - 10.CK.08 - dimensional reconciliation

The same recomputation rolled up to one dimension at a time. Status: `PASS` if `\|variance %\| < 0.1`, `WARNING` if `< 1`, else `FAIL`.

| id       | dimension       | distinct values | worst variance %  | status |
| -------- | --------------- | ---------------- | ------------------ | ------ |
| 10.CK.04 | legal_entity    | 4                 | 12.2325% (LE4)      | FAIL   |
| 10.CK.05 | gl_account      | 15                | 14.3507% (GL1009)   | FAIL   |
| 10.CK.06 | cost_center     | 10                | 14.3507% (CC10)     | FAIL   |
| 10.CK.07 | currency        | 3                 | 45.7804% (EUR)      | FAIL   |
| 10.CK.08 | accounting_date | 5                 | 11.8745% (2026-08-19) | FAIL |

**10.CK.07 currency finding** - `SGD` reconciles exactly (`0.0%` variance), while `EUR` (45.78%) and `USD` (34.12%) both fail by a wide margin. Every other dimension's variance is spread broadly across most of its values (e.g. all four legal entities and all five accounting dates FAIL in a similar 9-12% band) rather than concentrated in one or two outliers - `currency` is the one dimension where the finding is a clean split rather than a spread, worth carrying into task 3's investigation as the leading candidate dimension.

**findings** - every dimension FAILs the reconciliation status threshold except `currency=SGD`; this is the batch-level symptom the assignment scenario describes (platform closing balance materially disagreeing with the expected/recomputed figure), not a narrow one-record miss. Decomposing *why* - duplicate entries, wrong debit/credit indicator, FX conversion, missing mappings, late posting, misallocated legal entity/cost center - is task 3's job, not re-derived here.

## write-back to `reconciliation.rc_*`

`reconciliation.rc_reconciliation_results.dimension` is a closed set (`row_count`, `amount`) fixed by the reconciliation control-table schema; the fine-grained per-dimension detail above is reported in the notebook and this deliverable only, following the same split [Assessment 1's reconciliation results](../assessment-1/assessment-1-reconciliation-results.md) draws for its own level 1 batch totals.

| dimension | source [01] | target [02]  | variance    | variance % | status |
| --------- | ----------- | ------------ | ------------- | ---------- | ------ |
| row_count | 1523        | 589          | -934           | -61.3263%  | FAIL   |
| amount    | 16999151.01 | 12996847.89  | -4002303.12    | -23.5441%  | FAIL   |

01. `source` = `bronze.finance_transactions` (`COUNT(*)` / `SUM(local_amount)`).
02. `target` = `finance.gl_balance` (`COUNT(*)` / `SUM(closing_balance)`).

`batch_id=12` is the first `assessment_id = 'assessment-2'` row `reconciliation.rc_batch_control` carries - confirmed via direct SQL against `reconciliation.rc_reconciliation_results WHERE batch_id = 12`, independent of the notebook's own printed summary. Overall batch status: `FAIL`.
