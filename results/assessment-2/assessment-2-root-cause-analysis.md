# Assessment 2 - Root-Cause Analysis

status: draft

**Task 3 - Investigate a Finance Variance**

See [overview](assessment-2-overview.md) for the scenario, table shapes, and the seeded-vs-production scale statement. See [reconciliation results](assessment-2-reconciliation-results.md) for the variance this investigation decomposes.

## Sources

- notebook: [assessment2_gl_reconciliation.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment2_gl_reconciliation.ipynb) -> "Task 3 - Investigate a Finance Variance" section

## Method and headline finding

Each of the categories the scenario names is checked independently rather than searched for transaction by transaction. Task 1's expected-classification recomputation found SGD 297,137.40 in Ledger-vs-transaction movement variance. Three classification dimensions - legal-entity allocation, GL-account assignment, and cost-center assignment - are exactly the fields Task 1's recomputation substitutes an expected value for, so they are the candidates that can explain it: a misposted transaction is missing from its correct bucket and present in its wrong one, so its value counts twice toward the variance.

## Findings

### Categories that explain the Ledger movement variance

These four are the only categories Task 1's recomputation substitutes an expected value for, so they are the only ones capable of moving - and, together, the only ones needed to fully explain - the SGD 297,137.40 Ledger-vs-source movement variance. [Bridging the variance](#bridging-the-variance) below shows exactly how these four add up to that figure.

| category                              | rows / keys | value                  |
| -------------------------------------- | ----------- | ------------------------ |
| incorrect legal-entity allocation      | 6           | 60,697.50                 |
| incorrect GL-account assignment        | 6           | 53,687.44                 |
| incorrect cost-center assignment       | 3 [01]      | 40,036.00 [01]            |
| incorrect GL-account + cost-center [01] | 1          | 9,706.73 [01]             |

