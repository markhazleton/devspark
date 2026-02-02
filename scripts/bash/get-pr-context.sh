#!/usr/bin/env bash
# Extract PR context for review
#
# This script fetches Pull Request information from GitHub and provides it
# in JSON format for the pr-review command.
#
# Usage: ./get-pr-context.sh [PR_NUMBER] [--json]
#        ./get-pr-context.sh --json      # Auto-detect PR from current branch
#        ./get-pr-context.sh 123 --json  # Specific PR number
#        ./get-pr-context.sh #123 --json # Also accepts # prefix

set -e
set -u
set -o pipefail

#==============================================================================
# Configuration
#==============================================================================

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PR_NUMBER=""
JSON_MODE=false

#==============================================================================
# Parse Arguments
#==============================================================================

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        \#*)
            # Strip # prefix if provided
            PR_NUMBER="${arg#\#}"
            ;;
        [0-9]*)
            # Numeric PR number
            PR_NUMBER="$arg"
            ;;
        *)
            # Ignore other arguments
            ;;
    esac
done

#==============================================================================
# Utility Functions
#==============================================================================

log_error() {
    if [[ "$JSON_MODE" == true ]]; then
        # Output JSON error
        cat <<EOF
{
  "error": true,
  "message": "$1",
  "details": "${2:-}"
}
EOF
    else
        echo "ERROR: $1" >&2
        [[ -n "${2:-}" ]] && echo "$2" >&2
    fi
}

#==============================================================================
# PR Number Detection
#==============================================================================

detect_pr_number() {
    # Try various methods to detect PR number
    
    # Method 1: Check environment variables
    if [[ -n "${GITHUB_PR_NUMBER:-}" ]]; then
        echo "$GITHUB_PR_NUMBER"
        return 0
    fi
    
    if [[ -n "${PR_NUMBER_ENV:-}" ]]; then
        echo "$PR_NUMBER_ENV"
        return 0
    fi
    
    # Method 2: Try GitHub CLI for current branch
    if command -v gh &>/dev/null; then
        local detected_pr
        detected_pr=$(gh pr view --json number --jq '.number' 2>/dev/null || echo "")
        if [[ -n "$detected_pr" ]]; then
            echo "$detected_pr"
            return 0
        fi
    fi
    
    # Unable to detect
    return 1
}

#==============================================================================
# Main Execution
#==============================================================================

main() {
    # Detect PR number if not provided
    if [[ -z "$PR_NUMBER" ]]; then
        if ! PR_NUMBER=$(detect_pr_number); then
            log_error "Unable to detect PR number" \
                "Please provide PR number explicitly: /speckit.pr-review #123"
            exit 1
        fi
    fi
    
    # Validate PR number is numeric
    if ! [[ "$PR_NUMBER" =~ ^[0-9]+$ ]]; then
        log_error "Invalid PR number: $PR_NUMBER" \
            "PR number must be a positive integer"
        exit 1
    fi
    
    # Check if GitHub CLI is available
    if ! command -v gh &>/dev/null; then
        log_error "GitHub CLI (gh) is required but not installed" \
            "Install from: https://cli.github.com/"
        exit 1
    fi
    
    # Check GitHub CLI authentication
    if ! gh auth status &>/dev/null; then
        log_error "GitHub CLI not authenticated" \
            "Run: gh auth login"
        exit 1
    fi
    
    # Fetch PR data
    local pr_data
    if ! pr_data=$(gh pr view "$PR_NUMBER" --json number,title,body,state,author,headRefName,baseRefName,commits,files,additions,deletions,createdAt,updatedAt 2>&1); then
        log_error "Failed to fetch PR #$PR_NUMBER" \
            "Verify PR exists and you have access. Details: $pr_data"
        exit 1
    fi
    
    # Extract commit SHA (most recent commit)
    local commit_sha
    commit_sha=$(echo "$pr_data" | jq -r '.commits[-1].oid // "unknown"')
    
    # Get PR diff (may be large, so we'll include availability flag)
    local diff_available="false"
    if gh pr diff "$PR_NUMBER" &>/dev/null; then
        diff_available="true"
    fi
    
    # Extract file list
    local files_changed
    files_changed=$(echo "$pr_data" | jq -c '[.files[].path]')
    
    # Check for constitution
    local constitution_path="$REPO_ROOT/.documentation/memory/constitution.md"
    local constitution_exists="false"
    if [[ -f "$constitution_path" ]]; then
        constitution_exists="true"
    fi
    
    # Prepare review directory
    local review_dir="$REPO_ROOT/.documentation/specs/pr-review"
    
    # Build JSON output
    if [[ "$JSON_MODE" == true ]]; then
        cat <<EOF
{
  "REPO_ROOT": "$REPO_ROOT",
  "PR_CONTEXT": {
    "enabled": true,
    "pr_number": $(echo "$pr_data" | jq '.number'),
    "pr_title": $(echo "$pr_data" | jq '.title'),
    "pr_body": $(echo "$pr_data" | jq '.body // ""'),
    "pr_state": $(echo "$pr_data" | jq '.state'),
    "pr_author": $(echo "$pr_data" | jq '.author.login'),
    "source_branch": $(echo "$pr_data" | jq '.headRefName'),
    "target_branch": $(echo "$pr_data" | jq '.baseRefName'),
    "commit_sha": "$commit_sha",
    "commit_count": $(echo "$pr_data" | jq '.commits | length'),
    "files_changed": $files_changed,
    "lines_added": $(echo "$pr_data" | jq '.additions // 0'),
    "lines_deleted": $(echo "$pr_data" | jq '.deletions // 0'),
    "created_at": $(echo "$pr_data" | jq '.createdAt'),
    "updated_at": $(echo "$pr_data" | jq '.updatedAt'),
    "diff_available": $diff_available
  },
  "CONSTITUTION_PATH": "$constitution_path",
  "CONSTITUTION_EXISTS": $constitution_exists,
  "REVIEW_DIR": "$review_dir"
}
EOF
    else
        # Human-readable output
        echo "PR Context for #$PR_NUMBER"
        echo "========================="
        echo "$pr_data" | jq -r '"Title: \(.title)\nAuthor: \(.author.login)\nState: \(.state)\nBranch: \(.headRefName) → \(.baseRefName)\nCommit: '"$commit_sha"'\nFiles: \(.files | length)\nLines: +\(.additions // 0) -\(.deletions // 0)"'
        echo ""
        echo "Constitution: $([[ "$constitution_exists" == "true" ]] && echo "✓ Found" || echo "✗ Missing")"
        echo "Review will be saved to: $review_dir/pr-$PR_NUMBER.md"
    fi
}

# Execute main function
main "$@"
