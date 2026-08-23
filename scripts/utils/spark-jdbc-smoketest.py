#!/usr/bin/env python3
"""spark-jdbc-smoketest.py

PySpark smoke test for feature 03 (dev env setup - spark container): opens
a JDBC connection to the postgres service and reads a row count from
`src_transaction_daily`, proving cross-container connectivity end-to-end.

Runs *inside* the spark-master container via `spark-submit`, invoked by
scripts/utils/spark-inspect.py (which shells out via `docker exec`) - not
meant to be run directly on the host. The Postgres password is read from
the POSTGRES_PASSWORD environment variable, not a CLI arg, so it never
shows up in `ps`/`docker exec` command listings.

Prints one line `ROW_COUNT=<n>` on success so the caller can parse it.

Usage (inside the spark-master container):
    spark-submit /scripts/utils/spark-jdbc-smoketest.py \
        --host postgres --port 5432 --db as01_source_db \
        --user as01_admin --table src_transaction_daily
"""

import argparse
import os
import sys

from pyspark.sql import SparkSession


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="postgres")
    parser.add_argument("--port", default="5432")
    parser.add_argument("--db", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--table", default="src_transaction_daily")
    args = parser.parse_args()

    password = os.environ.get("POSTGRES_PASSWORD")
    if not password:
        print("[FAIL] spark-jdbc-smoketest: POSTGRES_PASSWORD not set in environment", file=sys.stderr)
        return 1

    spark = SparkSession.builder.appName("spark-jdbc-smoketest").getOrCreate()

    try:
        df = spark.read.jdbc(
            url=f"jdbc:postgresql://{args.host}:{args.port}/{args.db}",
            table=args.table,
            properties={
                "user": args.user,
                "password": password,
                "driver": "org.postgresql.Driver",
            },
        )
        count = df.count()
    except Exception as exc:  # noqa: BLE001 - top-level safe wrapper, no silent failure
        print(f"[FAIL] spark-jdbc-smoketest: {exc}", file=sys.stderr)
        spark.stop()
        return 1

    print(f"ROW_COUNT={count}")
    spark.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
