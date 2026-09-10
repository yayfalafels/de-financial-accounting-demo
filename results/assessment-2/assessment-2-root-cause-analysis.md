# Assessment 2 - Root-Cause Analysis

status: draft

**Task 3 - Investigate a Finance Variance**

See [overview](assessment-2-overview.md) for the scenario, table shapes, and the seeded-vs-production scale statement. See [reconciliation results](assessment-2-reconciliation-results.md) for the variance this investigation decomposes.

## Sources

- notebook: [assessment2_gl_reconciliation.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment2_gl_reconciliation.ipynb) -> "Task 3 - Investigate a Finance Variance" section

## Method and headline finding

Each of the categories the scenario names is checked independently rather than searched for transaction by transaction. Task 1's expected-classification recomputation found 268,250.94 in Ledger-vs-transaction movement variance. Two of the eight categories below - incorrect legal-entity allocation and incorrect cost-center assignment - are exactly the categories Task 1's recomputation substitutes an expected value for, so they are the natural candidates to explain it: a misposted transaction is missing from its correct bucket and present in its wrong one, so its value counts twice toward the variance.

## Findings

| category                            | rows / keys | value      |
| -------------------------------------- | ----------- | ------------ |
| duplicate / re-posted accounting entry   | 21            | 255,845.35 [01] |
| incorrect debit/credit indicator          | 9 [02]        | 78,480.32 [01] |
| incorrect FX conversion                    | 3             | 4,467.53 [01]  |
| missing accounting mapping                 | 385           | 4,387,367.89 [01][03] |
| posted one accounting day late              | 12 / 0 [04]   | -              |
| incorrect legal-entity allocation            | 6             | 60,697.50      |
| incorrect cost-center assignment              | 5             | 55,515.89      |

01. **duplicate entries, indicator, FX conversion, missing accounting mapping** - real, individually-verified findings, but none of them is a classification category Task 1's recomputation substitutes for, so none is expected to explain the movement variance (see the per-category notes below for why).
02. **indicator** - `ref.accounting_mapping` keys the expected GL account and cost center off *both* the product code and the debit/credit indicator, so a transaction carrying the wrong indicator often becomes an exact match for a *different*, valid mapping row under the opposite indicator: not some field being wrong, but every field being right, filed under the wrong sign. 9 transactions flagged this way. This is independent of Task 1's Ledger reconciliation - it reads the transaction and mapping data directly - so it isn't affected by that reconciliation's own finding that a flipped indicator is pass-through to the Ledger's movement figures.
03. **missing accounting mapping** - an audit-confidence gap, not a Ledger variance: these transactions keep their actual classification in Task 1's recomputation (no expected value to substitute), so they cannot contribute to the variance found.
04. **late posting** - 12 transactions post exactly one calendar day after their transaction date; 0 confirmed against the prior day's own movement shortfall - the Ledger is built from each transaction's own (possibly late) posting date, so the Ledger and the recomputation already agree on where a late-posted transaction lands.

## Bridging the variance

| step                                                  | amount     |
| -------------------------------------------------------- | ------------ |
| Task 1 movement variance (expected-classification basis)   | 268,250.94     |
| less: 2x incorrect legal-entity allocation (60,697.50 x 2)   | 121,395.00     |
| less: 2x incorrect cost-center assignment (55,515.89 x 2)     | 111,031.78     |
| = residual                                                | 35,824.16      |

87% of the variance is accounted for by the two classification categories, at twice their face value each (missing from the correct bucket, present in the wrong one) - confirmed as non-overlapping populations across all three of this section's classification checks (indicator, legal-entity, cost-center): no transaction is flagged by more than one. Part of the remaining 35,824.16 (13%) is explained precisely: one of the nine incorrect-indicator transactions (`FTX-0001297`, 11,453.83) posts under a product/indicator combination that - even corrected - is one of the six with more than one active, conflicting mapping row (see mapping validation), so Task 1's recomputation has no single unambiguous expected value to substitute for it either way; at twice face value that accounts for 22,907.66 of the residual. The remaining 12,916.50 stays genuinely unexplained by this investigation.

## Duplicate / re-posted accounting entries

