# Assessment 2 - Reconciliation Framework Design

status: draft

**Task 4 - Create a Reconciliation Framework**

See [overview](assessment-2-overview.md) for the scenario, table shapes, and the seeded-vs-production scale statement.

## Sources

- notebook: [assessment2_gl_reconciliation.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment2_gl_reconciliation.ipynb) -> "Task 4 - Reconciliation Framework" section
- batch: `reconciliation.rc_batch_control.batch_id = 29`

## Metrics

A daily run measures source, Bronze, and GL counts and amounts on a common SGD basis, then derives variance, exception count, and status from them. Bronze has no separate ingestion tier for this dataset, so `bronze_count`/`bronze_amount` read the same source figures `source_count`/`source_amount` do; the two names stay in the framework's vocabulary for consistency across assessments.

| metric                  | value                     |
| -------------------------- | --------------------------- |
| `source_count` / `bronze_count`  | 1,523                        |
| `gl_transaction_count`      | 589                          |
| `source_amount` / `bronze_amount` | SGD 16,999,151.01          |
| `gl_amount`                 | SGD 16,999,151.01            |
| `absolute_variance`         | SGD 0.00                     |
| `percentage_variance`       | 0.0000%                      |
| `exception_count`           | 1,223                        |
| `reconciliation_status`     | `PASS`                       |

`source_count`/`gl_transaction_count` compare two different grains - 1,523 individual transactions against 589 unique `(accounting_date, legal_entity, gl_account, cost_center, currency)` Ledger keys - so a row-count check on this pair states a structural fact of the data model. The framework's count metric is reported for completeness; `PASS`/`FAIL` assignment applies to the amount-basis metrics above, where source and GL sit on the same SGD flow basis and reconcile exactly.

## Tolerance rules

Configurable tolerance is expressed as a lookup keyed on dimension, currency, and GL account:

```
tolerance_rules(dimension, currency NULL=all, gl_account NULL=all,
                abs_tolerance, pct_warning, pct_fail)
```

`currency` and `gl_account` are nullable wildcard columns; the most specific non-null match wins, in the order `(currency, gl_account)` > `currency only` > the `(NULL, NULL)` default row. A currency or account with its own volatility profile - a thinly-traded currency pair, a suspense account under active remediation - takes a tighter or looser pair of thresholds without changing the default for every other combination.

## Status assignment

`PASS`/`WARNING`/`FAIL` default to 0.1% and 1% percentage-variance thresholds, overridable per currency/GL account by the tolerance-rule lookup above:

| status    | condition                  |
| ----------- | ----------------------------- |
| `PASS`      | `percentage_variance < 0.1%`   |
| `WARNING`   | `0.1% <= percentage_variance < 1%` |
| `FAIL`      | `percentage_variance >= 1%`    |

## Persistence for audit and historical analysis

Every daily run inserts a new batch, keeping a batch's measurements available for trend and audit review indefinitely:

| batch date | status |
| ------------ | -------- |
| 2026-09-13   | `FAIL`   |
| 2026-09-13   | `FAIL`   |
| 2026-09-13   | `FAIL`   |
| 2026-09-11   | `FAIL`   |
| 2026-09-11   | `FAIL`   |

Overall batch status carries the worst status across the batch's own measured dimensions - `FAIL` here reflects the count-grain mismatch discussed above, while the amount basis reconciles clean at `PASS` on every run shown. Historical trend analysis is a single query away, filtered to this assessment's own batches and ordered by date.
