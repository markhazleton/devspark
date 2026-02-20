#!/usr/bin/env bash
# Sync Spec Kit Spark with upstream github.com/github/spec-kit repository
#
# This script helps maintain the Spec Kit Spark fork by:
# - Fetching latest upstream changes
# - Categorizing commits by decision criteria
# - Auto-applying safe bug fixes (with --auto flag)
# - Generating reports for manual review
# - Updating FORK_DIVERGENCE.md with applied changes
#
# Usage:
#   sync-upstream.sh [--mode review|interactive|auto|report|update-doc] [--since <ref>] [--dry-run]

set -euo pipefail

# Color helpers
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
MAGENTA='\033[0;35m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_header() { echo -e "\n${MAGENTA}=== $1 ===${NC}"; }

# Default parameters
MODE="review"
SINCE=""
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --since)
            SINCE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: sync-upstream.sh [--mode review|auto|report|update-doc] [--since <ref>] [--dry-run]"
            exit 1
            ;;
    esac
done

# Find repository root
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [[ -z "$REPO_ROOT" ]]; then
    log_error "Must be run from within a git repository"
    exit 1
fi

DIVERGENCE_DOC="$REPO_ROOT/FORK_DIVERGENCE.md"

# Decision criteria patterns (grep -E compatible)
AUTO_PATTERNS=(
    "fix:.*dependency"
    "fix:.*version"
    "fix:.*typo"
    "fix:.*path.*error"
    "security:"
    "fix:.*cli"
    "fix:.*preserve constitution"
)

ADAPT_PATTERNS=(
    "refactor:.*template"
    "docs:.*readme"
    "refactor:.*bias"
    "fix:.*markdown"
    "feat:.*template"
    "docs:.*"
)

IGNORE_PATTERNS=(
    "chore\(deps\):.*bump"
    "chore:.*version"
    "workflow:"
    "ci:.*workflow"
    "Add.*agent:.*"
    "stale.*workflow"
)

EVALUATE_PATTERNS=(
    "extension.*system"
    "generic.*agent"
    "ai.*skills"
    "plugin"
    "modular"
)

# Get commit category based on message
get_commit_category() {
    local msg="$1"
    local lower_msg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    
    for pattern in "${AUTO_PATTERNS[@]}"; do
        if echo "$lower_msg" | grep -qiE "$pattern"; then
            echo "AUTO"
            return
        fi
    done
    
    for pattern in "${ADAPT_PATTERNS[@]}"; do
        if echo "$lower_msg" | grep -qiE "$pattern"; then
            echo "ADAPT"
            return
        fi
    done
    
    for pattern in "${IGNORE_PATTERNS[@]}"; do
        if echo "$lower_msg" | grep -qiE "$pattern"; then
            echo "IGNORE"
            return
        fi
    done
    
    for pattern in "${EVALUATE_PATTERNS[@]}"; do
        if echo "$lower_msg" | grep -qiE "$pattern"; then
            echo "EVALUATE"
            return
        fi
    done
    
    echo "REVIEW"
}

# Get last sync point from FORK_DIVERGENCE.md or merge-base
get_last_sync_point() {
    if [[ -f "$DIVERGENCE_DOC" ]]; then
        local base=$(grep -oP 'Upstream Commit.*?`\K[a-f0-9]+' "$DIVERGENCE_DOC" | head -1)
        if [[ -n "$base" ]]; then
            echo "$base"
            return
        fi
    fi
    
    # Fallback to merge base
    git merge-base main upstream/main
}

# Get upstream commits since sync point
get_upstream_commits() {
    local since="$1"
    local commits=()
    
    while IFS= read -r line; do
        if [[ $line =~ ^([a-f0-9]+)[[:space:]](.+)$ ]]; then
            local hash="${BASH_REMATCH[1]}"
            local message="${BASH_REMATCH[2]}"
            local category=$(get_commit_category "$message")
            
            commits+=("$hash|$message|$category")
        fi
    done < <(git log --oneline --no-merges "${since}..upstream/main")
    
    printf '%s\n' "${commits[@]}"
}

