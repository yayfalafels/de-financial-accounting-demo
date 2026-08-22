#!/usr/bin/env bash
# 01-dev-env-setup.sh
# Setup orchestrator for feature 02 (dev env setup - postgresql db):
#   venv -> generate DDL -> docker compose up -> apply DDL to the container.
# Every sub-step checks current state before acting (verify-or-create),
# so reruns are safe and cheap.
#
# See docs/features/02-dev-env-setup-postgresql-db.md -> Design

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
COMPOSE_FILE="docker/docker-compose.postgres.yml"
SCHEMA_JSON="data/schemas/as01-source-schema.json"
DDL_FILE="postgresql/as01-source-create-table.sql"
GENERATOR_SCRIPT="scripts/utils/sql-generators.py"

POSTGRES_CONTAINER_NAME="${POSTGRES_CONTAINER_NAME:-postgres-as01}"
POSTGRES_USER="${POSTGRES_USER:?POSTGRES_USER must be set in .env}"
POSTGRES_DB="${POSTGRES_DB:?POSTGRES_DB must be set in .env}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set in .secrets}"

FEATURE_ID="02.06"
TASK_NAME="dev-env-setup"

mkdir -p "$LOGS_DIR"
LOG_FILE="$(TZ="$TIMEZONE" date +"$TIMESTAMP_FORMAT")-${FEATURE_ID}-${TASK_NAME}.log"
LOG_PATH="$LOGS_DIR/$LOG_FILE"

log() {
    echo "$(TZ="$TIMEZONE" date +"%Y-%m-%d %H:%M:%S %Z") $1" | tee -a "$LOG_PATH"
}

# --- safe runnable wrappers ---

step_venv() {
    log "[INFO] [02.06] checking python venv at $VENV_DIR"
    if [ ! -x "$VENV_DIR/bin/python3" ]; then
        log "[INFO] [02.06] venv not found, creating"
        if ! python3 -m venv "$VENV_DIR" >>"$LOG_PATH" 2>&1; then
            log "[FAIL] [02.06] venv creation failed"
            return 1
        fi
    fi
    log "[PASS] [02.06] venv ready: $("$VENV_DIR/bin/python3" --version)"

    local deps
    deps="$("$VENV_DIR/bin/python3" -c '
import tomllib
with open("pyproject.toml", "rb") as f:
    print(" ".join(tomllib.load(f)["project"].get("dependencies", [])))
')"
    if [ -z "$deps" ]; then
        log "[PASS] [02.06] no dependencies declared in pyproject.toml, skipping pip install"
        return 0
    fi
    # shellcheck disable=SC2086
    if ! "$VENV_DIR/bin/pip" install -q $deps >>"$LOG_PATH" 2>&1; then
        log "[FAIL] [02.06] pip install of pyproject.toml dependencies failed"
        return 1
    fi
    log "[PASS] [02.06] pyproject.toml dependencies installed: $deps"
    return 0
}

step_generate_ddl() {
    log "[INFO] [02.04] generating DDL from $SCHEMA_JSON"
    if "$VENV_DIR/bin/python3" "$GENERATOR_SCRIPT" \
        --schema "$SCHEMA_JSON" --out "$DDL_FILE" >>"$LOG_PATH" 2>&1; then
        log "[PASS] [02.04] DDL generated at $DDL_FILE"
        return 0
    fi
    log "[FAIL] [02.04] DDL generation failed - see $GENERATOR_SCRIPT output above"
    return 1
}

step_container_up() {
    log "[INFO] [02.05/02.07] checking container '$POSTGRES_CONTAINER_NAME'"
    if [ "$(docker ps --filter "name=^${POSTGRES_CONTAINER_NAME}$" --format '{{.Names}}')" = "$POSTGRES_CONTAINER_NAME" ]; then
        log "[PASS] [02.07] container already running"
    else
        log "[INFO] [02.05] bringing up postgres via docker compose"
        if ! docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d >>"$LOG_PATH" 2>&1; then
            log "[FAIL] [02.05] docker compose up failed"
            return 1
        fi
        log "[PASS] [02.05] docker compose up completed"
    fi

    log "[INFO] [02.07] waiting for container to accept connections (pg_isready)"
    local attempt=0 max_attempts=30
    while [ "$attempt" -lt "$max_attempts" ]; do
        if docker exec "$POSTGRES_CONTAINER_NAME" pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >>"$LOG_PATH" 2>&1; then
            log "[PASS] [02.07] container is accepting connections"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    log "[FAIL] [02.07] container did not become ready within ${max_attempts}s"
    return 1
}

step_apply_ddl() {
    log "[INFO] [02.07] applying $DDL_FILE to $POSTGRES_DB"
    if docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" -i "$POSTGRES_CONTAINER_NAME" \
        psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 \
        < "$DDL_FILE" >>"$LOG_PATH" 2>&1; then
        log "[PASS] [02.07] DDL applied"
        return 0
    fi
    log "[FAIL] [02.07] DDL apply failed - see psql output above"
    return 1
}

main() {
    log "[INFO] === 01-dev-env-setup start (feature $FEATURE_ID) ==="

    step_venv || { log "[FAIL] setup aborted at venv step"; exit 1; }
    step_generate_ddl || { log "[FAIL] setup aborted at DDL generation step"; exit 1; }
    step_container_up || { log "[FAIL] setup aborted at container step"; exit 1; }
    step_apply_ddl || { log "[FAIL] setup aborted at DDL apply step"; exit 1; }

    log "[PASS] dev env setup completed successfully"
    log "[INFO] log written to $LOG_PATH"
    exit 0
}

main