Business fields (every column except the transaction id) hashed per transaction, grouped by posting date; every row sharing a hash and posting date beyond the first is flagged, indicating either the same entry recorded twice or the same transaction re-posted under a different id - the two scenarios the assignment names separately are not distinguishable from this data alone, since both leave an identical signature. 21 rows flagged this way, contributing 255,845.35 - already included in the Ledger's own recorded movement, since the Ledger is built from the same (duplicated) transaction data at its actual classification.

## Incorrect debit/credit indicator

`ref.accounting_mapping` keys the expected GL account and cost center off both the product code and the debit/credit indicator - a product's expected classification differs between its debit rows and its credit rows. A transaction whose actual classification fails to match any currently-active mapping row for its own posted indicator, but exactly matches one for the opposite indicator, is flagged: its own values are internally consistent with a real, valid combination, just filed under the wrong sign. 9 transactions flagged this way, contributing 78,480.32. This check does not depend on the Ledger at all, unlike a check built on Task 1's own recomputation output would - the Ledger's movement figures are aggregated from the same (already-mutated) indicator, so a flipped transaction is baked into both sides identically and leaves no signature there to find.

## Missing accounting mapping

385 transactions have no accounting mapping covering their product code and debit/credit type, so their General Ledger posting cannot be confirmed correct or incorrect. Their combined value, 4,387,367.89, is a disclosure figure - the largest population found - not a Ledger discrepancy.

## Incorrect FX conversion

The one category whose error does not reach the Ledger at all: the Ledger's movement figures are built from `transaction_amount`, which an FX-conversion error never touches (it only misstates `local_amount`). A misstated `local_amount` sits in the transaction data undetected by any Ledger-level reconciliation - the 3 flagged rows, 4,467.53, were found only by checking `local_amount` against its own inputs (`transaction_amount * exchange_rate`) directly.

## Incorrect legal-entity allocation

The accounting mapping table carries no expected legal entity, so this check compares each transaction's legal entity against the most frequently posted legal entity for the same account elsewhere in the period - a transaction disagreeing with its account's own usual entity is a probable misallocation. 6 transactions flagged, contributing 60,697.50, spread across 4 different account/entity pairs with no single pair dominating - the same substitution Task 1's recomputation applies for this dimension, so this category's transactions are exactly where that recomputation's legal-entity variance traces to.

## Incorrect cost-center assignment

The accounting mapping table does carry an expected cost center, so this check reuses the same effective-dated join as the accounting mapping validation, excluding transactions the indicator check above already explains (their cost center looks wrong only when checked against the wrong-indicator mapping row). 5 distinct transactions flagged (a transaction matching more than one active mapping row is checked against each independently, so the raw row count is higher before removing that duplication), contributing 55,515.89 - the same substitution Task 1's recomputation applies for this dimension.

## Remediation

- correct the 9 debit/credit indicator, 6 legal-entity, and 5 cost-center misclassifications directly against their originating records, and re-run Task 1's recomputation to confirm the movement variance closes to the expected residual
- reload or confirm the accounting mapping table's coverage for every product/transaction-type combination actually posted, so every transaction can be validated against an expected GL account and cost center
- review the 21 flagged duplicate/re-posted entries against their source system to confirm which are genuine re-entries versus legitimate repeat transactions, before reversing any
- confirm the FX rate source used for the 3 flagged transactions against the rate actually in force on their transaction date

## Permanent preventive controls

- add a control that flags a transaction whose legal entity or cost center disagrees with its account's established pattern, for review before posting rather than after - this is the pair of controls that would have prevented most of the variance found here
- add a control that flags a transaction whose posted classification doesn't match any valid mapping row for its own indicator but does for the opposite one, for review before posting - this is what catches a flipped debit/credit indicator without needing a dedicated normal-balance reference
- add a mapping-coverage check that runs whenever a new product or transaction type is introduced, alerting before any transaction can post without a matching accounting-mapping row
- add a same-batch duplicate check on the business-field hash used above, run before a batch is accepted into the Ledger feed rather than discovered afterward
- add an FX-tolerance check against the rate in force on the transaction date at the point of posting - this is the one category the standard Ledger-vs-transaction reconciliation cannot catch on its own, since the error never reaches the Ledger's own movement figures, so this control needs to sit upstream of Ledger posting
