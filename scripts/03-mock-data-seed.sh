#!/usr/bin/env bash
# 03-mock-data-seed.sh
# Seed orchestrator for feature 04 (seed mock data):
#   generate DDL (all 9 schemas) -> drop+recreate each seeded table ->
#   generate mock data -> COPY-load each table's CSV.
# Does NOT stand up infrastructure - fails fast if the postgres container
# isn't already running (that stays feature 02's job).
#
# Reload (not verify-or-create) is intentional for data: MOCK_DATA_SEED is
# fixed, so a rerun produces byte-identical data - see
# docs/features/04-seed-mock-data.md -> Design -> idempotency / rerun-safety.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ENV_FILE="$REPO_ROOT/.env"
SECRETS_FILE="$REPO_ROOT/.secrets"
[ -f "$ENV_FILE" ] && set -a && source "$ENV_FILE" && set +a
[ -f "$SECRETS_FILE" ] && set -a && source "$SECRETS_FILE" && set +a

LOGS_DIR="${LOGS_DIR:-.dev/logs}"
TIMEZONE="${TIMEZONE:-UTC}"
TIMESTAMP_FORMAT="${TIMESTAMP_FORMAT:-%Y%m%d%H%M%S}"

VENV_DIR="${VENV_DIR:-.venv}"
SCHEMA_DIR="data/schemas"
DDL_DIR="postgresql"
MOCK_DIR="data/mock"
SQL_GENERATOR="scripts/utils/sql-generators.py"
DATA_GENERATOR="scripts/utils/data-generators.py"

POSTGRES_CONTAINER_NAME="${POSTGRES_CONTAINER_NAME:-postgres-as01}"
POSTGRES_USER="${POSTGRES_USER:?POSTGRES_USER must be set in .env}"
POSTGRES_DB="${POSTGRES_DB:?POSTGRES_DB must be set in .env}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set in .secrets}"

FEATURE_ID="04.05"
TASK_NAME="mock-data-seed"

mkdir -p "$LOGS_DIR"
LOG_FILE="$(TZ="$TIMEZONE" date +"$TIMESTAMP_FORMAT")-${FEATURE_ID}-${TASK_NAME}.log"
LOG_PATH="$LOGS_DIR/$LOG_FILE"

log() {
    echo "$(TZ="$TIMEZONE" date +"%Y-%m-%d %H:%M:%S %Z") $1" | tee -a "$LOG_PATH"
}

psql_exec() {
    # $1 = sql string
    docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" -i "$POSTGRES_CONTAINER_NAME" \
        psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -c "$1"
}

psql_file() {
    # $1 = sql file
    docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" -i "$POSTGRES_CONTAINER_NAME" \
        psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 < "$1"
}

# table | qualified name | ddl file | csv file
TABLES=(
    "src_transaction_daily|src_transaction_daily|as01-source-create-table.sql|src_transaction_daily.csv"
    "bronze.transaction_daily|bronze.transaction_daily|as01-bronze-create-table.sql|bronze_transaction_daily.csv"
    "ref.accounting_mapping|ref.accounting_mapping|as02-accounting-mapping-create-table.sql|ref_accounting_mapping.csv"
    "bronze.finance_transactions|bronze.finance_transactions|as02-finance-transactions-create-table.sql|bronze_finance_transactions.csv"
    "finance.gl_balance|finance.gl_balance|as02-gl-balance-create-table.sql|finance_gl_balance.csv"
    "bronze.customer_master|bronze.customer_master|as03-customer-master-create-table.sql|bronze_customer_master.csv"
    "source.payment_transactions|source.payment_transactions|as03-payment-transactions-create-table.sql|source_payment_transactions.csv"
    "bronze.payment_transactions|bronze.payment_transactions|as03-bronze-payment-create-table.sql|bronze_payment_transactions.csv"
    "regulatory.payment_reporting|regulatory.payment_reporting|as03-payment-reporting-create-table.sql|regulatory_payment_reporting.csv"
)

step_venv() {
    log "[INFO] [04.05] checking python venv at $VENV_DIR"
    if [ ! -x "$VENV_DIR/bin/python3" ]; then
        log "[FAIL] [04.05] venv not found at $VENV_DIR - run scripts/01-dev-env-setup.sh first"
        return 1
    fi
    # sql-generators.py and data-generators.py are both stdlib-only (no
    # Faker, no DB driver - see data-generators.py's module docstring), so
    # there is nothing to pip install here; the venv just needs to exist.
    log "[PASS] [04.05] venv ready (stdlib-only, no dependencies to install)"
    return 0
}

