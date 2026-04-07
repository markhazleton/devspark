#!/usr/bin/env bash
# Archive context gathering script
# Scans .documentation/ for archive candidates (never reads .archive/)
# Outputs inventory for the AI to review and act on

set -e
set -u
set -o pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Multi-app support (T095a)
parse_app_context "$@" 2>/dev/null || true
if [[ -n "${DEVSPARK_APP_ID:-}" || "${DEVSPARK_REPO_SCOPE:-false}" == "true" ]]; then
    resolve_app_scope 2>/dev/null || true
    print_scope_summary >&2
fi

JSON_MODE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json) JSON_MODE=true; shift ;;
        *) shift ;;
    esac
done

REPO_ROOT=$(get_repo_root)
DOC_DIR="$REPO_ROOT/.documentation"
ARCHIVE_BASE="$REPO_ROOT/.archive"
TODAY=$(date +%Y-%m-%d)
ARCHIVE_DIR=".archive/$TODAY"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
GUIDE_PATH=".documentation/Guide.md"
CHANGELOG_PATH="CHANGELOG.md"

# Helper: list files in a dir as JSON array (relative to repo root), never crossing .archive
list_files_json() {
    local dir="$1"
    if [[ -d "$REPO_ROOT/$dir" ]]; then
        find "$REPO_ROOT/$dir" -type f -name "*.md" 2>/dev/null \
            | grep -v '/.archive/' \
            | sed "s|$REPO_ROOT/||" \
            | sort \
            | jq -R -s 'split("\n") | map(select(. != ""))' 2>/dev/null || echo '[]'
    else
        echo '[]'
    fi
}

# Helper: file modified date (ISO format)
file_mtime() {
    local f="$REPO_ROOT/$1"
    if [[ -f "$f" ]]; then
        local epoch
        epoch=$(stat -c %Y "$f" 2>/dev/null || stat -f %m "$f" 2>/dev/null) || { echo "unknown"; return; }
        date -u -r "$epoch" +%Y-%m-%d 2>/dev/null || date -u -d "@$epoch" +%Y-%m-%d 2>/dev/null || echo "unknown"
    else
        echo "unknown"
    fi
}

# Scan candidate categories inside .documentation/ (never .archive/)
DRAFTS_JSON=$(list_files_json ".documentation/drafts")

# Session docs: .documentation/copilot/session=*/
SESSION_JSON='[]'
if [[ -d "$DOC_DIR/copilot" ]]; then
    SESSION_JSON=$(find "$DOC_DIR/copilot" -maxdepth 2 -type f -name "*.md" 2>/dev/null \
        | grep -v '/.archive/' \
        | sed "s|$REPO_ROOT/||" \
        | sort \
        | jq -R -s 'split("\n") | map(select(. != ""))' 2>/dev/null || echo '[]')
fi

# Implementation plans and historical planning docs (top-level in .documentation/)
IMPL_PLANS_JSON=$(find "$DOC_DIR" -maxdepth 1 -name "*-implementation-plan.md" -o -name "*-plan.md" 2>/dev/null \
    | grep -v '/.archive/' \
    | sed "s|$REPO_ROOT/||" \
    | sort \
    | jq -R -s 'split("\n") | map(select(. != ""))' 2>/dev/null || echo '[]')

# Release docs
RELEASES_JSON=$(list_files_json ".documentation/releases")

# Quickfix records (candidates: completed QF records)
QUICKFIXES_JSON=$(list_files_json ".documentation/quickfixes")

# PR review records
PR_REVIEWS_JSON=$(list_files_json ".documentation/specs/pr-review")

# Current doc files (top-level .documentation/*.md, excluding already-caught items)
CURRENT_DOCS_JSON=$(find "$DOC_DIR" -maxdepth 1 -type f -name "*.md" 2>/dev/null \
    | grep -v '/.archive/' \
    | grep -v -- '-implementation-plan\.md' \
    | grep -v -- '-plan\.md' \
    | sed "s|$REPO_ROOT/||" \
    | sort \
    | jq -R -s 'split("\n") | map(select(. != ""))' 2>/dev/null || echo '[]')

# Existing archive folders
EXISTING_ARCHIVES_JSON='[]'
ARCHIVE_EXISTS="false"
if [[ -d "$ARCHIVE_BASE" ]]; then
    ARCHIVE_EXISTS="true"
    EXISTING_ARCHIVES_JSON=$(find "$ARCHIVE_BASE" -maxdepth 1 -mindepth 1 -type d 2>/dev/null \
        | sed "s|$REPO_ROOT/||" \
        | sort \
        | jq -R -s 'split("\n") | map(select(. != ""))' 2>/dev/null || echo '[]')
fi

# Check key files
GUIDE_EXISTS="false"
[[ -f "$REPO_ROOT/$GUIDE_PATH" ]] && GUIDE_EXISTS="true"

CHANGELOG_EXISTS="false"
[[ -f "$REPO_ROOT/$CHANGELOG_PATH" ]] && CHANGELOG_EXISTS="true"

if [[ "$JSON_MODE" == true ]]; then
    cat <<EOF
{
  "REPO_ROOT": "$REPO_ROOT",
  "TIMESTAMP": "$TIMESTAMP",
  "ARCHIVE_DIR": "$ARCHIVE_DIR",
  "ARCHIVE_EXISTS": $ARCHIVE_EXISTS,
  "EXISTING_ARCHIVES": $EXISTING_ARCHIVES_JSON,
  "GUIDE_PATH": "$GUIDE_PATH",
  "GUIDE_EXISTS": $GUIDE_EXISTS,
  "CHANGELOG_PATH": "$CHANGELOG_PATH",
  "CHANGELOG_EXISTS": $CHANGELOG_EXISTS,
  "CANDIDATES": {
    "drafts": $DRAFTS_JSON,
    "session_docs": $SESSION_JSON,
    "implementation_plans": $IMPL_PLANS_JSON,
    "release_docs": $RELEASES_JSON,
    "quickfix_records": $QUICKFIXES_JSON,
    "pr_reviews": $PR_REVIEWS_JSON
  },
  "CURRENT_DOCS": $CURRENT_DOCS_JSON
}
EOF
else
    echo "Archive Context"
    echo "==============="
    echo "Repository:   $REPO_ROOT"
    echo "Archive dir:  $ARCHIVE_DIR (exists: $ARCHIVE_EXISTS)"
    echo "Guide.md:     $GUIDE_PATH (exists: $GUIDE_EXISTS)"
    echo "CHANGELOG.md: $CHANGELOG_PATH (exists: $CHANGELOG_EXISTS)"
    echo ""
    echo "Candidates:"
    echo "  Drafts:              $(echo "$DRAFTS_JSON" | jq 'length' 2>/dev/null || echo 0)"
    echo "  Session docs:        $(echo "$SESSION_JSON" | jq 'length' 2>/dev/null || echo 0)"
    echo "  Implementation plans: $(echo "$IMPL_PLANS_JSON" | jq 'length' 2>/dev/null || echo 0)"
    echo "  Release docs:        $(echo "$RELEASES_JSON" | jq 'length' 2>/dev/null || echo 0)"
    echo "  Quickfix records:    $(echo "$QUICKFIXES_JSON" | jq 'length' 2>/dev/null || echo 0)"
    echo "  PR reviews:          $(echo "$PR_REVIEWS_JSON" | jq 'length' 2>/dev/null || echo 0)"
fi
