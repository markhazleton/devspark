#!/usr/bin/env bash
# Gather bounded, read-only topic context for /devspark.explain.
set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

DRY_RUN=false
TOPIC_PARTS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true ;;
        --json|-Json) ;;
        --) shift; while [[ $# -gt 0 ]]; do TOPIC_PARTS+=("$1"); shift; done; break ;;
        *) TOPIC_PARTS+=("$1") ;;
    esac
    shift
done

TOPIC="${TOPIC_PARTS[*]:-}"
if [[ -z "${TOPIC//[[:space:]]/}" ]]; then
    echo "A free-text topic or question is required." >&2
    exit 2
fi

if ! command -v rg >/dev/null 2>&1; then
    echo "explain-context requires ripgrep (rg)." >&2
    exit 2
fi
if ! command -v jq >/dev/null 2>&1; then
    echo "explain-context requires jq." >&2
    exit 2
fi

REPO_ROOT="$(get_repo_root)"
cd "$REPO_ROOT"

TERMS_JSON=$(printf '%s\n' "$TOPIC" |
    tr '[:upper:]' '[:lower:]' |
    tr -cs '[:alnum:]_-' '\n' |
    awk 'length($0) >= 3 && $0 !~ /^(how|what|where|when|why|who|the|and|are|was|were|does|did|done|for|from|into|with|this|that|work|works|implemented|implementation)$/ { if (!seen[$0]++) print }' |
    jq -R -s 'split("\n") | map(select(length > 0))')

if [[ "$TERMS_JSON" == "[]" ]]; then
    TERMS_JSON=$(printf '%s\n' "$TOPIC" |
        tr '[:upper:]' '[:lower:]' |
        tr -cs '[:alnum:]_-' '\n' |
        awk 'length($0) > 0 { if (!seen[$0]++) print }' |
        jq -R -s 'split("\n") | map(select(length > 0))')
fi
if [[ "$TERMS_JSON" == "[]" ]]; then
    echo "The topic must contain at least one letter or number." >&2
    exit 2
fi

TERM_PATTERN=$(printf '%s' "$TERMS_JSON" | jq -r '
    map(if length >= 8 then . + "|" + .[0:4] else . end) | join("|")
')

knowledge_matches() {
    [[ -d .knowledge ]] || return 0
    {
        rg -l -i \
            --glob '!.knowledge/ontology/*.generated.md' \
            --glob '!.knowledge/overrides/**' \
            -- "$TERM_PATTERN" .knowledge 2>/dev/null || true
        find .knowledge -type f \
            ! -path '.knowledge/ontology/*.generated.md' \
            ! -path '.knowledge/overrides/*' -print 2>/dev/null |
            rg -i -- "$TERM_PATTERN" || true
    } | sed 's#^\./##' | LC_ALL=C sort -u | awk 'NR <= 60'
}

RG_FILE_ARGS=(
    --glob '!**/.git/**'
    --glob '!**/.archive/**'
    --glob '!**/.devspark.work/**'
    --glob '!**/.devspark/**'
    --glob '!**/.knowledge/**'
    --glob '!**/.documentation/**'
    --glob '!**/node_modules/**'
    --glob '!**/.venv/**'
    --glob '!**/venv/**'
    --glob '!**/bin/**'
    --glob '!**/obj/**'
    --glob '!**/dist/**'
    --glob '!**/build/**'
    --glob '!**/.pytest_cache/**'
    --glob '*.{py,pyi,ts,tsx,js,jsx,mjs,cjs,cs,java,go,rs,rb,php,sh,ps1,json,yaml,yml,toml,xml,csproj,fsproj,mod}'
)

all_repo_matches() {
    {
        rg -l -i "${RG_FILE_ARGS[@]}" -- "$TERM_PATTERN" . 2>/dev/null || true
        rg --files "${RG_FILE_ARGS[@]}" . 2>/dev/null |
            rg -i -- "$TERM_PATTERN" || true
    } | sed 's#^\./##' | LC_ALL=C sort -u | awk 'NR <= 120'
}

KNOWLEDGE_JSON=$(knowledge_matches | jq -R -s 'split("\n") | map(select(length > 0))')
ALL_MATCHES=$(all_repo_matches)
TEST_JSON=$(printf '%s\n' "$ALL_MATCHES" |
    awk '{ path=tolower($0) } path ~ /(^|\/)(tests?|specs?)(\/|$)|(^|\/)(test_[^\/]*|[^\/]*(_test|\.test|_spec|\.spec)\.)/ && count < 40 { print; count++ }' |
    jq -R -s 'split("\n") | map(select(length > 0))')
CODE_JSON=$(printf '%s\n' "$ALL_MATCHES" |
    awk '{ path=tolower($0) } path !~ /(^|\/)(tests?|specs?)(\/|$)/ && path !~ /(^|\/)(test_[^\/]*|[^\/]*(_test|\.test|_spec|\.spec)\.)/ && count < 80 { print; count++ }' |
    jq -R -s 'split("\n") | map(select(length > 0))')

jq -n \
    --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg repo_root "$REPO_ROOT" \
    --arg topic "$TOPIC" \
    --argjson terms "$TERMS_JSON" \
    --argjson dry_run "$DRY_RUN" \
    --argjson knowledge_matches "$KNOWLEDGE_JSON" \
    --argjson code_matches "$CODE_JSON" \
    --argjson test_matches "$TEST_JSON" \
    '{
        timestamp: $timestamp,
        repo_root: $repo_root,
        topic: $topic,
        terms: $terms,
        dry_run: $dry_run,
        knowledge_matches: $knowledge_matches,
        code_matches: $code_matches,
        test_matches: $test_matches,
        counts: {
            knowledge: ($knowledge_matches | length),
            code: ($code_matches | length),
            tests: ($test_matches | length)
        },
        constraints: {
            read_only: true,
            archive_ignored: true,
            work_products_ignored: true
        }
    }'
