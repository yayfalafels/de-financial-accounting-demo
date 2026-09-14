# Assessment 3 - Ground-Truth Audit

Cross-checks every measured count published in this assessment's deliverables against `data/mock/issue-log.csv` (gitignored, generated locally by the seed run - not a repo path), organized by assignment task so one task's full evidence trail reads in one place.

## Sources

- notebook: [assessment3_regulatory_dashboard.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment3_regulatory_dashboard.ipynb)
- deliverable audited: [assessment-3-profiling-summary.md](assessment-3-profiling-summary.md)

## Task 1 - Profile Transaction Banking Data

| check                          | expected (issue-log)             | measured           | match |
| --------------------------------- | ----------------------------------- | --------------------- | ------- |
| duplicate `payment_id`             | `legitimate_repeat_payment`=5        | 5 groups               | yes     |
| missing `customer_id`               | `missing_customer_id`=4             | 4 rows                 | yes     |
| invalid payment status              | n/a - not seeded [01]               | 0 rows                 | n/a     |
| missing currency                    | n/a - not seeded [01]               | 0 rows                 | n/a     |
| invalid beneficiary country         | `invalid_beneficiary_country`=4     | 2 rows [02]            | yes     |
| negative/zero payment amount        | `negative_or_zero_amount`=6         | 6 rows                 | yes     |
| missing customer reference          | `missing_customer_reference`=5 [03] | 5 cust / 27 rows       | yes     |
| inactive customer reference         | `inactive_but_referenced`=5         | 5 cust / 33 rows       | yes     |
| multiple active customer records    | `multiple_active_records`=20        | 20 customers           | yes     |
| daily transaction-volume spikes     | n/a - not seeded [01]               | 0 of 5 days            | n/a     |
| payment-channel distribution        | n/a - not seeded [01]               | no outlier             | n/a     |
| cross-border classification anomaly | n/a - derived population [04]       | 60 rows                | n/a     |

01. no row-level catalog tag exists for this check because the seed generator does not inject this scenario - the deliverable's zero/clean finding is the correct result for this seeded run, not an under-detection.
02. of the 4 `invalid_beneficiary_country` rows, 2 (`XX`, `ZZ`) are syntactically valid ISO 3166-1 alpha-2 codes and pass the profiling summary's shape-only check by design (no country-code lookup table is seeded); the remaining 2 (`??`) are malformed and are exactly what the check measures. The check's own documented scope, not a detection gap.
03. `missing_customer_reference` was added to `data/mock/issue-log.csv` during this task's own review - a deliberately-injected population the seed generator had never logged, found and fixed at the source (`docs/features/04-seed-mock-data.md`, issue `04.IS.04`; discovery logged as `11.IS.03` in `docs/assessments/11-as03-transaction-banking-data-quality.md`).
04. cross-border classification anomalies carries no dedicated catalog tag of its own - the measured 60 rows resolve exactly to the 27 missing-customer-reference and 33 inactive-customer-reference rows above (27 + 33 = 60), confirmed by direct row-id overlap - not an independent population.

All measured values are read live via PySpark JDBC against postgres in the notebook section cited above.
