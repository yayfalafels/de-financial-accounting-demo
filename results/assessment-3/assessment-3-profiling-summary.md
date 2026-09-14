# Assessment 3 - Data Profiling Summary

**Task 1 - Profile Transaction Banking Data**

See [overview](assessment-3-overview.md) for the scenario, the four dataset shapes, and the seeded-vs-production scale statement.

## Sources

- notebook: [assessment3_regulatory_dashboard.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment3_regulatory_dashboard.ipynb) -> "Task 1 - Profile Transaction Banking Data" section
- tables profiled: `source.payment_transactions`, `bronze.payment_transactions`, `bronze.customer_master`

## Definitions

- **valid payment status**: `COMPLETED, PENDING, FAILED, REJECTED`
- **beneficiary-country shape check**: `beneficiary_country` matches `^[A-Z]{2}$` - a syntactically valid but non-existent code (e.g. `ZZ`) still passes, since no country-code lookup table is seeded to confirm actual country membership
- **volume-spike threshold**: a day's transaction count more than 2 standard deviations from the seeded period's own mean
- **channel-share threshold**: a channel's daily share of volume more than 15 percentage points from its own period-average share

## Findings

| check                                    | measured                                    |
| ------------------------------------------ | ---------------------------------------------- |
| record count / distinct `payment_id`       | 2005 / 2000 (5 duplicate groups) [01]           |
| missing `customer_id`                       | 4 rows                                          |
| invalid payment status                      | 0 rows                                          |
| missing currency                            | 0 rows                                          |
| invalid beneficiary country (shape)         | 2 rows                                          |
| negative or zero payment amount             | 6 rows                                          |
| missing customer reference record           | 27 rows / 5 distinct customers [02]             |
| payment linked to inactive customer record  | 33 rows / 5 distinct customers [02]             |
| multiple active customer records            | 20 customers                                    |
| daily transaction-volume spikes             | 0 of 5 days flagged [03]                        |
| payment-channel distribution                | API 492, BRANCH 515, INTERNET 550, MOBILE 468 [03] |
| cross-border classification anomalies       | 60 rows [04]                                    |

**date range** `payment_date` spans 2026-08-17 to 2026-08-21.

Notes below report what this level of analysis can deduce and the open question it raises for the next level.

01. the 5 duplicate `payment_id` groups each carry exactly one extra row (2005 total rows against 2000 distinct ids). Whether a given pair is a genuine repeated payment or an artifact of file reprocessing is an open question for the complex-issue investigation.
02. these are two distinct populations - "missing customer reference" has no `customer_master` row for the `customer_id` at all, "inactive customer reference" has history but none of it currently open. Together they touch 10 of the 300 distinct `customer_id`s referenced in `bronze.payment_transactions`, against `customer_master`'s 295-customer roster. Whether that gap is limited to these 10 customers or extends further under a different signal is an open question for the reconciliation task.
03. the closest daily count to the volume-spike threshold is 2026-08-19 (421 transactions, z = 1.78), short of the flagged bar; no channel/day combination crosses the 15-percentage-point share threshold either - this seeded run shows no distributional anomaly by either measure.
04. every one of the 60 cross-border classification anomalies falls inside the missing/inactive-customer-reference populations above (27 + 33 = 60) - the domestic/cross-border test cannot resolve a payment against a customer record that either does not exist or is not currently effective on the payment date. No anomaly traces to case or whitespace noise in the country codes themselves. Whether the classification rule itself is adequate once every payment does resolve to an effective customer record is an open question for the complex-issue investigation.

## Spark-scale handling at production volume

Every check above executes as a full in-memory scan against the seeded volume budget. At the assignment's production scale the same logic applies unchanged, run against a table partitioned by `payment_date` so date-scoped checks skip partitions outside their window, an approximate first pass (`approx_count_distinct`) ahead of any exact duplicate-group count, a broadcast join for every lookup against the small `customer_master` table, and column pruning carried through automatically by the query engine reading only the fields each check touches. See the notebook section cited above for the full narrative.

## Critical data elements

Nominated against the checks and joins actually exercised by this assessment's tasks - a column earns the label when a specific check or reconciliation cut depends on it.

| id | column                | why critical                                                       |
| -- | ---------------------- | --------------------------------------------------------------------- |
| 01 | payment_id              | business key - drives duplicate-id detection and every downstream join |
| 02 | customer_id             | ties a payment to its customer reference record and reconciliation cut |
| 03 | amount                  | negative/zero-amount check and every reconciliation amount dimension   |
| 04 | currency                | missing-currency check and the reconciliation currency dimension       |
| 05 | status                  | invalid-status check - filters which payments are reportable at all    |
| 06 | beneficiary_country     | beneficiary-country shape check and the cross-border classification    |
| 07 | payment_date            | reconciliation date dimension and the late-arrival investigation       |
| 08 | payment_channel         | payment-channel distribution check                                     |
| 09 | residence_country       | the other half of the cross-border classification                     |
| 10 | effective_start_date / effective_end_date | drives the customer-reference and overlapping-record checks |

`account_id`, `payment_timestamp`, `payment_type`, and `legal_entity` are excluded - none is read by any task 1 check in this assessment's scope.
