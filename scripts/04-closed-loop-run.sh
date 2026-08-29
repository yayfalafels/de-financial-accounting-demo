#!/usr/bin/env bash
# 04-closed-loop-run.sh
# Closed-loop orchestrator for feature 05: verify postgres+spark are already
# running -> apply reconciliation control-schema DDL (idempotent) ->
# reconciliation-runner.py -> feedback-report.py.
# Does NOT stand up infrastructure - fails fast if either container isn't
# already running. Batch history is append-only by design - see
# docs/features/05-ai-closed-loop-validation.md -> Design -> idempotency.

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
SQL_GENERATOR="scripts/utils/sql-generators.py"
RUNNER="scripts/utils/reconciliation-runner.py"
FEEDBACK="scripts/utils/feedback-report.py"

POSTGRES_CONTAINER_NAME="${POSTGRES_CONTAINER_NAME:-postgres-as01}"
POSTGRES_USER="${POSTGRES_USER:?POSTGRES_USER must be set in .env}"
POSTGRES_DB="${POSTGRES_DB:?POSTGRES_DB must be set in .env}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set in .secrets}"
SPARK_CONTAINER_NAME="${SPARK_CONTAINER_NAME:-spark-master}"

FEATURE_ID="05.06"
TASK_NAME="closed-loop-run"

# schema_json|ddl_out - the 3 new files only, single-file CLI mode so
# feature 04's 9 already-closed schema/DDL pairs are never touched
RC_TABLES=(
    "rc-batch-control-schema.json|rc-batch-control-create-table.sql"
    "rc-reconciliation-results-schema.json|rc-reconciliation-results-create-table.sql"
    "rc-audit-trail-schema.json|rc-audit-trail-create-table.sql"
)

mkdir -p "$LOGS_DIR"
LOG_FILE="$(TZ="$TIMEZONE" date +"$TIMESTAMP_FORMAT")-${FEATURE_ID}-${TASK_NAME}.log"
LOG_PATH="$LOGS_DIR/$LOG_FILE"

log() {
    echo "$(TZ="$TIMEZONE" date +"%Y-%m-%d %H:%M:%S %Z") $1" | tee -a "$LOG_PATH"
}

psql_file() {
    docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" -i "$POSTGRES_CONTAINER_NAME" \
        psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 < "$1"
}

step_container_check() {
    log "[INFO] [05.06] checking postgres container '$POSTGRES_CONTAINER_NAME' is already running"
    if [ "$(docker ps --filter "name=^${POSTGRES_CONTAINER_NAME}$" --format '{{.Names}}')" != "$POSTGRES_CONTAINER_NAME" ]; then
        log "[FAIL] [05.06] postgres container not running - this script does not provision infrastructure"
        return 1
    fi
    log "[PASS] [05.06] postgres container running"

    log "[INFO] [05.06] checking spark container '$SPARK_CONTAINER_NAME' is already running"
    if [ "$(docker ps --filter "name=^${SPARK_CONTAINER_NAME}$" --format '{{.Names}}')" != "$SPARK_CONTAINER_NAME" ]; then
        log "[FAIL] [05.06] spark container not running - this script does not provision infrastructure"
        return 1
    fi
    log "[PASS] [05.06] spark container running"
    return 0
}

step_apply_ddl() {
    log "[INFO] [05.03] generating + applying reconciliation control-schema DDL"
    for entry in "${RC_TABLES[@]}"; do
        IFS='|' read -r schema_file ddl_file <<<"$entry"
        if ! "$VENV_DIR/bin/python3" "$SQL_GENERATOR" \
            --schema "$SCHEMA_DIR/$schema_file" --out "$DDL_DIR/$ddl_file" >>"$LOG_PATH" 2>&1
        then
            log "[FAIL] [05.03] DDL generation failed for $schema_file"
            return 1
        fi
        if ! psql_file "$DDL_DIR/$ddl_file" >>"$LOG_PATH" 2>&1; then
            log "[FAIL] [05.03] DDL apply failed for $ddl_file"
            return 1
        fi
        log "[PASS] [05.03] $ddl_file applied (idempotent - CREATE TABLE IF NOT EXISTS)"
    done
    return 0
}

step_run_reconciliation() {
    log "[INFO] [05.04] running reconciliation-runner.py"
    if "$VENV_DIR/bin/python3" "$RUNNER" \
        --container "$POSTGRES_CONTAINER_NAME" --user "$POSTGRES_USER" --db "$POSTGRES_DB" \
        --assessment-id assessment-1 | tee -a "$LOG_PATH"
    then
        log "[PASS] [05.04] reconciliation runner completed"
        return 0
    fi
    log "[FAIL] [05.04] reconciliation runner failed or batch status FAIL"
    return 1
}

step_feedback() {
    log "[INFO] [05.05] running feedback-report.py"
    if "$VENV_DIR/bin/python3" "$FEEDBACK" \
        --container "$POSTGRES_CONTAINER_NAME" --user "$POSTGRES_USER" --db "$POSTGRES_DB" \
        --issue-log data/mock/issue-log.csv | tee -a "$LOG_PATH"
    then
        log "[PASS] [05.05] feedback report completed"
        return 0
    fi
    log "[FAIL] [05.05] feedback report failed or ground-truth mismatch"
    return 1
}

main() {
    log "[INFO] === 04-closed-loop-run start (feature $FEATURE_ID) ==="

    step_container_check || { log "[FAIL] closed loop aborted at container check"; exit 1; }
    step_apply_ddl || { log "[FAIL] closed loop aborted at DDL apply"; exit 1; }
    step_run_reconciliation || { log "[FAIL] closed loop aborted at reconciliation runner"; exit 1; }
    step_feedback || { log "[FAIL] closed loop aborted at feedback report"; exit 1; }

    log "[PASS] closed loop completed successfully"
    log "[INFO] log written to $LOG_PATH"
    exit 0
}

main
