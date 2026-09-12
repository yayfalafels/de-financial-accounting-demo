# Assessment 2 - Root-Cause Analysis

status: draft

**Task 3 - Investigate a Finance Variance**

See [overview](assessment-2-overview.md) for the scenario, table shapes, and the seeded-vs-production scale statement. See [reconciliation results](assessment-2-reconciliation-results.md) for the variance this investigation decomposes.

## Sources

- notebook: [assessment2_gl_reconciliation.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment2_gl_reconciliation.ipynb) -> "Task 3 - Investigate a Finance Variance" section

## Method and headline finding

Each of the categories the scenario names is checked independently. Task 1's expected-classification recomputation found SGD 297,137.40 in Ledger-vs-transaction movement variance. Three classification dimensions - legal-entity allocation, GL-account assignment, and cost-center assignment - are exactly the fields Task 1's recomputation substitutes an expected value for, so they are the candidates that explain it: a misposted transaction's value is missing from its correct bucket and present in its wrong one, counting twice toward the variance.

## Findings

### Categories that explain the Ledger movement variance

These four categories are the ones Task 1's recomputation substitutes an expected value for; together they explain the full SGD 297,137.40 Ledger-vs-source movement variance. [Bridging the variance](#bridging-the-variance) below shows how they add up to that figure.

| category                              | rows / keys | value                  |
| -------------------------------------- | ----------- | ------------------------ |
| incorrect legal-entity allocation      | 6           | 60,697.50                 |
| incorrect GL-account assignment        | 6           | 53,687.44                 |
| incorrect cost-center assignment       | 3 [01]      | 40,036.00 [01]            |
| incorrect GL-account + cost-center [01] | 1          | 9,706.73 [01]             |

