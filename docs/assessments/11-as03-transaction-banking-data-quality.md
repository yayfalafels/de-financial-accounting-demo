# Assessment 3 - Regulatory / Transaction Banking Data Quality, Lineage and Executive Dashboard - Feature tracker
>Review the guidelines before performing any actions including edits on the document

## 11 (pending) assessment 3 - regulatory dq, lineage and executive dashboard

## Contents

- [Tasks](#tasks)
- [Scope](#scope)
- [References](#references)
- [Design](#design)
  - [prerequisites](#prerequisites)
  - [assessment task to deliverable map](#assessment-task-to-deliverable-map)
  - [workflow cycle](#workflow-cycle)
  - [assessment context documentation](#assessment-context-documentation)
  - [profiling design - task 1](#profiling-design--task-1)
  - [end-to-end reconciliation design - task 2](#end-to-end-reconciliation-design--task-2)
  - [complex issue detection - task 3](#complex-issue-detection--task-3)
  - [exception dataset](#exception-dataset)
  - [lineage documentation - task 4](#lineage-documentation--task-4)
  - [dashboard design - task 5](#dashboard-design--task-5)
  - [performance-optimization design](#performance-optimization-design)
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

| id    | seq | status  | milestone                                     |
| ----- | --- | ------- | ----------------------------------------------- |
| 11.01 | 01  | closed  | design                                          |
| 11.02 | 02  | pending | prerequisites and seed data readiness           |
| 11.03 | 03  | pending | assessment scope and context write-up           |
| 11.04 | 04  | pending | task 1 - transaction banking profiling          |
| 11.05 | 05  | pending | task 2 - end-to-end reconciliation              |
| 11.06 | 06  | pending | exception dataset                               |
| 11.07 | 07  | pending | task 3 - complex issue detection                |
| 11.08 | 08  | pending | task 4 - data lineage documentation             |
| 11.09 | 09  | pending | task 5 - Power BI executive dashboard           |
| 11.10 | 10  | pending | performance-optimization notes                  |
| 11.11 | 11  | pending | five-minute presentation summary                |
| 11.12 | 12  | pending | notebook consolidation and clean rerun          |
| 11.13 | 13  | pending | deliverable review and status promotion         |
| 11.14 | 14  | pending | publish assessment site                         |
| 11.IS | 15  | pending | validate                                        |

## Scope

answer Assessment 3 of the **assignment design doc** end to end - profile `source.payment_transactions` / `bronze.payment_transactions`, reconcile Source -> Bronze -> `regulatory.payment_reporting`, detect the duplicate-processing / effective-dated-join / cross-border / late-arrival defects, document lineage for five critical regulatory attributes, extend the Power BI template with an executive dashboard, answer the 5B-row performance question by design, and publish the resulting deliverable set together with the assignment context that motivated it - see [milestones.md](../milestones.md)'s `assessment 3` entry for the milestone-level statement this tracker executes.

**assessment scope**

condensed from the **assignment design doc**'s Assessment 3 section

- **scenario** transaction volumes shown in the regulatory reporting mart do not match Transaction Banking records. management requires a Source -> Bronze -> Reporting lineage and reconciliation investigation.
- **the problem** `regulatory.payment_reporting` disagrees with `bronze.payment_transactions`, driven by more than one concurrent defect
- **checks to perform**

| id       | task ref | scope          | check                                             |
| -------- | -------- | -------------- | -------------------------------------------------- |
| 11.CK.01 | 01.01    | profile        | duplicate `payment_id`                              |
| 11.CK.02 | 01.02    | profile        | missing `customer_id`                                |
| 11.CK.03 | 01.03    | profile        | invalid payment status                               |
| 11.CK.04 | 01.04    | profile        | missing currency                                     |
| 11.CK.05 | 01.05    | profile        | invalid beneficiary country                          |
| 11.CK.06 | 01.06    | profile        | negative or zero payment amount                      |
| 11.CK.07 | 01.07    | profile        | missing customer reference record                    |
| 11.CK.08 | 01.08    | profile        | payment linked to inactive customer                  |
| 11.CK.09 | 01.09    | profile        | multiple active customer records [01]                |
| 11.CK.10 | 01.10    | profile        | unusual transaction-volume spikes                    |
| 11.CK.11 | 01.11    | profile        | unexpected payment-channel distribution              |
| 11.CK.12 | 01.12    | profile        | cross-border classification anomalies                |
| 11.CK.13 | 02.01    | e2e reconcile  | transaction count                                    |
| 11.CK.14 | 02.02    | e2e reconcile  | payment amount                                       |
| 11.CK.15 | 02.03    | e2e reconcile  | customer count                                       |
| 11.CK.16 | 02.04    | e2e reconcile  | currency                                             |
| 11.CK.17 | 02.05    | e2e reconcile  | legal entity                                         |
| 11.CK.18 | 02.06    | e2e reconcile  | payment type                                         |
| 11.CK.19 | 02.07    | e2e reconcile  | domestic vs. cross-border classification             |
| 11.CK.20 | 02.08    | e2e reconcile  | reporting date                                       |
| 11.CK.21 | 03.01    | complex issues | duplicate processing under 2nd `batch_id`            |
| 11.CK.22 | 03.02    | complex issues | effective-dated customer join fan-out                |
| 11.CK.23 | 03.03    | complex issues | cross-border misclassification sufficiency           |
| 11.CK.24 | 03.04    | complex issues | late-arriving transaction cutoff misassignment       |

01. "multiple active customer records" means multiple overlapping effective-dated `customer_master` rows for the same `customer_id`, the direct cause of **11.CK.22**'s fan-out.

- **task 1 - profile transaction banking data** - profile `source.payment_transactions` and `bronze.payment_transactions`, demonstrate how the checks would be handled efficiently in Spark/Databricks at scale

**task 1 checks**

| id       | check                                                 |
| -------- | ---------------------------------------------------------- |
| 11.CK.01 | duplicate `payment_id`                                      |
| 11.CK.02 | missing `customer_id`                                        |
| 11.CK.03 | invalid payment status                                        |
| 11.CK.04 | missing currency                                              |
| 11.CK.05 | invalid beneficiary country                                    |
| 11.CK.06 | negative or zero payment amount                                |
| 11.CK.07 | missing customer reference record                              |
| 11.CK.08 | payment linked to inactive customer record                     |
| 11.CK.09 | multiple active (effective-dated) customer records              |
| 11.CK.10 | unusual transaction-volume spikes                               |
| 11.CK.11 | unexpected payment-channel distribution                          |
| 11.CK.12 | cross-border classification anomalies                            |

- **task 2 - build end-to-end reconciliation** - reconcile Source -> Bronze -> Regulatory Reporting across the eight dimensions below, producing a reconciliation matrix (`Dimension | Source | Bronze | Regulatory | Variance | Status`)

**task 2 checks**

| id       | dimension                                |
| -------- | -------------------------------------------- |
| 11.CK.13 | transaction count                              |
| 11.CK.14 | payment amount                                 |
| 11.CK.15 | customer count                                 |
| 11.CK.16 | currency                                       |
| 11.CK.17 | legal entity                                   |
| 11.CK.18 | payment type                                   |
| 11.CK.19 | domestic vs. cross-border classification        |
| 11.CK.20 | reporting date                                 |

- **task 3 - detect complex data issues** - four named defects, each requiring detection logic beyond a simple count comparison

| id       | defect                                                                   |
| -------- | --------------------------------------------------------------------------- |
| 11.CK.21 | duplicate processing - a payment file loaded twice under different batch IDs |
| 11.CK.22 | effective-dated customer join issue - naive `customer_id`-only join fans out |
| 11.CK.23 | cross-border misclassification - `residence_country != beneficiary_country` sufficiency |
| 11.CK.24 | late-arriving transactions assigned to the next reporting date               |

- **task 4 - document data lineage** - lineage documentation for at least five critical regulatory attributes, each row naming source, source column, Bronze location, transformation, and the data-quality control that guards it
- **task 5 - Power BI dashboard** - executive KPIs, recommended visuals, and filter set - see [dashboard design](#dashboard-design--task-5)
- **technical optimization question** - explain (and where possible demonstrate at seeded scale) the techniques that would keep a reconciliation query against a 5B-row Bronze table under the assignment's 40-minute baseline - see [performance-optimization design](#performance-optimization-design)
- **expected deliverables** - notebook, profiling results, end-to-end reconciliation, exception tables, root-cause analysis, data-lineage document, Power BI dashboard or dashboard design, performance-optimization recommendations, and a five-minute presentation summary
- **assessment context** - the published results must state the assignment scenario, tasks, and scale framing they answer, so a reader is not handed measurements without the question they respond to - see [assessment context documentation](#assessment-context-documentation)

**prerequisite scope**

already-closed infrastructure this assessment consumes, not re-decided here

- **postgres db** ([02](../features/02-dev-env-setup-postgresql-db.md)) running, extended by the seed feature's schema JSON for `source.payment_transactions`, `bronze.payment_transactions`, `bronze.customer_master`, and `regulatory.payment_reporting`
- **spark + jupyter containers** ([03](../features/03-dev-env-setup-spark-container.md)) up - the master + 2 worker topology this assessment's technical-optimization narrative explicitly builds its argument on
- **seed data** ([04](../features/04-seed-mock-data.md)) loaded through `scripts/03-mock-data-seed.sh`, with `data/mock/issue-log.csv` as the ground-truth catalog of every injected Assessment 3 issue
- **reconciliation control tables** ([05](../features/05-ai-closed-loop-validation.md)) `reconciliation.rc_*` present, the schema this assessment's task 2 results are written into
- **deliverable paths** ([08](../features/08-assessment-deliverables-conventions.md)) scaffolded under `results/assessment-3/`, indexed by [results/assessment-3/README.md](../../results/assessment-3/README.md) - that manifest, not this tracker, is the single list of what must be produced
- **notebook path** ([07](../features/07-jupyter-notebook-workspace-setup.md)) `notebooks/assessment3_regulatory_dashboard.ipynb`
- **dashboard template** ([06](../features/06-powerbi-dashboard-setup.md)) `powerbi/reconciliation-dashboard-template/`, synced with `scripts/05-powerbi-sync.sh`

**out of scope**

- does not seed, extend, or regenerate mock data - if a check has nothing to find, that is a [04](../features/04-seed-mock-data.md) defect raised there, not a data edit made here
- does not change the `reconciliation.rc_*` schema; new checks are new rows, not new columns
- does not attempt the assignment's literal 5-billion-row Bronze table or its 40-minute baseline query - per [milestones.md](../milestones.md)'s `assessment 3` closure statement, the performance question is answered by technique explanation plus a small-scale demonstration, not literal 5B-row execution; no billion-row dataset is generated
- does not cover Assessment 1 or Assessment 2 datasets, deliverables, or notebooks

**closure**

Every deliverable listed in [results/assessment-3/README.md](../../results/assessment-3/README.md) carries `status: final`, the assessment context page exists and is referenced from every deliverable, each finding is traceable to a `reconciliation.rc_batch_control.batch_id` or a notebook section, `scripts/07-deliverables-scaffold.sh --check` passes, and the published site shows the Assessment 3 pages.

## References

- **assignment design doc** `docs/design/assignment.md` (Assessment 3 scenario, Tasks 1-5, Technical Optimization Question, Expected Deliverables)
- **milestones** `docs/milestones.md` (`assessment 3` scope and closure statement, incl. the performance-question closure note)
- **postgresql db tracker** `docs/features/02-dev-env-setup-postgresql-db.md`
- **spark container tracker** `docs/features/03-dev-env-setup-spark-container.md`
- **seed mock data tracker** `docs/features/04-seed-mock-data.md` (assessment 3 injected issue catalog)
- **ai closed-loop validation tracker** `docs/features/05-ai-closed-loop-validation.md` (`rc_*` schema)
- **powerbi dashboard setup tracker** `docs/features/06-powerbi-dashboard-setup.md`
- **jupyter notebook workspace tracker** `docs/features/07-jupyter-notebook-workspace-setup.md`
- **deliverables conventions tracker** `docs/features/08-assessment-deliverables-conventions.md`
- **deliverable manifest** `results/assessment-3/README.md`
- **issue log** `data/mock/issue-log.csv` gitignored, regenerated every seed run
- **schemas** `data/schemas/as03-payment-transactions-schema.json`, `data/schemas/as03-bronze-payment-schema.json`, `data/schemas/as03-customer-master-schema.json`, `data/schemas/as03-payment-reporting-schema.json`

## Design

### prerequisites

Ordered, rerunnable setup steps that must pass before any analysis task starts. Each is an existing script from a closed feature; this tracker only fixes the order and the evidence each step must leave behind.

| id       | step                        | command                                       | evidence         |
| -------- | --------------------------- | --------------------------------------------- | ----------------- |
| 11.PR.01 | host prerequisites          | `scripts/00-prereq-check.sh`                  | `[PASS]` log      |
| 11.PR.02 | postgres + tables           | `scripts/01-dev-env-setup.sh`                 | 9 tables exist    |
| 11.PR.03 | spark + jupyter containers  | `docker compose` full profile                 | `docker ps`       |
| 11.PR.04 | seed mock data              | `scripts/03-mock-data-seed.sh`                | `issue-log.csv`   |
| 11.PR.05 | seed validation             | `scripts/04-mock-data-validate.sh`            | row/issue counts  |
| 11.PR.06 | notebook connectivity       | `scripts/06-notebook-validate.sh`             | template passes   |
| 11.PR.07 | deliverable scaffold check  | `scripts/07-deliverables-scaffold.sh --check` | current           |

01. **11.PR.02** covers only DDL; a fresh clone must still run step 04 before any profiling query returns rows.
02. **11.PR.03** uses `docker/docker-compose.full.yml`; the master, both workers, and the Jupyter container must all be `Up` before the notebook is executed - the multi-worker topology is load-bearing here specifically, since [performance-optimization design](#performance-optimization-design) demonstrates against it directly.

### assessment task to deliverable map

One row per assignment task, naming the deliverable file it lands in and the executable artifact it is derived from. This is the traceability contract every write-up's **Sources** section must satisfy.

| id       | assignment task                       | deliverable file [01]     | artifact           |
| -------- | ---------------------------------------- | -------------------------- | ------------------- |
| 11.DM.01 | task 1 profiling                          | `profiling-summary`         | notebook            |
| 11.DM.02 | task 1 Spark-scale handling narrative     | `profiling-summary`         | notebook            |
| 11.DM.03 | task 2 end-to-end reconciliation matrix   | `reconciliation-results`    | `rc_*` + notebook   |
| 11.DM.04 | task 3 duplicate-processing detection     | `exception-dataset`         | notebook            |
| 11.DM.05 | task 3 effective-dated join fix           | `root-cause-analysis`       | notebook            |
| 11.DM.06 | task 3 cross-border sufficiency assessment | `root-cause-analysis`      | narrative           |
| 11.DM.07 | task 3 late-arrival quantification        | `root-cause-analysis`       | notebook            |
| 11.DM.08 | task 4 lineage documentation              | `lineage-doc`                | narrative           |
| 11.DM.09 | task 5 dashboard KPIs/visuals             | manifest reference row      | `.pbip` template    |
| 11.DM.10 | technical optimization question           | `performance-notes`         | narrative + notebook |
| 11.DM.11 | five-minute presentation summary          | `presentation-summary`      | narrative           |
| 11.DM.12 | notebook                                  | manifest reference row      | notebook            |
| 11.DM.13 | scenario and task context                 | `overview`                  | assignment doc      |

01. file names are `results/assessment-3/assessment-3-<slug>.md` per [08](../features/08-assessment-deliverables-conventions.md#directory-and-naming-convention).
02. **11.DM.13** is the authored context page introduced by this tracker, outside feature 08's generated taxonomy - see [assessment context documentation](#assessment-context-documentation).
03. task 3's four defects split across `exception-dataset` (row-level detail, **11.DM.04**) and `root-cause-analysis` (the explanation of each defect's mechanism and impact, **11.DM.05**-**11.DM.07**), the same division [10](10-as02-financial-accounting-gl.md#assessment-task-to-deliverable-map) draws for Assessment 2's task 3.

### workflow cycle

Identical five-stage loop to [09](09-as01-data-profiling-reconciliation.md#workflow-cycle), reused rather than redesigned so every claim in a markdown deliverable stays reproducible from a seeded database.

```
seed db  ->  notebook / spark  ->  rc_* control tables  ->  results markdown  ->  validation run
   ^                                                                                     |
   |_____________________________ rerun on any change ___________________________________|
```

| id       | stage             | action                                                   |
| -------- | ----------------- | ---------------------------------------------------------- |
| 11.WS.01 | seed db           | confirm seeded state, capture the seed run's `issue-log`    |
| 11.WS.02 | notebook / spark  | add or update the task's cells, execute top to bottom       |
| 11.WS.03 | control tables    | write measured results to `reconciliation.rc_*`             |
| 11.WS.04 | results markdown  | update the mapped deliverable and its **Sources** section   |
| 11.WS.05 | validation run    | rerun the scripted checks and record `[PASS]`/`[FAIL]`      |

01. **11.WS.03** applies to task 2's end-to-end reconciliation matrix only; profiling statistics, task 3's narrative findings, lineage documentation, and the performance narrative stop at **11.WS.02** and are cited by notebook cell rather than `batch_id`.
02. **11.WS.04** never restates a number the notebook did not produce in the same run - a changed measurement means the deliverable is edited in the same cycle, not the next one.
03. the Power BI substitute for **11.WS.04** is a `.pbip` edit plus `scripts/05-powerbi-sync.sh`, same as [09](09-as01-data-profiling-reconciliation.md#workflow-cycle) established for Assessment 1's dashboard mock-up.

### assessment context documentation

Same gap and same fix as [09](09-as01-data-profiling-reconciliation.md#assessment-context-documentation): the deliverables scaffolded by [08](../features/08-assessment-deliverables-conventions.md) present measurements without the assignment context that motivated them.

- **overview page** - `results/assessment-3/assessment-3-overview.md` restates the Assessment 3 scenario, the four dataset shapes, Tasks 1-5, the technical optimization question, and the expected deliverable list in the assignment's own framing
- **scale statement** - one paragraph naming the assignment's stated production volumes (the reconciliation-matrix example figures, and the 5-billion-row/40-minute performance scenario) alongside this demo's seeded volume budget, so every number published elsewhere is read against the right scale rather than mistaken for a production figure
- **per-deliverable context** - each deliverable opens with a single line, directly under its `status:` marker, naming the assignment task it answers and linking the overview page
- **linkage** - the overview is authored content outside feature 08's generated taxonomy, so it is linked from `results/index.md` and from each deliverable rather than from the generated manifest
- **no restatement of findings** - the overview carries assignment context only; measured results stay in their own deliverables so there is one place a number can change

### profiling design - task 1

**11.CK.01 - duplicate `payment_id`** - measured at `source.payment_transactions`, not Bronze: Bronze's business key is `(payment_id, batch_id)`, so a Bronze-level repeat is a different signal (**11.CK.21**'s reload detection), and folding the two together would double-count the same population under two checks.

```sql
SELECT payment_id, COUNT(*) AS n
FROM source.payment_transactions
GROUP BY payment_id
HAVING COUNT(*) > 1
```

**11.CK.02 - missing `customer_id`**

```sql
SELECT COUNT(*) FROM source.payment_transactions WHERE customer_id IS NULL OR TRIM(customer_id) = ''
```

**11.CK.03 - invalid payment status** - against the schema's closed set:

```sql
SELECT DISTINCT status FROM source.payment_transactions
WHERE status NOT IN ('COMPLETED', 'PENDING', 'FAILED', 'REJECTED')
```

**11.CK.04 - missing currency**

```sql
SELECT COUNT(*) FROM source.payment_transactions WHERE currency IS NULL OR TRIM(currency) = ''
```

**11.CK.05 - invalid beneficiary country** - ISO 3166-1 alpha-2 shape check, not a full country-code lookup table (none is seeded):

```sql
SELECT DISTINCT beneficiary_country FROM source.payment_transactions
WHERE beneficiary_country IS NULL OR beneficiary_country !~ '^[A-Z]{2}$'
```

**11.CK.06 - negative or zero payment amount**

```sql
SELECT COUNT(*) FROM source.payment_transactions WHERE amount <= 0
```

**11.CK.07 - missing customer reference record** - no `bronze.customer_master` row for the `customer_id` at all, at any effective date:

```sql
SELECT p.payment_id, p.customer_id
FROM bronze.payment_transactions p
WHERE NOT EXISTS (SELECT 1 FROM bronze.customer_master c WHERE c.customer_id = p.customer_id)
```

**11.CK.08 - payment linked to inactive customer record** - distinguished from **11.CK.07** by *some* `customer_master` history existing, but none of it currently open (`effective_end_date IS NULL`):

```sql
SELECT p.payment_id, p.customer_id
FROM bronze.payment_transactions p
WHERE EXISTS (SELECT 1 FROM bronze.customer_master c WHERE c.customer_id = p.customer_id)
  AND NOT EXISTS (
    SELECT 1 FROM bronze.customer_master c
    WHERE c.customer_id = p.customer_id AND c.effective_end_date IS NULL
  )
```

**11.CK.09 - multiple active (effective-dated) customer records** - overlapping windows for the same `customer_id`, the same self-join shape as [10](10-as02-financial-accounting-gl.md#mapping-validation-design--task-2)'s **10.CK.12**:

```sql
SELECT a.customer_id, a.effective_start_date, a.effective_end_date,
       b.effective_start_date AS overlap_start, b.effective_end_date AS overlap_end
FROM bronze.customer_master a
JOIN bronze.customer_master b
  ON  a.customer_id = b.customer_id
  AND a.effective_start_date < b.effective_start_date
  AND a.effective_start_date <= COALESCE(b.effective_end_date, DATE '9999-12-31')
  AND COALESCE(a.effective_end_date, DATE '9999-12-31') >= b.effective_start_date
```

**11.CK.10 - unusual transaction-volume spikes** - a daily count more than 2 standard deviations from the seeded period's own mean:

```sql
WITH daily AS (
  SELECT payment_date, COUNT(*) AS n FROM bronze.payment_transactions GROUP BY payment_date
),
stats AS ( SELECT AVG(n) AS mean_n, STDDEV_SAMP(n) AS sd_n FROM daily )
SELECT d.payment_date, d.n, (d.n - s.mean_n) / NULLIF(s.sd_n, 0) AS z_score
FROM daily d CROSS JOIN stats s
WHERE ABS((d.n - s.mean_n) / NULLIF(s.sd_n, 0)) > 2
```

**11.CK.11 - unexpected payment-channel distribution** - a channel's daily share of volume deviating more than 15 percentage points from its own period-average share:

```sql
WITH channel_share AS (
  SELECT payment_date, payment_channel,
         COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (PARTITION BY payment_date) AS daily_share
  FROM bronze.payment_transactions
  GROUP BY payment_date, payment_channel
),
baseline AS ( SELECT payment_channel, AVG(daily_share) AS baseline_share FROM channel_share GROUP BY payment_channel )
SELECT cs.payment_date, cs.payment_channel, cs.daily_share, b.baseline_share
FROM channel_share cs JOIN baseline b USING (payment_channel)
WHERE ABS(cs.daily_share - b.baseline_share) > 0.15
```

**11.CK.12 - cross-border classification anomalies** - profiling-level: rows the classification in [end-to-end reconciliation design](#end-to-end-reconciliation-design--task-2) cannot evaluate at all, or evaluates to a mismatched result due to case/whitespace noise rather than a genuine cross-border payment (Task 3's **11.CK.23** is the separate question of whether the classification *rule itself* is adequate):

```sql
SELECT p.payment_id, c.residence_country, p.beneficiary_country
FROM bronze.payment_transactions p
LEFT JOIN bronze.customer_master c
  ON  c.customer_id = p.customer_id
  AND p.payment_date BETWEEN c.effective_start_date AND COALESCE(c.effective_end_date, DATE '9999-12-31')
WHERE c.residence_country IS NULL
   OR (UPPER(TRIM(c.residence_country)) = UPPER(TRIM(p.beneficiary_country))
       AND c.residence_country <> p.beneficiary_country)
```

**presentation** - single-row summary for count-style checks (**11.CK.01**-**11.CK.08**), a distribution table for the channel/volume checks (**11.CK.10**-**11.CK.12**), carried into the profiling summary write-up.

**Spark-scale narrative** - one section explaining how each check would run efficiently at the assignment's real scale (partitioned scans, `approx_count_distinct` for the cardinality checks, `broadcast(customer_master)` for **11.CK.07**-**11.CK.09**'s reference-lookup joins) even though it executes here against the seeded volume budget - a narrower, task-1-scoped preview of [performance-optimization design](#performance-optimization-design).

**expected findings** - the assessment 3 issue counts from [04](../features/04-seed-mock-data.md#injected-issue-catalog--assessment-3) that each check must reproduce.

### end-to-end reconciliation design - task 2

**classification formula** - `regulatory.payment_reporting.domestic_crossborder_flag` has no equivalent column in Source/Bronze, so the *correct* (effective-dated) classification is derived at query time for the Source/Bronze sides of every comparison below:

```sql
CASE WHEN c.residence_country = p.beneficiary_country THEN 'DOMESTIC' ELSE 'CROSSBORDER' END
```

joined via `bronze.customer_master` on `customer_id` + `payment_date BETWEEN effective_start_date AND COALESCE(effective_end_date, DATE '9999-12-31')` - the same correct join [complex issue detection](#complex-issue-detection--task-3)'s **11.CK.22** contrasts against the pipeline's naive one.

**finest-grain three-tier aggregate** - Source and Bronze are aggregated to the same grain before comparison, since `regulatory.payment_reporting` is itself pre-aggregated (no `payment_id` column) and has no finer grain to drill into:

```sql
WITH source_agg AS (
  SELECT p.payment_date AS reporting_date, p.legal_entity, p.payment_type, p.currency,
         CASE WHEN c.residence_country = p.beneficiary_country THEN 'DOMESTIC' ELSE 'CROSSBORDER' END
           AS domestic_crossborder_flag,
         COUNT(*) AS txn_count, SUM(p.amount) AS amount
  FROM source.payment_transactions p
  JOIN bronze.customer_master c
    ON c.customer_id = p.customer_id
   AND p.payment_date BETWEEN c.effective_start_date AND COALESCE(c.effective_end_date, DATE '9999-12-31')
  GROUP BY 1, 2, 3, 4, 5
),
bronze_agg AS ( -- identical shape, FROM bronze.payment_transactions ),
regulatory_agg AS (
  SELECT reporting_date, legal_entity, payment_type, reporting_currency AS currency, domestic_crossborder_flag,
         SUM(transaction_count) AS txn_count, SUM(total_transaction_amount) AS amount
  FROM regulatory.payment_reporting
  GROUP BY 1, 2, 3, 4, 5
)
```

**11.CK.13-11.CK.20 - per-dimension matrix rows** - each dimension rolls the finest-grain aggregate above up to one column, `FULL OUTER JOIN`ed across the three CTEs on that column alone (matching [10](10-as02-financial-accounting-gl.md#gl-integrity-design--task-1)'s per-dimension roll-up pattern):

```sql
-- <dimension> is one of: reporting_date, legal_entity, payment_type, currency, domestic_crossborder_flag
SELECT COALESCE(s.<dimension>, b.<dimension>, r.<dimension>) AS <dimension>,
       s.txn_count AS source, b.txn_count AS bronze, r.txn_count AS regulatory,
       r.txn_count - s.txn_count AS variance,
       CASE
         WHEN ABS(r.txn_count - s.txn_count) / NULLIF(ABS(s.txn_count), 0) < 0.001 THEN 'PASS'
         WHEN ABS(r.txn_count - s.txn_count) / NULLIF(ABS(s.txn_count), 0) < 0.01  THEN 'WARNING'
         ELSE 'FAIL'
       END AS status
FROM (SELECT <dimension>, SUM(txn_count) AS txn_count FROM source_agg GROUP BY <dimension>) s
FULL OUTER JOIN (SELECT <dimension>, SUM(txn_count) AS txn_count FROM bronze_agg GROUP BY <dimension>) b
  USING (<dimension>)
FULL OUTER JOIN (SELECT <dimension>, SUM(txn_count) AS txn_count FROM regulatory_agg GROUP BY <dimension>) r
  USING (<dimension>)
```

**11.CK.14 - payment amount** and **11.CK.15 - customer count** are the two exceptions to the roll-up-by-summing pattern above:
- **payment amount** sums `amount`/`total_transaction_amount` instead of `txn_count` - otherwise identical.
- **customer count** cannot be derived from `source_agg`/`bronze_agg` by summing, since `COUNT(DISTINCT customer_id)` does not roll up additively across a `GROUP BY` that already collapsed `customer_id` away; it is computed as its own query directly against the row-level tables (`COUNT(DISTINCT customer_id)` grouped by whichever single dimension is being matrix-rolled), and `regulatory.payment_reporting`'s side is `COUNT(DISTINCT customer_id)` grouped the same way, not `SUM(transaction_count)`.

**matrix output** - `Dimension | Source | Bronze | Regulatory | Variance | Status`, one row per dimension per the query above, matching the assignment's own worked example shape.

**regulatory-stage caveat** - `regulatory.payment_reporting`'s row count is not independently seeded; per [04](../features/04-seed-mock-data.md#injected-issue-catalog--assessment-3), it is the generator's own replay of the naive (non-effective-dated) join, so the Bronze-vs-Regulatory variance this task measures is the same fan-out [complex issue detection](#complex-issue-detection--task-3) is asked to explain, not two independent findings.

**scale note** - the standard wording stating measured values come from the seeded volume budget, not the assignment's illustrative production-scale figures.

### complex issue detection - task 3

**11.CK.21 - duplicate processing** - the distinguishing rule separating a reload duplicate from a legitimate repeated payment (issue 01 in the seed catalog is the deliberate control case for this) is `record_hash`, not `payment_id` alone: a true reload carries the *same* business-field hash under two different `batch_id`s, while a coincidentally-shared `payment_id` on a genuinely different payment produces a different hash and is correctly excluded:

```sql
SELECT payment_id, record_hash, COUNT(DISTINCT batch_id) AS batch_count
FROM bronze.payment_transactions
GROUP BY payment_id, record_hash
HAVING COUNT(DISTINCT batch_id) > 1
```

**11.CK.22 - effective-dated join fan-out** - reproduce the pipeline's actual (naive) join, then the corrected one, and diff the two:

```sql
-- naive join the regulatory pipeline actually runs
SELECT p.payment_id, COUNT(*) AS naive_match_count
FROM bronze.payment_transactions p
JOIN bronze.customer_master c ON c.customer_id = p.customer_id
GROUP BY p.payment_id
HAVING COUNT(*) > 1

-- corrected, effective-dated join
SELECT p.payment_id, COUNT(*) AS correct_match_count
FROM bronze.payment_transactions p
JOIN bronze.customer_master c
  ON  c.customer_id = p.customer_id
  AND p.payment_date BETWEEN c.effective_start_date AND COALESCE(c.effective_end_date, DATE '9999-12-31')
GROUP BY p.payment_id
HAVING COUNT(*) > 1  -- should return zero rows once 11.CK.09's overlaps are otherwise clean
```

The row-count delta (`naive_match_count - 1`, summed over every affected `payment_id`) is the fan-out quantity - each such payment appears once for every `customer_master` row it naively matched, one of which is correct and the rest of which are the duplicate regulatory records **11.CK.22** is asked to detect.

**11.CK.23 - cross-border sufficiency** - narrative assessment of the current rule (`CASE WHEN c.residence_country <> p.beneficiary_country THEN 'CROSSBORDER' ELSE 'DOMESTIC' END`, the same expression [end-to-end reconciliation design](#end-to-end-reconciliation-design--task-2) uses), naming at least one concrete banking scenario it misclassifies - e.g. a domestic payment routed through a foreign correspondent bank, a resident with a foreign-domiciled account, or a payment for a customer with no `residence_country` on file (**11.CK.07**/**11.CK.08**), which the rule cannot classify at all rather than defaulting safely.

**11.CK.24 - late-arriving transactions** - `regulatory.payment_reporting` has no `payment_id`, so detection is two-step: identify the *candidate* late-arriving population in Bronze by processing-time proximity to a configurable ingestion cutoff, then confirm the day-pair count/amount shift in the regulatory aggregate:

```sql
-- step 1: candidate population (CUTOFF_TIME default 22:00 local, configurable)
SELECT payment_id, payment_date, payment_timestamp
FROM bronze.payment_transactions
WHERE payment_timestamp::time >= TIME '22:00'

-- step 2: confirm a same-key shortfall on payment_date matched by a surplus on payment_date + 1
SELECT r1.reporting_date, r1.customer_id, r1.payment_type, r1.legal_entity, r1.domestic_crossborder_flag,
       r1.transaction_count AS day_count, r2.transaction_count AS next_day_count,
       r2.total_transaction_amount AS next_day_amount_shifted
FROM regulatory.payment_reporting r1
JOIN regulatory.payment_reporting r2
  ON  r1.customer_id = r2.customer_id AND r1.payment_type = r2.payment_type
  AND r1.legal_entity = r2.legal_entity AND r1.domestic_crossborder_flag = r2.domestic_crossborder_flag
  AND r2.reporting_date = r1.reporting_date + INTERVAL '1 day'
```

The regulatory impact is `SUM(next_day_amount_shifted)` across confirmed pairs - transaction count and amount reported as shifted from their true `payment_date` into the following reporting date.

### exception dataset

- **schema** - at minimum `payment_id`, `issue_type`, `source_value`, `regulatory_value`, `variance`, `batch_id`, mirroring [09](09-as01-data-profiling-reconciliation.md#exception-dataset)'s minimum columns adapted to this assessment's three-stage comparison
- **materialisation** - table, notebook output, or embedded markdown extract, with the full row set's location stated where the write-up shows only a sample
- **ground-truth check** - the comparison against `issue-log.csv` proving detected issues match injected ones

**issue_type vocabulary** - the closed set of string values every check writes, matched against `issue-log.csv`'s own `issue_type` spelling so ground-truth comparison is a direct join:

| check id | `issue_type`               |
| -------- | ----------------------------- |
| 11.CK.01 | `DUPLICATE_PAYMENT_ID`          |
| 11.CK.02 | `MISSING_CUSTOMER_ID`           |
| 11.CK.03 | `INVALID_STATUS`                |
| 11.CK.04 | `MISSING_CURRENCY`              |
| 11.CK.05 | `INVALID_BENEFICIARY_COUNTRY`   |
| 11.CK.06 | `NEGATIVE_OR_ZERO_AMOUNT`       |
| 11.CK.07 | `MISSING_CUSTOMER_REFERENCE`    |
| 11.CK.08 | `INACTIVE_CUSTOMER_REFERENCE`   |
| 11.CK.09 | `OVERLAPPING_CUSTOMER_RECORD`   |
| 11.CK.21 | `DUPLICATE_PROCESSING`          |
| 11.CK.22 | `EFFECTIVE_DATE_JOIN_FANOUT`    |
| 11.CK.24 | `LATE_ARRIVAL_MISASSIGNED`      |

01. **11.CK.10**-**11.CK.12** and **11.CK.23** are distributional/narrative findings rather than row-level flags on an individual `payment_id`, so they do not carry an `issue_type` row in this table - they are reported directly in the profiling summary / root-cause write-up instead.
02. a `payment_id` may carry more than one `issue_type` (e.g. `MISSING_CUSTOMER_REFERENCE` and `DUPLICATE_PROCESSING` both true) - one row per `(payment_id, issue_type)` pair, same convention as [10](10-as02-financial-accounting-gl.md#exception-dataset)'s exception dataset.

### lineage documentation - task 4

**row shape** - `Regulatory Attribute | Source | Source Column | Bronze | Transformation | Data Quality Control`, per the assignment's own table. The five required rows, source column(s), and controlling check id(s) - the transformation each one applies is detailed in the notes below rather than in-cell, per the markdown-tables convention for long cell content:

| id | regulatory attribute | source column                              | control                    |
| -- | -------------------- | ------------------------------------------ | -------------------------- |
| 01 | Total Payment Amount | `amount`                                   | **11.CK.14**               |
| 02 | Transaction Count    | `payment_id`                               | **11.CK.13**               |
| 03 | Cross Border Flag    | `beneficiary_country`, `residence_country` | **11.CK.19**, **11.CK.23** |
| 04 | Reporting Date       | `payment_date`                             | **11.CK.20**, **11.CK.24** |
| 05 | Customer Count       | `customer_id`                              | **11.CK.15**, **11.CK.22** |

01. **Total Payment Amount** - source: Payment System; Bronze: `bronze.payment_transactions.amount`; transformation: `SUM(amount)` grouped by `reporting_date, legal_entity, payment_type, currency, domestic_crossborder_flag`.
02. **Transaction Count** - source: Payment System; Bronze: `bronze.payment_transactions`; transformation: `COUNT(*)` over the same grouping as row 01.
03. **Cross Border Flag** - source: Payment System + Customer Reference; Bronze: `bronze.payment_transactions` joined to `bronze.customer_master`; transformation: the effective-dated `CASE` expression from [end-to-end reconciliation design](#end-to-end-reconciliation-design--task-2).
04. **Reporting Date** - source: Payment System; Bronze: `bronze.payment_transactions.payment_date`; transformation: `reporting_date := payment_date`, except the late-arriving population which the defective pipeline misassigns to `payment_date + 1` (the exact defect **11.CK.24** detects).
05. **Customer Count** - source: Customer Reference; Bronze: `bronze.customer_master`; transformation: `COUNT(DISTINCT customer_id)` via the effective-dated join, per grouping.

**critical data elements** - the nominated CDE list stated with justification, echoing the same "table not prose" convention [09](09-as01-data-profiling-reconciliation.md#profiling-design--task-1) uses for its own CDE list; the five rows above are the CDE list itself, one CDE per lineage row, so no separate table is authored.

**control linkage** - each row's `Data Quality Control` column names an actual check id from [profiling design](#profiling-design--task-1), [end-to-end reconciliation design](#end-to-end-reconciliation-design--task-2), or [complex issue detection](#complex-issue-detection--task-3) rather than an aspirational, unimplemented control.

### dashboard design - task 5

The dashboard deliverable is satisfied by the existing `.pbip` template owned by [06](../features/06-powerbi-dashboard-setup.md), extended with an Assessment 3 view, not by a new Power BI project - the same reuse [09](09-as01-data-profiling-reconciliation.md#dashboard-mock-up) already established for Assessment 1. Edits are made in the tracked template, synced to the Windows-side working copy with `scripts/05-powerbi-sync.sh`, opened and saved in Power BI Desktop by the user, then synced back.

**executive KPIs** - each measure's exact source, so the DAX/Power Query measure is unambiguous:

| KPI                      | measure                                                                |
| ------------------------ | ---------------------------------------------------------------------- |
| source records           | `SUM(source_agg.txn_count)` [01]                                       |
| Bronze records           | `SUM(bronze_agg.txn_count)` [01]                                       |
| regulatory records       | `SUM(regulatory_agg.txn_count)` [01]                                   |
| reconciliation rate      | `1 - COUNT(status='FAIL') / COUNT(*)` over `rc_reconciliation_results` |
| financial variance       | `SUM(variance)`, payment-amount row of the reconciliation matrix       |
| data-quality issue count | `COUNT(*)` from the exception dataset                                  |
| critical exception count | `COUNT(*)` from the exception dataset, `issue_type` in [02]            |

01. `source_agg`/`bronze_agg`/`regulatory_agg` are the three CTEs from [end-to-end reconciliation design](#end-to-end-reconciliation-design--task-2).
02. `('EFFECTIVE_DATE_JOIN_FANOUT', 'DUPLICATE_PROCESSING', 'LATE_ARRIVAL_MISASSIGNED')` - the three highest-impact [exception dataset](#exception-dataset) categories.

**recommended visuals** - reconciliation status by reporting date, exception trend, variance by legal entity, variance by payment type, data-quality issues by category, top failing controls, Source-to-Bronze reconciliation trend, regulatory reconciliation trend - each binds directly to `reconciliation.rc_reconciliation_results` (`dimension`, `reconciliation_status`, `batch_date` via `rc_batch_control`) or the exception dataset's `issue_type` column, not a separately-modeled Power BI table.

**filters** - date, legal entity, currency, payment type, data-quality status - implemented as slicers on the columns above, shared across all visuals via the report page's sync-slicer setting.

**data source** - the `reconciliation.rc_*` tables the template already binds to, plus the task 2 reconciliation matrix for the three-stage visuals.

**user action** - the Desktop open/save round trip that only the user can perform.

### performance-optimization design

Answered by design and small-scale demonstration, not literal 5B-row execution, per [milestones.md](../milestones.md)'s `assessment 3` closure note - no billion-row dataset is generated; the Spark SQL is written to scale and demonstrated against the seeded data with an explicit note on the scale delta.

**techniques addressed and how each is demonstrated:**

| technique              | demonstration                                                              |
| ---------------------- | -------------------------------------------------------------------------- |
| partition strategy     | partition `bronze.payment_transactions` by `payment_date` (daily) [01]     |
| partition pruning      | `payment_date` range filter, confirmed via `explain()` [02]                |
| broadcast joins        | `F.broadcast(customer_master_df)` on every join to `customer_master` [03]  |
| incremental processing | reprocess only rows newer than the last batch's `ingestion_timestamp` [04] |
| pre-aggregated tables  | `reconciliation.rc_reconciliation_results` itself is the pattern           |

01. matches every reconciliation query's own `WHERE`/`GROUP BY` axis in [end-to-end reconciliation design](#end-to-end-reconciliation-design--task-2).
02. against the proposed partitioning from row 01, confirming a full scan is skipped rather than merely asserting it.
03. `bronze.customer_master` is small (low thousands of rows), avoiding a shuffle join against the much larger `bronze.payment_transactions`.
04. `ingestion_timestamp > (SELECT MAX(batch_date) FROM reconciliation.rc_batch_control WHERE assessment_id = 'assessment-3')`, rather than a full-table rerun on every batch.

Delta optimization (`OPTIMIZE`/Z-ORDER), data skipping, and predicate pushdown are explained conceptually only - they are Delta Lake/Databricks-runtime features this dev environment's plain-Parquet/postgres Spark setup does not stand up, so no demonstration is claimed for them.

**demonstration shape** - one Spark job run twice against `bronze.payment_transactions` at the seeded volume: once as a naive full scan with a row-wise join against `bronze.customer_master`, once applying partition pruning + the broadcast join above, reporting the wall-clock delta as evidence of *direction*, not magnitude - the write-up states explicitly that the seeded row count is far below the 40-minute baseline's threshold, so the delta demonstrates the technique, not the production time saving.

**what changed and why** - the write-up states the reasoning per technique against this assessment's own join/aggregation shape (the `customer_master` broadcast join, the `payment_date`-keyed reconciliation queries), not a generic Spark feature list.

### notebook organisation

`notebooks/assessment3_regulatory_dashboard.ipynb` is the single executable artifact for this assessment, sectioned in assignment order - connectivity, task 1 profiling, task 2 reconciliation, task 3 complex issues, performance-optimization demonstration - so a deliverable's **Sources** reference can name a section rather than a cell index that shifts on edit. Output commit policy follows [07](../features/07-jupyter-notebook-workspace-setup.md); the notebook must execute cleanly top to bottom against a freshly seeded database before 11.12 closes.

### idempotency / rerun-safety

- **notebook** - re-executable end to end against a freshly seeded database with no manual cell ordering; any writes it makes are keyed by `batch_id` so a rerun appends a new batch rather than mutating a prior one.
- **control tables** - reruns insert a new `rc_batch_control` row (`assessment_id = 'assessment-3'`); existing batches are never updated in place, preserving the evidence a published deliverable already cites.
- **deliverable markdown** - authored content, never regenerated by a script; `07-deliverables-scaffold.sh` remains verify-or-create and only the derived `README.md` manifest is rewritten.
- **seed data** - regenerated only by `scripts/03-mock-data-seed.sh`, which is deterministic under the fixed `MOCK_DATA_SEED`; this tracker never edits seeded rows directly.

### environment & secrets

No new variables and no new secrets. The work reuses the existing postgres connection settings, `LOGS_DIR`, `TIMEZONE`, and `TIMESTAMP_FORMAT` from `.env`, and the Power BI sync paths from [06](../features/06-powerbi-dashboard-setup.md#environment--secrets). Credentials are never written into a notebook cell, a deliverable markdown file, or the published site.

### workflow validation runner

Assessment 3 introduces no new runner by default; validation composes the existing scripts in [prerequisites](#prerequisites) plus `scripts/06-notebook-validate.sh` for headless notebook execution and `scripts/07-deliverables-scaffold.sh --check` for deliverable completeness. If a per-assessment orchestration step proves necessary, it is added as the next free script number and logged under `.dev/logs/` with `<ts>-11.<nn>-<name>.log` naming, printing one `[PASS]`/`[FAIL]` line per stage of the [workflow cycle](#workflow-cycle).

### publishing

Once every deliverable is promoted to `status: final`, `scripts/07-deliverables-scaffold.sh` regenerates the Assessment 3 manifest with the updated statuses, `scripts/08-assessment-site.sh build` validates the strict MkDocs build, and `scripts/08-assessment-site.sh deploy` publishes to `gh-pages` from a clean, reviewed worktree. The overview page must be reachable from the published navigation before deploy. Deployment is never run with uncommitted assessment evidence in the tree.

## Test cases

_test strategy_

Findings are validated at three layers so a measurement is never trusted on the strength of the write-up alone:

1. **script self-report** - `[PASS]`/`[FAIL]` lines and timestamped logs from the prerequisite and validation scripts show each stage ran.
2. **ground-truth comparison** - detected issues are joined against `data/mock/issue-log.csv`, the injected catalog from [04](../features/04-seed-mock-data.md), rather than eyeballed.
3. **content inspection** - deliverable markdown is checked for required headings, `status:` markers, context and source references, and table shape independently of the notebook that produced the numbers.

_test cases_

| id       | task  | layer        | check                                          |
| -------- | ----- | ------------ | ------------------------------------------------ |
| 11.TC.01 | 11.02 | script       | all prerequisite steps report `[PASS]`            |
| 11.TC.02 | 11.02 | ground-truth | seeded issue counts match the issue log           |
| 11.TC.03 | 11.03 | content      | overview states scenario, tasks, and scale        |
| 11.TC.04 | 11.03 | content      | every deliverable links the overview page         |
| 11.TC.05 | 11.04 | content      | every task 1 statistic is in the write-up         |
| 11.TC.06 | 11.04 | ground-truth | profiling counts match injected issue rows        |
| 11.TC.07 | 11.05 | script       | reconciliation matrix lands in `rc_*` for one batch |
| 11.TC.08 | 11.05 | content      | matrix reports all eight dimensions               |
| 11.TC.09 | 11.06 | content      | exception dataset carries the minimum columns     |
| 11.TC.10 | 11.06 | ground-truth | exception rows reconcile to the issue log         |
| 11.TC.11 | 11.07 | content      | all four complex-issue defects are addressed      |
| 11.TC.12 | 11.08 | content      | lineage doc covers at least five attributes       |
| 11.TC.13 | 11.09 | direct-fs    | dashboard round trip leaves no diff               |
| 11.TC.14 | 11.10 | content      | performance notes state technique + reasoning     |
| 11.TC.15 | 11.11 | content      | presentation summary fits a five-minute scope     |
| 11.TC.16 | 11.12 | script       | notebook executes clean top to bottom             |
| 11.TC.17 | 11.13 | content      | every deliverable reads `status: final`           |
| 11.TC.18 | 11.14 | build        | strict MkDocs build succeeds                      |
| 11.TC.19 | 11.14 | deployment   | published site shows assessment 3 pages           |

**tools**

```bash
cd /home/taylor-hickem/repos/de-financial-accounting-demo
./scripts/00-prereq-check.sh
./scripts/03-mock-data-seed.sh
./scripts/04-mock-data-validate.sh
./scripts/06-notebook-validate.sh
./scripts/07-deliverables-scaffold.sh --check
./scripts/08-assessment-site.sh build
grep -R --line-number '^status: \(draft\|final\)$' results/assessment-3
grep -RL 'assessment-3-overview.md' results/assessment-3/assessment-3-*.md
awk '/^\|/ && length($0) >= 115 { print FILENAME ":" FNR ": row too long"; bad = 1 } END { exit bad }' results/assessment-3/*.md
```

## Edit locations

| id       | path                                                           | change                       |
| -------- | --------------------------------------------------------------- | ---------------------------- |
| 11.EL.01 | `notebooks/assessment3_regulatory_dashboard.ipynb`              | full analysis notebook       |
| 11.EL.02 | `results/assessment-3/assessment-3-profiling-summary.md`        | task 1 write-up               |
| 11.EL.03 | `results/assessment-3/assessment-3-reconciliation-results.md`   | task 2 write-up               |
| 11.EL.04 | `results/assessment-3/assessment-3-exception-dataset.md`        | task 3 exception write-up     |
| 11.EL.05 | `results/assessment-3/assessment-3-root-cause-analysis.md`      | task 3 narrative write-up     |
| 11.EL.06 | `results/assessment-3/assessment-3-lineage-doc.md`              | task 4 write-up               |
| 11.EL.07 | `results/assessment-3/assessment-3-performance-notes.md`        | performance write-up          |
| 11.EL.08 | `results/assessment-3/assessment-3-presentation-summary.md`     | presentation write-up         |
| 11.EL.09 | `results/assessment-3/README.md`                                 | regenerated manifest          |
| 11.EL.10 | `powerbi/reconciliation-dashboard-template/`                    | assessment 3 dashboard view   |
| 11.EL.11 | `src/sparksql/`                                                  | reusable query files          |
| 11.EL.12 | `docs/milestones.md`                                             | milestone 11 status/closure   |
| 11.EL.13 | `results/assessment-3/assessment-3-overview.md`                 | assessment scope context      |
| 11.EL.14 | `results/index.md`                                               | link to the overview page     |
| 11.EL.15 | `mkdocs.yml`                                                     | overview in site nav          |

01. **11.EL.09** is generated by `scripts/07-deliverables-scaffold.sh`; never hand-edited.
02. **11.EL.11** is optional - used only where a query is worth extracting from the notebook for reuse, following the existing `src/pyspark/` naming pattern.
03. **11.EL.13** is authored content outside feature 08's generated taxonomy, so the scaffold neither creates nor validates it; it is created by hand in 11.03.
04. **11.EL.15** is only required if the strict build cannot reach the overview through `11.EL.14`'s link alone.

No `.env`, `.env.sample`, schema JSON, DDL, or seed-script change is expected. A required change to any of those is a defect in the owning feature and is raised there rather than patched from this tracker.

## Implement

Implementation order is prerequisites -> assessment context -> profiling -> end-to-end reconciliation -> exceptions -> complex issue detection -> lineage -> dashboard -> performance notes -> presentation summary -> notebook rerun -> review -> publish. Each step runs the full [workflow cycle](#workflow-cycle) before the next begins.

### 1. Prerequisites and seed data readiness

edit locations: none

Run the [prerequisites](#prerequisites) steps in order, confirming the evidence column for each. Record the seed run's issue counts as the baseline every later ground-truth comparison is made against. Do not start task 1 until every prerequisite reports `[PASS]`.

### 2. Assessment scope and context write-up

edit locations: `11.EL.13, 11.EL.14, 11.EL.15`

Author `results/assessment-3/assessment-3-overview.md` per [assessment context documentation](#assessment-context-documentation): the Assessment 3 scenario, the four dataset shapes, Tasks 1-5, the technical optimization question, the expected deliverable list, and the scale statement contrasting the assignment's 5B-row/40-minute figures with this demo's seeded volume budget. Link it from `results/index.md`, and add it to `mkdocs.yml`'s navigation only if the strict build cannot reach it through that link.

This step is done before any analysis write-up so each later deliverable can be authored with its context line already pointing at an existing page.

### 3. Task 1 - transaction banking profiling

edit locations: `11.EL.01, 11.EL.02`

Implement **11.CK.01**-**11.CK.12** exactly as specified in [profiling design](#profiling-design--task-1), against `source.payment_transactions`, `bronze.payment_transactions`, and `bronze.customer_master`, plus the Spark-scale handling narrative. Write the profiling summary deliverable citing the notebook section and referencing the overview page for scenario and scale.

### 4. Task 2 - end-to-end reconciliation

edit locations: `11.EL.01, 11.EL.03`

Implement the `source_agg`/`bronze_agg`/`regulatory_agg` CTEs and **11.CK.13**-**11.CK.20**'s per-dimension roll-up exactly as specified in [end-to-end reconciliation design](#end-to-end-reconciliation-design--task-2), including the `customer_count` exception to the roll-up-by-summing pattern. Write into `reconciliation.rc_*` under one `batch_id` (`assessment_id = 'assessment-3'`). Write the reconciliation results deliverable citing that `batch_id`, in the assignment's matrix shape.

### 5. Exception dataset

edit locations: `11.EL.01, 11.EL.04`

Union the row sets from **11.CK.01**-**11.CK.09**, **11.CK.21**, **11.CK.22**, and **11.CK.24** into the exception dataset's minimum columns per [exception dataset](#exception-dataset), one row per `(payment_id, issue_type)` pair, and reconcile detected rows against `issue-log.csv`. Write the exception dataset deliverable, sampling in the markdown and pointing at the full output.

### 6. Task 3 - complex issue detection

edit locations: `11.EL.01, 11.EL.05`

Implement **11.CK.21**-**11.CK.24** exactly as specified in [complex issue detection](#complex-issue-detection--task-3): the `record_hash`-based duplicate-processing detection, the naive-vs-corrected join diff, the cross-border sufficiency narrative, and the day-pair late-arrival confirmation. Write the root-cause analysis deliverable.

### 7. Task 4 - data lineage documentation

edit locations: `11.EL.06`

Write the lineage deliverable directly from [lineage documentation](#lineage-documentation--task-4)'s five-row table and its transformation notes - this step is a narrative write-up of an already-fully-specified design, not new query development.

### 8. Task 5 - Power BI executive dashboard

edit locations: `11.EL.10`

Edit the tracked `.pbip` template to add the Assessment 3 view, run `scripts/05-powerbi-sync.sh` to push it to the Windows-side working copy, have the user open and save it in Power BI Desktop, then sync back and confirm with an independent `diff -rq` that the round trip lost nothing.

### 9. Performance-optimization notes

edit locations: `11.EL.01, 11.EL.07`

Write the performance-optimization deliverable per [performance-optimization design](#performance-optimization-design): the technique explanations, the small-scale demonstration's wall-clock comparison, and the explicit scale-delta caveat.

### 10. Five-minute presentation summary

edit locations: `11.EL.08`

Write a concise, presentation-scoped summary (bulleted, five-minute-read length) drawing from the profiling, reconciliation, root-cause, lineage, and performance deliverables - a synthesis, not a restatement of any one of them in full.

### 11. Notebook consolidation and clean rerun

edit locations: `11.EL.01`

Reorder the notebook into assignment task order, remove scratch cells, reseed the database, and execute the notebook headless with `scripts/06-notebook-validate.sh`. Confirm every number cited in a deliverable still matches the rerun output; where it does not, correct the deliverable in the same cycle.

### 12. Deliverable review and status promotion

edit locations: `11.EL.02-11.EL.09, 11.EL.13`

Review each deliverable against the [task to deliverable map](#assessment-task-to-deliverable-map) for coverage, a populated **Sources** section, a context line linking the overview, and consistent numbers. Promote each `status: draft` to `status: final`, then run `scripts/07-deliverables-scaffold.sh` to regenerate the manifest with the new statuses and `--check` to confirm the result is current.

### 13. Publish

edit locations: `11.EL.12`

Commit the reviewed work, run `scripts/08-assessment-site.sh build` for the strict build, then `scripts/08-assessment-site.sh deploy` from the clean worktree. Confirm the published Assessment 3 pages, including that the overview is reachable from the site navigation, then update `docs/milestones.md` to mark milestone 11 closed with its closure evidence.

## Validate

**Issues**

- inventory all first out exceptions and issues encountered in this table
- for each issue, create an issue section and use this section to document diagnostics and resolution steps

| id       | seq | status  | issue                                    |
| -------- | --- | ------- | ----------------------------------------- |
| 11.IS.01 | 01  | pending | \<first out exception\>                  |

_11.IS.01 (pending) \<first out exception\>_

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
| 11.IS.01.01 | 01  | pending | \<diagnostic step 01\>               |

**diagnostic details**

**validation evidence**

**user actions**

- Power BI Desktop open/save round trip for the dashboard deliverable (11.09)
- GitHub authentication and the deploy confirmation for the published site (11.14)

## Guideline

## instructions

review and strictly follow these relevant skills when performing tasks for this
feature implementation and working with this document

## relevant skills

- markdown-tables
- feature-implementation-guide
- jupyter-notebook-workspace
- powerbi-dashboard-workspace
