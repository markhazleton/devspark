#!/usr/bin/env bash
# Detect DevSpark lifecycle state and recommend one next action. Read-only.
set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"
source "$SCRIPT_DIR/platform.sh"

AUTO=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --auto) AUTO=true ;;
        --json|-Json) ;;
    esac
    shift
done

if ! command -v jq >/dev/null 2>&1 || ! command -v rg >/dev/null 2>&1; then
    echo "next-context requires jq and ripgrep (rg)." >&2
    exit 2
fi

REPO_ROOT="$(get_repo_root)"
cd "$REPO_ROOT"

HAS_GIT=false
BRANCH="none"
GIT_DIRTY=false
UPSTREAM=""
AHEAD=0
BEHIND=0
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    HAS_GIT=true
    BRANCH="$(git branch --show-current 2>/dev/null || true)"
    [[ -n "$BRANCH" ]] || BRANCH="detached"
    [[ -z "$(git status --porcelain --untracked-files=normal 2>/dev/null)" ]] || GIT_DIRTY=true
    UPSTREAM="$(git rev-parse --abbrev-ref '@{upstream}' 2>/dev/null || true)"
    if [[ -n "$UPSTREAM" ]]; then
        COUNTS="$(git rev-list --left-right --count "$UPSTREAM...HEAD" 2>/dev/null || echo '0 0')"
        BEHIND="$(printf '%s' "$COUNTS" | awk '{print $1}')"
        AHEAD="$(printf '%s' "$COUNTS" | awk '{print $2}')"
    fi
fi

CONSTITUTION_EXISTS=false
[[ -f .knowledge/governance/constitution.md ]] && CONSTITUTION_EXISTS=true

FEATURE_DIR=""
SPEC_PATH=""
PLAN_PATH=""
TASKS_PATH=""
WORK_KIND="none"

if [[ "$BRANCH" != "none" && "$BRANCH" != "detached" && -d ".devspark.work/specs/$BRANCH" ]]; then
    FEATURE_DIR=".devspark.work/specs/$BRANCH"
    WORK_KIND="spec"
    SPEC_PATH="$FEATURE_DIR/spec.md"
    PLAN_PATH="$FEATURE_DIR/plan.md"
    TASKS_PATH="$FEATURE_DIR/tasks.md"
elif [[ "$BRANCH" != "none" && "$BRANCH" != "detached" && -d .devspark.work/quickfixes ]]; then
    QUICKFIX_PATH="$(rg -l -F -- "- **Branch**: $BRANCH" .devspark.work/quickfixes --glob '*.md' 2>/dev/null | LC_ALL=C sort | tail -1 || true)"
    if [[ -n "$QUICKFIX_PATH" ]]; then
        FEATURE_DIR="$(dirname "$QUICKFIX_PATH")"
        WORK_KIND="quickfix"
        SPEC_PATH="$QUICKFIX_PATH"
        TASKS_PATH="$QUICKFIX_PATH"
    fi
fi

HAS_SPEC=false
HAS_PLAN=false
HAS_TASKS=false
[[ -n "$SPEC_PATH" && -f "$SPEC_PATH" ]] && HAS_SPEC=true
[[ -n "$PLAN_PATH" && -f "$PLAN_PATH" ]] && HAS_PLAN=true
[[ -n "$TASKS_PATH" && -f "$TASKS_PATH" ]] && HAS_TASKS=true

SPEC_STATUS="missing"
REQUIRED_GATES=""
if $HAS_SPEC; then
    SPEC_STATUS="$(sed -nE 's/^\*\*Status\*\*:[[:space:]]*([^<]+).*/\1/p' "$SPEC_PATH" | head -1 | sed 's/[[:space:]]*$//' || true)"
    [[ -n "$SPEC_STATUS" ]] || SPEC_STATUS="unknown"
    REQUIRED_GATES="$(sed -nE 's/^required_gates:[[:space:]]*(.*)/\1/p' "$SPEC_PATH" | head -1 | tr '[:upper:]' '[:lower:]' || true)"
fi

TASKS_TOTAL=0
TASKS_COMPLETE=0
TASKS_INCOMPLETE=0
if $HAS_TASKS; then
    TASKS_COMPLETE="$(rg -c '^[[:space:]]*-[[:space:]]+\[[xX]\]' "$TASKS_PATH" 2>/dev/null || true)"
    TASKS_INCOMPLETE="$(rg -c '^[[:space:]]*-[[:space:]]+\[ \]' "$TASKS_PATH" 2>/dev/null || true)"
    TASKS_COMPLETE="${TASKS_COMPLETE:-0}"
    TASKS_INCOMPLETE="${TASKS_INCOMPLETE:-0}"
    TASKS_TOTAL=$((TASKS_COMPLETE + TASKS_INCOMPLETE))
