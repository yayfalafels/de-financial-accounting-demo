# Assessment 2 - Reconciliation Framework Design

status: draft

**Task 4 - Create a Reconciliation Framework**

See [overview](assessment-2-overview.md) for the scenario, table shapes, and the seeded-vs-production scale statement.

## Sources

- notebook: [assessment2_gl_reconciliation.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment2_gl_reconciliation.ipynb) -> "Task 4 - Reconciliation Framework" section
- batch: `reconciliation.rc_batch_control.batch_id = 36`

## Design: one model, three layers

Each transaction's expected legal entity, GL account, and cost center is substituted the same way Task 1's recomputation does - `ref.accounting_mapping` wherever a transaction matches exactly one active mapping row, the account's own majority-vote legal entity where no mapping field covers that dimension - then aggregated to the Ledger's own `(accounting_date, legal_entity, gl_account, cost_center, currency)` grain and compared against `finance.gl_balance`'s posted movements. The total layer sums that comparison's absolute variance across every key. The dimensional layer rolls the same comparison up to one classification dimension at a time, where a single bucket's own sub-total is visible. The category layer checks the named exception categories that explain why a key disagrees. All three read the same recomputation, run on the same SGD basis and the same daily cadence, and are demonstrated below on today's data.

## Total layer

| metric                  | value                     |
| -------------------------- | --------------------------- |
| `source_transaction_count` | 1,523                       |
| `gl_key_count`              | 589                          |
| `gl_amount`                 | SGD 16,999,151.01            |
| `total_layer_variance`      | SGD 297,137.40               |
| `percentage_variance`       | 1.7480%                      |
| `exception_count`           | 1,223                        |
| `reconciliation_status`     | `FAIL`                       |

`total_layer_variance` sums `|debit_variance| + |credit_variance|` across all 589 Ledger keys, comparing each key's posted movement to the recomputation's expected movement for that key - the same figure the dimensional layer below rolls up by dimension and the category layer traces to specific transactions. `source_transaction_count`/`gl_key_count` record the structural grain difference between the two tables (1,523 individual transactions aggregate into 589 Ledger keys) and carry no pass/fail status of their own.

## Dimensional layer

The same source-vs-GL comparison, rolled up to one classification dimension at a time:

| dimension       | distinct values | worst variance %      | status |
| ----------------- | ---------------- | ------------------------ | ------ |
| legal entity        | 4                 | 0.7482% (LE1)              | WARNING |
| GL account           | 16                | 4.6907% (GL1005)           | FAIL   |
| cost center          | 11                | 2.2957% (CC09)             | FAIL   |
| currency             | 3                 | 0.0%                       | PASS   |
| accounting date       | 5                 | 0.0%                       | PASS   |

Currency and accounting date reconcile exactly at every value; legal entity, GL account, and cost center each carry a real, material variance once transactions are checked against their expected classification. The dimensional-level movement variance totals SGD 297,137.40 across 30 of the 589 Ledger keys, matching the total layer's own figure exactly - the 559 keys under tolerance contribute nothing to either.

## Category layer

The named exception categories, checked independently, are what a daily run reports as the actionable list once a dimension fails:

| category                              | rows | value                  |
| -------------------------------------- | ----------- | ------------------------ |
| duplicate / re-posted accounting entry | 21          | SGD 255,845.35            |
| incorrect debit/credit indicator       | 9           | SGD 78,480.32             |
| incorrect FX conversion                | 3           | SGD 4,467.53              |
| missing accounting mapping             | 385         | SGD 4,387,367.89          |
| posted one accounting day late         | 0 confirmed | SGD 0.00                  |
| incorrect legal-entity allocation      | 6           | SGD 60,697.50             |
| incorrect GL-account assignment        | 6           | SGD 53,687.44             |
| incorrect cost-center assignment       | 3           | SGD 40,036.00             |
| incorrect GL-account + cost-center     | 1           | SGD 9,706.73              |

The last four rows - 16 transactions in total - are the categories that move the dimensional layer's figure; reverting exactly these 16 to their actual, as-posted classification and re-running the dimensional comparison closes it to 0 keys / SGD 0.00. The framework's daily exception list would name these 16 transactions directly. The first five rows are real, independently-verified findings the assignment names as candidate causes; none of them moves the dimensional or total layer's own arithmetic.

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
| 2026-09-14   | `FAIL`   |
| 2026-09-13   | `FAIL`   |
| 2026-09-13   | `FAIL`   |
| 2026-09-13   | `FAIL`   |
| 2026-09-13   | `FAIL`   |

Overall batch status is the total layer's own status - `FAIL` on every run shown, since the movement variance exceeds the 1% threshold each time; the dimensional and category layers above are what a daily run relies on to know why. Historical trend analysis is a single query away, filtered to this assessment's own batches and ordered by date.
