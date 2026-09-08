# Assessment 1 - Source-to-Bronze Data Profiling and Reconciliation - Feature tracker
>Review the guidelines before performing any actions including edits on the document

## 09 (open) assessment 1 - source-to-bronze profiling and reconciliation

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
  - [reconciliation design - task 2](#reconciliation-design--task-2)
  - [exception dataset](#exception-dataset)
  - [root-cause investigation - task 3](#root-cause-investigation--task-3)
  - [dq-control recommendations](#dq-control-recommendations)
  - [dashboard mock-up](#dashboard-mock-up)
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
| ----- | --- | ------- | ---------------------------------------- |
| 09.01 | 01  | closed  | design                                   |
| 09.02 | 02  | closed  | prerequisites and seed data readiness    |
| 09.03 | 03  | closed  | assessment scope and context write-up    |
| 09.04 | 04  | closed  | task 1 - data profiling                  |
| 09.05 | 05  | closed  | task 2 - source-to-bronze reconciliation |
| 09.06 | 06  | closed  | exception dataset                        |
| 09.07 | 07  | closed  | task 3 - root-cause investigation        |
| 09.10 | 08  | closed  | notebook consolidation and clean rerun   |
| 09.11 | 09  | closed  | deliverable review and status promotion  |
| 09.08 | 10  | closed  | dq-control recommendations               |
| 09.IS | 11  | closed  | validate                                 |
| 09.12 | 12  | closed  | publish assessment site                  |
| 09.09 | 13  | drop    | dashboard mock-up                        |
 
## Scope

answer Assessment 1 of the **assignment design doc** end to end - profile `src_transaction_daily` and `bronze.transaction_daily`, reconcile source to Bronze at batch, dimensional, and record level, explain the missing-record symptom, and publish the resulting deliverable set together with the assignment context that motivated it - see [milestones.md](../milestones.md)'s `assessment 1` entry for the milestone-level statement this tracker executes.

**assessment scope** 

condensed from the **assignment design doc**'s Assessment 1 section

- **scenario** a daily Core Banking extract lands in a Databricks-style Bronze layer.
- **the problem** Finance reports that the Bronze total local-currency balance does not match source
- **checks to perform**

| id       | task ref | scope             | check                                         |
| -------- | -------- | ----------------- | --------------------------------------------- |
| 09.CK.01 | 01.01    | datasets profiles | record/distinct counts                        |
| 09.CK.02 | 01.02    | datasets profiles | duplicate transaction ids                     |
| 09.CK.03 | 01.03    | datasets profiles | per-field null percentage                     |
| 09.CK.04 | 01.04    | datasets profiles | min/max transaction and posting dates         |
| 09.CK.05 | 01.05    | datasets profiles | distinct and invalid fx codes and txn types   |
| 09.CK.06 | 01.06    | datasets profiles | negative/zero amounts                         |
| 09.CK.07 | 01.07    | datasets profiles | branch/product/source-file distributions      |
| 09.CK.08 | 01.08    | datasets profiles | late-arriving records                         |
| 09.CK.09 | 01.09    | datasets profiles | posting date preceding transaction date       |
| 09.CK.10 | 01.10    | datasets profiles | FX rows breaching amt exchange-rate tolerance |
| 09.CK.11 | 02.01.01 | batch totals      | record count                                  |
| 09.CK.12 | 02.01.02 | batch totals      | distinct count                                |
| 09.CK.13 | 02.01.03 | batch totals      | debit sum                                     |
| 09.CK.14 | 02.01.04 | batch totals      | credit sum                                    |
| 09.CK.15 | 02.01.05 | batch totals      | net amount                                    |
| 09.CK.16 | 02.01.06 | batch totals      | local-currency sum                            |
| 09.CK.17 | 02.02.01 | dim reconcile     | transaction date                              |
| 09.CK.18 | 02.02.02 | dim reconcile     | branch                                        |
| 09.CK.19 | 02.02.03 | dim reconcile     | currency                                      |
| 09.CK.20 | 02.02.04 | dim reconcile     | product                                       |
| 09.CK.21 | 02.02.05 | dim reconcile     | transaction type                              |
| 09.CK.22 | 02.02.06 | dim reconcile     | source file                                   |
| 09.CK.23 | 02.03.01 | record classify   | exact match                                   |
| 09.CK.24 | 02.03.02 | record classify   | missing in Bronze                             |
| 09.CK.25 | 02.03.03 | record classify   | unexpected in Bronze                          |
| 09.CK.26 | 02.03.04 | record classify   | amount mismatch                               |
| 09.CK.27 | 02.03.05 | record classify   | currency mismatch                             |
| 09.CK.28 | 02.03.06 | record classify   | posting-date mismatch                         |
| 09.CK.29 | 02.03.07 | record classify   | duplicate in source                           |
| 09.CK.30 | 02.03.08 | record classify   | duplicate in Bronze                           |

- **task 1 - data profiling** - profile both datasets: nominate and justify the critical data elements

**task 1 checks**

| id       | check                                         |
| -------- | --------------------------------------------- |
| 09.CK.01 | record/distinct counts                        |
| 09.CK.02 | duplicate transaction ids                     |
| 09.CK.03 | per-field null percentage                     |
| 09.CK.04 | min/max transaction and posting dates         |
| 09.CK.05 | distinct and invalid fx codes and txn types   |
| 09.CK.06 | negative/zero amounts                         |
| 09.CK.07 | branch/product/source-file distributions      |
| 09.CK.08 | late-arriving records                         |
| 09.CK.09 | posting date preceding transaction date       |
| 09.CK.10 | FX rows breaching amt exchange-rate tolerance |

01. **09.CK.10** tolerance check: `local_currency_amount != transaction_amount * exchange_rate`.

- **task 2 - source-to-bronze reconciliation** 
  - level 1 batch totals
  - level 2 dimensional reconciliation with the largest-variance combinations identified
  - level 3 record-level classification

**task 2 - level 1 batch totals**

| id       | batch total        |
| -------- | ------------------ |
| 09.CK.11 | record count       |
| 09.CK.12 | distinct count     |
| 09.CK.13 | debit sum          |
| 09.CK.14 | credit sum         |
| 09.CK.15 | net amount         |
| 09.CK.16 | local-currency sum |

**task 2 - level 2 dimensional reconciliation dimensions** 

reconciled across every combination of these six dimensions, with the largest-variance combinations identified and reported.

| id       | dimension        |
| -------- | ---------------- |
| 09.CK.17 | transaction date |
| 09.CK.18 | branch           |
| 09.CK.19 | currency         |
| 09.CK.20 | product          |
| 09.CK.21 | transaction type |
| 09.CK.22 | source file      |

**task 2 - level 3 record-level classification**

| id       | record class          |
| -------- | --------------------- |
| 09.CK.23 | exact match           |
| 09.CK.24 | missing in Bronze     |
| 09.CK.25 | unexpected in Bronze  |
| 09.CK.26 | amount mismatch       |
| 09.CK.27 | currency mismatch     |
| 09.CK.28 | posting-date mismatch |
| 09.CK.29 | duplicate in source   |
| 09.CK.30 | duplicate in Bronze   |

- **task 3 - root cause** - explain the hypothesis:

  missing-record population concentrated in near-midnight source files where UTC source timestamps meet Singapore business-date ingestion

  - evidence the hypothesis with queries
  - quantify financial impact
  - identify affected branches/products/currencies/accounting dates
  - recommend remediation plus permanent preventive controls

- **expected deliverables** - notebook, profiling summary, reconciliation results, exception dataset, root-cause analysis, DQ-control recommendations, and a short reconciliation dashboard or mock-up
- **assessment context** - the published results must state the assignment scenario, tasks, and scale framing they answer, so a reader is not handed measurements without the question they respond to - see [assessment context documentation](#assessment-context-documentation)

**prerequisite scope** 

already-closed infrastructure this assessment consumes, not re-decided here

- **postgres db** ([02](../features/02-dev-env-setup-postgresql-db.md)) running with `src_transaction_daily` created, via `scripts/01-dev-env-setup.sh`
- **spark + jupyter containers** ([03](../features/03-dev-env-setup-spark-container.md)) up, so the notebook can reach both postgres over JDBC and the Spark master
- **seed data** ([04](../features/04-seed-mock-data.md)) loaded through `scripts/03-mock-data-seed.sh`, with `data/mock/issue-log.csv` as the ground-truth catalog of every injected Assessment 1 issue
- **reconciliation control tables** ([05](../features/05-ai-closed-loop-validation.md)) `reconciliation.rc_*` present, with `scripts/04-closed-loop-run.sh` already proving the batch-level check for this assessment
- **deliverable paths** ([08](../features/08-assessment-deliverables-conventions.md)) scaffolded under `results/assessment-1/`, indexed by [results/assessment-1/README.md](../../results/assessment-1/README.md) - that manifest, not this tracker, is the single list of what must be produced
- **notebook path** ([07](../features/07-jupyter-notebook-workspace-setup.md)) `notebooks/assessment1_profiling.ipynb`
- **dashboard template** ([06](../features/06-powerbi-dashboard-setup.md)) `powerbi/reconciliation-dashboard-template/`, synced with `scripts/05-powerbi-sync.sh`

**out of scope**

- does not seed, extend, or regenerate mock data - if a check has nothing to find, that is a [04](../features/04-seed-mock-data.md) defect raised there, not a data edit made here
- does not change the `reconciliation.rc_*` schema; new checks are new rows, not new columns
- does not attempt the assignment's literal 25M-row/day volumes - measured numbers come from the seeded volume budget and every write-up states that scale delta explicitly
- does not cover Assessment 2 or 3 datasets, deliverables, or notebooks

**closure**

Every deliverable listed in [results/assessment-1/README.md](../../results/assessment-1/README.md) carries `status: final`, the assessment context page exists and is referenced from every deliverable, each finding is traceable to a `reconciliation.rc_batch_control.batch_id` or a notebook section, `scripts/07-deliverables-scaffold.sh --check` passes, and the published site shows the Assessment 1 pages.

## References

- **assignment design doc** `docs/design/assignment.md` (Assessment 1 scenario, Tasks 1-3, Expected Deliverables)
- **milestones** `docs/milestones.md` (`assessment 1` scope and closure statement)
- **postgresql db tracker** `docs/features/02-dev-env-setup-postgresql-db.md`
- **spark container tracker** `docs/features/03-dev-env-setup-spark-container.md`
- **seed mock data tracker** `docs/features/04-seed-mock-data.md` (assessment 1 injected issue catalog)
- **ai closed-loop validation tracker** `docs/features/05-ai-closed-loop-validation.md` (`rc_*` schema)
- **powerbi dashboard setup tracker** `docs/features/06-powerbi-dashboard-setup.md`
- **jupyter notebook workspace tracker** `docs/features/07-jupyter-notebook-workspace-setup.md`
- **deliverables conventions tracker** `docs/features/08-assessment-deliverables-conventions.md`
- **deliverable manifest** `results/assessment-1/README.md`
- **issue log** `data/mock/issue-log.csv` gitignored, regenerated every seed run

## Design

### prerequisites

Ordered, rerunnable setup steps that must pass before any analysis task starts. Each is an existing script from a closed feature; this tracker only fixes the order and the evidence each step must leave behind.

| id       | step                        | command                                       | evidence         |
| -------- | --------------------------- | --------------------------------------------- | ---------------- |
| 09.PR.01 | host prerequisites          | `scripts/00-prereq-check.sh`                  | `[PASS]` log     |
| 09.PR.02 | postgres + tables           | `scripts/01-dev-env-setup.sh`                 | 9 tables exist   |
| 09.PR.03 | spark + jupyter containers  | `docker compose` full profile                 | `docker ps`      |
| 09.PR.04 | seed mock data              | `scripts/03-mock-data-seed.sh`                | `issue-log.csv`  |
| 09.PR.05 | seed validation             | `scripts/04-mock-data-validate.sh`            | row/issue counts |
| 09.PR.06 | notebook connectivity       | `scripts/06-notebook-validate.sh`             | template passes  |
| 09.PR.07 | control-table smoke run     | `scripts/04-closed-loop-run.sh`               | one `batch_id`   |
| 09.PR.08 | deliverable scaffold check  | `scripts/07-deliverables-scaffold.sh --check` | current          |

01. **09.PR.02** covers only DDL; a fresh clone must still run step 04 before any profiling query returns rows.
02. **09.PR.03** uses `docker/docker-compose.full.yml`; the master, both workers, and the Jupyter container must all be `Up` before the notebook is executed.

### assessment task to deliverable map

One row per assignment task, naming the deliverable file it lands in and the executable artifact it is derived from. This is the traceability contract every write-up's **Sources** section must satisfy.

| id       | assignment task              | deliverable file [01]     | artifact           |
| -------- | ---------------------------- | ------------------------- | ------------------ |
| 09.DM.01 | task 1 profiling             | `profiling-summary`       | notebook           |
| 09.DM.02 | task 1 critical data elements | `profiling-summary`      | notebook           |
| 09.DM.03 | task 2 level 1 batch          | `reconciliation-results`  | `rc_*` + notebook  |
| 09.DM.04 | task 2 level 2 dimensional    | `reconciliation-results`  | notebook           |
| 09.DM.05 | task 2 level 3 record-level   | `exception-dataset`       | notebook           |
| 09.DM.06 | task 3 root cause             | `root-cause-analysis`     | notebook           |
| 09.DM.07 | task 3 remediation            | `root-cause-analysis`     | narrative          |
| 09.DM.08 | task 3 permanent controls     | `dq-recommendations`      | narrative          |
| 09.DM.09 | dashboard mock-up             | manifest reference row    | `.pbip` template   |
| 09.DM.10 | notebook                      | manifest reference row    | notebook           |
| 09.DM.11 | scenario and task context     | `overview`                | assignment doc     |
| 09.DM.12 | ground-truth cross-check      | `audit`                   | notebook + issue-log |

01. file names are `results/assessment-1/assessment-1-<slug>.md` per [08](../features/08-assessment-deliverables-conventions.md#directory-and-naming-convention).
02. **09.DM.11** is the authored context page introduced by this tracker, outside feature 08's generated taxonomy - see [assessment context documentation](#assessment-context-documentation).
03. **09.DM.12** audits every other row's measured counts against `data/mock/issue-log.csv`, organized by assignment task/subtask rather than by deliverable, per user direction during 09.04 review.

### workflow cycle

Each implementation task runs the same five-stage loop, so every claim in a markdown deliverable is reproducible from a seeded database rather than hand-typed. A task is only complete when all five stages have run in order.

```
seed db  ->  notebook / spark  ->  rc_* control tables  ->  results markdown  ->  validation run
   ^                                                                                     |
   |_____________________________ rerun on any change ___________________________________|
```

| id       | stage             | action                                                   |
| -------- | ----------------- | -------------------------------------------------------- |
| 09.WS.01 | seed db           | confirm seeded state, capture the seed run's `issue-log`  |
| 09.WS.02 | notebook / spark  | add or update the task's cells, execute top to bottom     |
| 09.WS.03 | control tables    | write measured results to `reconciliation.rc_*`           |
| 09.WS.04 | results markdown  | update the mapped deliverable and its **Sources** section |
| 09.WS.05 | validation run    | rerun the scripted checks and record `[PASS]`/`[FAIL]`    |

01. **09.WS.03** applies to measurable reconciliation output only; profiling statistics and narrative findings stop at **09.WS.02** and are cited by notebook cell rather than `batch_id`.
02. **09.WS.04** never restates a number the notebook did not produce in the same run - a changed measurement means the deliverable is edited in the same cycle, not the next one.
03. the Power BI substitute for **09.WS.04** is a `.pbip` edit plus `scripts/05-powerbi-sync.sh`. a dashboard change is treated as a deliverable change and re-enters the cycle at **09.WS.05**.

### assessment context documentation

The deliverables scaffolded by [08](../features/08-assessment-deliverables-conventions.md) present measurements without the assignment context that motivated them - a reader landing on the profiling summary sees statistics but not the scenario, the task that asked for them, or the scale they were measured at. This tracker closes that gap explicitly rather than leaving the context implicit in this internal document.

- **overview page** - `results/assessment-1/assessment-1-overview.md` restates the Assessment 1 scenario, the source and Bronze table shapes, Tasks 1-3, and the expected deliverable list in the assignment's own framing, so the published results stand on their own without the reader holding the assignment doc open beside them
- **scale statement** - one paragraph naming the assignment's production volumes and this demo's seeded volume budget, so every number published elsewhere is read against the right scale rather than mistaken for a production figure
- **per-deliverable context** - each deliverable opens with a single line, directly under its `status:` marker, naming the assignment task it answers and linking the overview page
- **linkage** - the overview is authored content outside feature 08's generated taxonomy, so it is linked from `results/index.md` and from each deliverable rather than from the generated manifest; promoting it to a taxonomy row is a change raised in [08](../features/08-assessment-deliverables-conventions.md), not made here
- **no restatement of findings** - the overview carries assignment context only; measured results stay in their own deliverables so there is one place a number can change

### profiling - task 1

- **checks** - one row per profiling statistic named in Task 1, with its SQL/PySpark expression and the table(s) it runs against
- **critical data elements** - the nominated CDE list with the justification for each, stated as a table rather than prose so the reasoning is auditable per column
- **presentation** - how each statistic is rendered in the notebook (single-row summary vs. distribution table) and which of those carry through into the profiling summary write-up
- **blind-analyst framing [01]** - the notebook and every deliverable except `audit` reads as an analyst inspecting the data with no knowledge of how it was generated or which defects were intentionally injected; findings state what this level of analysis can deduce and the open question it raises for the next level, never a seed-generator issue-type name or an explanation of how a defect was mechanically produced
- **expected findings** - the assessment 1 issue counts from [04](../features/04-seed-mock-data.md#injected-issue-catalog--assessment-1) that each check must reproduce, verified only in `assessment-1-audit.md` (09.DM.12) - the one deliverable allowed to know the ground truth

01. added during 09.04 review - see [08](../features/08-assessment-deliverables-conventions.md#deliverable-type-taxonomy)'s `audit` taxonomy row for where the ground-truth-aware content belongs instead.

### reconciliation - task 2

- **level 1 batch** - the six batch totals, their tolerance, and the mapping onto `rc_reconciliation_results` rows already established by [05](../features/05-ai-closed-loop-validation.md)
- **level 2 dimensional** - the six reconciliation dimensions, the variance measure used to rank combinations, and the cut-off for what counts as a reported largest mismatch
- **level 3 record-level** - the business key used for the source-to-Bronze join, the classification decision order for the eight record classes, and the handling of rows matching more than one class
- **scale note** - the standard wording stating measured values come from the seeded volume budget, not the assignment's 25M-row/day production scale

### exception dataset

- **schema** - at minimum `transaction_id`, `issue_type`, `source_value`, `bronze_value`, `variance`, `batch_id`, per the assignment's stated minimum
- **issue_type vocabulary** - the closed set of values, aligned to the level 3 record classes and to `issue-log.csv`'s own `issue_type` spelling so ground-truth comparison is a direct join
- **materialisation** - whether the dataset is emitted as a table, a notebook output, or an embedded markdown extract in the deliverable, and where the full row set lives if the write-up shows only a sample
- **ground-truth check** - the comparison against `issue-log.csv` proving detected issues match injected ones

### root-cause investigation - task 3

- **hypothesis** - the UTC vs. Singapore-business-date boundary explanation, framed as a hypothesis until the evidence queries confirm it
- **evidence** - the queries demonstrating the missing population concentrates in near-midnight source files
- **financial impact** - the quantified local-currency value of the missing records
- **affected dimensions** - the branches, products, currencies, and accounting dates involved
- **remediation** - the corrective action for the affected batches
- **note** - the assignment's stated symptom counts are production-scale figures; findings are reported against seeded counts with the production figures cited as the scenario framing

### dq-control recommendations

- **preventive controls** - the permanent controls preventing recurrence of the root cause
- **detective controls** - the ongoing reconciliation and profiling checks, mapped onto the `rc_*` control-table pattern so a recommendation is expressed as something the existing framework can run
- **prioritisation** - severity/effort ranking so the list reads as a recommendation, not an inventory

### dashboard mock-up

The dashboard deliverable is satisfied by the existing `.pbip` template owned by [06](../features/06-powerbi-dashboard-setup.md), extended with an Assessment 1 view, not by a new Power BI project. Edits are made in the tracked template, synced to the Windows-side working copy with `scripts/05-powerbi-sync.sh`, opened and saved in Power BI Desktop by the user, then synced back. The deliverable manifest's dashboard row remains a reference to that path.

**data source** - the template's three live `reconciliation.rc_*` tables only cover level 1 (`rc_reconciliation_results.dimension IN ('row_count','amount')`, per [reconciliation design - task 2](#reconciliation-design--task-2)); level 2 dimensional variance and level 3 exception classes exist only in the notebook and the markdown deliverables, no live table. Rather than a staging step, two new tables query `src_transaction_daily`/`bronze.transaction_daily` directly - postgres-backed exactly like `rc_reconciliation_results.tmdl` already is, whose M query already embeds an arbitrary `SELECT` in `PostgreSQL.Database(...)`'s `Query=` parameter. No export script, no CSV, no intermediate table: each refresh in Desktop re-runs the query live.

| id | table                          | columns                                          |
| -- | ------------------------------- | --------------------------------------------------- |
| 01 | assessment1-dimension-variance   | `dimension, group_value, counts/amounts` [01]         |
| 02 | assessment1-exception-summary    | `issue_type, row_count` [02]                          |

01. **01** `src_count, bronze_count, count_variance, src_amount, bronze_amount, amount_variance` - one row per (`dimension`, `group_value`) across all six level 2 dimensions, live from source/Bronze, not tied to a `batch_id` snapshot.
02. **02** one row per level 3 record class, including the two duplicate classes - same live-query reasoning.

See [Implement step 8](#8-dashboard-mock-up) for the two tables' full M-query SQL.

**pages/visuals** - a new report page, "Assessment 1 - Reconciliation", alongside the template's existing shared page:

| id | visual                      | type/fields    | source table                   |
| -- | --------------------------- | -------------- | ------------------------------- |
| 01 | reconciliation summary [01] | 3 cards        | `rc_batch_control`               |
| 02 | variance by dimension       | bar chart [02] | `assessment1-dimension-variance` |
| 03 | exception breakdown         | table [03]     | `assessment1-exception-summary`  |
| 04 | total exceptions            | card [04]      | `assessment1-exception-summary`  |

01. **01** the template's existing batch-count / batches-by-status / latest-variance-% cards, reused unchanged.
02. **02** `group_value` (axis) x `amount_variance` (value), sliced by `dimension`.
03. **03** `issue_type, row_count`.
04. **04** sum of `row_count` where `issue_type <> 'exact_match'`.

**safe-edit boundary** - per the powerbi-dashboard-workspace skill: the two new tables (id/columns/M-query) are TMDL, safe to author directly. Visuals 02-04 bind to columns that don't exist in the project *yet*, and all four sit on a brand new page - both are the explicitly higher-risk category that skill reserves for a human in Desktop, not an agent edit. Only the data layer is implemented directly; the page and its visuals are a checklist the user builds.

**user action** - the Desktop open/save round trip (unchanged), plus building the new page's three visuals from the checklist above once the two new tables load with real data.

### notebook organisation

`notebooks/assessment1_profiling.ipynb` is the single executable artifact for this assessment, sectioned in assignment order - connectivity, task 1 profiling, task 2 levels 1-3, task 3 root cause - so a deliverable's **Sources** reference can name a section rather than a cell index that shifts on edit. Output commit policy follows [07](../features/07-jupyter-notebook-workspace-setup.md); the notebook must execute cleanly top to bottom against a freshly seeded database before 09.10 closes.

### idempotency / rerun-safety

- **notebook** - re-executable end to end against a freshly seeded database with no manual cell ordering; any writes it makes are keyed by `batch_id` so a rerun appends a new batch rather than mutating a prior one.
- **control tables** - reruns insert a new `rc_batch_control` row; existing batches are never updated in place, preserving the evidence a published deliverable already cites.
- **deliverable markdown** - authored content, never regenerated by a script; `07-deliverables-scaffold.sh` remains verify-or-create and only the derived `README.md` manifest is rewritten.
- **seed data** - regenerated only by `scripts/03-mock-data-seed.sh`, which is deterministic under the fixed `MOCK_DATA_SEED`; this tracker never edits seeded rows directly.

### environment & secrets

No new variables and no new secrets. The work reuses the existing postgres connection settings, `LOGS_DIR`, `TIMEZONE`, and `TIMESTAMP_FORMAT` from `.env`, and the Power BI sync paths from [06](../features/06-powerbi-dashboard-setup.md#environment--secrets). Credentials are never written into a notebook cell, a deliverable markdown file, or the published site.

### workflow validation runner

Assessment 1 introduces no new runner by default; validation composes the existing scripts in [prerequisites](#prerequisites) plus `scripts/06-notebook-validate.sh` for headless notebook execution and `scripts/07-deliverables-scaffold.sh --check` for deliverable completeness. If a per-assessment orchestration step proves necessary, it is added as the next free script number and logged under `.dev/logs/` with `<ts>-09.<nn>-<name>.log` naming, printing one `[PASS]`/`[FAIL]` line per stage of the [workflow cycle](#workflow-cycle).

### publishing

Once every deliverable is promoted to `status: final`, `scripts/07-deliverables-scaffold.sh` regenerates the Assessment 1 manifest with the updated statuses, `scripts/08-assessment-site.sh build` validates the strict MkDocs build, and `scripts/08-assessment-site.sh deploy` publishes to `gh-pages` from a clean, reviewed worktree. The overview page must be reachable from the published navigation before deploy, otherwise the context gap simply reappears on the site. Deployment is never run with uncommitted assessment evidence in the tree.

## Test cases

_test strategy_

Findings are validated at three layers so a measurement is never trusted on the strength of the write-up alone:

1. **script self-report** - `[PASS]`/`[FAIL]` lines and timestamped logs from the prerequisite and validation scripts show each stage ran.
2. **ground-truth comparison** - detected issues are joined against `data/mock/issue-log.csv`, the injected catalog from [04](../features/04-seed-mock-data.md), rather than eyeballed.
3. **content inspection** - deliverable markdown is checked for required headings, `status:` markers, context and source references, and table shape independently of the notebook that produced the numbers.

_test cases_

| id       | task  | layer        | check                                       |
| -------- | ----- | ------------ | ------------------------------------------- |
| 09.TC.01 | 09.02 | script       | all prerequisite steps report `[PASS]`      |
| 09.TC.02 | 09.02 | ground-truth | seeded issue counts match the issue log     |
| 09.TC.03 | 09.03 | content      | overview states scenario, tasks, and scale  |
| 09.TC.04 | 09.03 | content      | every deliverable links the overview page   |
| 09.TC.05 | 09.04 | content      | every task 1 statistic is in the write-up   |
| 09.TC.06 | 09.04 | ground-truth | profiling counts match injected issue rows  |
| 09.TC.07 | 09.05 | script       | level 1 totals land in `rc_*` for one batch |
| 09.TC.08 | 09.05 | content      | level 2 names the largest-variance combos   |
| 09.TC.09 | 09.06 | content      | exception dataset carries the six columns   |
| 09.TC.10 | 09.06 | ground-truth | exception rows reconcile to the issue log   |
| 09.TC.11 | 09.07 | content      | root cause states evidence and impact       |
| 09.TC.12 | 09.08 | content      | each control maps to a runnable check       |
| 09.TC.13 | 09.09 | direct-fs    | dashboard round trip leaves no diff         |
| 09.TC.14 | 09.10 | script       | notebook executes clean top to bottom       |
| 09.TC.15 | 09.11 | content      | every deliverable reads `status: final`     |
| 09.TC.16 | 09.12 | build        | strict MkDocs build succeeds                |
| 09.TC.17 | 09.12 | deployment   | published site shows assessment 1 pages     |

**tools**

```bash
cd /home/taylor-hickem/repos/de-financial-accounting-demo
./scripts/00-prereq-check.sh
./scripts/03-mock-data-seed.sh
./scripts/04-mock-data-validate.sh
./scripts/04-closed-loop-run.sh
./scripts/06-notebook-validate.sh
./scripts/07-deliverables-scaffold.sh --check
./scripts/08-assessment-site.sh build
grep -R --line-number '^status: \(draft\|final\)$' results/assessment-1
grep -RL 'assessment-1-overview.md' results/assessment-1/assessment-1-*.md
awk '/^\|/ && length($0) >= 115 { print FILENAME ":" FNR ": row too long"; bad = 1 } END { exit bad }' results/assessment-1/*.md
```

## Edit locations

| id       | path                                                        | change                        |
| -------- | ----------------------------------------------------------- | ----------------------------- |
| 09.EL.01 | `notebooks/assessment1_profiling.ipynb`                     | full analysis notebook        |
| 09.EL.02 | `results/assessment-1/assessment-1-profiling-summary.md`     | task 1 write-up               |
| 09.EL.03 | `results/assessment-1/assessment-1-reconciliation-results.md` | task 2 levels 1-2 write-up  |
| 09.EL.04 | `results/assessment-1/assessment-1-exception-dataset.md`     | task 2 level 3 write-up       |
| 09.EL.05 | `results/assessment-1/assessment-1-root-cause-analysis.md`   | task 3 write-up               |
| 09.EL.06 | `results/assessment-1/assessment-1-dq-recommendations.md`    | control recommendations       |
| 09.EL.07 | `results/assessment-1/README.md`                             | regenerated manifest          |
| 09.EL.08 | `powerbi/reconciliation-dashboard-template/`                 | assessment 1 dashboard view [08] |
| 09.EL.09 | `src/sparksql/`                                              | reusable query files          |
| 09.EL.10 | `docs/milestones.md`                                         | milestone 09 status/closure   |
| 09.EL.11 | `results/assessment-1/assessment-1-overview.md`              | assessment scope context      |
| 09.EL.12 | `results/index.md`                                           | link to the overview page     |
| 09.EL.13 | `mkdocs.yml`                                                 | overview in site nav [04]     |
| 09.EL.14 | `scripts/09-gh-pages-publish.sh`                             | authenticated gh-pages deploy [05] |
| 09.EL.15 | `.env`, `.env.sample`                                        | `GITHUB_PAT_FILE` param [05]   |
| 09.EL.16 | `scripts/07-deliverables-scaffold.sh`                        | status convention amendment [06] |
| 09.EL.17 | `docs/features/08-assessment-deliverables-conventions.md`    | status convention amendment [06] |
| 09.EL.18 | `results/assessment-1/assessment-1-audit.md`                 | ground-truth audit [07]       |

01. **09.EL.07** is generated by `scripts/07-deliverables-scaffold.sh`; never hand-edited.
02. **09.EL.09** is optional - used only where a query is worth extracting from the notebook for reuse, following the existing `src/pyspark/` naming pattern.
03. **09.EL.11** is authored content outside feature 08's generated taxonomy, so the scaffold neither creates nor validates it; it is created by hand in 09.03.
04. **09.EL.13** is only required if the strict build cannot reach the overview through `09.EL.12`'s link alone.
05. **09.EL.14/15** added for [09.IS.01](#validate) - the `gh-pages` push had no credentials available in this environment.
06. **09.EL.16/17** added for [09.IS.02](#validate) - moves deliverable `status` off the page and into the manifest, adding `open`.
07. **09.EL.18** the ground-truth checks moved out of `assessment-1-profiling-summary.md` into their own file, per user direction during 09.04 review - not a bug fix, a requested reorganization.
08. **09.EL.08** gains two new postgres-backed TMDL tables under `.SemanticModel/definition/tables/`, registered in `model.tmdl`, and (human-built, see [dashboard mock-up](#dashboard-mock-up)) one new report page under `.Report/definition/pages/`.

No `.env`, `.env.sample`, schema JSON, DDL, or seed-script change is expected. A required change to any of those is a defect in the owning feature and is raised there rather than patched from this tracker.

## Implement

Implementation order is prerequisites -> assessment context -> profiling -> reconciliation -> exceptions -> root cause -> recommendations -> dashboard -> notebook rerun -> review -> publish. Each step runs the full [workflow cycle](#workflow-cycle) before the next begins.

### 1. Prerequisites and seed data readiness

edit locations: none

_closed 09.02_ - ran every [prerequisites](#prerequisites) step in order against a clean session:

| id       | evidence observed                                                       |
| -------- | ------------------------------------------------------------------------ |
| 09.PR.01 | `[PASS]` docker + python3.14 + venv module                                |
| 09.PR.02 | `[PASS]` venv, DDL generated/applied, postgres up, spark 2/2 workers      |
| 09.PR.03 | `[PASS]` `docker ps` shows postgres/spark-master/2 workers/jupyter `Up`   |
| 09.PR.04 | `[PASS]` 9 tables recreated; `src_transaction_daily`=2010, `bronze.transaction_daily`=1993 rows |
| 09.PR.05 | `[PASS]` all row-count and ground-truth checks vs. `issue-log.csv` (300 rows/34 categories) |
| 09.PR.06 | `[PASS]` `00_template_connectivity_check.ipynb` executed clean, summary marker agrees |
| 09.PR.07 | `[PASS]` `reconciliation.rc_batch_control.batch_id=7`, status=WARNING [01]           |
| 09.PR.08 | `[PASS]` `07-deliverables-scaffold.sh --check` current for all three assessments |

01. **09.PR.07** WARNING is expected here - it is the batch-level symptom this assessment investigates (injected source-to-Bronze variance), not a script failure.

Baseline for later ground-truth comparison: `src_transaction_daily`=2010 rows / 2000 distinct `transaction_id`; `bronze.transaction_daily`=1993 rows / 1975 distinct `transaction_id`.

### 2. Assessment scope and context write-up

edit locations: `09.EL.11, 09.EL.12, 09.EL.13`

_closed 09.03_ - authored `results/assessment-1/assessment-1-overview.md`: scenario, both table shapes, Tasks 1-3, expected deliverables, and the scale statement (25M-rows/day production vs. this seed run's 2,010/1,993-row budget). Linked from `results/index.md`. `mkdocs.yml` nav (`09.EL.13`) was **not** touched - `./scripts/08-assessment-site.sh build` passed strictly with the overview reachable through the `results/index.md` link alone, per the design footnote.

### 3. Task 1 - data profiling

edit locations: `09.EL.01, 09.EL.02`

_closed 09.04_ - all ten task 1 checks (`09.CK.01`-`09.CK.10`, task refs `01.01`-`01.10`) plus critical-data-element nomination.

Added a "Task 1 - Data Profiling" section to `notebooks/assessment1_profiling.ipynb`: a Spark session against `spark://spark-master:7077`, JDBC reads of `src_transaction_daily` and `bronze.transaction_daily`, one function per check run against both tables, and a critical-data-elements markdown table. Executed headlessly via `docker exec jupyter-notebook jupyter nbconvert --to notebook --execute` per the jupyter-notebook-workspace skill (no dedicated `09.*-notebook-validate.sh` script yet - deferred to 09.10 per [workflow validation runner](#workflow-validation-runner)); confirmed the executed output before copying it back over the tracked notebook (never `--inplace`). Every check reproduced its expected count from `data/mock/issue-log.csv` exactly; two checks surfaced real cross-check findings worth carrying into later tasks: `09.CK.10`'s FX-tolerance breach count (27 on source) is 15 genuine `fx_mismatch` rows plus 12 rows that also carry the unrelated `negative_or_zero_amount` mutation (confirmed by exact `transaction_id` overlap - flipping the amount's sign without recomputing `local_currency_amount` mechanically breaches tolerance too), and `09.CK.07`'s source-file distribution shows the five `*_MIDNIGHT.dat` files (2-7 rows each, the `utc_sgt_midnight_boundary` issue) entirely absent from Bronze's distribution - visible evidence for task 3's root cause, surfaced here without further interpretation.

Wrote `results/assessment-1/assessment-1-profiling-summary.md` citing that notebook section, the overview page, a findings table for all ten checks, and the critical-data-elements table. Per user direction, ground-truth cross-checking every count against `issue-log.csv` does not belong in a deliverable write-up - moved to its own file, `results/assessment-1/assessment-1-audit.md` (09.EL.18, new taxonomy row `audit` added to [08](../features/08-assessment-deliverables-conventions.md#deliverable-type-taxonomy)), organized by assignment task/subtask (`01.01`-`01.10`) rather than by deliverable, so one task's full evidence trail reads in one place.

### 4. Task 2 - source-to-bronze reconciliation

edit locations: `09.EL.01, 09.EL.03`

_closed 09.05_ - level 1 batch totals (`09.CK.11`-`09.CK.16`, task refs `02.01.01`-`02.01.06`) and level 2 dimensional reconciliation (`09.CK.17`-`09.CK.22`, task refs `02.02.01`-`02.02.06`).

Added a "Task 2 - Source-to-Bronze Reconciliation" section to `notebooks/assessment1_profiling.ipynb`, following task 1's blind-analyst framing throughout. Level 1: all six batch totals computed via PySpark; `record count` and `amount` (debit sum + credit sum, the only two dimensions `reconciliation.rc_reconciliation_results`'s closed enum supports - widening it is out of scope) written into a fresh `batch_id=9` via `reconciliation.rc_batch_control`/`rc_reconciliation_results`; the other four totals reported in the notebook/deliverable only. Every one of the six totals disagrees beyond `PASS` (`net amount` off by ~16%), directly evidencing the batch-level symptom this assessment investigates. Level 2: each of the six dimensions grouped and compared independently, top-3 largest-variance values reported per dimension; `ingestion_file`'s finding answers task 1's own open question - the low-volume `*_MIDNIGHT.dat` files carry a disproportionate share of the missing-record variance. Executed headlessly, confirmed no cell error, copied back over the tracked notebook. Wrote `results/assessment-1/assessment-1-reconciliation-results.md` citing that section, `batch_id=9`, and the overview/audit pages.

### 5. Exception dataset

edit locations: `09.EL.01, 09.EL.04`

_closed 09.06_ - level 3 record-level classification (`09.CK.23`-`09.CK.30`, task refs `02.03.01`-`02.03.08`).

Added the "Level 3 - Record-Level Classification" section: business key `transaction_id`, an explicit decision order (duplicate in source -> duplicate in Bronze -> missing in Bronze -> unexpected in Bronze -> amount mismatch -> currency mismatch -> posting-date mismatch -> exact match) stated in the notebook and the deliverable, plus the one caveat that order creates (a Bronze-duplicated id excluded from the join classifies as "missing" even though Bronze holds a row for it - stated plainly, not resolved here). Result: 1940 exact match, 33 missing in Bronze, 0 unexpected, 9 amount mismatch, 4 currency mismatch, 4 posting-date mismatch, 20/10 duplicate-in-source rows/ids, 36/18 duplicate-in-Bronze rows/ids - 106 exception rows total, materialized in full in the notebook's cell output and sampled by class in the deliverable. A real bug surfaced and was fixed before this run: the first pass showed identical source/bronze values for `amount_mismatch` rows because the mismatch was in `transaction_amount`, not `local_currency_amount`, but only the latter was displayed - fixed to report whichever field actually differs. Wrote `results/assessment-1/assessment-1-exception-dataset.md` with the classification method, the eight-class table, and a representative sample.

### 6. Task 3 - root-cause investigation

edit locations: `09.EL.01, 09.EL.05`

_closed 09.07_ - two hypotheses raised by task 2's open questions, each stated, evidenced, and confirmed or left open on its own terms.

Added the "Task 3 - Root-Cause Investigation" section: **hypothesis 1** (near-UTC-midnight extraction timing, from `source_extract_ts`'s own schema documentation) - a crosstab of a `[23:45,23:59]` UTC flag against Bronze presence shows a perfect split, all 20 near-midnight rows absent from Bronze and no other row in that window; confirmed. **hypothesis 2** (Bronze-only duplicates trace to a reprocessing batch) - Bronze's own `batch_id` column shows all 8 unexplained duplicate ids carry a plain daily batch plus a `-R`-suffixed batch, recurring on 4 of 5 business dates; confirmed. The financial-impact bridge (source total - 25 genuinely-missing rows + 8 reprocessing-batch extra rows) closes task 2's entire level 1 local-currency variance to a `0.00` residual - no third mechanism needed. 5 further "missing in Bronze" rows fit neither hypothesis and are stated as an open, unresolved residual rather than forced under one.

Wrote `results/assessment-1/assessment-1-root-cause-analysis.md` with both hypotheses, the evidence tables, the financial bridge, affected dimensions, the unexplained residual, remediation, and permanent preventive controls. Updated `assessment-1-audit.md`'s Task 3 section confirming both populations and the residual match the injected catalog's `utc_sgt_midnight_boundary` (20), `duplicate_in_bronze_reprocessed` (8), and `missing_in_bronze_unrelated` (5) tags exactly - the ground-truth knowledge stays contained there, never in the deliverable itself.

### 7. DQ-control recommendations

edit locations: `09.EL.06`

_boilerplate - expand during 09.08_

Write the preventive and detective control recommendations, each expressed as something the `rc_*` framework can execute, prioritised by severity and effort.

### 8. Dashboard mock-up

edit locations: `09.EL.08`

_boilerplate - expand during 09.09_

Per [dashboard mock-up](#dashboard-mock-up)'s safe-edit boundary: the two TMDL tables (id/columns/M-query) are authored directly; the new page and its three visuals are a checklist the user builds in Desktop. No export script, no CSV, no `batch_id` staging column - both tables query `src_transaction_daily`/`bronze.transaction_daily` live, the same way `rc_reconciliation_results.tmdl` already queries `reconciliation.rc_reconciliation_results` live: an arbitrary `SELECT` embedded in `PostgreSQL.Database(...)`'s `Query=` parameter. Both SQL strings below were run directly against postgres and their row counts/values checked against the published deliverables before being written here.

**1. add the two TMDL tables** under `.SemanticModel/definition/tables/`, modeled directly on `rc_reconciliation_results.tmdl`'s postgres-partition shape (verified sibling, not invented syntax) - fresh `lineageTag` GUIDs per column, CRLF line endings:

`assessment1-dimension-variance.tmdl` - one row per (`dimension`, `group_value`) across all six level 2 dimensions, verified against postgres to return 65 rows (5+20+11+4+5+20):

```
table assessment1-dimension-variance
	lineageTag: 44d195ec-736a-486b-807b-8110a7b2d3cb

	column dimension
		dataType: string
		lineageTag: 4b5ae694-4aca-404c-9ba2-f659dce3197c
		summarizeBy: none
		sourceColumn: dimension

		annotation SummarizationSetBy = Automatic

	column group_value
		dataType: string
		lineageTag: 7370e5b3-5234-46c7-ac2c-8fe20cafff2e
		summarizeBy: none
		sourceColumn: group_value

		annotation SummarizationSetBy = Automatic

	column src_count
		dataType: int64
		formatString: 0
		lineageTag: c2ab1ca6-a543-4640-b524-75f75478e0bf
		summarizeBy: sum
		sourceColumn: src_count

		annotation SummarizationSetBy = Automatic

	column bronze_count
		dataType: int64
		formatString: 0
		lineageTag: 72517296-a0ca-4d22-91df-68c00505c02a
		summarizeBy: sum
		sourceColumn: bronze_count

		annotation SummarizationSetBy = Automatic

	column count_variance
		dataType: int64
		formatString: 0
		lineageTag: 1fcc2ed5-26b6-4701-8c2b-6a9e75a50f8c
		summarizeBy: sum
		sourceColumn: count_variance

		annotation SummarizationSetBy = Automatic

	column src_amount
		dataType: double
		lineageTag: f16e38af-862b-4d13-a49f-b946bdbf0cc7
		summarizeBy: sum
		sourceColumn: src_amount

		annotation SummarizationSetBy = Automatic
		annotation PBI_FormatHint = {"isGeneralNumber":true}

	column bronze_amount
		dataType: double
		lineageTag: 5b52beef-77d4-43d7-bc33-8abc829447b9
		summarizeBy: sum
		sourceColumn: bronze_amount

		annotation SummarizationSetBy = Automatic
		annotation PBI_FormatHint = {"isGeneralNumber":true}

	column amount_variance
		dataType: double
		lineageTag: c5f6b609-4884-4b00-bbd9-e58917c1e91c
		summarizeBy: sum
		sourceColumn: amount_variance

		annotation SummarizationSetBy = Automatic
		annotation PBI_FormatHint = {"isGeneralNumber":true}

	partition assessment1-dimension-variance = m
		mode: import
		source =
				let
				    Source = PostgreSQL.Database("localhost:5432", "as01_source_db", [Query="SELECT 'transaction_date' dimension, COALESCE(s.transaction_date::text, b.transaction_date::text) group_value, COALESCE(s.src_count,0) src_count, COALESCE(b.bronze_count,0) bronze_count, COALESCE(b.bronze_count,0)-COALESCE(s.src_count,0) count_variance, COALESCE(s.src_amount,0) src_amount, COALESCE(b.bronze_amount,0) bronze_amount, COALESCE(b.bronze_amount,0)-COALESCE(s.src_amount,0) amount_variance FROM (SELECT transaction_date, COUNT(*) src_count, SUM(local_currency_amount) src_amount FROM src_transaction_daily GROUP BY transaction_date) s FULL OUTER JOIN (SELECT transaction_date, COUNT(*) bronze_count, SUM(local_currency_amount) bronze_amount FROM bronze.transaction_daily GROUP BY transaction_date) b ON s.transaction_date = b.transaction_date UNION ALL SELECT 'branch_code' dimension, COALESCE(s.branch_code::text, b.branch_code::text) group_value, COALESCE(s.src_count,0) src_count, COALESCE(b.bronze_count,0) bronze_count, COALESCE(b.bronze_count,0)-COALESCE(s.src_count,0) count_variance, COALESCE(s.src_amount,0) src_amount, COALESCE(b.bronze_amount,0) bronze_amount, COALESCE(b.bronze_amount,0)-COALESCE(s.src_amount,0) amount_variance FROM (SELECT branch_code, COUNT(*) src_count, SUM(local_currency_amount) src_amount FROM src_transaction_daily GROUP BY branch_code) s FULL OUTER JOIN (SELECT branch_code, COUNT(*) bronze_count, SUM(local_currency_amount) bronze_amount FROM bronze.transaction_daily GROUP BY branch_code) b ON s.branch_code = b.branch_code UNION ALL SELECT 'currency_code' dimension, COALESCE(s.currency_code::text, b.currency_code::text) group_value, COALESCE(s.src_count,0) src_count, COALESCE(b.bronze_count,0) bronze_count, COALESCE(b.bronze_count,0)-COALESCE(s.src_count,0) count_variance, COALESCE(s.src_amount,0) src_amount, COALESCE(b.bronze_amount,0) bronze_amount, COALESCE(b.bronze_amount,0)-COALESCE(s.src_amount,0) amount_variance FROM (SELECT currency_code, COUNT(*) src_count, SUM(local_currency_amount) src_amount FROM src_transaction_daily GROUP BY currency_code) s FULL OUTER JOIN (SELECT currency_code, COUNT(*) bronze_count, SUM(local_currency_amount) bronze_amount FROM bronze.transaction_daily GROUP BY currency_code) b ON s.currency_code = b.currency_code UNION ALL SELECT 'product_code' dimension, COALESCE(s.product_code::text, b.product_code::text) group_value, COALESCE(s.src_count,0) src_count, COALESCE(b.bronze_count,0) bronze_count, COALESCE(b.bronze_count,0)-COALESCE(s.src_count,0) count_variance, COALESCE(s.src_amount,0) src_amount, COALESCE(b.bronze_amount,0) bronze_amount, COALESCE(b.bronze_amount,0)-COALESCE(s.src_amount,0) amount_variance FROM (SELECT product_code, COUNT(*) src_count, SUM(local_currency_amount) src_amount FROM src_transaction_daily GROUP BY product_code) s FULL OUTER JOIN (SELECT product_code, COUNT(*) bronze_count, SUM(local_currency_amount) bronze_amount FROM bronze.transaction_daily GROUP BY product_code) b ON s.product_code = b.product_code UNION ALL SELECT 'transaction_type' dimension, COALESCE(s.transaction_type::text, b.transaction_type::text) group_value, COALESCE(s.src_count,0) src_count, COALESCE(b.bronze_count,0) bronze_count, COALESCE(b.bronze_count,0)-COALESCE(s.src_count,0) count_variance, COALESCE(s.src_amount,0) src_amount, COALESCE(b.bronze_amount,0) bronze_amount, COALESCE(b.bronze_amount,0)-COALESCE(s.src_amount,0) amount_variance FROM (SELECT transaction_type, COUNT(*) src_count, SUM(local_currency_amount) src_amount FROM src_transaction_daily GROUP BY transaction_type) s FULL OUTER JOIN (SELECT transaction_type, COUNT(*) bronze_count, SUM(local_currency_amount) bronze_amount FROM bronze.transaction_daily GROUP BY transaction_type) b ON s.transaction_type = b.transaction_type UNION ALL SELECT 'ingestion_file' dimension, COALESCE(s.ingestion_file::text, b.ingestion_file::text) group_value, COALESCE(s.src_count,0) src_count, COALESCE(b.bronze_count,0) bronze_count, COALESCE(b.bronze_count,0)-COALESCE(s.src_count,0) count_variance, COALESCE(s.src_amount,0) src_amount, COALESCE(b.bronze_amount,0) bronze_amount, COALESCE(b.bronze_amount,0)-COALESCE(s.src_amount,0) amount_variance FROM (SELECT ingestion_file, COUNT(*) src_count, SUM(local_currency_amount) src_amount FROM src_transaction_daily GROUP BY ingestion_file) s FULL OUTER JOIN (SELECT ingestion_file, COUNT(*) bronze_count, SUM(local_currency_amount) bronze_amount FROM bronze.transaction_daily GROUP BY ingestion_file) b ON s.ingestion_file = b.ingestion_file"]),
				    #"Changed Type" = Table.TransformColumnTypes(Source,{{"dimension", type text}, {"group_value", type text}, {"src_count", Int64.Type}, {"bronze_count", Int64.Type}, {"count_variance", Int64.Type}, {"src_amount", type number}, {"bronze_amount", type number}, {"amount_variance", type number}})
				in
				    #"Changed Type"

	annotation PBI_ResultType = Table
```

`assessment1-exception-summary.tmdl` - one row per level 3 record class, verified against postgres to match `exception-dataset.md` exactly (`exact_match`=1940, `missing_in_bronze`=33, `amount_mismatch`=9, `currency_mismatch`=4, `posting_date_mismatch`=4, `duplicate_in_source`=20, `duplicate_in_bronze`=36):

```
table assessment1-exception-summary
	lineageTag: bc6d3dd5-2a1d-458e-aad9-76c0d4440f2c

	column issue_type
		dataType: string
		lineageTag: 81f928b3-8e6f-4363-aae3-cac7295dc81a
		summarizeBy: none
		sourceColumn: issue_type

		annotation SummarizationSetBy = Automatic

	column row_count
		dataType: int64
		formatString: 0
		lineageTag: 3789d592-403f-4b6f-903a-40cf5217bb91
		summarizeBy: sum
		sourceColumn: row_count

		annotation SummarizationSetBy = Automatic

	partition assessment1-exception-summary = m
		mode: import
		source =
				let
				    Source = PostgreSQL.Database("localhost:5432", "as01_source_db", [Query="WITH src_dupes AS (SELECT transaction_id FROM src_transaction_daily GROUP BY transaction_id HAVING COUNT(*) > 1), bronze_dupes AS (SELECT transaction_id FROM bronze.transaction_daily GROUP BY transaction_id HAVING COUNT(*) > 1), src_clean AS (SELECT * FROM src_transaction_daily WHERE transaction_id NOT IN (SELECT transaction_id FROM src_dupes)), bronze_clean AS (SELECT * FROM bronze.transaction_daily WHERE transaction_id NOT IN (SELECT transaction_id FROM bronze_dupes)), joined AS (SELECT COALESCE(s.transaction_id, b.transaction_id) transaction_id, s.local_currency_amount s_lca, b.local_currency_amount b_lca, s.transaction_amount s_amt, b.transaction_amount b_amt, s.currency_code s_ccy, b.currency_code b_ccy, s.posting_date s_pd, b.posting_date b_pd FROM src_clean s FULL OUTER JOIN bronze_clean b ON s.transaction_id = b.transaction_id) SELECT issue_type, COUNT(*) row_count FROM (SELECT CASE WHEN b_lca IS NULL THEN 'missing_in_bronze' WHEN s_lca IS NULL THEN 'unexpected_in_bronze' WHEN ABS(b_lca - s_lca) > 0.01 OR ABS(b_amt - s_amt) > 0.01 THEN 'amount_mismatch' WHEN b_ccy IS DISTINCT FROM s_ccy THEN 'currency_mismatch' WHEN b_pd IS DISTINCT FROM s_pd THEN 'posting_date_mismatch' ELSE 'exact_match' END AS issue_type FROM joined) t GROUP BY issue_type UNION ALL SELECT 'duplicate_in_source', (SELECT COUNT(*) FROM src_transaction_daily WHERE transaction_id IN (SELECT transaction_id FROM src_dupes)) UNION ALL SELECT 'duplicate_in_bronze', (SELECT COUNT(*) FROM bronze.transaction_daily WHERE transaction_id IN (SELECT transaction_id FROM bronze_dupes))"]),
				    #"Changed Type" = Table.TransformColumnTypes(Source,{{"issue_type", type text}, {"row_count", Int64.Type}})
				in
				    #"Changed Type"

	annotation PBI_ResultType = Table
```

The level 3 query's `CASE`/decision order mirrors the notebook's Level 3 section exactly (duplicate in source -> duplicate in Bronze -> missing -> unexpected -> amount -> currency -> posting-date -> exact match) - see [Level 3 - Record-Level Classification](#level-3---record-level-classification) for why that order and its one documented caveat.

**2. register both tables** in `.SemanticModel/definition/model.tmdl`, which already lists the four existing tables the same way:

```
annotation PBI_QueryOrder = ["reconciliation-summary", "rc_batch_control", "rc_reconciliation_results", "rc_audit_trail", "assessment1-dimension-variance", "assessment1-exception-summary"]

ref table assessment1-dimension-variance

ref table assessment1-exception-summary
```

**3. round trip** - `scripts/05-powerbi-sync.sh push` (repo -> Windows), user opens in Desktop, confirms both new tables refresh with real rows (no repair prompt - the pass signal per the skill; the Postgres credential prompt on first refresh is expected, same as the other three live tables), builds the "Assessment 1 - Reconciliation" page and its three visuals from the [pages/visuals](#dashboard-mock-up) checklist, saves; then `pull` (Windows -> repo) and an independent `diff -rq` confirming the round trip captured exactly the new page/visuals and nothing else.

### 9. Notebook consolidation and clean rerun

edit locations: `09.EL.01`

Reorder the notebook into assignment task order, remove scratch cells, reseed the database, and execute the notebook headless with `scripts/06-notebook-validate.sh`. Confirm every number cited in a deliverable still matches the rerun output; where it does not, correct the deliverable in the same cycle.

### 10. Deliverable review and status promotion

edit locations: `09.EL.02-09.EL.07, 09.EL.11`

Review each deliverable against the [task to deliverable map](#assessment-task-to-deliverable-map) for coverage, a populated **Sources** section, a context line linking the overview, and consistent numbers. Confirm the overview still matches the assignment wording after any analysis-driven edits. Promote each `status: draft` to `status: final`, then run `scripts/07-deliverables-scaffold.sh` to regenerate the manifest with the new statuses and `--check` to confirm the result is current.

### 11. Publish

edit locations: `09.EL.10`

Commit the reviewed work, run `scripts/08-assessment-site.sh build` for the strict build, then `scripts/08-assessment-site.sh deploy` from the clean worktree. Confirm the published Assessment 1 pages, including that the overview is reachable from the site navigation, then update `docs/milestones.md` to mark milestone 09 closed with its closure evidence.

## Validate

**Issues**

- inventory all first out exceptions and issues encountered in this table
- for each issue, create an issue section and use this section to document diagnostics and resolution steps

_09.02-09.04 run (prerequisites, context write-up, task 1 profiling - all ten checks): every script and notebook execution reported `[PASS]` on the first attempt - no exception surfaced there. Two issues surfaced during the follow-on publish/documentation pass, logged below._

| id       | seq | status | issue                                          |
| -------- | --- | ------ | ------------------------------------------------ |
| 09.IS.01 | 01  | closed | gh-pages `git push` had no credentials configured |
| 09.IS.02 | 02  | closed | deliverable status marker convention conflict     |
| 09.IS.03 | 03  | closed | exception dataset showed identical source/bronze values |

_09.IS.01 (closed) gh-pages `git push` had no credentials configured_

**problem description**

`./scripts/08-assessment-site.sh deploy` built the site strictly but failed at the `git push` step - the sandboxed dev environment had no git credential helper, cached HTTPS credentials, or token configured for `origin`.

**exception**

```log
fatal: could not read Username for 'https://github.com': No such device or address
subprocess.CalledProcessError: Command '['git', 'push', 'origin', 'gh-pages', '--force']' returned non-zero exit status 128.
[FAIL] [08.05] gh-pages deployment failed; see .dev/logs/260830204034-08.05-assessment-site-deploy.log
```

**triggering actions**

ran `./scripts/08-assessment-site.sh deploy` for the first gh-pages publish attempt of this session, after committing AS01 task 1 work.

**hypothesis**

no git credential source was available to this environment for pushing to GitHub over HTTPS; a Personal Access Token supplied out-of-band would resolve it without needing an interactive login.

**diagnostic steps**

- first out exception is NOT a diagnostic step
- diagnostic steps reveal information or apply a fix
- assume re-run and validation, these are not diagnostic steps
- keep the step description brief, use the diagnostics details section to elaborate actions and learnings for each step

| id          | seq | status | step                                          |
| ----------- | --- | ------ | ------------------------------------------------ |
| 09.IS.01.01 | 01  | closed | checked for a git credential helper - none found  |
| 09.IS.01.02 | 02  | closed | installed `gh` CLI - still needs a token/login [01] |
| 09.IS.01.03 | 03  | closed | user supplied a PAT; wrote the publish script     |
| 09.IS.01.04 | 04  | closed | reran the publish script - `git push` succeeded   |

01. **09.IS.01.02** `gh` doesn't remove the credential gap by itself - see diagnostic details.

**diagnostic details**

Step 03: `scripts/09-gh-pages-publish.sh` supplies the token to `git` via a one-shot `GIT_ASKPASS` helper script, never embedding it in the remote URL, argv, or any `tee`-captured log line - `git remote get-url origin` (which `08-assessment-site.sh` logs verbatim) stays token-free. It delegates the actual build+deploy to the existing `scripts/08-assessment-site.sh deploy` rather than duplicating that logic, and requires the same clean-worktree precondition; it does not decide which local changes are safe to stash first.

**validation evidence**

`[PASS] [09.12] gh-pages publish completed` in `.dev/logs/*-09.12-gh-pages-publish.log`; published site confirmed live.

_09.IS.02 (closed) deliverable status marker convention conflict_

**problem description**

While reviewing the published deliverable, the plain-text `status: draft` line was removed from `assessment-1-profiling-summary.md` and `results/assessment-1/README.md` was hand-edited to a status value (`open`) the scaffold script did not recognize - `scripts/07-deliverables-scaffold.sh --check` started failing.

**exception**

```log
[FAIL] [08.03] invalid status marker in results/assessment-1/assessment-1-profiling-summary.md
[FAIL] [08.03] missing or stale manifest results/assessment-1/README.md
[FAIL] [08.03] deliverable scaffold incomplete
```

**triggering actions**

manual edits to the deliverable page and its manifest row, changing the status convention.

**hypothesis**

this was a deliberate convention change - `open` as a real in-process status, tracked in the manifest only, not the page - confirmed directly with the user rather than assumed.

**diagnostic steps**

- first out exception is NOT a diagnostic step
- diagnostic steps reveal information or apply a fix
- assume re-run and validation, these are not diagnostic steps
- keep the step description brief, use the diagnostics details section to elaborate actions and learnings for each step

| id          | seq | status | step                                       |
| ----------- | --- | ------ | --------------------------------------------- |
| 09.IS.02.01 | 01  | closed | confirmed intent with the user first [01]      |
| 09.IS.02.02 | 02  | closed | updated `07-deliverables-scaffold.sh` [02]     |
| 09.IS.02.03 | 03  | closed | stripped `status: draft` from AS01's 4 stubs   |
| 09.IS.02.04 | 04  | closed | amended feature 08's docs [03]                 |

01. **09.IS.02.01** before changing an established, closed feature's convention rather than assuming.
02. **09.IS.02.02** page no longer requires/creates a status line; manifest status is read back from the existing README and carried forward, `draft` for a new row.
03. **09.IS.02.04** `docs/features/08-assessment-deliverables-conventions.md` - `draft`/`open`/`final`, manifest-only.

**diagnostic details**

Step 02's manifest-row regex had to tolerate the variable column padding markdown-tables uses (`open` is shorter than `draft`/`final`, so its cell carries extra trailing spaces) - the first fix matched too strictly and silently reset `open` back to the `draft` default; widened to `[[:space:]]*` around each delimiter and re-verified idempotency (rerunning the script twice left `open` unchanged).

**validation evidence**

`scripts/07-deliverables-scaffold.sh --check` and `./scripts/08-assessment-site.sh build` (strict) both pass; `results/assessment-1/README.md` row 01 reads `open` and survives a second scaffold run unchanged.

_09.IS.03 (closed) exception dataset showed identical source/bronze values_

**problem description**

The first execution of the level-3 exception dataset showed `amount_mismatch` rows with identical `source_value`/`bronze_value` (e.g. `6990.12` / `6990.12`, `variance=0.0`) - a mismatch class with no visible mismatch.

**exception**

```log
| TXN-0000010   | amount_mismatch    | 6990.12     | 6990.12     | 0.0     |
```

**triggering actions**

reviewed the notebook's own printed sample rows for the exception dataset after the first Task 2 execution.

**hypothesis**

the classification condition checks both `local_currency_amount` and `transaction_amount` for a mismatch (either can trigger `amount_mismatch`), but the displayed `source_value`/`bronze_value` always showed `local_currency_amount` regardless of which field actually differed.

**diagnostic steps**

- first out exception is NOT a diagnostic step
- diagnostic steps reveal information or apply a fix
- assume re-run and validation, these are not diagnostic steps
- keep the step description brief, use the diagnostics details section to elaborate actions and learnings for each step

| id          | seq | status | step                                     |
| ----------- | --- | ------ | ------------------------------------------- |
| 09.IS.03.01 | 01  | closed | confirmed via direct SQL which field differed |
| 09.IS.03.02 | 02  | closed | added a per-row field-detection column [01]  |
| 09.IS.03.03 | 03  | closed | reran the notebook and confirmed real values  |

01. **09.IS.03.02** `mismatched_field` picks `local_currency_amount` or `transaction_amount` per row depending on which one actually breached the 0.01 tolerance, and `source_value`/`bronze_value`/`variance` follow that same field.

**diagnostic details**

Confirmed via SQL that all 9 `amount_mismatch` rows differ on `transaction_amount` only, none on `local_currency_amount` - Bronze's amount-transform defect mutates the raw transaction amount, not the already-derived local-currency figure, so a check that only looked at `local_currency_amount` would report the right count but the wrong evidence for every single row.

**validation evidence**

Rerun sample rows show real, differing `source_value`/`bronze_value` pairs (e.g. `6990.12` / `6992.03`, `variance=1.91`); `exception_dataset.groupBy("mismatched_field")` confirms all 9 are `transaction_amount`.

**user actions**

- supplied the GitHub PAT used by `scripts/09-gh-pages-publish.sh` (09.IS.01)
- confirmed the `draft`/`open`/`final` status convention change (09.IS.02)
- Power BI Desktop open/save round trip for the dashboard deliverable (09.09)

## Guideline

## instructions

review and strictly follow these relevant skills when performing tasks for this
feature implementation and working with this document

## relevant skills

- markdown-tables
- feature-implementation-guide
- jupyter-notebook-workspace
- powerbi-dashboard-workspace