fi

gate_state() {
    local gate_file="$1"
    if [[ ! -f "$gate_file" ]]; then printf 'missing'; return; fi
    local status blocking
    status="$(sed -nE 's/^status:[[:space:]]*([^[:space:]]+).*/\1/p' "$gate_file" | head -1 | tr '[:upper:]' '[:lower:]' || true)"
    blocking="$(sed -nE 's/^blocking:[[:space:]]*([^[:space:]]+).*/\1/p' "$gate_file" | head -1 | tr '[:upper:]' '[:lower:]' || true)"
    if [[ "$blocking" == "true" || "$status" == "fail" ]]; then printf 'fail'
    elif [[ "$status" == "pass" || "$status" == "warn" ]]; then printf '%s' "$status"
    else printf 'fail'
    fi
}

CHECKLIST_STATE="not-required"
ANALYZE_STATE="not-required"
CRITIC_STATE="not-required"
if [[ "$WORK_KIND" == "spec" && -n "$FEATURE_DIR" ]]; then
    if [[ "$REQUIRED_GATES" == *checklist* ]]; then CHECKLIST_STATE="$(gate_state "$FEATURE_DIR/gates/checklist.md")"; fi
    if [[ "$REQUIRED_GATES" == *analyze* || -z "$REQUIRED_GATES" ]]; then ANALYZE_STATE="$(gate_state "$FEATURE_DIR/gates/analyze.md")"; fi
    if [[ "$REQUIRED_GATES" == *critic* || -z "$REQUIRED_GATES" ]]; then CRITIC_STATE="$(gate_state "$FEATURE_DIR/gates/critic.md")"; fi
fi

PR_NUMBER=""
PR_STATE="none"
PR_URL=""
PR_BASE=""
PR_REVIEW_DECISION=""
PR_MERGE_STATE=""
PLATFORM_CLI_AVAILABLE=false
PLATFORM_AUTHENTICATED=false
if command -v "$DEVSPARK_PR_CLI" >/dev/null 2>&1; then
    PLATFORM_CLI_AVAILABLE=true
    if check_platform_auth; then
        PLATFORM_AUTHENTICATED=true
        case "$DEVSPARK_PLATFORM_NAME" in
            github)
                PR_JSON="$(gh pr view --json number,state,url,baseRefName,reviewDecision,mergeStateStatus 2>/dev/null || true)"
                if [[ -n "$PR_JSON" ]] && printf '%s' "$PR_JSON" | jq -e . >/dev/null 2>&1; then
                    PR_NUMBER="$(printf '%s' "$PR_JSON" | jq -r '.number // empty')"
                    PR_STATE="$(printf '%s' "$PR_JSON" | jq -r '.state // "none"' | tr '[:upper:]' '[:lower:]')"
                    PR_URL="$(printf '%s' "$PR_JSON" | jq -r '.url // empty')"
                    PR_BASE="$(printf '%s' "$PR_JSON" | jq -r '.baseRefName // empty')"
                    PR_REVIEW_DECISION="$(printf '%s' "$PR_JSON" | jq -r '.reviewDecision // empty' | tr '[:lower:]' '[:upper:]')"
                    PR_MERGE_STATE="$(printf '%s' "$PR_JSON" | jq -r '.mergeStateStatus // empty' | tr '[:lower:]' '[:upper:]')"
                fi
                ;;
            azdo)
                PR_JSON="$(az repos pr list --source-branch "$BRANCH" --status all --top 1 --output json 2>/dev/null || true)"
                if [[ -n "$PR_JSON" ]] && printf '%s' "$PR_JSON" | jq -e . >/dev/null 2>&1; then
                    PR_NUMBER="$(printf '%s' "$PR_JSON" | jq -r '.[0].pullRequestId // empty')"
                    PR_STATE="$(printf '%s' "$PR_JSON" | jq -r '.[0].status // "none"' | tr '[:upper:]' '[:lower:]')"
                    PR_URL="$(printf '%s' "$PR_JSON" | jq -r '.[0].url // empty')"
                    PR_BASE="$(printf '%s' "$PR_JSON" | jq -r '.[0].targetRefName // empty' | sed 's#^refs/heads/##')"
                fi
                ;;
            gitlab)
                PR_JSON="$(glab mr view --output json 2>/dev/null || true)"
                if [[ -n "$PR_JSON" ]] && printf '%s' "$PR_JSON" | jq -e . >/dev/null 2>&1; then
                    PR_NUMBER="$(printf '%s' "$PR_JSON" | jq -r '.iid // empty')"
                    PR_STATE="$(printf '%s' "$PR_JSON" | jq -r '.state // "none"' | tr '[:upper:]' '[:lower:]')"
                    PR_URL="$(printf '%s' "$PR_JSON" | jq -r '.web_url // empty')"
                    PR_BASE="$(printf '%s' "$PR_JSON" | jq -r '.target_branch // empty')"
                fi
                ;;
        esac
    fi