01. **cost-center population split** - one transaction the mapping validation also flags as `GL_MISMATCH` posts to a sentinel account/cost-center pair wrong on both fields at once, reported on its own row so no dollar is counted under two headings. A further, genuinely cost-center-mismatched transaction is excluded from every row above: its product/transaction-type combination carries two currently-active, conflicting mapping rows (see mapping validation's overlapping-mapping finding), so Task 1's recomputation has no single unambiguous expected value to substitute for it and it cannot move the movement variance either way - it remains a real classification error, just not one this particular reconciliation can bridge to.

### Other findings - not reflected in the Ledger movement variance

Each of these is a real, independently-verified finding, but **none of them changes Task 1's Ledger-vs-source movement figure at all** - see the note for each for why. Their dollar values are not on the same basis as the 297,137.40 above and do not net against it in any way; `missing accounting mapping`'s 4,387,367.89 in particular is a disclosure total (the combined value of transactions with nothing to check them against), not a variance, and dwarfs the Ledger variance in scale precisely because it is a different kind of number.

| category                              | rows / keys | value                  |
| -------------------------------------- | ----------- | ------------------------ |
| duplicate / re-posted accounting entry | 21          | 255,845.35 [02]           |
| incorrect debit/credit indicator       | 9 [03]      | 78,480.32 [02]            |
| incorrect FX conversion                | 3           | 4,467.53 [02]             |
| missing accounting mapping             | 385         | 4,387,367.89 [02][04]     |
| posted one accounting day late         | 12 / 0 [05] | -                         |

02. **duplicate entries, indicator, FX conversion, missing accounting mapping** - real, individually-verified findings, but none of them is a classification category Task 1's recomputation substitutes for, so none is expected to explain the movement variance (see the per-category notes below for why).
03. **indicator** - `ref.accounting_mapping` keys the expected GL account and cost center off *both* the product code and the debit/credit indicator, so a transaction carrying the wrong indicator often becomes an exact match for a *different*, valid mapping row under the opposite indicator: not some field being wrong, but every field being right, filed under the wrong sign. 9 transactions flagged this way. This is independent of Task 1's Ledger reconciliation - it reads the transaction and mapping data directly - so it isn't affected by that reconciliation's own finding that a flipped indicator is pass-through to the Ledger's movement figures.
04. **missing accounting mapping** - an audit-confidence gap, not a Ledger variance: these transactions keep their actual classification in Task 1's recomputation (no expected value to substitute), so they cannot contribute to the variance found.
05. **late posting** - 12 transactions post exactly one calendar day after their transaction date; 0 confirmed against the prior day's own movement shortfall - the Ledger is built from each transaction's own (possibly late) posting date, so the Ledger and the recomputation already agree on where a late-posted transaction lands.

## Bridging the variance

Task 1's expected-classification recomputation substitutes a different value for exactly 16 transactions across three classification dimensions - legal-entity, GL-account, and cost-center (one transaction wrong on both fields at once) - every other transaction's actual and expected classification already agree, contributing identically to both the Ledger and the recomputation. The four categories are added back one at a time, in the order below, each measured as the exact increase in variance that category's own correction contributes on top of the ones already added - not each category's own published value taken in isolation, and not a face-value estimate. Measured this way, the four amounts add up to the total by construction, with nothing left over:

| step                                                | amount        |
| ------------------------------------------------------ | --------------- |
| total GL variance (Task 1 recomputation)                 | 297,137.40        |
| incorrect legal-entity allocation                         | 121,395.00        |
| incorrect GL-account assignment [01]                      | 76,256.94         |
| incorrect cost-center assignment                           | 80,072.00         |
| incorrect GL-account + cost-center (same transaction)       | 19,413.46         |
| = sum of the four categories                             | 297,137.40        |
| = residual                                              | 0.00              |

01. **incorrect GL-account assignment** contributes 76,256.94 here, not 2 x its 53,687.44 face value (107,374.88): legal-entity's correction is already in place by the time GL-account's is added, and some of the same five-key posting buckets are touched by both, so part of GL-account's effect is already reflected in the legal-entity row above it rather than adding again on top. Cost-center and the combined transaction do not share a bucket with anything already added, so their rows land exactly on twice their own face value (40,036.00 x 2 and 9,706.73 x 2).

0 of 589 keys exceed tolerance once all four corrections are in place, matching the Ledger exactly - the full SGD 297,137.40 is completely explained by these four categories and by no other transaction or category. Two further transactions are confirmed, real misclassifications - one flagged by the indicator check, one by the cost-center check - that cannot be added to this table at all, because both post under a product/transaction-type combination with more than one currently-active, conflicting mapping row, leaving no single unambiguous expected value to substitute either way (see finding 05 above and the mapping validation's overlapping-mapping finding).

## Duplicate / re-posted accounting entries

Business fields (every column except the transaction id) hashed per transaction, grouped by posting date; every row sharing a hash and posting date beyond the first is flagged, indicating either the same entry recorded twice or the same transaction re-posted under a different id - the two scenarios the assignment names separately are not distinguishable from this data alone, since both leave an identical signature. 21 rows flagged this way, contributing 255,845.35 - already included in the Ledger's own recorded movement, since the Ledger is built from the same (duplicated) transaction data at its actual classification.

## Incorrect debit/credit indicator

`ref.accounting_mapping` keys the expected GL account and cost center off both the product code and the debit/credit indicator - a product's expected classification differs between its debit rows and its credit rows. A transaction whose actual classification fails to match any currently-active mapping row for its own posted indicator, but exactly matches one for the opposite indicator, is flagged: its own values are internally consistent with a real, valid combination, just filed under the wrong sign. 9 transactions flagged this way, contributing 78,480.32. This check does not depend on the Ledger at all, unlike a check built on Task 1's own recomputation output would - the Ledger's movement figures are aggregated from the same (already-mutated) indicator, so a flipped transaction is baked into both sides identically and leaves no signature there to find.

## Missing accounting mapping

385 transactions have no accounting mapping covering their product code and debit/credit type, so their General Ledger posting cannot be confirmed correct or incorrect. Their combined value, 4,387,367.89, is a disclosure figure - the largest population found - not a Ledger discrepancy.

## Incorrect FX conversion

FX conversion is checked directly against `local_amount` because that is the SGD field feeding both the source aggregate and the Ledger's local-SGD movement fields. A misstated `local_amount` passes through both sides of the Ledger-vs-source aggregate, so the 3 flagged rows, 4,467.53, were found by checking `local_amount` against its own inputs (`transaction_amount * exchange_rate`) directly.

## Incorrect legal-entity allocation

The accounting mapping table carries no expected legal entity, so this check compares each transaction's legal entity against the most frequently posted legal entity for the same account elsewhere in the period - a transaction disagreeing with its account's own usual entity is a probable misallocation. 6 transactions flagged, contributing 60,697.50, spread across 4 different account/entity pairs with no single pair dominating - the same substitution Task 1's recomputation applies for this dimension, so this category's transactions are exactly where that recomputation's legal-entity variance traces to.

## Incorrect GL-account assignment

The accounting mapping table's expected GL account is checked the same way its expected cost center is - the same effective-dated join the accounting mapping validation uses - but on the `gl_account` field specifically. 6 transactions post to a GL account that matches only an *expired* mapping row for their own product/transaction-type combination, while a currently-active row (mapped to a different account) also covers their transaction date; a seventh transaction (below) is wrong on GL account and cost center simultaneously. 6 transactions flagged, contributing 53,687.44 - the same substitution Task 1's recomputation applies for this dimension, so this category's transactions are exactly where that recomputation's GL-account variance traces to.

## Incorrect cost-center assignment

The accounting mapping table does carry an expected cost center, so this check reuses the same effective-dated join as the accounting mapping validation, excluding transactions the indicator check above already explains (their cost center looks wrong only when checked against the wrong-indicator mapping row) and the one transaction reported separately below (wrong on both GL account and cost center). 3 distinct transactions flagged, contributing 40,036.00 - the same substitution Task 1's recomputation applies for this dimension. A fourth transaction the mapping validation also flags as cost-center-mismatched is excluded here: its product/transaction-type combination carries two currently-active, conflicting mapping rows, so no single expected cost center exists to check it against - see finding 05 above.

## Incorrect GL-account and cost-center assignment (same transaction)

One transaction posts to a sentinel GL account/cost-center pair that matches no accounting-mapping row at all under its own classification, and is wrong on both fields against the mapping row its transaction date now falls under. Reported on its own row (9,706.73) rather than under either category above, so this transaction's value is not counted twice.

## Remediation

- correct the 9 debit/credit indicator, 6 legal-entity, 6 GL-account, 3 cost-center, and 1 combined GL-account/cost-center misclassification directly against their originating records, and re-run Task 1's recomputation to confirm the movement variance closes to zero
- reload or confirm the accounting mapping table's coverage for every product/transaction-type combination actually posted, so every transaction can be validated against an expected GL account and cost center
- review the 21 flagged duplicate/re-posted entries against their source system to confirm which are genuine re-entries versus legitimate repeat transactions, before reversing any
- confirm the FX rate source used for the 3 flagged transactions against the rate actually in force on their transaction date

## Permanent preventive controls

- add a control that flags a transaction whose legal entity, GL account, or cost center disagrees with its account's established pattern, for review before posting rather than after - this is the group of controls that would have prevented most of the variance found here
- add a control that blocks a posting against a mapping row that has already expired when a currently-active row exists for the same product/transaction-type combination, so a transaction can't silently carry forward a superseded GL account
- add a control that flags a transaction whose posted classification doesn't match any valid mapping row for its own indicator but does for the opposite one, for review before posting - this is what catches a flipped debit/credit indicator without needing a dedicated normal-balance reference
- add a mapping-coverage check that runs whenever a new product or transaction type is introduced, alerting before any transaction can post without a matching accounting-mapping row
- add a same-batch duplicate check on the business-field hash used above, run before a batch is accepted into the Ledger feed rather than discovered afterward
- add an FX-tolerance check against the rate in force on the transaction date at the point of posting - the standard Ledger-vs-transaction reconciliation cannot catch this on its own when the same misstated SGD amount feeds both sides, so this control needs to sit upstream of Ledger posting
