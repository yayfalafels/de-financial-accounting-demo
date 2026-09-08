# Assessment 2 - Ground-Truth Audit

Cross-checks every measured count published in this assessment's deliverables against `data/mock/issue-log.csv` (gitignored, generated locally by the seed run - not a repo path), organized by assignment task and subtask rather than by deliverable.

## Sources

- notebook: [assessment2_gl_reconciliation.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment2_gl_reconciliation.ipynb)
- deliverable audited: [assessment-2-reconciliation-results.md](assessment-2-reconciliation-results.md)

## Task 1 - GL Integrity and Reconciliation

| task ref | check                    | expected (issue-log)              | measured | match |
| -------- | ------------------------ | ---------------------------------- | -------- | ----- |
| 01.01    | arithmetic integrity     | `arithmetic_integrity_violation`=5 | 5        | yes   |
| 01.02-08 | recomputation/dim recon  | n/a [01]                           | see reconciliation-results | n/a |

01. **01.02-08** has no single injected-issue tag of its own - the widespread dimensional variance these checks surface is the combined effect of every task 3 issue category (duplicate entries, wrong dr/cr indicator, FX conversion, missing mappings, late posting, misallocated legal entity/cost center) landing in `bronze.finance_transactions`, decomposed by category only once task 3 runs.

All measured values are read live via PySpark JDBC against postgres in the notebook section cited above, not hand-typed against the ground truth.
