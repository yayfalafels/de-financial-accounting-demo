# Assessment 2 - Business-Facing Summary

status: draft

## Sources

- notebook: `notebooks/assessment2_gl_reconciliation.ipynb`
- batch: `reconciliation.rc_batch_control.batch_id = 26`

The reconciliation compares source and General Ledger amounts on a common SGD basis. The Ledger-vs-source movement check finds SGD 297,137.40 of classification-driven variance across 30 Ledger keys. Incorrect legal-entity, GL-account, and cost-center postings (16 transactions in total) fully explain this amount - reverting exactly those 16 transactions to their as-posted classification and re-running the check returns a clean SGD 0.00, confirming no other transaction or cause contributes. Two further transactions carry a genuine misclassification each but post under a product/transaction-type combination with more than one currently-active, conflicting accounting-mapping row, so no single correct account exists to check them against.
