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
| 03.01 | 01  | closed  | design                                   | 
| 03.02 | 02  | closed  | spark image                              | 
| 03.03 | 03  | closed  | spark docker compose                     | 
| 03.04 | 04  | closed  | setup script extension                   | 
| 03.05 | 05  | closed  | docker container                         | 
| 03.06 | 06  | closed  | spark sql query e2e run                  | 
| 03.IS | 07  | closed  | validate                                 | 
| 03.07 | 08  | closed  | manual validate                          | 

## Revisions

| id        | date       | task  | change                                    | 
| --------- | ---------- | ----- | ------------------------------------------ | 
| 03.01.R01 | 2026-08-23 | 03.01 | merged postgres into single compose file  | 

**03.01.R01** postgres and spark services are combined into one `docker/docker-compose.yml` file instead of two files composed together with `-f` at run time. The existing `postgres_as01_data` named volume and the `postgres-as01` compose project name are carried over unchanged, so the merge reuses feature 02's existing data rather than creating a new volume.

## Scope

extend the **dev env design doc**'s complete stack onto the postgres slice feature 02 already stood up --> add the Spark cluster (master + workers) and Jupyter into the same docker compose file, without losing the running postgres container's volume or data.

- all steps can be executed by an autonomous claude ai agent with access to terminal using re-runnable idempotent scripts
- postgres, spark, and jupyter are defined together in one docker compose file; the postgres service block and its named volume are carried over from feature 02 unchanged so the merge reuses the existing data rather than recreating it
- build a custom spark image with pyspark, delta lake, and a postgres jdbc driver baked in
- all setup scripts remain verify-or-create logic for rerun safety, and extend the same **setup script** feature 02 introduced rather than adding a parallel one
- setup script extension
    - brings up the full stack — postgres, spark cluster (master + workers), and jupyter — from the single merged compose file
    - verifies workers have registered with the master before completing
    - mounts `data/`, `notebooks/`, and `scripts/` into the spark containers
- workflow validation runner extension
    - checks the spark master's worker count via its UI API
    - runs a trivial PySpark job, submitted inside the spark-master container, that reads `src_transaction_daily` from the postgres container over JDBC — proving cross-container connectivity end-to-end

## References

- **dev env design doc** `docs/design/development-environment.md`
- **docker compose file** `docker/docker-compose.yml`
- **setup script** `scripts/01-dev-env-setup.sh`
- **spark image** `docker/Dockerfile.spark`
- **spark inspect script** `scripts/utils/spark-inspect.py`

## Design

### docker image

