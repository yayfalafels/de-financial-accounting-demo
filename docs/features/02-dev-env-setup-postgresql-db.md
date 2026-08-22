# Setup Postgre SQL development environment - Feature tracker
>Review the guidelines before performing any actions including edits on the document 

## 02 (closed) dev env setup postgresql db

## Contents

- [Tasks](#tasks)
- [Scope](#scope)
- [References](#references)
- [Design](#design)
  - [schemas](#schemas)
  - [directory structure](#directory-structure)
  - [docker compose](#docker-compose)
  - [scripts](#scripts)
  - [idempotency / rerun-safety](#idempotency--rerun-safety)
  - [environment & secrets](#environment--secrets)
  - [workflow validation runner](#workflow-validation-runner)
- [Edit locations](#edit-locations)
- [Implement](#implement)
- [Validate](#validate)
- [Guidelines](#guidelines)

## Tasks

| id    | seq | status  | milestone                                | 
| ----- | --- | ------- | ---------------------------------------- | 
| 02.01 | 01  | closed  | docker install                           | 
| 02.02 | 02  | closed  | design                                   | 
| 02.03 | 03  | closed  | schema json                              | 
| 02.04 | 04  | closed  | generator script                         | 
| 02.05 | 05  | closed  | docker compose                           | 
| 02.06 | 06  | closed  | setup scripts                            | 
| 02.07 | 07  | closed  | docker container                         | 
| 02.IS | 08  | closed  | validate                                 | 

## Scope

develop a subset of the complete development env specified in the **dev env design doc** --> just the postgresql db on a docker container. still uses docker compose and generator scripts, but we don't go with the whole setup in one step but break it up with just first part as the postgresql db on a docker container.  

- all steps can be executed by an autonomous claude ai agent with access to terminal using re-runnable idempotent scripts
- generate the postgresql create table *.sql from the schema json using a generator script
- all setup scripts are verify-or-create logic for rerun safe
- prerequisite verification script that verifies or installs docker, python in local env
- setup script
    - sets up python virtual env
    - generate the create table sql from schema json using a utility generator script
    - creates the docker image from docker compose for the specified reference postgre image
    - stands up the db inside the container and creates the tables using the create table sql
- workflow validation runniner
    - runs the setup script
    - runs sql inspect to validate that the db is setup in the container with the expected schema

## References

- **dev env design doc** `docs/design/development-environment.md`
- **prereq check script** `scripts/00-prereq-check.sh`
- **setup script** `scripts/01-dev-env-setup.sh`
- **sql generator script** `scripts/utils/sql-generators.py`
- **workflow validate script** `scripts/02-workflow-validate.sh`

## Design

### schemas

`data/schemas/as01-source-schema.json` is the single source of truth for this slice — one table, `src_transaction_daily` (the Assessment 1 source table). It is the only schema in scope; the Bronze and reference schemas from the full assignment are deferred to later milestones.

Structure: `table_name`, `business_key`, and a `columns[]` array where each column carries `name`, `type`, `nullable`, `critical`, `description`, and optional constraint hints (`length`, `precision`/`scale`, `allowed_values`, `format`). The **sql generator script** reads this file and maps it to PostgreSQL DDL:

| id | json type                   | postgres type                  | constraint             |
| -- | --------------------------- | ------------------------------ | ---------------------- |
| 01 | `string` + `length`         | `VARCHAR(length)`              | -                      |
| 02 | `string` (no `length`)      | `TEXT`                         | -                      |
| 03 | `date`                      | `DATE`                         | -                      |
| 04 | `timestamp`                 | `TIMESTAMPTZ`                  | -                      |
| 05 | `decimal` (`precision`,`scale`) | `NUMERIC(precision,scale)` | -                      |
| 06 | `nullable: false`           | -                              | `NOT NULL`             |
| 07 | `allowed_values`            | -                              | `CHECK (col IN (...))` |
| 08 | `business_key`              | -                              | `PRIMARY KEY`          |

Schema JSON is treated as the only editable artifact for structural changes — the generated SQL file is regenerated output, not hand-edited.

### directory structure

```
data/
└── schemas/
    └── as01-source-schema.json        # source of truth for src_transaction_daily
postgresql/
└── as01-source-create-table.sql       # generated DDL, output of the generator script
docker/
├── docker-compose.full.yml            # existing full stack (spark + postgres + jupyter)
└── docker-compose.postgres.yml        # new: postgres-only subset for this slice
scripts/
├── 00-prereq-check.sh                 # verify/install docker, python
├── 01-dev-env-setup.sh                # orchestrator: venv, generate SQL, compose up, create tables
├── 02-workflow-validate.sh            # runs setup, then inspects the DB against schema JSON
└── utils/
    └── sql-generators.py              # schema JSON -> CREATE TABLE SQL
.env / .env.sample                     # POSTGRES_* connection settings
.secrets / .secrets.sample             # credentials, never committed
```

This mirrors the directory layout already scaffolded in the repo (`data/schemas/`, `postgresql/`, `scripts/`, `scripts/utils/`, `docker/`); nothing here introduces a new top-level directory.

### docker compose

`docker/docker-compose.postgres.yml` is a subset of `docker-compose.full.yml`, carrying only the `postgres` service (no `spark-master`/`spark-worker-*`/`jupyter`). Design decisions relative to the full compose file:

- **Reference image pinned**: `postgres:15-alpine`, matching the version already used in `docker-compose.full.yml`.
- **Credentials from environment, not hardcoded**: `docker-compose.full.yml` hardcodes `POSTGRES_PASSWORD: secure_password_123`; this slice instead reads `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` from `.env`/`.secrets` so nothing sensitive is checked in.
- **Fixed `container_name`**: lets scripts probe container state by name (`docker ps --filter name=...`) rather than parsing `docker compose ps` output.
- **No SQL mounted into `docker-entrypoint-initdb.d`**: table creation is intentionally *not* delegated to Postgres's init-scripts mechanism, because that mechanism only runs once, against a freshly-initialized (empty) data volume. A rerun against a container whose volume already exists would silently skip table creation, which breaks the verify-or-create contract this feature requires. Instead, the compose file only stands up an empty, healthy database; the **setup script** owns applying the generated DDL itself, after confirming the container is up, using idempotent SQL (`CREATE TABLE IF NOT EXISTS`) so it is safe whether the container is new or already running.
- **Named volume retained** (`postgres_data`) for data persistence across container restarts.

### scripts

| id | alias                     | role                 |
| -- | --------------------------- | -------------------- |
| 01 | prereq check script          | prerequisite check   |
| 02 | setup script                 | setup orchestrator   |
| 03 | sql generator script         | DDL generator        |
| 04 | workflow validate script     | validation runner    |

01. The **prereq check script** verifies Docker and Python 3.11+ are present in the local env, installing only on failure. Checks `command -v docker` / `python3 --version` first, so a rerun is a no-op once prerequisites are satisfied.
02. The **setup script** orchestrates: create/activate venv → run generator → `docker compose up -d` → apply create-table SQL. Each sub-step checks current state first (venv dir exists? container running? table exists?) before acting.
03. The **sql generator script** reads `as01-source-schema.json` and writes `postgresql/as01-source-create-table.sql`. Stateless/deterministic generator — overwriting its own output is safe, and the emitted DDL uses `IF NOT EXISTS`.
04. The **workflow validate script** runs the **setup script**, then inspects the live schema against `as01-source-schema.json` via a read-only query. Safe to rerun; exits non-zero on mismatch.

### idempotency / rerun-safety

Every step follows the same **verify-or-create** shape — check current state, act only on the gap, never assume a clean slate:

- **Local env**: the **prereq check script** checks for Docker/Python before installing anything.
- **Python venv**: the **setup script** checks whether the venv directory already exists before creating it.
- **Container**: checked by name via `docker ps --filter name=...` before `docker compose up -d` (compose itself is already idempotent, but the explicit check gives the agent a clear state signal to reason from).
- **Schema**: the generator's output DDL uses `CREATE TABLE IF NOT EXISTS`, and is regenerated (overwritten) fresh from the schema JSON on every run rather than patched.
- **Data**: out of scope for this slice — no seed/mock data is loaded, only the empty table structure.

This favors explicit state checks with human/agent-readable output at each step over try/fail/recover error handling, so an autonomous agent can decide what to do next from command output alone.

### environment & secrets

`.env`/`.env.sample` and `.secrets`/`.secrets.sample` hold `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, and `POSTGRES_PORT`. The **setup script** sources `.env` before invoking `docker compose`, so the same credentials flow through container creation and the script's own DB connection when applying DDL. Nothing sensitive is hardcoded in `docker-compose.postgres.yml` or committed to the repo — only the `.sample` files are tracked.

### workflow validation runner

The **workflow validate script**:

1. Runs the **setup script** end-to-end (so validation always exercises the real setup path, not a shortcut).
2. Connects to the running container and queries `information_schema.columns` for `public.src_transaction_daily`.
3. Diffs the live column list (name, type, nullable) against the expectations in `as01-source-schema.json`.
4. Prints a PASS/FAIL line per column and an overall summary; exits non-zero on any mismatch.

A non-zero exit here is meant to gate later milestones (e.g. loading mock Bronze data) rather than being investigated ad hoc — it should be the first thing checked if a downstream step fails unexpectedly.

## Edit locations

| id    | path                                       | change                       | 
| ----- | ------------------------------------------ | ----------------------------- | 
| 01    | `.env` / `.env.sample`                     | added POSTGRES_* + VENV_DIR   | 
| 02    | `.secrets` / `.secrets.sample`             | added POSTGRES_PASSWORD       | 
| 03    | `pyproject.toml`                           | new, venv dependency manifest | 
| 04    | `docker/docker-compose.postgres.yml`       | new, postgres-only subset     | 
| 05    | `scripts/00-prereq-check.sh`               | new, prereq check script      | 
| 06    | `scripts/01-dev-env-setup.sh`              | new, setup orchestrator       | 
| 07    | `scripts/02-workflow-validate.sh`          | new, validation runner        | 
| 08    | `scripts/utils/sql-generators.py`          | new, DDL generator            | 
| 09    | `scripts/utils/schema-inspect.py`          | new, live-schema diff utility | 
| 10    | `postgresql/as01-source-create-table.sql`  | generated output, was empty   | 

## Implement

Implemented per the **Design** section as specified, in dependency order: `00-prereq-check.sh` verifies/installs
Docker and Python 3.11+ (including the `python3.14-venv` apt package, needed by `ensurepip` for venv creation) →
`01-dev-env-setup.sh` orchestrates venv → DDL generation (`sql-generators.py`, stdlib-only) → `docker compose up -d`
on `docker-compose.postgres.yml` → `pg_isready` wait → DDL apply via `docker exec ... psql` (credentials passed
through `PGPASSWORD`, never hardcoded) → `02-workflow-validate.sh` reruns setup then diffs the live
`information_schema.columns` for `public.src_transaction_daily` against `as01-source-schema.json` via
`schema-inspect.py` (also stdlib-only, shells out to the `psql` client already inside the postgres:15-alpine
image rather than adding a `psycopg2` host dependency).

One deviation from the Design doc's directory structure: dependencies are declared in `pyproject.toml`
(`[project].dependencies`) instead of a `requirements.txt`, per user direction mid-implementation. The setup
script reads it with stdlib `tomllib` and installs only if the list is non-empty (currently empty - the venv
step still runs for future milestones, but there is nothing to `pip install` yet).

## Validate

Ran the full chain twice against a real Docker daemon (no mocks): first run exercised every "create" path
(venv creation, `python3.14-venv` apt install, container bring-up, DDL apply); second run confirmed every
"verify" path short-circuits (venv reused, container already running -> compose up skipped, DDL re-applied
idempotently via `IF NOT EXISTS`). `02-workflow-validate.sh` diffed all 14 columns of `public.src_transaction_daily`
against `as01-source-schema.json` (name, postgres type, nullable) - all PASS, exit 0.

Log artifacts (`.dev/logs/`, gitignored - see commands below to inspect or reproduce):

| id | log file                                        | exit | evidence                            | 
| -- | ------------------------------------------------ | ---- | ------------------------------------ | 
| 01 | `260822192831-02.06-prereq-check.log`             | 0    | installed python3.14-venv, then PASS | 
| 02 | `260822192858-02.06-dev-env-setup.log`            | 0    | first run, all steps PASS            | 
| 03 | `260822192931-02.IS-workflow-validate.log`        | 0    | 14/14 columns PASS [01]              | 
| 04 | `260822192939-02.06-prereq-check.log`             | 0    | rerun, all already satisfied         | 
| 05 | `260822192940-02.IS-workflow-validate.log`        | 0    | rerun, 14/14 columns PASS again [01] | 

01. **schema validated** every column in `src_transaction_daily` (transaction_id, account_id, transaction_date,
    posting_date, transaction_type, currency_code, transaction_amount, local_currency_amount, exchange_rate,
    branch_code, product_code, source_system, ingestion_file, source_extract_ts) matched expected postgres
    type and nullability, with the overall summary line `[PASS] schema validation: public.src_transaction_daily
    matches as01-source-schema.json`.

**secondary validation** - reproduce independently:

```bash
# full rerun of setup + schema validation (idempotent, safe to run again)
./scripts/02-workflow-validate.sh

# inspect the latest validate log directly
tail -20 "$(ls -t .dev/logs/*-02.IS-workflow-validate.log | head -1)"

# query the live schema yourself, bypassing the scripts entirely
source .env && source .secrets
docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "$POSTGRES_CONTAINER_NAME" \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\d public.src_transaction_daily"
```

The generated scripts have no unhandled first-out exceptions of their own (the one anticipated gap,
`python3.14-venv` missing `ensurepip`, was resolved automatically by `00-prereq-check.sh` in-band as designed).
One issue was raised and closed below: an environment discrepancy on the manual secondary-validation command
(not the feature's own scripts, which passed in both environments throughout).

**Issues**

- inventory all first out exceptions and issues encountered in this table
- for each issue, create an issue section and use this section to document diagnostics and resolution steps

| id       | seq | status  | issue                                     | 
| -------- | --- | ------- | ----------------------------------------- | 
| 02.IS.01 | 01  | closed  | raw docker exec psql command: empty output for user | 

_02.IS.01 (closed) raw docker exec psql command: empty output for user_

**problem description**

The manual secondary-validation command from `## Validate` (`docker exec -e PGPASSWORD=... psql -c "\d ..."`,
run outside the feature's own scripts) printed nothing at all in the user's terminal - no table output, no
error text. The same command, and the feature's own `02-workflow-validate.sh`, both pass with full output in
the agent's environment, including from a freshly isolated subshell with stdout/stderr captured separately.

**exception**

```log
<no error captured - user reports zero output, not an error message>
```

**triggering actions**

Pasting the `## Validate` secondary-validation `docker exec ... psql -c "\d public.src_transaction_daily"`
block directly into the user's own terminal, after an earlier `-it` TTY flag issue (already fixed - see
diagnostic step 01) had been ruled out as the cause.

**hypothesis**

- use hypothesis framing until a validated fix is applied

Most likely: `source .env && source .secrets` ran in a different shell context than the `docker exec` line
(different paste, different working directory, or a non-persistent shell), leaving `$POSTGRES_CONTAINER_NAME`
/ `$POSTGRES_USER` / `$POSTGRES_PASSWORD` unset, so `docker exec` failed before `psql` ever ran. Less likely:
the user's terminal/tool captures stdout but suppresses stderr, masking a real docker/psql error as silence.

**diagnostic steps**

- first out exception is NOT a diagnostic step
- diagnostic steps reveal information or apply a fix
- assume re-run and validation, these are not diagnostic steps
- keep the step description brief, use the diagnostics details section to elaborate actions and learnings for each step

| id          | seq | status  | step                                      | 
| ----------- | --- | ------- | ----------------------------------------- | 
| 02.IS.01.01 | 01  | closed  | reproduce raw command in isolated subshell, capture streams | 
| 02.IS.01.02 | 02  | closed  | user reruns self-verifying diagnostic block, reports output | 

**diagnostic details**

01. (closed) Ran the corrected command (`-it` dropped) in a brand-new `bash -c '...'` subshell with `.env`/
    `.secrets` sourced immediately before it, stdout and stderr captured to tmp diagnostic files (per the
    diagnostic-dir convention; removed after the issue closed). Result: full 14-column table + indexes + check
    constraint on stdout, empty stderr, exit 0. Rules out the command/container/credentials themselves being
    broken; narrows the cause to the user's shell context.
02. (closed) User confirmed the leading hypothesis directly: their terminal/tool was executing the pasted
    lines independently rather than as one continuous shell session, so `source .env && source .secrets` never
    carried forward to the `docker exec` line - `$POSTGRES_CONTAINER_NAME`/`$POSTGRES_USER`/`$POSTGRES_PASSWORD`
    were unset when `docker exec` ran. Fix on the user's side: join the block with `;` (or `&&`) between lines
    so it executes as a single command in their environment, rather than relying on newline-separated
    persistence. No code or script change needed - this was environment-specific, not a defect in the feature's
    scripts (`01-dev-env-setup.sh` / `02-workflow-validate.sh` were never affected, since each sources its own
    `.env`/`.secrets` internally within the same script invocation).

## Guideline

## instructions

review and strictly follow these relevant skills when performing tasks for this feature implementation and working with this document

## relevant skills

- markdown-tables
- feature-implementation-guide