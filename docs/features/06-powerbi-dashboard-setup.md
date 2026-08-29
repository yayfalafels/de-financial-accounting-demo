# Power BI Dashboard Setup - Feature tracker
>Review the guidelines before performing any actions including edits on the document

## 06 (open) power bi dashboard setup

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
| 06.03 | 04  | open    | `.pbip` template scaffold                    | 
| 06.04 | 05  | pending | sync script (`/mnt` <-> repo)                | 
| 06.05 | 06  | pending | round-trip sync validation                   | 
| 06.06 | 07  | pending | assessment-facing usage documentation        | 
| 06.IS | 08  | pending | validate                                     | 

## Scope

set up a git-tracked, version-controlled Power BI workspace using `.pbip` (Power BI Project) template files, plus a sync script keeping them mirrored between the Windows-side `/mnt/...` path (where Power BI Desktop actually runs - it's Windows-only and can't run inside this Linux/Docker sandbox) and this repo's `/home/...` working copy.

- Power BI Desktop is Windows-only and cannot run inside this Linux/Docker sandbox - this feature's job is to keep the `.pbip` project git-tracked and mirrored, not to run or render Power BI itself
- the deliverable is a reusable `.pbip` **template**, not a finished dashboard - both assessment 1 and assessment 3 need a dashboard/dashboard-mock-up deliverable per the **assignment design doc**'s Task 5 (Assessment 3) and deliverable list (Assessment 1), and this feature gives them a common starting point instead of each assessment inventing its own workspace layout
- the sync script keeps the Windows-side `/mnt/...` working copy (where Power BI Desktop actually saves its files) and this repo's `/home/...` git-tracked copy mirrored in both directions, so edits made inside Power BI Desktop round-trip back into git without manual copy/paste and without data loss
- `.pbip` (not `.pbix`) specifically because it's Power BI's source-controllable, folder-of-text-files project format - the whole point of this feature is that the workspace lives in git like every other artifact in this repo, not as an opaque binary
- does not build the assessments' actual dashboard content (KPIs, visuals, filters, DAX measures) - the **assignment design doc**'s Task 5 executive KPIs and recommended visuals stay scoped to assessment 1 and assessment 3's own deliverables; this feature only stands up the reusable scaffold and sync workflow they build on top of
- does not attempt to run, automate, or headlessly render Power BI Desktop from the Linux side - no CI validation of the `.pbip` content itself; round-trip correctness is checked by diffing the synced files, not by opening Power BI
- depends on nothing already provisioned by prior milestones - this feature's `.pbip` template is a starting scaffold, not wired to live postgres/Spark data yet; connecting it to real reconciliation results is additive work left to the assessments that build on it

## References

