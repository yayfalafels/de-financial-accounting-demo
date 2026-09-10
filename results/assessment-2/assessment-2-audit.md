# Assessment 2 - Ground-Truth Audit

Cross-checks every measured count published in this assessment's deliverables against `data/mock/issue-log.csv` (gitignored, generated locally by the seed run - not a repo path), organized by assignment task and subtask rather than by deliverable.

## Sources

- notebook: [assessment2_gl_reconciliation.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment2_gl_reconciliation.ipynb)
- deliverables audited: [assessment-2-reconciliation-results.md](assessment-2-reconciliation-results.md), [assessment-2-mapping-validation.md](assessment-2-mapping-validation.md), [assessment-2-exception-dataset.md](assessment-2-exception-dataset.md), [assessment-2-root-cause-analysis.md](assessment-2-root-cause-analysis.md)

## Task 1 - GL Integrity and Reconciliation

| task ref | check                    | expected (issue-log)              | measured | match |
| -------- | ------------------------ | ---------------------------------- | -------- | ----- |
| 01.01    | arithmetic integrity     | `arithmetic_integrity_violation`=5 | 5        | yes   |
| 01.02-08 | recomputation/dim recon  | n/a [01]                           | 30 keys, 268,250.94 | n/a |

01. **01.02-08** has no single injected-issue tag of its own; three implementation issues were found and fixed while developing this check (`docs/assessments/10-as02-financial-accounting-gl.md`, issues `10.IS.02`, `10.IS.03`, and `10.IS.04`, have the full diagnostic trail for each). First, the recomputation summed `local_amount` where `finance.gl_balance`'s own movement figures are aggregated from `transaction_amount` (confirmed against the seed generator's source) - fixing the column alone produced a 0.00 result. Second, that 0.00 was itself still tautological: the recomputation grouped by each transaction's *actual* `gl_account`/`cost_center`/`legal_entity`, the same values the Ledger was built from, so a genuine misclassification could never surface. Grouping instead by the *expected* classification (`ref.accounting_mapping` where unambiguous, majority-vote for legal entity) surfaced 34 keys, 305,281.76 - materially real, but a residual 2 of those keys turned out to be a third artifact: the mapping lookup is keyed on the transaction's own indicator, so a transaction carrying the wrong indicator was measured against the wrong mapping row's expected value. Correcting the lookup to the indicator a transaction's own actual classification is consistent with (see `10.IS.04`) settled the figure at 30 keys, 268,250.94 - see the reconciliation-results and root-cause-analysis deliverables for the finding this produces and how much of it Task 3's own categories explain.

## Task 2 - Accounting Mapping Validation

| task ref | check                 | expected (issue-log)                    | measured | match |
| -------- | ---------------------- | ----------------------------------------- | -------- | ----- |
| 02.02    | mapping effective-date | `expired_mapping_still_used`=2 [01]       | 0        | no [01] |
| 02.04    | overlapping mapping    | `overlapping_effective_dates`=3           | 8 pairs / 6 combos [02] | yes |
| 02.06    | multi-GL mapping       | `product_multiple_gl_accounts`=2          | 4 combos [02] | yes |
| 02.01    | GL_MISMATCH            | n/a [03]                                  | 403 rows / 319 txns | n/a |
| 02.03    | MAPPING_NOT_FOUND      | `missing_accounting_mapping`=5 combos [04] | 385 rows / 5 combos | yes |