fi

REVIEW_PATH=""
REVIEW_STATE="missing"
REVIEW_OPEN_FINDINGS=0
if [[ -n "$PR_NUMBER" && -f ".devspark.work/pr-reviews/pr-$PR_NUMBER.md" ]]; then
    REVIEW_PATH=".devspark.work/pr-reviews/pr-$PR_NUMBER.md"
    REVIEW_STATE="$(gate_state "$REVIEW_PATH")"
    REVIEW_OPEN_FINDINGS="$(rg -c '^[[:space:]]*-[[:space:]]+\[ \][[:space:]]+\*\*(C|H|M|L|CON)-[0-9]+' "$REVIEW_PATH" 2>/dev/null || true)"
    REVIEW_OPEN_FINDINGS="${REVIEW_OPEN_FINDINGS:-0}"
fi

RECOMMENDED_COMMAND="none"
RECOMMENDATION_REASON="The detected workflow is complete."
ACTION_KIND="complete"
SAFE_TO_AUTO=false
HUMAN_BOUNDARY="none"
MANUAL_COMMAND=""
ORIENTATION_STATE="complete"

recommend_devspark() {
    RECOMMENDED_COMMAND="$1"; RECOMMENDATION_REASON="$2"; ORIENTATION_STATE="$3"
    ACTION_KIND="devspark"; SAFE_TO_AUTO="$4"; HUMAN_BOUNDARY="none"; MANUAL_COMMAND=""
}
recommend_manual() {
    RECOMMENDED_COMMAND="$1"; RECOMMENDATION_REASON="$2"; ORIENTATION_STATE="$3"
    ACTION_KIND="manual"; SAFE_TO_AUTO=false; HUMAN_BOUNDARY="$4"; MANUAL_COMMAND="$5"
}

if ! $HAS_GIT; then
    recommend_manual "none" "DevSpark workflow detection requires a Git repository." "git-required" "repository" "git init"
elif ! $CONSTITUTION_EXISTS; then
    recommend_devspark "/devspark.constitution" "No project constitution exists yet; lifecycle work needs current governance first." "constitution-missing" false
    HUMAN_BOUNDARY="governance"
    MANUAL_COMMAND="/devspark.constitution"
elif ! $HAS_SPEC; then
    recommend_devspark "/devspark.specify" "No spec or branch-linked quickfix work package exists for '$BRANCH'." "work-not-started" false
    HUMAN_BOUNDARY="branch"
    MANUAL_COMMAND="/devspark.specify <describe the requested change>"
elif [[ "$WORK_KIND" == "spec" && "$HAS_PLAN" == false ]]; then
    recommend_devspark "/devspark.plan" "The spec exists, but plan.md has not been created." "spec-ready" true
elif [[ "$WORK_KIND" == "spec" && "$HAS_TASKS" == false ]]; then
    recommend_devspark "/devspark.tasks" "The implementation plan exists, but tasks.md has not been created." "plan-ready" true
elif [[ "$WORK_KIND" == "spec" && "$CHECKLIST_STATE" == "missing" ]]; then
    recommend_devspark "/devspark.checklist" "The spec requires the checklist gate and no checklist gate result exists." "checklist-required" true
elif [[ "$WORK_KIND" == "spec" && "$CHECKLIST_STATE" == "fail" ]]; then
    recommend_manual "/devspark.checklist" "The checklist gate is blocking and needs human-guided requirement repair." "checklist-blocked" "gate" "Review $FEATURE_DIR/gates/checklist.md, repair the requirements, then run /devspark.checklist"
elif [[ "$WORK_KIND" == "spec" && "$ANALYZE_STATE" == "missing" ]]; then
    recommend_devspark "/devspark.analyze" "Tasks exist, but the required cross-artifact analysis gate has not run." "analyze-required" true
elif [[ "$WORK_KIND" == "spec" && "$ANALYZE_STATE" == "fail" ]]; then
    recommend_manual "/devspark.analyze" "The analyze gate is blocking and its findings need to be resolved." "analyze-blocked" "gate" "Review $FEATURE_DIR/gates/analyze.md, repair the cited artifacts, then run /devspark.analyze"
