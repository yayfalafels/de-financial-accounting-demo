#!/usr/bin/env bash

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ENV_FILE="$REPO_ROOT/.env"
[ -f "$ENV_FILE" ] && set -a && source "$ENV_FILE" && set +a

LOGS_DIR="${LOGS_DIR:-.dev/logs}"
TIMEZONE="${TIMEZONE:-UTC}"
TIMESTAMP_FORMAT="${TIMESTAMP_FORMAT:-%Y%m%d%H%M%S}"
FEATURE_ID="08.03"
TASK_NAME="deliverables-scaffold"
MODE="write"
FAILURES=0

if [[ $# -gt 1 || ( $# -eq 1 && "$1" != "--check" ) ]]; then
    echo "usage: $0 [--check]" >&2
    exit 2
fi
[[ $# -eq 1 ]] && MODE="check"

mkdir -p "$LOGS_DIR"
LOG_FILE="$(TZ="$TIMEZONE" date +"$TIMESTAMP_FORMAT")-${FEATURE_ID}-${TASK_NAME}.log"
LOG_PATH="$LOGS_DIR/$LOG_FILE"

log() {
    echo "$(TZ="$TIMEZONE" date +"%Y-%m-%d %H:%M:%S %Z") $1" | tee -a "$LOG_PATH"
}

deliverables=(
    "assessment-1|profiling-summary|Data Profiling Summary"
    "assessment-1|reconciliation-results|Reconciliation Results"
    "assessment-1|exception-dataset|Exception Dataset"
    "assessment-1|root-cause-analysis|Root-Cause Analysis"
    "assessment-1|dq-recommendations|DQ-Control Recommendations"
    "assessment-2|reconciliation-results|Reconciliation Results"
    "assessment-2|exception-dataset|Exception Dataset"
    "assessment-2|root-cause-analysis|Root-Cause Analysis"
    "assessment-2|mapping-validation|Accounting Mapping Validation"
    "assessment-2|framework-design|Reconciliation Framework Design"
    "assessment-2|business-summary|Business-Facing Summary"
    "assessment-3|profiling-summary|Data Profiling Summary"
    "assessment-3|reconciliation-results|Reconciliation Results"
    "assessment-3|exception-dataset|Exception Dataset"
    "assessment-3|root-cause-analysis|Root-Cause Analysis"
    "assessment-3|lineage-doc|Data-Lineage Document"
    "assessment-3|performance-notes|Performance-Optimization Notes"
    "assessment-3|presentation-summary|Five-Minute Presentation Summary"
)

assessment_number() {
    echo "${1#assessment-}"
}

notebook_path() {
    case "$1" in
        assessment-1) echo "notebooks/assessment1_profiling.ipynb" ;;
        assessment-2) echo "notebooks/assessment2_gl_reconciliation.ipynb" ;;
        assessment-3) echo "notebooks/assessment3_regulatory_dashboard.ipynb" ;;
    esac
}

create_stub() {
    local assessment_id="$1" slug="$2" title="$3" path="$4"
    local assessment_no
    assessment_no="$(assessment_number "$assessment_id")"
    cat >"$path" <<EOF
# Assessment ${assessment_no} - ${title}

## Sources

- notebook: \`$(notebook_path "$assessment_id")\`
- batch: \`reconciliation.rc_batch_control.batch_id = <n>\`
EOF
}

process_deliverables() {
    local assessment_id="$1" entry parsed_assessment slug title path
    for entry in "${deliverables[@]}"; do
        IFS='|' read -r parsed_assessment slug title <<<"$entry"
        [[ "$parsed_assessment" == "$assessment_id" ]] || continue
        path="results/$assessment_id/$assessment_id-$slug.md"
        if [[ -f "$path" ]]; then
            log "[PASS] [$FEATURE_ID] preserved $path"
        elif [[ "$MODE" == "write" ]]; then
            mkdir -p "$(dirname "$path")"
            create_stub "$assessment_id" "$slug" "$title" "$path"
            log "[PASS] [$FEATURE_ID] created $path"
        else
            log "[FAIL] [$FEATURE_ID] missing $path"
            FAILURES=1
        fi
    done
}

write_manifest() {
    local assessment_id="$1" readme="results/$assessment_id/README.md"
    local temporary entry parsed_assessment slug title path status row=1
    # status lives only in this manifest (draft|open|final), never on the
    # deliverable page itself - carry forward whatever is already recorded
    # for a path, so a hand-set "open"/"final" survives a rerun; brand new
    # rows default to "draft".
    declare -A existing_status
    if [[ -f "$readme" ]]; then
        while IFS= read -r line; do
            if [[ "$line" =~ \]\(([^\)]+\.md)\)[[:space:]]*\|[[:space:]]*([a-zA-Z]+)[[:space:]]*\|[[:space:]]*$ ]]; then
                existing_status["${BASH_REMATCH[1]}"]="${BASH_REMATCH[2]}"
            fi
        done <"$readme"
    fi
    temporary="$(mktemp)"
    {
        echo "# Assessment $(assessment_number "$assessment_id") Deliverables"
        echo
        echo "Current assessment deliverables and their submission status."
        echo
        echo "| id | deliverable | status |"
        echo "| -- | ----------- | ------ |"
        for entry in "${deliverables[@]}"; do
            IFS='|' read -r parsed_assessment slug title <<<"$entry"
            [[ "$parsed_assessment" == "$assessment_id" ]] || continue
            path="$assessment_id-$slug.md"
            status="${existing_status[$path]:-draft}"
            printf '| %02d | [%s](%s) | %s |\n' "$row" "$title" "$path" "$status"
            row=$((row + 1))
        done
        echo "| 90 | notebook [07] | reference |"
        echo "| 91 | dashboard [06] | reference |"
    } >"$temporary"
    if [[ "$MODE" == "check" ]]; then
        if [[ -f "$readme" ]] && cmp -s "$temporary" "$readme"; then
            log "[PASS] [$FEATURE_ID] current manifest $readme"
        else
            log "[FAIL] [$FEATURE_ID] missing or stale manifest $readme"
            FAILURES=1
        fi
    elif [[ -f "$readme" ]] && cmp -s "$temporary" "$readme"; then
        log "[PASS] [$FEATURE_ID] preserved current manifest $readme"
    else
        mv "$temporary" "$readme"
        temporary=""
        log "[PASS] [$FEATURE_ID] generated manifest $readme"
    fi
    [[ -n "$temporary" ]] && rm -f "$temporary"
}

process_index() {
    local index="results/index.md"
    if [[ -f "$index" ]]; then
        log "[PASS] [$FEATURE_ID] preserved $index"
    elif [[ "$MODE" == "write" ]]; then
        cat >"$index" <<'EOF'
# Financial Accounting Assessments

Current assessment deliverables and their submission status.

- [Assessment 1](assessment-1/README.md)
- [Assessment 2](assessment-2/README.md)
- [Assessment 3](assessment-3/README.md)
EOF
        log "[PASS] [$FEATURE_ID] created $index"
    else
        log "[FAIL] [$FEATURE_ID] missing $index"
        FAILURES=1
    fi
}

main() {
    local assessment_id
    log "[INFO] [$FEATURE_ID] deliverable scaffold mode=$MODE"
    process_index
    for assessment_id in assessment-1 assessment-2 assessment-3; do
        process_deliverables "$assessment_id"
        write_manifest "$assessment_id"
    done
    if [[ "$FAILURES" -eq 0 ]]; then
        log "[PASS] [$FEATURE_ID] deliverable scaffold complete"
        log "[INFO] [$FEATURE_ID] log written to $LOG_PATH"
        exit 0
    fi
    log "[FAIL] [$FEATURE_ID] deliverable scaffold incomplete"
    log "[INFO] [$FEATURE_ID] log written to $LOG_PATH"
    exit 1
}

main