01. **02.02** `EXPIRED_MAPPING`=0 despite `issue-log.csv` naming 2 `expired_mapping_still_used` rows - both expired-row references land on a `(product_code, transaction_type)` pair that *also* carries a currently-valid mapping row, so per the design's own `NOT EXISTS` clause they classify as `GL_MISMATCH` (posted against the wrong, expired account while a valid one existed) rather than `EXPIRED_MAPPING` - confirmed by direct SQL: both injected rows appear in the `GL_MISMATCH` set. Not a defect - the design section states this combination explicitly ("that combination is GL_MISMATCH ... not EXPIRED_MAPPING").
02. **02.04/02.06** `issue-log.csv`'s counts (3 overlapping-date rows, 2 multi-GL rows) undercount the *pairs*/*combos* these two checks report, because a single injected conflict (e.g. one extra mapping row for `P1/DEBIT`) can produce more than one overlapping pair or push a combo's distinct-GL count above the multi-GL threshold - all 6 distinct (product, type) combos across both checks (`P1/CREDIT`, `P1/DEBIT`, `P4/DEBIT`, `P5/DEBIT`, `P8/CREDIT`, `P9/CREDIT`) are traceable to the 7 `ref.accounting_mapping` issue-log rows (2 `expired_mapping_still_used` + 3 `overlapping_effective_dates` + 2 `product_multiple_gl_accounts`).
03. **02.01** has no single injected-issue tag of its own: `GL_MISMATCH` is 99.5% explained by the 6 mapping-conflict combos above (401/403 rows - 4 from task ref 02.06's multi-GL combos, 2 more from task ref 02.04's overlapping-window combos) plus a 2-row residual the mapping-validation deliverable reports as unexplained. Both of those 2 rows (`FTX-0000158`, `FTX-0000660`) are among Task 3's `03.03` incorrect-debit/credit-indicator population (see below) - not a mapping conflict at all, but a transaction whose posted indicator, not its GL account, is wrong; the mapping-validation deliverable itself is not revised, since that connection only emerges from Task 3's later check.
04. **02.03** deliberately injected (`gen_assessment2()`'s `missing_combos`, catalog issue 03 in `docs/features/04-seed-mock-data.md`). The 5 tagged combos (`P2/DEBIT`, `P4/CREDIT`, `P6/CREDIT`, `P7/CREDIT`, `P10/CREDIT`) match the 5 combos the notebook's `MAPPING_NOT_FOUND` query independently finds exactly

## Task 3 - Investigate a Finance Variance

| task ref | check                          | expected (issue-log) [01] | measured    | match   |
| -------- | --------------------------------- | -------------------------- | ------------ | ------- |
| 03.01/02 | duplicate / re-posted entry         | 15 + 8 [02]                  | 21 rows        | close   |
| 03.03    | incorrect debit/credit indicator    | 10 [03]                      | 9              | close   |
| 03.04    | incorrect FX conversion              | 3                             | 3              | yes     |
| 03.06    | posted one accounting day late      | 12 [04]                      | 12 / 0 [04]    | partial |
| 03.07    | incorrect legal-entity allocation    | 6                             | 6              | yes     |
| 03.08    | incorrect cost-center assignment     | 7                             | 5 distinct [05] | partial |

01. **expected** column values are issue-log row counts for `duplicate_accounting_entry`, `posted_twice_different_id`, `incorrect_dr_cr_indicator`, `incorrect_fx_conversion`, `posted_one_day_late`, `incorrect_legal_entity`, `incorrect_cost_center` respectively.
02. **03.01/02** both scenarios manifest identically in the data (same business fields hashed, different transaction id) and are detected by one query per the design; `issue-log.csv` tags 23 rows across the two categories combined, the notebook's single detection finds 21 - a 2-row shortfall not further isolated by this run.
03. **03.03** the swap-and-exact-match method (does a transaction's actual classification exactly match a valid mapping row under the opposite indicator, having failed to match one under its own) finds 9 of 10 tagged rows with zero false positives. The one miss, `FTX-0001358`, has no active mapping row at all for the opposite indicator to match against - genuinely nothing to swap-match, not a method weakness. That same transaction is picked up instead by `03.08`'s cost-center check below (its actual cost center disagrees with the mapping row its own, uncorrected indicator points to) - a reasonable fallback attribution given the swap method can't confirm it.
04. **03.06** the raw day-shift candidate count (12) matches the tagged count exactly - the detection step itself is accurate - but the confirmation step (requiring a candidate's amount to closely match its prior day's own shortfall) rejected all 12, for the same structural reason as `03.03`'s original indirect method: the Ledger is built from each transaction's own (possibly late) posting date, so the Ledger and the recomputation already agree on where a late-posted transaction lands - there is no shortfall left to match against. The root-cause deliverable reports the raw 12 as the finding, with no confirmation attempted.
05. **03.08** of the 5 transactions flagged, 4 (`FTX-0000068/0080/1341/1452`) are genuinely `incorrect_cost_center`-tagged; the 5th (`FTX-0001358`) is `03.03`'s one unconfirmed indicator miss, picked up here instead (see above). 3 tagged `incorrect_cost_center` rows (`FTX-0000028/0915/1427`) are not found by this check at all, before or after `03.03`'s addition - a pre-existing gap this investigation did not further diagnose.

**bridge check** - Task 1's corrected recomputation (30 keys, 268,250.94) is checked directly against Task 3's own categories rather than left as a standalone figure: `03.07` + `03.08` at twice face value (60,697.50 + 55,515.89, x2 - a misposted transaction's value is missing from its correct bucket and present in its wrong one) = 232,426.78, 87% of 268,250.94. Confirmed the two categories' transactions, and `03.03`'s indicator population, don't overlap - zero overlap found across all three. Of the remaining 35,824.16, 22,907.66 (2x `FTX-0001297`'s 11,453.83) traces precisely to one `03.03` transaction whose corrected classification is still one of the six ambiguous mapping-conflict combos, so it can't be substituted into Task 1's recomputation either way. `FTX-0000660`, previously reported here as an unresolved multi-dimension interaction, is now fully explained by `03.03` alone (see `01.02-08` above) - that hypothesis is retracted, not carried forward. The remaining 12,916.50 stays genuinely unexplained.

All measured values are read live via Spark SQL/PySpark against postgres in the notebook section cited above, not hand-typed against the ground truth.
