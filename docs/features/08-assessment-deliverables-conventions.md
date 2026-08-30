# Assessment Deliverables Conventions - Feature tracker
>Review the guidelines before performing any actions including edits on the document

## 08 (closed) assessment deliverables conventions

## Contents

- [Tasks](#tasks)
- [Scope](#scope)
- [References](#references)
- [Design](#design)
  - [deliverable-type taxonomy](#deliverable-type-taxonomy)
  - [directory & naming convention](#directory--naming-convention)
  - [deliverable markdown template](#deliverable-markdown-template)
  - [relationship to existing artifact conventions](#relationship-to-existing-artifact-conventions)
  - [per-assessment deliverable manifest](#per-assessment-deliverable-manifest)
  - [idempotency / rerun-safety](#idempotency--rerun-safety)
  - [environment & secrets](#environment--secrets)
  - [workflow validation runner](#workflow-validation-runner)
    - [assessment publishing site](#assessment-publishing-site)
    - [local documentation workflow](#local-documentation-workflow)
    - [github pages publishing workflow](#github-pages-publishing-workflow)
- [Test cases](#test-cases)
- [Edit locations](#edit-locations)
- [Implement](#implement)
- [Validate](#validate)
- [Guideline](#guideline)

## Tasks

| id    | seq | status  | milestone                                |
| ----- | --- | ------- | ---------------------------------------- |
| 08.01 | 01  | closed  | design                                   |
| 08.02 | 02  | closed  | edit locations and implementation guide  |
| 08.03 | 03  | closed  | directory scaffold and naming convention |
| 08.04 | 04  | closed  | cross-reference from assessment trackers |
| 08.05 | 05  | closed  | assessment documentation publishing      |
| 08.IS | 06  | closed  | validate                                 |

## Scope

decide, once, where every assessment's non-code deliverables live and in what format, so assessments 1-3 aren't each inventing their own layout - see [milestones.md](../milestones.md)'s `08. assessment deliverables conventions` entry for the milestone-level statement this tracker executes.

- covers the full non-code deliverable lists from the **assignment design doc**'s three "Expected Deliverables" sections:
    - **shared** exception datasets and DQ-control recommendations
    - **assessment 1** data profiling summaries and Source-to-Bronze reconciliation results
    - **assessment 2** GL reconciliation output, accounting-mapping validation, root-cause findings, reconciliation-framework design, and a business-facing summary
    - **assessment 3** profiling results, end-to-end reconciliation, exception tables, root-cause analysis, a data-lineage document, and performance-optimization recommendations
- default format is git-tracked markdown under one consistent per-assessment path (e.g. `results/<assessment-id>/...` or equivalent) - this feature picks the path convention and per-deliverable-type file naming, not the analytical content of any deliverable
- publishes the tracked assessment Markdown as a static GitHub Pages site built with MkDocs; the published site is a readable view of `results/`, not an alternate source of truth or a new location for authored deliverables
- provides a repeatable local installation, preview, build, and deployment workflow; deployment uses MkDocs' `gh-deploy` command to publish the generated `site/` output to the repository's `gh-pages` branch
- depends on, and does not re-decide, three conventions already established by earlier milestones:
    - the **jupyter notebook workspace tracker** (07) for where each assessment's working notebook lives
    - the **power bi dashboard setup tracker** (06)'s `.pbip` template/sync workflow for the dashboard/dashboard-mock-up deliverable
    - the **ai closed-loop validation tracker** (05)'s `reconciliation.rc_*` control tables for structured
    - DB-resident reconciliation results - this feature's job is the narrative/markdown write-up layer referencing those, not a second home for the same numbers
- does not implement any assessment's actual profiling, reconciliation, root-cause, lineage, or dashboard content - purely a directory/format/naming decision, exercised for real by the assessment milestones once their own trackers exist
- does not publish Power BI project files, databases, credentials, notebook outputs, or `.dev/` artifacts; dashboard and notebook deliverables remain linked source artifacts owned by Features 06 and 07
- closure per milestones.md: a documented directory convention exists and is referenced from each of the assessments' own feature scope once those trackers are created

## References

- **assignment design doc** `docs/design/assignment.md` (each assessment's "Expected Deliverables" section)
- **milestones** `docs/milestones.md` (08's scope/closure statement, and each assessment's condensed deliverable list)
- **ai closed-loop validation tracker** `docs/features/05-ai-closed-loop-validation.md` (`reconciliation.rc_*` control-table schema)
- **powerbi dashboard setup tracker** `docs/features/06-powerbi-dashboard-setup.md` (`.pbip` template convention)
- **jupyter notebook workspace tracker** `docs/features/07-jupyter-notebook-workspace-setup.md` (notebook naming/directory convention)
- **MkDocs deployment documentation** `https://www.mkdocs.org/user-guide/deploying-your-docs/` (`gh-deploy` behavior and GitHub Pages configuration)

## Design

### deliverable-type taxonomy

The **assignment design doc**'s three "Expected Deliverables" lists use different wording for what is structurally the same kind of write-up across assessments (e.g. "Data profiling summary" vs. "Profiling results") - this feature collapses them into one small closed set of deliverable-type slugs, applied per assessment rather than each assessment inventing its own file list. The notebook and dashboard/dashboard-mock-up deliverables are excluded here - they already have an owning convention ([07](07-jupyter-notebook-workspace-setup.md), [06](06-powerbi-dashboard-setup.md)) and this feature does not re-decide where those live, only how everything else references them (see [relationship to existing artifact conventions](#relationship-to-existing-artifact-conventions)).

| id | slug                   | deliverable title                 | a1 | a2 | a3 |
| -- | ---------------------- | --------------------------------- | -- | -- | -- |
| 01 | profiling-summary      | data profiling summary            | x  |    | x  |
| 02 | reconciliation-results | reconciliation results write-up   | x  | x  | x  |
| 03 | exception-dataset      | exception dataset                 | x  | x  | x  |
| 04 | root-cause-analysis    | root-cause analysis               | x  | x  | x  |
| 05 | dq-recommendations     | DQ-control recommendations        | x  |    |    |
| 06 | mapping-validation     | accounting mapping validation     |    | x  |    |
| 07 | framework-design       | reconciliation framework design   |    | x  |    |
| 08 | business-summary       | business-facing summary           |    | x  |    |
| 09 | lineage-doc            | data-lineage document             |    |    | x  |
| 10 | performance-notes      | performance-optimization notes    |    |    | x  |
| 11 | presentation-summary   | five-minute presentation summary  |    |    | x  |

01. `a1`/`a2`/`a3` are `assessment-1`/`assessment-2`/`assessment-3`, matching the `assessment_id` spelling `rc_batch_control` already writes ([05](05-ai-closed-loop-validation.md#reconciliation-control-schema)) - one spelling for the concept everywhere, not a directory-name variant of a DB value.
02. row 02 (`reconciliation-results`) is the narrative write-up of a batch's numbers, not a duplicate of `reconciliation.rc_reconciliation_results` - see [relationship to existing artifact conventions](#relationship-to-existing-artifact-conventions).

### directory and naming convention

One folder per assessment id under `results/`, one flat file per taxonomy row that assessment has checked, named `<assessment-id>-<slug>.md` - the same "flat, one path per concept, no further subfolders" precedent [07](07-jupyter-notebook-workspace-setup.md#notebook-naming--directory-conventions) already set for `notebooks/`, applied here instead of nesting by deliverable-type across assessments:

```
results/
├── assessment-1/
│   ├── assessment-1-profiling-summary.md
│   ├── assessment-1-reconciliation-results.md
│   ├── assessment-1-exception-dataset.md
│   ├── assessment-1-root-cause-analysis.md
│   ├── assessment-1-dq-recommendations.md
│   └── README.md
├── assessment-2/
│   ├── assessment-2-reconciliation-results.md
│   ├── assessment-2-exception-dataset.md
│   ├── assessment-2-root-cause-analysis.md
│   ├── assessment-2-mapping-validation.md
│   ├── assessment-2-framework-design.md
│   ├── assessment-2-business-summary.md
│   └── README.md
└── assessment-3/
    ├── assessment-3-profiling-summary.md
    ├── assessment-3-reconciliation-results.md
    ├── assessment-3-exception-dataset.md
    ├── assessment-3-root-cause-analysis.md
    ├── assessment-3-lineage-doc.md
    ├── assessment-3-performance-notes.md
    ├── assessment-3-presentation-summary.md
    └── README.md
```

### deliverable markdown template

Every deliverable file (the `README.md` index is a separate, derived shape - see [per-assessment deliverable manifest](#per-assessment-deliverable-manifest)) opens with the same two-part shape, so a reader lands in a known structure regardless of which assessment or deliverable-type they open:

- an H1 title combining the assessment id and the taxonomy row's deliverable title
- a **Sources** section, always present, naming exactly which executable/queryable artifact the write-up is derived from - a notebook path, a `batch_id`, a `.pbip` page - per [relationship to existing artifact conventions](#relationship-to-existing-artifact-conventions). A source that is a tracked repo file links to its actual GitHub blob URL rather than naming a bare local path [01], so the published site's reader can open it directly; an untracked/gitignored artifact (e.g. `data/mock/issue-log.csv`) stays a plain path with a note that it isn't in the repo.

The page itself carries no status marker [02] - status lives only in the per-assessment manifest, see [per-assessment deliverable manifest](#per-assessment-deliverable-manifest).

Illustrative shape only, not a literal stub file this feature ships - `results/assessment-1/assessment-1-profiling-summary.md`:

```markdown
# Assessment 1 - Data Profiling Summary

## Sources

- notebook: [assessment1_profiling.ipynb](https://github.com/<org>/<repo>/blob/main/notebooks/assessment1_profiling.ipynb)
- batch: `reconciliation.rc_batch_control.batch_id = <n>`
```

01. amended alongside AS01 task 1 ([09](../assessments/09-as01-data-profiling-reconciliation.md)) - `scripts/07-deliverables-scaffold.sh` derives the blob base from `git remote get-url origin` plus `GITHUB_DEFAULT_BRANCH` (default `main`) rather than hard-coding the org/repo, so a stub it creates is portable across forks/clones.

02. amended during AS01 task 1 ([09](../assessments/09-as01-data-profiling-reconciliation.md)): the original design put a plain-text `status: draft`/`final` line directly under the title. That duplicated the manifest's own status column and drifted out of sync in practice, and a two-state vocabulary couldn't express a deliverable that answers one task of several while the file overall stays unfinished - the manifest's `status` column is now the single place this is tracked, with a third value, `open`, for exactly that in-process case.

### relationship to existing artifact conventions

This feature adds one narrative-markdown layer on top of three conventions already fixed by earlier milestones, without duplicating what any of them already own:

- **notebook** ([07](07-jupyter-notebook-workspace-setup.md)) - the executable analysis stays in `notebooks/`; a deliverable file's **Sources** section points at it by path, it never inlines a copy of notebook code or output.
- **dashboard** ([06](06-powerbi-dashboard-setup.md)) - the `.pbip` project stays under `powerbi/`; assessment 1's dashboard-mock-up and assessment 3's dashboard deliverable are satisfied by that existing template plus a short pointer file in `results/`, not a second dashboard location.
- **structured reconciliation numbers** ([05](05-ai-closed-loop-validation.md#reconciliation-control-schema)) - `reconciliation.rc_reconciliation_results` stays the source of truth for measured values; a `reconciliation-results.md` file is the write-up of what one `batch_id`'s numbers mean, not a re-exported copy of the same rows - re-querying the table is always cheaper and more current than trusting a markdown snapshot.

This closes the deferral [07](07-jupyter-notebook-workspace-setup.md#notebook-output-commit-policy) explicitly left open ("where each assessment's *other* non-notebook deliverables live is left to the assessment deliverables conventions milestone").

### per-assessment deliverable manifest

Each `results/<assessment-id>/README.md` is the concrete artifact [milestones.md](../milestones.md)'s closure line asks for ("referenced from each of the assessments own feature scope"): it lists exactly the [deliverable-type taxonomy](#deliverable-type-taxonomy) rows checked for that assessment, each linked to its file, plus the notebook and dashboard paths as reference-only rows owned by 07/06. `status` is one of `draft` (not started or a stub), `open` (in-process - answers some but not all of what the deliverable type expects), or `final` (complete and reviewed); it is authored directly in this manifest and carried forward unchanged on every scaffold rerun, never derived from the deliverable page itself (see the [deliverable markdown template](#deliverable-markdown-template) amendment). Once an assessment's own tracker (09, 10, or 11) exists, its Scope section links this README instead of re-listing the deliverable set - one statement of what an assessment must produce, not two that can drift apart.

### idempotency / rerun-safety

- **deliverable files**: verify-or-create, the same convention [07](07-jupyter-notebook-workspace-setup.md#idempotency--rerun-safety) already used for notebook stubs - created with the [template](#deliverable-markdown-template) skeleton only if missing at its expected path; a file already started is never touched or overwritten.
- **README**: regenerated in full on every scaffold run, since it's a derived index rather than authored content - but each row's `status` value already on disk is read back and carried forward before the file is rewritten, so a hand-set `open`/`final` survives the regeneration; a brand new row defaults to `draft`.

### environment & secrets

No new variables and no secrets - the scaffold script only creates and lists local files under `results/`, the same no-DB, local-file-only shape [06](06-powerbi-dashboard-setup.md#environment--secrets)'s sync script already has for its own operations.

### workflow validation runner

`scripts/07-deliverables-scaffold.sh` (next free script number after `06-notebook-validate.sh`) turns [milestones.md](../milestones.md)'s closure line into something rerunnable rather than a one-time manual folder creation:

1. For each assessment id, creates any missing deliverable file from [deliverable-type taxonomy](#deliverable-type-taxonomy)'s checked rows, per [idempotency / rerun-safety](#idempotency--rerun-safety) - never touching a file that already exists.
2. Regenerates each `results/<assessment-id>/README.md` from the taxonomy table, carrying forward each row's `status` already recorded in the existing manifest (`draft` for a new row), so the manifest always reflects the deliverable set actually on disk while `status` stays authored, not derived.
3. Runs in a `--check` mode too - reports missing files or a stale README without writing anything, the mode a later assessment milestone's own validation step calls before declaring its deliverables closed.
4. Logs its run under `.dev/logs/`, per the `feature-implementation-guide` skill's `<ts>-<task-id>-<name>.log` naming convention, printing one `[PASS]`/`[FAIL]` line per assessment id plus an overall summary.

### assessment publishing site

`mkdocs.yml` is the single site configuration. It sets `site_name: Financial Accounting Assessments`, `docs_dir: results`, `site_dir: site`, and the built-in `mkdocs` theme so no additional theme dependency is required. Its explicit navigation starts with `index.md`, then includes the three assessment manifests; each manifest remains the entry point to its deliverables. This intentionally publishes `results/` only, preventing internal feature trackers and design notes from becoming public merely because they are stored under `docs/`.

`results/index.md` is a concise site landing page created by the scaffold if missing. It links to the three assessment manifests and explains that the pages report the current `draft` or `final` status. It is authored content after creation and follows the same never-overwrite rule as deliverables.

### local documentation workflow

Declare MkDocs in `pyproject.toml` as an optional `docs` dependency group pinned to the supported 1.x range: `mkdocs>=1.6,<2`. Install it from the repository root with `python -m pip install '.[docs]'`. Use `python -m mkdocs serve` for a local preview and `python -m mkdocs build --strict` for a production-equivalent validation build. The ignored `site/` directory is build output only and is never committed.

### github pages publishing workflow

`scripts/08-assessment-site.sh` owns the site commands and writes a Feature 08 log for each invocation. Its `serve`, `build`, and `deploy` subcommands run `python -m mkdocs serve`, `python -m mkdocs build --strict`, and `python -m mkdocs gh-deploy --force` respectively. `deploy` builds from the current tracked worktree and commits the generated output to `gh-pages` through the configured `origin` remote; it does not push the current feature branch.

Before the first deployment, authenticate the local Git client or GitHub CLI with permission to push the repository, confirm `origin` is the intended GitHub repository, and set the repository's GitHub Pages source to the `gh-pages` branch at `/ (root)`. This repository setting is a one-time human GitHub action, not a file the script can safely change. Deploy only from a reviewed branch with a clean index so uncommitted assessment evidence is never silently published.

## Test cases

_test strategy_

The scaffold is validated at three layers so its generated files, derived manifests, and non-writing mode are independently checked:

1. **script self-report** - the scaffold's `[PASS]`/`[FAIL]` lines and timestamped log demonstrate each expected stage ran.
2. **direct filesystem inspection** - `find`, `test -f`, and `cmp` examine the result paths and preserved authored content without trusting the scaffold's summary.
3. **content inspection** - `grep` and an independent Markdown-table check verify required headings, source references, statuses, links, and table shape.

_test cases_

| id       | task  | layer      | check                                      |
| -------- | ----- | ---------- | ------------------------------------------ |
| 08.TC.01 | 08.03 | script     | normal run creates all missing paths       |
| 08.TC.02 | 08.03 | direct-fs  | 18 deliverables and 3 manifests exist [01] |
| 08.TC.03 | 08.03 | content    | each deliverable has title, status, Sources |
| 08.TC.04 | 08.03 | content    | manifests link only expected rows [02]     |
| 08.TC.05 | 08.03 | direct-fs  | authored deliverable survives rerun        |
| 08.TC.06 | 08.03 | script     | rerun reports no file overwrites           |
| 08.TC.07 | 08.03 | script     | `--check` passes after normal run          |
| 08.TC.08 | 08.03 | script     | `--check` fails on removed required file   |
| 08.TC.09 | 08.03 | direct-fs  | `--check` writes no files or README        |
| 08.TC.10 | 08.03 | content    | log name and status markers match policy   |
| 08.TC.11 | 08.05 | build      | strict MkDocs build succeeds               |
| 08.TC.12 | 08.05 | content    | navigation exposes only `results/` content |
| 08.TC.13 | 08.05 | script     | wrapper rejects an unknown command         |
| 08.TC.14 | 08.05 | deployment | `gh-deploy` updates `gh-pages` [03]        |

01. **08.TC.02** expects five Assessment 1 files, six Assessment 2 files, and seven Assessment 3 files; the three README manifests are checked separately.
02. **08.TC.04** requires the notebook and dashboard reference rows, the checked taxonomy rows only, relative links to existing deliverables, and each row's `status` value carried forward from the existing manifest.
03. **08.TC.14** requires a reviewed clean worktree, valid GitHub authentication, and the Pages source configured to `gh-pages` root. Check the deployed commit with `git ls-remote origin gh-pages`, then open the repository Pages URL and confirm its assessment navigation matches the local build.

**tools**

```bash
cd /home/taylor-hickem/repos/de-financial-accounting-demo
./scripts/07-deliverables-scaffold.sh
./scripts/07-deliverables-scaffold.sh --check
python -m pip install '.[docs]'
./scripts/08-assessment-site.sh build
find results -type f | sort
grep -RE '\| (draft|open|final) +\|$' results/*/README.md
awk '/^\|/ && length($0) >= 115 { print FILENAME ":" FNR ": table row is too long"; bad = 1 } END { exit bad }' results/**/*.md
```

## Edit locations

| id       | path                                                       | change                         |
| -------- | ---------------------------------------------------------- | ------------------------------ |
| 08.EL.01 | `scripts/07-deliverables-scaffold.sh`                     | new scaffold and check runner  |
| 08.EL.02 | `results/assessment-1/README.md`                          | generated Assessment 1 index   |
| 08.EL.03 | `results/assessment-1/assessment-1-profiling-summary.md` | new deliverable stub           |
| 08.EL.04 | `results/assessment-1/assessment-1-reconciliation-results.md` | new deliverable stub       |
| 08.EL.05 | `results/assessment-1/assessment-1-exception-dataset.md` | new deliverable stub           |
| 08.EL.06 | `results/assessment-1/assessment-1-root-cause-analysis.md` | new deliverable stub         |
| 08.EL.07 | `results/assessment-1/assessment-1-dq-recommendations.md` | new deliverable stub          |
| 08.EL.08 | `results/assessment-2/README.md`                          | generated Assessment 2 index   |
| 08.EL.09 | `results/assessment-2/assessment-2-reconciliation-results.md` | new deliverable stub       |
| 08.EL.10 | `results/assessment-2/assessment-2-exception-dataset.md` | new deliverable stub           |
| 08.EL.11 | `results/assessment-2/assessment-2-root-cause-analysis.md` | new deliverable stub         |
| 08.EL.12 | `results/assessment-2/assessment-2-mapping-validation.md` | new deliverable stub          |
| 08.EL.13 | `results/assessment-2/assessment-2-framework-design.md` | new deliverable stub           |
| 08.EL.14 | `results/assessment-2/assessment-2-business-summary.md` | new deliverable stub           |
| 08.EL.15 | `results/assessment-3/README.md`                          | generated Assessment 3 index   |
| 08.EL.16 | `results/assessment-3/assessment-3-profiling-summary.md` | new deliverable stub           |
| 08.EL.17 | `results/assessment-3/assessment-3-reconciliation-results.md` | new deliverable stub       |
| 08.EL.18 | `results/assessment-3/assessment-3-exception-dataset.md` | new deliverable stub           |
| 08.EL.19 | `results/assessment-3/assessment-3-root-cause-analysis.md` | new deliverable stub         |
| 08.EL.20 | `results/assessment-3/assessment-3-lineage-doc.md`       | new deliverable stub           |
| 08.EL.21 | `results/assessment-3/assessment-3-performance-notes.md` | new deliverable stub           |
| 08.EL.22 | `results/assessment-3/assessment-3-presentation-summary.md` | new deliverable stub        |
| 08.EL.23 | `results/index.md`                                        | generated site landing page    |
| 08.EL.24 | `mkdocs.yml`                                               | new results-only site config   |
| 08.EL.25 | `pyproject.toml`                                           | add optional MkDocs dependency |
| 08.EL.26 | `scripts/08-assessment-site.sh`                            | new site command wrapper       |

01. **08.EL.01** is the only hand-authored implementation file. It holds the taxonomy as Bash data and creates the remaining locations, avoiding a second hand-maintained manifest source.
02. **08.EL.02, 08.EL.08, 08.EL.15** are generated indexes. Do not edit them by hand because each scaffold run replaces them with the current filesystem-derived view.
03. **08.EL.03-08.EL.07, 08.EL.09-08.EL.14, 08.EL.16-08.EL.22** are verify-or-create authored deliverables. The scaffold must never rewrite an existing file.
04. **08.EL.23** is verify-or-create authored content. It is intentionally outside an assessment directory so it can be MkDocs' landing page.
05. **08.EL.24, 08.EL.25, 08.EL.26** are hand-authored publishing infrastructure. They must never contain a deployment token, GitHub personal access token, or Pages URL tied to one user's account.

No `.env`, `.env.sample`, database, notebook, or Power BI template change is required. `.gitignore` already excludes MkDocs' `site/` build directory. The scripts read existing `LOGS_DIR`, `TIMEZONE`, and `TIMESTAMP_FORMAT` settings and operate only on tracked content plus the ignored generated site.

## Implement

Implementation order is runner -> missing deliverable stubs -> generated manifests -> normal and negative-path checks. This keeps the taxonomy in one executable source and makes every later assessment consume the same paths.

### 1. Scaffold runner

edit locations: `08.EL.01`

Create an executable Bash script using `set -uo pipefail`. Resolve `REPO_ROOT` from the script location, change to it, and source `.env` when present. Set defaults for `LOGS_DIR`, `TIMEZONE`, and `TIMESTAMP_FORMAT`; then set `FEATURE_ID=08.03` and `TASK_NAME=deliverables-scaffold` before constructing `${LOGS_DIR}/$(TZ="$TIMEZONE" date +"$TIMESTAMP_FORMAT")-${FEATURE_ID}-${TASK_NAME}.log`.

Implement `log()` to timestamp and `tee -a` every message to the log. Parse only zero or one argument: no argument selects write mode, `--check` selects validation-only mode, and any other input logs `[FAIL]`, prints usage, and exits non-zero. Create `LOGS_DIR` before the first log write, but do not create `results/` in check mode.

Represent the taxonomy as explicit assessment/slug/title triples in the script. Use exactly the 18 deliverables in `08.EL.03-08.EL.07`, `08.EL.09-08.EL.14`, and `08.EL.16-08.EL.22`; no dashboard slug is created because Dashboard ownership remains with Feature 06. Keep title strings in the script so both stubs and manifests draw from the same source.

For each triple, derive `results/<assessment-id>/<assessment-id>-<slug>.md`. In write mode, `mkdir -p` its parent and create the file only when absent. Each new stub contains the H1 `# Assessment N - <deliverable title>`, a blank line, and `## Sources` (no status line on the page - see the [deliverable markdown template](#deliverable-markdown-template) amendment); then include a notebook source for its assessment and a `reconciliation.rc_batch_control.batch_id = <n>` source when reconciliation output is relevant. Log `[PASS]` for both created and preserved files, using distinct action text. In check mode, missing files log `[FAIL]` and set an accumulated failure status; existing files log `[PASS]` and are never modified. Create `results/index.md` only when absent with an H1 and relative links to the three manifests, giving MkDocs its site root without overwriting authored landing-page content.

### 2. Manifest generation

edit locations: `08.EL.02, 08.EL.08, 08.EL.15`

After all required deliverables for one assessment have been checked, generate its README content in a temporary file. Use an H1 naming the assessment, a brief single-line statement, and one fixed-width Markdown table with `id` as its first column. Include one row for each taxonomy deliverable with its relative link and the `status` value already recorded for that row in the existing manifest, carried forward unchanged (`draft` for a row with no prior manifest entry). Add notebook and dashboard rows as reference-only entries that point to the Feature 07 notebook path and Feature 06 Power BI template path without claiming the scaffold owns either artifact.

In write mode, replace the README atomically with `mv` only when the generated temporary file differs from the existing README. Before replacement, compare the expected slug set to the deliverable files already on disk and fail if replacement would omit a required taxonomy file; extra authored files may remain on disk but must not be presented as taxonomy deliverables. In check mode, compare the generated content with the checked-in README using `cmp -s`; a missing or different README logs `[FAIL]` and is not written.

### 3. Exit handling and diagnostics

edit locations: `08.EL.01`

Continue checking all three assessments after an individual failure so a single `--check` run inventories every missing or stale artifact. Print one assessment-level `[PASS]` or `[FAIL]` summary, followed by an overall summary and the log path. Exit zero only when no missing stub or stale manifest was found; otherwise exit non-zero. A normal write run must also fail when it cannot create a path or regenerate a manifest.

### 4. Execute acceptance checks

edit locations: `08.EL.01-08.EL.22`

Run the normal command to create the directory scaffold, then run `--check` to prove the generated state is current. Change a non-status line in one deliverable, rerun the normal command, and use `cmp` or `git diff` to prove the authored edit remains. Remove a required stub, run `--check`, and verify a non-zero exit with no recreated file; restore it only through a normal write run. Finally inspect the three manifests and use the command in [Test cases](#test-cases) to verify every Markdown table row is below 115 characters, padded, and begins with an `id` column.

### 5. MkDocs site configuration and dependency

edit locations: `08.EL.24, 08.EL.25`

Add the `docs` optional dependency group to `pyproject.toml` with `mkdocs>=1.6,<2`; leave the runtime `dependencies` list empty. Create `mkdocs.yml` at the repository root with the site name, `docs_dir: results`, `site_dir: site`, built-in `mkdocs` theme, and an explicit navigation containing the landing page and three assessment README manifests. Do not use an external theme, plugin, or `extra` value that assumes a public URL because the generated site must work both locally and at the repository's eventual Pages URL.

### 6. Site command wrapper and deployment

edit locations: `08.EL.26`

Create an executable Bash wrapper using `set -uo pipefail`, the repository-root resolution, optional `.env` load, `LOGS_DIR` defaults, timestamped `08.05-assessment-site-<command>.log` name, and `log()` implementation already specified for the scaffold. Accept exactly `serve`, `build`, or `deploy`. Each mode first confirms `python -m mkdocs --version` succeeds and logs `[FAIL]` with the `python -m pip install '.[docs]'` remediation when it does not.

Dispatch `serve` to `python -m mkdocs serve`, preserving the interactive process exit code. Dispatch `build` to `python -m mkdocs build --strict`; log the resulting `site/` location on success. Before `deploy`, reject a dirty worktree with `git diff --quiet` and `git diff --cached --quiet`, confirm `origin` resolves, run the same strict build, and only then run `python -m mkdocs gh-deploy --force`. Log the selected command, its `[PASS]` or `[FAIL]` result, and the log path. Never pass credentials as command arguments or write them to the log.

### 7. Publish GitHub Pages

edit locations: `08.EL.24, 08.EL.26`

After a reviewed branch passes the scaffold check and `08.EL.26 build`, authenticate the local Git/GitHub client with repository push permission. In GitHub repository settings, choose Pages deployment from branch `gh-pages` at `/ (root)` once; then run `./scripts/08-assessment-site.sh deploy`. Confirm `git ls-remote origin gh-pages` returns the new branch head and review the Pages URL manually. Subsequent publishes repeat the same deploy command and replace only the generated site branch content.

## Validate

**Issues**

- inventory all first out exceptions and issues encountered in this table
- for each issue, create an issue section and use this section to document diagnostics and resolution steps

| id       | seq | status  | issue                                     |
| -------- | --- | ------- | ------------------------------------------ |
| 08.IS.01 | 01  | closed | MkDocs module unavailable for site build   |

_08.IS.01 (closed) MkDocs module unavailable for site build_

**problem description**

The new `08-assessment-site.sh build` command could not start its strict static-site build because the selected Python environment did not yet contain the MkDocs dependency declared by this feature.

**exception**

```log
```log
[FAIL] [08.05] MkDocs unavailable; run: python -m pip install '.[docs]'
```
```

**triggering actions**

Ran `bash scripts/08-assessment-site.sh build` after the deliverable scaffold's write and `--check` modes completed successfully.

**hypothesis**

- use hypothesis framing until a validated fix is applied

The project has no pre-existing documentation dependency installation, so `python -m mkdocs --version` fails until the new `docs` optional dependency group is installed in the active Python environment.

**diagnostic steps**

- first out exception is NOT a diagnostic step
- diagnostic steps reveal information or apply a fix
- assume re-run and validation, these are not diagnostic steps
- keep the step description brief, use the diagnostics details section to elaborate actions and learnings for each step

| id          | seq | status  | step                                      |
| ----------- | --- | ------- | ------------------------------------------ |
| 08.IS.01.01 | 01  | closed | inspect the wrapper's MkDocs preflight     |
| 08.IS.01.02 | 02  | closed | install the declared `docs` dependency     |

**diagnostic details**

01. (closed) The wrapper's `require_mkdocs()` preflight ran before any `site/` write and returned exit status 1 with the exact project-local installation command. This confirmed a missing local dependency rather than malformed `mkdocs.yml` or generated assessment content.

02. (closed) Installed `mkdocs>=1.6,<2` into `.venv` using the configured Python package installer. `.venv/bin/python -m mkdocs --version` reported MkDocs 1.6.1, `gh-deploy --help` returned successfully, and `08-assessment-site.sh build` completed `mkdocs build --strict` with a generated `site/` directory.

**validation evidence**

01. (closed) 08.TC.01, 08.TC.02, 08.TC.03, 08.TC.04, 08.TC.07, and 08.TC.11 passed: the write scaffold created `results/index.md`, 18 deliverables, and three manifests; `--check` found them current; and the strict MkDocs build completed successfully.

02. (closed) 08.TC.05 and 08.TC.06 passed: a SHA-256 comparison before and after a normal rerun confirmed an existing deliverable was unchanged. 08.TC.07 and 08.TC.09 passed: a full hash of all `results/` files was identical before and after `--check`.

03. (closed) 08.TC.08 passed: moving one required deliverable aside made `--check` exit non-zero and it did not recreate the file. A normal write run restored the missing file. 08.TC.10 passed through the timestamped logs emitted by both scaffold modes. 08.TC.12 passed: the strict build generated all four expected page entry points and contained no `docs/features`, `docs/design`, `.secrets`, or `.dev/` content. 08.TC.13 passed: an invalid site command exited non-zero.

04. (pending) 08.TC.14 requires the user's one-time GitHub Pages setup and an authenticated remote deployment. The deployment wrapper deliberately rejects the current dirty worktree, so the reviewed source changes must be committed before it can publish.

05. (closed) 08.TC.14 passed: after the user confirmed the reviewed source changes were committed and pushed, Git authentication was available, and GitHub Pages was enabled from `gh-pages` at `/ (root)`, `08-assessment-site.sh deploy` completed successfully. `git ls-remote origin gh-pages` reported `e42e1d4cd2244f471f24b7b43cafc6996a4bcd1b`, and the published landing page loaded at `https://yayfalafels.github.io/de-financial-accounting-demo/` with links to Assessment 1, Assessment 2, and Assessment 3.

**user actions**

01. (completed) Committed and pushed the reviewed Feature 08 source changes before deployment, satisfying the wrapper's clean-worktree guard.

02. (completed) Confirmed this machine's Git credentials could push to `origin` without sharing a credential in the tracker or chat.

03. (completed) In GitHub repository Settings > Pages, selected **Deploy from a branch**, chose `gh-pages`, selected `/ (root)`, and saved the setting.

04. (completed) Opened the published site in a browser and confirmed the landing-page navigation after deployment.

## Guideline

## instructions

review and strictly follow these relevant skills when performing tasks for this feature implementation and working with this document

## relevant skills

- markdown-tables
- feature-implementation-guide
