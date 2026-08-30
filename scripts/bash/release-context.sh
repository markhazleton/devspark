#!/usr/bin/env bash
# Release context gathering script for DevSpark v4 current-truth releases.

set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

JSON_MODE=false
VERSION_ARG=""
DRY_RUN=false
RELEASE_FROM_ARG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --from)
            RELEASE_FROM_ARG="$2"
            shift 2
            ;;
        --from=*)
            RELEASE_FROM_ARG="${1#--from=}"
            shift
            ;;
        v*)
            VERSION_ARG="${1#v}"
            shift
            ;;
        [0-9]*)
            VERSION_ARG="$1"
            shift
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
CONSTITUTION_PATH="$KNOWLEDGE_DIR/governance/constitution.md"
DEVSPARK_VERSION_PATH="$REPO_ROOT/.devspark/VERSION"

CURRENT_VERSION="0.0.0"
VERSION_SOURCE="default"
if [[ -f "$DEVSPARK_VERSION_PATH" ]]; then
    CURRENT_VERSION=$(sed -nE 's/^version:[[:space:]]*([^[:space:]]+).*/\1/p' "$DEVSPARK_VERSION_PATH" 2>/dev/null | head -1 || echo "0.0.0")
    VERSION_SOURCE=".devspark/VERSION"
fi

LAST_TAG=""
LAST_RELEASE_DATE=""
COMMITS_SINCE=0
if has_git; then
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [[ -n "$LAST_TAG" ]]; then
        LAST_RELEASE_DATE=$(git log -1 --format=%ci "$LAST_TAG" 2>/dev/null || echo "")
        COMMITS_SINCE=$(git rev-list "$LAST_TAG"..HEAD --count 2>/dev/null || echo "0")
    else
        COMMITS_SINCE=$(git rev-list HEAD --count 2>/dev/null || echo "0")
    fi
fi

RELEASE_DATE=$(date +"%Y-%m-%d")
ARCHIVE_ROOT="$REPO_ROOT/.archive"
ARCHIVE_DATE="$RELEASE_DATE"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
RELEASE_FROM="$RELEASE_FROM_ARG"
if [[ -z "$RELEASE_FROM" && -n "$LAST_RELEASE_DATE" ]]; then
    RELEASE_FROM="${LAST_RELEASE_DATE:0:10}"
fi
RELEASE_TO="$RELEASE_DATE"

IN_FLIGHT_WORK_PACKAGES='[]'
VERIFY_READY_WORK_PACKAGES='[]'
BLOCKED_WORK_PACKAGES='[]'

if [[ -d "$WORK_PACKAGES_DIR" ]]; then
    while IFS= read -r -d '' package_dir; do
        package_name=$(basename "$package_dir")
        IN_FLIGHT_WORK_PACKAGES=$(jq -c --arg value "$package_name" '. + [$value]' <<<"$IN_FLIGHT_WORK_PACKAGES")

        tasks_file="$package_dir/tasks.md"
        if [[ -f "$tasks_file" ]]; then
            unchecked=$(grep -c '^\s*- \[ \]' "$tasks_file" 2>/dev/null || echo "0")
            checked=$(grep -ci '^\s*- \[x\]' "$tasks_file" 2>/dev/null || echo "0")
            missing_linkage=$(grep -ciE 'code_ref:[[:space:]]*$|knowledge_ref:[[:space:]]*$|code_ref:[[:space:]]*TODO|knowledge_ref:[[:space:]]*TODO' "$tasks_file" 2>/dev/null || echo "0")
            if [[ "$unchecked" -eq 0 && "$checked" -gt 0 && "$missing_linkage" -eq 0 ]]; then
                VERIFY_READY_WORK_PACKAGES=$(jq -c --arg value "$package_name" '. + [$value]' <<<"$VERIFY_READY_WORK_PACKAGES")
            else
                BLOCKED_WORK_PACKAGES=$(jq -c --arg value "$package_name" '. + [$value]' <<<"$BLOCKED_WORK_PACKAGES")
            fi
        else
            BLOCKED_WORK_PACKAGES=$(jq -c --arg value "$package_name" '. + [$value]' <<<"$BLOCKED_WORK_PACKAGES")
        fi
    done < <(find "$WORK_PACKAGES_DIR" -mindepth 1 -maxdepth 1 -type d -print0 2>/dev/null)
