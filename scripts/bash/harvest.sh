#!/usr/bin/env bash
set -euo pipefail

# Pre-scan repository for harvest targets and emit JSON for /speckit.harvest.

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

scope="full"
json_only=false
sample_limit=100

for arg in "$@"; do
  case "$arg" in
    --json)
      json_only=true
      ;;
    --scope=*)
      scope="${arg#--scope=}"
      ;;
    full|specs|docs|comments|changelog|scan)
      scope="$arg"
      ;;
    --sample-limit=*)
      sample_limit="${arg#--sample-limit=}"
      ;;
  esac
done

case "$scope" in
  full|specs|docs|comments|changelog|scan)
    ;;
  *)
    echo "Invalid scope: $scope" >&2
    exit 1
    ;;
esac

repo_root=$(get_repo_root)
harvest_date=$(date -u +%F)
harvest_timestamp=$(date -u +%FT%TZ)
report_path=".documentation/copilot/harvest-${harvest_date}.md"

json_escape() {
  python - <<'PY' "$1"
import json, sys
print(json.dumps(sys.argv[1]))
PY
}

count_checked_tasks() {
  local file=$1
  local total completed
  total=$(grep -E '^- \[[ Xx]\]' "$file" 2>/dev/null | wc -l | tr -d ' ')
  completed=$(grep -E '^- \[[Xx]\]' "$file" 2>/dev/null | wc -l | tr -d ' ')
  echo "$total $completed"
}

spec_entries=()
changelog_gap_entries=()
changelog_entries=()
specs_completed=0
specs_in_progress=0
specs_draft=0
summary_changelog_gaps=0

changelog_content=""
if [[ -f "$repo_root/CHANGELOG.md" ]]; then
  changelog_content=$(cat "$repo_root/CHANGELOG.md")
fi