- **dev env design doc** `docs/design/development-environment.md` (BI tooling note, Scenario 6 dashboard-mockup scenario)
- **assignment design doc** `docs/design/assignment.md` (Task 5 - Power BI Dashboard; Assessment 1's dashboard mock-up deliverable)
- **ai closed-loop validation tracker** `docs/features/05-ai-closed-loop-validation.md`
- **powerbi template** `powerbi/reconciliation-dashboard-template/reconciliation-dashboard-template.pbip` (+ its `.Report` / `.SemanticModel` folders)
- **sync script** `scripts/05-powerbi-sync.sh`
- **sample data fixture** `powerbi/reconciliation-dashboard-template/sample-data/reconciliation-summary.csv`

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

| id | subcommand | direction                    | when used                                                             | 
| -- | ---------- | ---------------------------- | --------------------------------------------------------------------- | 
| 01 | `scaffold` | repo only                    | first-time creation of the template (verify-or-create)                | 
| 02 | `push`     | repo -> `/mnt` working copy  | start/resume a Power BI Desktop editing session                       | 
| 03 | `pull`     | `/mnt` working copy -> repo  | capture edits made in Power BI Desktop back into git                  | 
| 04 | `verify`   | read-only, both sides        | round-trip / rerun-safety proof, see [workflow validation runner](#workflow-validation-runner) | 

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
| 06.TC.01 | 06.03 | self-report | `scaffold` verifies template + CSV fixture present, `[PASS]`   | 
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

01. **06.TC.03** `diff -rq`/`sha256sum` run directly against both directories, independent of `powerbi-sync.py`'s own printed summary - see **tools** below.
02. **06.TC.04** "no repair prompt" is the concrete signal Power BI Desktop uses when it can't parse a hand/AI-modified project; that absence, plus the **sample data fixture**'s rows actually showing in a table visual, is the pass condition - not just "the app didn't crash".
03. **06.TC.05** Save As `.pbix` is a one-time sanity check that the `.pbip` project is a fully valid, loadable Power BI project (`.pbix` packages the live model+report together) - per [`.pbip` project anatomy](#pbip-project-anatomy) the resulting `.pbix` stays out of git; discard it after this check, it is not a tracked deliverable.
04. **06.TC.06** the edit should be something a byte diff can unambiguously confirm afterwards - e.g. renaming the visual's title or adding a text box with known text - not a cosmetic drag/resize that TMDL/PBIR may serialize non-deterministically.
05. **06.TC.08** checked against the pre-edit commit (`git diff`) or the prior manifest checksums - proving `pull` didn't silently touch files the human never edited (a Desktop-generated cache file leaking past 06.EL.02's `.gitignore` patterns would be exactly this kind of miss).
06. **06.TC.09** applied with the same Edit tool used on every other git-tracked file in this repo - no Power BI Desktop involved on this leg - proving an agent, not only a human via the Desktop GUI, can produce a change Power BI Desktop later accepts as valid.
07. **06.TC.11** the layer that actually proves the AI's edit was valid *Power BI* content, not merely well-formed JSON/TMDL syntax - a malformed AI edit could still pass 06.TC.10's plain file copy and only fail here.
08. **06.TC.12** reruns `push` then `pull` back-to-back with no intervening change on either side; per [idempotency / rerun-safety](#idempotency--rerun-safety) a fully-matching manifest means zero files copied - checked directly, not by trusting the script's own "up to date" line.

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
| 06.EL.03 | `*.pbip`                 | new, bootstrapped from Power BI Desktop, not hand-authored     | 
| 06.EL.04 | `*.Report/`              | new, bootstrapped from Power BI Desktop, not hand-authored     | 
| 06.EL.05 | `*.SemanticModel/`       | new, bootstrapped from Power BI Desktop, not hand-authored     | 
| 06.EL.06 | `.sync-manifest.json`    | new, generated by first successful sync, git-tracked           | 
| 06.EL.07 | `powerbi-sync.py`        | new: scaffold/push/pull/verify logic, checksum manifest        | 
| 06.EL.08 | `05-powerbi-sync.sh`     | new: thin CLI wrapper, dispatches to 06.EL.07                  | 

01. **06.EL.01** `.env` / `.env.sample`
02. **06.EL.02** `.gitignore`
03. **06.EL.03** `powerbi/reconciliation-dashboard-template/reconciliation-dashboard-template.pbip`
04. **06.EL.04** `powerbi/reconciliation-dashboard-template/reconciliation-dashboard-template.Report/`
05. **06.EL.05** `powerbi/reconciliation-dashboard-template/reconciliation-dashboard-template.SemanticModel/`
06. **06.EL.06** `powerbi/reconciliation-dashboard-template/.sync-manifest.json`
07. **06.EL.07** `scripts/utils/powerbi-sync.py`
08. **06.EL.08** `scripts/05-powerbi-sync.sh`

## Implement

>this section is the implementation guide - instructions to carry out, written before any of it is applied to disk. Once executed, the Validate section records what actually happened, per the same before/after split

Applied in dependency order, each step referencing its **Edit locations** id:

01. **`.env` / `.env.sample`** (06.EL.01) - add a new block alongside the existing per-feature sections. `POWERBI_REPO_DIR` is the same value for everyone (default-able), `POWERBI_WINDOWS_DIR` is machine-specific and has no safe default - `.env.sample` keeps a placeholder, the real `.env` value is filled in locally by whoever has Power BI Desktop installed:

    ```bash
    # power bi dashboard sync (feature 06) - machine-specific Windows path, no secrets
    POWERBI_REPO_DIR=powerbi/reconciliation-dashboard-template
    POWERBI_WINDOWS_DIR=/mnt/c/Users/<windows-user>/OneDrive/powerbi-workspace/reconciliation-dashboard-template
    ```

02. **`.gitignore`** (06.EL.02) - Power BI Desktop writes a local cache/settings folder and binary cache artifacts alongside a `.pbip` project whenever it's opened; these are machine-local noise, not part of the tracked template, and would otherwise make the [sync script design](#sync-script-design)'s checksum manifest drift on every open:

    ```gitignore
    # power bi (feature 06) - Desktop-generated cache/local settings, never the tracked project itself
    powerbi/**/.pbi/
    powerbi/**/*.abf
    ```

03. **`.pbip` / `.Report/` / `.SemanticModel/`** (06.EL.03, 06.EL.04, 06.EL.05) - per [`.pbip` project anatomy](#pbip-project-anatomy), these are Power BI Desktop's own generated format (PBIR JSON, TMDL text); this feature does not hand-author them from scratch; publicly documented examples of the exact JSON/TMDL shape exist but the byte-exact schema is versioned by whichever Power BI Desktop build does the export, so hand-typing it risks producing a project Power BI Desktop itself then "repairs" or rejects. Bootstrap once, on the Windows side, via the UI - not code:

    ```text
    1. Open Power BI Desktop.
    2. File > New > blank report.
    3. File > Save as > Power BI project (.pbip).
    4. Save into: %POWERBI_WINDOWS_DIR% (the path from Edit locations 01,
       e.g. C:\Users\<windows-user>\OneDrive\powerbi-workspace\reconciliation-dashboard-template)
    5. Close Power BI Desktop (releases its file locks before syncing).
    ```

    Then capture that bootstrap into git by running `pull` (06's step 05 below) - the Windows-side output becomes the repo-tracked template's initial content, not a hand-written stand-in for it.

04. **`.sync-manifest.json`** (06.EL.06) - not hand-authored either; `cmd_pull`/`cmd_push` in 06.EL.07 write it as a side effect of the first successful sync. Its shape:

    ```json
    {
      "checksums": {
        "reconciliation-dashboard-template.pbip": "3f2ad1...",
        "reconciliation-dashboard-template.Report/report.json": "9c1e77...",
        "reconciliation-dashboard-template.SemanticModel/definition/model.tmdl": "77bd42..."
      },
      "last_sync_utc": "2026-08-29T13:05:00Z",
      "last_sync_direction": "pull"
    }
    ```

    Tracked in git (not gitignored) - it's the shared "last known good" reference both sides diff against, per [sync script design](#sync-script-design); a fresh clone needs it to detect drift on the first `push`/`pull` it runs.

05. **`scripts/utils/powerbi-sync.py`** (06.EL.07) - the checksum-manifest logic behind all four subcommands from [sync script design](#sync-script-design):

    ```python
    #!/usr/bin/env python3
    """scripts/utils/powerbi-sync.py

    Bidirectional file sync between the git-tracked .pbip template (POWERBI_REPO_DIR)
    and the Windows-side working copy Power BI Desktop actually opens (POWERBI_WINDOWS_DIR),
    guarded by a checksum manifest.
    See docs/features/06-powerbi-dashboard-setup.md -> Design -> sync script design.
    """
    import argparse
    import hashlib
    import json
    import shutil
    import sys
    import time
    from pathlib import Path

    MANIFEST_NAME = ".sync-manifest.json"
    IGNORE_DIRS = {".pbi", "__pycache__"}
    IGNORE_SUFFIXES = {".abf", ".tmp"}


    def checksums(root: Path) -> dict[str, str]:
        out = {}
        for path in sorted(root.rglob("*")):
            if path.is_dir():
                continue
            if any(part in IGNORE_DIRS for part in path.relative_to(root).parts):
                continue
            if path.suffix in IGNORE_SUFFIXES or path.name == MANIFEST_NAME:
                continue
            rel = str(path.relative_to(root))
            out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        return out


    def load_manifest(repo_dir: Path) -> dict:
        manifest_path = repo_dir / MANIFEST_NAME
        if not manifest_path.exists():
            return {"checksums": {}, "last_sync_utc": None, "last_sync_direction": None}
        return json.loads(manifest_path.read_text())


    def save_manifest(repo_dir: Path, checksum_map: dict, direction: str) -> None:
        manifest_path = repo_dir / MANIFEST_NAME
        manifest_path.write_text(json.dumps({
            "checksums": checksum_map,
            "last_sync_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "last_sync_direction": direction,
        }, indent=2, sort_keys=True) + "\n")


    def diverged(current: dict, manifest_checksums: dict) -> list[str]:
        """files in `current` that don't match the last-known-good manifest."""
        return sorted(p for p, h in current.items() if manifest_checksums.get(p) != h)


    def copy_tree(src: Path, dst: Path, src_checksums: dict) -> None:
        dst.mkdir(parents=True, exist_ok=True)
        dst_files = {str(p.relative_to(dst)) for p in dst.rglob("*")
                     if p.is_file() and p.name != MANIFEST_NAME}
        for stale in dst_files - set(src_checksums):
            (dst / stale).unlink()
        for rel in src_checksums:
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src / rel, target)


    def cmd_scaffold(repo_dir: Path, windows_dir: Path) -> int:
        if list(repo_dir.glob("*.pbip")):
            print(f"[PASS] scaffold: template already present at {repo_dir}")
            return 0
        print(f"[FAIL] scaffold: no .pbip file found under {repo_dir}")
        print("  this feature does not hand-author .pbip/.Report/.SemanticModel content -")
        print("  create it once in Power BI Desktop (File > New > blank report >")
        print(f"  Save as > Power BI project), saved into: {windows_dir}")
        print("  then run: scripts/05-powerbi-sync.sh pull")
        return 1


    def cmd_push(repo_dir: Path, windows_dir: Path) -> int:
        manifest = load_manifest(repo_dir)
        repo_sums = checksums(repo_dir)
        if windows_dir.exists():
            stale = diverged(checksums(windows_dir), manifest["checksums"])
            if stale:
                print(f"[FAIL] push: {windows_dir} has un-pulled changes, would overwrite: {stale}")
                print("  run: scripts/05-powerbi-sync.sh pull   (capture the Desktop edits first)")
                return 1
        copy_tree(repo_dir, windows_dir, repo_sums)
        save_manifest(repo_dir, repo_sums, "push")
        print(f"[PASS] push: {len(repo_sums)} files -> {windows_dir}")
        return 0


    def cmd_pull(repo_dir: Path, windows_dir: Path) -> int:
        if not windows_dir.exists():
            print(f"[FAIL] pull: {windows_dir} does not exist - nothing to pull")
            return 1
        manifest = load_manifest(repo_dir)
        win_sums = checksums(windows_dir)
        repo_stale = diverged(checksums(repo_dir), manifest["checksums"])
        win_stale = diverged(win_sums, manifest["checksums"])
        if repo_stale and win_stale:
            print("[FAIL] pull: both sides changed since last sync - resolve manually")
            print(f"  repo-side:    {repo_stale}")
            print(f"  windows-side: {win_stale}")
            return 1
        copy_tree(windows_dir, repo_dir, win_sums)
        save_manifest(repo_dir, win_sums, "pull")
        print(f"[PASS] pull: {len(win_sums)} files -> {repo_dir}")
        return 0


    def cmd_verify(repo_dir: Path, windows_dir: Path) -> int:
        manifest = load_manifest(repo_dir)
        repo_ok = not diverged(checksums(repo_dir), manifest["checksums"])
        win_ok = windows_dir.exists() and not diverged(checksums(windows_dir), manifest["checksums"])
        print(f"[{'PASS' if repo_ok else 'WARN'}] verify: repo-side matches last-sync manifest")
        print(f"[{'PASS' if win_ok else 'WARN'}] verify: windows-side matches last-sync manifest")
        return 0 if (repo_ok and win_ok) else 1


    def main() -> int:
        parser = argparse.ArgumentParser()
        parser.add_argument("command", choices=["scaffold", "push", "pull", "verify"])
        parser.add_argument("--repo-dir", required=True, type=Path)
        parser.add_argument("--windows-dir", required=True, type=Path)
        args = parser.parse_args()
        dispatch = {"scaffold": cmd_scaffold, "push": cmd_push, "pull": cmd_pull, "verify": cmd_verify}
        return dispatch[args.command](args.repo_dir, args.windows_dir)


    if __name__ == "__main__":
        sys.exit(main())
    ```

    `diverged()` is what [sync script design](#sync-script-design)'s conflict rule maps to directly: a file counts as "changed since last sync" when its checksum no longer matches the manifest, and `pull`/`push` refuse to proceed only when *both* sides show divergence at once - a single-sided change always has an unambiguous direction to copy.

06. **`scripts/05-powerbi-sync.sh`** (06.EL.08) - thin wrapper: sources `.env`, resolves the log file name per the `feature-implementation-guide` skill's `<ts>-<task-id>-<name>.log` convention, fails fast if `POWERBI_WINDOWS_DIR` is unset, then dispatches to 06.EL.07:

`cmd_verify` above is the read-only "are we currently in sync" check; the [workflow validation runner](#workflow-validation-runner)'s destructive round-trip proof (push, edit, pull, diff, both directions, twice) is a test-harness procedure built on top of `push`/`pull`/`verify`, not a fifth subcommand - it belongs in 06.05's own validation script/session, not baked into 06.EL.07's production code path.

    ```bash
    #!/usr/bin/env bash
    # scripts/05-powerbi-sync.sh
    # Orchestrates the .pbip template <-> Windows working-copy sync (feature 06).
    # Usage: scripts/05-powerbi-sync.sh {scaffold|push|pull|verify}
    set -euo pipefail
    cd "$(dirname "${BASH_SOURCE[0]}")/.."
    set -a && source .env && set +a

    SUBCOMMAND="${1:-}"
    case "$SUBCOMMAND" in
      scaffold|push|pull) TASK_ID=06.04 ;;
      verify)             TASK_ID=06.05 ;;
      *) echo "usage: $0 {scaffold|push|pull|verify}" >&2; exit 2 ;;
    esac

    : "${POWERBI_WINDOWS_DIR:?POWERBI_WINDOWS_DIR not set in .env - see docs/features/06-powerbi-dashboard-setup.md#environment--secrets}"
    : "${POWERBI_REPO_DIR:=powerbi/reconciliation-dashboard-template}"

    if [[ "$SUBCOMMAND" != "scaffold" && ! -d "$POWERBI_WINDOWS_DIR" ]]; then
      echo "[FAIL] POWERBI_WINDOWS_DIR does not exist: $POWERBI_WINDOWS_DIR" >&2
      exit 1
    fi

    mkdir -p "$LOGS_DIR"
    TS="$(date +"$TIMESTAMP_FORMAT")"
    LOG_FILE="$LOGS_DIR/${TS}-${TASK_ID}-powerbi-sync-${SUBCOMMAND}.log"

    python3 scripts/utils/powerbi-sync.py "$SUBCOMMAND" \
      --repo-dir "$POWERBI_REPO_DIR" \
      --windows-dir "$POWERBI_WINDOWS_DIR" \
      | tee "$LOG_FILE"

    exit "${PIPESTATUS[0]}"
    ```

## Validate

**Issues**

- inventory all first out exceptions and issues encountered in this table
- for each issue, create an issue section and use this section to document diagnostics and resolution steps

| id       | seq | status  | issue                                     | 
| -------- | --- | ------- | ------------------------------------------ | 
| 06.IS.01 | 01  | pending | <first out exception>                      | 

_06.IS.01 (pending) <first out exception>_

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
| 06.IS.01.01 | 01  | pending | <diagnostic step 01>                       | 

**diagnostic details**

## Guideline

## instructions

review and strictly follow these relevant skills when performing tasks for this feature implementation and working with this document

## relevant skills

- markdown-tables
- feature-implementation-guide
