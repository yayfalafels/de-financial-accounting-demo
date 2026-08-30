#!/usr/bin/env bash
# 05-powerbi-sync.sh
# Orchestrates the .pbip template <-> Windows working-copy sync (feature 06).
# Usage: scripts/05-powerbi-sync.sh {scaffold|push|pull|verify}
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
set -a && source .env && set +a

SUBCOMMAND="${1:-}"
case "$SUBCOMMAND" in
  scaffold|push|pull) TASK_ID=06.04 ;;
  verify)             TASK_ID=06.05 ;;
  *) echo "usage: $0 {scaffold|push|pull|verify}" >&2; exit 2 ;;
esac

: "${POWERBI_WINDOWS_DIR:?POWERBI_WINDOWS_DIR not set in .env - see docs/features/06-powerbi-dashboard-setup.md#environment--secrets}"
: "${POWERBI_REPO_DIR:=powerbi/reconciliation-dashboard-template}"

if [[ "$SUBCOMMAND" != "scaffold" && "$SUBCOMMAND" != "push" && ! -d "$POWERBI_WINDOWS_DIR" ]]; then
  echo "[FAIL] POWERBI_WINDOWS_DIR does not exist: $POWERBI_WINDOWS_DIR" >&2
  exit 1
fi

mkdir -p "$LOGS_DIR"
TS="$(date +"$TIMESTAMP_FORMAT")"
LOG_FILE="$LOGS_DIR/${TS}-${TASK_ID}-powerbi-sync-${SUBCOMMAND}.log"

python3 scripts/utils/powerbi-sync.py "$SUBCOMMAND" \
  --repo-dir "$POWERBI_REPO_DIR" \
  --windows-dir "$POWERBI_WINDOWS_DIR" \
  | tee "$LOG_FILE"

exit "${PIPESTATUS[0]}"