if [[ "$scope" == "full" || "$scope" == "specs" || "$scope" == "scan" || "$scope" == "changelog" ]]; then
  specs_dir="$repo_root/.documentation/specs"
  reviews_dir="$repo_root/.documentation/specs/pr-review"
  if [[ -d "$specs_dir" ]]; then
    while IFS= read -r -d '' spec_dir; do
      spec_name=$(basename "$spec_dir")
      [[ "$spec_name" == "pr-review" ]] && continue
      spec_number=""
      if [[ "$spec_name" =~ ^([0-9]{3,4})- ]]; then
        spec_number="${BASH_REMATCH[1]}"
      fi

      tasks_path="$spec_dir/tasks.md"
      total_tasks=0
      completed_tasks=0
      incomplete_tasks=0
      has_tasks=false
      if [[ -f "$tasks_path" ]]; then
        has_tasks=true
        read -r total_tasks completed_tasks < <(count_checked_tasks "$tasks_path")
        incomplete_tasks=$((total_tasks - completed_tasks))
      fi

      has_spec=false
      has_plan=false
      [[ -f "$spec_dir/spec.md" ]] && has_spec=true
      [[ -f "$spec_dir/plan.md" ]] && has_plan=true

      in_changelog=false
      if [[ -n "$spec_number" && -n "$changelog_content" ]]; then
        if grep -Eq "${spec_name}|\[Spec[[:space:]]+0*${spec_number#0}" <<<"$changelog_content"; then
          in_changelog=true
        fi
      fi

      pr_review=""
      if [[ -d "$reviews_dir" ]]; then
        while IFS= read -r -d '' review_file; do
          if grep -q "$spec_name" "$review_file" 2>/dev/null; then
            pr_review=$(basename "$review_file")
            break
          fi
        done < <(find "$reviews_dir" -type f -name '*.md' -print0)
      fi

      status="draft"
      if [[ "$has_tasks" == true && "$total_tasks" -gt 0 && "$incomplete_tasks" -eq 0 && "$in_changelog" == true ]]; then
        status="completed"
        specs_completed=$((specs_completed + 1))
      elif [[ "$has_tasks" == true && "$total_tasks" -gt 0 && "$incomplete_tasks" -eq 0 ]]; then
        status="completed-needs-changelog"
        specs_completed=$((specs_completed + 1))
        summary_changelog_gaps=$((summary_changelog_gaps + 1))
        changelog_gap_entries+=("{\"spec_name\":$(json_escape "$spec_name"),\"spec_number\":$(json_escape "$spec_number"),\"reason\":\"All tasks complete but no CHANGELOG entry found\"}")
      elif [[ "$has_tasks" == true && "$completed_tasks" -gt 0 ]]; then
        status="in-progress"
        specs_in_progress=$((specs_in_progress + 1))
      else
        specs_draft=$((specs_draft + 1))
      fi

      rel_path=${spec_dir#"$repo_root/"}
      spec_entries+=("{\"name\":$(json_escape "$spec_name"),\"number\":$(json_escape "$spec_number"),\"status\":$(json_escape "$status"),\"path\":$(json_escape "$rel_path"),\"has_spec\":$has_spec,\"has_plan\":$has_plan,\"has_tasks\":$has_tasks,\"total_tasks\":$total_tasks,\"completed_tasks\":$completed_tasks,\"incomplete_tasks\":$incomplete_tasks,\"in_changelog\":$in_changelog,\"pr_review\":$(json_escape "$pr_review")}")
      changelog_entries+=("{\"spec_name\":$(json_escape "$spec_name"),\"spec_number\":$(json_escape "$spec_number"),\"status\":$(json_escape "$status"),\"in_changelog\":$in_changelog,\"pr_review\":$(json_escape "$pr_review")}")
    done < <(find "$specs_dir" -mindepth 1 -maxdepth 1 -type d -print0 | head -z -n "$sample_limit")
  fi
fi

code_comments=()
code_comment_count=0
if [[ "$scope" == "full" || "$scope" == "comments" || "$scope" == "scan" ]]; then
  while IFS= read -r match; do
    file=${match%%:*}
    rest=${match#*:}
    line=${rest%%:*}
    text=${rest#*:}
    rel=${file#"$repo_root/"}
    code_comments+=("{\"file\":$(json_escape "$rel"),\"line\":$line,\"text\":$(json_escape "$text"),\"type\":\"spec-reference\"}")
    code_comment_count=$((code_comment_count + 1))
  done < <(grep -RInE --include='*.py' --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' --include='*.cs' --include='*.go' --include='*.rs' '(#|//)[[:space:]]*(spec[[:space:]]+[0-9]+|FR-[0-9]+|Phase[[:space:]]+[0-9]+|TODO\(spec|plan[[:space:]]+[0-9]{3}|T[0-9]{3})' "$repo_root" 2>/dev/null | head -n "$sample_limit" || true)
fi

archive_existing=()
if [[ -d "$repo_root/.archive" ]]; then
  while IFS= read -r -d '' archive_file; do
    archive_existing+=("$(json_escape "${archive_file#"$repo_root/"}")")
  done < <(find "$repo_root/.archive" -type f -print0 | head -z -n "$sample_limit")
fi

docs_all=()
living_reference=()
completed_reviews=()
completed_audits=()
stale_drafts=()
session_notes=()
backup_files=()
orphaned_files=()
impl_plans=()
release_docs=()
quickfix_records=()
legacy_root_docs=()
docs_to_archive=0
bak_files=()
bak_files_found=0
legacy_roots=()

score_doc() {
  local category=$1
  local path=$2
  local score=80
  local taxon="AUTHORITATIVE_REFERENCE"
  local disposition="keep"

  case "$category" in
    completed_review|completed_audit|stale_draft|session_notes|backup|orphaned|legacy_root_doc)
      score=18
      disposition="archive"
      taxon="HISTORICAL_RECORD"
      ;;
    quickfix_record|release_doc)
      score=45
      disposition="consolidate"
      taxon="HISTORICAL_RECORD"
      ;;
    impl_plan)
      score=35
      disposition="archive"
      taxon="RESEARCH_OR_CONTEXT"
      ;;
  esac

  if [[ "$path" == docs/* ]]; then
    taxon="STALE_REFERENCE"
    disposition="archive"
    score=15
  fi

  printf '%s|%s|%s' "$taxon" "$score" "$disposition"
}

if [[ "$scope" == "full" || "$scope" == "docs" || "$scope" == "scan" || "$scope" == "changelog" ]]; then
  doc_roots=()
  [[ -d "$repo_root/.documentation" ]] && doc_roots+=("$repo_root/.documentation:canonical")
  [[ -d "$repo_root/docs" ]] && doc_roots+=("$repo_root/docs:legacy") && legacy_roots+=("docs/")

  for root_info in "${doc_roots[@]:-}"; do
    [[ -z "$root_info" ]] && continue
    root_path=${root_info%%:*}
    root_mode=${root_info##*:}
    while IFS= read -r -d '' file; do
      rel=${file#"$repo_root/"}
      name=$(basename "$file")
      ext=".${name##*.}"
      [[ "$name" != *.* ]] && ext=""
      category="living_reference"

      case "$name" in
        *.bak|*.backup|*.old)
          category="backup"
          bak_files+=("$(json_escape "$rel")")
          bak_files_found=$((bak_files_found + 1))
          ;;
      esac

      if [[ "$root_mode" == "legacy" ]]; then
        category="legacy_root_doc"
      elif [[ "$rel" == .documentation/specs/pr-review/* ]]; then
        category="completed_review"
      elif [[ "$rel" == .documentation/copilot/audit/* ]]; then
        category="completed_audit"
      elif [[ "$rel" == .documentation/drafts/* ]]; then
        category="stale_draft"
      elif [[ "$rel" == .documentation/copilot/session* ]]; then
        category="session_notes"
      elif [[ "$rel" == *.md && "$rel" == *-implementation-plan.md ]]; then
        category="impl_plan"
      elif [[ "$rel" == .documentation/releases/* ]]; then
        category="release_doc"
      elif [[ "$rel" == .documentation/quickfixes/* ]]; then
        category="quickfix_record"
      fi

      IFS='|' read -r taxon score disposition < <(score_doc "$category" "$rel")
      entry="{\"path\":$(json_escape "$rel"),\"name\":$(json_escape "$name"),\"extension\":$(json_escape "$ext"),\"size_bytes\":$(stat -c %s "$file" 2>/dev/null || stat -f %z "$file" 2>/dev/null || echo 0),\"last_modified\":$(json_escape "$(date -u -r "$file" +%F 2>/dev/null || python - <<'PY' "$file"
import datetime, os, sys
print(datetime.datetime.utcfromtimestamp(os.path.getmtime(sys.argv[1])).strftime('%Y-%m-%d'))
PY
)"),\"category\":$(json_escape "$category"),\"taxon\":$(json_escape "$taxon"),\"usefulness_score\":$score,\"disposition\":$(json_escape "$disposition")}"
      docs_all+=("$entry")

      case "$category" in
        living_reference) living_reference+=("$entry") ;;
        completed_review) completed_reviews+=("$entry"); docs_to_archive=$((docs_to_archive + 1)) ;;
        completed_audit) completed_audits+=("$entry"); docs_to_archive=$((docs_to_archive + 1)) ;;
        stale_draft) stale_drafts+=("$entry"); docs_to_archive=$((docs_to_archive + 1)) ;;
        session_notes) session_notes+=("$entry"); docs_to_archive=$((docs_to_archive + 1)) ;;
        backup) backup_files+=("$entry"); docs_to_archive=$((docs_to_archive + 1)) ;;
        orphaned) orphaned_files+=("$entry"); docs_to_archive=$((docs_to_archive + 1)) ;;
        impl_plan) impl_plans+=("$entry"); docs_to_archive=$((docs_to_archive + 1)) ;;
        release_doc) release_docs+=("$entry"); docs_to_archive=$((docs_to_archive + 1)) ;;
        quickfix_record) quickfix_records+=("$entry"); docs_to_archive=$((docs_to_archive + 1)) ;;
        legacy_root_doc) legacy_root_docs+=("$entry"); docs_to_archive=$((docs_to_archive + 1)) ;;
      esac
    done < <(find "$root_path" -type f -print0 | head -z -n "$sample_limit")
  done
fi

join_json_array() {
  local first=true
  printf '['
  for item in "$@"; do
    if [[ "$first" == true ]]; then
      first=false
    else
      printf ','
    fi
    printf '%s' "$item"
  done
  printf ']'
}

printf '{'
printf '"harvest_date":%s,' "$(json_escape "$harvest_date")"
printf '"harvest_timestamp":%s,' "$(json_escape "$harvest_timestamp")"
printf '"repo_root":%s,' "$(json_escape "$repo_root")"
printf '"scope":%s,' "$(json_escape "$scope")"
printf '"report_path":%s,' "$(json_escape "$report_path")"
printf '"specs":%s,' "$(join_json_array "${spec_entries[@]}")"
printf '"docs":{' 
printf '"all":%s,' "$(join_json_array "${docs_all[@]}")"
printf '"living_reference":%s,' "$(join_json_array "${living_reference[@]}")"
printf '"completed_reviews":%s,' "$(join_json_array "${completed_reviews[@]}")"
printf '"completed_audits":%s,' "$(join_json_array "${completed_audits[@]}")"
printf '"stale_drafts":%s,' "$(join_json_array "${stale_drafts[@]}")"
printf '"session_notes":%s,' "$(join_json_array "${session_notes[@]}")"
printf '"backup_files":%s,' "$(join_json_array "${backup_files[@]}")"
printf '"orphaned_files":%s,' "$(join_json_array "${orphaned_files[@]}")"
printf '"impl_plans":%s,' "$(join_json_array "${impl_plans[@]}")"
printf '"release_docs":%s,' "$(join_json_array "${release_docs[@]}")"
printf '"quickfix_records":%s,' "$(join_json_array "${quickfix_records[@]}")"
printf '"legacy_root_docs":%s,' "$(join_json_array "${legacy_root_docs[@]}")"
printf '"taxonomy_counts":{},"disposition_counts":{}},'
printf '"code_comments":%s,' "$(join_json_array "${code_comments[@]}")"
printf '"changelog_gaps":%s,' "$(join_json_array "${changelog_gap_entries[@]}")"
printf '"changelog_entries":%s,' "$(join_json_array "${changelog_entries[@]}")"
printf '"bak_files":%s,' "$(join_json_array "${bak_files[@]}")"
printf '"archive_existing":%s,' "$(join_json_array "${archive_existing[@]}")"
printf '"path_roots":{"canonical_documentation":".documentation/","legacy_roots":%s},' "$(join_json_array "${legacy_roots[@]}")"
printf '"summary":{' 
printf '"specs_completed":%d,' "$specs_completed"
printf '"specs_in_progress":%d,' "$specs_in_progress"
printf '"specs_draft":%d,' "$specs_draft"
printf '"docs_to_archive":%d,' "$docs_to_archive"
printf '"code_comments_found":%d,' "$code_comment_count"
printf '"changelog_gaps":%d,' "$summary_changelog_gaps"
printf '"bak_files_found":%d' "$bak_files_found"
printf '}}'

if [[ "$json_only" == false ]]; then
  printf '\n'
fi
