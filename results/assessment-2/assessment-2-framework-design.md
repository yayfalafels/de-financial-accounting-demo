# Assessment 2 - Reconciliation Framework Design

status: draft

## Sources

- notebook: `notebooks/assessment2_gl_reconciliation.ipynb`
- batch: `reconciliation.rc_batch_control.batch_id = 24`

This framework uses common-currency SGD amounts for aggregate amount reconciliation: source value is `SUM(bronze.finance_transactions.local_amount)` and GL value is `SUM(finance.gl_balance.local_sgd_debit_movement + finance.gl_balance.local_sgd_credit_movement)` for movement checks. Native-currency GL fields stay available for per-currency diagnostics only.
