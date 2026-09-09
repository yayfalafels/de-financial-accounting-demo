# Assessment 2 - Root-Cause Analysis

status: draft

**Task 3 - Investigate a Finance Variance**

See [overview](assessment-2-overview.md) for the scenario, table shapes, and the seeded-vs-production scale statement. See [reconciliation results](assessment-2-reconciliation-results.md) for the Ledger reconciliation this investigation's findings sit alongside.

## Sources

- notebook: [assessment2_gl_reconciliation.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment2_gl_reconciliation.ipynb) -> "Task 3 - Investigate a Finance Variance" section

## Method and headline finding

Each of the categories the scenario names is checked independently rather than searched for transaction by transaction. The reconciliation results deliverable's corrected recomputation shows the General Ledger reconciles exactly against the transaction data - zero variance at every key, on every dimension. None of the categories below is therefore measured against a Ledger-level gap to explain; each stands as its own finding, verified directly against the source data.

## Findings

| category                            | rows / keys | value      |
| -------------------------------------- | ----------- | ------------ |
| duplicate / re-posted accounting entry   | 21            | 255,845.35     |
| incorrect debit/credit indicator          | 0 [01]        | -              |
| incorrect FX conversion                    | 3             | 4,467.53       |
| missing accounting mapping                 | 385           | 4,387,367.89 [02] |
| posted one accounting day late              | 12 / 0 [03]   | -              |
| incorrect legal-entity allocation            | 6             | 60,697.50      |
| incorrect cost-center assignment              | 8             | 85,485.13      |

01. **indicator** checked by looking for a Ledger key where the debit and credit variance from the movement recomputation cancel to near zero while neither is individually zero - the signature a single flipped transaction would leave if the Ledger did not also reflect the flip. None found: the Ledger's movement figures are aggregated from the same transaction data this check reads, so a flipped indicator is baked into both consistently and is structurally invisible to a Ledger-vs-transaction reconciliation. Confirming a wrong indicator needs a rule external to this reconciliation (e.g. an expected normal balance per GL account), not attempted here.
02. **missing accounting mapping** - an audit-confidence gap, not a Ledger variance: the Ledger's movement figures already include these transactions at whatever GL account/cost center they were actually posted to, confirmed or not against the reference mapping table (see reconciliation results - the Ledger reconciles exactly including these transactions).
03. **late posting** - 12 transactions post exactly one calendar day after their transaction date; 0 confirmed against the prior day's own movement shortfall, for the same structural reason as the indicator check - the Ledger is built from each transaction's own (possibly late) posting date, so the Ledger and the recomputation already agree on where a late-posted transaction lands.

## Duplicate / re-posted accounting entries

Business fields (every column except the transaction id) hashed per transaction, grouped by posting date; every row sharing a hash and posting date beyond the first is flagged, indicating either the same entry recorded twice or the same transaction re-posted under a different id - the two scenarios the assignment names separately are not distinguishable from this data alone, since both leave an identical signature. 21 rows flagged this way, contributing 255,845.35 - already included in the Ledger's own reconciled total, since the Ledger is built from the same (duplicated) transaction data.

## Missing accounting mapping

385 transactions have no accounting mapping covering their product code and debit/credit type, so their General Ledger posting cannot be confirmed correct or incorrect. Their combined value, 4,387,367.89, is a disclosure figure - the largest population found - not a Ledger discrepancy: the reconciliation results deliverable confirms the Ledger's own movement figures already include this value.

## Incorrect FX conversion

The one category whose error does not reach the Ledger at all: the Ledger's movement figures are built from `transaction_amount`, which an FX-conversion error never touches (it only misstates `local_amount`). A misstated `local_amount` sits in the transaction data undetected by any Ledger-level reconciliation - the 3 flagged rows, 4,467.53, were found only by checking `local_amount` against its own inputs (`transaction_amount * exchange_rate`) directly.

## Incorrect legal-entity allocation

The accounting mapping table carries no expected legal entity, so this check compares each transaction's legal entity against the most frequently posted legal entity for the same account elsewhere in the period - a transaction disagreeing with its account's own usual entity is a probable misallocation. 6 transactions flagged, contributing 60,697.50, spread across 4 different account/entity pairs with no single pair dominating.

## Incorrect cost-center assignment

The accounting mapping table does carry an expected cost center, so this check reuses the same effective-dated join as the accounting mapping validation. 8 distinct transactions flagged (a transaction matching more than one active mapping row is checked against each independently, so the raw row count is higher before removing that duplication), contributing 85,485.13.

## Remediation

- reload or confirm the accounting mapping table's coverage for every product/transaction-type combination actually posted, so every transaction can be validated against an expected GL account and cost center
- review the 21 flagged duplicate/re-posted entries against their source system to confirm which are genuine re-entries versus legitimate repeat transactions, before reversing any
- confirm the FX rate source used for the 3 flagged transactions against the rate actually in force on their transaction date
- review the 6 legal-entity and 8 cost-center mismatches against their originating account records to confirm the correct allocation

## Permanent preventive controls

- add a mapping-coverage check that runs whenever a new product or transaction type is introduced, alerting before any transaction can post without a matching accounting-mapping row
- add a same-batch duplicate check on the business-field hash used above, run before a batch is accepted into the Ledger feed rather than discovered afterward
- add an FX-tolerance check against the rate in force on the transaction date at the point of posting - this is the one category the standard Ledger-vs-transaction reconciliation cannot catch on its own, since the error never reaches the Ledger's own movement figures, so this control needs to sit upstream of Ledger posting, not rely on downstream reconciliation to find it
- add a control that flags a transaction whose legal entity or cost center disagrees with its account's established pattern, for review before posting rather than after
