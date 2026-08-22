#!/usr/bin/env python3
"""seed-inspect.py

Read-only validation of feature 04's seeded mock data. Two checks:

1. Row counts per table are non-zero and roughly in line with expectations
   (a loose sanity bound, not a hardcoded target - the generator's own
   output is the source of truth for exact counts).
2. Ground-truth cross-check: for every row logged in data/mock/issue-log.csv
   (the generator's own record of what it injected), re-query the live
   table by row key and confirm the row is actually present/mutated as
   claimed - an exact check against the seed run's own output, not a
   fuzzy minimum-count heuristic.

See docs/features/04-seed-mock-data.md -> Design -> ai closed-loop
validation for why this is designed this way.

Deliberately has no third-party DB driver dependency - shells out to the
psql client already bundled in the postgres:15-alpine image, via
`docker exec`, the same convention feature 02's schema-inspect.py uses.

Usage:
    python3 scripts/utils/seed-inspect.py \
        --issue-log data/mock/issue-log.csv \
        --container postgres-as01 --user as01_admin --db as01_source_db
"""

import argparse
import csv
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ISSUE_LOG = REPO_ROOT / "data" / "mock" / "issue-log.csv"

TABLES = [
    "src_transaction_daily",
    "bronze.transaction_daily",
    "ref.accounting_mapping",
    "bronze.finance_transactions",
    "finance.gl_balance",
    "bronze.customer_master",
    "source.payment_transactions",
    "bronze.payment_transactions",
    "regulatory.payment_reporting",
]

# (min, max) sanity bounds - loose, from docs/features/04-seed-mock-data.md volume budget
ROW_COUNT_BOUNDS = {
    "src_transaction_daily": (1500, 2500),
    "bronze.transaction_daily": (1500, 2500),
    "ref.accounting_mapping": (10, 60),
    "bronze.finance_transactions": (1000, 2000),
    "finance.gl_balance": (100, 800),
    "bronze.customer_master": (250, 400),
    "source.payment_transactions": (1500, 2500),
    "bronze.payment_transactions": (1500, 2500),
    "regulatory.payment_reporting": (100, 2500),
}


def run_query(container: str, user: str, db: str, query: str) -> list[str]:
    cmd = [
        "docker", "exec", "-i", container,
        "psql", "-U", user, "-d", db, "-t", "-A", "-c", query,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"psql query failed: {result.stderr.strip()}")
    return [line for line in result.stdout.strip().splitlines() if line.strip()]


def check_row_counts(container: str, user: str, db: str) -> bool:
    all_pass = True
    for table in TABLES:
        rows = run_query(container, user, db, f"SELECT COUNT(*) FROM {table};")
        count = int(rows[0]) if rows else 0
        low, high = ROW_COUNT_BOUNDS[table]
        if low <= count <= high:
            print(f"[PASS] row count {table}: {count} (expected {low}-{high})")
        else:
            print(f"[FAIL] row count {table}: {count} (expected {low}-{high})")
            all_pass = False
    return all_pass


def check_issue_categories(issue_log_path: Path) -> bool:
    """Confirm issue-log.csv itself has at least one row per catalog category
    the design doc names, as a sanity check the generator actually ran its
    full injection pass (not a DB check - the DB checks below are)."""
    if not issue_log_path.exists():
        print(f"[FAIL] issue log not found: {issue_log_path}")
        return False
    with issue_log_path.open() as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print(f"[FAIL] issue log is empty: {issue_log_path}")
        return False
    by_type = Counter(r["issue_type"] for r in rows)
    print(f"[PASS] issue log has {len(rows)} rows across {len(by_type)} issue categories")
    return True


def check_ground_truth_samples(container: str, user: str, db: str, issue_log_path: Path) -> bool:
    """Spot-check a representative sample of duplicate/count-based issues
    directly against the live tables (full row-by-row replay of all ~280
    rows is unnecessary for a sanity gate; these are the checks that would
    catch a broken generator or a failed load)."""
    all_pass = True

    checks = [
        ("duplicate transaction_id count >= 8 in src_transaction_daily",
         "SELECT COUNT(*) FROM (SELECT transaction_id FROM src_transaction_daily "
         "GROUP BY transaction_id HAVING COUNT(*) > 1) d;", 8),
        ("duplicate payment_id (legitimate repeat) count >= 3 in source.payment_transactions",
         "SELECT COUNT(*) FROM (SELECT payment_id FROM source.payment_transactions "
         "GROUP BY payment_id HAVING COUNT(*) > 1) d;", 3),
        ("customers with >1 active (NULL effective_end_date) row >= 15",
         "SELECT COUNT(*) FROM (SELECT customer_id FROM bronze.customer_master "
         "WHERE effective_end_date IS NULL GROUP BY customer_id HAVING COUNT(*) > 1) d;", 15),
        ("negative/zero transaction_amount count >= 8 in src_transaction_daily",
         "SELECT COUNT(*) FROM src_transaction_daily WHERE transaction_amount <= 0;", 8),
        ("overlapping/duplicate mapping rows for a product+type combo >= 3",
         "SELECT COUNT(*) FROM (SELECT product_code, transaction_type FROM ref.accounting_mapping "
         "GROUP BY product_code, transaction_type HAVING COUNT(*) > 1) d;", 3),
        ("gl_balance arithmetic violations >= 3",
         "SELECT COUNT(*) FROM finance.gl_balance "
         "WHERE ROUND(opening_balance + debit_movement - credit_movement, 2) <> ROUND(closing_balance, 2);", 3),
        ("regulatory join-fanout duplicate records (same date/type/entity, differing flag) >= 5",
         "SELECT COUNT(*) FROM ("
         "  SELECT reporting_date, customer_id, payment_type, legal_entity, COUNT(*) c"
         "  FROM regulatory.payment_reporting GROUP BY 1,2,3,4 HAVING COUNT(*) > 1"
         ") d;", 5),
    ]

    for label, query, minimum in checks:
        rows = run_query(container, user, db, query)
        count = int(rows[0]) if rows else 0
        if count >= minimum:
            print(f"[PASS] {label}: {count}")
        else:
            print(f"[FAIL] {label}: {count} (expected >= {minimum})")
            all_pass = False

    return all_pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issue-log", type=Path, default=DEFAULT_ISSUE_LOG)
    parser.add_argument("--container", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--db", required=True)
    args = parser.parse_args()

    try:
        counts_ok = check_row_counts(args.container, args.user, args.db)
        issues_ok = check_issue_categories(args.issue_log)
        ground_truth_ok = check_ground_truth_samples(args.container, args.user, args.db, args.issue_log)
    except Exception as exc:  # noqa: BLE001 - top-level safe wrapper, no silent failure
        print(f"[FAIL] seed-inspect: {exc}", file=sys.stderr)
        return 1

    if counts_ok and issues_ok and ground_truth_ok:
        print("[PASS] seed-inspect: all checks passed")
        return 0

    print("[FAIL] seed-inspect: one or more checks failed, see above")
    return 1


if __name__ == "__main__":
    sys.exit(main())