# Show commits grouped by category
show_commits_by_category() {
    local -a auto_commits adapt_commits ignore_commits evaluate_commits review_commits
    
    while IFS='|' read -r hash message category; do
        case $category in
            AUTO) auto_commits+=("$hash|$message") ;;
            ADAPT) adapt_commits+=("$hash|$message") ;;
            IGNORE) ignore_commits+=("$hash|$message") ;;
            EVALUATE) evaluate_commits+=("$hash|$message") ;;
            REVIEW) review_commits+=("$hash|$message") ;;
        esac
    done
    
    log_header "Upstream Commits by Category"
    
    if [[ ${#auto_commits[@]} -gt 0 ]]; then
        echo -e "\n${GREEN}🟢 AUTO (${#auto_commits[@]} commits)${NC}"
        for commit in "${auto_commits[@]}"; do
            IFS='|' read -r hash message <<< "$commit"
            echo -e "  ${GRAY}$hash - $message${NC}"
        done
    fi
    
    if [[ ${#adapt_commits[@]} -gt 0 ]]; then
        echo -e "\n${YELLOW}🟡 ADAPT (${#adapt_commits[@]} commits)${NC}"
        for commit in "${adapt_commits[@]}"; do
            IFS='|' read -r hash message <<< "$commit"
            echo -e "  ${GRAY}$hash - $message${NC}"
        done
    fi
    
    if [[ ${#ignore_commits[@]} -gt 0 ]]; then
        echo -e "\n${RED}🔴 IGNORE (${#ignore_commits[@]} commits)${NC}"
        for commit in "${ignore_commits[@]}"; do
            IFS='|' read -r hash message <<< "$commit"
            echo -e "  ${GRAY}$hash - $message${NC}"
        done
    fi
    
    if [[ ${#evaluate_commits[@]} -gt 0 ]]; then
        echo -e "\n${CYAN}🔵 EVALUATE (${#evaluate_commits[@]} commits)${NC}"
        for commit in "${evaluate_commits[@]}"; do
            IFS='|' read -r hash message <<< "$commit"
            echo -e "  ${GRAY}$hash - $message${NC}"
        done
    fi
    
    if [[ ${#review_commits[@]} -gt 0 ]]; then
        echo -e "\n⚪ REVIEW (${#review_commits[@]} commits)"
        for commit in "${review_commits[@]}"; do
            IFS='|' read -r hash message <<< "$commit"
            echo -e "  ${GRAY}$hash - $message${NC}"
        done
    fi
    
    local total=$((${#auto_commits[@]} + ${#adapt_commits[@]} + ${#ignore_commits[@]} + ${#evaluate_commits[@]} + ${#review_commits[@]}))
    echo ""
    log_info "Total: $total new commits"
    log_info "Auto-applicable: ${#auto_commits[@]}"
    log_info "Need adaptation: ${#adapt_commits[@]}"
    log_info "For evaluation: ${#evaluate_commits[@]}"
}

# Auto-apply safe cherry-picks
auto_apply_commits() {
    local -a commits=()
    local -a applied=()
    local -a failed=()
    
    # Get AUTO commits
    while IFS='|' read -r hash message category; do
        if [[ "$category" == "AUTO" ]]; then
            commits+=("$hash|$message")
        fi
    done
    
    if [[ ${#commits[@]} -eq 0 ]]; then
        log_info "No auto-applicable commits found"
        return
    fi
    
    log_header "Auto-Applying Safe Cherry-Picks"
    log_info "Found ${#commits[@]} commits to apply"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN MODE - No changes will be made"
    fi
    
    # Create checkpoint branch
    local checkpoint="sync-checkpoint-$(date +%Y%m%d-%H%M%S)"
    if [[ "$DRY_RUN" != "true" ]]; then
        git branch "$checkpoint"
        log_info "Created checkpoint branch: $checkpoint"
    fi
    
    # Apply commits
    for commit_data in "${commits[@]}"; do
        IFS='|' read -r hash message <<< "$commit_data"
        echo ""
        echo "Processing: $hash - $message"
        
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "Would cherry-pick: $hash"
            applied+=("$hash|$message")
            continue
        fi
        
        if git cherry-pick "$hash" 2>&1; then
            # Check for conflicts
            if git status --porcelain | grep -qE '^(DD|AU|UD|UA|DU|AA|UU)'; then
                log_error "Failed: $hash - has conflicts"
                git cherry-pick --abort 2>/dev/null || true
                failed+=("$hash|$message")
            else
                log_success "Applied: $hash"
                applied+=("$hash|$message")
            fi
        else
            log_error "Failed: $hash - cherry-pick error"
            git cherry-pick --abort 2>/dev/null || true
            failed+=("$hash|$message")
        fi
    done
    
    log_header "Auto-Apply Summary"
    log_success "Applied: ${#applied[@]}"
    log_error "Failed: ${#failed[@]}"
    
    if [[ ${#failed[@]} -gt 0 ]]; then
        log_warning "Failed commits need manual attention:"
        for fail in "${failed[@]}"; do
            IFS='|' read -r hash message <<< "$fail"
            echo -e "  ${YELLOW}$hash - $message${NC}"
        done
    fi
    
    if [[ "$DRY_RUN" != "true" ]] && [[ ${#applied[@]} -gt 0 ]]; then
        log_info "Checkpoint branch available if rollback needed: $checkpoint"
        log_info "To rollback: git reset --hard $checkpoint"
    fi
    
    # Update divergence doc if commits applied
    if [[ "$DRY_RUN" != "true" ]] && [[ ${#applied[@]} -gt 0 ]]; then
        local upstream_head=$(git rev-parse upstream/main)
        update_divergence_doc "$upstream_head" applied[@]
    fi
}

# Generate detailed sync report
generate_sync_report() {
    local since="$1"
    local date=$(date +%Y-%m-%d)
    local upstream_head=$(git rev-parse upstream/main)
    local -a commits=()
    
    while IFS='|' read -r hash message category; do
        commits+=("$hash|$message|$category")
    done
    
    cat << EOF
# Upstream Sync Report
**Generated**: $date  
**Upstream HEAD**: \`$upstream_head\`  
**Base**: \`$since\`  
**New Commits**: ${#commits[@]}

---

EOF
    
    # Group by category
    local -a auto_c adapt_c ignore_c evaluate_c review_c
    for commit in "${commits[@]}"; do
        IFS='|' read -r hash message category <<< "$commit"
        case $category in
            AUTO) auto_c+=("$hash|$message") ;;
            ADAPT) adapt_c+=("$hash|$message") ;;
            IGNORE) ignore_c+=("$hash|$message") ;;
            EVALUATE) evaluate_c+=("$hash|$message") ;;
            REVIEW) review_c+=("$hash|$message") ;;
        esac
    done
    
    # Output each category
    for category in AUTO ADAPT IGNORE EVALUATE REVIEW; do
        local icon count
        case $category in
            AUTO) icon="🟢 AUTO-CHERRY-PICK"; count=${#auto_c[@]}; commits_ref=("${auto_c[@]}") ;;
            ADAPT) icon="🟡 ADAPT & MERGE"; count=${#adapt_c[@]}; commits_ref=("${adapt_c[@]}") ;;
            IGNORE) icon="🔴 IGNORE"; count=${#ignore_c[@]}; commits_ref=("${ignore_c[@]}") ;;
            EVALUATE) icon="🔵 EVALUATE"; count=${#evaluate_c[@]}; commits_ref=("${evaluate_c[@]}") ;;
            REVIEW) icon="⚪ NEEDS REVIEW"; count=${#review_c[@]}; commits_ref=("${review_c[@]}") ;;
        esac
        
        [[ $count -eq 0 ]] && continue
        
        echo "## $icon ($count commits)"
        echo ""
        
        for commit in "${commits_ref[@]}"; do
            IFS='|' read -r hash message <<< "$commit"
            
            # Get commit details
            local author=$(git show -s --format='%an' "$hash")
            local commit_date=$(git show -s --format='%ai' "$hash")
            
            echo "### \`$hash\` - $message"
            echo ""
            echo "**Author**: $author  "
            echo "**Date**: $commit_date  "
            echo ""
            
            # Get files changed
            echo "**Files Changed**:"
            git diff-tree --no-commit-id --name-only -r "$hash" | while read -r file; do
                echo "- \`$file\`"
            done
            echo ""
            
            # Decision guidance
            echo "**Decision**: "
            case $category in
                AUTO) echo "✅ Safe to auto-apply" ;;
                ADAPT) echo "⚠️ Requires path adaptation (docs/ → .documentation/)" ;;
                IGNORE) echo "🚫 Skip - not applicable to Spark" ;;
                EVALUATE) echo "🤔 Needs team evaluation - major feature" ;;
                REVIEW) echo "👀 Manual categorization required" ;;
            esac
            echo ""
            echo "---"
            echo ""
        done
    done
    
    cat << EOF

## Recommendations

### Immediate Actions
1. Review AUTO commits and run: \`./sync-upstream.sh --mode auto\`
2. Manually adapt ADAPT commits (adjust paths, test commands)
3. Schedule evaluation meetings for EVALUATE commits

### Next Steps
- Update FORK_DIVERGENCE.md with absorbed changes
- Test all commands after applying changes
- Run full test suite if available
- Update documentation if behavior changes

---

*Report generated by sync-upstream.sh*
EOF
}

# Update FORK_DIVERGENCE.md
update_divergence_doc() {
    local upstream_head="$1"
    shift
    local applied=("$@")
    
    if [[ ! -f "$DIVERGENCE_DOC" ]]; then
        log_warning "FORK_DIVERGENCE.md not found, skipping update"
        return
    fi
    
    local date=$(date +%Y-%m-%d)
    
    # Update header metadata
    sed -i.bak "s/\*\*Last Sync\*\*: .*/\*\*Last Sync\*\*: $date/" "$DIVERGENCE_DOC"
    sed -i.bak "s/\*\*Current Upstream\*\*: \`[a-f0-9]*\`/\*\*Current Upstream\*\*: \`$upstream_head\`/" "$DIVERGENCE_DOC"
    
    # Add sync entry if commits applied
    if [[ ${#applied[@]} -gt 0 ]]; then
        local sync_entry="### $date: Auto-Applied Cherry-Picks\n\n"
        sync_entry+="**Upstream Commit**: \`$upstream_head\`  \n"
        sync_entry+="**Applied**: ${#applied[@]} commits\n\n"
        
        for commit in "${applied[@]}"; do
            IFS='|' read -r hash message <<< "$commit"
            sync_entry+="- \`$hash\` - $message\n"
        done
        
        # Insert after "## Sync History" header
        awk -v entry="$sync_entry" '/## Sync History/{print; print ""; print entry; next}1' \
            "$DIVERGENCE_DOC" > "$DIVERGENCE_DOC.tmp"
        mv "$DIVERGENCE_DOC.tmp" "$DIVERGENCE_DOC"
    fi
    
    rm -f "$DIVERGENCE_DOC.bak"
    log_success "Updated FORK_DIVERGENCE.md"
}

# Interactive commit review
interactive_review() {
    local -a applied_commits=()
    local -a skipped_commits=()
    local -a deferred_commits=()
    
    # Get all commits into array
    local -a all_commits=()
    while IFS='|' read -r hash message category; do
        all_commits+=("$hash|$message|$category")
    done
    
    if [[ ${#all_commits[@]} -eq 0 ]]; then
        log_info "No commits to review"
        return
    fi
    
    log_header "Interactive Commit Review"
    log_info "Review each commit and decide: Apply, Skip, or Defer"
    log_info "Total commits: ${#all_commits[@]}"
    
    # Create checkpoint branch
    local checkpoint="sync-checkpoint-$(date +%Y%m%d-%H%M%S)"
    git branch "$checkpoint"
    log_info "Created checkpoint branch: $checkpoint"
    
    local commit_num=0
    for commit_data in "${all_commits[@]}"; do
        ((commit_num++))
        IFS='|' read -r hash message category <<< "$commit_data"
        
        echo ""
        echo -e "${CYAN}$(printf '=%.0s' {1..80})${NC}"
        echo -e "${CYAN}COMMIT $commit_num OF ${#all_commits[@]}${NC}"
        echo -e "${CYAN}$(printf '=%.0s' {1..80})${NC}"
        
        # Show commit details
        echo -e "\n${YELLOW}📋 Commit: ${NC}$hash - $message"
        
        echo -en "${YELLOW}🏷️  Category: ${NC}"
        case $category in
            AUTO) echo -e "${GREEN}$category${NC}" ;;
            ADAPT) echo -e "${YELLOW}$category${NC}" ;;
            IGNORE) echo -e "${RED}$category${NC}" ;;
            EVALUATE) echo -e "${CYAN}$category${NC}" ;;
            REVIEW) echo -e "${NC}$category" ;;
        esac
        
        # Get detailed info
        local author=$(git show -s --format='%an' "$hash")
        local commit_date=$(git show -s --format='%ai' "$hash")
        local body=$(git show -s --format='%b' "$hash")
        
        echo -e "\n${YELLOW}👤 Author: ${NC}$author"
        echo -e "${YELLOW}📅 Date: ${NC}$commit_date"
        
        if [[ -n "$body" ]]; then
            echo -e "\n${YELLOW}📝 Description:${NC}"
            echo -e "${GRAY}$(echo "$body" | sed 's/^/  /')${NC}"
        fi
        
        # Show files changed
        echo -e "\n${YELLOW}📂 Files Changed:${NC}"
        git diff-tree --no-commit-id --name-status -r "$hash" | while IFS=$'\t' read -r status file; do
            case $status in
                A) echo -e "  ${GRAY}✨ $file${NC}" ;;
                M) echo -e "  ${GRAY}📝 $file${NC}" ;;
                D) echo -e "  ${GRAY}🗑️  $file${NC}" ;;
            esac
        done
        
        # Show diff stats
        echo -e "\n${YELLOW}📊 Changes:${NC}"
        git diff --stat "${hash}^..$hash" | sed 's/^/  /' | while read -r line; do
            echo -e "${GRAY}$line${NC}"
        done
        
        # Explain implications
        echo -e "\n${MAGENTA}💡 Implications for Spark:${NC}"
        case $category in
            AUTO)
                echo -e "  ${GREEN}✅ SAFE TO APPLY - This is a bug fix or security patch${NC}"
                echo -e "  ${GRAY}• Should apply cleanly with no conflicts${NC}"
                echo -e "  ${GRAY}• No Spark-specific adaptations needed${NC}"
                echo -e "  ${GRAY}• Improves stability or security${NC}"
                ;;
            ADAPT)
                echo -e "  ${YELLOW}⚠️  REQUIRES ADAPTATION - Template or documentation change${NC}"
                echo -e "  ${GRAY}• May need path adjustments (docs/ → .documentation/)${NC}"
                echo -e "  ${GRAY}• Test all commands after applying${NC}"
                echo -e "  ${GRAY}• Verify no conflicts with Spark enhancements${NC}"
                ;;
            IGNORE)
                echo -e "  ${RED}🚫 RECOMMENDED TO SKIP - Not applicable to Spark${NC}"
                echo -e "  ${GRAY}• Tied to upstream-specific infrastructure${NC}"
                echo -e "  ${GRAY}• Conflicts with Spark architecture${NC}"
                echo -e "  ${GRAY}• No value for Spark users${NC}"
                ;;
            EVALUATE)
                echo -e "  ${CYAN}🤔 NEEDS EVALUATION - Major feature${NC}"
                echo -e "  ${GRAY}• Large architectural change${NC}"
                echo -e "  ${GRAY}• Requires team discussion${NC}"
                echo -e "  ${GRAY}• Should be tested in isolation first${NC}"
                echo -e "  ${GRAY}• Consider deferring for separate RFC${NC}"
                ;;
            REVIEW)
                echo -e "  ${NC}👀 NEEDS MANUAL CATEGORIZATION"
                echo -e "  ${GRAY}• Doesn't match automatic patterns${NC}"
                echo -e "  ${GRAY}• Review changes carefully${NC}"
                ;;
        esac
        
        # Check for Spark-specific file conflicts
        local files_changed=$(git diff-tree --no-commit-id --name-only -r "$hash")
        if echo "$files_changed" | grep -qE '(\.documentation/|critic\.md|pr-review\.md|site-audit\.md|quickfix\.md|evolve-constitution\.md|release\.md)'; then
            echo -e "\n${RED}⚠️  WARNING: This commit modifies Spark-specific files!${NC}"
            echo -e "   ${YELLOW}Extra care needed - may conflict with Spark enhancements${NC}"
        fi
        
        # Prompt for action
        while true; do
            echo -e "\n${CYAN}❓ What would you like to do?${NC}"
            echo -e "  ${GREEN}[A]${NC} Apply this commit now"
            echo -e "  ${YELLOW}[S]${NC} Skip this commit"
            echo -e "  ${CYAN}[D]${NC} Defer for later (add note)"
            echo -e "  ${MAGENTA}[V]${NC} View full diff"
            echo -e "  ${RED}[Q]${NC} Quit interactive review"
            
            read -p $'\nChoice (A/S/D/V/Q): ' choice
            choice=$(echo "$choice" | tr '[:lower:]' '[:upper:]')
            
            case $choice in
                V)
                    echo -e "\n${CYAN}📄 Full Diff:${NC}"
                    git show "$hash" | less -R
                    ;;
                A)
                    echo -e "\n${CYAN}⏳ Applying commit...${NC}"
                    if git cherry-pick "$hash" 2>&1; then
                        # Check for conflicts
                        if git status --porcelain | grep -qE '^(DD|AU|UD|UA|DU|AA|UU)'; then
                            log_error "Cherry-pick has conflicts!"
                            echo -e "\n${YELLOW}❓ How to resolve?${NC}"
                            echo -e "  ${CYAN}[R]${NC} Resolve manually and continue"
                            echo -e "  ${RED}[A]${NC} Abort this cherry-pick"
                            
                            read -p $'\nChoice (R/A): ' resolve_choice
                            resolve_choice=$(echo "$resolve_choice" | tr '[:lower:]' '[:upper:]')
                            
                            if [[ "$resolve_choice" == "R" ]]; then
                                echo -e "\n${YELLOW}Resolve conflicts, then run: git cherry-pick --continue${NC}"
                                read -p "Press Enter when ready..."
                            else
                                git cherry-pick --abort 2>&1 || true
                                log_warning "Cherry-pick aborted by user"
                                
                                read -p "Mark as deferred? (Y/N): " defer_choice
                                defer_choice=$(echo "$defer_choice" | tr '[:lower:]' '[:upper:]')
                                if [[ "$defer_choice" == "Y" ]]; then
                                    read -p "Add note (optional): " defer_note
                                    deferred_commits+=("$hash|$message|Failed auto-apply: conflicts|$defer_note")
                                else
                                    skipped_commits+=("$hash|$message")
                                fi
                                break
                            fi
                        fi
                        
                        log_success "Successfully applied: $hash"
                        applied_commits+=("$hash|$message")
                        break
                    else
                        log_error "Failed to apply commit"
                        git cherry-pick --abort 2>&1 || true
                        
                        read -p "Mark as deferred? (Y/N): " defer_choice
                        defer_choice=$(echo "$defer_choice" | tr '[:lower:]' '[:upper:]')
                        if [[ "$defer_choice" == "Y" ]]; then
                            read -p "Add note (optional): " defer_note
                            deferred_commits+=("$hash|$message|Failed auto-apply|$defer_note")
                        else
                            skipped_commits+=("$hash|$message")
                        fi
                        break
                    fi
                    ;;
                S)
                    log_warning "Skipping commit"
                    skipped_commits+=("$hash|$message")
                    break
                    ;;
                D)
                    read -p $'\nReason for deferring: ' reason
                    deferred_commits+=("$hash|$message|$reason|")
                    log_info "Deferred for later review"
                    break
                    ;;
                Q)
                    log_warning "Exiting interactive review"
                    
                    log_header "Interactive Review Summary"
                    log_success "Applied: ${#applied_commits[@]}"
                    log_warning "Skipped: ${#skipped_commits[@]}"
                    log_info "Deferred: ${#deferred_commits[@]}"
                    echo -e "${GRAY}Remaining: $((${#all_commits[@]} - commit_num))${NC}"
                    
                    # Show results and cleanup
                    show_interactive_results
                    return
                    ;;
                *)
                    log_warning "Invalid choice. Please enter A, S, D, V, or Q"
                    ;;
            esac
        done
    done
    
    log_header "Interactive Review Complete"
    log_success "Applied: ${#applied_commits[@]}"
    log_warning "Skipped: ${#skipped_commits[@]}"
    log_info "Deferred: ${#deferred_commits[@]}"
    
    show_interactive_results
}

show_interactive_results() {
    # Show deferred commits
    if [[ ${#deferred_commits[@]} -gt 0 ]]; then
        echo -e "\n${YELLOW}📋 Deferred Commits:${NC}"
        for deferred in "${deferred_commits[@]}"; do
            IFS='|' read -r hash message reason note <<< "$deferred"
            echo -e "  ${GRAY}• $hash - $message${NC}"
            echo -e "    ${GRAY}Reason: $reason${NC}"
            if [[ -n "$note" ]]; then
                echo -e "    ${GRAY}Note: $note${NC}"
            fi
        done
    fi
    
    if [[ ${#applied_commits[@]} -gt 0 ]]; then
        local checkpoint="sync-checkpoint-$(date +%Y%m%d-%H%M%S | head -1)"
        log_info "Checkpoint branch available if rollback needed: $checkpoint"
        log_info "To rollback: git reset --hard $checkpoint"
        
        # Update divergence doc
        local upstream_head=$(git rev-parse upstream/main)
        update_divergence_doc "$upstream_head" "${applied_commits[@]}"
    fi
}

# Main execution
log_header "Spec Kit Spark - Upstream Sync Tool"
log_info "Mode: $MODE"

# Ensure upstream remote exists
if ! git remote | grep -q '^upstream$'; then
    log_error "Upstream remote not configured"
    log_info "Run: git remote add upstream https://github.com/github/spec-kit.git"
    exit 1
fi

# Fetch upstream
log_info "Fetching upstream changes..."
git fetch upstream 2>&1 >/dev/null
log_success "Fetch complete"

# Determine sync point
if [[ -z "$SINCE" ]]; then
    SINCE=$(get_last_sync_point)
    log_info "Using sync point: $SINCE"
else
    log_info "Using specified sync point: $SINCE"
fi

# Get new commits
commits_data=$(get_upstream_commits "$SINCE")
commit_count=$(echo "$commits_data" | wc -l)

if [[ -z "$commits_data" ]] || [[ "$commit_count" -eq 0 ]]; then
    log_success "Already up-to-date with upstream!"
    exit 0
fi

# Execute requested mode
case $MODE in
    review)
        echo "$commits_data" | show_commits_by_category
        
        echo ""
        echo -e "${YELLOW}💡 Next Steps:${NC}"
        echo "  • Interactive review: ./sync-upstream.sh --mode interactive"
        echo "  • Auto-apply safe fixes: ./sync-upstream.sh --mode auto"
        echo "  • Generate full report: ./sync-upstream.sh --mode report > report.md"
        echo "  • Cherry-pick manually: git cherry-pick <hash>"
        ;;
    
    interactive)
        echo "$commits_data" | interactive_review
        
        echo ""
        echo -e "${YELLOW}💡 Next Steps:${NC}"
        echo "  • Review deferred commits and handle manually"
        echo "  • Run tests to verify applied changes"
        echo "  • Update documentation if behavior changed"
        ;;
    
    auto)
        echo "$commits_data" | auto_apply_commits
        ;;
    
    report)
        echo "$commits_data" | generate_sync_report "$SINCE"
        ;;
    
    update-doc)
        upstream_head=$(git rev-parse upstream/main)
        update_divergence_doc "$upstream_head"
        log_success "Updated sync metadata in FORK_DIVERGENCE.md"
        ;;
    
    *)
        log_error "Invalid mode: $MODE"
        echo "Valid modes: review, auto, report, update-doc"
        exit 1
        ;;
esac

echo ""
log_success "Sync operation complete"
