#!/usr/bin/env bash
# 00-prereq-check.sh
# Verifies (or installs) Docker and Python 3.11+ in the local env.
# Verify-or-create / rerun-safe: checks current state first, installs only
# on a gap, and never fails silently.
#
# See docs/features/02-dev-env-setup-postgresql-db.md -> Design -> scripts

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ENV_FILE="$REPO_ROOT/.env"
SECRETS_FILE="$REPO_ROOT/.secrets"
[ -f "$ENV_FILE" ] && set -a && source "$ENV_FILE" && set +a

LOGS_DIR="${LOGS_DIR:-.dev/logs}"
TIMEZONE="${TIMEZONE:-UTC}"
TIMESTAMP_FORMAT="${TIMESTAMP_FORMAT:-%Y%m%d%H%M%S}"
PYTHON_MIN_VERSION="${PYTHON_MIN_VERSION:-3.11}"

FEATURE_ID="02.06"
TASK_NAME="prereq-check"

mkdir -p "$LOGS_DIR"
LOG_FILE="$(TZ="$TIMEZONE" date +"$TIMESTAMP_FORMAT")-${FEATURE_ID}-${TASK_NAME}.log"
LOG_PATH="$LOGS_DIR/$LOG_FILE"

log() {
    echo "$(TZ="$TIMEZONE" date +"%Y-%m-%d %H:%M:%S %Z") $1" | tee -a "$LOG_PATH"
}

# --- safe runnable wrappers: each always returns (exit 0 from the wrapper
# itself), signals pass/fail via return code, never aborts the script ---

check_docker() {
    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
        log "[PASS] docker present and daemon reachable: $(docker --version)"
        return 0
    fi
    log "[FAIL] docker not found or daemon not reachable"
    return 1
}

check_python() {
    if ! command -v python3 >/dev/null 2>&1; then
        log "[FAIL] python3 not found"
        return 1
    fi
    local ver
    ver="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
    if python3 - "$PYTHON_MIN_VERSION" <<'PY'
import sys
min_v = tuple(int(x) for x in sys.argv[1].split("."))
sys.exit(0 if sys.version_info[:2] >= min_v else 1)
PY
    then
        log "[PASS] python3 present: $ver (>= $PYTHON_MIN_VERSION)"
        return 0
    fi
    log "[FAIL] python3 version $ver is below required $PYTHON_MIN_VERSION"
    return 1
}

check_venv_module() {
    local py_ver
    py_ver="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
    if python3 -m venv --help >/dev/null 2>&1 && \
       python3 -c 'import venv, ensurepip' >/dev/null 2>&1; then
        log "[PASS] python3 venv module (with ensurepip) available"
        return 0
    fi
    log "[FAIL] python3 venv module missing ensurepip (need python${py_ver}-venv)"
    return 1
}

with_sudo() {
    # runs "$@" under sudo -S using SUDO_PWD from .secrets; never aborts caller
    if [ -f "$SECRETS_FILE" ]; then set -a && source "$SECRETS_FILE" && set +a; fi
    if [ -z "${SUDO_PWD:-}" ]; then
        log "[FAIL] cannot elevate: SUDO_PWD not set in .secrets"
        return 1
    fi
    if echo "$SUDO_PWD" | sudo -S "$@" >>"$LOG_PATH" 2>&1; then
        return 0
    fi
    return 1
}

install_docker() {
    log "[INFO] installing docker via apt-get"
    if with_sudo apt-get update -y && with_sudo apt-get install -y docker.io; then
        log "[PASS] docker install command completed"
        return 0
    fi
    log "[FAIL] docker install failed - see $LOG_PATH for apt-get output"
    return 1
}

install_python_venv_pkg() {
    local py_ver
    py_ver="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
    log "[INFO] installing python${py_ver}-venv via apt-get"
    if with_sudo apt-get update -y && with_sudo apt-get install -y "python${py_ver}-venv" python3-pip; then
        log "[PASS] python${py_ver}-venv install command completed"
        return 0
    fi
    log "[FAIL] python${py_ver}-venv install failed - see $LOG_PATH for apt-get output"
    return 1
}

main() {
    log "[INFO] === 00-prereq-check start (feature $FEATURE_ID) ==="
    local status=0

    if ! check_docker; then
        install_docker
        check_docker || status=1
    fi

    if ! check_python; then
        status=1
    else
        if ! check_venv_module; then
            install_python_venv_pkg
            check_venv_module || status=1
        fi
    fi

    if [ "$status" -eq 0 ]; then
        log "[PASS] all prerequisites satisfied"
    else
        log "[FAIL] prerequisite check failed - see entries above"
    fi
    log "[INFO] log written to $LOG_PATH"
    exit "$status"
}

main