elif [[ "$WORK_KIND" == "spec" && "$CRITIC_STATE" == "missing" ]]; then
    recommend_devspark "/devspark.critic" "Analysis is complete, but the required adversarial risk gate has not run." "critic-required" true
elif [[ "$WORK_KIND" == "spec" && "$CRITIC_STATE" == "fail" ]]; then
    recommend_manual "/devspark.critic" "The critic gate is blocking and its risks need a human decision or repair." "critic-blocked" "gate" "Review $FEATURE_DIR/gates/critic.md, repair or acknowledge the risks, then run /devspark.critic"
elif [[ "$TASKS_INCOMPLETE" -gt 0 || "$TASKS_TOTAL" -eq 0 ]]; then
    recommend_devspark "/devspark.implement" "$TASKS_INCOMPLETE implementation task(s) remain incomplete." "implementation-ready" true
elif [[ "$WORK_KIND" == "spec" && "$(printf '%s' "$SPEC_STATUS" | tr '[:upper:]' '[:lower:]')" != "complete" ]]; then
    recommend_devspark "/devspark.implement" "All tasks are checked off, but the spec lifecycle status still needs completion validation." "implementation-finalization" true
elif $GIT_DIRTY; then
    recommend_manual "git commit" "Implementation is complete, but code/test/knowledge changes are still uncommitted." "commit-required" "commit" "git status --short && git add <code-test-knowledge-files> && git commit -m \"<message>\""
elif [[ "$BEHIND" -gt 0 ]]; then
    recommend_manual "git rebase" "The branch is $BEHIND commit(s) behind its upstream and must be synchronized by a human." "sync-required" "sync" "git fetch origin && git rebase $UPSTREAM"
elif [[ "$AHEAD" -gt 0 ]]; then
    recommend_manual "git push" "The branch is $AHEAD commit(s) ahead of its upstream; pushing is a shared operation." "push-required" "sync" "git push"
elif [[ -z "$PR_NUMBER" && -z "$UPSTREAM" ]]; then
    recommend_manual "git push" "The completed branch has no upstream; publishing it is a shared operation." "push-required" "sync" "git push -u origin $BRANCH"
elif [[ -z "$PR_NUMBER" && "$PLATFORM_CLI_AVAILABLE" == false ]]; then
    recommend_manual "/devspark.create-pr" "The platform CLI is unavailable, so PR state cannot be verified or created safely." "platform-cli-required" "shared-service" "Install $DEVSPARK_PR_CLI from $DEVSPARK_PR_CLI_INSTALL_URL, then run /devspark.create-pr"
elif [[ -z "$PR_NUMBER" && "$PLATFORM_AUTHENTICATED" == false ]]; then
    recommend_manual "/devspark.create-pr" "The platform CLI is not authenticated, so PR state cannot be verified or created safely." "platform-auth-required" "shared-service" "$DEVSPARK_PR_CLI auth login"
elif [[ -z "$PR_NUMBER" ]]; then
    recommend_devspark "/devspark.create-pr" "Implementation is committed and synchronized, but no pull request exists." "pr-required" true
elif [[ "$PR_STATE" == "merged" || "$PR_STATE" == "completed" ]]; then
    RECOMMENDED_COMMAND="none"; RECOMMENDATION_REASON="PR $PR_NUMBER is merged; this development flow is complete. Release remains a separate human-triggered event."; ORIENTATION_STATE="merged"; ACTION_KIND="complete"; SAFE_TO_AUTO=false
elif [[ "$PR_STATE" == "closed" || "$PR_STATE" == "abandoned" ]]; then
    case "$DEVSPARK_PLATFORM_NAME" in
        github) REOPEN_COMMAND="gh pr reopen $PR_NUMBER" ;;
        gitlab) REOPEN_COMMAND="glab mr reopen $PR_NUMBER" ;;
        azdo) REOPEN_COMMAND="Review PR $PR_NUMBER in Azure DevOps" ;;
    esac
    recommend_manual "/devspark.create-pr" "PR $PR_NUMBER is closed without merge; reopening or replacing it needs a human decision." "pr-closed" "pull-request" "$REOPEN_COMMAND"
elif [[ "$PR_MERGE_STATE" == "BEHIND" ]]; then
    recommend_manual "sync branch" "PR $PR_NUMBER is behind '$PR_BASE'; review cannot proceed until a human synchronizes it." "pr-sync-required" "sync" "gh pr update-branch $PR_NUMBER"
