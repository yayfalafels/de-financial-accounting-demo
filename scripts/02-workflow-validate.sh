#!/usr/bin/env bash
# 02-workflow-validate.sh
# Runs the setup script end-to-end, then inspects the live schema against
# the schema JSON via a read-only query. Safe to rerun; exits non-zero on
# any setup failure or schema mismatch.
#
# See docs/features/02-dev-env-setup-postgresql-db.md -> Design -> workflow validation runner

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ENV_FILE="$REPO_ROOT/.env"
[ -f "$ENV_FILE" ] && set -a && source "$ENV_FILE" && set +a

LOGS_DIR="${LOGS_DIR:-.dev/logs}"
TIMEZONE="${TIMEZONE:-UTC}"
TIMESTAMP_FORMAT="${TIMESTAMP_FORMAT:-%Y%m%d%H%M%S}"

VENV_DIR="${VENV_DIR:-.venv}"
SCHEMA_JSON="data/schemas/as01-source-schema.json"
TABLE_NAME="src_transaction_daily"
INSPECT_SCRIPT="scripts/utils/schema-inspect.py"

POSTGRES_CONTAINER_NAME="${POSTGRES_CONTAINER_NAME:-postgres-as01}"
POSTGRES_USER="${POSTGRES_USER:?POSTGRES_USER must be set in .env}"
POSTGRES_DB="${POSTGRES_DB:?POSTGRES_DB must be set in .env}"

FEATURE_ID="02.IS"
TASK_NAME="workflow-validate"

mkdir -p "$LOGS_DIR"
LOG_FILE="$(TZ="$TIMEZONE" date +"$TIMESTAMP_FORMAT")-${FEATURE_ID}-${TASK_NAME}.log"
LOG_PATH="$LOGS_DIR/$LOG_FILE"

log() {
    echo "$(TZ="$TIMEZONE" date +"%Y-%m-%d %H:%M:%S %Z") $1" | tee -a "$LOG_PATH"
}

main() {
    log "[INFO] === 02-workflow-validate start (feature $FEATURE_ID) ==="

    log "[INFO] running setup script (real setup path, not a shortcut)"
    if ! ./scripts/01-dev-env-setup.sh >>"$LOG_PATH" 2>&1; then
        log "[FAIL] setup script failed - see entries above"
        log "[FAIL] workflow validation failed"
        exit 1
    fi
    log "[PASS] setup script completed"

    log "[INFO] inspecting live schema for public.$TABLE_NAME"
    if "$VENV_DIR/bin/python3" "$INSPECT_SCRIPT" \
        --schema "$SCHEMA_JSON" \
        --table "$TABLE_NAME" \
        --container "$POSTGRES_CONTAINER_NAME" \
        --user "$POSTGRES_USER" \
        --db "$POSTGRES_DB" | tee -a "$LOG_PATH"
    then
        log "[PASS] workflow validation completed - schema matches expectations"
        log "[INFO] log written to $LOG_PATH"
        exit 0
    fi

    log "[FAIL] workflow validation failed - schema mismatch, see entries above"
    log "[INFO] log written to $LOG_PATH"
    exit 1
}

main
