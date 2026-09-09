# Assessment 2 - Exception Dataset

status: draft

**Task 2 - Accounting Mapping Validation (exception dataset)**

See [overview](assessment-2-overview.md) for the scenario, table shapes, and the seeded-vs-production scale statement. See [assessment-2-mapping-validation.md](assessment-2-mapping-validation.md) for the per-check breakdown.

## Sources

- notebook: [assessment2_gl_reconciliation.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment2_gl_reconciliation.ipynb) -> "Exception Dataset" section
- cited by notebook section, not a `reconciliation.rc_batch_control.batch_id` - see the coverage note below
- ground-truth verification: [assessment-2-audit.md](assessment-2-audit.md)

## Coverage - task 2 categories only, extended in 10.07

This dataset unions the row sets from **10.CK.09**-**10.CK.14** (task 2's own mapping-validation checks). **10.CK.15**-**10.CK.22** (task 3's variance-investigation categories: duplicate entries, wrong debit/credit indicator, FX conversion, late posting, misallocated legal entity/cost center) are added when task 3 (10.07) runs - this deliverable is extended in that cycle rather than restating numbers not yet produced. `10.CK.12`/`10.CK.14` are mapping-level findings with no `transaction_id` to key on and are not part of this per-transaction dataset - see the mapping-validation deliverable for those two.

## Exception dataset schema

Minimum columns: `transaction_id`, `issue_type`, `source_value`, `gl_value`, `variance`. No `batch_id` column - task 2 findings are cited by notebook section, not a `reconciliation.rc_batch_control` batch (see the tracker's workflow cycle note 01; only task 1/4 write to `reconciliation.rc_*`). `source_value`/`gl_value` hold the transaction's actual `gl_account` and the mapping's `expected_gl_account` respectively, where a mapping exists; `variance` is unused for these categories (no numeric amount is being compared) and stays `NULL`.

| issue_type            | rows | materialisation   |
| ----------------------- | ---- | -------------------- |
| `GL_MISMATCH`            | 403  | see exception rows   |
| `NO_EFFECTIVE_MAPPING`   | 0    | -                     |
| `MAPPING_NOT_FOUND`      | 385  | see exception rows   |
| `EXPIRED_MAPPING`        | 0    | -                     |
| **total**                | **788** |                    |

**Materialisation**: the full 788-row exception dataset lives in the notebook's own cell output (`exception_dataset`, cached and printed by class), git-tracked as part of the committed, executed notebook. This deliverable embeds only representative rows below.

| transaction_id | issue_type        | source_value | gl_value | variance |
| --------------- | -------------------- | ------------- | --------- | -------- |
| FTX-0000008     | GL_MISMATCH           | GL1007         | GL1014     | -        |
| FTX-0000012     | GL_MISMATCH           | GL1007         | GL1014     | -        |
| FTX-0000019     | MAPPING_NOT_FOUND     | GL9999         | -           | -        |
| FTX-0000026     | MAPPING_NOT_FOUND     | GL9999         | -           | -        |

Full per-category rows (394 more `GL_MISMATCH`, 383 more `MAPPING_NOT_FOUND`) are in the notebook output, not reproduced here.
