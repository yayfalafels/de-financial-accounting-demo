# AI Closed-Loop Validation - Feature tracker
>Review the guidelines before performing any actions including edits on the document 

## 05 (open) ai closed loop develop and validation

## Contents

- [Tasks](#tasks)
- [Scope](#scope)
- [References](#references)
- [Design](#design)
  - [reconciliation control schema](#reconciliation-control-schema)
  - [directory structure](#directory-structure)
  - [claude code vs extension terminal capability](#claude-code-vs-extension-terminal-capability)
  - [reconciliation runner scope](#reconciliation-runner-scope)
  - [ground-truth feedback & audit trail](#ground-truth-feedback--audit-trail)
  - [idempotency / rerun-safety](#idempotency--rerun-safety)
  - [environment & secrets](#environment--secrets)
  - [workflow validation runner](#workflow-validation-runner)
- [Edit locations](#edit-locations)
- [Implement](#implement)
- [Validate](#validate)
- [Guideline](#guideline)

## Tasks

| id    | seq | status  | milestone                                | 
| ----- | --- | ------- | ----------------------------------------- | 
| 05.01 | 01  | open    | design                                    | 
| 05.02 | 02  | pending | reconciliation control schema json        | 
| 05.03 | 03  | pending | ddl generator extension                   | 
| 05.04 | 04  | pending | reconciliation runner script              | 
| 05.05 | 05  | pending | feedback / ground-truth report script     | 
| 05.06 | 06  | pending | closed loop orchestrator script           | 
| 05.IS | 07  | pending | validate                                  | 

## Scope

develop the subset of the **dev env design doc**'s closed-loop feedback system (its §3) that fits this repo's actual agent, not the VS Code-Copilot-chat / `tasks.json` model its §4 was written against - see [claude code vs extension terminal capability](#claude-code-vs-extension-terminal-capability). The closed loop sits on top of already-provisioned infrastructure; it does not stand up containers itself.

- depends on postgresql and spark container - this feature assumes both containers are already running and does not provision infrastructure; it fails fast with a clear message if either is unreachable
- builds the generic reconciliation control-table stack (`reconciliation.rc_batch_control`, `reconciliation.rc_reconciliation_results`, `reconciliation.rc_audit_trail`) the **dev env design doc** sketches and seed data explicitly deferred, so assessment milestones have a persistence layer to log into instead of each inventing their own
- proves the framework end-to-end on one concrete check - Assessment 1's batch-level source-vs-bronze reconciliation - rather than implementing all three assessments' reconciliation logic now; dimensional/record-level checks and the Assessment 2/3 equivalents are additive work for their own milestones
- ground truth for "did the runner get the right answer" is seed data's `data/mock/issue-log.csv`, not a hand-verified expected value - the feedback step cross-checks the runner's measured variance against what was actually injected, so this is a self-check of the assignment scaffold, not a candidate grader
- all steps executable by an autonomous claude code agent with terminal access using re-runnable idempotent scripts; control-table DDL is verify-or-create, but each closed-loop run itself appends a new batch rather than converging to one row - see [idempotency / rerun-safety](#idempotency--rerun-safety)
- does not implement Assessment 2/3 reconciliation logic, Spark-scale (5B-row) profiling, or Power BI dashboards - those stay scoped to the assessments

## References

- **dev env design doc** `docs/design/development-environment.md` (§3 Closed-Loop Feedback System, §4 VS Code & AI Agent Integration)
- **assignment design doc** `docs/design/assignment.md`
- **postgresql dev env tracker** `docs/features/02-dev-env-setup-postgresql-db.md`
- **spark container dev env tracker** `docs/features/03-dev-env-setup-spark-container.md`
- **seed mock data tracker** `docs/features/04-seed-mock-data.md`
- **reconciliation control schemas** `data/schemas/rc-*-schema.json`
- **sql generator script** `scripts/utils/sql-generators.py`
- **closed loop orchestrator script** `scripts/04-closed-loop-run.sh`
- **reconciliation runner script** `scripts/utils/reconciliation-runner.py`
- **feedback report script** `scripts/utils/feedback-report.py`
- **issue log ground truth** `data/mock/issue-log.csv`

## Design

### reconciliation control schema

Three new tables in one new postgres schema, `reconciliation`, following the schema-JSON-as-source-of-truth convention and the seed data's extended to multiple schemas - one new JSON file per table, `sql-generators.py` maps JSON to DDL, nothing hand-edited downstream of the JSON.

| id | table                     | business_key              | role                                       | 
| -- | --------------------------- | ---------------------------- | --------------------------------------------- | 
| 01 | `rc_batch_control`          | `batch_id` (serial)          | one row per closed-loop run                    | 
| 02 | `rc_reconciliation_results` | `result_id` (serial) [01]    | one row per dimension checked in a batch       | 
| 03 | `rc_audit_trail`            | `audit_id` (serial) [01]     | one row per feedback action/decision           | 

01. `rc_reconciliation_results.batch_id` and `rc_audit_trail.batch_id` are foreign keys into `rc_batch_control.batch_id` - both child tables carry a full run's context without repeating it.

Columns follow the **dev env design doc**'s §3.1/§3.2 sketch directly:

- `rc_batch_control`: `batch_id`, `batch_date`, `assessment_id`, `status`, `created_at`
- `rc_reconciliation_results`: `result_id`, `batch_id`, `dimension`, `source_value`, `target_value`, `variance`, `variance_pct`, `reconciliation_status`, `created_at`
- `rc_audit_trail`: `audit_id`, `batch_id`, `action`, `actor`, `created_at`

`reconciliation_status` and `rc_batch_control.status` reuse the postgresql dev env tracker's `allowed_values` -> `CHECK` mapping, constrained to `PASS` / `WARNING` / `FAIL` (`rc_batch_control.status` also allows `RUNNING`, its initial value). The status thresholds mirror the **dev env design doc**'s §3.1 `run_assessment_1` rule: `PASS` under 0.1% variance, `WARNING` under 1%, `FAIL` at or above 1%.

One deviation from the design doc's sketch: no live `psycopg2` connection with `INSERT ... RETURNING batch_id` from Python. The postgresql dev env setup and the seed mock data feature both avoid a host-side DB driver dependency by shelling out to `psql`/`COPY` through `docker exec`; this feature keeps that convention - **reconciliation runner script** computes results in Python, writes them to a local CSV, and bulk-loads via the same `docker exec ... psql \copy` path the seed mock data feature already established for seeding, rather than opening a live connection.

### directory structure

```
data/
├── schemas/
│   ├── rc-batch-control-schema.json          # new
│   ├── rc-reconciliation-results-schema.json # new
│   └── rc-audit-trail-schema.json            # new
└── mock/
    └── issue-log.csv                         # existing - read, not written
postgresql/
├── rc-batch-control-create-table.sql          # new, generated
├── rc-reconciliation-results-create-table.sql # new, generated
└── rc-audit-trail-create-table.sql            # new, generated
scripts/
├── 04-closed-loop-run.sh                      # new: orchestrates the closed loop end to end
└── utils/
    ├── sql-generators.py                      # unchanged - already multi-schema
    ├── reconciliation-runner.py                # new: computes batch-level metrics, loads results
    └── feedback-report.py                      # new: ground-truth cross-check, audit trail, summary
```

### claude code vs extension terminal capability

The **dev env design doc**'s §4 (VS Code & AI Agent Integration) was written against a different execution model than the one actually running this repo's work: a `.vscode/copilot-prompts.md` catalog of prompt text for a human to paste into an editor chat panel, plus a `.vscode/tasks.json` a human clicks to shell out to `docker exec spark-master python3 /scripts/run_reconciliation.py`. In that model the AI only drafts code inside the editor; a human is the one who triggers execution, reads the result, and decides what happens next.

Every prior feature in this repo has instead run on a **Claude Code terminal-agent model**: the agent itself has direct Bash access, writes git-tracked idempotent scripts, executes them, reads their `[PASS]`/`[FAIL]` log output, and decides the next action - all inside one continuous session, with no editor extension or human click mediating that loop. This feature follows that same model rather than the design doc's §4 sketch:

- **no `.vscode/tasks.json` / Copilot prompt templates** - the design doc's §4.1/§4.2 catalogue of things for a human to paste or click is dropped entirely; `scripts/04-closed-loop-run.sh` is invoked directly, the same way `02-workflow-validate.sh` and `03-mock-data-seed.sh` already are
- **the agent closes its own loop** - "closed-loop" here means the same agent that ran the reconciliation script also reads its PASS/WARNING/FAIL output and decides whether to rerun, adjust the schema/generator, or report done, in one session; there is no separate human-in-the-editor step the design doc's model assumed
- **logs are the interface, not a chat panel** - results surface as the standard `[PASS]`/`[FAIL]` log lines under `.dev/logs/`, per the `feature-implementation-guide` skill's logging convention, inspectable by the agent or a human with the same `tail`/`grep` commands used for every prior feature's validation
- this is a difference in *how* the loop runs, not *what* it checks - the reconciliation logic itself (batch, dimensional, record-level checks) is unchanged from the design doc's intent, only relocated from a Python-in-notebook/Copilot-drafted sketch into the same script-and-log convention used by this repo's prior dev-env, spark-container, and seed-data features

### reconciliation runner scope

`reconciliation-runner.py` implements one check for this feature: the **dev env design doc**'s §3.1 `run_assessment_1` batch-level reconciliation, applied to the tables the seed mock data feature already seeded (`src_transaction_daily` / `bronze.transaction_daily`):

1. `source_count` / `bronze_count` - row counts from each table.
2. `source_amount` / `bronze_amount` - `SUM(transaction_amount)` from each table.
3. `variance` = `bronze_amount - source_amount`; `variance_pct` = `variance / source_amount * 100`.
4. Status: `PASS` under 0.1% variance, `WARNING` under 1%, `FAIL` at or above 1% (matches [reconciliation control schema](#reconciliation-control-schema) above).

Both queries run via `docker exec ... psql`, the same pattern **schema-inspect script** already uses - no new host-side DB driver dependency. Explicitly deferred, as additive work for their own milestones: Level 2 (dimensional) and Level 3 (record-level) checks from Assessment 1 Task 2, and the Assessment 2 / Assessment 3 equivalents (GL reconciliation, source -> Bronze -> regulatory lineage). This feature's job is to prove the control-table + runner + feedback pattern once, end to end, so extending it with more checks later is additive rather than a redesign.

### ground-truth feedback & audit trail

`feedback-report.py` closes the loop:

1. Reads back `reconciliation.rc_reconciliation_results` for the batch the runner just inserted.
2. Independently reads `data/mock/issue-log.csv` and sums the expected variance implied by the assessment-1 issue catalog's Bronze-side issues (missing/duplicate/mismatched rows - catalog ids 09-14 in the seed mock data feature's [injected issue catalog - assessment 1](04-seed-mock-data.md#injected-issue-catalog--assessment-1)).
3. Compares the runner's *measured* variance against the *expected* variance derived from the issue log. A mismatch beyond a small tolerance means the runner or the seed data has a bug, not that a real reconciliation break was found - this is a self-consistency check on the scaffold, distinct from a candidate's own reconciliation work in the assessment 1/2/3 milestones.
4. Inserts one `reconciliation.rc_audit_trail` row recording the comparison outcome and any triggered action (`INVESTIGATE` if the self-check itself disagrees with the issue log, `NOTIFY` otherwise), and prints a `[PASS]`/`[WARN]`/`[FAIL]` summary line.

### idempotency / rerun-safety

- **Control tables**: DDL uses `CREATE TABLE IF NOT EXISTS`, same generator, same convention as the postgresql and seed-data features - safe to rerun.
- **Container prerequisites**: the orchestrator checks postgres and spark are already running (`docker ps --filter name=...`) before doing anything else; it fails fast with a clear message rather than standing them up, matching the seed mock data feature's orchestrator convention (that stays the postgresql and spark container features' job).
- **Batch history is intentionally append-only**: unlike prior features' verify-or-create tables, every closed-loop run inserts a *new* `rc_batch_control` row and its own `rc_reconciliation_results` / `rc_audit_trail` rows rather than overwriting - the assignment's Assessment 2 Task 4 explicitly asks how reconciliation results should be "persisted for audit and historical analysis," so rerunning is expected to accumulate history, not converge to one row. Rerun-safety here means "safe to run again without corrupting prior batches," not "idempotent output."

### environment & secrets

No new secrets - `reconciliation-runner.py` and `feedback-report.py` reuse the existing `POSTGRES_*` variables from `.env`/`.secrets`, connecting through the same `docker exec ... psql` path as every prior feature, since this feature only reads already-seeded tables and writes to its own control schema with those same credentials. If the spark container dev env feature introduces a `SPARK_MASTER_CONTAINER_NAME` (or similar) variable, this feature only reads it, to verify the container is up per [idempotency / rerun-safety](#idempotency--rerun-safety) - it does not add its own Spark-specific variables, since the runner itself does not submit Spark jobs in this slice.

### workflow validation runner

`scripts/04-closed-loop-run.sh`:

1. Verifies the postgres container (and the spark container, once the spark container dev env feature lands) are already running; fails fast otherwise.
2. Applies the reconciliation control-schema DDL (idempotent).
3. Runs **reconciliation runner script**: computes the Assessment 1 batch-level check against the tables the seed mock data feature seeded, inserts a new `rc_batch_control` row plus its `rc_reconciliation_results` rows.
4. Runs **feedback report script**: cross-checks the batch's results against `issue-log.csv`, inserts an `rc_audit_trail` row, prints the overall summary, and exits non-zero on `FAIL`.

## Edit locations

_to fill in during Implement - see [directory structure](#directory-structure) for the planned file set_

## Implement

## Validate

**Issues**

- inventory all first out exceptions and issues encountered in this table
- for each issue, create an issue section and use this section to document diagnostics and resolution steps

| id       | seq | status  | issue                                     | 
| -------- | --- | ------- | ------------------------------------------ | 
| 05.IS.01 | 01  | pending | <first out exception>                      | 

_05.IS.01 (pending) <first out exception>_

**problem description**

<to fill in>

**exception**

```log
<to fill in>
```

**triggering actions**

<to fill in>

**hypothesis**

- use hypothesis framing until a validated fix is applied

<to fill in>

**diagnostic steps**

- first out exception is NOT a diagnostic step
- diagnostic steps reveal information or apply a fix
- assume re-run and validation, these are not diagnostic steps
- keep the step description brief, use the diagnostics details section to elaborate actions and learnings for each step

| id          | seq | status  | step                                      | 
| ----------- | --- | ------- | ------------------------------------------ | 
| 05.IS.01.01 | 01  | pending | <diagnostic step 01>                       | 

**diagnostic details**

## Guideline

## instructions

review and strictly follow these relevant skills when performing tasks for this feature implementation and working with this document

## relevant skills

- markdown-tables
- feature-implementation-guide
