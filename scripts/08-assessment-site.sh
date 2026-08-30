#!/usr/bin/env bash

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ENV_FILE="$REPO_ROOT/.env"
[ -f "$ENV_FILE" ] && set -a && source "$ENV_FILE" && set +a

LOGS_DIR="${LOGS_DIR:-.dev/logs}"
TIMEZONE="${TIMEZONE:-UTC}"
TIMESTAMP_FORMAT="${TIMESTAMP_FORMAT:-%Y%m%d%H%M%S}"
FEATURE_ID="08.05"
COMMAND="${1:-}"

if [[ $# -ne 1 || ! "$COMMAND" =~ ^(serve|build|deploy)$ ]]; then
    echo "usage: $0 {serve|build|deploy}" >&2
    exit 2
fi

mkdir -p "$LOGS_DIR"
LOG_FILE="$(TZ="$TIMEZONE" date +"$TIMESTAMP_FORMAT")-${FEATURE_ID}-assessment-site-${COMMAND}.log"
LOG_PATH="$LOGS_DIR/$LOG_FILE"

log() {
    echo "$(TZ="$TIMEZONE" date +"%Y-%m-%d %H:%M:%S %Z") $1" | tee -a "$LOG_PATH"
}

require_mkdocs() {
    if ! python -m mkdocs --version >>"$LOG_PATH" 2>&1; then
        log "[FAIL] [$FEATURE_ID] MkDocs unavailable; run: python -m pip install '.[docs]'"
        return 1
    fi
    log "[PASS] [$FEATURE_ID] MkDocs available"
}

build_site() {
    log "[INFO] [$FEATURE_ID] building MkDocs site strictly"
    if python -m mkdocs build --strict >>"$LOG_PATH" 2>&1; then
        log "[PASS] [$FEATURE_ID] site built at site/"
        return 0
    fi
    log "[FAIL] [$FEATURE_ID] strict MkDocs build failed; see $LOG_PATH"
    return 1
}

main() {
    require_mkdocs || exit 1
    case "$COMMAND" in
        serve)
            log "[INFO] [$FEATURE_ID] serving MkDocs site"
            python -m mkdocs serve >>"$LOG_PATH" 2>&1
            ;;
        build)
            build_site || exit 1
            ;;
        deploy)
            if ! git diff --quiet || ! git diff --cached --quiet; then
                log "[FAIL] [$FEATURE_ID] deploy requires a clean worktree and index"
                exit 1
            fi
            if ! git remote get-url origin >>"$LOG_PATH" 2>&1; then
                log "[FAIL] [$FEATURE_ID] origin remote is required for deployment"
                exit 1
            fi
            build_site || exit 1
            log "[INFO] [$FEATURE_ID] deploying site to gh-pages"
            if python -m mkdocs gh-deploy --force >>"$LOG_PATH" 2>&1; then
                log "[PASS] [$FEATURE_ID] gh-pages deployment completed"
            else
                log "[FAIL] [$FEATURE_ID] gh-pages deployment failed; see $LOG_PATH"
                exit 1
            fi
            ;;
    esac
    log "[INFO] [$FEATURE_ID] log written to $LOG_PATH"
}

main