step_container_check() {
    log "[INFO] [04.05] checking container '$POSTGRES_CONTAINER_NAME' is already running"
    if [ "$(docker ps --filter "name=^${POSTGRES_CONTAINER_NAME}$" --format '{{.Names}}')" = "$POSTGRES_CONTAINER_NAME" ]; then
        log "[PASS] [04.05] container already running"
        return 0
    fi
    log "[FAIL] [04.05] container not running - this script does not provision infrastructure, run scripts/01-dev-env-setup.sh first"
    return 1
}

step_generate_ddl() {
    log "[INFO] [04.03] generating DDL for all schemas in $SCHEMA_DIR"
    if "$VENV_DIR/bin/python3" "$SQL_GENERATOR" --schema-dir "$SCHEMA_DIR" --out-dir "$DDL_DIR" >>"$LOG_PATH" 2>&1; then
        log "[PASS] [04.03] DDL generated for all 9 tables"
        return 0
    fi
    log "[FAIL] [04.03] DDL generation failed - see $SQL_GENERATOR output above"
    return 1
}

step_recreate_tables() {
    log "[INFO] [04.05] dropping and recreating all 9 seeded tables (empty tables, safe - see idempotency design)"
    for entry in "${TABLES[@]}"; do
        IFS='|' read -r _ qualified ddl_file _ <<<"$entry"
        if ! psql_exec "DROP TABLE IF EXISTS ${qualified} CASCADE;" >>"$LOG_PATH" 2>&1; then
            log "[FAIL] [04.05] DROP TABLE failed for $qualified"
            return 1
        fi
        if ! psql_file "$DDL_DIR/$ddl_file" >>"$LOG_PATH" 2>&1; then
            log "[FAIL] [04.05] DDL apply failed for $qualified ($ddl_file)"
            return 1
        fi
        log "[PASS] [04.05] recreated $qualified"
    done
    return 0
}

step_generate_data() {
    log "[INFO] [04.04] generating mock data into $MOCK_DIR"
    if "$VENV_DIR/bin/python3" "$DATA_GENERATOR" --out-dir "$MOCK_DIR" >>"$LOG_PATH" 2>&1; then
        log "[PASS] [04.04] mock data generated"
        return 0
    fi
    log "[FAIL] [04.04] mock data generation failed - see $DATA_GENERATOR output above"
    return 1
}

step_load_data() {
    log "[INFO] [04.05] loading CSVs into $POSTGRES_DB via psql \\copy"
    for entry in "${TABLES[@]}"; do
        IFS='|' read -r _ qualified _ csv_file <<<"$entry"
        local csv_path="$MOCK_DIR/$csv_file"
        if [ ! -f "$csv_path" ]; then
            log "[FAIL] [04.05] missing generated CSV: $csv_path"
            return 1
        fi
        if docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" -i "$POSTGRES_CONTAINER_NAME" \
            psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 \
            -c "\\copy ${qualified} FROM STDIN WITH (FORMAT csv, HEADER true)" \
            < "$csv_path" >>"$LOG_PATH" 2>&1
        then
            local row_count
            row_count=$(wc -l < "$csv_path")
            log "[PASS] [04.05] loaded $qualified ($((row_count - 1)) data rows from $csv_file)"
        else
            log "[FAIL] [04.05] load failed for $qualified from $csv_file"
            return 1
        fi
    done
    return 0
}

main() {
    log "[INFO] === 03-mock-data-seed start (feature $FEATURE_ID) ==="

    step_venv || { log "[FAIL] seed aborted at venv step"; exit 1; }
    step_container_check || { log "[FAIL] seed aborted at container check"; exit 1; }
    step_generate_ddl || { log "[FAIL] seed aborted at DDL generation step"; exit 1; }
    step_recreate_tables || { log "[FAIL] seed aborted at table recreate step"; exit 1; }
    step_generate_data || { log "[FAIL] seed aborted at data generation step"; exit 1; }
    step_load_data || { log "[FAIL] seed aborted at data load step"; exit 1; }

    log "[PASS] mock data seed completed successfully"
    log "[INFO] log written to $LOG_PATH"
    exit 0
}

main
