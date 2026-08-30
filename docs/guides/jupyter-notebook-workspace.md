# Jupyter Notebook Workspace Guide

How to start, open, edit, and validate the notebook workspace that `docs/features/07-jupyter-notebook-workspace-setup.md` set up - the Jupyter container, the `notebooks/` directory, and the browser UI.

## Contents

- [How it actually works - no deploy step](#how-it-actually-works---no-deploy-step)
- [Starting the stack](#starting-the-stack)
- [Opening the notebook UI in your browser](#opening-the-notebook-ui-in-your-browser)
- [What's in notebooks/](#whats-in-notebooks)
- [Editing a notebook](#editing-a-notebook)
- [Validating the template notebook](#validating-the-template-notebook)
- [Stopping the stack](#stopping-the-stack)
- [Troubleshooting](#troubleshooting)

## How it actually works - no deploy step

There is **no sync, push, or deploy step for notebooks** - unlike the Power BI workspace (`docs/features/06-powerbi-dashboard-setup.md`), which needs a `push`/`pull` script because Power BI Desktop is a Windows-only app that can't open this repo's WSL working tree directly.

Jupyter has no such constraint - it runs in the same Docker/Linux environment as everything else in this repo, so `docker/docker-compose.yml`'s `jupyter` service mounts the repo's `notebooks/` directory straight into the container as a **live bind mount**:

```yaml
volumes:
  - ../notebooks:/notebooks
```

A bind mount is not a copy - it's the same files, visible from both sides at once:

- edit a `.ipynb` file on the host (with a script, an editor, or Claude Code) -> the change is visible inside the container instantly, no restart needed
- edit/run a notebook from the browser UI -> the change lands directly on the host's `notebooks/` directory, ready to `git add`/`git commit` right away

So "loading notebooks into the container" isn't a separate action - it already happened the moment the file was written to `notebooks/`. The only things that ever need an explicit step are standing the containers up in the first place, and (occasionally) rebuilding the image if a Python dependency changes - covered below.

## Starting the stack

From the repo root:

```bash
./scripts/01-dev-env-setup.sh
```

Verify-or-create - safe to run whether or not postgres/spark/jupyter are already up. Brings up (or confirms already running): `postgres-as01`, `spark-master`, `spark-worker-1`, `spark-worker-2`, and `jupyter-notebook`. Takes a few seconds if everything's already up, a few minutes on a first build.

Check it worked:

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}'
```

All 5 should show `Up`.

## Opening the notebook UI in your browser

```
http://localhost:8888
```

That's it - no token, no password (tokenless by design; see `docs/features/03-dev-env-setup-spark-container.md` -> Design -> environment & secrets). On WSL2, `localhost` forwards to Windows automatically, so this works the same from a Windows browser as it would from a native Linux desktop. It redirects to `/tree`, the file browser.

## What's in notebooks/

| file                                     | purpose                                                   | 
| ---------------------------------------- | --------------------------------------------------------- | 
| `00_template_connectivity_check.ipynb`   | proves postgres (JDBC + psycopg2) and Spark are reachable | 
| `assessment1_profiling.ipynb`            | assessment 1 working notebook (stub)                      | 
| `assessment2_gl_reconciliation.ipynb`    | assessment 2 working notebook (stub)                      | 
| `assessment3_regulatory_dashboard.ipynb` | assessment 3 working notebook (stub)                      | 

Naming convention and full design rationale: `docs/features/07-jupyter-notebook-workspace-setup.md` -> Design -> notebook naming & directory conventions.

## Editing a notebook

Open the file in the browser UI and edit/run cells normally - changes save straight to `notebooks/<file>.ipynb` on the host, immediately visible to `git status`.

Before committing, per the feature's [notebook output commit policy](../features/07-jupyter-notebook-workspace-setup.md#notebook-output-commit-policy): use **Kernel -> Restart Kernel and Run All Cells** so the committed outputs reflect one clean top-to-bottom run, not a stale or out-of-order one. Never let a cell print a credential value or a connection string built from one - committed output is real, git-tracked output.

## Validating the template notebook

Rather than eyeballing the browser, the scripted check re-executes `00_template_connectivity_check.ipynb` headlessly and parses its own `[PASS]`/`[FAIL]` summary line:

```bash
./scripts/06-notebook-validate.sh; echo "exit: $?"
```

Fails fast if the containers aren't up (it doesn't provision infrastructure itself - run `01-dev-env-setup.sh` first). Writes a timestamped log under `.dev/logs/` and never overwrites the tracked notebook on a failed run - see `docs/features/07-jupyter-notebook-workspace-setup.md` -> Design -> workflow validation runner.

## Stopping the stack

```bash
docker compose --env-file .env -f docker/docker-compose.yml down
```

Notebook files are untouched either way (they live on the host, not inside the container) - stopping or removing the containers never loses anything under `notebooks/`.

## Troubleshooting

**Browser shows an empty file list / can't connect.** Check the container is actually running before assuming anything is wrong with the notebook setup:

```bash
docker ps --filter name=jupyter-notebook
```

If it's not listed (or shows `Exited`), the whole stack has stopped - most commonly a Docker Desktop/WSL2 restart, unrelated to anything notebook-specific. Rerun `./scripts/01-dev-env-setup.sh` and reload the page. A stale browser tab pointed at a server that's since stopped looks identical to a genuinely empty mount - this exact scenario is written up as `docs/features/07-jupyter-notebook-workspace-setup.md` -> Validate -> `07.IS.02`.

**Want server-side proof instead of trusting a screenshot:**

```bash
curl http://localhost:8888/api/contents
```

Lists every file the browser's own file-list UI would show, straight from the same REST endpoint.
