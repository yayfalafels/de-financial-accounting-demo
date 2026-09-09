# Assessment 2 - Ground-Truth Audit

Cross-checks every measured count published in this assessment's deliverables against `data/mock/issue-log.csv` (gitignored, generated locally by the seed run - not a repo path), organized by assignment task and subtask rather than by deliverable.

## Sources

- notebook: [assessment2_gl_reconciliation.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment2_gl_reconciliation.ipynb)
- deliverables audited: [assessment-2-reconciliation-results.md](assessment-2-reconciliation-results.md), [assessment-2-mapping-validation.md](assessment-2-mapping-validation.md), [assessment-2-exception-dataset.md](assessment-2-exception-dataset.md)

## Task 1 - GL Integrity and Reconciliation

| task ref | check                    | expected (issue-log)              | measured | match |
| -------- | ------------------------ | ---------------------------------- | -------- | ----- |
| 01.01    | arithmetic integrity     | `arithmetic_integrity_violation`=5 | 5        | yes   |
| 01.02-08 | recomputation/dim recon  | n/a [01]                           | see reconciliation-results | n/a |

01. **01.02-08** has no single injected-issue tag of its own - the widespread dimensional variance these checks surface is the combined effect of every task 3 issue category (duplicate entries, wrong dr/cr indicator, FX conversion, missing mappings, late posting, misallocated legal entity/cost center) landing in `bronze.finance_transactions`, decomposed by category only once task 3 runs.

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
03. **02.01** has no single injected-issue tag of its own: `GL_MISMATCH` is 99.5% explained by the 6 mapping-conflict combos above (401/403 rows - 4 from `10.CK.14`'s multi-GL combos, 2 more from `10.CK.12`'s overlapping-window combos) plus a 2-row unexplained residual (see mapping-validation deliverable).
04. **02.03** deliberately injected (`gen_assessment2()`'s `missing_combos`, catalog issue 03 in `docs/features/04-seed-mock-data.md`) but never logged to `issue-log.csv` until that feature's `04.IS.03` was fixed - previously reported here as an unexplained "n/a" data characteristic; corrected once the seed generator's `log_issue()` gap was fixed and reseeded. The 5 tagged combos (`P2/DEBIT`, `P4/CREDIT`, `P6/CREDIT`, `P7/CREDIT`, `P10/CREDIT`) match the 5 combos the notebook's `MAPPING_NOT_FOUND` query independently finds exactly, and the underlying seeded data (row counts, `bronze.finance_transactions`/`ref.accounting_mapping` content) is unchanged by the fix - it only corrected the ground-truth log, confirmed by an identical reseed under `MOCK_DATA_SEED=42`.

All measured values are read live via Spark SQL against postgres in the notebook section cited above, not hand-typed against the ground truth.
