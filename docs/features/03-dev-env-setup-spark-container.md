# Setup Spark development environment - Feature tracker
>Review the guidelines before performing any actions including edits on the document

## 03 (open) dev env setup spark container

## Contents

- [Tasks](#tasks)
- [Scope](#scope)
- [References](#references)
- [Design](#design)
  - [docker image](#docker-image)
  - [directory structure](#directory-structure)
  - [docker compose](#docker-compose)
  - [scripts](#scripts)
  - [idempotency / rerun-safety](#idempotency--rerun-safety)
  - [environment & secrets](#environment--secrets)
  - [workflow validation runner](#workflow-validation-runner)
- [Edit locations](#edit-locations)
- [Implement](#implement)
- [Validate](#validate)
- [Guideline](#guideline)

## Tasks

| id    | seq | status  | milestone                                | 
| ----- | --- | ------- | ---------------------------------------- | 
| 03.01 | 01  | open    | design                                   | 
| 03.02 | 02  | pending | spark image                              | 
| 03.03 | 03  | pending | spark docker compose                     | 
| 03.04 | 04  | pending | setup script extension                   | 
| 03.05 | 05  | pending | docker container                         | 
| 03.IS | 06  | pending | validate                                 | 

## Scope

extend the **dev env design doc**'s complete stack onto the postgres slice feature 02 already stood up --> add the Spark cluster (master + workers) and Jupyter, without disturbing the running postgres container, volume, or scripts feature 02 introduced.

- all steps can be executed by an autonomous claude ai agent with access to terminal using re-runnable idempotent scripts
- do not replace or restart the existing postgres service/volume from feature 02 — spark is composed alongside it via a second, spark-only compose file
- build a custom spark image with pyspark, delta lake, and a postgres jdbc driver baked in
- all setup scripts remain verify-or-create logic for rerun safety, and extend the same **setup script** feature 02 introduced rather than adding a parallel one
- setup script extension
    - brings up the spark cluster (master + workers) and jupyter alongside the already-running postgres container, by composing the **postgres compose file** and the **spark compose file** together
    - verifies workers have registered with the master before completing
    - mounts `data/`, `notebooks/`, and `scripts/` into the spark containers
- workflow validation runner extension
    - checks the spark master's worker count via its UI API
    - runs a trivial PySpark job, submitted inside the spark-master container, that reads `src_transaction_daily` from the postgres container over JDBC — proving cross-container connectivity end-to-end

## References

- **dev env design doc** `docs/design/development-environment.md`
- **postgres compose file** `docker/docker-compose.postgres.yml`
- **setup script** `scripts/01-dev-env-setup.sh`
- **spark image** `docker/Dockerfile.spark`
- **spark compose file** `docker/docker-compose.spark.yml`
- **spark inspect script** `scripts/utils/spark-inspect.py`

## Design

### docker image

The **spark image** is a small customization of the reference image named in the **dev env design doc** (`bitnami/spark:3.5.0`), adding the Python packages the notebooks/scripts need: `pyspark`, `delta-spark`, `faker`, the `postgresql-client` (for `psql`, matching feature 02's inspect-script pattern), and a JDBC driver jar for reaching the **postgres compose file**'s database from inside Spark jobs. The same image is reused for `spark-master`, each `spark-worker-*`, and `jupyter`, so the **spark compose file** itself only differs per service in container name and role env vars, not in what gets built.

### directory structure

```
docker/
├── docker-compose.full.yml            # original single-file reference, unused going forward
├── docker-compose.postgres.yml        # feature 02: postgres-only, still running unchanged
├── docker-compose.spark.yml           # new: spark-master + spark-worker-* + jupyter
└── Dockerfile.spark                   # new: custom spark image
notebooks/                             # new: mounted into spark-master and jupyter
scripts/
├── 01-dev-env-setup.sh                # extended: now also brings up the spark cluster
└── utils/
    ├── sql-generators.py              # feature 02, unchanged
    ├── schema-inspect.py              # feature 02, unchanged
    └── spark-inspect.py               # new: worker-count + JDBC smoke-test validation
sparksql/                              # already scaffolded, still empty - out of scope until a data-loading milestone
```

### docker compose

`docker/docker-compose.spark.yml` carries only `spark-master`, `spark-worker-*`, and `jupyter` — no `postgres` service, so it never touches the container or volume feature 02 already stood up. It is composed together with the **postgres compose file** at run time rather than merged into one file:

```bash
docker compose --env-file .env \
  -f docker/docker-compose.postgres.yml \
  -f docker/docker-compose.spark.yml \
  up -d
```

Design decisions relative to `docker-compose.full.yml`:

- **Built from the spark image once**, rather than the inline `build:` block repeated per service in `docker-compose.full.yml`.
- **`depends_on` plus a poll-based wait** on `spark-master` before workers are considered up, so a rerun after a partial failure doesn't race the master.
- **Shares the postgres compose file's network**, so Spark jobs can reach the postgres container by name over JDBC.
- **Credentials still sourced from `.env`/`.secrets`**, consistent with feature 02 — nothing new hardcoded.

### scripts

| id | alias                   | role                                    |
| -- | ------------------------- | ------------------------------------------|
| 01 | setup script                | extended: also brings up spark             |
| 02 | spark inspect script        | validation: workers + JDBC smoke test        |

01. The **setup script** (introduced in feature 02) gains a Spark stage: once the postgres table is confirmed present, it composes up the **spark compose file** alongside the **postgres compose file**, then polls the master's UI API until the expected worker count has registered.

02. The **spark inspect script** is the Spark-side counterpart to feature 02's `schema-inspect.py` — it checks worker registration and runs a smoke-test PySpark job, submitted via `docker exec ... spark-submit`, that reads `src_transaction_daily` from the postgres container over JDBC. Shells out via `docker exec`, so no local PySpark/JDBC dependency is needed on the host.

### idempotency / rerun-safety

Every step still follows the **verify-or-create** shape feature 02 established:

- **Spark containers**: checked by name via `docker ps --filter name=spark-` before composing up, mirroring feature 02's container check.
- **Worker registration**: the **setup script** polls the master's UI API in a loop with a timeout rather than a fixed `sleep`, so a rerun against an already-registered cluster returns immediately.
- **Postgres untouched**: because the **spark compose file** carries no `postgres` service, composing it up repeatedly can never recreate or restart the container/volume feature 02 owns.
- **Image**: rebuilding the **spark image** is idempotent via Docker's layer cache; the setup script only rebuilds when the Dockerfile or its pinned package versions change.

### environment & secrets

Extends the same `.env`/`.secrets` feature 02 introduced with Spark-specific, non-sensitive settings (worker count, worker memory/cores, Jupyter port). No new secrets are introduced — Jupyter runs without a token/password in this slice, matching the **dev env design doc**'s original Jupyter service, and Spark's inter-node RPC stays unauthenticated for local dev, also matching that doc.

### workflow validation runner

The **spark inspect script**:

1. Polls the spark-master UI API until either the expected worker count registers or a timeout elapses.
2. Submits a smoke-test PySpark job inside the spark-master container that opens a JDBC connection to the postgres container and reads a row count from `src_transaction_daily`.
3. Prints one `[PASS]`/`[FAIL]` line per check plus an overall summary; exits non-zero on any mismatch.
4. Runs after the **setup script**'s Spark stage, the same way feature 02's `schema-inspect.py` runs after its DB stage — so a single command validates the whole stack end-to-end.

## Edit locations

## Implement

## Validate

**Issues**

- inventory all first out exceptions and issues encountered in this table
- for each issue, create an issue section and use this section to document diagnostics and resolution steps

| id       | seq | status  | issue                                     | 
| -------- | --- | ------- | ----------------------------------------- | 
| 03.IS.01 | 01  | pending | <first out exception>                     | 

_03.IS.01 (pending) <first out exception>_

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
| ----------- | --- | ------- | ----------------------------------------- | 
| 03.IS.01.01 | 01  | pending | <diagnostic step 01>                      | 

**diagnostic details**

## Guideline

## instructions

review and strictly follow these relevant skills when performing tasks for this feature implementation and working with this document

## relevant skills

- markdown-tables
- feature-implementation-guide
