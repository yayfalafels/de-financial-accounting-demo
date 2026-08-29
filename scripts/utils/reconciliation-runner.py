#!/usr/bin/env python3
"""reconciliation-runner.py

Computes Assessment 1's batch-level source-vs-bronze reconciliation
(src_transaction_daily vs bronze.transaction_daily: row count and
SUM(transaction_amount)), inserts one new reconciliation.rc_batch_control
row plus two reconciliation.rc_reconciliation_results rows (dimension =
'row_count' / 'amount'), and prints a [PASS]/[WARNING]/[FAIL] summary per
dimension plus one overall summary line.

No third-party DB driver - shells out to psql via `docker exec`, same
convention as schema-inspect.py / seed-inspect.py. batch_id is reserved
via psql `nextval(...)` (not a live INSERT ... RETURNING) so the same
value can be written into both CSVs before either is \\copy-loaded. See
docs/features/05-ai-closed-loop-validation.md -> Design -> reconciliation
control schema.

Usage:
    python3 scripts/utils/reconciliation-runner.py \
        --container postgres-as01 --user as01_admin --db as01_source_db \
        --assessment-id assessment-1
"""

import argparse
import csv
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORK_DIR = REPO_ROOT / ".dev" / "tmp" / "reconciliation-runner"

SOURCE_TABLE = "src_transaction_daily"
BRONZE_TABLE = "bronze.transaction_daily"
AMOUNT_COL = "transaction_amount"


def status_for(variance_pct: float) -> str:
    # PASS <0.1%, WARNING <1%, FAIL >=1% - matches the CHECK thresholds in
    # rc-reconciliation-results-schema.json
    pct = abs(variance_pct)
    if pct < 0.1:
        return "PASS"
    if pct < 1.0:
        return "WARNING"
    return "FAIL"


def psql_scalar(container: str, user: str, db: str, query: str) -> str:
    cmd = ["docker", "exec", "-i", container, "psql", "-U", user, "-d", db, "-t", "-A", "-c", query]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"psql query failed: {result.stderr.strip()}")
    return result.stdout.strip()


def psql_copy(container: str, user: str, db: str, table: str, columns: list[str], csv_path: Path) -> None:
    col_list = ", ".join(columns)
    cmd = [
        "docker", "exec", "-i", container, "psql", "-U", user, "-d", db, "-v", "ON_ERROR_STOP=1",
        "-c", f"\\copy {table} ({col_list}) FROM STDIN WITH (FORMAT csv, HEADER true)",
    ]
    with csv_path.open("rb") as f:
        result = subprocess.run(cmd, stdin=f, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"\\copy into {table} failed: {result.stderr.strip()}")


def reserve_batch_id(container: str, user: str, db: str) -> int:
    seq = "reconciliation.rc_batch_control_batch_id_seq"
    return int(psql_scalar(container, user, db, f"SELECT nextval('{seq}');"))


def measure(container: str, user: str, db: str) -> dict:
    return {
        "source_count": int(psql_scalar(container, user, db, f"SELECT COUNT(*) FROM {SOURCE_TABLE};")),
        "bronze_count": int(psql_scalar(container, user, db, f"SELECT COUNT(*) FROM {BRONZE_TABLE};")),
        "source_amount": float(psql_scalar(container, user, db, f"SELECT COALESCE(SUM({AMOUNT_COL}),0) FROM {SOURCE_TABLE};")),
        "bronze_amount": float(psql_scalar(container, user, db, f"SELECT COALESCE(SUM({AMOUNT_COL}),0) FROM {BRONZE_TABLE};")),
    }


def build_dimension_rows(batch_id: int, m: dict) -> list[dict]:
    rows = []
    for dimension, source_value, target_value in (
        ("row_count", m["source_count"], m["bronze_count"]),
        ("amount", m["source_amount"], m["bronze_amount"]),
    ):
        variance = target_value - source_value
        variance_pct = round((variance / source_value * 100) if source_value else 0.0, 4)
        rows.append({
            "batch_id": batch_id,
            "dimension": dimension,
            "source_value": source_value,
            "target_value": target_value,
            "variance": variance,
            "variance_pct": variance_pct,
            "reconciliation_status": status_for(variance_pct),
            "created_at": datetime.now().isoformat(),
        })
    return rows


def worst_status(rows: list[dict]) -> str:
    order = {"PASS": 0, "WARNING": 1, "FAIL": 2}
    return max((r["reconciliation_status"] for r in rows), key=lambda s: order[s])


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--container", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--assessment-id", default="assessment-1")
    args = parser.parse_args()

    try:
        batch_id = reserve_batch_id(args.container, args.user, args.db)
        dimension_rows = build_dimension_rows(batch_id, measure(args.container, args.user, args.db))
        status = worst_status(dimension_rows)

        batch_row = {
            "batch_id": batch_id,
            "batch_date": date.today().isoformat(),
            "assessment_id": args.assessment_id,
            "status": status,
            "created_at": datetime.now().isoformat(),
        }

        batch_csv = WORK_DIR / f"batch_{batch_id}_control.csv"
        results_csv = WORK_DIR / f"batch_{batch_id}_results.csv"
        write_csv(batch_csv, list(batch_row.keys()), [batch_row])
        write_csv(results_csv, list(dimension_rows[0].keys()), dimension_rows)

        psql_copy(args.container, args.user, args.db, "reconciliation.rc_batch_control",
                  list(batch_row.keys()), batch_csv)
        psql_copy(args.container, args.user, args.db, "reconciliation.rc_reconciliation_results",
                  list(dimension_rows[0].keys()), results_csv)
    except Exception as exc:  # noqa: BLE001 - top-level safe wrapper, no silent failure
        print(f"[FAIL] reconciliation-runner: {exc}", file=sys.stderr)
        return 1

    for r in dimension_rows:
        print(f"[{r['reconciliation_status']}] {r['dimension']}: source={r['source_value']} "
              f"bronze={r['target_value']} variance_pct={r['variance_pct']}%")
    print(f"[{status}] reconciliation-runner: batch_id={batch_id} overall status={status}")
    return 0 if status != "FAIL" else 1


if __name__ == "__main__":
    sys.exit(main())
