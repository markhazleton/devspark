#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

JSON_MODE=false
BASE_REF=""
HEAD_REF="HEAD"
FROM_DATE=""
TO_DATE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --json)
      JSON_MODE=true
      shift
      ;;
    --base-ref)
      BASE_REF="$2"
      shift 2
      ;;
    --head-ref)
      HEAD_REF="$2"
      shift 2
      ;;
    --from)
      FROM_DATE="$2"
      shift 2
      ;;
    --to)
      TO_DATE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

if ! has_git; then
  echo "ERROR: release-history-context requires git." >&2
  exit 1
fi

PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD="python"
else
  echo "ERROR: python3/python is required to generate JSON output." >&2
  exit 1
fi

REPO_ROOT=$(get_repo_root)

JSON_OUTPUT=$(
  "$PYTHON_CMD" - "$REPO_ROOT" "$BASE_REF" "$HEAD_REF" "$FROM_DATE" "$TO_DATE" <<'PY'
import json
import re
import subprocess
import sys
from pathlib import Path

repo_root = Path(sys.argv[1])
base_ref = sys.argv[2]
head_ref = sys.argv[3]
from_date = sys.argv[4]
to_date = sys.argv[5]


def git_lines(*args: str) -> list[str]:
    result = subprocess.run(["git", *args], cwd=repo_root, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


range_ref = f"{base_ref}..{head_ref}" if base_ref else head_ref
commits_raw = git_lines(
    "log",
    range_ref,
    "--date=short",
    "--pretty=format:%H%x1f%ad%x1f%an%x1f%s",
)

commits = []
contributors: dict[str, int] = {}
pr_numbers: set[int] = set()
for line in commits_raw:
    parts = line.split("\x1f", 3)
    if len(parts) != 4:
        continue
    sha, date, author, subject = parts
    if from_date and date < from_date:
        continue
    if to_date and date > to_date:
        continue
    contributors[author] = contributors.get(author, 0) + 1
    for match in re.findall(r"\(#(\d+)\)|Merge pull request #(\d+)", subject):
        value = match[0] or match[1]
        if value:
            pr_numbers.add(int(value))
    commits.append({"sha": sha, "date": date, "author_role": author, "message": subject})

dates = [item["date"] for item in commits]
result = {
    "REPO_ROOT": str(repo_root),
    "RELEASE_FROM": from_date or (min(dates) if dates else ""),
    "RELEASE_TO": to_date or (max(dates) if dates else ""),
    "COMMITS": commits,
    "CONTRIBUTORS": sorted(contributors),
    "CONTRIBUTOR_COUNTS": contributors,
    "MERGED_PR_NUMBERS": sorted(pr_numbers),
    "MERGED_PR_COUNT": len(pr_numbers),
    "PR_REVIEW_SUMMARY": {
        "matched_reviews": 0,
        "files_changed": 0,
        "tests_added": 0,
        "breaking_changes": 0,
        "resolved_high_findings": 0,
    },
}
print(json.dumps(result, indent=2))
PY
)

if [[ "$JSON_MODE" == true ]]; then
  printf '%s\n' "$JSON_OUTPUT"
else
  JSON_FILE=$(mktemp)
  trap 'rm -f "$JSON_FILE"' EXIT
  printf '%s\n' "$JSON_OUTPUT" > "$JSON_FILE"
  "$PYTHON_CMD" - "$JSON_FILE" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text())
print("Release History Context")
print("=======================")
print(f"Commits: {len(data['COMMITS'])}")
print(f"Contributors: {len(data['CONTRIBUTORS'])}")
print(f"Merged PRs: {data['MERGED_PR_COUNT']}")
print(f"Window: {data['RELEASE_FROM']} -> {data['RELEASE_TO']}")
PY
fi
