#!/usr/bin/env bash
# Release context gathering script
# Supports archiving development artifacts and generating release documentation

set -e
set -u
set -o pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Default values
JSON_MODE=false
VERSION_ARG=""
DRY_RUN=false

# Parse arguments
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
        v*)
            VERSION_ARG="$1"
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

# Get repository context
REPO_ROOT=$(get_repo_root)
SPECS_DIR="$REPO_ROOT/.documentation/specs"
RELEASES_DIR="$REPO_ROOT/.documentation/releases"
QUICKFIX_DIR="$REPO_ROOT/.documentation/quickfixes"
DECISIONS_DIR="$REPO_ROOT/.documentation/decisions"
CONSTITUTION_PATH="$REPO_ROOT/.documentation/memory/constitution.md"

# Detect current version from package files
CURRENT_VERSION="0.0.0"
VERSION_SOURCE="default"

if [[ -f "$REPO_ROOT/package.json" ]]; then
    CURRENT_VERSION=$(jq -r '.version // "0.0.0"' "$REPO_ROOT/package.json" 2>/dev/null || echo "0.0.0")
    VERSION_SOURCE="package.json"
elif [[ -f "$REPO_ROOT/pyproject.toml" ]]; then
    CURRENT_VERSION=$(grep -oP 'version\s*=\s*"\K[^"]+' "$REPO_ROOT/pyproject.toml" 2>/dev/null || echo "0.0.0")
    VERSION_SOURCE="pyproject.toml"
elif [[ -f "$REPO_ROOT/Cargo.toml" ]]; then
    CURRENT_VERSION=$(grep -oP '^version\s*=\s*"\K[^"]+' "$REPO_ROOT/Cargo.toml" 2>/dev/null || echo "0.0.0")
    VERSION_SOURCE="Cargo.toml"
fi

# Get last release info from git tags
LAST_TAG=""
LAST_RELEASE_DATE=""
COMMITS_SINCE=0

if has_git; then
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [[ -n "$LAST_TAG" ]]; then
        LAST_RELEASE_DATE=$(git log -1 --format=%ci "$LAST_TAG" 2>/dev/null || echo "")
        COMMITS_SINCE=$(git rev-list "$LAST_TAG"..HEAD --count 2>/dev/null || echo "0")
    else
        # No tags, count all commits
        COMMITS_SINCE=$(git rev-list HEAD --count 2>/dev/null || echo "0")
    fi
fi

# Find completed specs (those with all tasks checked in tasks.md)
COMPLETED_SPECS='[]'
PENDING_SPECS='[]'

