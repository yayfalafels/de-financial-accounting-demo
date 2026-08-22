#!/usr/bin/env python3
"""schema-inspect.py

Read-only validation: queries the live PostgreSQL schema (via
`docker exec ... psql`) for a table and diffs it against the expectations
in a schema JSON file (name, postgres type, nullability).

Prints one [PASS]/[FAIL] line per column plus an overall summary line, and
exits non-zero on any mismatch. Deliberately has no third-party DB driver
dependency - shells out to the psql client already bundled in the
postgres:15-alpine image, via `docker exec`.

Usage:
    python3 scripts/utils/schema-inspect.py \
        --schema data/schemas/as01-source-schema.json \
        --table src_transaction_daily \
        --container postgres-as01 \
        --user as01_admin \
        --db as01_source_db
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = REPO_ROOT / "data" / "schemas" / "as01-source-schema.json"

# information_schema.columns.data_type strings for each json type.
# length/precision/scale are compared separately.
EXPECTED_DATA_TYPE = {
    "string": "character varying",   # overridden to "text" below when no length
    "date": "date",
    "timestamp": "timestamp with time zone",
    "decimal": "numeric",
}


def expected_columns(schema: dict, table_name: str) -> dict:
    table = next(t for t in schema["tables"] if t["table_name"] == table_name)
    business_key = table.get("business_key", [])
    enforce_constraints = table.get("enforce_constraints", True)
    expected = {}
    for col in table["columns"]:
        json_type = col["type"]
        if json_type == "string":
            data_type = "character varying" if col.get("length") else "text"
        else:
            data_type = EXPECTED_DATA_TYPE[json_type]

        not_null = not col.get("nullable", True)
        if not enforce_constraints:
            # Relaxed raw-landing table - mirrors scripts/utils/sql-generators.py's
            # column_ddl(): only a business-key column stays NOT NULL, every other
            # NOT NULL is deliberately dropped so dirty rows are insertable. See
            # docs/features/04-seed-mock-data.md -> constraint relaxation.
            not_null = col["name"] in business_key

        expected[col["name"]] = {
            "data_type": data_type,
            "is_nullable": "NO" if not_null else "YES",
        }
    return expected


def query_live_columns(container: str, user: str, db: str, table_name: str) -> dict:
    query = (
        "SELECT column_name, data_type, is_nullable "
        "FROM information_schema.columns "
        f"WHERE table_schema='public' AND table_name='{table_name}' "
        "ORDER BY ordinal_position;"
    )
    cmd = [
        "docker", "exec", "-i", container,
        "psql", "-U", user, "-d", db, "-t", "-A", "-F", "|", "-c", query,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"psql query failed: {result.stderr.strip()}")

    live = {}
    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        name, data_type, is_nullable = line.split("|")
        live[name] = {"data_type": data_type, "is_nullable": is_nullable}
    return live


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--table", required=True)
    parser.add_argument("--container", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--db", required=True)
    args = parser.parse_args()

    try:
        schema = json.loads(args.schema.read_text())
        expected = expected_columns(schema, args.table)
        live = query_live_columns(args.container, args.user, args.db, args.table)
    except Exception as exc:  # noqa: BLE001 - top-level safe wrapper, no silent failure
        print(f"[FAIL] schema-inspect: {exc}", file=sys.stderr)
        return 1

    all_pass = True
    print(f"[INFO] validating public.{args.table} against {args.schema.name}")

    for name, exp in expected.items():
        live_col = live.get(name)
        if live_col is None:
            print(f"[FAIL] column '{name}': missing in live database")
            all_pass = False
            continue

        mismatches = []
        if live_col["data_type"] != exp["data_type"]:
            mismatches.append(
                f"type expected={exp['data_type']} actual={live_col['data_type']}"
            )
        if live_col["is_nullable"] != exp["is_nullable"]:
            mismatches.append(
                f"nullable expected={exp['is_nullable']} actual={live_col['is_nullable']}"
            )

        if mismatches:
            print(f"[FAIL] column '{name}': {'; '.join(mismatches)}")
            all_pass = False
        else:
            print(
                f"[PASS] column '{name}': type={live_col['data_type']} "
                f"nullable={live_col['is_nullable']}"
            )

    extra_columns = set(live) - set(expected)
    for name in sorted(extra_columns):
        print(f"[FAIL] column '{name}': present in live database but not in schema JSON")
        all_pass = False

    if all_pass:
        print(f"[PASS] schema validation: public.{args.table} matches {args.schema.name}")
        return 0

    print(f"[FAIL] schema validation: public.{args.table} does not match {args.schema.name}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
