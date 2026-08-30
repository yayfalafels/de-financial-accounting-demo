---
name: jupyter-notebook-workspace
description: creating, editing, deploying, validating, and serving this repo's Jupyter notebooks (notebooks/*.ipynb) via the jupyter-notebook container - nbformat JSON authoring, headless execution/validation, the live bind-mount deploy model, and browser-UI serving. Load before writing or editing any .ipynb file, running scripts/06-notebook-validate.sh, or troubleshooting the Jupyter container/UI.
---

## relevant skills

- markdown-tables - apply it to any table produced while documenting notebook work in `docs/features/07-jupyter-notebook-workspace-setup.md`
- feature-implementation-guide - the issues/diagnostics workflow (`07.IS.*`) that anomalies found while working on notebooks get logged into

## mental model - there is no deploy step

`docker/docker-compose.yml`'s `jupyter` service bind-mounts the repo's `notebooks/` directory straight into the container:

```yaml
volumes:
  - ../notebooks:/notebooks
```

A bind mount is not a copy. Writing a `.ipynb` file to `notebooks/` on the host **is** deploying it - the running container sees it immediately, no restart, no sync script, no `docker cp`. Do not build or suggest a push/pull sync step for notebooks (that pattern exists in this repo only for `docs/features/06-powerbi-dashboard-setup.md`'s Power BI workspace, which needs it because Power BI Desktop is Windows-only and can't open the WSL working tree directly - Jupyter has no such constraint).

The only things that ever need an explicit step:

- **containers not running at all** - `./scripts/01-dev-env-setup.sh` (verify-or-create; brings up postgres+spark+jupyter together)
- **a Python dependency changed** (e.g. a new pip pin in `docker/Dockerfile.spark`) - rebuild just `jupyter`: `docker compose --env-file .env -f docker/docker-compose.yml build jupyter && docker compose --env-file .env -f docker/docker-compose.yml up -d jupyter` (scoped - does not touch the already-running `postgres`/`spark-master`/`spark-worker-*` containers)

Full user-facing walkthrough: `docs/guides/jupyter-notebook-workspace.md`. Design rationale for every decision below: `docs/features/07-jupyter-notebook-workspace-setup.md`.

## creating or editing a notebook

No `nbformat`/`jupyter` package is available on the host by default - author `.ipynb` files as plain nbformat-v4.5 JSON directly (`json.dump`, not string templating - cell source must be a list of lines, not one blob). Minimal skeleton:

```python
def code_cell(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": source.splitlines(keepends=True)}

def markdown_cell(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)}

nb = {
    "cells": [markdown_cell("# Title\n"), code_cell("import os\n")],
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                 "language_info": {"name": "python", "version": "3.11"}},
    "nbformat": 4,
    "nbformat_minor": 5,
}
```

**Known gap**: cells written this way have no `id` field. `nbformat_minor: 5` requires one per cell - `nbconvert` only warns today (`MissingIDFieldWarning`) but its own changelog says this becomes a hard error in a future version. Fix it before committing rather than leaving the warning: run one identity conversion inside the container, which normalizes missing ids for free -

```bash
docker cp notebooks/<file>.ipynb jupyter-notebook:/notebooks/<file>.ipynb
docker exec jupyter-notebook jupyter nbconvert --to notebook --output /tmp/normalized.ipynb /notebooks/<file>.ipynb
docker cp jupyter-notebook:/tmp/normalized.ipynb notebooks/<file>.ipynb
```

Then confirm it's still unexecuted / still has the intended cells (`execution_count: None`, `outputs: []` for a fresh notebook) before committing - the identity pass only fixes structure, it does not run anything.

## validating a notebook (headless, scripted)

Never trust a raw `nbconvert` exit code alone - it only proves "no cell raised an exception," not "the checks the notebook is supposed to prove actually agreed." For the template connectivity-check notebook, the standing check is:

```bash
./scripts/06-notebook-validate.sh; echo "exit: $?"
```

It fails fast if `jupyter`/`spark-master`/`postgres-as01` aren't already running (it does not provision infrastructure), executes `00_template_connectivity_check.ipynb` to a fresh output path (never `--inplace` - a failed run must never corrupt the tracked, last-known-good notebook), and parses the executed notebook's own `[PASS]`/`[FAIL]` summary line rather than trusting `nbconvert`'s exit code alone. Writes a standard `.dev/logs/<ts>-07.IS-notebook-validate.log`.

To validate a *new* notebook the same way (no dedicated script yet), reuse the same shape by hand:

```bash
docker exec jupyter-notebook jupyter nbconvert --to notebook --execute \
    --ExecutePreprocessor.timeout=120 --output /tmp/executed.ipynb /notebooks/<file>.ipynb
```

Only copy `/tmp/executed.ipynb` back over the tracked file (`docker cp jupyter-notebook:/tmp/executed.ipynb notebooks/<file>.ipynb`) once you've confirmed it actually passed - per `docs/features/07-jupyter-notebook-workspace-setup.md` -> Design -> notebook output commit policy, committed notebooks keep their real executed output (no `nbstripout`), so what gets copied back becomes the git-tracked evidence.

**Never let a cell print a credential value or a connection string built from one.** `POSTGRES_DB`/`POSTGRES_USER`/`POSTGRES_PASSWORD` reach the kernel via the `jupyter` service's own `environment:` block in `docker-compose.yml` (added because a persistent kernel can't take credentials per-invocation the way this repo's other one-shot `docker exec -e ...` scripts do) - safe to read via `os.environ`, never safe to print, since committed output is real output.

## serving the browser UI

```
http://localhost:8888
```

Tokenless by design. Works from a Windows browser under WSL2 via automatic `localhost` port forwarding.

**If the file list looks empty or the page won't load**, check the container before suspecting the notebook workspace itself:

```bash
docker ps --filter name=jupyter-notebook
```

Not listed / `Exited` means the whole stack stopped (most commonly a Docker Desktop/WSL2 restart, not a notebook-specific problem - see `docs/features/07-jupyter-notebook-workspace-setup.md` -> Validate -> `07.IS.02` for the fully diagnosed instance of this). Fix: `./scripts/01-dev-env-setup.sh`, then reload. To confirm server-side without trusting a screenshot, hit the same endpoint the browser's file-list UI calls:

```bash
curl http://localhost:8888/api/contents
```

## when something unexpected happens

Log it under `docs/features/07-jupyter-notebook-workspace-setup.md` -> Validate -> Issues as the next `07.IS.<n>`, following the `feature-implementation-guide` skill's protocol (problem description / exception / triggering actions / hypothesis / diagnostic steps / diagnostic details) - including behavioral anomalies with no traceback, not only crashes. Two real examples already on file worth reading before re-diagnosing from scratch: `07.IS.01` (a pip pin with no wheel for the image's Python version) and `07.IS.02` (the empty-file-list symptom above).