fi

NEXT_VERSION="$VERSION_ARG"
VERSION_BUMP="patch"
if [[ -z "$NEXT_VERSION" ]]; then
    IFS='.' read -r major minor patch <<< "${CURRENT_VERSION%-*}"
    major=${major:-0}
    minor=${minor:-0}
    patch=${patch:-0}
    NEXT_VERSION="$major.$minor.$((patch + 1))"
fi

CONTRIBUTORS='[]'
if has_git; then
    if [[ -n "$LAST_TAG" ]]; then
        CONTRIBUTORS=$(git log "$LAST_TAG"..HEAD --format='%aN' 2>/dev/null | sort -u | jq -R -s 'split("\n") | map(select(. != ""))' 2>/dev/null || echo '[]')
    else
        CONTRIBUTORS=$(git log --format='%aN' 2>/dev/null | sort -u | head -20 | jq -R -s 'split("\n") | map(select(. != ""))' 2>/dev/null || echo '[]')
    fi
fi

if [[ "$JSON_MODE" == true ]]; then
    cat <<EOF
{
  "REPO_ROOT": "$REPO_ROOT",
  "WORK_DIR": "$WORK_DIR",
  "WORK_PACKAGES_DIR": "$WORK_PACKAGES_DIR",
  "ARCHIVE_ROOT": "$ARCHIVE_ROOT",
  "ARCHIVE_DATE": "$ARCHIVE_DATE",
  "KNOWLEDGE_DIR": "$KNOWLEDGE_DIR",
  "CONSTITUTION_PATH": "$CONSTITUTION_PATH",
  "CURRENT_VERSION": "$CURRENT_VERSION",
  "VERSION_SOURCE": "$VERSION_SOURCE",
  "NEXT_VERSION": "$NEXT_VERSION",
  "VERSION_BUMP": "$VERSION_BUMP",
  "RELEASE_FROM": "$RELEASE_FROM",
  "RELEASE_TO": "$RELEASE_TO",
  "IN_FLIGHT_WORK_PACKAGES": $IN_FLIGHT_WORK_PACKAGES,
  "VERIFY_READY_WORK_PACKAGES": $VERIFY_READY_WORK_PACKAGES,
  "BLOCKED_WORK_PACKAGES": $BLOCKED_WORK_PACKAGES,
  "LAST_TAG": "$LAST_TAG",
  "LAST_RELEASE_DATE": "$LAST_RELEASE_DATE",
  "COMMITS_SINCE_RELEASE": $COMMITS_SINCE,
  "CONTRIBUTORS": $CONTRIBUTORS,
  "TIMESTAMP": "$TIMESTAMP",
  "RELEASE_DATE": "$RELEASE_DATE",
  "DRY_RUN": $DRY_RUN,
  "DEVSPARK_VERSION_PATH": "$DEVSPARK_VERSION_PATH",
  "INSTALLED_VERSION": "$CURRENT_VERSION"
}
EOF
else
    echo "Release Context"
    echo "==============="
    echo "Repository: $REPO_ROOT"
    echo "Current Version: $CURRENT_VERSION (from $VERSION_SOURCE)"
    echo "Next Version: $NEXT_VERSION ($VERSION_BUMP bump)"
    echo "Last Release: $LAST_TAG ($LAST_RELEASE_DATE)"
    echo "Release Window: $RELEASE_FROM -> $RELEASE_TO"
    echo "Archive Root: $ARCHIVE_ROOT"
    echo "Archive Date: $ARCHIVE_DATE"
    echo "Commits Since: $COMMITS_SINCE"
    echo "In-flight Work Packages: $(jq 'length' <<<"$IN_FLIGHT_WORK_PACKAGES")"
    echo "Verify-ready Work Packages: $(jq 'length' <<<"$VERIFY_READY_WORK_PACKAGES")"
    echo "Blocked Work Packages: $(jq 'length' <<<"$BLOCKED_WORK_PACKAGES")"
    echo "Contributors: $(jq 'length' <<<"$CONTRIBUTORS")"
    if [[ "$DRY_RUN" == true ]]; then
        echo ""
        echo "** DRY RUN MODE - No changes will be made **"
    fi
fi
