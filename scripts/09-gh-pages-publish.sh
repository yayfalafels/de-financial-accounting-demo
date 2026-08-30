#!/usr/bin/env bash
# 09-gh-pages-publish.sh
# Authenticates `git push` for the gh-pages deploy using a local PAT file,
# then delegates the actual build+deploy to scripts/08-assessment-site.sh
# deploy (never duplicates that logic here). The token is supplied to git
# via a one-shot GIT_ASKPASS helper - it is never embedded in the remote
# URL, never exported as a plain env var another process could dump, and
# never written to a log file. Requires a clean git worktree and index,
# same precondition 08-assessment-site.sh deploy already enforces - this
# script does not stash or otherwise decide which local changes are safe
# to set aside, that stays a human/agent judgment call made before running it.
#
# See docs/assessments/09-as01-data-profiling-reconciliation.md -> Design ->
# publishing (09.12) - this script exists only because the GitHub Pages
# push needs authentication no prior feature's script had to supply.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ENV_FILE="$REPO_ROOT/.env"
[ -f "$ENV_FILE" ] && set -a && source "$ENV_FILE" && set +a

LOGS_DIR="${LOGS_DIR:-.dev/logs}"
TIMEZONE="${TIMEZONE:-UTC}"
TIMESTAMP_FORMAT="${TIMESTAMP_FORMAT:-%Y%m%d%H%M%S}"
GITHUB_PAT_FILE="${GITHUB_PAT_FILE:-$HOME/GITHUB_PAT}"
FEATURE_ID="09.12"

mkdir -p "$LOGS_DIR"
LOG_FILE="$(TZ="$TIMEZONE" date +"$TIMESTAMP_FORMAT")-${FEATURE_ID}-gh-pages-publish.log"
LOG_PATH="$LOGS_DIR/$LOG_FILE"

log() {
    echo "$(TZ="$TIMEZONE" date +"%Y-%m-%d %H:%M:%S %Z") $1" | tee -a "$LOG_PATH"
}

# --- safe runnable wrappers ---

check_clean_tree() {
    if ! git diff --quiet || ! git diff --cached --quiet; then
        log "[FAIL] [$FEATURE_ID] worktree/index not clean - commit or stash local changes first (this script will not decide that for you)"
        return 1
    fi
    log "[PASS] [$FEATURE_ID] worktree and index clean"
}

check_pat_file() {
    if [ ! -s "$GITHUB_PAT_FILE" ]; then
        log "[FAIL] [$FEATURE_ID] GITHUB_PAT_FILE not found or empty: $GITHUB_PAT_FILE"
        return 1
    fi
    log "[PASS] [$FEATURE_ID] PAT file present: $GITHUB_PAT_FILE"
}

ASKPASS_FILE=""
cleanup() { [ -n "$ASKPASS_FILE" ] && rm -f "$ASKPASS_FILE"; }
trap cleanup EXIT

main() {
    check_clean_tree || exit 1
    check_pat_file || exit 1

    local askpass
    askpass="$(mktemp)"
    ASKPASS_FILE="$askpass"
    cat > "$askpass" <<EOF
#!/usr/bin/env bash
case "\$1" in
    Username*) echo "x-access-token" ;;
    Password*) cat "$GITHUB_PAT_FILE" ;;
    *) echo "" ;;
esac
EOF
    chmod +x "$askpass"

    log "[INFO] [$FEATURE_ID] delegating to scripts/08-assessment-site.sh deploy"
    if GIT_ASKPASS="$askpass" GIT_TERMINAL_PROMPT=0 ./scripts/08-assessment-site.sh deploy; then
        log "[PASS] [$FEATURE_ID] gh-pages publish completed"
    else
        log "[FAIL] [$FEATURE_ID] gh-pages publish failed - see scripts/08-assessment-site.sh's own log"
        exit 1
    fi
    log "[INFO] [$FEATURE_ID] log written to $LOG_PATH"
}

main
