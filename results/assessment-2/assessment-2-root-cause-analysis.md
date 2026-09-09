# Assessment 2 - Root-Cause Analysis

status: draft

**Task 3 - Investigate a Finance Variance**

See [overview](assessment-2-overview.md) for the scenario, table shapes, and the seeded-vs-production scale statement. See [reconciliation results](assessment-2-reconciliation-results.md) for the scale of the variance this investigation decomposes.

## Sources

- notebook: [assessment2_gl_reconciliation.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment2_gl_reconciliation.ipynb) -> "Task 3 - Investigate a Finance Variance" section

## Method

Each of the categories the scenario names is checked independently rather than searched for transaction by transaction. A category's contribution is the sum of `local_amount` across the transactions it flags. Two totals are then compared: the single top-line variance between the Ledger's total and the independently recomputed transaction total (the same figure the scenario's own reported variance is an instance of), and the bottom-up sum of every category's contribution. Categories are not guaranteed mutually exclusive (a single transaction can be flagged by more than one check), so the two totals are not expected to match exactly - any gap is reported as an unexplained residual rather than forced to close.

## Findings

| category                            | rows       | value attributed |
| -------------------------------------- | ---------- | ------------------ |
| duplicate / re-posted accounting entry   | 21           | 255,845.35            |
| incorrect debit/credit indicator          | 0 [01]       | -                      |
| incorrect FX conversion                    | 3            | 4,467.53               |
| missing accounting mapping                 | 385          | 4,387,367.89           |
| posted one accounting day late              | 0 [02]       | -                      |
| incorrect legal-entity allocation            | 6            | 60,697.50              |
| incorrect cost-center assignment              | 8            | 85,485.13              |
| **independent Ledger total variance** [03] | -          | **4,002,303.12**      |
| **bottom-up sum of the categories above**   | -          | **4,793,863.40**      |
| **unexplained residual** [04]               | -          | **-791,560.28**       |

01. **indicator** checked indirectly, by looking for a Ledger key where the debit and credit variance from Task 1's recomputation cancel to near zero while neither is individually zero (the signature a single flipped transaction would leave if it were the only cause of variance at that key) - no key in this dataset showed that signature. A single flipped transaction's effect can be present but too small to surface this way once a key already carries a larger variance from another cause; this check did not find a category-specific population it could isolate.
02. **late posting** - 12 transactions post exactly one calendar day after their transaction date, but none of the 12 materially closes the prior day's own movement variance at the same key when moved back a day, so none is confirmed as this category's cause rather than a normal one-day processing lag.
03. **independent Ledger total variance** - the absolute difference between the Ledger's total closing balance and the independently recomputed total transaction value, from Task 1 - the top-down figure this bottom-up decomposition is checked against.
04. **unexplained residual** = independent Ledger total variance - bottom-up sum. Negative here, meaning the categories together attribute *more* value than the single top-line variance - consistent with not every category being a pure driver of that one total: legal-entity and cost-center misclassification move a transaction's value between sub-totals without changing the grand total, so their inclusion in the bottom-up sum does not correspondingly reduce the top-down figure. The residual is reported as found, not adjusted to zero.

## Duplicate / re-posted accounting entries

Business fields (every column except the transaction id) hashed per transaction, grouped by posting date; every row sharing a hash and posting date beyond the first is flagged, indicating either the same entry recorded twice or the same transaction re-posted under a different id - the two scenarios the assignment names separately are not distinguishable from this data alone, since both leave an identical signature. 21 rows flagged this way, contributing 255,845.35.

## Missing accounting mapping

385 transactions have no accounting mapping covering their product code and debit/credit type, so their General Ledger posting cannot be confirmed correct or incorrect - their combined transaction value, 4,387,367.89, is reported as unexplained/unmapped rather than folded into a mismatch count. This is the largest single contribution found.

## Incorrect legal-entity allocation

The accounting mapping table carries no expected legal entity, so this check compares each transaction's legal entity against the most frequently posted legal entity for the same account elsewhere in the period - a transaction disagreeing with its account's own usual entity is a probable misallocation. 6 transactions flagged, contributing 60,697.50, spread across 4 different account/entity pairs with no single pair dominating.

## Incorrect cost-center assignment

The accounting mapping table does carry an expected cost center, so this check reuses the same effective-dated join as the accounting mapping validation. 8 distinct transactions flagged (a transaction matching more than one active mapping row is checked against each independently, so the raw row count is higher before removing that duplication), contributing 85,485.13.

## Unexplained residual

The bottom-up sum of category contributions (4,793,863.40) exceeds the independent top-line Ledger variance (4,002,303.12) by 791,560.28. The categories above are not partitions of a single known total the way a source-to-target record diff would be - legal-entity and cost-center misclassification redistribute value between sub-totals without changing the Ledger's grand total, so summing them alongside categories that genuinely move the total (duplicates, unmapped transactions, FX errors) overstates what the bottom-up sum should be compared against. Separately, two of the eight named categories (incorrect debit/credit indicator, posted one accounting day late) returned no confirmed population from the methods used - this investigation cannot rule out that either is present but too small, or too entangled with a larger co-occurring cause at the same Ledger key, to isolate with the checks used here.

## Remediation

- reload or confirm the accounting mapping table's coverage for every product/transaction-type combination actually posted, so every transaction can be validated against an expected GL account and cost center
- review the 21 flagged duplicate/re-posted entries against their source system to confirm which are genuine re-entries versus legitimate repeat transactions, before reversing any
- confirm the FX rate source used for the 3 flagged transactions against the rate actually in force on their transaction date
- review the 6 legal-entity and 8 cost-center mismatches against their originating account records to confirm the correct allocation

## Permanent preventive controls

- add a mapping-coverage check that runs whenever a new product or transaction type is introduced, alerting before any transaction can post without a matching accounting-mapping row
- add a same-batch duplicate check on the business-field hash used above, run before a batch is accepted into the Ledger feed rather than discovered afterward
- add an FX-tolerance check against the rate in force on the transaction date at the point of posting, not just at investigation time
- add a control that flags a transaction whose legal entity or cost center disagrees with its account's established pattern, for review before posting rather than after
