#!/usr/bin/env bash
# 06-notebook-validate.sh
# Validates feature 07's template connectivity-check notebook end to end:
# verifies jupyter/spark/postgres are already running -> executes
# 00_template_connectivity_check.ipynb headlessly inside the jupyter
# container -> parses the notebook's own [PASS]/[FAIL] summary marker
# (never trusts nbconvert's exit code alone). Does NOT stand up
# infrastructure, and does NOT overwrite the tracked notebook - it writes
# the executed copy to a temp path for review. See
# docs/features/07-jupyter-notebook-workspace-setup.md -> Design ->
# workflow validation runner.

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

JUPYTER_CONTAINER_NAME="${JUPYTER_CONTAINER_NAME:-jupyter-notebook}"
SPARK_CONTAINER_NAME="${SPARK_CONTAINER_NAME:-spark-master}"
POSTGRES_CONTAINER_NAME="${POSTGRES_CONTAINER_NAME:-postgres-as01}"

NOTEBOOK_PATH="/notebooks/00_template_connectivity_check.ipynb"
EXECUTED_PATH="/tmp/00_template_connectivity_check.executed.ipynb"
SUMMARY_PREFIX="00-template-connectivity-check: overall status="

FEATURE_ID="07.IS"
TASK_NAME="notebook-validate"

mkdir -p "$LOGS_DIR"
LOG_FILE="$(TZ="$TIMEZONE" date +"$TIMESTAMP_FORMAT")-${FEATURE_ID}-${TASK_NAME}.log"
LOG_PATH="$LOGS_DIR/$LOG_FILE"

log() {
    echo "$(TZ="$TIMEZONE" date +"%Y-%m-%d %H:%M:%S %Z") $1" | tee -a "$LOG_PATH"
}

step_container_check() {
    for name in "$JUPYTER_CONTAINER_NAME" "$SPARK_CONTAINER_NAME" "$POSTGRES_CONTAINER_NAME"; do
        log "[INFO] [07.IS] checking container '$name' is already running"
        if [ "$(docker ps --filter "name=^${name}$" --format '{{.Names}}')" != "$name" ]; then
            log "[FAIL] [07.IS] container '$name' not running - this script does not provision infrastructure"
            return 1
        fi
        log "[PASS] [07.IS] container '$name' running"
    done
    return 0
}

step_execute_notebook() {
    log "[INFO] [07.IS] executing $NOTEBOOK_PATH headlessly inside $JUPYTER_CONTAINER_NAME"
    if ! docker exec "$JUPYTER_CONTAINER_NAME" \
        jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=120 \
        --output "$EXECUTED_PATH" "$NOTEBOOK_PATH" >>"$LOG_PATH" 2>&1
    then
        log "[FAIL] [07.IS] nbconvert execution failed - see $LOG_PATH for the traceback"
        return 1
    fi
    log "[PASS] [07.IS] nbconvert execution completed - no cell raised"
    return 0
}

step_parse_summary() {
    log "[INFO] [07.IS] parsing executed notebook for the [PASS]/[FAIL] summary marker"
    local marker
    marker="$(docker exec "$JUPYTER_CONTAINER_NAME" python3 -c "
import json
nb = json.load(open('$EXECUTED_PATH'))
text = ''.join(
    ''.join(o.get('text', [])) if isinstance(o.get('text'), list) else o.get('text', '')
    for cell in nb['cells'] for o in cell.get('outputs', [])
)
lines = [l for l in text.splitlines() if '$SUMMARY_PREFIX' in l]
print(lines[-1] if lines else 'NOT_FOUND')
")"
    log "[INFO] [07.IS] summary line: $marker"

    if [[ "$marker" == "[PASS] ${SUMMARY_PREFIX}"* ]]; then
        log "[PASS] [07.IS] notebook summary marker agrees"
        return 0
    fi
    log "[FAIL] [07.IS] notebook summary marker missing or FAIL"
    return 1
}

main() {
    log "[INFO] === 06-notebook-validate start (feature $FEATURE_ID) ==="

    step_container_check || { log "[FAIL] notebook validate aborted at container check"; exit 1; }
    step_execute_notebook || { log "[FAIL] notebook validate aborted at notebook execution"; exit 1; }
    step_parse_summary || { log "[FAIL] notebook validate aborted at summary parse"; exit 1; }

    log "[PASS] notebook validate completed successfully"
    log "[INFO] executed copy: $EXECUTED_PATH (inside $JUPYTER_CONTAINER_NAME) - copy over $NOTEBOOK_PATH and commit if this run's output should become the tracked version"
    log "[INFO] log written to $LOG_PATH"
    exit 0
}

main
