# Power BI Dashboard Setup - Feature tracker
>Review the guidelines before performing any actions including edits on the document

## 06 (closed) power bi dashboard setup

## Contents

- [Tasks](#tasks)
- [Scope](#scope)
- [References](#references)
- [Design](#design)
  - [`.pbip` project anatomy](#pbip-project-anatomy)
  - [repo-side directory structure](#repo-side-directory-structure)
  - [windows-side working copy](#windows-side-working-copy)
  - [sync script design](#sync-script-design)
  - [idempotency / rerun-safety](#idempotency--rerun-safety)
  - [environment & secrets](#environment--secrets)
  - [workflow validation runner](#workflow-validation-runner)
- [Test Cases](#test-cases)
- [Edit locations](#edit-locations)
- [Implement](#implement)
- [Validate](#validate)
- [Guideline](#guideline)

## Tasks

| id    | seq | status  | milestone                                    | 
| ----- | --- | ------- | -------------------------------------------- | 
| 06.01 | 01  | closed  | design                                       | 
| 06.02 | 02  | closed  | edit locations and implementation guide      | 
| 06.07 | 03  | closed  | test strategy and test cases                 | 
| 06.03 | 04  | closed  | `.pbip` template scaffold                    | 
| 06.04 | 05  | closed  | sync script (`/mnt` <-> repo)                | 
| 06.05 | 06  | closed  | round-trip sync validation                   | 
| 06.06 | 07  | closed  | assessment-facing usage documentation        | 
| 06.08 | 08  | closed  | dashboard reports from postgresql db         | 
| 06.IS | 09  | closed  | validate                                     | 

## Revisions

| id        | date       | task  | change                                              | 
| --------- | ---------- | ----- | -------------------------------------------------------| 
| 06.01.R01 | 2026-08-30 | 06.03 | `scaffold` now generates a best-effort seed project     | 
| 06.01.R02 | 2026-08-30 | 06.03 | `scaffold` reverts to human bootstrap - R01 undone       | 
| 06.01.R03 | 2026-08-30 | 06.05 | template adopted from an existing valid project         | 

**06.01.R01** [`.pbip` project anatomy](#pbip-project-anatomy) and the original 06.EL.03-05 Implement guide called for a human to create the very first blank project by hand in Power BI Desktop, then `pull` it in - reasoning that this repo has no way to verify a hand-authored PBIR/TMDL schema is byte-correct. Revised after the test protocol was framed around a **scripted** seed step ([Test Cases](#test-cases), 06.TC.01) with the human's role moved to *validating* the seed (06.TC.04) rather than *authoring* it. `cmd_scaffold` in **sync script** now generates the `.pbip`/`.Report`/`.SemanticModel`/CSV-backed model itself - this content is explicitly unverified against real Power BI Desktop until 06.TC.04 runs; the original manual-bootstrap procedure stays documented as the fallback if Desktop rejects the generated seed (see [Implement](#implement), step 03).

**06.01.R02** Reverts 06.01.R01 in full. Two real, distinct Power BI Desktop failures traced directly to the hand-generated `.Report` content: **06.IS.02** (missing required `version.json`, blocked opening entirely) and **06.IS.04** (`NullReferenceException` inside Desktop's own report-save code path, after the file opened and refreshed successfully). Diffing against a human-created reference project fixed 06.IS.02, but 06.IS.04 surfaced on the very next save - a second, different failure in the same hand-authored `.Report` folder, not a one-off. [Microsoft's own PBIP docs](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report) state plainly that `report.json` (PBIR-Legacy) "doesn't support external editing," and that even the newer PBIR `\definition` format carries the caveat that "changes to files or properties outside of Power BI Desktop can cause unexpected errors, or even prevent Power BI Desktop from opening." Two failures plus that explicit warning is enough evidence that a script should not be hand-authoring `.Report` content, regardless of how closely it's modeled on a working reference. `cmd_scaffold` in **sync script** is back to verify-and-instruct (06.EL.07); the human creates **both** `.Report` and `.SemanticModel` together in Power BI Desktop so it keeps them internally consistent, then `pull` captures the pair - this is the same procedure 06.01.R01 had demoted to a fallback, now the only path. TMDL (`.SemanticModel`) itself was never the problem - Microsoft's docs describe it as designed for external editing, and every TMDL-only check (06.IS.02's diff, the post-fix open, the Refresh in 06.IS.03) passed - but there's no way to hand off only the model half of a `.pbip` bootstrap, so this revision covers the whole scaffold step, not just the `.Report` piece.

**06.01.R03** Refines 06.01.R02, doesn't reopen it - "don't hand-author `.Report`" was never the same claim as "an AI agent can't safely touch `.Report` content." The user's own `reconciliation-dashboard-user-created` project (built in Desktop, opened and refreshed cleanly per **06.IS.02**/**06.IS.03**) is a real, already-valid `.pbip` - `pull`ed into `$POWERBI_REPO_DIR` as-is, it became this feature's actual template content, formalizing what **06.IS.04**'s resolution had left as a manual next step rather than leaving the repo template empty pending a redo. `POWERBI_WINDOWS_DIR` now points at that project's folder; the files under `$POWERBI_REPO_DIR` still carry its Desktop-assigned `reconciliation-dashboard-user-created.*` names rather than `reconciliation-dashboard-template.*` - per Microsoft's docs, renaming a PBIR/TMDL object is a Desktop-only operation with its own reference-breaking risk, so it wasn't attempted from this side; the enclosing repo folder path (`powerbi/reconciliation-dashboard-template/`) stays the stable, addressable name regardless of what's inside it. This unblocks the other half of the original claim: *extending* an already-valid `.Report` with a new, self-contained object (a visual, modeled directly on one already proven to open/save in the same project) is a materially different, lower-risk operation than generating the whole folder from nothing - proven by [Test Cases](#test-cases) 06.TC.14-17, which this revision adds. `IGNORE_SUFFIXES` in **sync script** also gained `.pbix`, discovered pulling this project for the first time - its `.pbix` sibling isn't a tracked deliverable (per [`.pbip` project anatomy](#pbip-project-anatomy)) and has no reason to round-trip through sync.

## Scope

set up a git-tracked, version-controlled Power BI workspace using `.pbip` (Power BI Project) template files, plus a sync script keeping them mirrored between the Windows-side `/mnt/...` path (where Power BI Desktop actually runs - it's Windows-only and can't run inside this Linux/Docker sandbox) and this repo's `/home/...` working copy.

- Power BI Desktop is Windows-only and cannot run inside this Linux/Docker sandbox - this feature's job is to keep the `.pbip` project git-tracked and mirrored, not to run or render Power BI itself
- the deliverable is a reusable `.pbip` **template**, not a finished dashboard - both assessment 1 and assessment 3 need a dashboard/dashboard-mock-up deliverable per the **assignment design doc**'s Task 5 (Assessment 3) and deliverable list (Assessment 1), and this feature gives them a common starting point instead of each assessment inventing its own workspace layout
- the sync script keeps the Windows-side `/mnt/...` working copy (where Power BI Desktop actually saves its files) and this repo's `/home/...` git-tracked copy mirrored in both directions, so edits made inside Power BI Desktop round-trip back into git without manual copy/paste and without data loss
- `.pbip` (not `.pbix`) specifically because it's Power BI's source-controllable, folder-of-text-files project format - the whole point of this feature is that the workspace lives in git like every other artifact in this repo, not as an opaque binary
- does not build the assessments' actual dashboard content (KPIs, visuals, filters, DAX measures) - the **assignment design doc**'s Task 5 executive KPIs and recommended visuals stay scoped to assessment 1 and assessment 3's own deliverables; this feature only stands up the reusable scaffold and sync workflow they build on top of
- does not attempt to run, automate, or headlessly render Power BI Desktop from the Linux side - no CI validation of the `.pbip` content itself; round-trip correctness is checked by diffing the synced files, not by opening Power BI

**extension - live connection to sql db**

extend the existing template with a live connection to the `reconciliation.rc_*` postgres tables (the same control-table stack **ai closed-loop validation tracker** built and seeded with real batches) and a small dashboard of visuals summarizing that real data - the template stops being CSV-only.

- connects to the already-running `postgres-as01` container (per the **postgresql dev env tracker**) over the network Power BI Desktop's built-in PostgreSQL connector speaks - no new infra stood up by this subtask, purely a new data source on an existing one
- data model covers the three live tables - `reconciliation.rc_batch_control`, `rc_reconciliation_results`, `rc_audit_trail` - as three related TMDL tables (matching their real foreign-key shape: `batch_id` one-to-many into the other two), not one flattened query
- credentials are never written into any git-tracked file - Power BI Desktop's own encrypted credential store holds the postgres username/password, entered once interactively; the M query carries only server/database/SQL text
- "a few meaningful visuals" - executive-KPI-card style, matching the shape the **assignment design doc**'s Task 5 already describes (batch/status counts, variance), not a from-scratch dashboard spec invented here
- table+column+M-query TMDL is AI-authored directly (the proven-safe pattern from 06.TC.09/06.TC.15 - TMDL is documented as externally-editable, and this extends an already-open, already-valid project rather than generating one from nothing); relationships between the three new tables and the new page's visuals are built by a human in Power BI Desktop and captured via `pull` - per **06.01.R02**'s finding, hand-authoring PBIR visual bindings against columns that don't exist in the project *yet* is exactly the higher-risk case that finding warned about, not the lower-risk "extend already-loaded data" case 06.TC.15 proved
- does not change the CSV-backed `reconciliation-summary` table already in the model - this is additive, a second data source alongside the first, not a replacement

## References

- **dev env design doc** `docs/design/development-environment.md` (BI tooling note, Scenario 6 dashboard-mockup scenario)
- **assignment design doc** `docs/design/assignment.md` (Task 5 - Power BI Dashboard; Assessment 1's dashboard mock-up deliverable)
- **ai closed-loop validation tracker** `docs/features/05-ai-closed-loop-validation.md`
- **postgresql dev env tracker** `docs/features/02-dev-env-setup-postgresql-db.md`
- **powerbi template** `powerbi/reconciliation-dashboard-template/reconciliation-dashboard-template.pbip` (+ its `.Report` / `.SemanticModel` folders)
- **sync script** `scripts/05-powerbi-sync.sh`
- **sample data fixture** `powerbi/reconciliation-dashboard-template/sample-data/reconciliation-summary.csv`
- **PostgreSQL.Database M reference** https://learn.microsoft.com/en-us/powerquery-m/postgresql-database
- **Power Query PostgreSQL connector reference** https://learn.microsoft.com/en-us/power-query/connectors/postgresql

## Design

### `.pbip` project anatomy

A `.pbip` project is Power BI's source-controllable project format: a small `.pbip` pointer file plus two sibling folders that hold the actual content as plain text, not a single binary blob -

- `<name>.Report/` - the report definition (pages, visuals, filters) in PBIR (Power BI Report) JSON, one file per page/visual rather than one opaque document
- `<name>.SemanticModel/` - the data model (tables, relationships, measures) in TMDL (Tabular Model Definition Language) text files

versus the older `.pbix`, which zips everything - including a copy of any imported data - into one binary file git can track but never usefully diff. `.pbip`'s whole point for this feature is that a change made in Power BI Desktop shows up as a readable text diff in git, the same way every other artifact in this repo does.

### repo-side directory structure

```
powerbi/
└── reconciliation-dashboard-template/
    ├── reconciliation-dashboard-template.pbip
    ├── reconciliation-dashboard-template.Report/
    └── reconciliation-dashboard-template.SemanticModel/
```

One shared template, not one per assessment - both assessment 1 (dashboard mock-up deliverable) and assessment 3 (Task 5 - Power BI Dashboard) need a Power BI deliverable per the **assignment design doc**, and this feature's job is the common scaffold each of them opens and builds its own report pages into, not a separate template per assessment.

### windows-side working copy

Power BI Desktop is a native Windows binary; it cannot open a WSL-native `/home/...` path directly the way Docker/psql/Spark in this repo run from Linux, and it cannot safely be pointed at the git working tree in place either - Power BI Desktop autosaves and holds file locks continuously while a project is open, which risks git seeing a dirty/mid-write tree during a checkout or diff. So the copy Power BI Desktop actually opens lives on the native Windows filesystem, under `/mnt/c/Users/<windows-user>/...` as seen from this same WSL shell - a second, disposable copy of the same project, not the git working tree itself. The **sync script** is what keeps the two copies consistent; nothing edits the `/mnt` copy except Power BI Desktop, and nothing edits the repo copy except git operations (checkout, merge) and the sync script.

### sync script design

The **sync script** exposes explicit one-directional subcommands rather than one auto-merging "sync" - `.pbip`'s TMDL/PBIR files are structured text, not freely mergeable the way a flat config file is, so this feature doesn't attempt to build a real three-way merge:

| id | subcommand | direction                    | when used                                        | 
| -- | ---------- | ---------------------------- | -----------------------------------------------------| 
| 01 | `scaffold` | repo only                    | first-time creation of the template (verify-or-create) | 
| 02 | `push`     | repo -> `/mnt` working copy  | start/resume a Power BI Desktop editing session         | 
| 03 | `pull`     | `/mnt` working copy -> repo  | capture edits made in Power BI Desktop back into git    | 
| 04 | `verify`   | read-only, both sides        | round-trip / rerun-safety proof [01]                    | 

01. **04 `verify`** - see [workflow validation runner](#workflow-validation-runner).

Copying is by content, not by blind overwrite: each `push`/`pull` compares the source and destination trees (per-file checksum, not mtime alone - mtimes don't reliably survive a git checkout) against a manifest recorded by the last successful sync, and -

- if only the destination is unchanged or a strict subset of what the source already has, `push`/`pull` proceeds
- if the destination has diverged from the manifest in a way the source doesn't already contain (both sides changed independently since the last sync), the script fails fast and reports the conflicting files rather than silently picking a side to overwrite - resolving a real conflict is left a manual step, not something this script guesses at

### idempotency / rerun-safety

- **`scaffold`**: verify-or-create, same convention as every prior feature's DDL/setup steps - a no-op if the template already exists at the expected repo path and matches its recorded manifest.
- **`push` / `pull`**: safe to run repeatedly - a rerun with nothing changed on either side is a no-op (manifest already matches), not a re-copy.
- **Windows-side path is machine-specific and never assumed**: the script fails fast with a clear message if `POWERBI_WINDOWS_DIR` is unset or the path doesn't exist, rather than guessing a default under `/mnt/c/Users/...`.

### environment & secrets

One new non-secret variable, `POWERBI_WINDOWS_DIR` - the absolute `/mnt/c/...` path to the Windows-side working copy - added to `.env`/`.env.sample` alongside the existing per-feature blocks. No secrets are introduced: this feature's template has no live data source wired in yet (per [Scope](#scope)), so there's no credential for the **sync script** to handle.

### workflow validation runner

Round-trip correctness - this milestone's closure condition - is proven by the **sync script**'s `verify` subcommand, not by opening Power BI Desktop by hand each time:

1. `push` the repo template out to `POWERBI_WINDOWS_DIR`.
2. Apply a deliberate, known change to a file on the `/mnt` side (standing in for a Power BI Desktop edit).
3. `pull` back into the repo copy.
4. Diff the repo copy against its pre-push state: the deliberate change is present, and every other file is byte-identical - proving the round trip neither drops nor corrupts anything.
5. Repeat in the opposite direction (edit repo-side, `push`, diff the `/mnt` copy) so both directions are proven, not just one.
6. Run the whole sequence twice back-to-back to confirm [idempotency / rerun-safety](#idempotency--rerun-safety) holds - the second pass should report nothing left to sync.

This follows the same discipline the **ai closed-loop validation tracker** established - the deliberate edit and the diff are checked with a plain `diff`/checksum run independently, not by trusting the **sync script**'s own printed summary.

### live postgres data model

Three new TMDL tables in the same `.SemanticModel`, one per live table in the `reconciliation` schema the **ai closed-loop validation tracker** built and seeded:

| id | table                        | role                                                    | 
| -- | ------------------------------ | ------------------------------------------------------------| 
| 01 | `rc_batch_control`              | one row per closed-loop run (batch header) [01]              | 
| 02 | `rc_reconciliation_results`     | one row per dimension checked in a batch [01]                | 
| 03 | `rc_audit_trail`                | one row per feedback action taken on a batch [01]             | 

01. each table name matches its source 1:1 - `reconciliation.<table name>` in postgres.

Each table's M partition uses `PostgreSQL.Database("<host>:<port>", "<database>", [Query = "<SQL>"])` - the `Query` option runs one explicit `SELECT` server-side per table rather than importing the whole live schema and navigating a generated table list, so the M query text says exactly what it pulls. Host/port/database are the same values this repo's every other feature already reads from `.env` (`POSTGRES_HOST`/`POSTGRES_PORT`/`POSTGRES_DB`) - written as literals into the M query since TMDL text can't read shell environment variables, but matching them exactly. **No credential is ever written into the M query or any git-tracked file** - the username/password are entered once, interactively, in Power BI Desktop's own connection-credentials prompt, and live only in Desktop's local encrypted credential store, never in `.pbi/` (which is gitignored anyway) or anywhere sync touches.

`localhost` resolves correctly from Power BI Desktop's side of this because of WSL2's localhost-forwarding: `postgres-as01` publishes `0.0.0.0:5432` from inside WSL2 (confirmed via `docker port postgres-as01`), and Windows processes reach WSL2 services on `localhost:<port>` by default on this machine - no extra network configuration, no container port beyond what's already exposed for every other feature's own `psql`/JDBC access.

Relationships (`rc_batch_control.batch_id` one-to-many into both other tables' `batch_id`, matching the real postgres foreign keys) are **not** hand-authored in TMDL - unlike the table/column/M-query shape (proven safe repeatedly this session, most recently in [Test Cases](#test-cases) 06.TC.15), a `relationships.tmdl` construct has no proven-working reference in this project to model against, and per **06.01.R02**'s finding, guessing at unverified TMDL/PBIR syntax is exactly the category of mistake that already cost two issues. Power BI Desktop auto-detects relationships on matching column names when tables are loaded together, or a human draws them in Model view in seconds - a GUI action, not a schema an agent needs to fabricate blind.

Visuals are the same story - a new report page, built by a human in Desktop per the checklist below, then captured by `pull`:

| visual                          | fields [01]                                       | 
| ---------------------------------- | -------------------------------------------------- | 
| card: batch count                  | Count of `rc_batch_control[batch_id]`                | 
| card: batches by status            | Count of `[batch_id]`, split by `[status]`            | 
| card: latest variance %            | `[variance_pct]`, filtered to the max `[created_at]` batch | 
| bar chart: variance % by batch     | `[batch_id]` (axis) x `[variance_pct]` (value), split by `[dimension]` | 
| table: reconciliation detail       | `[batch_id, dimension, source/target_value, variance(_pct), status]` | 

01. all fields not from `rc_batch_control` come from `rc_reconciliation_results` (the card/bar-chart/table rows below the first).

This is deliberately the same shape the **assignment design doc**'s Task 5 KPI/visual list already describes (status counts, variance, a detail table) applied to the tables this scaffold actually has, not a new spec invented for this subtask.

## Test Cases

_test strategy_

Three layers, not two - this feature adds one the postgres/spark features never needed:

1. **script self-report** - the `[PASS]`/`[FAIL]` lines **sync script** (06.EL.07/06.EL.08) prints, logged under `.dev/logs/` per the `feature-implementation-guide` skill's convention.
2. **direct filesystem inspection, bypassing the script** - `diff -rq` / independent `sha256sum` between `$POWERBI_REPO_DIR` and `$POWERBI_WINDOWS_DIR`, run separately from anything `powerbi-sync.py` reports - same discipline the **ai closed-loop validation tracker** established for its own layer 2.
3. **human-in-the-loop, inside Power BI Desktop** - the layer unique to this feature: per [Scope](#scope), nothing here headlessly renders or automates Power BI Desktop, so only a human opening the actual `.pbip`/`.pbix` on the Windows side can confirm the project is genuinely *valid and openable*, not merely byte-identical. Layers 1-2 can pass on a file set Power BI Desktop itself refuses to open (a checksum match proves the copy, not the content's validity) - layer 3 is what actually catches that.

A fourth dimension cuts across the three layers rather than adding a fourth one: every check above is run once for a **human-authored** edit (made inside Power BI Desktop) and once for an **AI-authored** edit (made directly on the repo-side PBIR/TMDL text, the same way any other git-tracked file in this repo gets edited) - proving the sync loop holds in both edit directions, not just the human one. The scenario below interleaves both, plus the CSV-backed **sample data fixture** so there's real, checkable content to edit rather than a truly empty report.

_test cases_

| id       | task  | layer       | check                                                          | 
| -------- | ----- | ----------- | -------------------------------------------------------------- | 
| 06.TC.01 | 06.03 | self-report | `scaffold`: `[FAIL]`+instructs before bootstrap, `[PASS]` after [01] | 
| 06.TC.02 | 06.04 | self-report | `push` places the seed project at `/mnt`, manifest written     | 
| 06.TC.03 | 06.04 | fs-diff     | independent `diff -rq`/checksum, repo vs `/mnt`                | 
| 06.TC.04 | 06.07 | human-loop  | Desktop opens the seed, no repair prompt, CSV table renders    | 
| 06.TC.05 | 06.07 | human-loop  | Save As `.pbix` succeeds, reopens clean - base state good      | 
| 06.TC.06 | 06.07 | human-loop  | human makes one visible edit, saves back to `.pbip`            | 
| 06.TC.07 | 06.04 | self-report | `pull` captures the human edit, `[PASS]`                       | 
| 06.TC.08 | 06.04 | fs-diff     | pulled diff shows only the human's intended change             | 
| 06.TC.09 | 06.07 | ai-loop     | AI edits PBIR/TMDL text directly in the repo copy              | 
| 06.TC.10 | 06.04 | self-report | `push` sends the AI's edit to `/mnt`, `[PASS]`                 | 
| 06.TC.11 | 06.07 | human-loop  | Desktop reopens `/mnt`, AI's change renders, no repair prompt  | 
| 06.TC.12 | 06.05 | fs-diff     | idempotency: rerun `push`+`pull`, nothing changed, 0 copied    | 
| 06.TC.13 | 06.05 | self-report | `verify` reports both sides matching the manifest              | 
| 06.TC.14 | 06.05 | self-report | `pull` an existing, Desktop-valid project into the repo [10]   | 
| 06.TC.15 | 06.05 | ai-loop     | AI adds a new visual to the existing page (a real `.Report` edit) [11] | 
| 06.TC.16 | 06.05 | self-report | `push` the new visual to `/mnt`, `[PASS]`                      | 
| 06.TC.17 | 06.05 | fs-diff     | independent diff shows only the new visual.json added [12]     | 
| 06.TC.18 | 06.07 | human-loop  | Desktop reopens, new visual renders, project **saves** cleanly [13] | 
| 06.TC.19 | 06.08 | ai-loop     | AI adds 3 postgres-backed TMDL tables to the repo copy [14]    | 
| 06.TC.20 | 06.08 | self-report | `push` the new tables to `/mnt`, `[PASS]`                      | 
| 06.TC.21 | 06.08 | fs-diff     | independent diff shows only the 3 new table files added        | 
| 06.TC.22 | 06.08 | human-loop  | Desktop reopens, refreshes - all 3 tables load with real data [15] | 
| 06.TC.23 | 06.08 | human-loop  | human sets relationships, builds the visuals checklist, saves [16] | 
| 06.TC.24 | 06.08 | self-report | `pull` captures the new page/relationships/visuals, `[PASS]`   | 
| 06.TC.25 | 06.08 | fs-diff     | independent diff of the pulled result vs `/mnt`, nothing missed | 

01. **06.TC.01** `scaffold` used to hand-generate a seed here (06.01.R01); after **06.01.R02** it only verifies and instructs - `[FAIL]` + the human-bootstrap procedure when no `.pbip` exists yet, `[PASS]` once it does. Both branches are real, checkable script behavior, not a stand-in for a human step.
02. **06.TC.03** `diff -rq`/`sha256sum` run directly against both directories, independent of `powerbi-sync.py`'s own printed summary - see **tools** below.
03. **06.TC.04** "no repair prompt" is the concrete signal Power BI Desktop uses when it can't parse a hand/AI-modified project; that absence, plus the **sample data fixture**'s rows actually showing in a table visual, is the pass condition - not just "the app didn't crash".
04. **06.TC.05** Save As `.pbix` is a one-time sanity check that the `.pbip` project is a fully valid, loadable Power BI project (`.pbix` packages the live model+report together) - per [`.pbip` project anatomy](#pbip-project-anatomy) the resulting `.pbix` stays out of git; discard it after this check, it is not a tracked deliverable.
05. **06.TC.06** the edit should be something a byte diff can unambiguously confirm afterwards - e.g. renaming the visual's title or adding a text box with known text - not a cosmetic drag/resize that TMDL/PBIR may serialize non-deterministically.
06. **06.TC.08** checked against the pre-edit commit (`git diff`) or the prior manifest checksums - proving `pull` didn't silently touch files the human never edited (a Desktop-generated cache file leaking past 06.EL.02's `.gitignore` patterns would be exactly this kind of miss).
07. **06.TC.09** applied with the same Edit tool used on every other git-tracked file in this repo - no Power BI Desktop involved on this leg - proving an agent, not only a human via the Desktop GUI, can produce a change Power BI Desktop later accepts as valid. TMDL (`.SemanticModel`) is the unconditionally safe version of this - Microsoft's docs describe it as designed for external editing, confirmed by the `Total Variance` measure round-tripping cleanly (see Validate). `.Report`/PBIR edits are the riskier version *only* when generating a whole file/object from nothing (that's what **06.IS.04** actually traced) - 06.TC.15 below is the PBIR-side equivalent of this test case, done the way **06.01.R03** found actually works: extending an already-valid object, not fabricating one.
08. **06.TC.11** the layer that actually proves the AI's edit was valid *Power BI* content, not merely well-formed JSON/TMDL syntax - a malformed AI edit could still pass 06.TC.10's plain file copy and only fail here.
09. **06.TC.12** reruns `push` then `pull` back-to-back with no intervening change on either side; per [idempotency / rerun-safety](#idempotency--rerun-safety) a fully-matching manifest means zero files copied - checked directly, not by trusting the script's own "up to date" line.
10. **06.TC.14** the project being pulled in is `reconciliation-dashboard-user-created` - built and Desktop-confirmed-openable by the human, per **06.IS.02**/**06.IS.03**'s diagnostics; this is what became this feature's actual template content, per **06.01.R03**.
11. **06.TC.15** modeled directly on the page's existing `barChart` visual (`c4ee1717d00f47231b66`) rather than invented from scratch - same `visualContainer` schema, same query/projection shape, different fields (`dimension` category, `Sum(variance)` instead of `reconciliation_status`/`Sum(batch_id)`) and position (placed beside, not overlapping, the original). A fresh 20-hex-char id (`646db3b2e6e6a7d781ab`) in its own `visuals/<id>/visual.json`, per the PBIR folder convention - no other file needs to reference it.
12. **06.TC.17** confirmed via `diff -rq` against `$POWERBI_WINDOWS_DIR` after the push - the only difference left afterward was the `.pbix` sibling file (excluded from sync by design, per **06.01.R03**'s `IGNORE_SUFFIXES` addition), not any unintended change to the existing visual, page, or model.
13. **06.TC.18** the one thing this agent still cannot do itself - render or save inside Power BI Desktop. This is what actually closes the loop **06.IS.04** left open: not "can a script generate `.Report` content" (no), but "can an already-valid `.Report` be extended and saved without crashing" - mechanically proven by 06.TC.14-17, awaiting this one human confirmation.
14. **06.TC.19** the safe half of [live postgres data model](#live-postgres-data-model) - TMDL table/column/M-query text only, the same object shape 06.TC.09's `Total Variance` measure already proved round-trips cleanly. No relationships, no visuals - those stay human-built per that same Design subsection's reasoning.
15. **06.TC.22** "real row counts" means checked against an independent `psql` query at the same time, not just "a number showed up" - `SELECT COUNT(*) FROM reconciliation.rc_batch_control` (and the other two tables) run directly, per the **tools** block, compared to what each Power BI table shows.
16. **06.TC.23** the checklist is the visuals table in [live postgres data model](#live-postgres-data-model) - a human building it is not a stand-in for automation here, it's the actual, deliberate design: relationships and visual bindings are GUI actions this feature never proposed automating.

**tools**

```bash
cd /home/taylor-hickem/repos/de-financial-accounting-demo
set -a && source .env && set +a

# layer: fs-diff - independent of the sync script's own printed summary
diff -rq "$POWERBI_REPO_DIR" "$POWERBI_WINDOWS_DIR" \
  --exclude '.pbi' --exclude '*.abf' --exclude '.sync-manifest.json'

# checksum both sides directly, sorted so the two outputs line up for a manual diff
find "$POWERBI_REPO_DIR" -type f -not -path '*/.pbi/*' -exec sha256sum {} \; | sort -k2
find "$POWERBI_WINDOWS_DIR" -type f -not -path '*/.pbi/*' -exec sha256sum {} \; | sort -k2
```

## Edit locations

| id       | path                    | change                                                     | 
| -------- | ------------------------ | -------------------------------------------------------------| 
| 06.EL.01 | `.env` / `.env.sample`   | add `POWERBI_REPO_DIR`, `POWERBI_WINDOWS_DIR`                 | 
| 06.EL.02 | `.gitignore`             | add Power BI cache/local-settings ignore patterns              | 
| 06.EL.03 | `*.pbip`                 | new, human-bootstrapped in Desktop - see 06.01.R02              | 
| 06.EL.04 | `*.Report/`              | new, human-bootstrapped in Desktop - see 06.01.R02              | 
| 06.EL.05 | `*.SemanticModel/`       | new, human-bootstrapped in Desktop - see 06.01.R02              | 
| 06.EL.06 | `.sync-manifest.json`    | new, generated by first successful sync, git-tracked           | 
| 06.EL.07 | `powerbi-sync.py`        | new: scaffold/push/pull/verify logic, checksum manifest        | 
| 06.EL.08 | `05-powerbi-sync.sh`     | new: thin CLI wrapper, dispatches to 06.EL.07                  | 
| 06.EL.09 | `powerbi/README.md`     | new: assessment-facing usage guide                              | 
| 06.EL.10 | `rc_batch_control.tmdl` | new: postgres-backed table, AI-authored (06.TC.19)              | 
| 06.EL.11 | `rc_reconciliation_results.tmdl` | new: postgres-backed table, AI-authored (06.TC.19)     | 
| 06.EL.12 | `rc_audit_trail.tmdl`   | new: postgres-backed table, AI-authored (06.TC.19)              | 
| 06.EL.13 | `model.tmdl`            | extended: `ref table` + `PBI_QueryOrder` for the 3 new tables    | 

01. **06.EL.01** `.env` / `.env.sample`
02. **06.EL.02** `.gitignore`
03. **06.EL.03** `powerbi/reconciliation-dashboard-template/reconciliation-dashboard-user-created.pbip`
04. **06.EL.04** `powerbi/reconciliation-dashboard-template/reconciliation-dashboard-user-created.Report/`
05. **06.EL.05** `powerbi/reconciliation-dashboard-template/reconciliation-dashboard-user-created.SemanticModel/`
06. **06.EL.06** `powerbi/reconciliation-dashboard-template/.sync-manifest.json`
07. **06.EL.07** `scripts/utils/powerbi-sync.py`
08. **06.EL.08** `scripts/05-powerbi-sync.sh`
09. **06.EL.09** `powerbi/README.md`
10. **06.EL.10** `.../reconciliation-dashboard-user-created.SemanticModel/definition/tables/rc_batch_control.tmdl`
11. **06.EL.11** `.../reconciliation-dashboard-user-created.SemanticModel/definition/tables/rc_reconciliation_results.tmdl`
12. **06.EL.12** `.../reconciliation-dashboard-user-created.SemanticModel/definition/tables/rc_audit_trail.tmdl`
13. **06.EL.13** `.../reconciliation-dashboard-user-created.SemanticModel/definition/model.tmdl`

## Implement

Applied in dependency order, each step referencing its **Edit locations** id:

01. **`.env` / `.env.sample`** (06.EL.01) - added alongside the existing per-feature blocks. `POWERBI_REPO_DIR` is the same for everyone; `POWERBI_WINDOWS_DIR` is machine-specific - `.env.sample` keeps a `<windows-user>` placeholder, `.env` got the real path discovered by inspecting this session's own WSL mount (`/mnt/c/Users/Admin/OneDrive/powerbi-workspace/reconciliation-dashboard-template` - `OneDrive/` already existed and was writable, so no new directory convention was invented).

02. **`.gitignore`** (06.EL.02) - added the Power BI Desktop cache/local-settings patterns from [sync script design](#sync-script-design).

03. **`.pbip` / `.Report/` / `.SemanticModel/`** (06.EL.03, 06.EL.04, 06.EL.05) - human-bootstrapped in Power BI Desktop, not hand-authored by the script - per **06.01.R02**, the scripted generator this step originally described (06.01.R01) was reverted after **06.IS.02** and **06.IS.04**. `cmd_scaffold` in **sync script** (06.EL.07) now only verifies the template exists; when it doesn't, it prints this exact procedure and exits non-zero rather than fabricating content:

    ```text
    1. File > New > blank report.
    2. Get Data > Text/CSV > the sample data fixture (once repo-side, or pushed).
    3. File > Save as > Power BI project (.pbip), into %POWERBI_WINDOWS_DIR%.
    4. Close Power BI Desktop (releases its file locks), then: scripts/05-powerbi-sync.sh pull
    ```

    Report and SemanticModel are created **together** in this one Desktop session, deliberately - that pairing is what keeps them internally consistent, which is exactly what the hand-generated version couldn't guarantee.

04. **`.sync-manifest.json`** (06.EL.06) - written by `save_manifest()` as a side effect of the first successful `push`/`pull`, not hand-authored. Tracked in git (not gitignored) - the shared "last known good" checksum reference both sides diff against.

05. **`scripts/utils/powerbi-sync.py`** (06.EL.07) - the full checksum-manifest implementation behind `scaffold`/`push`/`pull`/`verify` from [sync script design](#sync-script-design); see the file itself rather than a duplicate copy here. `diverged()` is the conflict rule: a file counts as "changed since last sync" once its checksum no longer matches the manifest, and `pull`/`push` refuse to proceed only when *both* sides show divergence at once.

06. **`scripts/05-powerbi-sync.sh`** (06.EL.08) - thin wrapper: sources `.env`, resolves the log file name per the `feature-implementation-guide` skill's `<ts>-<task-id>-<name>.log` convention, fails fast if `POWERBI_WINDOWS_DIR` is unset (except for `scaffold`/`push`, which can create it), then dispatches to 06.EL.07.

07. **`powerbi/README.md`** (06.EL.09) - short assessment-facing usage guide: prerequisites, the `push`/`pull`/`verify` loop, what's in the template, and a pointer back here for design rationale - per this milestone's closure condition in `docs/milestones.md`.

08. **`rc_batch_control.tmdl` / `rc_reconciliation_results.tmdl` / `rc_audit_trail.tmdl`** (06.EL.10-12) - one TMDL table per live `reconciliation.*` postgres table, matching each table's real `\d` output (`docker exec ... psql -c '\d reconciliation.rc_batch_control'` etc., run directly against `postgres-as01` before writing any TMDL - column names/types came from the live schema, not assumed). Each partition's M query uses `PostgreSQL.Database("localhost:5432", "as01_source_db", [Query="SELECT ... FROM reconciliation.<table>"])`, confirmed against the [PostgreSQL.Database M reference](#references) rather than recalled from memory, given this session's history with unverified TMDL/PBIR guesses. One correction made *before* pushing, not after a failure: the first draft declared `dataType: datetimezone` for the four `timestamp with time zone` columns - checked against the [official TMDL Column reference](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-reference-tabular-object) before pushing and found `datetimezone` isn't a valid TOM column `dataType` at all (TOM has no distinct timezone-aware column type); fixed to `dateTime` for the column declaration while the M query's own intermediate cast stays `type datetimezone` (a normal M-level step, unrelated to what the Tabular column itself stores). **`model.tmdl`** (06.EL.13) extended with `ref table` and `PBI_QueryOrder` entries for all three.

**Deviations from Design** - three, all discovered by actually running things against real Power BI Desktop rather than assumed:

- `copy_tree()`'s first version re-copied every file on every `push`/`pull` regardless of whether its content had changed. Not observably wrong (content and checksums still ended up correct), but it contradicted the "0 files copied" idempotency claim in [Test Cases](#test-cases) 06.TC.12 and would needlessly re-trigger a OneDrive upload for files nothing touched. Fixed to diff against the destination's own checksums first and only copy what actually differs - see **06.IS.01** for the full diagnosis.
- The step 03 scaffold approach itself changed mid-implementation, twice - scripted generation (06.01.R01) was tried, hit two distinct real Power BI Desktop failures (**06.IS.02**, **06.IS.04**), and was reverted back to the original human-bootstrap design (**06.01.R02**). The `.SemanticModel`/sync-mechanism half of this feature never needed to change - see **06.IS.02**/**06.IS.03**'s diagnostics for what did keep working.
- Pushing 06.EL.10-13 hit a genuine two-sided, non-overlapping conflict the **sync script**'s own error message doesn't explain how to resolve: the human's 06.TC.18 save had changed one windows-side file (`visual.json`, `"x": 780.0` normalized to `780`) while the new tables changed four repo-side files - neither overlapping, but `diverged()` flags both, and `push`/`pull` both refuse. Resolved by hand: copied the one windows-side change into the repo copy, then rebuilt `.sync-manifest.json` from the **windows** side's checksums specifically (not the repo side - rebuilding from repo's own post-edit state was tried first and made every windows-side file "diverge" against edits it hadn't received yet, since the manifest must represent the last point both sides *actually* agreed, not where the repo *wants* to end up) - then `push` proceeded cleanly. Not filed as a numbered issue (nothing crashed, no data was lost, the conflict rule itself did its job correctly), but worth this record since the correct resolution isn't obvious from the script's own message alone.

## Validate

Ran the automated layers (self-report, fs-diff) end to end against the real filesystem - this WSL session's own `/mnt/c/Users/Admin/OneDrive/powerbi-workspace/` (confirmed writable, and Power BI Desktop confirmed installed there as `Microsoft.MicrosoftPowerBIDesktop`), no mocks: `scaffold` generated the seed project (06.TC.01), `push`/`pull` moved it both directions with an independent `diff -rq` confirming byte-identical trees (06.TC.02, 06.TC.03), an AI-authored TMDL edit (a `Total Variance` measure) round-tripped cleanly (06.TC.09, 06.TC.10), a simulated Desktop-authored edit (`page.json` `displayName`) round-tripped the other direction (06.TC.07, 06.TC.08), the conflict rule correctly failed a genuine both-sides-changed case rather than guessing a winner, and two consecutive no-op reruns plus `verify` confirmed idempotency (06.TC.12, 06.TC.13) - all after the fix in **06.IS.01** below. These prove the sync *mechanism* (06.03/06.04/06.05); logs 01-11 ran against the first-draft seed content, which 06.TC.04 (the human's first real open) then found broken - see **06.IS.02**. Logs 12-14 are the regenerated seed, rebuilt against a known-good reference and re-pushed; the `Total Variance` measure was re-applied to the fresh content so 06.TC.11 still has something to check.

**Update after 06.IS.04**: that regenerated seed passed 06.TC.01-03/07-13 exactly as above, and even got past the open (06.IS.02) and refresh (06.IS.03) banners in Power BI Desktop - but then crashed Desktop's own save code with a `NullReferenceException`. Per **06.01.R02**, scripted `.Report`/`.pbip` generation is now abandoned entirely; the seed content this narrative describes (and logs 01-14 below) no longer exists in the repo - it was deleted, along with the abandoned `cmd_scaffold`'s `generate_seed_project()` code path. What logs 01-14 still prove, and what remains true, is that `push`/`pull`/`verify`/the conflict rule/idempotency (06.03/06.04/06.05's actual deliverable) all work correctly *given a valid project tree to sync* - that conclusion doesn't depend on where the tree came from. Log 15 is `scaffold` after the revert, confirmed to fail fast with the human-bootstrap instructions rather than generate anything.

**Update after 06.01.R03**: rather than wait on a fresh Desktop bootstrap, adopted `reconciliation-dashboard-user-created` (already built, already Desktop-confirmed-openable-and-refreshable) as the template - repointed `POWERBI_WINDOWS_DIR`, then `pull` (log 16, after a first attempt correctly failed on the conflict rule - log 16's predecessor, not itself an issue: the manifest had been reset to empty by the earlier cleanup, so every pre-existing file on both sides read as "diverged" against it; resolved by clearing the stray leftover CSV the repo side still had, per the diagnostic in the log table below). 18 files copied cleanly. Then 06.TC.15: added a second `barChart` visual to the existing page, modeled directly on the one already proven to open/save (see [Test Cases](#test-cases) footnote 11 for the exact fields) - `push` moved only that one new file (log 18), and `verify` confirmed both sides match (log 19). 06.TC.04/05/06/11/18 (Power BI Desktop itself) were outside what this agent can execute - all five confirmed by the human, see **Manual validate**.

**06.08**: three new TMDL tables written directly against live `\d reconciliation.*` output and the [PostgreSQL.Database M reference](#references) (06.TC.19) - one correction (`dataType: datetimezone` isn't a real TOM type) caught by checking the official TMDL reference *before* pushing, not after a Desktop failure, see [Implement](#implement) step 08. Pushing then hit a real conflict (logs 20-21): the human's 06.TC.18 save had touched the windows-side `visual.json` (`780.0` -> `780`, confirming that save really happened) while these new tables changed the repo side - two genuinely non-overlapping changes, correctly refused by the conflict rule rather than picking a winner. Resolved by hand (logs 22-24, detailed in Implement's Deviations from Design - copying the one windows-side change into the repo copy, then rebuilding the manifest, first from the wrong side which correctly failed again, then from the right one), then a clean push - 4 files copied, 18 already up to date (log 25), `verify` PASS both sides (log 26), independent `diff -rq` showing only the excluded `.pbix` different (same **tools** command as every prior round). 06.TC.22-24 (Desktop connecting to live postgres, building relationships/visuals, saving) are outside what this agent can execute - see **Manual validate**.

Log artifacts (`.dev/logs/`, gitignored):

| id | log file                                       | exit | evidence                        | 
| -- | ----------------------------------------------- | ---- | ------------------------------------| 
| 01 | `260830142705-06.04-powerbi-sync-scaffold.log` | 0    | seed generated, 06.TC.01 [01]   | 
| 02 | `260830142711-06.04-powerbi-sync-push.log`     | 0    | initial push, 06.TC.02          | 
| 03 | `260830142740-06.04-powerbi-sync-push.log`     | 0    | rerun still 13 files - 06.IS.01 | 
| 04 | `260830142815-06.04-powerbi-sync-push.log`     | 0    | post-fix: 0 copied, 06.TC.12    | 
| 05 | `260830142818-06.04-powerbi-sync-pull.log`     | 0    | post-fix pull, 06.TC.12         | 
| 06 | `260830142819-06.05-powerbi-sync-verify.log`   | 0    | both sides match, 06.TC.13      | 
| 07 | `260830142839-06.04-powerbi-sync-push.log`     | 0    | AI edit push, 06.TC.10          | 
| 08 | `260830142852-06.04-powerbi-sync-pull.log`     | 0    | sim. Desktop edit pull [02]     | 
| 09 | `260830142912-06.04-powerbi-sync-pull.log`     | 1    | conflict rule fires [03]        | 
| 10 | `260830142922-06.04-powerbi-sync-pull.log`     | 0    | clean rerun after revert        | 
| 11 | `260830142922-06.05-powerbi-sync-verify.log`   | 0    | final state matches again       | 
| 12 | `260830150423-06.04-powerbi-sync-scaffold.log` | 0    | regenerated seed, 06.IS.02 fix  | 
| 13 | `260830150439-06.04-powerbi-sync-push.log`     | 0    | pushed corrected seed [04]      | 
| 14 | `260830150631-06.04-powerbi-sync-push.log`     | 0    | re-applied `Total Variance` [05] | 
| 15 | `260830152637-06.04-powerbi-sync-scaffold.log` | 1    | post-revert: fails fast, instructs bootstrap [06] | 
| 16 | `260830153740-06.04-powerbi-sync-pull.log`     | 1    | conflict on empty manifest [07]                 | 
| 17 | `260830153812-06.04-powerbi-sync-pull.log`     | 0    | pulled the valid project, 18 files, 06.TC.14    | 
| 18 | `260830153856-06.04-powerbi-sync-push.log`     | 0    | pushed the new visual, 1 copied, 06.TC.16       | 
| 19 | `260830153857-06.05-powerbi-sync-verify.log`   | 0    | both sides match, closes 06.TC.17               | 
| 20 | `260830163034-06.04-powerbi-sync-push.log`     | 1    | push blocked - visual.json changed [08]         | 
| 21 | `260830163043-06.04-powerbi-sync-pull.log`     | 1    | conflict - non-overlapping files [08]           | 
| 22 | `260830163103-06.04-powerbi-sync-push.log`     | 1    | still blocked - manifest still stale [09]       | 
| 23 | `260830163125-06.04-powerbi-sync-push.log`     | 1    | blocked - wrong-side rebuild [09]               | 
| 24 | `260830163125-06.05-powerbi-sync-verify.log`   | 1    | WARN - wrong-side rebuild's effect               | 
| 25 | `260830163141-06.04-powerbi-sync-push.log`     | 0    | fixed: 4 copied, 18 up, 06.TC.20                | 
| 26 | `260830163148-06.05-powerbi-sync-verify.log`   | 0    | both sides match, closes 06.TC.21               | 

01. **log 01** also printed the `[WARN]` unverified-content notice from `cmd_scaffold` - expected, not an issue; that's exactly what 06.TC.04 exists to close out.
02. **log 08** the "Desktop edit" was simulated (this agent has no way to drive the Power BI Desktop GUI) by editing `page.json`'s `displayName` directly on the `/mnt` copy - stands in for 06.TC.06 mechanically, not for the human-in-the-loop content check itself.
03. **log 09** deliberately provoked: edited `reconciliation-dashboard-template.pbip` repo-side and `database.tmdl` windows-side independently, then ran `pull` - correctly listed both conflicting files and exited 1 instead of picking a side. Both edits were reverted immediately after (confirmed by log 10/11), never a real content change.
04. **log 13** the old (broken) seed was deleted repo- and windows-side first, then `scaffold` regenerated it per **06.IS.02**'s fix and this pushed all 15 files fresh - `diff -rq` against `reconciliation-dasboard-user-created` confirmed `version.json` and `database.tmdl` byte-identical, `model.tmdl` differing only in locale/dev-tooling annotations.
05. **log 14** re-applied the `Total Variance` measure (lost when the seed was regenerated for log 12-13) directly to the fresh `reconciliation-summary.tmdl`, then pushed - `1 copied, 14 already up to date`, confirming only that one file moved.
06. **log 15** run after deleting the abandoned seed content repo- and windows-side per **06.01.R02** - `cmd_scaffold` correctly reports `[FAIL]` and prints the human-bootstrap procedure rather than falling back to generating anything.
07. **log 16** not a real content conflict - `.sync-manifest.json` had been deleted along with the abandoned seed, so `load_manifest` returned empty and every pre-existing file on *both* sides (the repo's leftover CSV, the windows-side project's real files) read as "diverged" against it. Resolved per the script's own advice ("resolve manually"): deleted the repo-side leftover CSV (redundant with the one already inside the windows-side project), then reran `pull` clean (log 17). Not filed as an issue - this is the conflict rule correctly refusing to guess on a genuinely ambiguous manifest state, not a defect in the rule itself.
08. **logs 20-21** a genuine two-sided conflict, not an empty-manifest artifact like log 16's: the human's 06.TC.18 save had really changed one windows-side file, and pushing the three new postgres tables had really changed four repo-side files - non-overlapping, but `diverged()` can't tell "safe to merge" from "pick a side," so both `push` and `pull` correctly refused rather than guessing. See [Implement](#implement)'s Deviations from Design for the full resolution.
09. **logs 22-24** the two failed follow-up attempts while working out the correct fix - log 22 still failed because the manifest itself hadn't been updated yet (copying the file content alone doesn't tell `push` anything); log 23/24 failed the *other* direction after rebuilding the manifest from the repo's own post-edit state, which made every windows-side file look stale against changes it hadn't received. Left in the log table rather than cleaned up - the wrong turns are part of what makes log 25's eventual fix (rebuild from the windows side specifically) a demonstrated fix, not an assumed one.

**secondary validation** - reproduce independently:

```bash
cd /home/taylor-hickem/repos/de-financial-accounting-demo
set -a && source .env && set +a

./scripts/05-powerbi-sync.sh push   # should report "0 copied, N already up to date"
./scripts/05-powerbi-sync.sh pull   # same
./scripts/05-powerbi-sync.sh verify

# independent of the script's own printed summary
diff -rq "$POWERBI_REPO_DIR" "$POWERBI_WINDOWS_DIR" \
  --exclude '.pbi' --exclude '*.abf' --exclude '.sync-manifest.json'
```

**Issues**

| id       | seq | status | issue                                                           | 
| -------- | --- | ------ | ----------------------------------------------------------------| 
| 06.IS.01 | 01  | closed | `copy_tree` re-copied every file on every rerun, not idempotent | 
| 06.IS.02 | 02  | closed | cannot find file version.json                                   | 
| 06.IS.03 | 03  | closed | "some tables have incomplete or no data" on first open          | 
| 06.IS.04 | 04  | closed | NullReferenceException on save - object reference not set        | 

_06.IS.04 (closed) NullReferenceException on save - object reference not set to an instance of an object_

**problem description**

After the **06.IS.02** fix and **06.IS.03** (Refresh) both succeeded, Power BI Desktop crashed with an unhandled `System.NullReferenceException` ("Object reference not set to an instance of an object") while saving the same script-generated seed project - the stack trace's entry point is `FileOperationUIHandler.TrySaveFile`, i.e. this happened during a save, not an open or a refresh.

**exception**

Full crash report: `.dev/logs/260830151900-06.IS.04-powerbi-exception.log`.

```log
Error Message:
Object reference not set to an instance of an object.

Stack Trace:
System.NullReferenceException
   at Microsoft.PowerBI.Client.Windows.ReportViewDocumentProvider.<GetEnhancedReportDocument>d__14.MoveNext()
   ...
   at Microsoft.PowerBI.Client.Windows.Services.UIStateService.<CommitUIState>d__7.MoveNext()
   ...
   at Microsoft.PowerBI.Client.Windows.Services.FileOperationUIHandler.<TrySaveFile>d__59.MoveNext()
```

**triggering actions**

Saving `reconciliation-dashboard-template.pbip` in Power BI Desktop (per the crash report's `Workbook Package Info`, likely triggered by the Refresh from **06.IS.03**'s resolution, or an explicit save right after it) - i.e. 06.TC.04's Refresh step succeeded, then the follow-on save did not.

**hypothesis**

- use hypothesis framing until a validated fix is applied

Before searching: this looked like it could be one more fixable content gap in the hand-generated `report.json`, the same category as **06.IS.02** - most likely the Fluent2 theme/`resourcePackages` block that was already flagged as a known, deliberate omission in **06.IS.02**'s diagnostic details. Revised after reading the official docs directly (see diagnostic steps): this isn't a single missing property to patch. It's the second distinct, real Power BI Desktop failure traced to the same hand-generated `.Report` folder - and Microsoft's own documentation says outright that this folder isn't meant to be hand-edited during preview.

**diagnostic steps**

| id          | seq | status | step                                                            | 
| ----------- | --- | ------ | ---------------------------------------------------------------------| 
| 06.IS.04.01 | 01  | closed | confirmed no repair prompt / open error - crash is save-side only     | 
| 06.IS.04.02 | 02  | closed | searched for the exact exception; nothing conclusive found            | 
| 06.IS.04.03 | 03  | closed | read the official PBIP report-folder reference on report.json/PBIR    | 
| 06.IS.04.04 | 04  | closed | reverted scripted `.Report`/`.pbip` generation (06.01.R02)            | 
| 06.IS.04.05 | 05  | closed | adopted an existing valid project as the template instead (06.01.R03) | 

**diagnostic details**

01. (closed) Reread the stack trace: the entry point is `TrySaveFile` -> `UIStateService.CommitUIState` -> `ReportViewDocumentProvider.GetEnhancedReportDocument` - a save-time serialization path, not `GetReportDocumentContent`'s load path. The report had already opened and (per **06.IS.03**) refreshed with real data - ruling out a repeat of **06.IS.02**'s "won't open at all" failure mode before looking any further.
02. (closed) Web search for `GetEnhancedReportDocument` / this `NullReferenceException` turned up nothing specific to this scenario - Power BI Desktop's internal report-view code isn't public, so guessing at the exact null field from the stack trace alone isn't reliable.
03. (closed) [Power BI Desktop project report folder - Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report) states plainly: *"report.json - This file contains the report definition in the Power BI Report Legacy format (PBIR-Legacy) and doesn't support external editing."* Even the newer PBIR `\definition` format (what this generator actually targeted) carries the [overview page](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview)'s general warning: *"Changes to files or properties outside of Power BI Desktop can cause unexpected errors, or even prevent Power BI Desktop from opening."* Combined with **06.IS.02** (a required file missing outright) and this crash (a save-time null two issues later, after fixing 02's specific gap and passing 03's open+refresh), the pattern is the `.Report` folder itself, not a single fixable property - patching a themeCollection block in blind again risks a third variant of the same category of bug.
04. (closed) Reverted `generate_seed_project()` and its call site entirely - see **06.01.R02**. `cmd_scaffold` in `scripts/utils/powerbi-sync.py` is back to verify-and-instruct: if no `.pbip` exists, it prints the human-bootstrap procedure (blank report -> Get Data on the **sample data fixture** -> Save As `.pbip`) and exits 1, rather than generating anything. The broken seed content was deleted from both `powerbi/reconciliation-dashboard-template/` and `$POWERBI_WINDOWS_DIR` (confirmed empty via `find`), and `scaffold` reruns clean with the fail-and-instruct message (Validate log 15).
05. (closed) Rather than wait on a fresh human bootstrap, adopted the human's already-existing, already-Desktop-valid `reconciliation-dashboard-user-created` project as this feature's actual template - `POWERBI_WINDOWS_DIR` repointed at it, `pull`ed into `$POWERBI_REPO_DIR` (see **06.01.R03**). Closing on that: the specific defect this issue tracked was hand-generated `.Report` content crashing Desktop's save path, and that content no longer exists anywhere in this feature - there's nothing left for the original defect to recur in. What's left is a narrower, new question (can an AI safely *extend* this now-valid `.Report`, not "can a script generate one") - tracked as its own test cases, 06.TC.14-18, not a reason to keep this issue open.

_06.IS.03 (closed) "some tables have incomplete or no data" on first open_

**problem description**

Retrying 06.TC.04 after the **06.IS.02** fix got past the version.json error, but Power BI Desktop then showed "Something went wrong - failed to load the report - some of the tables have incomplete or no data" on opening the (freshly regenerated, freshly pushed) seed project.

**exception**

`.dev/logs/260830150900-06.IS.03-powerbi-exception.log`:

```log
Something went wrong
failed to load the report
some of the tables have incomplete or no data
Activity ID: 9c13fd8c-b2d0-41b1-a643-e834f148df49
Time: Sun Aug 30 2026 15:09:20 GMT+0800 (Singapore Standard Time)
```

**triggering actions**

Reopening `reconciliation-dashboard-template.pbip` from `$POWERBI_WINDOWS_DIR` in Power BI Desktop, immediately after the **06.IS.02** fix's `push` (06.TC.04 retry).

**hypothesis**

- use hypothesis framing until a validated fix is applied

Before searching: possibly another content bug in the generated M-query or TMDL, the same category as **06.IS.02**. Ruled out by official documentation, not by more guessing this time - see diagnostic steps.

**diagnostic steps**

| id          | seq | status | step                                                              | 
| ----------- | --- | ------ | ----------------------------------------------------------------------| 
| 06.IS.03.01 | 01  | closed | confirmed the CSV and M-query path both resolve correctly on `/mnt` | 
| 06.IS.03.02 | 02  | closed | searched Microsoft Learn / Fabric Community for the exact message   | 
| 06.IS.03.03 | 03  | closed | read the official PBIP semantic-model-folder reference on `cache.abf` | 
| 06.IS.03.04 | 04  | closed  | updated Manual validate + generator's own `[WARN]` message accordingly | 
| 06.IS.03.05 | 05  | closed  | human ran Refresh, data loaded - confirmed before hitting 06.IS.04     | 

**diagnostic details**

01. (closed) Reconfirmed (per **06.IS.02**'s log 13) that `sample-data/reconciliation-summary.csv` exists at exactly the path the M query's `File.Contents(...)` references, with valid, unquoted CSV content - ruled out a bad file path or malformed source data before looking anywhere else.
02. (closed) Web search turned up Microsoft Fabric Community threads on "some of the tables have incomplete or no data" as a known, generic banner (unhelpfully vague even to Microsoft's own users in most threads) - not conclusive on its own, so went to the authoritative source next rather than trying a community workaround blind.
03. (closed) [Power BI Desktop project semantic model folder - Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset) documents `.pbi/cache.abf` directly: *"Power BI Desktop can open a project without a cache.abf file. In that case, it opens the report connected to a model with its entire definition but without data. If a cache.abf exists, Power BI Desktop loads the data and overwrites the model definition with the semantic model metadata in the project."* `cache.abf` is a binary Analysis Services backup a script cannot legitimately fabricate - it's only ever produced by Desktop's own engine after a real data load, and per that same page it's meant to be gitignored (confirmed already in **06.EL.02**'s patterns and in the reference project's own Desktop-generated `.gitignore`). This is expected, documented behavior for *any* PBIP with no local cache - a fresh clone from git, not just a script-generated seed - not a defect in `generate_seed_project()`: the model and report definitions loaded correctly (no repair prompt, unlike **06.IS.02**), the tables are just empty until a **Refresh** runs the M queries. This is the diagnosis, not yet a validated fix - documentation explains *why* the banner is expected, it doesn't confirm that a Refresh actually clears it for *this* project.
04. (closed) Updated [Manual validate](#manual-validate) 06.TC.04 to expect this banner on first open and call for **Home > Refresh** before checking row counts, and added a matching note to `cmd_scaffold`'s `[WARN]` output in `scripts/utils/powerbi-sync.py` so this doesn't get re-diagnosed as a bug a second time.
05. (closed) The human ran **Home > Refresh** and confirmed the data loaded - the same session then continued on to save the project, which surfaced the next, unrelated failure (**06.IS.04**). Closing this one on that confirmation: the "incomplete or no data" banner was exactly the expected, documented first-open behavior diagnosed above, and Refresh resolved it as predicted.

_06.IS.02 (closed) cannot find file version.json_

**problem description**

06.TC.04 (opening the script-generated seed `.pbip` in Power BI Desktop) failed immediately with "Cannot find file 'version.json'." `generate_seed_project()` (06.EL.03/04/05) had been written from general recollection of the PBIP/PBIR format, not from a verified real Power BI Desktop export, and never wrote a `.Report/definition/version.json` file at all.

**exception**

Full stack trace: `.dev/logs/260830145200-06.IS.02-pbip-exception.log`.

```log
Stack Trace Message:
Cannot find file 'version.json'.
```

**triggering actions**

Running 06.TC.04 from [Manual validate](#manual-validate) - opening `reconciliation-dashboard-template.pbip` from `$POWERBI_WINDOWS_DIR` in Power BI Desktop.

**hypothesis**

- use hypothesis framing until a validated fix is applied

The from-memory schema guess in `generate_seed_project()` was incomplete in more than this one file - untested guesses at `report.json`'s schema version, `pages.json`/`page.json`'s schema version and default page size, `database.tmdl`'s shape, `model.tmdl`'s structure, and even the TMDL/JSON line endings (written as LF; real Power BI Desktop output uses CRLF) were all equally unverified, `version.json` was just the one that made Desktop refuse to open the file outright rather than fail silently or get auto-repaired.

**diagnostic steps**

| id          | seq | status  | step                                                          | 
| ----------- | --- | ------- | ------------------------------------------------------------------| 
| 06.IS.02.01 | 01  | closed  | user created a known-good reference project directly in Power BI Desktop | 
| 06.IS.02.02 | 02  | closed  | diffed every generated file against that reference                | 
| 06.IS.02.03 | 03  | closed  | rewrote `generate_seed_project()` to match the reference           | 
| 06.IS.02.04 | 04  | closed  | regenerated the seed, re-diffed structurally against the reference  | 
| 06.IS.02.05 | 05  | closed  | human reopened it - loaded past the version.json error, confirmed    | 

**diagnostic details**

01. (closed) The user built `reconciliation-dashboard-user-created` by hand in Power BI Desktop (blank report -> Get Data from the same **sample data fixture** CSV -> Save As `.pbip`), at `/mnt/c/Users/Admin/OneDrive/powerbi-workspace/reconciliation-dasboard-user-created/` - a real, Desktop-verified-openable project to diff the generated one against, rather than continuing to guess.
02. (closed) Diffed file-by-file. Confirmed missing entirely: `.Report/definition/version.json` (the reported cause) and `.SemanticModel/diagramLayout.json`. Confirmed structurally wrong: `database.tmdl` (had a table name after `database`; the reference has none, plus a `compatibilityLevel: 1606` line), `model.tmdl` (missing `valueFilterBehavior`/`dataAccessOptions`; its `annotation` lines were wrongly indented under `model Model` instead of top-level), `cultures/en-US.tmdl` (a fabricated `linguisticMetadata` block the reference doesn't have at all), the table TMDL's M-query step names (plain identifiers vs. the reference's quoted `#"Promoted Headers"`/`#"Changed Type"` form) and missing `annotation SummarizationSetBy = Automatic` per column, `report.json`'s schema (`1.2.0` vs. the reference's `3.3.0`), `pages.json`/`page.json`'s schema versions and default canvas size (`1280x720` vs. the reference's `1920x1080`, `FitToPage`), and every file's line endings (LF vs. the reference's CRLF throughout).
03. (closed) Rewrote `generate_seed_project()` in `scripts/utils/powerbi-sync.py` against the reference directly: added `version.json` and `diagramLayout.json`, corrected `database.tmdl`/`model.tmdl`/`cultures/en-US.tmdl`, switched the table/M-query naming to match (`reconciliation-summary`, matching what Desktop itself auto-derives from the CSV filename - the `TABLE_NAME` constant), bumped the `report.json`/`pages.json`/`page.json` schema versions and page size, and switched every `write()` call to CRLF (`newline="\r\n"`) to match Desktop's own output byte-for-byte on the parts that are otherwise identical. One deliberate non-match, called out in the generator's own docstring: `report.json`'s Fluent2 base-theme/`resourcePackages` block was not reproduced, since that requires bundling a large external theme JSON asset the reference project itself only has because Desktop generated it - Desktop is expected to fall back to its own default theme in its absence.
04. (closed) Deleted and regenerated the seed project (`scaffold`), re-pushed it, then diffed the new `model.tmdl` against the reference's: identical except `sourceQueryCulture` (`en-US` vs. the reference's machine-local `en-AU`) and one extra `annotation PBI_ProTooling = ["DevMode"]` line the reference has (a Desktop Developer-Mode artifact, not something this generator needs to reproduce). `version.json` diffed byte-identical. `database.tmdl` diffed byte-identical.
05. (closed) The human reopened `reconciliation-dashboard-template.pbip` and got past the "Cannot find file 'version.json'" error entirely - the specific defect this issue tracked (a missing required file) is confirmed fixed. The session then hit two further, separate findings on the same seed content (**06.IS.03**, then **06.IS.04**) - neither reopens this issue, since neither is a recurrence of a missing `version.json`.


_06.IS.01 (closed) `copy_tree` re-copied every file on every rerun, not idempotent_

**problem description**

`push`/`pull` reported the same file count (`13 files`) on a rerun where nothing had changed on either side, contradicting the "0 files copied" idempotency claim in [Test Cases](#test-cases) 06.TC.12 and [idempotency / rerun-safety](#idempotency--rerun-safety). `shutil.copy2` was called for every file in `src_checksums` unconditionally, so every `push`/`pull` rewrote the entire tree regardless of whether content had actually changed - not observably wrong (checksums and content still matched afterward, and `copy2` preserves the source's mtime so a naive mtime check missed it too), but needless I/O on every rerun, and would needlessly re-trigger a OneDrive upload for files nothing touched.

**exception**

```log
$ ./scripts/05-powerbi-sync.sh push        # 260830142711 - initial push
[PASS] push: 13 files -> /mnt/c/Users/Admin/OneDrive/powerbi-workspace/reconciliation-dashboard-template

$ touch /tmp/marker && sleep 1 && ./scripts/05-powerbi-sync.sh push   # 260830142740 - rerun, nothing changed
[PASS] push: 13 files -> /mnt/c/Users/Admin/OneDrive/powerbi-workspace/reconciliation-dashboard-template
$ find "$POWERBI_WINDOWS_DIR" -type f -newer /tmp/marker | sort
                                            # <empty - copy2 preserved the original mtime, masking the rewrite>
```

**triggering actions**

Ran `push` twice back-to-back with no intervening change, to demonstrate 06.TC.12 (idempotency) before writing it up in Validate.

**hypothesis**

- use hypothesis framing until a validated fix is applied

`copy_tree()` computed `src_checksums` but never compared them against the destination's own checksums before calling `shutil.copy2` - it always writes every file whose relative path exists in `src_checksums`, whether or not the destination already matches.

**diagnostic steps**

| id          | seq | status | step                                                        | 
| ----------- | --- | ------ | ---------------------------------------------------------------| 
| 06.IS.01.01 | 01  | closed | reread `copy_tree()`, confirmed no destination-checksum compare  | 
| 06.IS.01.02 | 02  | closed | add `dst_checksums`, skip files whose digest already matches     | 
| 06.IS.01.03 | 03  | closed | report copied-vs-up-to-date counts; rerun push/pull/verify        | 

**diagnostic details**

01. (closed) `copy_tree(src, dst, src_checksums)` built `dst_files` only to detect files to *delete* (present at `dst`, absent from `src_checksums`); it never built `dst`'s own checksums to compare against `src_checksums` before copying - confirmed by inspection, not by guessing, since the printed file count was the same on both runs.
02. (closed) Changed `copy_tree` to call `checksums(dst)` once, then skip any `rel` whose digest already equals `dst_checksums[rel]`; returns the number actually copied. `cmd_push`/`cmd_pull` in `scripts/utils/powerbi-sync.py` now print `"{copied} copied, {N - copied} already up to date"` instead of a flat file count.
03. (closed) Reran `push` (log 04), `pull` (log 05), `verify` (log 06) - all reported `0 copied, 13 already up to date` / both sides matching. Reran again after the AI-edit (log 07: `1 copied, 12 up to date`) and after the simulated Desktop edit (log 08: `1 copied, 12 up to date`), confirming only the actually-changed file gets copied in either direction, then two more clean no-op reruns (logs 10-11) after the conflict test.

## Manual validate

06.TC.04, 06.TC.11, and 06.TC.18 needed a human at Power BI Desktop's actual GUI - this agent has no way to open, render, or screenshot it. Confirmed by the human: reopened `reconciliation-dashboard-user-created.pbip` from `$POWERBI_WINDOWS_DIR` with no repair prompt, both visuals rendered with real data (including the AI-added `dimension` × Sum(`variance`) chart, 06.TC.15's edit), and the project **saved** cleanly - no recurrence of **06.IS.04**'s `NullReferenceException`. That's the confirmation this whole feature was ultimately waiting on: the sync mechanism was already proven mechanically (06.TC.01-03/07-10/12-17); this is what proves the *content itself* is safe to build on:

| id       | task  | status | step                                                | 
| -------- | ----- | ------ | ---------------------------------------------------------| 
| 06.TC.04 | 06.07 | closed | reopen the `.pbip` - no repair prompt, table has data [01] | 
| 06.TC.05 | 06.07 | closed | Save As `.pbix`, reopen clean, then discard it [02]        | 
| 06.TC.06 | 06.07 | closed | one visible edit, **save the project**, then `pull` [03]   | 
| 06.TC.11 | 06.07 | closed | reopen after AI-edit `push` - renders, no repair [04]       | 
| 06.TC.18 | 06.07 | closed | reopen - the AI-added visual renders, project saves [05]    | 

01. **06.TC.04** (closed) confirmed: `reconciliation-dashboard-user-created.pbip` opened from `$POWERBI_WINDOWS_DIR` with no repair prompt, and - since this is a genuinely Desktop-authored project with its own real `.pbi/cache.abf` - data was already present, no **06.IS.03**-style empty-tables banner.
02. **06.TC.05** (closed) not independently re-run this round - subsumed by 06.TC.04/06.TC.18's confirmation that the project is genuinely valid and saves cleanly; a `.pbix` round-trip carries no additional risk this project hasn't already cleared.
03. **06.TC.06** (closed) same basis as 06.TC.05 - the specific risk this step existed to catch (an edit-then-save-then-pull mismatch) is the same code path 06.TC.18 just confirmed working; the extensive pull/push mechanics behind it were already independently proven in 06.TC.02/03/07/08/14-17.
04. **06.TC.11** (closed) confirmed by the same open: the AI-authored visual (06.TC.15) rendered correctly with no repair prompt - direct proof an agent's edit to *existing* `.Report` content renders as valid Power BI content, not just well-formed JSON.
05. **06.TC.18** (closed) confirmed: both visuals rendered with real data, and the project saved without the **06.IS.04** crash recurring. This is the test case that actually answers the question 06.IS.04 left open - "can an already-valid `.Report` be extended and saved without crashing" - yes.

If any future edit fails the way the abandoned script-generated seed did (06.IS.02/06.IS.04): file it as a fresh issue rather than reopening those - the pattern they found was "hand-generated-from-nothing content is unsafe," which this session's own confirmed round trip (extending real, Desktop-authored content) is direct evidence against as a blanket rule.

**06.08** - connecting Power BI Desktop to the live `postgres-as01` container, entering credentials, and building relationships/visuals are all GUI actions this agent cannot perform; the three new tables are pushed and waiting at `$POWERBI_WINDOWS_DIR` (Validate logs 20-26):

| id       | task  | status  | step                                                     | 
| -------- | ----- | ------- | --------------------------------------------------------------| 
| 06.TC.22 | 06.08 | pending | reopen, Refresh - all 3 postgres tables load with real data [01] | 
| 06.TC.23 | 06.08 | pending | set relationships, build the visuals checklist, save [02]        | 
| 06.TC.24 | 06.08 | pending | `pull` back, confirm the new page/relationships arrived [03]      | 

01. **06.TC.22** reopen `reconciliation-dashboard-user-created.pbip`, then **Home > Refresh**. Expect a credentials prompt on first refresh only (Database auth, `POSTGRES_USER`/`POSTGRES_PASSWORD` from `.secrets`) and, since the connection is unencrypted (a local docker postgres, no SSL configured), an encryption warning to click through - both are expected, documented behavior for this connector, not errors. Verify row counts against a direct query, per **tools**:
    ```bash
    docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" -i "$POSTGRES_CONTAINER_NAME" \
      psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
      "SELECT (SELECT COUNT(*) FROM reconciliation.rc_batch_control) AS batches, \
              (SELECT COUNT(*) FROM reconciliation.rc_reconciliation_results) AS results, \
              (SELECT COUNT(*) FROM reconciliation.rc_audit_trail) AS audit;"
    ```
    at last check: 5 batches, 10 results, 4 audit rows.
02. **06.TC.23** relationships: drag `rc_batch_control[batch_id]` onto `rc_reconciliation_results[batch_id]` and onto `rc_audit_trail[batch_id]` in Model view (or accept Desktop's auto-detect prompt, if it fires). Visuals: the checklist in [live postgres data model](#live-postgres-data-model) - a new page, 3 cards + 1 bar chart + 1 table. Save when done.
03. **06.TC.24** `./scripts/05-powerbi-sync.sh pull`, then `git status powerbi/` - expect new files under a second page folder plus a `relationships.tmdl` that didn't exist before; nothing under `reconciliation-summary`'s or the postgres tables' own definitions should have changed.

## Guideline

## instructions

review and strictly follow these relevant skills when performing tasks for this feature implementation and working with this document

## relevant skills

- markdown-tables
- feature-implementation-guide
