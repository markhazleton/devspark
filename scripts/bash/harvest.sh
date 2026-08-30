#!/usr/bin/env bash
# DevSpark v4 harvest pre-scan: current-truth cleanup and work-package hygiene.

set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

JSON_MODE=false
SCOPE="all"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --scope=*)
            SCOPE="${1#--scope=}"
            shift
            ;;
        --scope)
            SCOPE="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

REPO_ROOT=$(get_repo_root)
WORK_DIR="$REPO_ROOT/.devspark.work"
WORK_PACKAGES_DIR="$WORK_DIR/specs"
KNOWLEDGE_DIR="$REPO_ROOT/.knowledge"
ARCHIVE_ROOT="$REPO_ROOT/.archive"
ARCHIVE_DATE=$(date +"%Y-%m-%d")
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

WORK_PACKAGES='[]'
ARCHIVE_CANDIDATES='[]'
ARCHIVE_TARGETS='[]'
BLOCKED_PACKAGES='[]'

if [[ -d "$WORK_PACKAGES_DIR" ]]; then
    while IFS= read -r -d '' package_dir; do
        package_name=$(basename "$package_dir")
        tasks_file="$package_dir/tasks.md"
        status="blocked"
        if [[ -f "$tasks_file" ]]; then
            unchecked=$(grep -c '^\s*- \[ \]' "$tasks_file" 2>/dev/null || echo "0")
            checked=$(grep -ci '^\s*- \[x\]' "$tasks_file" 2>/dev/null || echo "0")
            missing_linkage=$(grep -ciE 'code_ref:[[:space:]]*$|knowledge_ref:[[:space:]]*$|code_ref:[[:space:]]*TODO|knowledge_ref:[[:space:]]*TODO' "$tasks_file" 2>/dev/null || echo "0")
            if [[ "$unchecked" -eq 0 && "$checked" -gt 0 && "$missing_linkage" -eq 0 ]]; then
                status="archive-after-verification"
                ARCHIVE_CANDIDATES=$(jq -c --arg value "$package_name" '. + [$value]' <<<"$ARCHIVE_CANDIDATES")
                ARCHIVE_TARGETS=$(jq -c \
                    --arg id "$package_name" \
                    --arg source ".devspark.work/specs/$package_name" \
                    --arg target ".archive/$ARCHIVE_DATE/$package_name" \
                    '. + [{id:$id,source:$source,target:$target}]' <<<"$ARCHIVE_TARGETS")
            else
                BLOCKED_PACKAGES=$(jq -c --arg value "$package_name" '. + [$value]' <<<"$BLOCKED_PACKAGES")
            fi
        else
            BLOCKED_PACKAGES=$(jq -c --arg value "$package_name" '. + [$value]' <<<"$BLOCKED_PACKAGES")
        fi
        WORK_PACKAGES=$(jq -c --arg id "$package_name" --arg status "$status" '. + [{id:$id,status:$status}]' <<<"$WORK_PACKAGES")
    done < <(find "$WORK_PACKAGES_DIR" -mindepth 1 -maxdepth 1 -type d -print0 2>/dev/null)
fi

if [[ "$JSON_MODE" == true ]]; then
    cat <<EOF
{
  "repo_root": "$REPO_ROOT",
  "scope": "$SCOPE",
  "work_dir": "$WORK_DIR",
  "archive_root": "$ARCHIVE_ROOT",
  "archive_date": "$ARCHIVE_DATE",
  "knowledge_dir": "$KNOWLEDGE_DIR",
  "work_packages": $WORK_PACKAGES,
  "archive_candidates": $ARCHIVE_CANDIDATES,
  "archive_targets": $ARCHIVE_TARGETS,
  "blocked_packages": $BLOCKED_PACKAGES,
  "timestamp": "$TIMESTAMP"
}
EOF
else
    echo "DevSpark v4 Harvest Context"
    echo "==========================="
    echo "Repository: $REPO_ROOT"
    echo "Scope: $SCOPE"
    echo "Archive Root: $ARCHIVE_ROOT"
    echo "Archive Date: $ARCHIVE_DATE"
    echo "Work packages: $(jq 'length' <<<"$WORK_PACKAGES")"
    echo "Archive after verification: $(jq 'length' <<<"$ARCHIVE_CANDIDATES")"
    echo "Blocked packages: $(jq 'length' <<<"$BLOCKED_PACKAGES")"
fi
