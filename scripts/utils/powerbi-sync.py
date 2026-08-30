#!/usr/bin/env python3
"""powerbi-sync.py

Bidirectional file sync between the git-tracked .pbip template (POWERBI_REPO_DIR)
and the Windows-side working copy Power BI Desktop actually opens (POWERBI_WINDOWS_DIR),
guarded by a checksum manifest. See:
    docs/features/06-powerbi-dashboard-setup.md -> Design -> sync script design

`scaffold` verifies the template exists and instructs a one-time human bootstrap
in Power BI Desktop if it doesn't - it does NOT hand-generate .pbip/.Report/
.SemanticModel content. See docs/features/06-powerbi-dashboard-setup.md ->
Revisions -> 06.01.R02 for why: a scripted generator was tried (06.01.R01) and
reverted after two real Power BI Desktop failures traced to it (06.IS.02,
06.IS.04), on top of Microsoft's own docs stating report.json/PBIR "doesn't
support external editing" during preview.

Usage:
    python3 scripts/utils/powerbi-sync.py {scaffold|push|pull|verify} \
        --repo-dir powerbi/reconciliation-dashboard-template \
        --windows-dir /mnt/c/Users/<user>/OneDrive/powerbi-workspace/reconciliation-dashboard-template
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
IGNORE_SUFFIXES = {".abf", ".tmp", ".pbix"}
CSV_RELPATH = "sample-data/reconciliation-summary.csv"


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


def copy_tree(src: Path, dst: Path, src_checksums: dict) -> int:
    """mirror src -> dst, skipping files whose content already matches at dst
    (per 06.IS.01 - copy2 otherwise rewrites every file on every rerun, which
    is not observably wrong but is needless churn, e.g. re-triggering a
    OneDrive upload for files nothing actually changed). Returns files copied."""
    dst.mkdir(parents=True, exist_ok=True)
    dst_checksums = checksums(dst)
    dst_files = set(dst_checksums)
    for stale in dst_files - set(src_checksums):
        (dst / stale).unlink()
    copied = 0
    for rel, digest in src_checksums.items():
        if dst_checksums.get(rel) == digest:
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / rel, target)
        copied += 1
    return copied


# ---------------------------------------------------------------------------
# scaffold - see docs/features/06-powerbi-dashboard-setup.md -> Revisions ->
# 06.01.R02: hand-generating .pbip/.Report content was reverted after two
# real failures traced to it (06.IS.02, 06.IS.04), on top of Microsoft's own
# docs stating report.json/PBIR "doesn't support external editing" during
# preview. scaffold is back to verify-and-instruct; the human creates the
# project once in Power BI Desktop (both Report and SemanticModel together,
# so Desktop keeps them internally consistent), then `pull` captures it.
# ---------------------------------------------------------------------------

def cmd_scaffold(repo_dir: Path, windows_dir: Path) -> int:
    if list(repo_dir.glob("*.pbip")):
        print(f"[PASS] scaffold: template already present at {repo_dir}")
        return 0
    print(f"[FAIL] scaffold: no .pbip file found under {repo_dir}")
    print("  this feature does not hand-author .pbip/.Report/.SemanticModel content -")
    print("  see docs/features/06-powerbi-dashboard-setup.md, Revisions 06.01.R02.")
    print("  create it once in Power BI Desktop:")
    print("    1. File > New > blank report")
    print(f"    2. Get Data > Text/CSV > {CSV_RELPATH} (under this project's own folder,")
    print("       once pushed - or the repo copy directly)")
    print(f"    3. File > Save as > Power BI project (.pbip), into {windows_dir}")
    print("    4. Close Power BI Desktop (releases its file locks)")
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
    copied = copy_tree(repo_dir, windows_dir, repo_sums)
    save_manifest(repo_dir, repo_sums, "push")
    print(f"[PASS] push: {copied} copied, {len(repo_sums) - copied} already up to date -> {windows_dir}")
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
    copied = copy_tree(windows_dir, repo_dir, win_sums)
    save_manifest(repo_dir, win_sums, "pull")
    print(f"[PASS] pull: {copied} copied, {len(win_sums) - copied} already up to date -> {repo_dir}")
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
