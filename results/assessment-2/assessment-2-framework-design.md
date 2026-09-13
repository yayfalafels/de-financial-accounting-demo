# Assessment 2 - Reconciliation Framework Design

status: draft

**Task 4 - Create a Reconciliation Framework**

See [overview](assessment-2-overview.md) for the scenario, table shapes, and the seeded-vs-production scale statement.

## Sources

- notebook: [assessment2_gl_reconciliation.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment2_gl_reconciliation.ipynb) -> "Task 4 - Reconciliation Framework" section
- batch: `reconciliation.rc_batch_control.batch_id = 30`

## Design: three layers

`finance.gl_balance` is generated as a direct aggregation of `bronze.finance_transactions` - every GL movement figure is built from the same rows the source table holds, with the same values. One consequence follows directly: a comparison between a GL-side total and a source-side total, where both sides read actual, as-posted values, is comparing one total to itself. Proof, run directly against this dataset: `SUM(GL debit) - SUM(GL credit)` = SGD -127,183.63, exactly equal to `SUM(source local_amount, signed by its own posted debit/credit indicator)` = SGD -127,183.63 - the two are identical to the cent, for the whole table. A total-layer check built this way returns a clean match for every one of the assignment's seven candidate causes, because neither side ever carries a figure independent of the other to disagree with.

A reusable framework needs two further layers that substitute an *expected* value for at least one side. Even then, the total layer stays fixed: reclassifying which legal entity, GL account, or cost center a transaction's value is grouped under redistributes that value among buckets, but grouping is a partition of one fixed sum - it cannot change the total across all buckets combined, at any level of substitution. A dimensional layer, rolling the same source-vs-GL comparison up to one classification dimension at a time, is where a redistribution first becomes visible, because it looks at one bucket's own sub-total. A category layer then checks the named exception categories that explain why a dimension disagrees. All three run on the same SGD basis and the same daily cadence; each is demonstrated below on today's data.

## Total layer

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

This layer's `PASS` carries no diagnostic weight on its own: given how `finance.gl_balance` is built, it returns `PASS` regardless of which (if any) of the seven candidate causes are present in a given day's data - see the proof above. It stays in the framework because a real deployment's "expected" figure would typically come from a genuinely independent source (a separate sub-ledger, a prior reconciled balance) capable of disagreeing with the platform on more than classification; this dataset supplies no such independent source, so `source_amount` is derived from the same rows `gl_amount` is, and the two dimensions Task 4 measures at this layer - `source_count`/`gl_transaction_count` (a structural grain difference: 1,523 individual transactions against 589 unique `(accounting_date, legal_entity, gl_account, cost_center, currency)` Ledger keys) and `source_amount`/`gl_amount` - are reported for completeness.

## Dimensional layer

The same source-vs-GL comparison, rolled up to one classification dimension at a time:

| dimension       | distinct values | worst variance %      | status |
| ----------------- | ---------------- | ------------------------ | ------ |
| legal entity        | 4                 | 0.7482% (LE1)              | WARNING |
| GL account           | 16                | 4.6907% (GL1005)           | FAIL   |
| cost center          | 11                | 2.2957% (CC09)             | FAIL   |
| currency             | 3                 | 0.0%                       | PASS   |
| accounting date       | 5                 | 0.0%                       | PASS   |

Currency and accounting date reconcile exactly at every value; legal entity, GL account, and cost center each carry a real, material variance once transactions are checked against their expected classification. The dimensional-level movement variance totals SGD 297,137.40 across 30 of the 589 Ledger keys - the figure the total layer's clean `PASS` cannot surface.

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
| 2026-09-13   | `FAIL`   |
| 2026-09-13   | `FAIL`   |
| 2026-09-13   | `FAIL`   |
| 2026-09-13   | `FAIL`   |
| 2026-09-11   | `FAIL`   |

Overall batch status carries the worst status across the batch's own measured dimensions - `FAIL` here reflects the total layer's count-grain mismatch, while the total layer's amount metric reconciles clean at `PASS` on every run shown; the dimensional and category layers above are the ones a daily run would actually rely on to know why. Historical trend analysis is a single query away, filtered to this assessment's own batches and ordered by date.
