# AI Closed-Loop Validation - Feature tracker
>Review the guidelines before performing any actions including edits on the document 

## 05 (closed) ai closed loop develop and validation

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
- [Test cases](#test-cases)
- [Edit locations](#edit-locations)
- [Implement](#implement)
- [Validate](#validate)
- [Guideline](#guideline)

## Tasks

| id    | seq | status  | milestone                                 | 
| ----- | --- | ------- | ----------------------------------------- | 
| 05.01 | 01  | closed  | design and test cases                     | 
| 05.07 | 02  | closed  | edit locations implementation plan        | 
| 05.02 | 03  | closed  | reconciliation control schema json        | 
| 05.03 | 04  | closed  | ddl generator extension                   | 
| 05.04 | 05  | closed  | reconciliation runner script              | 
| 05.05 | 06  | closed  | feedback / ground-truth report script     | 
| 05.06 | 07  | closed  | closed loop orchestrator script           | 
| 05.IS | 08  | closed  | validate                                  | 

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

| id | table                       | business_key              | role                                     | 
| -- | --------------------------- | ------------------------- | ---------------------------------------- | 
| 01 | `rc_batch_control`          | `batch_id` (serial)       | one row per closed-loop run              | 
| 02 | `rc_reconciliation_results` | `result_id` (serial) [01] | one row per dimension checked in a batch | 
| 03 | `rc_audit_trail`            | `audit_id` (serial) [01]  | one row per feedback action/decision     | 

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

## Test cases

_test strategy_

Every task below is checked on three independent layers, so a pass is never just "the script printed `[PASS]`":

1. **script self-report** - the `[PASS]`/`[FAIL]` log lines each script/orchestrator emits under `.dev/logs/`, per the `feature-implementation-guide` skill's logging convention.
2. **direct DB inspection, bypassing the scripts** - raw `docker exec ... psql` queries against `information_schema` (DDL/schema shape) and the live tables (row counts, sums, appended rows), run independently of anything the runner or feedback script reports - the same pattern as the **postgresql dev env tracker**'s secondary-validation `\d` command and [schema-inspect.py](../../scripts/utils/schema-inspect.py)'s live-vs-JSON diff, extended to cover the new `reconciliation` schema.
3. **independently-derived expected values** - before trusting `feedback-report.py`'s own ground-truth comparison, hand-derive the expected variance from `issue-log.csv` catalog ids 09-14 with a separate ad-hoc query, so the feedback script is never grading its own homework.

Append-only/idempotency (the [idempotency / rerun-safety](#idempotency--rerun-safety) design point) is tested by running the DDL apply and the orchestrator twice each and diffing row counts directly via layer 2, not by re-reading either script's own printed summary.

_test cases_

| id       | task  | layer       | check                                                    | 
| -------- | ----- | ----------- | -------------------------------------------------------- | 
| 05.TC.01 | 05.02 | schema      | 3 JSON files parse, shape matches convention             | 
| 05.TC.02 | 05.02 | schema      | `batch_id` FK declared on both child tables              | 
| 05.TC.03 | 05.02 | schema      | `allowed_values` sets match spec                         | 
| 05.TC.04 | 05.03 | direct-db   | generated SQL text has correct DDL per table             | 
| 05.TC.05 | 05.03 | direct-db   | live `information_schema` diff vs JSON, all 3 tables     | 
| 05.TC.06 | 05.03 | direct-db   | DDL apply rerun twice - no error, 0 rows both times      | 
| 05.TC.07 | 05.04 | direct-db   | one new `rc_batch_control` row + result rows appended    | 
| 05.TC.08 | 05.04 | independent | runner counts/sums match raw `COUNT`/`SUM` query         | 
| 05.TC.09 | 05.04 | independent | variance/variance_pct/status arithmetic checked by hand  | 
| 05.TC.10 | 05.04 | direct-db   | runner rerun - `batch_id` increments, no overwrite       | 
| 05.TC.11 | 05.05 | independent | hand-derived expected variance vs script's own           | 
| 05.TC.12 | 05.05 | direct-db   | feedback reads back the same `batch_id` just written     | 
| 05.TC.13 | 05.05 | direct-db   | exactly 1 new `rc_audit_trail` row, correct action       | 
| 05.TC.14 | 05.05 | script      | forced-FAIL path exits non-zero, not eyeballed           | 
| 05.TC.15 | 05.06 | direct-db   | containers down -> fails fast, no batch row written      | 
| 05.TC.16 | 05.06 | script      | full run - 4 stages in order, log file per stage         | 
| 05.TC.17 | 05.06 | direct-db   | 2 consecutive runs - batch count +1, priors intact       | 
| 05.TC.18 | 05.06 | script      | log file names match `<ts>-05.<sub>-<name>.log`          | 

01. **05.TC.01** same `{"tables": [{"table_name", "columns": [...], "business_key", ...}]}` shape `sql-generators.py` already parses for `as01-source-schema.json` - checked by `json.loads` + key-set diff, not just "file exists".
02. **05.TC.03** `rc_reconciliation_results.reconciliation_status` and `rc_batch_control.status` -> `{PASS, WARNING, FAIL}`, plus `RUNNING` only on `rc_batch_control.status`.
03. **05.TC.04** `grep` the generated `.sql` for `CREATE TABLE IF NOT EXISTS reconciliation.<table>`, the `CHECK` clause text, and the `FOREIGN KEY (batch_id) REFERENCES reconciliation.rc_batch_control` clause on both child tables - not just that the generator exited 0.
04. **05.TC.08** re-run `SELECT COUNT(*), SUM(transaction_amount) FROM src_transaction_daily` and the `bronze.` equivalent directly via `docker exec ... psql` at the same point in time the runner ran, and diff against what got inserted into `rc_reconciliation_results` - the runner's own printed numbers are not trusted as the source of truth.
05. **05.TC.11** sum the amounts of the `issue-log.csv` row_keys under catalog ids 09-14 (missing/duplicate/dropped rows' amounts pulled by a separate join against `src_transaction_daily`, plus catalog id 12's expected_value-vs-injected_value delta) with an ad-hoc script, before running `feedback-report.py` - then compare its result to the feedback script's own computed expected variance.
06. **05.TC.13** force both branches at least once: a clean run (expect `NOTIFY`) and a synthetic mismatch, e.g. pointing the comparison at a fabricated pair of values in isolation, to prove `INVESTIGATE` actually fires and isn't dead code.
07. **05.TC.14** checked with `echo $?` right after a run forced into the FAIL branch (e.g. by pointing it at a batch with a fabricated large variance), not by reading the printed summary text.
08. **05.TC.16** DDL apply -> reconciliation runner -> feedback report, in that order; overall orchestrator exit code equals the worst of the three stage exit codes.

**tools**

Reused directly, no new tooling needed for layer 2/3 checks:

```bash
cd /home/taylor-hickem/repos/de-financial-accounting-demo
set -a && source .env && source .secrets && set +a
psql_run() { docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" -i "$POSTGRES_CONTAINER_NAME" \
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$1"; }

# layer 2 - schema shape, independent of sql-generators.py's own report
psql_run "\d reconciliation.rc_batch_control"
psql_run "\d reconciliation.rc_reconciliation_results"
psql_run "\d reconciliation.rc_audit_trail"

# layer 2 - row counts before/after a run, to catch overwrite-vs-append bugs
psql_run "SELECT COUNT(*) FROM reconciliation.rc_batch_control;"
psql_run "SELECT batch_id, dimension, source_value, target_value, variance_pct, reconciliation_status FROM reconciliation.rc_reconciliation_results ORDER BY batch_id DESC LIMIT 10;"

# layer 3 - independently-measured source/bronze counts and sums, not read from the runner's own output
psql_run "SELECT COUNT(*), SUM(transaction_amount) FROM src_transaction_daily;"
psql_run "SELECT COUNT(*), SUM(transaction_amount) FROM bronze.transaction_daily;"
```

`schema-inspect.py` is reused as-is for 05.TC.05 (point `--schema` at the new `rc-*-schema.json` files and `--table` at each of the 3 new tables) rather than writing a parallel diff tool.

## Edit locations

| id       | path                                                    | 
| -------- | ------------------------------------------------------- | 
| 05.EL.01 | `data/schemas/rc-batch-control-schema.json`             | 
| 05.EL.02 | `data/schemas/rc-reconciliation-results-schema.json`    | 
| 05.EL.03 | `data/schemas/rc-audit-trail-schema.json`               | 
| 05.EL.04 | `scripts/utils/sql-generators.py`                       | 
| 05.EL.05 | `postgresql/rc-batch-control-create-table.sql`          | 
| 05.EL.06 | `postgresql/rc-reconciliation-results-create-table.sql` | 
| 05.EL.07 | `postgresql/rc-audit-trail-create-table.sql`            | 
| 05.EL.08 | `scripts/utils/reconciliation-runner.py`                | 
| 05.EL.09 | `scripts/utils/feedback-report.py`                      | 
| 05.EL.10 | `scripts/04-closed-loop-run.sh`                         | 

01. **05.EL.04** extended: serial/integer, default, FK. see [DDL generator extension](#2-ddl-generator-extension-edit-location-04) below for the three function-level diffs.
02. **05.EL.05, 05.EL.06, 05.EL.07** generated by running the extended `05.EL.04`: `sql-generators.py` against each of the 3 new schema JSONs `05.EL.01,05.EL.02,05.EL.03` - not hand-written, per the schema-JSON-as-source-of-truth convention already established.

No `.env`/`.gitignore`/`pyproject.toml` changes - per [environment & secrets](#environment--secrets), the runner and feedback scripts reuse existing `POSTGRES_*` values and shell out to `psql` the same way `schema-inspect.py`/`seed-inspect.py` already do (no new dependency, no new secret). Container names default inline in the shell script (`"${POSTGRES_CONTAINER_NAME:-postgres-as01}"`, `"${SPARK_CONTAINER_NAME:-spark-master}"`), matching how `spark-master` is referenced as a literal elsewhere in this repo rather than a `.env` variable.

## Implement

Implementation order matches the dependency chain in [directory structure](#directory-structure): schemas -> generator extension -> generated DDL -> runner -> feedback -> orchestrator. Each item below was transcribed directly with no code changes during 05.02-05.06 - see [Validate](#validate) for the run-by-run evidence.

### 1. EL.05.01 reconciliation control schema JSON

edit locations: `EL.05.01, EL.05.02, EL.05.03`

Three flat files in `data/schemas/`, same convention as the existing 9 (`as0*-*-schema.json`). All three use `"enforce_constraints": true` (the default - omitted) since these are structured control tables, not raw dirty-data landing tables like `src_transaction_daily`.

**`data/schemas/rc-batch-control-schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "schema_id": "rc-batch-control-schema",
  "description": "Control table: one row per closed-loop reconciliation run.",
  "tables": [
    {
      "table_name": "reconciliation.rc_batch_control",
      "description": "One row per closed-loop run; parent of rc_reconciliation_results and rc_audit_trail.",
      "business_key": ["batch_id"],
      "columns": [
        { "name": "batch_id", "type": "serial", "nullable": false, "description": "Auto-increment run id" },
        { "name": "batch_date", "type": "date", "nullable": false, "description": "Business date the batch reconciles" },
        { "name": "assessment_id", "type": "string", "nullable": false, "description": "Which assessment's check this batch runs, e.g. 'assessment-1'" },
        { "name": "status", "type": "string", "nullable": false, "default": "'RUNNING'", "allowed_values": ["RUNNING", "PASS", "WARNING", "FAIL"], "description": "RUNNING until the runner finishes, then worst status across its dimension rows" },
        { "name": "created_at", "type": "timestamp", "nullable": false, "default": "now()", "description": "Row insert time" }
      ]
    }
  ]
}
```

**`data/schemas/rc-reconciliation-results-schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "schema_id": "rc-reconciliation-results-schema",
  "description": "One row per dimension checked in a batch.",
  "tables": [
    {
      "table_name": "reconciliation.rc_reconciliation_results",
      "description": "Child of rc_batch_control - one row per dimension checked ('row_count', 'amount').",
      "business_key": ["result_id"],
      "foreign_keys": [
        { "columns": ["batch_id"], "references_table": "reconciliation.rc_batch_control", "references_columns": ["batch_id"] }
      ],
      "columns": [
        { "name": "result_id", "type": "serial", "nullable": false, "description": "Auto-increment result row id" },
        { "name": "batch_id", "type": "integer", "nullable": false, "description": "FK to rc_batch_control.batch_id" },
        { "name": "dimension", "type": "string", "nullable": false, "allowed_values": ["row_count", "amount"], "description": "Which check this row is" },
        { "name": "source_value", "type": "decimal", "precision": 20, "scale": 4, "nullable": false, "description": "Measured value on the source side" },
        { "name": "target_value", "type": "decimal", "precision": 20, "scale": 4, "nullable": false, "description": "Measured value on the Bronze side" },
        { "name": "variance", "type": "decimal", "precision": 20, "scale": 4, "nullable": false, "description": "target_value - source_value" },
        { "name": "variance_pct", "type": "decimal", "precision": 10, "scale": 4, "nullable": false, "description": "variance / source_value * 100" },
        { "name": "reconciliation_status", "type": "string", "nullable": false, "allowed_values": ["PASS", "WARNING", "FAIL"], "description": "PASS <0.1%, WARNING <1%, FAIL >=1% of |variance_pct|" },
        { "name": "created_at", "type": "timestamp", "nullable": false, "default": "now()", "description": "Row insert time" }
      ]
    }
  ]
}
```

**`data/schemas/rc-audit-trail-schema.json`**

**implementation decision** - the design doc says "one row per dimension checked in a batch" without naming the dimensions. This plan fixes them at exactly two: `row_count` (source/bronze row counts, [reconciliation runner scope](#reconciliation-runner-scope) item 1) and `amount` (source/bronze `SUM(transaction_amount)`, item 2) - both scored with the same variance/variance_pct/status formula, so `rc_batch_control.status` becomes the worst of the two. This is the natural reading of items 1-4 taken together, not a literal quote from the design doc - flag it during 05.04 review if a different split is wanted.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "schema_id": "rc-audit-trail-schema",
  "description": "One row per feedback action/decision - the ground-truth cross-check outcome.",
  "tables": [
    {
      "table_name": "reconciliation.rc_audit_trail",
      "description": "Child of rc_batch_control - records the feedback step's comparison outcome.",
      "business_key": ["audit_id"],
      "foreign_keys": [
        { "columns": ["batch_id"], "references_table": "reconciliation.rc_batch_control", "references_columns": ["batch_id"] }
      ],
      "columns": [
        { "name": "audit_id", "type": "serial", "nullable": false, "description": "Auto-increment audit row id" },
        { "name": "batch_id", "type": "integer", "nullable": false, "description": "FK to rc_batch_control.batch_id" },
        { "name": "action", "type": "string", "nullable": false, "allowed_values": ["NOTIFY", "INVESTIGATE"], "description": "INVESTIGATE if the ground-truth cross-check disagrees, NOTIFY otherwise" },
        { "name": "actor", "type": "string", "nullable": false, "description": "What produced this row, e.g. 'feedback-report.py'" },
        { "name": "created_at", "type": "timestamp", "nullable": false, "default": "now()", "description": "Row insert time" }
      ]
    }
  ]
}
```

### 2. DDL generator extension 

edit locations: `05.EL.04`

None of the 9 existing schema JSONs use an auto-increment id, a column `default`, or a foreign key - `scripts/utils/sql-generators.py` has no support for any of the three today. All three are needed for `batch_id`/`result_id`/`audit_id` (serial), `status`/`created_at` (defaults), and the two child tables' `batch_id` FK. Three functions change:

`pg_type()` - add two branches:

```python
    if json_type == "serial":
        return "SERIAL"
    if json_type == "integer":
        return "INTEGER"
```
(inserted right before the existing `raise ValueError(...)` at the end of the function.)

`column_ddl()` - add a `DEFAULT` clause between the existing `NOT NULL` append and the `CHECK` append:

```python
    if not_null:
        parts.append("NOT NULL")

    if default := column.get("default"):
        parts.append(f"DEFAULT {default}")

    if enforce_constraints and (allowed := column.get("allowed_values")):
        values_sql = ", ".join(f"'{v}'" for v in allowed)
        parts.append(f'CHECK ("{column["name"]}" IN ({values_sql}))')
```
`default` is passed through as a raw SQL fragment (`"'RUNNING'"`, `"now()"`) rather than a typed value, same trust level the JSON already has as hand-authored source-of-truth - no new escaping logic needed.

`generate_table_ddl()` - add a `FOREIGN KEY` loop after the existing `PRIMARY KEY` block, before `columns_sql` is joined:

```python
    for fk in table.get("foreign_keys", []):
        cols = ", ".join(f'"{c}"' for c in fk["columns"])
        ref_schema, ref_name = qualify_table_name(fk["references_table"])
        ref_qualified = f'"{ref_schema}"."{ref_name}"' if ref_schema else f'"{ref_name}"'
        ref_cols = ", ".join(f'"{c}"' for c in fk["references_columns"])
        lines.append(f"    FOREIGN KEY ({cols}) REFERENCES {ref_qualified} ({ref_cols})")
```
Reuses the existing `qualify_table_name()` helper unchanged - `references_table` is written the same schema-qualified way as `table_name` already is (`"reconciliation.rc_batch_control"`).

**expected generated output** (`rc-reconciliation-results-create-table.sql`, for review against the actual generator run in 05.03):

```sql
CREATE SCHEMA IF NOT EXISTS "reconciliation";

CREATE TABLE IF NOT EXISTS "reconciliation"."rc_reconciliation_results" (
    "result_id" SERIAL NOT NULL,
    "batch_id" INTEGER NOT NULL,
    "dimension" TEXT NOT NULL CHECK ("dimension" IN ('row_count', 'amount')),
    "source_value" NUMERIC(20,4) NOT NULL,
    "target_value" NUMERIC(20,4) NOT NULL,
    "variance" NUMERIC(20,4) NOT NULL,
    "variance_pct" NUMERIC(10,4) NOT NULL,
    "reconciliation_status" TEXT NOT NULL CHECK ("reconciliation_status" IN ('PASS', 'WARNING', 'FAIL')),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY ("result_id"),
    FOREIGN KEY ("batch_id") REFERENCES "reconciliation"."rc_batch_control" ("batch_id")
);
```

### 3. reconciliation-runner.py 

edit locations: `05.EL.08`

No live `psycopg2` connection ([reconciliation control schema](#reconciliation-control-schema)'s stated deviation) - `batch_id` is reserved via `nextval()` on the table's own auto-created sequence *before* either CSV is written, so the same value can go into both the `rc_batch_control` row and the `rc_reconciliation_results` rows ahead of either `\copy`. `\copy` calls give an explicit target column list (`batch_id, dimension, ...` - never the `SERIAL` column itself), unlike `03-mock-data-seed.sh`'s positional `\copy` - that script's tables have no auto-increment column, so positional CSV-order-matches-DDL-order was safe there; it is not here.

```python
#!/usr/bin/env python3
"""reconciliation-runner.py

Computes Assessment 1's batch-level source-vs-bronze reconciliation
(src_transaction_daily vs bronze.transaction_daily: row count and
SUM(transaction_amount)), inserts one new reconciliation.rc_batch_control
row plus two reconciliation.rc_reconciliation_results rows (dimension =
'row_count' / 'amount'), and prints a [PASS]/[WARNING]/[FAIL] summary per
dimension plus one overall summary line.

No third-party DB driver - shells out to psql via `docker exec`, same
convention as schema-inspect.py / seed-inspect.py. See
docs/features/05-ai-closed-loop-validation.md -> Design -> reconciliation
control schema for the no-live-connection rationale.

Usage:
    python3 scripts/utils/reconciliation-runner.py \
        --container postgres-as01 --user as01_admin --db as01_source_db \
        --assessment-id assessment-1
"""

import argparse
import csv
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORK_DIR = REPO_ROOT / ".dev" / "tmp" / "reconciliation-runner"

SOURCE_TABLE = "src_transaction_daily"
BRONZE_TABLE = "bronze.transaction_daily"
AMOUNT_COL = "transaction_amount"


def status_for(variance_pct: float) -> str:
    # PASS <0.1%, WARNING <1%, FAIL >=1% - matches the CHECK thresholds in
    # rc-reconciliation-results-schema.json
    pct = abs(variance_pct)
    if pct < 0.1:
        return "PASS"
    if pct < 1.0:
        return "WARNING"
    return "FAIL"


def psql_scalar(container: str, user: str, db: str, query: str) -> str:
    cmd = ["docker", "exec", "-i", container, "psql", "-U", user, "-d", db, "-t", "-A", "-c", query]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"psql query failed: {result.stderr.strip()}")
    return result.stdout.strip()


def psql_copy(container: str, user: str, db: str, table: str, columns: list[str], csv_path: Path) -> None:
    col_list = ", ".join(columns)
    cmd = [
        "docker", "exec", "-i", container, "psql", "-U", user, "-d", db, "-v", "ON_ERROR_STOP=1",
        "-c", f"\\copy {table} ({col_list}) FROM STDIN WITH (FORMAT csv, HEADER true)",
    ]
    with csv_path.open("rb") as f:
        result = subprocess.run(cmd, stdin=f, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"\\copy into {table} failed: {result.stderr.strip()}")


def reserve_batch_id(container: str, user: str, db: str) -> int:
    seq = "reconciliation.rc_batch_control_batch_id_seq"
    return int(psql_scalar(container, user, db, f"SELECT nextval('{seq}');"))


def measure(container: str, user: str, db: str) -> dict:
    return {
        "source_count": int(psql_scalar(container, user, db, f"SELECT COUNT(*) FROM {SOURCE_TABLE};")),
        "bronze_count": int(psql_scalar(container, user, db, f"SELECT COUNT(*) FROM {BRONZE_TABLE};")),
        "source_amount": float(psql_scalar(container, user, db, f"SELECT COALESCE(SUM({AMOUNT_COL}),0) FROM {SOURCE_TABLE};")),
        "bronze_amount": float(psql_scalar(container, user, db, f"SELECT COALESCE(SUM({AMOUNT_COL}),0) FROM {BRONZE_TABLE};")),
    }


def build_dimension_rows(batch_id: int, m: dict) -> list[dict]:
    rows = []
    for dimension, source_value, target_value in (
        ("row_count", m["source_count"], m["bronze_count"]),
        ("amount", m["source_amount"], m["bronze_amount"]),
    ):
        variance = target_value - source_value
        variance_pct = round((variance / source_value * 100) if source_value else 0.0, 4)
        rows.append({
            "batch_id": batch_id,
            "dimension": dimension,
            "source_value": source_value,
            "target_value": target_value,
            "variance": variance,
            "variance_pct": variance_pct,
            "reconciliation_status": status_for(variance_pct),
            "created_at": datetime.now().isoformat(),
        })
    return rows


def worst_status(rows: list[dict]) -> str:
    order = {"PASS": 0, "WARNING": 1, "FAIL": 2}
    return max((r["reconciliation_status"] for r in rows), key=lambda s: order[s])


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--container", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--assessment-id", default="assessment-1")
    args = parser.parse_args()

    try:
        batch_id = reserve_batch_id(args.container, args.user, args.db)
        dimension_rows = build_dimension_rows(batch_id, measure(args.container, args.user, args.db))
        status = worst_status(dimension_rows)

        batch_row = {
            "batch_id": batch_id,
            "batch_date": date.today().isoformat(),
            "assessment_id": args.assessment_id,
            "status": status,
            "created_at": datetime.now().isoformat(),
        }

        batch_csv = WORK_DIR / f"batch_{batch_id}_control.csv"
        results_csv = WORK_DIR / f"batch_{batch_id}_results.csv"
        write_csv(batch_csv, list(batch_row.keys()), [batch_row])
        write_csv(results_csv, list(dimension_rows[0].keys()), dimension_rows)

        psql_copy(args.container, args.user, args.db, "reconciliation.rc_batch_control",
                   list(batch_row.keys()), batch_csv)
        psql_copy(args.container, args.user, args.db, "reconciliation.rc_reconciliation_results",
                   list(dimension_rows[0].keys()), results_csv)
    except Exception as exc:  # noqa: BLE001 - top-level safe wrapper, no silent failure
        print(f"[FAIL] reconciliation-runner: {exc}", file=sys.stderr)
        return 1

    for r in dimension_rows:
        print(f"[{r['reconciliation_status']}] {r['dimension']}: source={r['source_value']} "
              f"bronze={r['target_value']} variance_pct={r['variance_pct']}%")
    print(f"[{status}] reconciliation-runner: batch_id={batch_id} overall status={status}")
    return 0 if status != "FAIL" else 1


if __name__ == "__main__":
    sys.exit(main())
```

### 4. feedback-report.py

edit locations: `05.EL.09`

`expected_amount_variance()` is the independently-derived ground truth [05.TC.11](#test-cases) checks against - it re-reads `issue-log.csv` and re-queries `src_transaction_daily` itself rather than trusting anything the runner wrote, matching [ground-truth feedback & audit trail](#ground-truth-feedback--audit-trail) item 2. It maps catalog ids 09-14 to the live `issue_type` strings the seed mock data feature actually writes (`bronze_amount_mismatch`, `missing_in_bronze_unrelated`, `duplicate_in_bronze_reprocessed`, `utc_sgt_midnight_boundary`; `bronze_currency_mismatch`/`bronze_posting_date_mismatch` are excluded - they change currency/date, not the amount sum) [01]:

| id | issue_type                        | table                      | amount effect           | 
| -- | --------------------------------- | -------------------------- | ----------------------- | 
| 09 | `utc_sgt_midnight_boundary`       | `src_transaction_daily`    | dropped -> subtract     | 
| 10 | `missing_in_bronze_unrelated`     | `bronze.transaction_daily` | dropped -> subtract     | 
| 11 | `duplicate_in_bronze_reprocessed` | `bronze.transaction_daily` | duplicated -> add       | 
| 12 | `bronze_amount_mismatch`          | `bronze.transaction_daily` | add (injected-expected) | 
| 13 | `bronze_currency_mismatch`        | `bronze.transaction_daily` | n/a                     | 
| 14 | `bronze_posting_date_mismatch`    | `bronze.transaction_daily` | n/a                     | 

01. table/issue_type values confirmed live against the current `data/mock/issue-log.csv` (`awk -F',' '{print $1","$3}' data/mock/issue-log.csv | sort -u`) - re-verify this mapping if the seed mock data feature's generator ever renames a category.

```python
#!/usr/bin/env python3
"""feedback-report.py

Closes the loop: reads back the batch reconciliation-runner.py just wrote,
independently sums the expected 'amount' variance implied by
data/mock/issue-log.csv's Bronze-side issues (assessment-1 catalog ids
09-14), compares it against the runner's own measured 'amount' variance,
inserts one reconciliation.rc_audit_trail row (INVESTIGATE if they
disagree beyond tolerance, NOTIFY otherwise), and prints a
[PASS]/[FAIL] summary. Exits non-zero if the batch's own status is FAIL
or the ground-truth check disagrees. See
docs/features/05-ai-closed-loop-validation.md -> Design -> ground-truth
feedback & audit trail.

Usage:
    python3 scripts/utils/feedback-report.py \
        --container postgres-as01 --user as01_admin --db as01_source_db \
        --issue-log data/mock/issue-log.csv
"""

import argparse
import csv
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ISSUE_LOG = REPO_ROOT / "data" / "mock" / "issue-log.csv"
WORK_DIR = REPO_ROOT / ".dev" / "tmp" / "feedback-report"

TOLERANCE_ABS = 1.00  # dollars - absorbs float/decimal rounding, not a real disagreement
ACTOR = "feedback-report.py"


def run_query(container: str, user: str, db: str, query: str) -> list[str]:
    cmd = ["docker", "exec", "-i", container, "psql", "-U", user, "-d", db, "-t", "-A", "-F", "|", "-c", query]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"psql query failed: {result.stderr.strip()}")
    return [line for line in result.stdout.strip().splitlines() if line.strip()]


def latest_batch(container: str, user: str, db: str) -> int:
    rows = run_query(container, user, db, "SELECT MAX(batch_id) FROM reconciliation.rc_batch_control;")
    return int(rows[0])


def measured_amount_variance(container: str, user: str, db: str, batch_id: int) -> float:
    query = (
        "SELECT variance FROM reconciliation.rc_reconciliation_results "
        f"WHERE batch_id = {batch_id} AND dimension = 'amount';"
    )
    rows = run_query(container, user, db, query)
    if not rows:
        raise RuntimeError(f"no 'amount' dimension row found for batch_id={batch_id}")
    return float(rows[0])


def source_amounts(container: str, user: str, db: str, transaction_ids: list[str]) -> dict:
    if not transaction_ids:
        return {}
    id_list = ", ".join(f"'{t}'" for t in transaction_ids)
    query = f"SELECT transaction_id, transaction_amount FROM src_transaction_daily WHERE transaction_id IN ({id_list});"
    amounts = {}
    for line in run_query(container, user, db, query):
        txn_id, amount = line.split("|")
        amounts[txn_id] = float(amount)
    return amounts


def expected_amount_variance(container: str, user: str, db: str, issue_log_path: Path) -> float:
    with issue_log_path.open() as f:
        issue_rows = list(csv.DictReader(f))

    mismatch_delta = sum(
        float(r["injected_value"]) - float(r["expected_value"])
        for r in issue_rows
        if r["table"] == "bronze.transaction_daily" and r["issue_type"] == "bronze_amount_mismatch"
    )
    missing_ids = [r["row_key"] for r in issue_rows
                   if r["table"] == "bronze.transaction_daily" and r["issue_type"] == "missing_in_bronze_unrelated"]
    midnight_ids = [r["row_key"] for r in issue_rows
                    if r["table"] == "src_transaction_daily" and r["issue_type"] == "utc_sgt_midnight_boundary"]
    duplicate_ids = [r["row_key"] for r in issue_rows
                     if r["table"] == "bronze.transaction_daily" and r["issue_type"] == "duplicate_in_bronze_reprocessed"]

    amounts = source_amounts(container, user, db, list(set(missing_ids + midnight_ids + duplicate_ids)))
    dropped_amount = sum(amounts.get(t, 0.0) for t in missing_ids + midnight_ids)
    duplicated_amount = sum(amounts.get(t, 0.0) for t in duplicate_ids)

    return mismatch_delta - dropped_amount + duplicated_amount


def batch_status(container: str, user: str, db: str, batch_id: int) -> str:
    rows = run_query(container, user, db, f"SELECT status FROM reconciliation.rc_batch_control WHERE batch_id={batch_id};")
    return rows[0] if rows else "FAIL"


def write_audit_row(container: str, user: str, db: str, batch_id: int, action: str) -> None:
    row = {"batch_id": batch_id, "action": action, "actor": ACTOR, "created_at": datetime.now().isoformat()}
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = WORK_DIR / f"batch_{batch_id}_audit.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)

    col_list = ", ".join(row.keys())
    cmd = [
        "docker", "exec", "-i", container, "psql", "-U", user, "-d", db, "-v", "ON_ERROR_STOP=1",
        "-c", f"\\copy reconciliation.rc_audit_trail ({col_list}) FROM STDIN WITH (FORMAT csv, HEADER true)",
    ]
    with csv_path.open("rb") as f:
        result = subprocess.run(cmd, stdin=f, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"\\copy into rc_audit_trail failed: {result.stderr.strip()}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--container", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--issue-log", type=Path, default=DEFAULT_ISSUE_LOG)
    args = parser.parse_args()

    try:
        batch_id = latest_batch(args.container, args.user, args.db)
        measured = measured_amount_variance(args.container, args.user, args.db, batch_id)
        expected = expected_amount_variance(args.container, args.user, args.db, args.issue_log)
        status = batch_status(args.container, args.user, args.db, batch_id)

        mismatch = abs(measured - expected) > TOLERANCE_ABS
        action = "INVESTIGATE" if mismatch else "NOTIFY"
        write_audit_row(args.container, args.user, args.db, batch_id, action)
    except Exception as exc:  # noqa: BLE001 - top-level safe wrapper, no silent failure
        print(f"[FAIL] feedback-report: {exc}", file=sys.stderr)
        return 1

    print(f"[INFO] batch_id={batch_id} measured_variance={measured:.2f} expected_variance={expected:.2f}")
    verdict = "[FAIL]" if mismatch else "[PASS]"
    print(f"{verdict} feedback-report: measured vs. issue-log expected variance - action={action}")

    if status == "FAIL" or mismatch:
        print(f"[FAIL] feedback-report: batch_id={batch_id} overall status={status} action={action}")
        return 1
    print(f"[PASS] feedback-report: batch_id={batch_id} overall status={status} action={action}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 5. closed-loop orchestrator script 

edit locations: `05.EL.10`

Same shape as `03-mock-data-seed.sh` / `04-mock-data-validate.sh` (`log()`/`psql_file()` helpers, per-step functions, `main()` chaining them with `||` short-circuit) but with a container check that covers *both* postgres and spark, and no drop/recreate step - DDL apply is verify-or-create only, matching [idempotency / rerun-safety](#idempotency--rerun-safety).

```bash
#!/usr/bin/env bash
# 04-closed-loop-run.sh
# Closed-loop orchestrator for feature 05: verify postgres+spark are already
# running -> apply reconciliation control-schema DDL (idempotent) ->
# reconciliation-runner.py -> feedback-report.py.
# Does NOT stand up infrastructure - fails fast if either container isn't
# already running. Batch history is append-only by design - see
# docs/features/05-ai-closed-loop-validation.md -> Design -> idempotency.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ENV_FILE="$REPO_ROOT/.env"
SECRETS_FILE="$REPO_ROOT/.secrets"
[ -f "$ENV_FILE" ] && set -a && source "$ENV_FILE" && set +a
[ -f "$SECRETS_FILE" ] && set -a && source "$SECRETS_FILE" && set +a

LOGS_DIR="${LOGS_DIR:-.dev/logs}"
TIMEZONE="${TIMEZONE:-UTC}"
TIMESTAMP_FORMAT="${TIMESTAMP_FORMAT:-%Y%m%d%H%M%S}"
VENV_DIR="${VENV_DIR:-.venv}"

SCHEMA_DIR="data/schemas"
DDL_DIR="postgresql"
SQL_GENERATOR="scripts/utils/sql-generators.py"
RUNNER="scripts/utils/reconciliation-runner.py"
FEEDBACK="scripts/utils/feedback-report.py"

POSTGRES_CONTAINER_NAME="${POSTGRES_CONTAINER_NAME:-postgres-as01}"
POSTGRES_USER="${POSTGRES_USER:?POSTGRES_USER must be set in .env}"
POSTGRES_DB="${POSTGRES_DB:?POSTGRES_DB must be set in .env}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set in .secrets}"
SPARK_CONTAINER_NAME="${SPARK_CONTAINER_NAME:-spark-master}"

FEATURE_ID="05.06"
TASK_NAME="closed-loop-run"

# schema_json|ddl_out - the 3 new files only, single-file CLI mode so
# feature 04's 9 already-closed schema/DDL pairs are never touched
RC_TABLES=(
    "rc-batch-control-schema.json|rc-batch-control-create-table.sql"
    "rc-reconciliation-results-schema.json|rc-reconciliation-results-create-table.sql"
    "rc-audit-trail-schema.json|rc-audit-trail-create-table.sql"
)

mkdir -p "$LOGS_DIR"
LOG_FILE="$(TZ="$TIMEZONE" date +"$TIMESTAMP_FORMAT")-${FEATURE_ID}-${TASK_NAME}.log"
LOG_PATH="$LOGS_DIR/$LOG_FILE"

log() {
    echo "$(TZ="$TIMEZONE" date +"%Y-%m-%d %H:%M:%S %Z") $1" | tee -a "$LOG_PATH"
}

psql_file() {
    docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" -i "$POSTGRES_CONTAINER_NAME" \
        psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 < "$1"
}

step_container_check() {
    log "[INFO] [05.06] checking postgres container '$POSTGRES_CONTAINER_NAME' is already running"
    if [ "$(docker ps --filter "name=^${POSTGRES_CONTAINER_NAME}$" --format '{{.Names}}')" != "$POSTGRES_CONTAINER_NAME" ]; then
        log "[FAIL] [05.06] postgres container not running - this script does not provision infrastructure"
        return 1
    fi
    log "[PASS] [05.06] postgres container running"

    log "[INFO] [05.06] checking spark container '$SPARK_CONTAINER_NAME' is already running"
    if [ "$(docker ps --filter "name=^${SPARK_CONTAINER_NAME}$" --format '{{.Names}}')" != "$SPARK_CONTAINER_NAME" ]; then
        log "[FAIL] [05.06] spark container not running - this script does not provision infrastructure"
        return 1
    fi
    log "[PASS] [05.06] spark container running"
    return 0
}

step_apply_ddl() {
    log "[INFO] [05.03] generating + applying reconciliation control-schema DDL"
    for entry in "${RC_TABLES[@]}"; do
        IFS='|' read -r schema_file ddl_file <<<"$entry"
        if ! "$VENV_DIR/bin/python3" "$SQL_GENERATOR" \
            --schema "$SCHEMA_DIR/$schema_file" --out "$DDL_DIR/$ddl_file" >>"$LOG_PATH" 2>&1
        then
            log "[FAIL] [05.03] DDL generation failed for $schema_file"
            return 1
        fi
        if ! psql_file "$DDL_DIR/$ddl_file" >>"$LOG_PATH" 2>&1; then
            log "[FAIL] [05.03] DDL apply failed for $ddl_file"
            return 1
        fi
        log "[PASS] [05.03] $ddl_file applied (idempotent - CREATE TABLE IF NOT EXISTS)"
    done
    return 0
}

step_run_reconciliation() {
    log "[INFO] [05.04] running reconciliation-runner.py"
    if "$VENV_DIR/bin/python3" "$RUNNER" \
        --container "$POSTGRES_CONTAINER_NAME" --user "$POSTGRES_USER" --db "$POSTGRES_DB" \
        --assessment-id assessment-1 | tee -a "$LOG_PATH"
    then
        log "[PASS] [05.04] reconciliation runner completed"
        return 0
    fi
    log "[FAIL] [05.04] reconciliation runner failed or batch status FAIL"
    return 1
}

step_feedback() {
    log "[INFO] [05.05] running feedback-report.py"
    if "$VENV_DIR/bin/python3" "$FEEDBACK" \
        --container "$POSTGRES_CONTAINER_NAME" --user "$POSTGRES_USER" --db "$POSTGRES_DB" \
        --issue-log data/mock/issue-log.csv | tee -a "$LOG_PATH"
    then
        log "[PASS] [05.05] feedback report completed"
        return 0
    fi
    log "[FAIL] [05.05] feedback report failed or ground-truth mismatch"
    return 1
}

main() {
    log "[INFO] === 04-closed-loop-run start (feature $FEATURE_ID) ==="

    step_container_check || { log "[FAIL] closed loop aborted at container check"; exit 1; }
    step_apply_ddl || { log "[FAIL] closed loop aborted at DDL apply"; exit 1; }
    step_run_reconciliation || { log "[FAIL] closed loop aborted at reconciliation runner"; exit 1; }
    step_feedback || { log "[FAIL] closed loop aborted at feedback report"; exit 1; }

    log "[PASS] closed loop completed successfully"
    log "[INFO] log written to $LOG_PATH"
    exit 0
}

main
```

`chmod +x scripts/04-closed-loop-run.sh` after creating it, matching every prior orchestrator script.

## Validate

Ran the full closed loop against the real `postgres-as01` container (no mocks), executing every one of [Test cases](#test-cases)'s 18 checks across all three validation layers (script self-report, direct DB inspection bypassing the scripts, independently-derived expected values) - all 18 PASS. `04-closed-loop-run.sh` ran clean on its first attempt with no code changes needed to any of the 5 new/extended files; the one issue surfaced was in ad-hoc test scaffolding used to force 05.TC.14's INVESTIGATE branch, not in the feature's own scripts - see 05.IS.01 below.

- **05.02/05.03** (schema JSON + DDL generator extension): `sql-generators.py`'s 3 new capabilities (`serial`/`integer` types, `default`, `foreign_keys`) generated DDL for the 3 new tables that matched the plan's expected output verbatim (05.TC.04), a live `\d` inspection of all 3 tables confirmed PK/FK/CHECK constraints exactly as designed (05.TC.02/03/05), and the DDL apply is idempotent - identical rerun, 0 rows, exit 0 (05.TC.06). Regenerating all 9 of feature 04's existing schemas with the extended generator produced byte-identical DDL (`diff` empty on all 9 files) - the extension didn't disturb any prior feature.
- **05.04** (reconciliation runner): first run inserted 1 `rc_batch_control` row + 2 `rc_reconciliation_results` rows (`row_count`, `amount`) computed against the live seeded data (2010 source / 1993 Bronze rows, $49,422,242.23 source / $48,954,502.10 Bronze) - independently re-queried with raw `COUNT`/`SUM` SQL and matched exactly (05.TC.07/08), and the variance/variance_pct/status arithmetic checked out by hand (-17 row variance = -0.8458%, -$467,740.13 amount variance = -0.9464%, both WARNING per the <0.1%/<1%/>=1% thresholds) (05.TC.09). A second run appended `batch_id=2` without touching batch 1's rows (05.TC.10).
- **05.05** (feedback report): independently hand-derived the expected amount variance from `issue-log.csv` (catalog ids 09-14: $33.48 mismatch delta - $715,774.28 dropped (missing+midnight rows) + $248,000.67 duplicated = -$467,740.13) *before* running the script - matched the runner's measured variance to the cent (05.TC.11), confirmed it read back the correct latest `batch_id` (05.TC.12), and wrote exactly 1 `rc_audit_trail` row with `action=NOTIFY` (05.TC.13). Both branches of the INVESTIGATE/NOTIFY decision were verified against the real `TOLERANCE_ABS` constant and comparison expression, plus a full end-to-end run against a synthetic fabricated batch confirmed the INVESTIGATE path really does exit non-zero (05.TC.14) - see 05.IS.01 for the scaffolding issue hit while setting that up.
- **05.06** (orchestrator): stopping the postgres container and rerunning confirmed fail-fast, exit 1, zero new batch rows (05.TC.15); a normal run executed all 4 stages in order into one log file (05.TC.16); two consecutive runs appended `batch_id=5` then `batch_id=6` with batches 1/2/4 untouched (05.TC.17); and every log file matches the `<ts>-05.06-closed-loop-run.log` naming convention (05.TC.18).

Log artifacts (`.dev/logs/`, gitignored - see commands below to inspect or reproduce):

| id | log file                                 | exit | evidence                                                | 
| -- | ---------------------------------------- | ---- | ------------------------------------------------------- | 
| 01 | `260829205935-05.06-closed-loop-run.log` | 0    | first full run, batch_id=4, all 4 stages PASS [01]      | 
| 02 | `260829205950-05.06-closed-loop-run.log` | 1    | fail-fast: postgres stopped, container check FAIL [02]  | 
| 03 | `260829210008-05.06-closed-loop-run.log` | 0    | second run, batch_id=5, appended (05.TC.17)             | 
| 04 | `260829210011-05.06-closed-loop-run.log` | 0    | third run, batch_id=6, appended (05.TC.17)              | 

01. overall summary `[PASS] closed loop completed successfully`; both dimension rows WARNING (row_count -0.8458%, amount -0.9464%).
02. stopped `postgres-as01` one command before the run - `docker ps --filter` correctly reported the container absent and aborted before the DDL/runner/feedback steps.

**secondary validation** - reproduce independently:

```bash
# full rerun of the closed loop (idempotent DDL, appends a new batch - safe to run again)
./scripts/04-closed-loop-run.sh

# inspect the latest run's log directly
tail -20 "$(ls -t .dev/logs/*-05.06-closed-loop-run.log | head -1)"

# query the live control tables yourself, bypassing the scripts entirely
source .env && source .secrets
docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "$POSTGRES_CONTAINER_NAME" \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT * FROM reconciliation.rc_batch_control ORDER BY batch_id;"
docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "$POSTGRES_CONTAINER_NAME" \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT * FROM reconciliation.rc_reconciliation_results ORDER BY batch_id;"
```

The generated scripts have no unhandled first-out exceptions of their own - all 5 new/extended files ran clean against real infrastructure on the first attempt, across every one of the 18 test cases. One issue was raised and closed below: a capture bug in this validation's own throwaway bash scaffolding (not the feature's shipped scripts), hit while forcing 05.TC.14's INVESTIGATE branch end-to-end.

**Issues**

- inventory all first out exceptions and issues encountered in this table
- for each issue, create an issue section and use this section to document diagnostics and resolution steps

| id       | seq | status | issue                                                       | 
| -------- | --- | ------ | ----------------------------------------------------------- | 
| 05.IS.01 | 01  | closed | psql -t -A still emits the INSERT ... RETURNING command tag | 

_05.IS.01 (closed) psql -t -A still emits the INSERT ... RETURNING command tag_

**problem description**

While forcing 05.TC.14's `INVESTIGATE` branch end-to-end (a real fabricated batch inserted via raw SQL, not a shipped script), the shell variable meant to capture the new `batch_id` from `INSERT ... RETURNING batch_id` via `psql -t -A -c "..."` instead captured both the `INSERT 0 1` command-completion tag and the returned value on separate lines. The two follow-up `INSERT` statements that used that variable then failed with a SQL syntax error, and the cleanup `DELETE` statements that used it also silently failed, leaving a synthetic test batch (`batch_id=3`) in `reconciliation.rc_batch_control` after the first attempt.

**exception**

```log
ERROR:  syntax error at or near "INSERT"
LINE 2: INSERT 0 1, 'row_count', 2010, 1993, -17, -0.8458, 'WARNING'...
        ^
```

**triggering actions**

Ad-hoc bash test scaffolding for 05.TC.14 (not `reconciliation-runner.py`/`feedback-report.py`, which never use `INSERT ... RETURNING` by design - see [reconciliation control schema](#reconciliation-control-schema)'s stated deviation): `TEST_BATCH_ID=$(docker exec ... psql -t -A -c "INSERT INTO reconciliation.rc_batch_control (...) VALUES (...) RETURNING batch_id;")`, then reusing `$TEST_BATCH_ID` in two more `INSERT`s and three `DELETE`s.

**hypothesis**

- use hypothesis framing until a validated fix is applied

`-t` (tuples-only) suppresses column headers and row-count footers for a plain `SELECT`, but with `INSERT ... RETURNING` psql appears to still emit the `INSERT 0 1` command tag as an extra line ahead of the returned value, since the statement is an `INSERT` at the wire-protocol level even though it also returns rows - `-t` only quiets the parts of `SELECT`-shaped output.

**diagnostic steps**

- first out exception is NOT a diagnostic step
- diagnostic steps reveal information or apply a fix
- assume re-run and validation, these are not diagnostic steps
- keep the step description brief, use the diagnostics details section to elaborate actions and learnings for each step

| id          | seq | status | step                                                                   | 
| ----------- | --- | ------ | ---------------------------------------------------------------------- | 
| 05.IS.01.01 | 01  | closed | queried rc_batch_control directly, found the stray row [01]            | 
| 05.IS.01.02 | 02  | closed | completed the fabricated batch's rows, reran 05.TC.14, deleted it [02] | 

**diagnostic details**

01. (closed) `SELECT * FROM reconciliation.rc_batch_control ORDER BY batch_id;` showed a third row (`batch_id=3, assessment_id='test-05.TC.14'`) with no matching `rc_reconciliation_results` rows - confirming the capture bug left a half-written synthetic batch behind, and ruling out any defect in the DDL/FK constraints themselves (the row inserted and stayed exactly where a manual `INSERT` without `RETURNING`-capture issues would put it).
02. (closed) Re-ran the two `rc_reconciliation_results` `INSERT`s using the literal `batch_id=3` instead of the corrupted variable, confirmed `feedback-report.py` genuinely takes the `INVESTIGATE` branch and exits 1 against this real fabricated batch (measured=$950,577,757.76 vs expected=-$467,740.13), then deleted all 3 tables' `batch_id=3` rows in FK-child-first order (`rc_audit_trail` -> `rc_reconciliation_results` -> `rc_batch_control`) to keep the append-only batch history free of test artifacts. Confirmed clean: `rc_batch_control` back to genuine rows only, `rc_reconciliation_results` and `rc_audit_trail` matching. No change to any shipped script - this was scaffolding-only, and the underlying scripts' own INVESTIGATE/exit-code behavior was verified correct in the process (05.TC.14 PASS).

## Guideline


## instructions

review and strictly follow these relevant skills when performing tasks for this feature implementation and working with this document

## relevant skills

- markdown-tables
- feature-implementation-guide