01. **cost-center population split** - one transaction the mapping validation also flags as `GL_MISMATCH` posts to a sentinel account/cost-center pair wrong on both fields at once, reported on its own row. A further, genuinely cost-center-mismatched transaction is excluded from every row above: its product/transaction-type combination carries two currently-active, conflicting mapping rows (see mapping validation's overlapping-mapping finding), so Task 1's recomputation has no expected value to substitute for it. It remains a real classification error outside this reconciliation's reach.

### Other findings

Each of these is a real, independently-verified finding on its own basis - see the note for each. `missing accounting mapping`'s 4,387,367.89 in particular is a disclosure total: the combined value of transactions with nothing to check them against.

| category                              | rows / keys | value                  |
| -------------------------------------- | ----------- | ------------------------ |
| duplicate / re-posted accounting entry | 21          | 255,845.35 [02]           |
| incorrect debit/credit indicator       | 9 [03]      | 78,480.32 [02]            |
| incorrect FX conversion                | 3           | 4,467.53 [02]             |
| missing accounting mapping             | 385         | 4,387,367.89 [02][04]     |
| posted one accounting day late         | 12 / 0 [05] | -                         |

02. **duplicate entries, indicator, FX conversion, missing accounting mapping** - independently-verified findings outside the three classification categories Task 1's recomputation substitutes for (see the per-category notes below).
03. **indicator** - `ref.accounting_mapping` keys the expected GL account and cost center off *both* the product code and the debit/credit indicator, so a transaction carrying the wrong indicator often becomes an exact match for a *different*, valid mapping row under the opposite indicator - every field correct, filed under the wrong sign. 9 transactions flagged this way. This check reads the transaction and mapping data directly, independent of Task 1's Ledger reconciliation.
04. **missing accounting mapping** - an audit-confidence gap: these transactions keep their actual classification in Task 1's recomputation, since no expected value exists to substitute.
05. **late posting** - 12 transactions post exactly one calendar day after their transaction date; the Ledger is built from each transaction's own (possibly late) posting date, so the Ledger and the recomputation already agree on where a late-posted transaction lands.

## Bridging the variance

Task 1's expected-classification recomputation substitutes a different value for exactly 16 transactions across three classification dimensions - legal-entity, GL-account, and cost-center (one transaction wrong on both fields at once). Every other transaction's actual and expected classification already agree, contributing identically to both the Ledger and the recomputation. The four categories are added back one at a time, in the order below, each measured as the exact increase in variance that category's own correction contributes on top of the ones already added. The four amounts add up to the total by construction:

| step                                                | amount        |
| ------------------------------------------------------ | --------------- |
| total GL variance (Task 1 recomputation)                 | 297,137.40        |
| incorrect legal-entity allocation                         | 121,395.00        |
| incorrect GL-account assignment [01]                      | 76,256.94         |
| incorrect cost-center assignment                           | 80,072.00         |
| incorrect GL-account + cost-center (same transaction)       | 19,413.46         |
| = sum of the four categories                             | 297,137.40        |
| = residual                                              | 0.00              |

01. **incorrect GL-account assignment** contributes 76,256.94 here: legal-entity's correction is already in place by the time GL-account's is added, and the two share some of the same five-key posting buckets, so part of GL-account's effect is already reflected in the legal-entity row above it. Cost-center and the combined transaction share no bucket with anything already added, so their rows each land on exactly twice their own face value (40,036.00 x 2 and 9,706.73 x 2).

0 of 589 keys exceed tolerance once all four corrections are in place, matching the Ledger exactly - the full SGD 297,137.40 is completely explained by these four categories. Two further transactions are confirmed, real misclassifications - one flagged by the indicator check, one by the cost-center check - excluded from this table: both post under a product/transaction-type combination with more than one currently-active, conflicting mapping row, so no expected value exists to substitute for them (see the cost-center population-split note above and the mapping validation's overlapping-mapping finding).

## Duplicate / re-posted accounting entries

Business fields (every column except the transaction id) hashed per transaction, grouped by posting date; every row sharing a hash and posting date beyond the first is flagged, indicating either the same entry recorded twice or the same transaction re-posted under a different id - both leave an identical signature. 21 rows flagged this way, contributing 255,845.35, already included in the Ledger's own recorded movement, since the Ledger is built from the same (duplicated) transaction data at its actual classification.

## Incorrect debit/credit indicator

`ref.accounting_mapping` keys the expected GL account and cost center off both the product code and the debit/credit indicator - a product's expected classification differs between its debit rows and its credit rows. A transaction whose actual classification fails to match any currently-active mapping row for its own posted indicator, but exactly matches one for the opposite indicator, is flagged: its own values are internally consistent with a real, valid combination, filed under the wrong sign. 9 transactions flagged this way, contributing 78,480.32. This check reads the transaction and mapping data directly, independent of Task 1's Ledger reconciliation - the Ledger's own movement figures are aggregated from the same (already-mutated) indicator, so a flipped transaction is baked into both sides identically and leaves no signature there to find.

## Missing accounting mapping

385 transactions have no accounting mapping covering their product code and debit/credit type, so their General Ledger posting cannot be confirmed correct or incorrect. Their combined value, 4,387,367.89, is a disclosure figure - the largest population found.

## Incorrect FX conversion

FX conversion is checked directly against `local_amount` because that is the SGD field feeding both the source aggregate and the Ledger's local-SGD movement fields. A misstated `local_amount` passes through both sides of the Ledger-vs-source aggregate, so the 3 flagged rows, 4,467.53, were found by checking `local_amount` against its own inputs (`transaction_amount * exchange_rate`) directly.

## Incorrect legal-entity allocation

The accounting mapping table carries no expected legal entity, so this check compares each transaction's legal entity against the most frequently posted legal entity for the same account elsewhere in the period - a transaction disagreeing with its account's own usual entity is a probable misallocation. 6 transactions flagged, contributing 60,697.50, spread across 4 different account/entity pairs with no single pair dominating - the same substitution Task 1's recomputation applies for this dimension, so this category's transactions are exactly where that recomputation's legal-entity variance traces to.

## Incorrect GL-account assignment

The accounting mapping table's expected GL account is checked the same way its expected cost center is, on the `gl_account` field. 6 transactions post to a GL account that matches only an *expired* mapping row for their own product/transaction-type combination, while a currently-active row (mapped to a different account) also covers their transaction date; a seventh transaction (below) is wrong on GL account and cost center simultaneously. 6 transactions flagged, contributing 53,687.44 - the same substitution Task 1's recomputation applies for this dimension, so this category's transactions are exactly where that recomputation's GL-account variance traces to.

## Incorrect cost-center assignment

The accounting mapping table carries an expected cost center, so this check reuses the same effective-dated join as the accounting mapping validation, excluding transactions the indicator check above already explains (their cost center looks wrong only when checked against the wrong-indicator mapping row) and the one transaction reported separately below (wrong on both GL account and cost center). 3 distinct transactions flagged, contributing 40,036.00 - the same substitution Task 1's recomputation applies for this dimension. A fourth transaction the mapping validation also flags as cost-center-mismatched is excluded here: its product/transaction-type combination carries two currently-active, conflicting mapping rows, so no single expected cost center exists to check it against - see the cost-center population-split note above.

## Incorrect GL-account and cost-center assignment (same transaction)

One transaction posts to a sentinel GL account/cost-center pair that matches no accounting-mapping row under its own classification, and is wrong on both fields against the mapping row its transaction date now falls under. Reported on its own row (9,706.73), so its value is counted exactly once.

## Remediation

- correct the 9 debit/credit indicator, 6 legal-entity, 6 GL-account, 3 cost-center, and 1 combined GL-account/cost-center misclassification directly against their originating records, and re-run Task 1's recomputation to confirm the movement variance closes to zero
- reload or confirm the accounting mapping table's coverage for every product/transaction-type combination actually posted, so every transaction can be validated against an expected GL account and cost center
- review the 21 flagged duplicate/re-posted entries against their source system to confirm which are genuine re-entries versus legitimate repeat transactions, before reversing any
- confirm the FX rate source used for the 3 flagged transactions against the rate actually in force on their transaction date

## Permanent preventive controls

- add a control that flags a transaction whose legal entity, GL account, or cost center disagrees with its account's established pattern, for review before posting - this is the group of controls that would have prevented most of the variance found here
- add a control that blocks a posting against a mapping row that has already expired when a currently-active row exists for the same product/transaction-type combination, so a transaction can't silently carry forward a superseded GL account
- add a control that flags a transaction whose posted classification matches a valid mapping row only under the opposite indicator, for review before posting - this is what catches a flipped debit/credit indicator without needing a dedicated normal-balance reference
- add a mapping-coverage check that runs whenever a new product or transaction type is introduced, alerting before any transaction can post without a matching accounting-mapping row
- add a same-batch duplicate check on the business-field hash used above, run before a batch is accepted into the Ledger feed
- add an FX-tolerance check against the rate in force on the transaction date at the point of posting, upstream of Ledger posting
