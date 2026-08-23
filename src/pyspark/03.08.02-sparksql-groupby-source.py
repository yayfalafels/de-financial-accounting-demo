"""03.08.02-sparksql-groupby-source.py

Manual validation script for feature 03 (dev env setup - spark container):
same JDBC source as 03.08.01, registered as a temp view and queried with
Spark SQL (GROUP BY), run inside spark-master via `docker exec`. See
docs/features/03-dev-env-setup-spark-container.md -> Validate -> manual validation.

Credentials are read from the environment (POSTGRES_DB/POSTGRES_USER/
POSTGRES_PASSWORD), not hardcoded - pass them through with `docker exec -e`.

Usage (from the repo root, with .env/.secrets sourced):
    docker exec -e POSTGRES_DB="$POSTGRES_DB" -e POSTGRES_USER="$POSTGRES_USER" \
        -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" spark-master \
        python3 /src/pyspark/03.08.02-sparksql-groupby-source.py
"""

import os

from pyspark.sql import SparkSession

spark = SparkSession.builder.master("spark://spark-master:7077").appName("manual-sparksql-check").getOrCreate()

df = spark.read.jdbc(
    url=f"jdbc:postgresql://postgres:5432/{os.environ['POSTGRES_DB']}",
    table="src_transaction_daily",
    properties={
        "user": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
        "driver": "org.postgresql.Driver",
    },
)
df.createOrReplaceTempView("src_transaction_daily")
spark.sql("""
    SELECT currency_code, COUNT(*) AS txn_count, ROUND(SUM(transaction_amount), 2) AS total_amount
    FROM src_transaction_daily
    GROUP BY currency_code
    ORDER BY txn_count DESC
""").show()
spark.stop()
