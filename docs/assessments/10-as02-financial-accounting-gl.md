# Assessment 2 - Financial Accounting and General Ledger Reconciliation - Feature tracker
>Review the guidelines before performing any actions including edits on the document

## 10 (pending) assessment 2 - financial accounting and GL reconciliation

## Contents

- [Tasks](#tasks)
- [Scope](#scope)
- [References](#references)
- [Design](#design)
  - [prerequisites](#prerequisites)
  - [assessment task to deliverable map](#assessment-task-to-deliverable-map)
  - [workflow cycle](#workflow-cycle)
  - [assessment context documentation](#assessment-context-documentation)
  - [GL integrity design - task 1](#gl-integrity-design--task-1)
  - [mapping validation design - task 2](#mapping-validation-design--task-2)
  - [variance investigation design - task 3](#variance-investigation-design--task-3)
  - [reconciliation framework design - task 4](#reconciliation-framework-design--task-4)
  - [exception dataset](#exception-dataset)
  - [advanced sql coverage](#advanced-sql-coverage)
  - [notebook organisation](#notebook-organisation)
  - [idempotency / rerun-safety](#idempotency--rerun-safety)
  - [environment & secrets](#environment--secrets)
  - [workflow validation runner](#workflow-validation-runner)
  - [publishing](#publishing)
- [Test cases](#test-cases)
- [Edit locations](#edit-locations)
- [Implement](#implement)
- [Validate](#validate)
- [Guideline](#guideline)

## Tasks

| id    | seq | status  | milestone                                |
| ----- | --- | ------- | ----------------------------------------- |
| 10.01 | 01  | closed  | design                                    |
| 10.02 | 02  | pending | prerequisites and seed data readiness     |
| 10.03 | 03  | pending | assessment scope and context write-up     |
| 10.04 | 04  | pending | task 1 - GL integrity and reconciliation  |
| 10.05 | 05  | pending | task 2 - accounting mapping validation    |
| 10.06 | 06  | pending | exception dataset                         |
| 10.07 | 07  | pending | task 3 - finance variance investigation   |
| 10.08 | 08  | pending | task 4 - reconciliation framework design  |
| 10.09 | 09  | pending | business-facing summary                   |
| 10.10 | 10  | pending | notebook consolidation and clean rerun    |
| 10.11 | 11  | pending | deliverable review and status promotion   |
| 10.12 | 12  | pending | publish assessment site                   |
| 10.IS | 13  | pending | validate                                  |

## Scope

Assessment 2 of the **assignment design doc** end to end - validate `finance.gl_balance` arithmetic integrity, independently recompute GL movements from `bronze.finance_transactions`, validate `ref.accounting_mapping`, explain the SGD-scale finance variance symptom, design a reusable reconciliation framework, and publish the resulting deliverable set together with the assignment context that motivated it - see [milestones.md](../milestones.md)'s `assessment 2` entry for the milestone-level statement this tracker executes.

**assessment scope**

- **scenario** Finance reports that balances generated from the new data platform do not reconcile with the bank's General Ledger.  trace the cause(s) to: 
  - source data
  - ingestion
  - transformation
  - FX conversion
  - accounting classification
  - duplicate transactions
  - missing transactions
- **the problem** platform closing balance disagrees with the expected closing balance by a material amount
- **checks to perform**

| id       | task ref | scope                  | check                                                |
| -------- | -------- | ----------------------- | ----------------------------------------------------- |
| 10.CK.01 | 01.01    | GL integrity            | opening + debit - credit = closing arithmetic check   |
| 10.CK.02 | 01.02    | GL integrity            | recomputed debit movement vs `gl_balance.debit_movement`  |
| 10.CK.03 | 01.03    | GL integrity            | recomputed credit movement vs `gl_balance.credit_movement` |
| 10.CK.04 | 01.04    | dim reconcile            | legal entity                                          |
| 10.CK.05 | 01.05    | dim reconcile            | GL account                                            |
| 10.CK.06 | 01.06    | dim reconcile            | cost center                                           |
| 10.CK.07 | 01.07    | dim reconcile            | currency                                              |
| 10.CK.08 | 01.08    | dim reconcile            | accounting date                                       |
| 10.CK.09 | 02.01    | mapping validate         | transaction posted to expected GL account             |
| 10.CK.10 | 02.02    | mapping validate         | mapping effective-date validity                       |
| 10.CK.11 | 02.03    | mapping validate         | transactions with missing accounting mapping          |
| 10.CK.12 | 02.04    | mapping validate         | overlapping effective-date mapping ranges             |
| 10.CK.13 | 02.05    | mapping validate         | expired mapping still referenced                      |
| 10.CK.14 | 02.06    | mapping validate         | product mapped to multiple GL accounts unexpectedly   |
| 10.CK.15 | 03.01    | variance investigation   | duplicate accounting entry                            |
| 10.CK.16 | 03.02    | variance investigation   | transaction posted twice under a different id         |
| 10.CK.17 | 03.03    | variance investigation   | incorrect debit/credit indicator                      |
| 10.CK.18 | 03.04    | variance investigation   | incorrect FX conversion                               |
| 10.CK.19 | 03.05    | variance investigation   | missing accounting mapping's variance contribution    |
| 10.CK.20 | 03.06    | variance investigation   | transaction posted one accounting day late            |
| 10.CK.21 | 03.07    | variance investigation   | incorrect legal-entity allocation                     |
| 10.CK.22 | 03.08    | variance investigation   | incorrect cost-center assignment                      |
| 10.CK.23 | 04.01    | framework metrics        | source/Bronze/GL counts, amounts, variance, status    |

- **task 1 - validate accounting integrity** - confirm `opening_balance + debit_movement - credit_movement = closing_balance` on `finance.gl_balance`, identify violations, then independently recompute expected debit/credit movements from `bronze.finance_transactions` and reconcile against the GL at legal entity, GL account, cost center, currency, and accounting date

**task 1 checks**

| id       | check                                                      |
| -------- | ---------------------------------------------------------- |
| 10.CK.01 | opening + debit - credit = closing arithmetic check        |
| 10.CK.02 | recomputed debit movement vs `gl_balance.debit_movement`   |
| 10.CK.03 | recomputed credit movement vs `gl_balance.credit_movement` |
| 10.CK.04 | reconcile by legal entity                                  |
| 10.CK.05 | reconcile by GL account                                    |
| 10.CK.06 | reconcile by cost center                                   |
| 10.CK.07 | reconcile by currency                                      |
| 10.CK.08 | reconcile by accounting date                               |

- **task 2 - validate accounting mapping** - using `ref.accounting_mapping`, confirm transactions post to their expected GL account, validate mapping effective dates, and produce an exception output (`Transaction, Product, Actual GL, Expected GL, Accounting Date, Exception`)

**task 2 checks**

| id       | check                                                |
| -------- | ---------------------------------------------------- |
| 10.CK.09 | transaction posted to expected GL account            |
| 10.CK.10 | mapping effective-date validity                      |
| 10.CK.11 | transactions with missing accounting mapping         |
| 10.CK.12 | overlapping effective-date mapping ranges            |
| 10.CK.13 | expired mapping still referenced                     |
| 10.CK.14 | product mapped to multiple GL accounts unexpectedly  |

- **task 3 - investigate a finance variance** - explain the SGD-scale closing-balance variance between expected and platform figures, structured rather than transaction-by-transaction, covering:

| id       | issue category                                      |
| -------- | --------------------------------------------------- |
| 10.CK.15 | duplicate accounting entry                          |
| 10.CK.16 | transaction posted twice under a different id       |
| 10.CK.17 | incorrect debit/credit indicator                    |
| 10.CK.18 | incorrect FX conversion                             |
| 10.CK.19 | missing accounting mapping's variance contribution  |
| 10.CK.20 | transaction posted one accounting day late          |
| 10.CK.21 | incorrect legal-entity allocation                   |
| 10.CK.22 | incorrect cost-center assignment                    |

- **task 4 - create a reconciliation framework** - design a reusable, daily-run framework generating the metrics in **10.CK.23**, configurable tolerance rules (absolute, percentage, currency-specific, account-specific), `PASS`/`WARNING`/`FAIL` status assignment, and a persistence design for audit and historical analysis
- **advanced SQL requirement** - demonstrate several of CTEs, window functions, conditional aggregation, `MERGE`, ranking, deduplication, effective-dated joins, hash comparison, incremental processing, exception categorization - see [advanced sql coverage](#advanced-sql-coverage)
- **expected deliverables** - notebook, GL reconciliation output, accounting mapping validation, identified root causes of the variance, exception dataset, reconciliation-framework design, and a business-facing summary
- **assessment context** - the published results must state the assignment scenario, tasks, and scale framing they answer, so a reader is not handed measurements without the question they respond to - see [assessment context documentation](#assessment-context-documentation)

**prerequisite scope**

already-closed infrastructure this assessment consumes, not re-decided here

- **postgres db** ([02](../features/02-dev-env-setup-postgresql-db.md)) running, extended by the seed feature's schema JSON for `finance.gl_balance`, `bronze.finance_transactions`, and `ref.accounting_mapping`
- **spark + jupyter containers** ([03](../features/03-dev-env-setup-spark-container.md)) up, so the notebook can reach both postgres over JDBC and the Spark master
- **seed data** ([04](../features/04-seed-mock-data.md)) loaded through `scripts/03-mock-data-seed.sh`, with `data/mock/issue-log.csv` as the ground-truth catalog of every injected Assessment 2 issue
- **reconciliation control tables** ([05](../features/05-ai-closed-loop-validation.md)) `reconciliation.rc_*` present, the same schema this assessment's task 1/4 results are written into
- **deliverable paths** ([08](../features/08-assessment-deliverables-conventions.md)) scaffolded under `results/assessment-2/`, indexed by [results/assessment-2/README.md](../../results/assessment-2/README.md) - that manifest, not this tracker, is the single list of what must be produced
- **notebook path** ([07](../features/07-jupyter-notebook-workspace-setup.md)) `notebooks/assessment2_gl_reconciliation.ipynb`

**out of scope**

- does not seed, extend, or regenerate mock data - if a check has nothing to find, that is a [04](../features/04-seed-mock-data.md) defect raised there, not a data edit made here
- does not change the `reconciliation.rc_*` schema; task 4's framework design proposes tolerance/status logic expressed against the existing schema, it does not add new columns
- does not attempt the assignment's literal SGD 8.4B-scale GL volumes - measured numbers come from the seeded volume budget, and the assignment's own SGD 3,222,215.72 variance is cited only as the scenario's framing figure, never as a target the seeded data is expected to reproduce exactly (per [04](../features/04-seed-mock-data.md#injected-issue-catalog--assessment-2), the actual seeded variance is whatever that run's RNG produces)
- does not build a dashboard deliverable - the [deliverable-type taxonomy](../features/08-assessment-deliverables-conventions.md#deliverable-type-taxonomy) has no dashboard row for Assessment 2
- does not cover Assessment 1 or Assessment 3 datasets, deliverables, or notebooks

**closure**

Every deliverable listed in [results/assessment-2/README.md](../../results/assessment-2/README.md) carries `status: final`, the assessment context page exists and is referenced from every deliverable, each finding is traceable to a `reconciliation.rc_batch_control.batch_id` or a notebook section, `scripts/07-deliverables-scaffold.sh --check` passes, and the published site shows the Assessment 2 pages.

## References

- **assignment design doc** `docs/design/assignment.md` (Assessment 2 scenario, Tasks 1-4, Advanced SQL Requirement, Expected Deliverables)
- **milestones** `docs/milestones.md` (`assessment 2` scope and closure statement)
- **postgresql db tracker** `docs/features/02-dev-env-setup-postgresql-db.md`
- **spark container tracker** `docs/features/03-dev-env-setup-spark-container.md`
- **seed mock data tracker** `docs/features/04-seed-mock-data.md` (assessment 2 injected issue catalog)
- **ai closed-loop validation tracker** `docs/features/05-ai-closed-loop-validation.md` (`rc_*` schema)
- **jupyter notebook workspace tracker** `docs/features/07-jupyter-notebook-workspace-setup.md`
- **deliverables conventions tracker** `docs/features/08-assessment-deliverables-conventions.md`
- **deliverable manifest** `results/assessment-2/README.md`
- **issue log** `data/mock/issue-log.csv` gitignored, regenerated every seed run
- **schemas** `data/schemas/as02-finance-transactions-schema.json`, `data/schemas/as02-gl-balance-schema.json`, `data/schemas/as02-accounting-mapping-schema.json`

## Design

### prerequisites

Ordered, rerunnable setup steps that must pass before any analysis task starts. Each is an existing script from a closed feature. this tracker only fixes the order and the evidence each step must leave behind.

| id       | step                        | command                                       | evidence         |
| -------- | --------------------------- | --------------------------------------------- | ----------------- |
| 10.PR.01 | host prerequisites          | `scripts/00-prereq-check.sh`                  | `[PASS]` log      |
| 10.PR.02 | postgres + tables           | `scripts/01-dev-env-setup.sh`                 | 9 tables exist    |
| 10.PR.03 | spark + jupyter containers  | `docker compose` full profile                 | `docker ps`       |
| 10.PR.04 | seed mock data              | `scripts/03-mock-data-seed.sh`                | `issue-log.csv`   |
| 10.PR.05 | seed validation             | `scripts/04-mock-data-validate.sh`            | row/issue counts  |
| 10.PR.06 | notebook connectivity       | `scripts/06-notebook-validate.sh`             | template passes   |
| 10.PR.07 | deliverable scaffold check  | `scripts/07-deliverables-scaffold.sh --check` | current           |

01. **10.PR.02** covers only DDL; a fresh clone must still run step 04 before any GL query returns rows.
02. **10.PR.03** uses `docker/docker-compose.full.yml`; the master, both workers, and the Jupyter container must all be `Up` before the notebook is executed.
03. unlike [09](09-as01-data-profiling-reconciliation.md#prerequisites), there is no assessment-2-specific control-table smoke run prerequisite - `reconciliation.rc_*` already exists and is proven end to end by Assessment 1's own closed-loop run; this tracker's task 1/4 steps are the first ones to write an `assessment_id = 'assessment-2'` batch into it.

### assessment task to deliverable map

One row per assignment task, naming the deliverable file it lands in and the executable artifact it is derived from. This is the traceability contract every write-up's **Sources** section must satisfy.

| id       | assignment task                    | deliverable file [01]  | artifact          |
| -------- | ---------------------------------- | ----------------------- | ------------------ |
| 10.DM.01 | task 1 GL arithmetic integrity     | `reconciliation-results` | `rc_*` + notebook  |
| 10.DM.02 | task 1 dimensional reconciliation  | `reconciliation-results` | notebook           |
| 10.DM.03 | task 2 mapping validation          | `mapping-validation`     | notebook           |
| 10.DM.04 | task 2 exception output            | `mapping-validation`     | notebook           |
| 10.DM.05 | task 3 variance investigation      | `root-cause-analysis`    | notebook           |
| 10.DM.06 | task 3 record-level exceptions     | `exception-dataset`      | notebook           |
| 10.DM.07 | task 4 framework design            | `framework-design`       | narrative          |
| 10.DM.08 | task 4 tolerance/status design     | `framework-design`       | narrative          |
| 10.DM.09 | task 4 persistence design          | `framework-design`       | `rc_*` (existing)  |
| 10.DM.10 | business-facing summary            | `business-summary`       | narrative          |
| 10.DM.11 | notebook                           | manifest reference row  | notebook           |
| 10.DM.12 | scenario and task context          | `overview`               | assignment doc     |

01. file names are `results/assessment-2/assessment-2-<slug>.md` per [08](../features/08-assessment-deliverables-conventions.md#directory-and-naming-convention).
02. **10.DM.12** is the authored context page introduced by this tracker, outside feature 08's generated taxonomy - see [assessment context documentation](#assessment-context-documentation).
03. **10.DM.06** and **10.DM.05** are both sourced from the same task 3 investigation - the exception dataset is the row-level detail (one row per flagged transaction/GL entry), the root-cause analysis is the narrative explaining what that detail adds up to; a number is never restated between the two, one links the other.

### workflow cycle

Identical five-stage loop to [09](09-as01-data-profiling-reconciliation.md#workflow-cycle), reused rather than redesigned so every claim in a markdown deliverable stays reproducible from a seeded database.

```
seed db  ->  notebook / spark  ->  rc_* control tables  ->  results markdown  ->  validation run
   ^                                                                                     |
   |_____________________________ rerun on any change ___________________________________|
```

| id       | stage             | action                                                   |
| -------- | ----------------- | ---------------------------------------------------------- |
| 10.WS.01 | seed db           | confirm seeded state, capture the seed run's `issue-log`    |
| 10.WS.02 | notebook / spark  | add or update the task's cells, execute top to bottom       |
| 10.WS.03 | control tables    | write measured results to `reconciliation.rc_*`             |
| 10.WS.04 | results markdown  | update the mapped deliverable and its **Sources** section   |
| 10.WS.05 | validation run    | rerun the scripted checks and record `[PASS]`/`[FAIL]`      |

01. **10.WS.03** applies to task 1 (GL reconciliation) and task 4 (framework metrics) only; task 2 mapping validation and task 3's narrative findings stop at **10.WS.02** and are cited by notebook cell rather than `batch_id`, the same split [09](09-as01-data-profiling-reconciliation.md#workflow-cycle) draws for profiling vs. reconciliation.
02. **10.WS.04** never restates a number the notebook did not produce in the same run - a changed measurement means the deliverable is edited in the same cycle, not the next one.

### assessment context documentation

Same gap and same fix as [09](09-as01-data-profiling-reconciliation.md#assessment-context-documentation): the deliverables scaffolded by [08](../features/08-assessment-deliverables-conventions.md) present measurements without the assignment context that motivated them.

- **overview page** - `results/assessment-2/assessment-2-overview.md` restates the Assessment 2 scenario, the three dataset shapes (`bronze.finance_transactions`, `finance.gl_balance`, `ref.accounting_mapping`), Tasks 1-4, and the expected deliverable list in the assignment's own framing
- **scale statement** - one paragraph naming the assignment's SGD 8.4B-scale closing balances and SGD 3,222,215.72 variance figure alongside this demo's seeded volume budget, so every number published elsewhere is read against the right scale rather than mistaken for a production figure
- **per-deliverable context** - each deliverable opens with a single line, directly under its `status:` marker, naming the assignment task it answers and linking the overview page
- **linkage** - the overview is authored content outside feature 08's generated taxonomy, so it is linked from `results/index.md` and from each deliverable rather than from the generated manifest
- **no restatement of findings** - the overview carries assignment context only; measured results stay in their own deliverables so there is one place a number can change

### GL integrity design - task 1

**business key & date convention** - `finance.gl_balance`'s five-dimension grouping key (`accounting_date, legal_entity, gl_account, cost_center, currency`) is also the grouping key every recomputation below aggregates `bronze.finance_transactions` onto, joining `bronze.finance_transactions.posting_date` to `gl_balance.accounting_date` - the GL is dated by *posting*, not by `transaction_date`. This is load-bearing: **10.CK.20**'s late-posting issue is only detectable because the recomputation buckets by `posting_date`, the same column the injected defect perturbs.

**10.CK.01 - arithmetic integrity**

```sql
SELECT accounting_date, legal_entity, gl_account, cost_center, currency,
       opening_balance, debit_movement, credit_movement, closing_balance,
       (opening_balance + debit_movement - credit_movement) AS computed_closing,
       closing_balance - (opening_balance + debit_movement - credit_movement) AS variance
FROM finance.gl_balance
WHERE closing_balance <> opening_balance + debit_movement - credit_movement
```

Tolerance: exact equality - any nonzero `variance` is a violation. No rounding tolerance applies here: all four columns are `decimal(20,2)` and the expression is pure addition/subtraction, so a nonzero result is a genuine arithmetic break, not a rounding artifact.

**10.CK.02 / 10.CK.03 - independent movement recomputation**

```sql
WITH recomputed AS (
  SELECT
    posting_date AS accounting_date,
    legal_entity, gl_account, cost_center, currency,
    SUM(CASE WHEN debit_credit_indicator = 'DEBIT'  THEN local_amount ELSE 0 END) AS recomputed_debit,
    SUM(CASE WHEN debit_credit_indicator = 'CREDIT' THEN local_amount ELSE 0 END) AS recomputed_credit
  FROM bronze.finance_transactions
  GROUP BY posting_date, legal_entity, gl_account, cost_center, currency
)
SELECT
  g.accounting_date, g.legal_entity, g.gl_account, g.cost_center, g.currency,
  g.debit_movement,  r.recomputed_debit,  g.debit_movement  - r.recomputed_debit  AS debit_variance,
  g.credit_movement, r.recomputed_credit, g.credit_movement - r.recomputed_credit AS credit_variance
FROM finance.gl_balance g
FULL OUTER JOIN recomputed r
  ON  g.accounting_date = r.accounting_date AND g.legal_entity = r.legal_entity
  AND g.gl_account      = r.gl_account      AND g.cost_center  = r.cost_center
  AND g.currency        = r.currency
WHERE ABS(COALESCE(g.debit_movement,0)  - COALESCE(r.recomputed_debit,0))  > 0.01
   OR ABS(COALESCE(g.credit_movement,0) - COALESCE(r.recomputed_credit,0)) > 0.01
```

Tolerance: `MOVEMENT_TOLERANCE_ABS = 0.01` (one minor-currency-unit) applied independently to each side - loose enough to absorb FX-rounding noise already baked into `local_amount`, tight enough that it never masks a genuine one-record miss. `FULL OUTER JOIN` (not `LEFT`/`INNER`) so a GL key with no matching transactions, or a transaction key with no matching GL row, both surface as a variance instead of silently dropping out of the comparison.

**10.CK.04-10.CK.08 - dimensional reconciliation** - the same recomputation, rolled up to one dimension at a time instead of the full five-key grain:

```sql
-- <dimension> is one of: legal_entity, gl_account, cost_center, currency, accounting_date
SELECT <dimension>,
       SUM(g.debit_movement)  AS gl_debit,  SUM(r.recomputed_debit)  AS recomputed_debit,
       SUM(g.credit_movement) AS gl_credit, SUM(r.recomputed_credit) AS recomputed_credit,
       SUM(g.debit_movement)  - SUM(r.recomputed_debit)  AS debit_variance,
       SUM(g.credit_movement) - SUM(r.recomputed_credit) AS credit_variance,
       ABS(SUM(g.debit_movement) - SUM(r.recomputed_debit))
         / NULLIF(ABS(SUM(g.debit_movement)), 0) AS debit_variance_pct
FROM finance.gl_balance g
FULL OUTER JOIN recomputed r ON <same five-column join as 10.CK.02/10.CK.03>
GROUP BY <dimension>
```

`reconciliation_status` per row: `PASS` if `variance_pct < 0.001`, `WARNING` if `< 0.01`, `FAIL` otherwise - the same thresholds `reconciliation.rc_batch_control.status` already fixes ([05](../features/05-ai-closed-loop-validation.md#reconciliation-control-schema)), reused rather than reinvented.

**presentation** - one summary table per dimension (source/GL amount, variance, variance %, status) in the notebook, carried into the reconciliation-results write-up.

**expected findings** - the assessment 2 issue counts from [04](../features/04-seed-mock-data.md#injected-issue-catalog--assessment-2) that each check must reproduce, most directly issue 12 (`opening + debit - credit != closing` violations injected straight into `gl_balance`).

### mapping validation design - task 2

**join key** - `ref.accounting_mapping.transaction_type` and `bronze.finance_transactions.debit_credit_indicator` carry the same domain (`DEBIT`/`CREDIT`) under different column names; every check below effective-dates the join on the transaction's own `transaction_date` (not `posting_date` - the mapping rule governs which policy applied when the transaction occurred, independent of when it was later posted):

```sql
FROM bronze.finance_transactions t
JOIN ref.accounting_mapping m
  ON  t.product_code = m.product_code
  AND t.debit_credit_indicator = m.transaction_type
  AND t.transaction_date >= m.effective_start_date
  AND (t.transaction_date <= m.effective_end_date OR m.effective_end_date IS NULL)
```

**10.CK.09 - expected GL account**

```sql
SELECT t.transaction_id, t.product_code, t.gl_account AS actual_gl,
       m.expected_gl_account, t.posting_date AS accounting_date,
       'GL_MISMATCH' AS exception
FROM bronze.finance_transactions t
JOIN ref.accounting_mapping m
  ON  t.product_code = m.product_code AND t.debit_credit_indicator = m.transaction_type
  AND t.transaction_date >= m.effective_start_date
  AND (t.transaction_date <= m.effective_end_date OR m.effective_end_date IS NULL)
WHERE t.gl_account <> m.expected_gl_account
```

If the join returns more than one mapping row per transaction (an overlapping-range case, **10.CK.12**), every matched row is evaluated independently rather than one being picked arbitrarily - a transaction is `GL_MISMATCH` if it disagrees with *any* matched mapping, so an overlap never hides a genuine misclassification behind whichever row happens to sort first.

**10.CK.10 - effective-date validity** - a transaction whose `(product_code, debit_credit_indicator)` exists in `ref.accounting_mapping` but for which no row's window covers `transaction_date` is `NO_EFFECTIVE_MAPPING`:

```sql
SELECT t.transaction_id, t.product_code, t.debit_credit_indicator
FROM bronze.finance_transactions t
WHERE EXISTS (
  SELECT 1 FROM ref.accounting_mapping m
  WHERE m.product_code = t.product_code AND m.transaction_type = t.debit_credit_indicator
)
AND NOT EXISTS (
  SELECT 1 FROM ref.accounting_mapping m
  WHERE m.product_code = t.product_code AND m.transaction_type = t.debit_credit_indicator
    AND t.transaction_date >= m.effective_start_date
    AND (t.transaction_date <= m.effective_end_date OR m.effective_end_date IS NULL)
)
```

**10.CK.11 - missing mapping** - distinguished from **10.CK.10** by whether *any* row exists for the `(product_code, transaction_type)` pair at all, not just whether one covers the right date:

```sql
SELECT t.transaction_id, t.product_code, t.debit_credit_indicator
FROM bronze.finance_transactions t
WHERE NOT EXISTS (
  SELECT 1 FROM ref.accounting_mapping m
  WHERE m.product_code = t.product_code AND m.transaction_type = t.debit_credit_indicator
)
```

**10.CK.12 - overlapping effective-date ranges** - two mapping rows for the same `(product_code, transaction_type)` whose windows intersect:

```sql
SELECT a.product_code, a.transaction_type, a.effective_start_date, a.effective_end_date,
       b.effective_start_date AS overlap_start, b.effective_end_date AS overlap_end
FROM ref.accounting_mapping a
JOIN ref.accounting_mapping b
  ON  a.product_code = b.product_code AND a.transaction_type = b.transaction_type
  AND a.effective_start_date < b.effective_start_date
  AND a.effective_start_date <= COALESCE(b.effective_end_date, DATE '9999-12-31')
  AND COALESCE(a.effective_end_date, DATE '9999-12-31') >= b.effective_start_date
```

(`a.effective_start_date < b.effective_start_date` breaks the symmetric self-join into one row per overlapping pair rather than two.)

**10.CK.13 - expired mapping still referenced**

```sql
SELECT t.transaction_id, m.product_code, m.effective_end_date, t.transaction_date
FROM bronze.finance_transactions t
JOIN ref.accounting_mapping m
  ON t.product_code = m.product_code AND t.debit_credit_indicator = m.transaction_type
WHERE m.effective_end_date IS NOT NULL
  AND t.transaction_date > m.effective_end_date
  AND NOT EXISTS ( -- no *other*, currently-valid mapping row exists for this transaction
    SELECT 1 FROM ref.accounting_mapping m2
    WHERE m2.product_code = t.product_code AND m2.transaction_type = t.debit_credit_indicator
      AND t.transaction_date >= m2.effective_start_date
      AND (t.transaction_date <= m2.effective_end_date OR m2.effective_end_date IS NULL)
  )
```

The `NOT EXISTS` clause is what separates this from **10.CK.09**: a transaction can reference an expired row while *also* having a currently-valid mapping row it should have used instead - that combination is `GL_MISMATCH` (posted against the wrong, expired GL account), not `EXPIRED_MAPPING`. **10.CK.13** fires only when the expired row is the sole candidate.

**10.CK.14 - product mapped to multiple GL accounts unexpectedly**

```sql
SELECT product_code, transaction_type, COUNT(DISTINCT expected_gl_account) AS gl_account_count
FROM ref.accounting_mapping
WHERE effective_end_date IS NULL OR effective_end_date >= CURRENT_DATE
GROUP BY product_code, transaction_type
HAVING COUNT(DISTINCT expected_gl_account) > 1
```

Distinct from **10.CK.12**: this flags currently-active rows (open-ended or not yet expired) that disagree on `expected_gl_account` - a genuine data conflict rather than a time-ordered supersession. Two active rows can have non-overlapping windows and still trip this check if both windows are current and they disagree.

**exception output** - the assignment's own shape: `Transaction, Product, Actual GL, Expected GL, Accounting Date, Exception`, one row per flagged transaction, `Exception` populated from the closed vocabulary in [exception dataset](#exception-dataset).

### variance investigation design - task 3

**structured investigation, not manual search** - each of the eight categories below is a standalone query tagging its rows with that category's `issue_type` (see [exception dataset](#exception-dataset)); the notebook unions them into one exception set, and the write-up sums each category's `local_amount` contribution to decompose the total variance from [GL integrity design](#gl-integrity-design--task-1), with any unexplained residual called out explicitly rather than silently dropped.

**10.CK.15 - duplicate accounting entry** - hash the business fields (every column except `transaction_id`) and find hash collisions across distinct `transaction_id`s posted on the same `posting_date`:

```sql
SELECT transaction_id, account_id, posting_date, local_amount,
       MD5(CONCAT_WS('|', account_id, posting_date, transaction_amount, currency,
                      debit_credit_indicator, product_code, gl_account, cost_center)) AS entry_hash
FROM bronze.finance_transactions
-- rows sharing entry_hash + posting_date but a different transaction_id are the duplicate group
```

Every row in an `entry_hash` group of size > 1 is flagged except the first (ordered by `transaction_id`); the *extra* rows' `local_amount` is the variance contribution.

**10.CK.16 - transaction posted twice under a different id** - the same hash-collision query as **10.CK.15** (the hash deliberately excludes `transaction_id`, so a same-fields/different-id repost is already caught there); this is a second `issue_type` label applied to the same detected rows, kept separate only because the assignment names the two scenarios independently.

**10.CK.17 - incorrect debit/credit indicator** - without a dedicated GL normal-balance reference table, a flipped indicator is detected indirectly through [GL integrity design](#gl-integrity-design--task-1)'s recomputation: flipping DEBIT/CREDIT sends a transaction's `local_amount` to the wrong side of the SUM, producing an equal-and-opposite debit/credit variance at the same key rather than a one-sided miss:

```sql
SELECT accounting_date, gl_account, cost_center, currency, debit_variance, credit_variance
FROM <10.CK.02 / 10.CK.03 output>
WHERE ABS(debit_variance + credit_variance) < 0.01   -- the two variances cancel
  AND ABS(debit_variance) > 0.01                       -- but neither is individually zero
```

**10.CK.18 - incorrect FX conversion** - the same tolerance check Assessment 1 uses for its own FX field ([09.CK.10](09-as01-data-profiling-reconciliation.md#profiling-design--task-1)):

```sql
SELECT transaction_id, transaction_amount, exchange_rate, local_amount,
       ROUND(transaction_amount * exchange_rate, 2) AS expected_local_amount,
       local_amount - ROUND(transaction_amount * exchange_rate, 2) AS fx_variance
FROM bronze.finance_transactions
WHERE ABS(local_amount - ROUND(transaction_amount * exchange_rate, 2)) > 0.01
```

**10.CK.19 - missing accounting mapping's variance contribution** - the `local_amount` sum of every transaction flagged by **10.CK.10** (no effective mapping) or **10.CK.11** (missing mapping): a transaction with no valid mapping cannot be confirmed against an expected GL account, so it is reported as unexplained/unmapped variance rather than folded into **10.CK.09**'s `GL_MISMATCH` count.

**10.CK.20 - transaction posted one accounting day late** - candidates are transactions whose `posting_date` is exactly one calendar day after `transaction_date`:

```sql
SELECT posting_date, transaction_date, transaction_id, local_amount
FROM bronze.finance_transactions
WHERE posting_date = transaction_date + INTERVAL '1 day'
```

Every candidate is then cross-checked against [GL integrity design](#gl-integrity-design--task-1)'s per-day variance before being counted - flagged only if moving it to `posting_date - 1 day` materially improves that prior day's `debit_variance`/`credit_variance` (i.e. the transaction's own `local_amount` closely matches the prior day's shortfall) - so a transaction the bank's own processing calendar legitimately posts a day later (e.g. a weekend transaction posted next business day) is not over-flagged. The write-up states the exclusion rule applied.

**10.CK.21 - incorrect legal-entity allocation** - `ref.accounting_mapping` carries no `expected_legal_entity` column, so this is instead a majority-vote check per `account_id`: an account's legal entity is expected to be stable, so a transaction whose `legal_entity` disagrees with that account's most-frequent posted value elsewhere in the seeded period is a probable misallocation:

```sql
WITH account_entity_mode AS (
  SELECT account_id, legal_entity, COUNT(*) AS n,
         ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY COUNT(*) DESC) AS rnk
  FROM bronze.finance_transactions
  GROUP BY account_id, legal_entity
)
SELECT t.transaction_id, t.legal_entity AS actual_entity, e.legal_entity AS expected_entity
FROM bronze.finance_transactions t
JOIN account_entity_mode e ON t.account_id = e.account_id AND e.rnk = 1
WHERE t.legal_entity <> e.legal_entity
```

**10.CK.22 - incorrect cost-center assignment** - unlike legal entity, `ref.accounting_mapping.expected_cost_center` exists, so this reuses **10.CK.09**'s effective-dated join directly:

```sql
SELECT t.transaction_id, t.cost_center AS actual_cost_center, m.expected_cost_center
FROM bronze.finance_transactions t
JOIN ref.accounting_mapping m
  ON t.product_code = m.product_code AND t.debit_credit_indicator = m.transaction_type
  AND t.transaction_date >= m.effective_start_date
  AND (t.transaction_date <= m.effective_end_date OR m.effective_end_date IS NULL)
WHERE t.cost_center <> m.expected_cost_center
```

**scale note** - the standard wording stating measured values come from the seeded volume budget, with the assignment's SGD 3,222,215.72 figure cited as the scenario framing, not the seeded target.

**affected dimensions** - the legal entities, GL accounts, cost centers, and accounting dates carrying the largest share of the decomposed variance.

### reconciliation framework design - task 4

This is a design deliverable, not new code - the framework it specifies already exists as `reconciliation.rc_*` ([05](../features/05-ai-closed-loop-validation.md#reconciliation-control-schema)); task 4 documents how that existing schema satisfies the assignment's ask, and where it would need to extend.

**10.CK.23 - metrics** - this dataset has no separate raw-source ingestion tier the way Assessment 1's `src_transaction_daily` does (no `source.*` schema for finance) - `bronze.finance_transactions` is the earliest tier available, so `source_count`/`source_amount` and `bronze_count`/`bronze_amount` are measured as the same value for this assessment; the split is kept in the vocabulary only so the metric names stay uniform with Assessment 1/3's frameworks, and the design states this explicitly rather than leaving two identical numbers unexplained.

| metric              | expression                                                          |
| -------------------- | -------------------------------------------------------------------- |
| `source_count`        | `SELECT COUNT(*) FROM bronze.finance_transactions`                    |
| `bronze_count`        | same query as `source_count` (see note above)                         |
| `gl_transaction_count`| `SELECT COUNT(*) FROM finance.gl_balance`                             |
| `source_amount`       | `SELECT SUM(local_amount) FROM bronze.finance_transactions`           |
| `bronze_amount`       | same query as `source_amount`                                         |
| `gl_amount`           | `SELECT SUM(closing_balance) FROM finance.gl_balance`                 |
| `absolute_variance`   | `gl_amount - source_amount`                                           |
| `percentage_variance` | `ABS(gl_amount - source_amount) / NULLIF(ABS(source_amount), 0)`      |
| `exception_count`     | `COUNT(*)` across the unioned [exception dataset](#exception-dataset) |
| `reconciliation_status` | `PASS`/`WARNING`/`FAIL` per the thresholds below                    |

Each row lands in `reconciliation.rc_reconciliation_results` with `dimension` carrying the metric name and `source_value`/`target_value`/`variance`/`variance_pct`/`reconciliation_status` populated from the table above:

```sql
INSERT INTO reconciliation.rc_reconciliation_results
  (batch_id, dimension, source_value, target_value, variance, variance_pct, reconciliation_status)
SELECT :batch_id, 'gl_amount', s.source_amount, g.gl_amount,
       g.gl_amount - s.source_amount AS variance,
       ABS(g.gl_amount - s.source_amount) / NULLIF(ABS(s.source_amount), 0) AS variance_pct,
       CASE
         WHEN ABS(g.gl_amount - s.source_amount) / NULLIF(ABS(s.source_amount), 0) < :pct_warning THEN 'PASS'
         WHEN ABS(g.gl_amount - s.source_amount) / NULLIF(ABS(s.source_amount), 0) < :pct_fail    THEN 'WARNING'
         ELSE 'FAIL'
       END
FROM (SELECT SUM(local_amount) AS source_amount FROM bronze.finance_transactions) s
CROSS JOIN (SELECT SUM(closing_balance) AS gl_amount FROM finance.gl_balance) g
```

**tolerance rules** - absolute, percentage, currency-specific, and account-specific tolerance, expressed as a design proposal for a `rc_tolerance_rules`-shaped lookup, not a table this tracker adds (doing so is a [05](../features/05-ai-closed-loop-validation.md) change if adopted):

```
rc_tolerance_rules(assessment_id, dimension, currency NULL=all, gl_account NULL=all,
                    abs_tolerance, pct_warning, pct_fail)
```

`currency`/`gl_account` are nullable wildcard columns; the most specific non-null match wins in the order `(currency, gl_account)` > `currency only` > `(NULL, NULL)` default row, so `:pct_warning`/`:pct_fail` above are resolved by that lookup rather than hardcoded per call site.

**status assignment** - `PASS`/`WARNING`/`FAIL` default to the thresholds `reconciliation.rc_batch_control.status` already establishes (per [05](../features/05-ai-closed-loop-validation.md#reconciliation-control-schema): `PASS` under 0.1%, `WARNING` under 1%, `FAIL` at or above 1%), overridable per currency/GL account by the tolerance-rule lookup above.

**persistence for audit/historical analysis** - answered by `rc_batch_control`'s existing append-only design ([05](../features/05-ai-closed-loop-validation.md#idempotency--rerun-safety)): every daily run inserts a new batch rather than overwriting, so history is a `SELECT ... WHERE assessment_id = 'assessment-2' ORDER BY batch_date` away.

### exception dataset

- **schema** - at minimum `transaction_id`, `issue_type`, `source_value`, `bronze_value`/`gl_value`, `variance`, `batch_id`, mirroring [09](09-as01-data-profiling-reconciliation.md#exception-dataset)'s minimum columns adapted to this assessment's GL-vs-transaction comparison
- **materialisation** - table, notebook output, or embedded markdown extract, with the full row set's location stated where the write-up shows only a sample
- **ground-truth check** - the comparison against `issue-log.csv` proving detected issues match injected ones

**issue_type vocabulary** - the closed set of string values every check writes, one per check id, matched against `issue-log.csv`'s own `issue_type` spelling so ground-truth comparison is a direct join:

| check id | `issue_type`             |
| -------- | -------------------------- |
| 10.CK.09 | `GL_MISMATCH`                |
| 10.CK.10 | `NO_EFFECTIVE_MAPPING`       |
| 10.CK.11 | `MAPPING_NOT_FOUND`          |
| 10.CK.12 | `OVERLAPPING_MAPPING`        |
| 10.CK.13 | `EXPIRED_MAPPING`            |
| 10.CK.14 | `MULTI_GL_MAPPING`           |
| 10.CK.15 | `DUPLICATE_ENTRY`            |
| 10.CK.16 | `DUPLICATE_REPOST`           |
| 10.CK.17 | `WRONG_DR_CR_INDICATOR`      |
| 10.CK.18 | `FX_CONVERSION_ERROR`        |
| 10.CK.19 | `UNMAPPED_VARIANCE`          |
| 10.CK.20 | `LATE_POSTING`               |
| 10.CK.21 | `WRONG_LEGAL_ENTITY`         |
| 10.CK.22 | `WRONG_COST_CENTER`          |

01. a row may legitimately carry more than one `issue_type` for the same `transaction_id` (e.g. `WRONG_DR_CR_INDICATOR` and `FX_CONVERSION_ERROR` both true) - the exception dataset is one row per `(transaction_id, issue_type)` pair, not one row per transaction, so `exception_count` in [reconciliation framework design](#reconciliation-framework-design--task-4) counts flagged pairs.

### advanced sql coverage

The assignment asks for "several" of ten named techniques, not all ten; this tracker commits to a specific subset so 10.10's notebook consolidation has a concrete checklist rather than a vague aspiration.

| id       | technique                | where it is used                                              |
| -------- | --------------------------- | ------------------------------------------------------------------ |
| 10.SQ.01 | CTEs                        | staged recomputation (transactions -> movements -> variance)        |
| 10.SQ.02 | window functions            | ranking largest-variance dimension combinations (task 1/3)          |
| 10.SQ.03 | conditional aggregation     | debit/credit split from `debit_credit_indicator` in one pass        |
| 10.SQ.04 | effective-dated joins       | `ref.accounting_mapping` join, task 2                                |
| 10.SQ.05 | deduplication                | duplicate/re-posted accounting entry detection, task 3               |
| 10.SQ.06 | exception categorization    | the closed `issue_type` vocabulary applied across tasks 2-3           |

01. `MERGE`, hash comparison, ranking (beyond window-function ranking already covered), and incremental processing are not committed to a specific cell - if a natural fit appears during 10.04-10.07 it is added and this table updated, but they are not required to close this tracker.

### notebook organisation

`notebooks/assessment2_gl_reconciliation.ipynb` is the single executable artifact for this assessment, sectioned in assignment order - connectivity, task 1 GL integrity, task 2 mapping validation, task 3 variance investigation, task 4 framework demonstration - so a deliverable's **Sources** reference can name a section rather than a cell index that shifts on edit. Output commit policy follows [07](../features/07-jupyter-notebook-workspace-setup.md); the notebook must execute cleanly top to bottom against a freshly seeded database before 10.10 closes.

### idempotency / rerun-safety

- **notebook** - re-executable end to end against a freshly seeded database with no manual cell ordering; any writes it makes are keyed by `batch_id` so a rerun appends a new batch rather than mutating a prior one.
- **control tables** - reruns insert a new `rc_batch_control` row (`assessment_id = 'assessment-2'`); existing batches are never updated in place, preserving the evidence a published deliverable already cites.
- **deliverable markdown** - authored content, never regenerated by a script; `07-deliverables-scaffold.sh` remains verify-or-create and only the derived `README.md` manifest is rewritten.
- **seed data** - regenerated only by `scripts/03-mock-data-seed.sh`, which is deterministic under the fixed `MOCK_DATA_SEED`; this tracker never edits seeded rows directly.

### environment & secrets

No new variables and no new secrets. The work reuses the existing postgres connection settings, `LOGS_DIR`, `TIMEZONE`, and `TIMESTAMP_FORMAT` from `.env`. Credentials are never written into a notebook cell, a deliverable markdown file, or the published site.

### workflow validation runner

Assessment 2 introduces no new runner by default; validation composes the existing scripts in [prerequisites](#prerequisites) plus `scripts/06-notebook-validate.sh` for headless notebook execution and `scripts/07-deliverables-scaffold.sh --check` for deliverable completeness. If a per-assessment orchestration step proves necessary, it is added as the next free script number and logged under `.dev/logs/` with `<ts>-10.<nn>-<name>.log` naming, printing one `[PASS]`/`[FAIL]` line per stage of the [workflow cycle](#workflow-cycle).

### publishing

Once every deliverable is promoted to `status: final`, `scripts/07-deliverables-scaffold.sh` regenerates the Assessment 2 manifest with the updated statuses, `scripts/08-assessment-site.sh build` validates the strict MkDocs build, and `scripts/08-assessment-site.sh deploy` publishes to `gh-pages` from a clean, reviewed worktree. The overview page must be reachable from the published navigation before deploy. Deployment is never run with uncommitted assessment evidence in the tree.

## Test cases

_test strategy_

Findings are validated at three layers so a measurement is never trusted on the strength of the write-up alone:

1. **script self-report** - `[PASS]`/`[FAIL]` lines and timestamped logs from the prerequisite and validation scripts show each stage ran.
2. **ground-truth comparison** - detected issues are joined against `data/mock/issue-log.csv`, the injected catalog from [04](../features/04-seed-mock-data.md), rather than eyeballed.
3. **content inspection** - deliverable markdown is checked for required headings, `status:` markers, context and source references, and table shape independently of the notebook that produced the numbers.

_test cases_

| id       | task  | layer        | check                                        |
| -------- | ----- | ------------ | -------------------------------------------- |
| 10.TC.01 | 10.02 | script       | all prerequisite steps report `[PASS]`        |
| 10.TC.02 | 10.02 | ground-truth | seeded issue counts match the issue log       |
| 10.TC.03 | 10.03 | content      | overview states scenario, tasks, and scale    |
| 10.TC.04 | 10.03 | content      | every deliverable links the overview page     |
| 10.TC.05 | 10.04 | content      | GL arithmetic violations reported with counts |
| 10.TC.06 | 10.04 | ground-truth | violation counts match injected issue rows    |
| 10.TC.07 | 10.04 | script       | task 1 results land in `rc_*` for one batch   |
| 10.TC.08 | 10.05 | content      | mapping exception table carries six columns   |
| 10.TC.09 | 10.05 | ground-truth | mapping exceptions reconcile to the issue log |
| 10.TC.10 | 10.06 | content      | exception dataset carries the minimum columns |
| 10.TC.11 | 10.07 | content      | variance decomposition sums to stated total   |
| 10.TC.12 | 10.08 | content      | framework maps each metric onto `rc_*`        |
| 10.TC.13 | 10.09 | content      | business summary states findings in plain terms |
| 10.TC.14 | 10.10 | script       | notebook executes clean top to bottom         |
| 10.TC.15 | 10.11 | content      | every deliverable reads `status: final`       |
| 10.TC.16 | 10.12 | build        | strict MkDocs build succeeds                  |
| 10.TC.17 | 10.12 | deployment   | published site shows assessment 2 pages       |

**tools**

```bash
cd /home/taylor-hickem/repos/de-financial-accounting-demo
./scripts/00-prereq-check.sh
./scripts/03-mock-data-seed.sh
./scripts/04-mock-data-validate.sh
./scripts/06-notebook-validate.sh
./scripts/07-deliverables-scaffold.sh --check
./scripts/08-assessment-site.sh build
grep -R --line-number '^status: \(draft\|final\)$' results/assessment-2
grep -RL 'assessment-2-overview.md' results/assessment-2/assessment-2-*.md
awk '/^\|/ && length($0) >= 115 { print FILENAME ":" FNR ": row too long"; bad = 1 } END { exit bad }' results/assessment-2/*.md
```

## Edit locations

| id       | path                                                           | change                        |
| -------- | ---------------------------------------------------------------- | ------------------------------ |
| 10.EL.01 | `notebooks/assessment2_gl_reconciliation.ipynb`                  | full analysis notebook         |
| 10.EL.02 | `results/assessment-2/assessment-2-reconciliation-results.md`    | task 1 write-up                |
| 10.EL.03 | `results/assessment-2/assessment-2-mapping-validation.md`        | task 2 write-up                |
| 10.EL.04 | `results/assessment-2/assessment-2-exception-dataset.md`         | task 3 exception write-up      |
| 10.EL.05 | `results/assessment-2/assessment-2-root-cause-analysis.md`       | task 3 variance write-up       |
| 10.EL.06 | `results/assessment-2/assessment-2-framework-design.md`          | task 4 write-up                |
| 10.EL.07 | `results/assessment-2/assessment-2-business-summary.md`          | business-facing summary        |
| 10.EL.08 | `results/assessment-2/README.md`                                 | regenerated manifest           |
| 10.EL.09 | `src/sparksql/`                                                   | reusable query files           |
| 10.EL.10 | `docs/milestones.md`                                              | milestone 10 status/closure    |
| 10.EL.11 | `results/assessment-2/assessment-2-overview.md`                  | assessment scope context       |
| 10.EL.12 | `results/index.md`                                                | link to the overview page      |
| 10.EL.13 | `mkdocs.yml`                                                      | overview in site nav           |

01. **10.EL.08** is generated by `scripts/07-deliverables-scaffold.sh`; never hand-edited.
02. **10.EL.09** is optional - used only where a query is worth extracting from the notebook for reuse, following the existing `src/pyspark/` naming pattern.
03. **10.EL.11** is authored content outside feature 08's generated taxonomy, so the scaffold neither creates nor validates it; it is created by hand in 10.03.
04. **10.EL.13** is only required if the strict build cannot reach the overview through `10.EL.12`'s link alone.

No `.env`, `.env.sample`, schema JSON, DDL, or seed-script change is expected. A required change to any of those is a defect in the owning feature and is raised there rather than patched from this tracker.

## Implement

Implementation order is prerequisites -> assessment context -> GL integrity -> mapping validation -> exceptions -> variance investigation -> framework design -> business summary -> notebook rerun -> review -> publish. Each step runs the full [workflow cycle](#workflow-cycle) before the next begins.

### 1. Prerequisites and seed data readiness

edit locations: none

Run the [prerequisites](#prerequisites) steps in order, confirming the evidence column for each. Record the seed run's issue counts as the baseline every later ground-truth comparison is made against. Do not start task 1 until every prerequisite reports `[PASS]`.

### 2. Assessment scope and context write-up

edit locations: `10.EL.11, 10.EL.12, 10.EL.13`

Author `results/assessment-2/assessment-2-overview.md` per [assessment context documentation](#assessment-context-documentation): the Assessment 2 scenario, the three dataset shapes, Tasks 1-4, the expected deliverable list, and the scale statement contrasting the assignment's SGD 8.4B-scale figures with this demo's seeded volume budget. Link it from `results/index.md`, and add it to `mkdocs.yml`'s navigation only if the strict build cannot reach it through that link.

This step is done before any analysis write-up so each later deliverable can be authored with its context line already pointing at an existing page.

### 3. Task 1 - GL integrity and reconciliation

edit locations: `10.EL.01, 10.EL.02`

Implement **10.CK.01**-**10.CK.08** exactly as specified in [GL integrity design](#gl-integrity-design--task-1) - the arithmetic check, the `recomputed` CTE, and the per-dimension roll-up are not re-derived here, only translated into notebook cells against the seeded tables. Write results into `reconciliation.rc_*` under one `batch_id` (`assessment_id = 'assessment-2'`, `dimension` per row per the [reconciliation framework design](#reconciliation-framework-design--task-4) metrics table). Write the reconciliation results deliverable citing that `batch_id` and the overview page.

### 4. Task 2 - accounting mapping validation

edit locations: `10.EL.01, 10.EL.03`

Implement **10.CK.09**-**10.CK.14** exactly as specified in [mapping validation design](#mapping-validation-design--task-2), tagging each flagged row with its `issue_type` from [exception dataset](#exception-dataset)'s vocabulary table. Produce the exception output in the assignment's stated shape (`Transaction, Product, Actual GL, Expected GL, Accounting Date, Exception`). Write the mapping validation deliverable.

### 5. Exception dataset

edit locations: `10.EL.01, 10.EL.04`

Union the row sets from **10.CK.09**-**10.CK.22** into the exception dataset's minimum columns per [exception dataset](#exception-dataset), one row per `(transaction_id, issue_type)` pair, and reconcile detected rows against `issue-log.csv`. Write the exception dataset deliverable, sampling in the markdown and pointing at the full output.

### 6. Task 3 - finance variance investigation

edit locations: `10.EL.01, 10.EL.05`

Implement **10.CK.15**-**10.CK.22** exactly as specified in [variance investigation design](#variance-investigation-design--task-3), including **10.CK.20**'s cross-check against task 1's per-day variance before counting a late-posting candidate. Decompose the total variance across the eight categories, identify affected dimensions, and state remediation. Write the root-cause analysis deliverable.

### 7. Task 4 - reconciliation framework design

edit locations: `10.EL.06`

Write the framework design deliverable from [reconciliation framework design](#reconciliation-framework-design--task-4) directly: the metrics table (**10.CK.23**), the `rc_tolerance_rules` proposal, the status-assignment thresholds, and the persistence design - this step is a narrative write-up of an already-fully-specified design, not new query development.

### 8. Business-facing summary

edit locations: `10.EL.07`

Write a short, non-technical summary of the variance findings and recommended controls aimed at a Finance stakeholder, distinct from the technical root-cause write-up.

### 9. Notebook consolidation and clean rerun

edit locations: `10.EL.01`

Reorder the notebook into assignment task order, remove scratch cells, reseed the database, and execute the notebook headless with `scripts/06-notebook-validate.sh`. Confirm every number cited in a deliverable still matches the rerun output; where it does not, correct the deliverable in the same cycle. Confirm the [advanced sql coverage](#advanced-sql-coverage) checklist is satisfied.

### 10. Deliverable review and status promotion

edit locations: `10.EL.02-10.EL.08, 10.EL.11`

Review each deliverable against the [task to deliverable map](#assessment-task-to-deliverable-map) for coverage, a populated **Sources** section, a context line linking the overview, and consistent numbers. Promote each `status: draft` to `status: final`, then run `scripts/07-deliverables-scaffold.sh` to regenerate the manifest with the new statuses and `--check` to confirm the result is current.

### 11. Publish

edit locations: `10.EL.10`

Commit the reviewed work, run `scripts/08-assessment-site.sh build` for the strict build, then `scripts/08-assessment-site.sh deploy` from the clean worktree. Confirm the published Assessment 2 pages, then update `docs/milestones.md` to mark milestone 10 closed with its closure evidence.

## Validate

**Issues**

- inventory all first out exceptions and issues encountered in this table
- for each issue, create an issue section and use this section to document diagnostics and resolution steps

| id       | seq | status  | issue                                    |
| -------- | --- | ------- | ----------------------------------------- |
| 10.IS.01 | 01  | pending | \<first out exception\>                  |

_10.IS.01 (pending) \<first out exception\>_

**problem description**

**exception**

```log
```

**triggering actions**

**hypothesis**

- use hypothesis framing until a validated fix is applied

**diagnostic steps**

- first out exception is NOT a diagnostic step
- diagnostic steps reveal information or apply a fix
- assume re-run and validation, these are not diagnostic steps
- keep the step description brief, use the diagnostics details section to elaborate actions and learnings for each step

| id          | seq | status  | step                                 |
| ----------- | --- | ------- | ------------------------------------- |
| 10.IS.01.01 | 01  | pending | \<diagnostic step 01\>               |

**diagnostic details**

**validation evidence**

**user actions**

- GitHub authentication and the deploy confirmation for the published site (10.12)

## Guideline

## instructions

review and strictly follow these relevant skills when performing tasks for this
feature implementation and working with this document

## relevant skills

- markdown-tables
- feature-implementation-guide
- jupyter-notebook-workspace