The **spark image** is a small customization of the reference image named in the **dev env design doc** (`bitnami/spark:3.5.0`), adding the Python packages the notebooks/scripts need: `pyspark`, `delta-spark`, `faker`, the `postgresql-client` (for `psql`, matching feature 02's inspect-script pattern), and a JDBC driver jar for reaching the postgres service's database from inside Spark jobs. The same image is reused for `spark-master`, each `spark-worker-*`, and `jupyter`, so the **docker compose file** itself only differs per service in container name and role env vars, not in what gets built.

### directory structure

```
docker/
├── docker-compose.full.yml            # original single-file reference, unused going forward
├── docker-compose.yml                 # postgres + spark-master + spark-worker-* + jupyter
└── Dockerfile.spark                   # new: custom spark image
notebooks/                             # new: mounted into spark-master and jupyter
scripts/
├── 01-dev-env-setup.sh                # extended: now also brings up the spark cluster
└── utils/
    ├── sql-generators.py              # generates sql create commands
    ├── schema-inspect.py              # inspect sql schema
    └── spark-inspect.py               # new: worker-count + JDBC smoke-test validation
sparksql/                              # already scaffolded, still empty - out of scope until a data-loading milestone
```

### docker compose

`docker/docker-compose.yml` carries `postgres`, `spark-master`, `spark-worker-*`, and `jupyter` together, brought up with a single command:

```bash
docker compose --env-file .env \
  -f docker/docker-compose.yml \
  up -d
```

The `postgres` service block is extended on — same image, environment, ports, and volume mount — so its config never diverges and Compose has no reason to recreate the container. Preserving the existing `postgres_as01_data` volume and its data depends on two things staying the same:

- the top-level `name: postgres-as01` project field, which Compose uses to resolve/prefix the volume (`postgres-as01_postgres_as01_data`)
- the volume name `postgres_as01_data` mounted at `/var/lib/postgresql/data`

As long as both match, `docker compose up` on the merged file attaches to the same existing volume instead of creating a new one.

Design decisions relative to `docker-compose.full.yml`:

- **Built from the spark image once**, rather than the inline `build:` block repeated per service in `docker-compose.full.yml`.
- **`depends_on` plus a poll-based wait** on `spark-master` before workers are considered up, so a rerun after a partial failure doesn't race the master.
- **All services share one Compose network by default**, so Spark jobs can reach the postgres container by name over JDBC without extra network config.
- **Credentials still sourced from `.env`/`.secrets`**, consistent with feature 02 — nothing new hardcoded.

### scripts

| id | alias                   | role                                    |
| -- | ------------------------- | ------------------------------------------|
| 01 | setup script                | extended: also brings up spark             |
| 02 | spark inspect script        | validation: workers + JDBC smoke test        |

01. The **setup script**  gains a Spark stage: once the postgres table is confirmed present, it composes up the merged **docker compose file**, bringing up `spark-master`, `spark-worker-*`, and `jupyter` alongside the already-running `postgres` service, then polls the master's UI API until the expected worker count has registered.

02. The **spark inspect script** is the Spark-side counterpart to feature 02's `schema-inspect.py` — it checks worker registration and runs a smoke-test PySpark job, submitted via `docker exec ... spark-submit`, that reads `src_transaction_daily` from the postgres container over JDBC. Shells out via `docker exec`, so no local PySpark/JDBC dependency is needed on the host.

### idempotency / rerun-safety

Every step still follows the **verify-or-create** shape feature 02 established:

- **Spark containers**: checked by name via `docker ps --filter name=spark-` before composing up, mirroring feature 02's container check.
- **Worker registration**: the **setup script** polls the master's UI API in a loop with a timeout rather than a fixed `sleep`, so a rerun against an already-registered cluster returns immediately.
- **Postgres untouched**: the `postgres` service block in the merged compose file is byte-for-byte what feature 02 defined, so `docker compose up` never sees a config diff for it and leaves the running container and its volume alone — adding the spark services to the same file doesn't trigger a recreate.
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

| id | path                                     | change                                                          | 
| -- | ----------------------------------------- | ---------------------------------------------------------------- | 
| 01 | `.env` / `.env.sample`                    | add Spark/Jupyter ports, worker resources, JDBC driver version   | 
| 02 | `docker/docker-compose.yml`               | new: merged postgres + spark-master + spark-worker-1/2 + jupyter | 
| 03 | `docker/docker-compose.postgres.yml`      | removed, superseded by `docker-compose.yml`                      | 
| 04 | `docker/Dockerfile.spark`                 | new: custom spark image + baked-in JDBC driver jar                | 
| 05 | `notebooks/`                              | new: empty dir, mounted into spark-master and jupyter             | 
| 06 | `scripts/01-dev-env-setup.sh`             | extended: spark stage - compose up, poll worker registration      | 
| 07 | `scripts/02-workflow-validate.sh`         | extended: run spark-inspect after schema-inspect                  | 
| 08 | `scripts/utils/spark-inspect.py`          | new: worker-count + JDBC smoke-test validation                    | 
| 09 | `scripts/utils/spark-jdbc-smoketest.py`   | new: PySpark job, runs inside spark-master via spark-submit       | 
| 10 | `docker/entrypoint.sh`                    | new: SPARK_MODE role selector (master/worker/exec passthrough)    | 
| 11 | `docker/docker-compose.yml`               | mount `../src:/src` into spark-master and jupyter                 | 
| 12 | `src/pyspark/03.08.01-pyspark-select-source.py`   | new: manual validation, JDBC select               | 
| 13 | `src/pyspark/03.08.02-sparksql-groupby-source.py` | new: manual validation, Spark SQL GROUP BY         | 

## Implement

Implemented per the **Design** section in dependency order, each step referencing its **Edit locations** id:

01. **`.env` / `.env.sample`** (01) - added, alongside the existing `POSTGRES_*` block: `SPARK_MASTER_PORT=7077`, `SPARK_MASTER_UI_PORT=8080`, `SPARK_WORKER_COUNT=2`, `SPARK_WORKER_MEMORY=2G`, `SPARK_WORKER_CORES=2`, `JUPYTER_PORT=8888`, `JDBC_DRIVER_VERSION=42.7.3`. No new secrets - Jupyter stays tokenless and Spark's inter-node RPC stays unauthenticated, per Design -> environment & secrets.

02. **`docker/Dockerfile.spark`** (04) + **`docker/entrypoint.sh`** (10) - `USER root`, install `postgresql-client` via apt (matching feature 02's inspect-script pattern), pip install pinned `pyspark==3.5.0 delta-spark==3.0.0 faker==19.0.0` (the versions the **dev env design doc** pins), then `curl` the Postgres JDBC driver `postgresql-${JDBC_DRIVER_VERSION}.jar` from Maven Central straight into Spark's `jars/` dir so it is on the classpath for every `spark-submit`/`pyspark` call without a `--jars` flag. `mkdir -p /data /notebooks /scripts` + `chmod -R 777`, matching the mount points below. `entrypoint.sh` reads `SPARK_MODE` and execs `spark-class org.apache.spark.deploy.master.Master` or `...worker.Worker $SPARK_MASTER_URL` in the foreground, or passes through `"$@"` for any other role (the jupyter service's `command:`) - this is what lets one image serve spark-master, each spark-worker-*, and jupyter, differing only by env vars/command per Design -> docker image.

03. **`docker/docker-compose.yml`** (02) - built from the existing `postgres` service verbatim (same `container_name`, env, ports, `postgres_as01_data` volume, healthcheck) plus `spark-master` (`SPARK_MODE=master`, ports `${SPARK_MASTER_PORT}:7077` / `${SPARK_MASTER_UI_PORT}:8080` / `4040:4040`), `spark-worker-1` / `spark-worker-2` (`SPARK_MODE=worker`, `SPARK_MASTER_URL=spark://spark-master:7077`, `SPARK_WORKER_MEMORY`/`SPARK_WORKER_CORES` from `.env`, `depends_on: [spark-master]`), and `jupyter` (same image, `command:` launches `jupyter notebook` with the ports/tokens described below, `depends_on: [spark-master, postgres]`). All four Spark-family services mount `../data:/data` and `../notebooks:/notebooks`; `spark-master` and `jupyter` also mount `../scripts:/scripts`. The top-level `name: postgres-as01` project field and the volume name `postgres_as01_data` were kept exactly as they were in feature 02's file - confirmed by inspecting the running container after every compose-up in this feature: its `CreatedAt` timestamp never changed. No explicit `networks:` block was needed - services in one Compose file already share the project's default network, so `spark-master` reaches `postgres` by service name.

04. **`docker/docker-compose.postgres.yml`** (03) - deleted; its content lives on as the `postgres` service block inside `docker-compose.yml`, and `scripts/01-dev-env-setup.sh` was repointed at the merged file in the same change.

05. **`notebooks/`** (05) - created as an empty directory (no placeholder file needed - `sparksql/` is already scaffolded the same way and isn't git-tracked either, since git doesn't track empty directories).

06. **`scripts/01-dev-env-setup.sh`** (06) - extended with a `step_spark_up()` run after the existing postgres steps, following the same safe-runnable-wrapper shape as `step_container_up()`:
    a. checks `docker ps --filter name=spark-` for the three expected `spark-*` containers before composing up (verify-or-create, mirroring the existing postgres check - it deliberately does *not* reuse the postgres check, since postgres being up no longer implies spark is),
    b. runs `docker compose --env-file "$ENV_FILE" -f docker/docker-compose.yml up -d`,
    c. polls `http://localhost:${SPARK_MASTER_UI_PORT}/json/` (the master's REST endpoint, returns `{"aliveworkers": N, ...}`) in a loop with a timeout, succeeding once `aliveworkers >= $SPARK_WORKER_COUNT`.

07. **`scripts/utils/spark-jdbc-smoketest.py`** (09) - a small PySpark script that lives under `/scripts/utils/` inside the containers (already mounted). Builds a `SparkSession`, reads `src_transaction_daily` via `spark.read.jdbc(url="jdbc:postgresql://postgres:5432/$POSTGRES_DB", table="src_transaction_daily", properties={"user": ..., "password": ..., "driver": "org.postgresql.Driver"})`, prints `ROW_COUNT=N`, exits 0/1. The Postgres password is read from the `POSTGRES_PASSWORD` environment variable rather than a CLI arg, so it never shows up in a `ps`/`docker exec` listing.

08. **`scripts/utils/spark-inspect.py`** (08) - the Spark-side counterpart to `schema-inspect.py`, same stdlib-only shape (argparse + subprocess, no local PySpark/JDBC dependency on the host):
    a. polls the master UI JSON endpoint for `aliveworkers` (same check as step 06c, so the setup script and the inspect script share one source of truth for "is the cluster up"),
    b. runs `docker exec -e POSTGRES_PASSWORD=... spark-master spark-submit --master spark://spark-master:7077 /scripts/utils/spark-jdbc-smoketest.py ...`, parses the `ROW_COUNT=` line from stdout,
    c. prints one `[PASS]`/`[FAIL]` line per check (worker count, JDBC read) plus an overall summary; non-zero exit on any mismatch.

09. **`scripts/02-workflow-validate.sh`** (07) - after the existing `schema-inspect.py` call, added a call to `spark-inspect.py` with the same container/credential args (also now sources `.secrets`, needed for `POSTGRES_PASSWORD`), so one command (`./scripts/02-workflow-validate.sh`) validates the postgres schema, spark cluster health, and cross-container JDBC connectivity end-to-end.

**Deviations from Design** - two, both forced by upstream packages having moved since the **dev env design doc** was written, discovered by actually building the image rather than assumed:

- **Base image**: `bitnami/spark:3.5.0` (Design's named reference image) is no longer a free image on Docker Hub - `docker pull bitnami/spark:3.5.0` returns "not found", and the Docker Hub API describes the repo as now requiring a paid "Bitnami Secure Images" subscription. Swapped the base to `python:3.11-slim-bookworm` (Debian 12, so `openjdk-17-jre-headless` is still installable - the newer `python:3.11-slim` defaults to Debian trixie, which only ships `openjdk-21`, ahead of what Spark 3.5.0 officially supports) plus `pip install pyspark==3.5.0`, which bundles the same Spark 3.5.0 `spark-class`/standalone-cluster scripts under `site-packages/pyspark` - no proprietary distribution involved. `docker/entrypoint.sh` (Edit locations id 10) replaces the role-selection logic bitnami's image provided out of the box; it was already anticipated in the **dev env design doc**'s original directory structure (`docker/entrypoint.sh # Spark startup`), so this isn't a new artifact type, just built earlier than that doc assumed.
- **Jupyter packages**: the versions in the **dev env design doc**'s appendix (`jupyter==1.0.0`, `jupyterlab==4.0.0`) install a `notebook`/`jupyter_server`/`traitlets` combination that crashes on startup (`TypeError: warn() missing 1 required keyword-only argument: 'stacklevel'`, from a `notebook`/`jupyter_server` incompatibility - see Validate -> Issues 03.IS.03). Pinned `notebook==7.0.6` alone instead, which resolves a compatible dependency set. Its config namespace also renamed `--NotebookApp.*` flags to `--ServerApp.*`, reflected in `docker-compose.yml`'s `jupyter` service `command:`.

## Validate

Ran the full chain against a real Docker daemon (no mocks), from a repo state where feature 02's postgres container was already up with real data (2,010 rows in `src_transaction_daily`, seeded by feature 04): `01-dev-env-setup.sh` first attempt hit two build-time exceptions (below), each fixed and rebuilt in place; the third attempt built clean (`docker compose up completed`, image build ~3 min) and both workers registered (`2/2 alive workers`). Confirmed throughout - after every compose-up in this feature, including the two rebuilds and two full reruns - that `postgres-as01`'s `CreatedAt` timestamp never changed (`2026-08-22 19:29:21`, from before this feature started) and its volume stayed `postgres-as01_postgres_as01_data`: the merge never recreated the container or touched its data. `02-workflow-validate.sh` then ran end-to-end twice: all 14 `src_transaction_daily` columns PASS against `as01-source-schema.json`, worker registration PASS (2/2), and the JDBC smoke test PASS, reading `ROW_COUNT=2010` from inside `spark-master` over JDBC to the `postgres` service - matching the row count queried directly via `psql` outside Spark entirely, proving the cross-container connectivity end-to-end.

Log artifacts (`.dev/logs/`, gitignored - see commands below to inspect or reproduce):

| id | log file                                        | exit | evidence                                            | 
| -- | ------------------------------------------------ | ---- | ----------------------------------------------------- | 
| 01 | `260823155804-02.06-dev-env-setup.log`            | 1    | build FAIL - openjdk-17 unavailable [01]               | 
| 02 | `260823155844-02.06-dev-env-setup.log`            | 0    | build PASS, 2/2 workers registered [02]                | 
| 03 | `260823160628-02.IS-workflow-validate.log`        | 0    | 14/14 columns + 2/2 workers + JDBC ROW_COUNT=2010 [03] | 
| 04 | `260823160654-02.06-dev-env-setup.log`            | 0    | rerun, all steps short-circuit (verify-or-create) [04] | 
| 05 | `260823160748-02.IS-workflow-validate.log`        | 0    | rerun, all checks PASS again [03]                      | 

01. **build failure, resolved in-band**: `docker/Dockerfile.spark`'s first version (`FROM python:3.11-slim`) failed installing `openjdk-17-jre-headless` - Debian's newer `trixie` default only ships `openjdk-21`. Fixed by pinning `python:3.11-slim-bookworm` (see Implement -> Deviations from Design); not re-run standalone, superseded by log 02.
02. **first clean build** produced `spark-master`, `spark-worker-1`, `spark-worker-2` and the merged `postgres`/spark/jupyter compose stack, with the overall summary line `[PASS] dev env setup completed successfully`.
03. **full workflow validation**, both runs identical: `[PASS] schema validation: public.src_transaction_daily matches as01-source-schema.json`, `[PASS] worker registration: 2/2 alive workers`, `[PASS] JDBC smoke test: public.src_transaction_daily ROW_COUNT=2010`, `[PASS] spark-inspect: cluster healthy, JDBC connectivity to postgres confirmed`.
04. **idempotency rerun** of the setup script alone: postgres container check, spark container check, and worker poll all short-circuit to PASS in ~1s, confirming the verify-or-create shape holds with everything already up.

**secondary validation** - reproduce independently:

```bash
# full rerun of setup + schema + spark validation (idempotent, safe to run again)
./scripts/02-workflow-validate.sh

# inspect the latest validate log directly
tail -20 "$(ls -t .dev/logs/*-02.IS-workflow-validate.log | head -1)"

# confirm postgres was never recreated by the spark merge - CreatedAt should predate this feature
docker inspect postgres-as01 --format '{{.Created}}'
docker volume ls | grep postgres-as01

# check spark-master's worker registration yourself, bypassing the scripts entirely
curl -s http://localhost:${SPARK_MASTER_UI_PORT:-8080}/json/ | python3 -m json.tool
```

**Issues**

- inventory all first out exceptions and issues encountered in this table
- for each issue, create an issue section and use this section to document diagnostics and resolution steps

| id       | seq | status | issue                                                   | 
| -------- | --- | ------ | -------------------------------------------------------- | 
| 03.IS.01 | 01  | closed | bitnami/spark:3.5.0 no longer free on Docker Hub          | 
| 03.IS.02 | 02  | closed | openjdk-17-jre-headless unavailable on python:3.11-slim   | 
| 03.IS.03 | 03  | closed | jupyter==1.0.0/jupyterlab==4.0.0 crash on startup          | 

_03.IS.01 (closed) bitnami/spark:3.5.0 no longer free on Docker Hub_

**problem description**

The **dev env design doc**'s named reference image, `bitnami/spark:3.5.0`, could not be pulled - Docker confirmed the repository exists but the tag resolves to nothing accessible without a paid subscription.

**exception**

```log
$ docker pull bitnami/spark:3.5.0
Error response from daemon: failed to resolve reference "docker.io/bitnami/spark:3.5.0": docker.io/bitnami/spark:3.5.0: not found

$ curl -s https://hub.docker.com/v2/repositories/bitnami/spark/
{"status_description":"active", ... "full_description":"# Bitnami Secure Image for spark\n\nThis image is no
longer available for free through Docker Hub. This image is available as a built OCI artifact ... through a
commercial subscription of Bitnami Secure Images. ..."}
```

**triggering actions**

`docker pull bitnami/spark:3.5.0`, run to warm the base image before the first `docker compose up -d` build, per the **Design** section's named reference image.

**hypothesis**

- use hypothesis framing until a validated fix is applied

Bitnami (VMware/Broadcom) moved its image catalog behind a paid subscription tier sometime after the **dev env design doc** was written; confirmed directly via the Docker Hub API's repository description rather than inferred, so no longer a hypothesis by the time it was recorded here.

**diagnostic steps**

- first out exception is NOT a diagnostic step
- diagnostic steps reveal information or apply a fix
- assume re-run and validation, these are not diagnostic steps
- keep the step description brief, use the diagnostics details section to elaborate actions and learnings for each step

| id          | seq | status | step                                                | 
| ----------- | --- | ------ | ------------------------------------------------------ | 
| 03.IS.01.01 | 01  | closed | confirm via Docker Hub API, not just the pull error      | 
| 03.IS.01.02 | 02  | closed | swap base image, see Implement -> Deviations from Design | 

**diagnostic details**

01. (closed) `curl https://hub.docker.com/v2/repositories/bitnami/spark/` confirmed `status_description: active` but a `full_description` explicitly stating the image is subscription-only - ruling out a transient pull error or registry outage.
02. (closed) Rebuilt `docker/Dockerfile.spark` on `python:3.11-slim` + `pip install pyspark==3.5.0`, which bundles the same Spark 3.5.0 binaries under `site-packages/pyspark`. Immediately hit 03.IS.02 on the first build attempt, resolved separately below.

_03.IS.02 (closed) openjdk-17-jre-headless unavailable on python:3.11-slim_

**problem description**

`docker/Dockerfile.spark`'s `apt-get install openjdk-17-jre-headless` failed on the `python:3.11-slim` base image chosen to replace `bitnami/spark:3.5.0` (03.IS.01).

**exception**

```log
#7 4.201 Package openjdk-17-jre-headless is not available, but is referred to by another package.
#7 4.201 However the following packages replace it:
#7 4.201   openjdk-21-jre openjdk-21-jdk-headless
#7 4.206 E: Package 'openjdk-17-jre-headless' has no installation candidate
target jupyter: failed to solve: process "/bin/sh -c apt-get update && apt-get install -y --no-install-recommends
openjdk-17-jre-headless postgresql-client curl procps && rm -rf /var/lib/apt/lists/*" did not complete
successfully: exit code: 100
```

Captured in `.dev/logs/260823155804-02.06-dev-env-setup.log`.

**triggering actions**

`./scripts/01-dev-env-setup.sh`, first run after switching the base image away from `bitnami/spark:3.5.0`.

**hypothesis**

- use hypothesis framing until a validated fix is applied

Plain `python:3.11-slim` tracks Debian's current `trixie` release, which no longer ships `openjdk-17` at all (only `openjdk-21`) - ahead of the Java versions Spark 3.5.0 officially supports (8/11/17).

**diagnostic steps**

- first out exception is NOT a diagnostic step
- diagnostic steps reveal information or apply a fix
- assume re-run and validation, these are not diagnostic steps
- keep the step description brief, use the diagnostics details section to elaborate actions and learnings for each step

| id          | seq | status | step                                                    | 
| ----------- | --- | ------ | ---------------------------------------------------------- | 
| 03.IS.02.01 | 01  | closed | pin `python:3.11-slim-bookworm` (Debian 12, has openjdk-17)  | 
| 03.IS.02.02 | 02  | closed | rerun setup script, confirm clean build + 2/2 workers         | 

**diagnostic details**

01. (closed) Debian 12 "bookworm" still packages `openjdk-17-jre-headless`; `python:3.11-slim-bookworm` pins to that release explicitly instead of floating to whatever Debian `slim` currently defaults to.
02. (closed) Reran `./scripts/01-dev-env-setup.sh` end-to-end: build completed (~3 min), `spark-master` + `spark-worker-1` + `spark-worker-2` came up, and the worker-registration poll reached `2/2` - captured in `.dev/logs/260823155844-02.06-dev-env-setup.log`.

_03.IS.03 (closed) jupyter==1.0.0/jupyterlab==4.0.0 crash on startup_

**problem description**

The `jupyter-notebook` container built and started but its process exited immediately (`Exited (1)`); the **dev env design doc**'s pinned `jupyter==1.0.0` + `jupyterlab==4.0.0` pulled in a `notebook`/`jupyter_server` combination that crashes before serving any requests. Discovered via `docker logs jupyter-notebook`, not via the automated validation scripts - jupyter's own health isn't part of the workflow validation runner's scope (only worker registration + JDBC connectivity are), so this never blocked `02-workflow-validate.sh`.

**exception**

```log
File ".../notebook/traittypes.py", line 238, in _resolve_classes
    warn(f"{klass} is not importable. Is it installed?", ImportWarning)
TypeError: warn() missing 1 required keyword-only argument: 'stacklevel'
```

**triggering actions**

`docker logs jupyter-notebook`, run to spot-check the one service the automated workflow-validate script doesn't cover, after `01-dev-env-setup.sh` had already reported overall success.

**hypothesis**

- use hypothesis framing until a validated fix is applied

The `notebook` package resolved by `jupyter==1.0.0` at build time (unpinned itself, so it floats to whatever is current on PyPI) is a newer major version than `jupyterlab==4.0.0` was tested against, and its `traittypes` compatibility shim calls `warnings.warn()` with an argument shape older `traitlets` versions don't expect - a three-way version mismatch across packages the **dev env design doc** didn't pin tightly enough to survive PyPI moving forward since it was written.

**diagnostic steps**

- first out exception is NOT a diagnostic step
- diagnostic steps reveal information or apply a fix
- assume re-run and validation, these are not diagnostic steps
- keep the step description brief, use the diagnostics details section to elaborate actions and learnings for each step

| id          | seq | status | step                                                     | 
| ----------- | --- | ------ | ------------------------------------------------------------ | 
| 03.IS.03.01 | 01  | closed | replace with a single pinned `notebook==7.0.6`                 | 
| 03.IS.03.02 | 02  | closed | update launch flags `--NotebookApp.*` -> `--ServerApp.*`         | 
| 03.IS.03.03 | 03  | closed | rebuild + recreate jupyter only, confirm serving via docker logs | 

**diagnostic details**

01. (closed) Dropped the separate `jupyter`/`jupyterlab` pins in favor of one pinned `notebook==7.0.6`, letting pip resolve a single self-consistent `jupyter_server`/`traitlets` set instead of two independently-floating top-level packages.
02. (closed) Notebook 7 is built on `jupyter_server`, which renamed the classic `NotebookApp.*` config traits to `ServerApp.*`; updated `docker-compose.yml`'s `jupyter` service `command:` accordingly (`--ServerApp.ip`, `--ServerApp.port`, `--ServerApp.token=`, `--ServerApp.password=`).
03. (closed) `docker compose build jupyter && docker compose up -d jupyter` (postgres and the already-healthy spark-master/workers untouched by this call). `docker logs jupyter-notebook` then showed `Jupyter Server 2.20.0 is running at: http://0.0.0.0:8888/tree` with `All authentication is disabled` (matching the tokenless-by-design choice in Design -> environment & secrets), and the container stayed `Up` rather than exiting.

## Manual validate

| id       | seq | status  | milestone                                | 
| -------- | --- | ------- | ---------------------------------------- | 
| 03.08.01 | 01  | closed  | design                                   | 
| 03.08.02 | 02  | closed  | spark image                              | 

**manual validate** - spin up the spark cluster yourself, then run a PySpark command and a Spark SQL query that both connect to the postgres container over JDBC and return real query results (each block tested against the live containers before being staged here).

Both query scripts live under `src/pyspark/` (mounted into spark-master and jupyter at `/src/pyspark`, same pattern as the `data/`/`notebooks/`/`scripts/` mounts) rather than being pasted inline, so they can be opened, edited, and rerun directly - via `docker exec`, or interactively from the Jupyter/notebooks mount:

- `src/pyspark/03.08.01-pyspark-select-source.py` - JDBC read + DataFrame API `select()`/`show()`.
- `src/pyspark/03.08.02-sparksql-groupby-source.py` - same JDBC source, registered as a temp view, queried with a Spark SQL `GROUP BY`.

Both read `POSTGRES_DB`/`POSTGRES_USER`/`POSTGRES_PASSWORD` from the environment (never hardcoded), so pass them through explicitly with `docker exec -e VAR="$VAR"` - `docker exec -e VAR` without a value does not reliably forward the caller's shell env for `exec` in this environment.

```bash
# 1. spin up postgres + spark + jupyter (no-op if already up - postgres is never recreated either way)
source .env && source .secrets
PYSPARK_DIR=src/pyspark
docker compose --env-file .env -f docker/docker-compose.yml up -d
docker ps --format '{{.Names}}\t{{.Status}}'

pyspark_run() { docker exec -e POSTGRES_DB="$POSTGRES_DB" -e POSTGRES_USER="$POSTGRES_USER" \
-e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" spark-master python3 "$1"; }

# 2. PySpark: JDBC read + DataFrame API, executed inside spark-master against the postgres service
pyspark_run $PYSPARK_DIR/03.08.01-pyspark-select-source.py

# 3. Spark SQL: same JDBC source registered as a temp view, queried with GROUP BY
pyspark_run $PYSPARK_DIR/03.08.02-sparksql-groupby-source.py

# 4. optional: same checks from a browser instead of the CLI
#    Spark master UI  - http://localhost:${SPARK_MASTER_UI_PORT:-8080}
#    Jupyter          - http://localhost:${JUPYTER_PORT:-8888}  (tokenless, per Design -> environment & secrets)
```

Expected output for block 2 (5 sample rows + a total row count matching the live table), from this session's own dry run:

```
+--------------+-----------+------------------+-------------+
|transaction_id| account_id|transaction_amount|currency_code|
+--------------+-----------+------------------+-------------+
|   TXN-0000001|ACC-1000346|          13758.72|          USD|
|   TXN-0000002|ACC-1000287|           4693.83|          SGD|
|   TXN-0000003|ACC-1000174|          29467.39|          SGD|
|   TXN-0000004|ACC-1000135|           4646.36|          JPY|
|   TXN-0000005|ACC-1000360|          27606.51|          JPY|
+--------------+-----------+------------------+-------------+
only showing top 5 rows

row count: 2010
```

and for block 3 (a currency-level aggregate computed by Spark, sourced entirely from postgres over JDBC):

```
+-------------+---------+------------+
|currency_code|txn_count|total_amount|
+-------------+---------+------------+
|          SGD|     1093| 27150037.95|
|          USD|      402|  9659466.36|
|          EUR|      206|  4817082.87|
|          GBP|      197|  4890180.67|
|          JPY|       99|  2557906.00|
|         NULL|        5|   158783.59|
|          ZZZ|        3|    64971.16|
|          XXX|        3|    86728.95|
|          usd|        1|      693.59|
|           SG|        1|    36391.09|
+-------------+---------+------------+
```

(the odd `usd`/`SG`/`ZZZ`/`XXX`/`NULL` rows are intentional dirty-data cases from feature 04's mock data seeding, not a bug in this feature's query - they're exactly the kind of thing a real reconciliation job should catch.)

The generated scripts have no unhandled first-out exceptions of their own by the end of this session - both build-time exceptions below were resolved in-band before the feature's own `01-dev-env-setup.sh` / `02-workflow-validate.sh` runs were considered representative, and the third (jupyter) was a runtime issue on a service outside the automated validation path, also resolved in-band.


## Guideline

## instructions

review and strictly follow these relevant skills when performing tasks for this feature implementation and working with this document

## relevant skills

- markdown-tables
- feature-implementation-guide
