# Assessment 2 - Exception Dataset

status: draft

**Task 2 - Validate Accounting Mapping / Task 3 - Investigate a Finance Variance**

See [overview](assessment-2-overview.md) for the scenario, table shapes, and the seeded-vs-production scale statement. See [mapping validation](assessment-2-mapping-validation.md) and [root-cause analysis](assessment-2-root-cause-analysis.md) for the per-check breakdown behind each category below.

## Sources

- notebook: [assessment2_gl_reconciliation.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment2_gl_reconciliation.ipynb) -> "Exception Dataset" section

## Schema

Minimum columns: `transaction_id`, `issue_type`, `source_value`, `comparison_value`, `variance`. `source_value`/`comparison_value` hold whichever field the check actually compared (a GL account, a cost center, an FX-derived amount); `variance` is populated only where a numeric difference applies (FX conversion, unmapped transaction value). A transaction matching more than one accounting-mapping row is evaluated against each match independently (see the mapping validation deliverable), so it can carry more than one row under the same `issue_type`.

| issue_type            | rows | materialisation   |
| ------------------------ | ---- | -------------------- |
| `GL_MISMATCH`             | 403  | see exception rows   |
| `MAPPING_NOT_FOUND`       | 385  | see exception rows   |
| `UNMAPPED_VARIANCE`       | 385  | see exception rows   |
| `DUPLICATE_ENTRY`         | 21   | see exception rows   |
| `WRONG_COST_CENTER`       | 11   | see exception rows   |
| `WRONG_DR_CR_INDICATOR`   | 9    | see exception rows   |
| `WRONG_LEGAL_ENTITY`      | 6    | see exception rows   |
| `FX_CONVERSION_ERROR`     | 3    | see exception rows   |
| **total**                  | **1223** |                    |

**Materialisation**: the full exception dataset lives in the notebook's own cell output (`exception_dataset`, cached and printed by class), git-tracked as part of the committed, executed notebook. This deliverable embeds only representative rows below.

| transaction_id | issue_type          | source_value | comparison_value | variance |
| ---------------- | ---------------------- | ------------- | ------------------- | -------- |
| FTX-0000008       | GL_MISMATCH             | GL1007         | GL1014               | -        |
| FTX-0000019       | MAPPING_NOT_FOUND       | GL9999         | -                     | -        |
| FTX-0001392       | WRONG_LEGAL_ENTITY      | LE1            | LE3                   | -        |
| FTX-0000080       | WRONG_COST_CENTER       | CC04           | CC08                  | -        |
| FTX-0000660       | WRONG_DR_CR_INDICATOR   | DEBIT          | -                     | 17900.46 |
| FTX-0000072       | FX_CONVERSION_ERROR     | 27475.7        | 24977.91              | 2497.79  |
| FTX-DUP001503     | DUPLICATE_ENTRY         | 12574.31       | -                     | 12574.31 |

Full per-category rows are in the notebook output, not reproduced here.
