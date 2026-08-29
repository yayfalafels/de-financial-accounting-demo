#!/usr/bin/env python3
"""feedback-report.py

Closes the loop: reads back the batch reconciliation-runner.py just wrote,
independently sums the expected 'amount' variance implied by
data/mock/issue-log.csv's Bronze-side issues (assessment-1 catalog ids
09-14), compares it against the runner's own measured 'amount' variance,
inserts one reconciliation.rc_audit_trail row (INVESTIGATE if they
disagree beyond tolerance, NOTIFY otherwise), and prints a
[PASS]/[FAIL] summary. Exits non-zero if the batch's own status is FAIL
or the ground-truth check disagrees. See
docs/features/05-ai-closed-loop-validation.md -> Design -> ground-truth
feedback & audit trail.

Usage:
    python3 scripts/utils/feedback-report.py \
        --container postgres-as01 --user as01_admin --db as01_source_db \
        --issue-log data/mock/issue-log.csv
"""

import argparse
import csv
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ISSUE_LOG = REPO_ROOT / "data" / "mock" / "issue-log.csv"
WORK_DIR = REPO_ROOT / ".dev" / "tmp" / "feedback-report"

TOLERANCE_ABS = 1.00  # dollars - absorbs float/decimal rounding, not a real disagreement
ACTOR = "feedback-report.py"


def run_query(container: str, user: str, db: str, query: str) -> list[str]:
    cmd = ["docker", "exec", "-i", container, "psql", "-U", user, "-d", db, "-t", "-A", "-F", "|", "-c", query]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"psql query failed: {result.stderr.strip()}")
    return [line for line in result.stdout.strip().splitlines() if line.strip()]


def latest_batch(container: str, user: str, db: str) -> int:
    rows = run_query(container, user, db, "SELECT MAX(batch_id) FROM reconciliation.rc_batch_control;")
    return int(rows[0])


def measured_amount_variance(container: str, user: str, db: str, batch_id: int) -> float:
    query = (
        "SELECT variance FROM reconciliation.rc_reconciliation_results "
        f"WHERE batch_id = {batch_id} AND dimension = 'amount';"
    )
    rows = run_query(container, user, db, query)
    if not rows:
        raise RuntimeError(f"no 'amount' dimension row found for batch_id={batch_id}")
    return float(rows[0])


def source_amounts(container: str, user: str, db: str, transaction_ids: list[str]) -> dict:
    if not transaction_ids:
        return {}
    id_list = ", ".join(f"'{t}'" for t in transaction_ids)
    query = f"SELECT transaction_id, transaction_amount FROM src_transaction_daily WHERE transaction_id IN ({id_list});"
    amounts = {}
    for line in run_query(container, user, db, query):
        txn_id, amount = line.split("|")
        amounts[txn_id] = float(amount)
    return amounts


def expected_amount_variance(container: str, user: str, db: str, issue_log_path: Path) -> float:
    with issue_log_path.open() as f:
        issue_rows = list(csv.DictReader(f))

    mismatch_delta = sum(
        float(r["injected_value"]) - float(r["expected_value"])
        for r in issue_rows
        if r["table"] == "bronze.transaction_daily" and r["issue_type"] == "bronze_amount_mismatch"
    )
    missing_ids = [r["row_key"] for r in issue_rows
                   if r["table"] == "bronze.transaction_daily" and r["issue_type"] == "missing_in_bronze_unrelated"]
    midnight_ids = [r["row_key"] for r in issue_rows
                    if r["table"] == "src_transaction_daily" and r["issue_type"] == "utc_sgt_midnight_boundary"]
    duplicate_ids = [r["row_key"] for r in issue_rows
                     if r["table"] == "bronze.transaction_daily" and r["issue_type"] == "duplicate_in_bronze_reprocessed"]

    amounts = source_amounts(container, user, db, list(set(missing_ids + midnight_ids + duplicate_ids)))
    dropped_amount = sum(amounts.get(t, 0.0) for t in missing_ids + midnight_ids)
    duplicated_amount = sum(amounts.get(t, 0.0) for t in duplicate_ids)

    return mismatch_delta - dropped_amount + duplicated_amount


def batch_status(container: str, user: str, db: str, batch_id: int) -> str:
    rows = run_query(container, user, db, f"SELECT status FROM reconciliation.rc_batch_control WHERE batch_id={batch_id};")
    return rows[0] if rows else "FAIL"


def write_audit_row(container: str, user: str, db: str, batch_id: int, action: str) -> None:
    row = {"batch_id": batch_id, "action": action, "actor": ACTOR, "created_at": datetime.now().isoformat()}
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = WORK_DIR / f"batch_{batch_id}_audit.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)

    col_list = ", ".join(row.keys())
    cmd = [
        "docker", "exec", "-i", container, "psql", "-U", user, "-d", db, "-v", "ON_ERROR_STOP=1",
        "-c", f"\\copy reconciliation.rc_audit_trail ({col_list}) FROM STDIN WITH (FORMAT csv, HEADER true)",
    ]
    with csv_path.open("rb") as f:
        result = subprocess.run(cmd, stdin=f, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"\\copy into rc_audit_trail failed: {result.stderr.strip()}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--container", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--issue-log", type=Path, default=DEFAULT_ISSUE_LOG)
    args = parser.parse_args()

    try:
        batch_id = latest_batch(args.container, args.user, args.db)
        measured = measured_amount_variance(args.container, args.user, args.db, batch_id)
        expected = expected_amount_variance(args.container, args.user, args.db, args.issue_log)
        status = batch_status(args.container, args.user, args.db, batch_id)

        mismatch = abs(measured - expected) > TOLERANCE_ABS
        action = "INVESTIGATE" if mismatch else "NOTIFY"
        write_audit_row(args.container, args.user, args.db, batch_id, action)
    except Exception as exc:  # noqa: BLE001 - top-level safe wrapper, no silent failure
        print(f"[FAIL] feedback-report: {exc}", file=sys.stderr)
        return 1

    print(f"[INFO] batch_id={batch_id} measured_variance={measured:.2f} expected_variance={expected:.2f}")
    verdict = "[FAIL]" if mismatch else "[PASS]"
    print(f"{verdict} feedback-report: measured vs. issue-log expected variance - action={action}")

    if status == "FAIL" or mismatch:
        print(f"[FAIL] feedback-report: batch_id={batch_id} overall status={status} action={action}")
        return 1
    print(f"[PASS] feedback-report: batch_id={batch_id} overall status={status} action={action}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