elif [[ "$PR_REVIEW_DECISION" == "CHANGES_REQUESTED" || "$REVIEW_OPEN_FINDINGS" -gt 0 || "$REVIEW_STATE" == "fail" ]]; then
    recommend_manual "/devspark.address-pr-review" "PR $PR_NUMBER has unresolved review findings; the repair flow may create commits." "review-findings" "commit" "/devspark.address-pr-review $PR_NUMBER"
elif [[ "$REVIEW_STATE" == "missing" || "$REVIEW_STATE" == "unknown" ]]; then
    recommend_devspark "/devspark.pr-review" "PR $PR_NUMBER exists, but no current local PR-review gate result is available." "review-required" true
else
    case "$DEVSPARK_PLATFORM_NAME" in
        github) MERGE_COMMAND="gh pr merge $PR_NUMBER" ;;
        azdo) MERGE_COMMAND="az repos pr update --id $PR_NUMBER --status completed" ;;
        gitlab) MERGE_COMMAND="glab mr merge $PR_NUMBER" ;;
    esac
    recommend_manual "merge PR" "PR $PR_NUMBER has a non-blocking review result; merging is a human-owned shared operation." "merge-ready" "merge" "$MERGE_COMMAND"
fi

jq -n \
    --arg repo_root "$REPO_ROOT" \
    --arg branch "$BRANCH" \
    --arg platform "$DEVSPARK_PLATFORM_NAME" \
    --arg work_kind "$WORK_KIND" \
    --arg feature_dir "$FEATURE_DIR" \
    --arg spec_status "$SPEC_STATUS" \
    --arg checklist_state "$CHECKLIST_STATE" \
    --arg analyze_state "$ANALYZE_STATE" \
    --arg critic_state "$CRITIC_STATE" \
    --arg upstream "$UPSTREAM" \
    --arg pr_number "$PR_NUMBER" \
    --arg pr_state "$PR_STATE" \
    --arg pr_url "$PR_URL" \
    --arg review_state "$REVIEW_STATE" \
    --arg orientation_state "$ORIENTATION_STATE" \
    --arg recommended_command "$RECOMMENDED_COMMAND" \
    --arg recommendation_reason "$RECOMMENDATION_REASON" \
    --arg action_kind "$ACTION_KIND" \
    --arg human_boundary "$HUMAN_BOUNDARY" \
    --arg manual_command "$MANUAL_COMMAND" \
    --argjson auto "$AUTO" \
    --argjson has_git "$HAS_GIT" \
    --argjson git_dirty "$GIT_DIRTY" \
    --argjson has_spec "$HAS_SPEC" \
    --argjson has_plan "$HAS_PLAN" \
    --argjson has_tasks "$HAS_TASKS" \
    --argjson tasks_total "$TASKS_TOTAL" \
    --argjson tasks_complete "$TASKS_COMPLETE" \
    --argjson tasks_incomplete "$TASKS_INCOMPLETE" \
    --argjson ahead "$AHEAD" \
    --argjson behind "$BEHIND" \
    --argjson review_open_findings "$REVIEW_OPEN_FINDINGS" \
    --argjson safe_to_auto "$SAFE_TO_AUTO" \
    '{
        REPO_ROOT: $repo_root,
        BRANCH: $branch,
        PLATFORM: $platform,
        AUTO: $auto,
        HAS_GIT: $has_git,
        GIT_DIRTY: $git_dirty,
        UPSTREAM: $upstream,
        AHEAD: $ahead,
        BEHIND: $behind,
        WORK_KIND: $work_kind,
        FEATURE_DIR: $feature_dir,
        HAS_SPEC: $has_spec,
        HAS_PLAN: $has_plan,
        HAS_TASKS: $has_tasks,
        SPEC_STATUS: $spec_status,
        TASKS: {total: $tasks_total, complete: $tasks_complete, incomplete: $tasks_incomplete},
        GATES: {checklist: $checklist_state, analyze: $analyze_state, critic: $critic_state},
        PR: {number: $pr_number, state: $pr_state, url: $pr_url},
        REVIEW: {state: $review_state, open_findings: $review_open_findings},
        ORIENTATION_STATE: $orientation_state,
        RECOMMENDED_COMMAND: $recommended_command,
        RECOMMENDATION_REASON: $recommendation_reason,
        ACTION_KIND: $action_kind,
        SAFE_TO_AUTO: $safe_to_auto,
        HUMAN_BOUNDARY: $human_boundary,
        MANUAL_COMMAND: $manual_command,
        READ_ONLY: true
    }'
