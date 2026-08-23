#!/usr/bin/env python3
"""spark-inspect.py

Spark-side counterpart to schema-inspect.py (see
docs/features/03-dev-env-setup-spark-container.md -> Design -> workflow
validation runner). Stdlib-only, shells out via `docker exec` - no local
PySpark/JDBC dependency needed on the host:

1. Polls the spark-master UI's REST endpoint (http://localhost:<port>/json/)
   until the expected worker count has registered, or a timeout elapses.
2. Submits scripts/utils/spark-jdbc-smoketest.py inside the spark-master
   container via `docker exec ... spark-submit`, which opens a JDBC
   connection to the postgres container and reads a row count.
3. Prints one [PASS]/[FAIL] line per check plus an overall summary; exits
   non-zero on any mismatch.

Usage:
    POSTGRES_PASSWORD=*** python3 scripts/utils/spark-inspect.py \
        --master-container spark-master --ui-port 8080 --worker-count 2 \
        --table src_transaction_daily --db as01_source_db --user as01_admin
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request


def poll_worker_count(ui_port: int, expected: int, timeout: int, interval: int) -> int:
    url = f"http://localhost:{ui_port}/json/"
    deadline = time.time() + timeout
    last_seen = -1
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                status = json.loads(resp.read())
            last_seen = status.get("aliveworkers", 0)
            if last_seen >= expected:
                return last_seen
        except OSError:
            pass
        time.sleep(interval)
    return last_seen


def run_smoketest(container: str, db: str, user: str, table: str) -> tuple[bool, str]:
    password = os.environ.get("POSTGRES_PASSWORD")
    if not password:
        return False, "POSTGRES_PASSWORD not set in environment"

    cmd = [
        "docker", "exec", "-e", f"POSTGRES_PASSWORD={password}", container,
        "spark-submit", "--master", "spark://spark-master:7077",
        "/scripts/utils/spark-jdbc-smoketest.py",
        "--host", "postgres", "--db", db, "--user", user, "--table", table,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return False, "spark-submit timed out"

    for line in result.stdout.splitlines():
        if line.startswith("ROW_COUNT="):
            return True, line.strip()

    tail = (result.stdout + result.stderr).strip().splitlines()
    detail = tail[-1] if tail else "spark-submit failed, no output"
    return False, detail


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master-container", default="spark-master")
    parser.add_argument("--ui-port", type=int, default=8080)
    parser.add_argument("--worker-count", type=int, required=True)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--interval", type=int, default=2)
    parser.add_argument("--table", default="src_transaction_daily")
    parser.add_argument("--db", required=True)
    parser.add_argument("--user", required=True)
    args = parser.parse_args()

    all_pass = True

    print(f"[INFO] polling spark-master UI (port {args.ui_port}) for {args.worker_count} worker(s)")
    seen = poll_worker_count(args.ui_port, args.worker_count, args.timeout, args.interval)
    if seen >= args.worker_count:
        print(f"[PASS] worker registration: {seen}/{args.worker_count} alive workers")
    else:
        print(f"[FAIL] worker registration: {seen}/{args.worker_count} alive workers after {args.timeout}s")
        all_pass = False

    print(f"[INFO] submitting JDBC smoke test inside {args.master_container}")
    ok, detail = run_smoketest(args.master_container, args.db, args.user, args.table)
    if ok:
        print(f"[PASS] JDBC smoke test: public.{args.table} {detail}")
    else:
        print(f"[FAIL] JDBC smoke test: {detail}")
        all_pass = False

    if all_pass:
        print("[PASS] spark-inspect: cluster healthy, JDBC connectivity to postgres confirmed")
        return 0

    print("[FAIL] spark-inspect: one or more checks failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
