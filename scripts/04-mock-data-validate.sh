#!/usr/bin/env bash
# 04-mock-data-validate.sh
# Runs the seed orchestrator end-to-end, then validates the seeded data
# against its own ground-truth issue-log.csv via seed-inspect.py.
# Safe to rerun; exits non-zero on any seed failure or validation mismatch.
#
# Deliberately a standalone script rather than an edit to feature 02's
# already-closed scripts/02-workflow-validate.sh, to keep that closed
# feature's validated file untouched - same shape (run setup, then
# inspect), one level up the stack. See
# docs/features/04-seed-mock-data.md -> Design -> ai closed-loop validation.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ENV_FILE="$REPO_ROOT/.env"
[ -f "$ENV_FILE" ] && set -a && source "$ENV_FILE" && set +a

LOGS_DIR="${LOGS_DIR:-.dev/logs}"
TIMEZONE="${TIMEZONE:-UTC}"
TIMESTAMP_FORMAT="${TIMESTAMP_FORMAT:-%Y%m%d%H%M%S}"

VENV_DIR="${VENV_DIR:-.venv}"
ISSUE_LOG="data/mock/issue-log.csv"
INSPECT_SCRIPT="scripts/utils/seed-inspect.py"

POSTGRES_CONTAINER_NAME="${POSTGRES_CONTAINER_NAME:-postgres-as01}"
POSTGRES_USER="${POSTGRES_USER:?POSTGRES_USER must be set in .env}"
POSTGRES_DB="${POSTGRES_DB:?POSTGRES_DB must be set in .env}"

FEATURE_ID="04.IS"
TASK_NAME="mock-data-validate"

mkdir -p "$LOGS_DIR"
LOG_FILE="$(TZ="$TIMEZONE" date +"$TIMESTAMP_FORMAT")-${FEATURE_ID}-${TASK_NAME}.log"
LOG_PATH="$LOGS_DIR/$LOG_FILE"

log() {
    echo "$(TZ="$TIMEZONE" date +"%Y-%m-%d %H:%M:%S %Z") $1" | tee -a "$LOG_PATH"
}

main() {
    log "[INFO] === 04-mock-data-validate start (feature $FEATURE_ID) ==="

    log "[INFO] running seed orchestrator (real seed path, not a shortcut)"
    if ! ./scripts/03-mock-data-seed.sh >>"$LOG_PATH" 2>&1; then
        log "[FAIL] seed orchestrator failed - see entries above"
        log "[FAIL] workflow validation failed"
        exit 1
    fi
    log "[PASS] seed orchestrator completed"

    log "[INFO] inspecting seeded data against $ISSUE_LOG"
    if "$VENV_DIR/bin/python3" "$INSPECT_SCRIPT" \
        --issue-log "$ISSUE_LOG" \
        --container "$POSTGRES_CONTAINER_NAME" \
        --user "$POSTGRES_USER" \
        --db "$POSTGRES_DB" | tee -a "$LOG_PATH"
    then
        log "[PASS] workflow validation completed - seeded data matches expectations"
        log "[INFO] log written to $LOG_PATH"
        exit 0
    fi

    log "[FAIL] workflow validation failed - seed mismatch, see entries above"
    log "[INFO] log written to $LOG_PATH"
    exit 1
}

main
