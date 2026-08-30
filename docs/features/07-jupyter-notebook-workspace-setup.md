# Jupyter Notebook Workspace Setup - Feature tracker
>Review the guidelines before performing any actions including edits on the document 

## 07 (closed) jupyter notebook workspace setup

## Contents

- [Tasks](#tasks)
- [Scope](#scope)
- [References](#references)
- [Design](#design)
  - [notebook naming & directory conventions](#notebook-naming--directory-conventions)
  - [template notebook design](#template-notebook-design)
  - [psycopg2 dependency](#psycopg2-dependency)
  - [notebook output commit policy](#notebook-output-commit-policy)
  - [idempotency / rerun-safety](#idempotency--rerun-safety)
  - [environment & secrets](#environment--secrets)
  - [workflow validation runner](#workflow-validation-runner)
- [Test Cases](#test-cases)
- [Edit locations](#edit-locations)
- [Implement](#implement)
- [Validate](#validate)
- [Guideline](#guideline)

## Tasks

| id    | seq | status  | milestone                                          | 
| ----- | --- | ------- | -------------------------------------------------- | 
| 07.01 | 01  | closed  | design                                             | 
| 07.06 | 02  | closed  | test strategy test cases                           | 
| 07.02 | 03  | closed  | edit locations and implementation plan             | 
| 07.03 | 04  | closed  | jupyter workspace conventions                      | 
| 07.04 | 05  | closed  | template notebook - postgres + spark connectivity  | 
| 07.05 | 06  | closed  | per-assessment notebook scaffolding                | 
| 07.IS | 07  | closed  | validate                                           | 

## Scope

define the notebook workspace conventions the three assessments build their own working notebooks on top of, plus one template notebook proving the Jupyter container the **spark container dev env tracker** already stood up actually reaches both postgres and the Spark cluster from inside its own environment. This feature stands up conventions and proof-of-connectivity, not any assessment's analysis content.

- depends on the **spark container dev env tracker** - the `jupyter` container, its `notebooks/` mount, and the Spark/postgres network path already exist as of that feature; this feature does not provision new infrastructure or touch the docker compose stack, it only adds notebook files and, if needed, one Python package pin to the existing jupyter image
- one notebook per assessment, named to match the assessment's own naming (e.g. `assessment1_profiling.ipynb`) - this feature fixes that naming convention and scaffolds the starting files, it does not write any assessment's actual profiling, reconciliation, or lineage analysis
- one template notebook (not assessment-specific) proves the connectivity pattern every assessment notebook reuses: a Spark session that reaches the cluster (`spark-master:7077`), and a postgres connection reaching `src_transaction_daily` and the seeded schemas - via JDBC from PySpark and/or a direct Python driver, per the **dev env design doc**'s appendix pattern
- `psycopg2`/`psycopg2-binary` is pinned in the **dev env design doc**'s appendix but was not carried into the **spark container dev env tracker**'s actual `Dockerfile.spark` build list (`pyspark`, `delta-spark`, `faker`, `postgresql-client` only) - if the template notebook needs a direct Python-side postgres connection rather than JDBC-only, adding that pin is in scope here, since this is the first feature that actually needs it
- decides and documents where notebook *outputs* get committed - executed-cell outputs (result tables, printed profiling summaries, small plots) checked into git alongside the `.ipynb` source, versus cleared before commit - so the three assessments aren't each deciding this ad hoc; this is scoped to notebooks specifically and feeds into the broader **assessment deliverables conventions** milestone's per-assessment deliverable-location decision
- does not implement any assessment's actual analysis, profiling, reconciliation, or lineage logic - the template notebook only proves connectivity, the same reusable-scaffold-not-content precedent the **powerbi dashboard setup tracker** already set for its `.pbip` template
- does not change the jupyter container's authentication or networking posture (tokenless, per the **spark container dev env tracker**'s environment & secrets design) - no new ports, no new container; the only `docker-compose.yml` change is passing the existing postgres credentials through to the `jupyter` service's own environment (see [Design -> environment & secrets](#environment--secrets)), needed only because a persistent Jupyter kernel can't take credentials per-invocation the way every prior feature's one-shot `docker exec -e` scripts do

## References

## Design

### notebook naming & directory conventions

`notebooks/` already exists, empty, mounted into `jupyter` and `spark-master` at `/notebooks`. This feature populates it with four files, all flat under `notebooks/` - no per-assessment subfolders, matching how the directory is mounted and referenced as a single path everywhere it's already used:

```
notebooks/
├── 00_template_connectivity_check.ipynb   # new - proves postgres + spark reachability
├── assessment1_profiling.ipynb            # new - stub, assessment 1 working notebook
├── assessment2_gl_reconciliation.ipynb    # new - stub, assessment 2 working notebook
└── assessment3_regulatory_dashboard.ipynb # new - stub, assessment 3 working notebook
```

The three assessment notebook names extend the one example already fixed in `docs/milestones.md` (`assessment1_profiling.ipynb`) using the same `assessment<n>_<short-topic>.ipynb` pattern against each assessment's own milestone title. The `00_` prefix on the template sorts it first in a directory listing and signals it isn't itself a graded deliverable - the same "reusable scaffold, not assessment content" role the **powerbi dashboard setup tracker**'s `.pbip` template already plays for dashboards.

there is no machine-generated source of truth to build a notebook from, Unlike the schema-JSON -> generated-DDL convention (postgres) or the hand-authored-in-Power-BI-Desktop convention (`.pbip`). All four files are hand-authored `.ipynb` JSON, created once and git-tracked directly, not templated by a generator script. Creation is still verify-or-create: The scaffolding step must not overwrite an assessment notebook a candidate has already started.

### template notebook design

`00_template_connectivity_check.ipynb` proves, from inside a live Jupyter kernel (not a one-shot `spark-submit`), that both dependencies every assessment notebook needs are actually reachable. Cells, in order:

1. **setup** - imports (`os`, `psycopg2`, `pyspark.sql.SparkSession`); reads connection parameters from `os.environ` only, never hardcoded - see [environment & secrets](#environment--secrets). No cell in this notebook prints a credential value or a connection string containing one.
2. **spark connectivity** - builds a `SparkSession` against `spark://spark-master:7077` and runs one trivial distributed action (e.g. a small `spark.range(...).count()`), proving the *notebook's own kernel* reaches the cluster - a different code path than the **spark container dev env tracker**'s `spark-jdbc-smoketest.py`, which runs as a job submitted from inside `spark-master` itself, not from `jupyter`.
3. **postgres - JDBC path** - `spark.read.jdbc(...)` against `src_transaction_daily`, the same URL/table/driver shape `spark-jdbc-smoketest.py` already established, read this time from the notebook kernel rather than a submitted job - the path assessment notebooks are expected to use for anything Spark-scale.
4. **postgres - direct Python path** - a `psycopg2` connection running a simple read (e.g. `SELECT COUNT(*) FROM src_transaction_daily`) against the same table, independent of the JDBC path above - the lighter-weight path assessment notebooks may prefer for small lookups that don't need a Spark job.
5. **summary** - prints one `[PASS]`/`[FAIL]` line per check plus one overall summary line, in the same bracket notation every script in this repo already uses, so [workflow validation runner](#workflow-validation-runner) can grep the executed notebook for the same marker text rather than inventing a notebook-specific report format.

Cross-checking cell 3's and cell 4's row counts against each other (and against the independently-queried count in [Test Cases](#test-cases)) is what proves the two access patterns agree, not just that neither raised an exception.

### psycopg2 dependency

The **dev env design doc**'s appendix pins `psycopg2-binary==2.9.0`, but the **spark container dev env tracker**'s actual `Dockerfile.spark` build list never carried it forward (`pyspark`, `delta-spark`, `faker`, `postgresql-client` only) - confirmed by inspecting that feature's Implement section directly, not assumed. Cell 4 above is the first thing in this repo that actually needs a direct Python postgres driver, so this feature adds the pin.

- starts from the design doc's stated `2.9.0` pin; deviate only if it fails to build, following the same discovered-by-building precedent the **spark container dev env tracker** already set for its `jupyter`/`jupyterlab` pin (03.IS.03) - not assumed compatible up front.
- goes into the existing pip-install step of `docker/Dockerfile.spark`, the one image shared by `spark-master`, both `spark-worker-*`, and `jupyter` - so all four containers get the package even though only `jupyter` needs it, matching that same tracker's "one image, no per-service build differentiation" design.
- rebuilding only requires `docker compose build jupyter && docker compose up -d jupyter` - the already-running `spark-master`/`spark-worker-*` containers are untouched (same scoped-rebuild precedent as 03.IS.03's resolution), since nothing about their own role depends on `psycopg2`.

**Deviation, discovered by building**: `2.9.0` failed exactly the way this subsection anticipated - no prebuilt wheel for Python 3.11, source build fails on a missing `pg_config` - see [07.IS.01](#validate). Bumped to `psycopg2-binary==2.9.9`, which does publish a `cp311` wheel; no other change was needed. [Implement -> 1. psycopg2 dependency](#1-psycopg2-dependency) shows the pin actually shipped.

### notebook output commit policy

Committed notebooks keep their executed outputs - no `nbstripout`/clear-on-commit filter is introduced, unlike the usual "diff-friendly, outputs stripped" default for notebooks in git. This repo's convention elsewhere is to keep evidence of an actual run as a git-tracked artifact (`.dev/logs/*.log`, the **ai closed-loop validation tracker**'s audit-trail rows) rather than optimize purely for clean diffs; for a notebook, its own cell outputs already serve as that log; before committing, a notebook is expected to have been run top-to-bottom (Restart & Run All), not assembled from out-of-order cell executions, so committed output is trustworthy evidence rather than stale or order-dependent.

This makes the guardrail from [environment & secrets](#environment--secrets) load-bearing rather than cosmetic: since committed output is real output, no cell may ever print a credential value or a connection string that embeds one - only derived, non-sensitive results (row counts, `[PASS]`/`[FAIL]` text). [Test Cases](#test-cases) checks this directly against the committed file, not by trusting the notebook's own discipline.

Where each assessment's *other* non-notebook deliverables (profiling summaries, root-cause write-ups, etc.) live is explicitly left to the **assessment deliverables conventions** milestone per [Scope](#scope) - this decision covers only the notebook files themselves.

### idempotency / rerun-safety

- **template notebook**: every check it runs is read-only (`COUNT`, a trivial Spark action) - rerunning it is always safe and reproduces the same evidence, no special append-only handling needed the way the **ai closed-loop validation tracker**'s batch tables required.
- **notebooks read, scripts write**: assessment notebooks are expected to follow the same read-only default - any write path (loading results, inserting audit rows) stays in a git-tracked script per the existing convention, not inline notebook code, so the append-only/idempotent-write discipline [05](05-ai-closed-loop-validation.md#idempotency--rerun-safety) already established never has to be re-derived inside a notebook.
- **scaffold creation**: verify-or-create per [notebook naming & directory conventions](#notebook-naming--directory-conventions) - 07.02's creation step checks each target path before writing, same convention as every prior feature's DDL/setup steps.

### environment & secrets

No new secrets and no new variable names - reuses the existing `POSTGRES_DB`/`POSTGRES_USER`/`POSTGRES_PASSWORD` from `.env`/`.secrets`, the same three every PySpark script under `src/pyspark/` already reads via `os.environ`.

The mechanism has to differ from precedent, though. Every prior feature's Spark-side script is a one-shot job, invoked as `docker exec -e POSTGRES_PASSWORD=... spark-master spark-submit ...` - credentials are injected fresh at the moment of each invocation. A Jupyter kernel is not one-shot: `jupyter` is a long-running container started once by `docker compose up`, and today its service block in `docker-compose.yml` has no `environment:` section at all (confirmed by inspecting the file directly) - so there is no per-cell moment to `docker exec -e` a credential into an already-running kernel.

This feature adds an `environment:` block to the `jupyter` service only, mirroring the `postgres` service's own block (`POSTGRES_DB: ${POSTGRES_DB}`, etc.) - substituted from the invoking shell's already-`.secrets`-sourced environment the same way every `docker compose up` in this repo already works, so it introduces no new secrets file or plumbing, only extends an existing pattern to a service that didn't need it before. `spark-master`/`spark-worker-*` keep using the existing per-invocation `docker exec -e` pattern for their own one-shot smoke test, untouched by this change.

**Guardrail** (load-bearing per [notebook output commit policy](#notebook-output-commit-policy)): these three values reach `os.environ` inside the kernel precisely so notebook code can use them - no cell may print any of them, or a connection string built from them, since committed notebook output is real, git-tracked output.

### workflow validation runner

`scripts/06-notebook-validate.sh` (next free number after `05-powerbi-sync.sh`) is what makes the milestone's closure condition - "the template notebook runs cleanly end to end ... successfully querying both postgres and Spark" - a scripted, rerunnable check rather than something eyeballed once in the Jupyter UI:

1. Verifies `jupyter`, `spark-master`, and `postgres` are already running (`docker ps --filter name=...`); fails fast otherwise, matching the **ai closed-loop validation tracker** and **powerbi dashboard setup tracker**'s orchestrator precedent - this feature doesn't stand up infrastructure either.
2. Executes `00_template_connectivity_check.ipynb` headlessly inside the `jupyter` container (`jupyter nbconvert --to notebook --execute`), writing to a fresh output path rather than `--inplace` - a failed run never overwrites the last-known-good, git-tracked notebook; only a successful run's output is the one that gets committed, keeping [notebook output commit policy](#notebook-output-commit-policy)'s "output reflects an actual passing run" true by construction.
3. Parses the executed notebook's own summary cell for the `[PASS]`/`[FAIL]` marker from [template notebook design](#template-notebook-design) step 5 - `nbconvert`'s exit code alone only proves "no cell raised," not "the checks agreed," the same never-trust-the-script's-own-exit-code discipline the **ai closed-loop validation tracker**'s test strategy already applies.
4. Writes a standard `.dev/logs/<ts>-07.<sub>-notebook-validate.log` per the `feature-implementation-guide` skill's naming convention, capturing `nbconvert`'s output plus the extracted marker.
5. Exits non-zero if either the notebook execution itself failed or the extracted marker says `FAIL`.

## Test Cases

_test strategy_

Every task below is checked on more than one independent layer, so a pass is never just "the notebook printed `[PASS]`" or "`nbconvert` exited 0":

1. **script/notebook self-report** - `06-notebook-validate.sh`'s own `[PASS]`/`[FAIL]` log lines under `.dev/logs/`, per the `feature-implementation-guide` skill's logging convention, and the executed notebook's own summary cell.
2. **direct inspection, bypassing the notebook** - the same postgres/Spark queries run independently via `docker exec ... psql` / `docker exec ... spark-submit`, outside the notebook's own kernel, diffed against what the notebook itself printed - the notebook is never trusted to grade its own connectivity check.
3. **independently-recorded expected values** - row counts checked against what the **spark container dev env tracker** and **seed mock data tracker** already recorded, not just cross-checked between this notebook's own cells.
4. **committed-artifact inspection** - since this is the first feature to put live credentials into a container's persistent environment and then commit that container's own notebook output to git, the committed `.ipynb` file itself is scanned for leaked secret values, not just reviewed by eye.

_test cases_

| id       | task         | layer              | check                                                  | 
| -------- | ------------ | ------------------ | ------------------------------------------------------ | 
| 07.TC.01 | 07.03        | structure          | `notebooks/` has the 4 expected files, correctly named | 
| 07.TC.02 | 07.04        | direct-check       | Spark connectivity cell reproduced independently       | 
| 07.TC.03 | 07.04        | direct-check       | JDBC row count matches independent `psql COUNT(*)`     | 
| 07.TC.04 | 07.04        | direct-check       | `psycopg2` row count matches the same `COUNT(*)`       | 
| 07.TC.05 | 07.04        | independent        | row count matches already-recorded seed volume         | 
| 07.TC.06 | 07.04        | committed-artifact | committed notebook has no leaked `POSTGRES_PASSWORD`   | 
| 07.TC.07 | 07.02        | direct-check       | jupyter container env has postgres creds set           | 
| 07.TC.08 | 07.IS        | script             | forced-FAIL path exits non-zero                        | 
| 07.TC.09 | 07.IS        | script             | two runs both PASS, same marker - idempotent           | 
| 07.TC.10 | 07.05        | structure          | assessment stub notebooks parse as valid JSON          | 
| 07.TC.11 | 07.04, 07.05 | manual             | browser file list shows all 4 notebooks, opens cleanly | 

01. **07.TC.02** re-run the same trivial distributed action (e.g. `spark.range(...).count()`) via `docker exec spark-master spark-submit`, independent of the notebook kernel, and compare results.
02. **07.TC.05** cross-check against the volume already recorded by [04](04-seed-mock-data.md) and [03](03-dev-env-setup-spark-container.md)'s own JDBC smoke test, not just internal self-consistency between this notebook's own cells.
03. **07.TC.06** `grep` the raw committed `.ipynb` file for the literal current value of `POSTGRES_PASSWORD` (read from `.secrets` at test time, never hardcoded into the test itself) - expect zero matches, not a regex guess at what a leak might look like.
04. **07.TC.07** `docker exec jupyter-notebook env` shows `POSTGRES_DB`/`POSTGRES_USER`/`POSTGRES_PASSWORD` present, without needing a `docker exec -e` override - proves the [environment & secrets](#environment--secrets) compose change actually took effect.
05. **07.TC.08** force a deliberately broken cell in a scratch copy of the notebook, then check `06-notebook-validate.sh`'s exit code with `echo $?` right after the run, not the printed summary text.
06. **07.TC.09** run `06-notebook-validate.sh` twice back-to-back; both runs must print `[PASS]` with an identical summary marker, per [idempotency / rerun-safety](#idempotency--rerun-safety).
07. **07.TC.10** each assessment stub notebook, even near-empty, parses as valid notebook JSON via `nbconvert` - proves the scaffold itself isn't malformed, no analysis content expected yet.
08. **07.TC.11** the one layer the other 10 cases don't cover - opening `http://localhost:8888` in an actual browser and confirming the file list, not just the server-side API/filesystem view every other case checks. Server-side proxy for the same check: `curl http://localhost:8888/api/contents` lists all 4 `.ipynb` files with `"type": "notebook"`.

## Edit locations

| id       | path                                               | 
| -------- | -------------------------------------------------- | 
| 07.EL.01 | `docker/Dockerfile.spark`                          | 
| 07.EL.02 | `docker/docker-compose.yml`                        | 
| 07.EL.03 | `notebooks/00_template_connectivity_check.ipynb`   | 
| 07.EL.04 | `notebooks/assessment1_profiling.ipynb`            | 
| 07.EL.05 | `notebooks/assessment2_gl_reconciliation.ipynb`    | 
| 07.EL.06 | `notebooks/assessment3_regulatory_dashboard.ipynb` | 
| 07.EL.07 | `scripts/06-notebook-validate.sh`                  | 

01. **07.EL.01** adds the [psycopg2 dependency](#psycopg2-dependency) pin to the pip-install step already in the file.
02. **07.EL.02** adds the `environment:` block to the `jupyter` service only, per [environment & secrets](#environment--secrets).
03. **07.EL.03** the template notebook - new, per [template notebook design](#template-notebook-design).
04. **07.EL.04, 07.EL.05, 07.EL.06** the three assessment stub notebooks - new, per [notebook naming & directory conventions](#notebook-naming--directory-conventions); each gets a title cell and the same setup cell as 07.EL.03, no analysis content.
05. **07.EL.07** the notebook workflow validation runner - new, per [workflow validation runner](#workflow-validation-runner).

No `.env`/`.env.sample` changes - [environment & secrets](#environment--secrets) reuses the existing `POSTGRES_DB`/`POSTGRES_USER`/`POSTGRES_PASSWORD` names, and the jupyter container name defaults inline in `07.EL.07` (`"${JUPYTER_CONTAINER_NAME:-jupyter-notebook}"`) the same way `SPARK_CONTAINER_NAME` already defaults inline in `04-closed-loop-run.sh` without a `.env.sample` entry.

## Implement

Implementation order follows the dependency chain: dependency pin -> credential plumbing -> template notebook -> assessment stubs -> validation runner - each later step assumes the one before it is already in place.

### 1. psycopg2 dependency

edit locations: `07.EL.01`

One line added to the existing `RUN pip install --no-cache-dir` block in `docker/Dockerfile.spark`, alongside the packages the **spark container dev env tracker** already pinned. Shown here as actually shipped (`2.9.9`, not Design's starting-point `2.9.0`) - see [07.IS.01](#validate) for why:

```dockerfile
RUN pip install --no-cache-dir \
    pyspark==3.5.0 \
    delta-spark==3.0.0 \
    faker==19.0.0 \
    notebook==7.0.6 \
    psycopg2-binary==2.9.9
```

`psycopg2-binary` ships its own bundled `libpq` in the wheel, so no additional `apt-get` package is needed beyond what's already installed - true of `2.9.9`'s wheel; `2.9.0` had no `cp311` wheel at all and fell back to a source build this image can't satisfy, per [07.IS.01](#validate). Rebuild scope is `jupyter` only, per [psycopg2 dependency](#psycopg2-dependency):

```bash
docker compose --env-file .env -f docker/docker-compose.yml build jupyter
docker compose --env-file .env -f docker/docker-compose.yml up -d jupyter
```

### 2. jupyter credential plumbing

edit locations: `07.EL.02`

An `environment:` block added to the `jupyter` service in `docker/docker-compose.yml`, inserted right after `container_name: jupyter-notebook` and before `command:`, mirroring the `postgres` service's own block exactly:

```yaml
  jupyter:
    build:
      context: .
      dockerfile: Dockerfile.spark
      args:
        JDBC_DRIVER_VERSION: ${JDBC_DRIVER_VERSION:-42.7.3}
    container_name: jupyter-notebook
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    command:
      - jupyter
      - notebook
      - --ServerApp.ip=0.0.0.0
      - --ServerApp.port=8888
      - --no-browser
      - --allow-root
      - --ServerApp.token=
      - --ServerApp.password=
```

Takes effect on the same `docker compose up -d jupyter` used to pick up the `07.EL.01` rebuild - no separate step. Verified directly per [07.TC.07](#test-cases): `docker exec jupyter-notebook env | grep POSTGRES_` should list all three, with no `docker exec -e` override needed.

### 3. template notebook

edit locations: `07.EL.03`

`notebooks/00_template_connectivity_check.ipynb`, built either directly in the Jupyter UI (`File -> New -> Notebook`, kernel `python3`) or via the `nbformat` API in a throwaway Python REPL - either way, the `.ipynb` file that lands at this path and gets committed is the source of truth, not the tool used to create it, per [notebook naming & directory conventions](#notebook-naming--directory-conventions). 5 cells, matching [template notebook design](#template-notebook-design) exactly:

**cell 1 - setup**

```python
import os
from pyspark.sql import SparkSession
import psycopg2

POSTGRES_DB = os.environ["POSTGRES_DB"]
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
SOURCE_TABLE = "src_transaction_daily"
```

**cell 2 - spark connectivity**

```python
spark = (
    SparkSession.builder.master("spark://spark-master:7077")
    .appName("00-template-connectivity-check")
    .getOrCreate()
)

spark_check_count = spark.range(1000).count()
spark_status = "PASS" if spark_check_count == 1000 else "FAIL"
print(f"[{spark_status}] spark connectivity: spark.range(1000).count()={spark_check_count}")
```

**cell 3 - postgres, JDBC path**

```python
jdbc_df = spark.read.jdbc(
    url=f"jdbc:postgresql://postgres:5432/{POSTGRES_DB}",
    table=SOURCE_TABLE,
    properties={
        "user": POSTGRES_USER,
        "password": POSTGRES_PASSWORD,
        "driver": "org.postgresql.Driver",
    },
)
jdbc_row_count = jdbc_df.count()
jdbc_status = "PASS" if jdbc_row_count > 0 else "FAIL"
print(f"[{jdbc_status}] postgres JDBC path: {SOURCE_TABLE} row_count={jdbc_row_count}")
```

**cell 4 - postgres, direct Python path**

```python
conn = psycopg2.connect(
    host="postgres", port=5432, dbname=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD,
)
with conn, conn.cursor() as cur:
    cur.execute(f"SELECT COUNT(*) FROM {SOURCE_TABLE};")
    psycopg2_row_count = cur.fetchone()[0]
conn.close()

psycopg2_status = "PASS" if psycopg2_row_count > 0 else "FAIL"
print(f"[{psycopg2_status}] postgres psycopg2 path: {SOURCE_TABLE} row_count={psycopg2_row_count}")
```

**cell 5 - summary**

```python
checks = {
    "spark_connectivity": spark_status,
    "postgres_jdbc": jdbc_status,
    "postgres_psycopg2": psycopg2_status,
    "row_count_cross_check": "PASS" if jdbc_row_count == psycopg2_row_count else "FAIL",
}

for name, status in checks.items():
    print(f"[{status}] {name}")

overall = "PASS" if all(s == "PASS" for s in checks.values()) else "FAIL"
print(f"[{overall}] 00-template-connectivity-check: overall status={overall}")

spark.stop()
```

No cell prints `POSTGRES_PASSWORD`, `POSTGRES_USER`, or a connection string built from them - only derived row counts and `[PASS]`/`[FAIL]` text, per [environment & secrets](#environment--secrets)'s guardrail. The exact final line (`[{overall}] 00-template-connectivity-check: overall status={overall}`) is the marker `07.EL.07` greps for - keep its prefix text unchanged if this cell is ever edited.

### 4. assessment stub notebooks

edit locations: `07.EL.04, 07.EL.05, 07.EL.06`

Each stub is 2 cells: one markdown title cell, then the same setup code as [template notebook](#3-template-notebook)'s cell 1, so a candidate's first cell already has working imports and credentials rather than a blank file - no analysis logic beyond that, per [Scope](#scope).

**`notebooks/assessment1_profiling.ipynb`** - markdown cell:

```markdown
# Assessment 1 - Source-to-Bronze Profiling & Reconciliation

See `docs/milestones.md` and `docs/design/assignment.md` for task scope.
Connectivity conventions: see `00_template_connectivity_check.ipynb`.
```

**`notebooks/assessment2_gl_reconciliation.ipynb`** - markdown cell:

```markdown
# Assessment 2 - Financial Accounting & GL Reconciliation

See `docs/milestones.md` and `docs/design/assignment.md` for task scope.
Connectivity conventions: see `00_template_connectivity_check.ipynb`.
```

**`notebooks/assessment3_regulatory_dashboard.ipynb`** - markdown cell:

```markdown
# Assessment 3 - Regulatory DQ, Lineage & Executive Dashboard

See `docs/milestones.md` and `docs/design/assignment.md` for task scope.
Connectivity conventions: see `00_template_connectivity_check.ipynb`.
```

All three follow with the identical code cell:

```python
import os
from pyspark.sql import SparkSession
import psycopg2

POSTGRES_DB = os.environ["POSTGRES_DB"]
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
```

### 5. workflow validation runner

edit locations: `07.EL.07`

`scripts/06-notebook-validate.sh`, same `log()`/step-function/`main()` shape as `04-closed-loop-run.sh`, extended with a headless `nbconvert` call and a marker-parsing step neither prior script needed:

```bash
#!/usr/bin/env bash
# 06-notebook-validate.sh
# Validates feature 07's template connectivity-check notebook end to end:
# verifies jupyter/spark/postgres are already running -> executes
# 00_template_connectivity_check.ipynb headlessly inside the jupyter
# container -> parses the notebook's own [PASS]/[FAIL] summary marker
# (never trusts nbconvert's exit code alone). Does NOT stand up
# infrastructure, and does NOT overwrite the tracked notebook - it writes
# the executed copy to a temp path for review. See
# docs/features/07-jupyter-notebook-workspace-setup.md -> Design ->
# workflow validation runner.

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

JUPYTER_CONTAINER_NAME="${JUPYTER_CONTAINER_NAME:-jupyter-notebook}"
SPARK_CONTAINER_NAME="${SPARK_CONTAINER_NAME:-spark-master}"
POSTGRES_CONTAINER_NAME="${POSTGRES_CONTAINER_NAME:-postgres-as01}"

NOTEBOOK_PATH="/notebooks/00_template_connectivity_check.ipynb"
EXECUTED_PATH="/tmp/00_template_connectivity_check.executed.ipynb"
SUMMARY_PREFIX="00-template-connectivity-check: overall status="

FEATURE_ID="07.IS"
TASK_NAME="notebook-validate"

mkdir -p "$LOGS_DIR"
LOG_FILE="$(TZ="$TIMEZONE" date +"$TIMESTAMP_FORMAT")-${FEATURE_ID}-${TASK_NAME}.log"
LOG_PATH="$LOGS_DIR/$LOG_FILE"

log() {
    echo "$(TZ="$TIMEZONE" date +"%Y-%m-%d %H:%M:%S %Z") $1" | tee -a "$LOG_PATH"
}

step_container_check() {
    for name in "$JUPYTER_CONTAINER_NAME" "$SPARK_CONTAINER_NAME" "$POSTGRES_CONTAINER_NAME"; do
        log "[INFO] [07.IS] checking container '$name' is already running"
        if [ "$(docker ps --filter "name=^${name}$" --format '{{.Names}}')" != "$name" ]; then
            log "[FAIL] [07.IS] container '$name' not running - this script does not provision infrastructure"
            return 1
        fi
        log "[PASS] [07.IS] container '$name' running"
    done
    return 0
}

step_execute_notebook() {
    log "[INFO] [07.IS] executing $NOTEBOOK_PATH headlessly inside $JUPYTER_CONTAINER_NAME"
    if ! docker exec "$JUPYTER_CONTAINER_NAME" \
        jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=120 \
        --output "$EXECUTED_PATH" "$NOTEBOOK_PATH" >>"$LOG_PATH" 2>&1
    then
        log "[FAIL] [07.IS] nbconvert execution failed - see $LOG_PATH for the traceback"
        return 1
    fi
    log "[PASS] [07.IS] nbconvert execution completed - no cell raised"
    return 0
}

step_parse_summary() {
    log "[INFO] [07.IS] parsing executed notebook for the [PASS]/[FAIL] summary marker"
    local marker
    marker="$(docker exec "$JUPYTER_CONTAINER_NAME" python3 -c "
import json
nb = json.load(open('$EXECUTED_PATH'))
text = ''.join(
    ''.join(o.get('text', [])) if isinstance(o.get('text'), list) else o.get('text', '')
    for cell in nb['cells'] for o in cell.get('outputs', [])
)
lines = [l for l in text.splitlines() if '$SUMMARY_PREFIX' in l]
print(lines[-1] if lines else 'NOT_FOUND')
")"
    log "[INFO] [07.IS] summary line: $marker"

    if [[ "$marker" == "[PASS] ${SUMMARY_PREFIX}"* ]]; then
        log "[PASS] [07.IS] notebook summary marker agrees"
        return 0
    fi
    log "[FAIL] [07.IS] notebook summary marker missing or FAIL"
    return 1
}

main() {
    log "[INFO] === 06-notebook-validate start (feature $FEATURE_ID) ==="

    step_container_check || { log "[FAIL] notebook validate aborted at container check"; exit 1; }
    step_execute_notebook || { log "[FAIL] notebook validate aborted at notebook execution"; exit 1; }
    step_parse_summary || { log "[FAIL] notebook validate aborted at summary parse"; exit 1; }

    log "[PASS] notebook validate completed successfully"
    log "[INFO] executed copy: $EXECUTED_PATH (inside $JUPYTER_CONTAINER_NAME) - copy over $NOTEBOOK_PATH and commit if this run's output should become the tracked version"
    log "[INFO] log written to $LOG_PATH"
    exit 0
}

main
```

`--ExecutePreprocessor.timeout=120` bounds the whole run so a hung Spark connectivity attempt (e.g. `spark-master` unreachable despite the container check passing) fails the step rather than hanging the script indefinitely. The `--output` path is absolute and outside `/notebooks`, so a failed or in-progress run can never leave a partially-written file at the git-tracked path - satisfying [workflow validation runner](#workflow-validation-runner) step 2's "never overwrite the last-known-good notebook" requirement by construction rather than by convention.

## Validate

Ran the full chain against real infrastructure (no mocks): `01-dev-env-setup.sh` to bring postgres + spark + jupyter up (already-seeded `src_transaction_daily`, 2,010 rows, carried over from feature 04), then `07.EL.01`/`07.EL.02` applied for real, `jupyter` rebuilt and recreated, all 4 notebooks under `notebooks/` created, and `06-notebook-validate.sh` run 5 times across this session - one first-attempt build failure (07.IS.01, below), then a clean run, two back-to-back determinism runs, one deliberately forced-FAIL run, and one final confirmation run after restoring the tracked notebook. Every [Test Cases](#test-cases) protocol was executed and checked directly, not eyeballed from the script's own summary alone - see the results table below. A second session opened the Jupyter UI in an actual browser per [workflow validation runner](#workflow-validation-runner); the container stack had stopped in the meantime (07.IS.02, below) - brought back up and reconfirmed, both server-side and in the browser.

Log artifacts (`.dev/logs/`, gitignored - see [workflow validation runner](#workflow-validation-runner) for how to reproduce):

| id | log file                                   | exit | evidence                                  | 
| -- | ------------------------------------------ | ---- | ----------------------------------------- | 
| 01 | `260830154758-02.06-dev-env-setup.log`     | 0    | postgres+spark+jupyter up, 2/2 workers    | 
| 02 | `260830160150-07.IS-notebook-validate.log` | 0    | first clean PASS, after psycopg2 fix [01] | 
| 03 | `260830160450-07.IS-notebook-validate.log` | 0    | determinism run 1                         | 
| 04 | `260830160518-07.IS-notebook-validate.log` | 0    | determinism run 2, identical marker       | 
| 05 | `260830160619-07.IS-notebook-validate.log` | 1    | forced-FAIL (07.TC.08) [02]               | 
| 06 | `260830160630-07.IS-notebook-validate.log` | 0    | post-restore confirmation PASS            | 
| 07 | `260830161927-02.06-dev-env-setup.log`     | 0    | stack restart after 07.IS.02 [03]         | 

01. resolves 07.IS.01 below - the first build attempt (`psycopg2-binary==2.9.0`) failed before this log was written.
02. deliberate: cell 2 of a scratch copy replaced with `raise RuntimeError(...)`, run in place of the tracked notebook, then the tracked notebook restored byte-identical (`diff` confirmed) before the next run.
03. resolves 07.IS.02 below - the entire stack (all 5 containers) had stopped outside this session's own scripts; this is the recovery run.

**test case results** - each row is [Test Cases](#test-cases)' protocol executed for real, not inferred:

| id       | status | observed                                             | 
| -------- | ------ | ---------------------------------------------------- | 
| 07.TC.01 | PASS   | 4/4 files present under notebooks/, correctly named  | 
| 07.TC.02 | PASS   | independent spark-submit: 1000, notebook: 1000       | 
| 07.TC.03 | PASS   | JDBC 2010 rows = independent psql COUNT(*) 2010      | 
| 07.TC.04 | PASS   | psycopg2 2010 rows = same independent COUNT(*) 2010  | 
| 07.TC.05 | PASS   | 2010 matches feature 04's recorded seed volume       | 
| 07.TC.06 | PASS   | grep for live POSTGRES_PASSWORD: 0 matches           | 
| 07.TC.07 | PASS   | env has POSTGRES_DB/USER/PASSWORD, no -e override    | 
| 07.TC.08 | PASS   | forced-FAIL run exited 1, checked via echo $?        | 
| 07.TC.09 | PASS   | 2 consecutive runs, identical [PASS] marker          | 
| 07.TC.10 | PASS   | all 3 stubs parse via nbconvert, exit 0, no warnings | 
| 07.TC.11 | PASS   | GET /api/contents lists all 4 notebooks [04]         | 

A second, unplanned finding surfaced during 07.TC.10: the hand-authored stub notebooks (built directly as nbformat-v4.5 JSON, not round-tripped through a kernel the way the template notebook was) were missing each cell's `id` field, which `nbconvert` only warned about here but nbformat's own changelog says will become a hard error in a future version. Not a first-out *exception* - every command still exited 0 - but corrected before commit anyway: each stub was passed through one identity `jupyter nbconvert --to notebook` conversion, which nbformat normalizes by filling in the missing `id`s, and the fixed files were confirmed to still carry only the title/setup cells with no execution output.

04. **07.TC.11** see [07.IS.02](#validate) - the container stack had stopped between this session's earlier runs and the browser check; `GET /api/contents` was checked after bringing it back up, not against the stopped instance.

**Issues**

| id       | seq | status | issue                                                     | 
| -------- | --- | ------ | --------------------------------------------------------- | 
| 07.IS.01 | 01  | closed | psycopg2-binary==2.9.0 has no cp311 wheel, fails to build | 
| 07.IS.02 | 02  | closed | browser showed no notebooks - whole stack had stopped     | 

_07.IS.01 (closed) psycopg2-binary==2.9.0 has no prebuilt wheel for Python 3.11, source build fails_

**problem description**

`docker compose build jupyter`, the first build after adding the [07.EL.01](#edit-locations) pip pin, failed during `RUN pip install`. Per [psycopg2 dependency](#psycopg2-dependency), the Design section had already flagged this as a possible outcome and set the deviation policy ("deviate only if it fails to build") before the build was ever attempted.

**exception**

```log
#8 100.2   Error: pg_config executable not found.
#8 100.2   
#8 100.2   pg_config is required to build psycopg2 from source.  Please add the directory
#8 100.2   containing pg_config to the $PATH or specify the full executable path with the
#8 100.2   option:
#8 100.2 error: metadata-generation-failed
#8 ERROR: process "/bin/sh -c pip install --no-cache-dir pyspark==3.5.0 delta-spark==3.0.0 \
     faker==19.0.0 notebook==7.0.6 psycopg2-binary==2.9.0" did not complete successfully: exit code: 1
```

**triggering actions**

```bash
set -a && source .env && source .secrets && set +a
docker compose --env-file .env -f docker/docker-compose.yml build jupyter
```
run immediately after adding `psycopg2-binary==2.9.0` to `docker/Dockerfile.spark`'s existing `RUN pip install` block per [07.EL.01](#edit-locations).

**hypothesis**

- `psycopg2-binary` publishes prebuilt manylinux wheels per release, but only for the Python versions current when that release shipped - `2.9.0` (2021) likely predates any wheel built for `python:3.11-slim-bookworm`'s Python 3.11, so `pip` falls back to the source sdist, which needs `pg_config` (from `libpq-dev`) to build - not installed in this image.

**diagnostic steps**

| id          | seq | status | step                                                     | 
| ----------- | --- | ------ | -------------------------------------------------------- | 
| 07.IS.01.01 | 01  | closed | rerun build --no-cache, capture full pip traceback       | 
| 07.IS.01.02 | 02  | closed | isolate root-cause line from captured output             | 
| 07.IS.01.03 | 03  | closed | bump pin to psycopg2-binary==2.9.9, rebuild jupyter only | 
| 07.IS.01.04 | 04  | closed | confirm import + full connectivity check pass            | 

**diagnostic details**

01. `docker compose build --no-cache jupyter`, output filtered for `error`/`Error`/`ERROR` context lines - reproduced the same failure with the full traceback visible (a cached-layer rerun would have hidden it behind buildkit's cache).
02. The isolated traceback confirmed the hypothesis exactly: `Error: pg_config executable not found. pg_config is required to build psycopg2 from source.` - a missing-wheel-triggers-source-build issue, not a transient network/registry failure, so a version bump (not a system package addition) was the fix already anticipated in Design.
03. Changed `docker/Dockerfile.spark`'s pin to `psycopg2-binary==2.9.9`, then `docker compose build jupyter` (scoped, per [psycopg2 dependency](#psycopg2-dependency) - `spark-master`/`spark-worker-*` untouched) - built clean, `Image postgres-as01-jupyter Built`.
04. `docker compose up -d jupyter` recreated only the `jupyter` container (`postgres-as01`/`spark-master` stayed `Running`, confirming the scoped rebuild claim); `docker exec jupyter-notebook python3 -c "import psycopg2; print(psycopg2.__version__)"` printed `2.9.9`, and the full `06-notebook-validate.sh` run immediately after (log `01` in the Validate table above) passed end to end on the first try - no further deviation needed. [Design -> psycopg2 dependency](#psycopg2-dependency) and [Implement -> 1. psycopg2 dependency](#1-psycopg2-dependency) both reflect `2.9.9` as the value actually shipped, not `2.9.0`.

_07.IS.02 (closed) browser showed no notebooks - whole stack had stopped, not a workspace defect_

**problem description**

Opened `http://localhost:8888` per [workflow validation runner](#workflow-validation-runner) - the file browser showed no notebooks, despite [07.TC.01](#test-cases) and [07.TC.10](#test-cases) already having confirmed all 4 files present earlier in this same session.

**exception**

No traceback - this is a first-out *behavioral* anomaly, not a crash; the `feature-implementation-guide` skill's protocol still calls for it to be logged here the same way a traceback would be. The only "evidence" at first was the reported empty file list; `docker logs jupyter-notebook` was the first place an actual signal turned up:

```log
[I 2026-08-30 08:01:44.269 ServerApp] Serving notebooks from local directory: /notebooks
[I 2026-08-30 08:01:44.269 ServerApp] Jupyter Server 2.21.0 is running at:
[I 2026-08-30 08:01:44.269 ServerApp] http://0.0.0.0:8888/tree
[I 2026-08-30 08:12:35.905 ServerApp] 302 GET / (@172.18.0.1) 8.75ms
[I 2026-08-30 08:13:23.696 ServerApp] 302 GET / (@172.18.0.1) 6.43ms
[C 2026-08-30 08:13:33.459 ServerApp] received signal 15, stopping
[I 2026-08-30 08:13:33.538 ServerApp] Shutting down 5 extensions
```

**triggering actions**

Opening `http://localhost:8888` in a Windows browser via WSL2's automatic `localhost` port forwarding, sometime after this session's earlier `06-notebook-validate.sh` runs had already confirmed the notebook was in place and passing.

**hypothesis**

- the browser tab was pointed at a `jupyter-notebook` server instance that had, by the time of viewing, already stopped or was about to - not a defect in the `notebooks/` mount, naming, or contents themselves, since those were independently confirmed correct earlier in the same session via `07.TC.01`/`07.TC.10`.
- candidate causes: (a) a stale/cached browser tab reconnecting to a server no longer running, or (b) the whole container stack having been torn down by something outside this feature's own scripts (a Docker Desktop/WSL2 VM restart), not a bug this feature introduced.

**diagnostic steps**

| id          | seq | status | step                                                              | 
| ----------- | --- | ------ | ------------------------------------------------------------------ | 
| 07.IS.02.01 | 01  | closed | docker ps/ps -a: all 5 containers exited, same ~1 min window      | 
| 07.IS.02.02 | 02  | closed | docker logs jupyter-notebook: server had started+served fine      | 
| 07.IS.02.03 | 03  | closed | docker inspect Mounts: bind source + host files confirmed correct | 
| 07.IS.02.04 | 04  | closed | docker events for the window: empty (daemon-restart signature)    | 
| 07.IS.02.05 | 05  | closed | restart stack, confirm via GET /api/contents, not just ls         | 

**diagnostic details**

01. `docker ps -a --filter name=postgres-as01 --filter name=spark --filter name=jupyter` showed all 5 containers (`postgres-as01`, `spark-master`, `spark-worker-1`, `spark-worker-2`, `jupyter-notebook`) `Exited` within the same roughly 60-second window - not just `jupyter-notebook` alone, which rules out a `jupyter`-specific crash or a targeted `docker stop jupyter-notebook`.
02. `docker logs jupyter-notebook` confirmed the server had started correctly at 08:01:43 UTC with `Serving notebooks from local directory: /notebooks` (the right path), and had already served two successful `302 GET /` redirects (the browser's own requests) before receiving `signal 15` (SIGTERM) and shutting down at 08:13:33 UTC - so the server itself, its config, and its mount were never the problem; it was simply gone by the time (or moments after) the page was viewed.
03. `docker inspect jupyter-notebook --format '{{json .Mounts}}'` confirmed the bind mount's source was exactly `.../de-financial-accounting-demo/notebooks` the entire time, and a direct `ls` on that host path showed all 4 `.ipynb` files present with mtimes well before the container's 08:01:43 UTC start - the mount was never empty or misdirected.
04. `docker events --since ... --until ...` for the shutdown window returned nothing at all, which is itself the tell: a live daemon always logs a `stop`/`die` event per container; an empty history for a window where 5 containers demonstrably stopped means the daemon's own in-memory event buffer was reset - consistent with a full Docker Desktop/WSL2 VM restart, not anything issued from within this session or this feature's scripts (no `docker compose down`, `docker stop`, or `docker kill` was run against this stack in this session before that point).
05. `./scripts/01-dev-env-setup.sh` (verify-or-create, no data lost - postgres's volume and `notebooks/`'s bind-mounted host files were never touched by the restart) brought all 5 containers back `Up`. Rather than re-trust a screenshot, `curl http://localhost:8888/api/contents` - the same REST endpoint the browser's own file-list UI calls - was checked directly and returned all 4 files with `"type": "notebook"`, matching `docker exec jupyter-notebook ls /notebooks` exactly. [07.TC.11](#test-cases) captures this as a standing test case so a future recurrence is checked server-side first, not just visually.

**resolution**: not a defect in this feature's notebook workspace setup - the entire containerized stack stopped together, outside anything this feature's scripts did, most likely a Docker Desktop/WSL2 restart. Closed once the stack was brought back up and the notebook listing was reconfirmed both server-side (`GET /api/contents`) and, per the user, in the browser itself. No scope or design change follows from this - worth noting for future reference: if the browser ever again shows an empty file list, check `docker ps` for the running container before assuming a workspace bug, since a stale tab pointed at a server that's since stopped looks identical to a real empty mount.

## Guideline

## instructions

review and strictly follow these relevant skills when performing tasks for this feature implementation and working with this document

## relevant skills

- markdown-tables
- feature-implementation-guide
- jupyter-notebook-workspace