if [[ -d "$SPECS_DIR" ]]; then
    for spec_dir in "$SPECS_DIR"/*/; do
        if [[ -d "$spec_dir" ]]; then
            spec_name=$(basename "$spec_dir")
            # Skip pr-review directory
            if [[ "$spec_name" == "pr-review" ]]; then
                continue
            fi

            tasks_file="$spec_dir/tasks.md"
            if [[ -f "$tasks_file" ]]; then
                # Count unchecked tasks (- [ ])
                unchecked=$(grep -c '^\s*- \[ \]' "$tasks_file" 2>/dev/null || echo "0")
                # Count checked tasks (- [x] or - [X])
                checked=$(grep -ci '^\s*- \[x\]' "$tasks_file" 2>/dev/null || echo "0")

                if [[ "$unchecked" -eq 0 && "$checked" -gt 0 ]]; then
                    COMPLETED_SPECS=$(echo "$COMPLETED_SPECS" | jq --arg s "$spec_name" '. + [$s]')
                elif [[ -f "$spec_dir/spec.md" ]]; then
                    PENDING_SPECS=$(echo "$PENDING_SPECS" | jq --arg s "$spec_name" '. + [$s]')
                fi
            elif [[ -f "$spec_dir/spec.md" ]]; then
                # Has spec but no tasks - consider pending
                PENDING_SPECS=$(echo "$PENDING_SPECS" | jq --arg s "$spec_name" '. + [$s]')
            fi
        fi
    done
fi

# Find quickfixes since last release
QUICKFIXES='[]'
if [[ -d "$QUICKFIX_DIR" ]]; then
    if [[ -n "$LAST_RELEASE_DATE" ]]; then
        # Find quickfixes newer than last release
        QUICKFIXES=$(find "$QUICKFIX_DIR" -name "QF-*.md" -newer "$REPO_ROOT/.git/refs/tags/$LAST_TAG" 2>/dev/null | while read -r f; do
            basename "$f" .md
        done | jq -R -s 'split("\n") | map(select(. != ""))' 2>/dev/null || echo '[]')
    else
        # No previous release, include all
        QUICKFIXES=$(ls "$QUICKFIX_DIR"/QF-*.md 2>/dev/null | while read -r f; do
            basename "$f" .md
        done | jq -R -s 'split("\n") | map(select(. != ""))' 2>/dev/null || echo '[]')
    fi
fi

# Calculate next version if not provided
NEXT_VERSION="$VERSION_ARG"
VERSION_BUMP="patch"

if [[ -z "$NEXT_VERSION" ]]; then
    # Parse current version
    IFS='.' read -r major minor patch <<< "${CURRENT_VERSION%-*}"
    major=${major:-0}
    minor=${minor:-0}
    patch=${patch:-0}

    completed_count=$(echo "$COMPLETED_SPECS" | jq 'length')
    quickfix_count=$(echo "$QUICKFIXES" | jq 'length')

    if [[ "$completed_count" -gt 0 ]]; then
        # Minor bump for new features
        VERSION_BUMP="minor"
        NEXT_VERSION="$major.$((minor + 1)).0"
    elif [[ "$quickfix_count" -gt 0 ]]; then
        # Patch bump for fixes only
        VERSION_BUMP="patch"
        NEXT_VERSION="$major.$minor.$((patch + 1))"
    else
        # Default patch bump
        VERSION_BUMP="patch"
        NEXT_VERSION="$major.$minor.$((patch + 1))"
    fi
fi

# Get git contributors since last release
CONTRIBUTORS='[]'
if has_git; then
    if [[ -n "$LAST_TAG" ]]; then
        CONTRIBUTORS=$(git log "$LAST_TAG"..HEAD --format='%aN' 2>/dev/null | sort -u | jq -R -s 'split("\n") | map(select(. != ""))' 2>/dev/null || echo '[]')
    else
        CONTRIBUTORS=$(git log --format='%aN' 2>/dev/null | sort -u | head -20 | jq -R -s 'split("\n") | map(select(. != ""))' 2>/dev/null || echo '[]')
    fi
fi

# Get timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
RELEASE_DATE=$(date +"%Y-%m-%d")

# Output JSON if requested
if [[ "$JSON_MODE" == true ]]; then
    cat <<EOF
{
  "REPO_ROOT": "$REPO_ROOT",
  "SPECS_DIR": "$SPECS_DIR",
  "RELEASES_DIR": "$RELEASES_DIR",
  "QUICKFIX_DIR": "$QUICKFIX_DIR",
  "DECISIONS_DIR": "$DECISIONS_DIR",
  "CONSTITUTION_PATH": "$CONSTITUTION_PATH",
  "CURRENT_VERSION": "$CURRENT_VERSION",
  "VERSION_SOURCE": "$VERSION_SOURCE",
  "NEXT_VERSION": "$NEXT_VERSION",
  "VERSION_BUMP": "$VERSION_BUMP",
  "COMPLETED_SPECS": $COMPLETED_SPECS,
  "PENDING_SPECS": $PENDING_SPECS,
  "QUICKFIXES": $QUICKFIXES,
  "LAST_TAG": "$LAST_TAG",
  "LAST_RELEASE_DATE": "$LAST_RELEASE_DATE",
  "COMMITS_SINCE_RELEASE": $COMMITS_SINCE,
  "CONTRIBUTORS": $CONTRIBUTORS,
  "TIMESTAMP": "$TIMESTAMP",
  "RELEASE_DATE": "$RELEASE_DATE",
  "DRY_RUN": $DRY_RUN
}
EOF
else
    # Human-readable output
    echo "Release Context"
    echo "==============="
    echo "Repository: $REPO_ROOT"
    echo "Current Version: $CURRENT_VERSION (from $VERSION_SOURCE)"
    echo "Next Version: $NEXT_VERSION ($VERSION_BUMP bump)"
    echo "Last Release: $LAST_TAG ($LAST_RELEASE_DATE)"
    echo "Commits Since: $COMMITS_SINCE"
    echo ""
    echo "Completed Specs: $(echo "$COMPLETED_SPECS" | jq 'length')"
    echo "Pending Specs: $(echo "$PENDING_SPECS" | jq 'length')"
    echo "Quickfixes: $(echo "$QUICKFIXES" | jq 'length')"
    echo "Contributors: $(echo "$CONTRIBUTORS" | jq 'length')"
    if [[ "$DRY_RUN" == true ]]; then
        echo ""
        echo "** DRY RUN MODE - No changes will be made **"
    fi
fi
