#!/usr/bin/env bash
set -euo pipefail

# generate-release-notes.sh
# Generate release notes from git history
# Usage: generate-release-notes.sh <new_version> <last_tag>

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <new_version> <last_tag>" >&2
  exit 1
fi

NEW_VERSION="$1"
export NEW_VERSION
LAST_TAG="$2"

# Get commits since last tag
if [ "$LAST_TAG" = "v0.0.0" ]; then
  # Check how many commits we have and use that as the limit
  COMMIT_COUNT=$(git rev-list --count HEAD)
  if [ "$COMMIT_COUNT" -gt 10 ]; then
    COMMITS=$(git log --oneline --pretty=format:"- %s" HEAD~10..HEAD)
  else
    COMMITS=$(git log --oneline --pretty=format:"- %s" HEAD~$COMMIT_COUNT..HEAD 2>/dev/null || git log --oneline --pretty=format:"- %s")
  fi
else
  COMMITS=$(git log --oneline --pretty=format:"- %s" $LAST_TAG..HEAD)
fi

# Create release notes
cat > release_notes.md << EOF
# DevSpark

DevSpark is an Adaptive System Life Cycle Development (ASLCD) toolkit with constitution-powered commands, prompt-first onboarding, and right-sized workflows for AI coding assistants.

## Highlights

- **Prompt-first lifecycle**: Quickstart and upgrade flows work directly from remote prompt files
- **Constitution-powered workflows**: Requirements, planning, review, and audit flows stay aligned with project rules
- **Agent-agnostic architecture**: Shared stock prompts plus thin shims for 17+ AI coding assistants
- **Safe customization model**: .devspark/ stays replaceable while .documentation/ preserves project work

## Using This Release

For normal use, bootstrap and update DevSpark from your AI chat using the remote quickstart and upgrade prompt files. The CLI remains available for advanced terminal-driven automation.

## Changelog

$COMMITS

---

*DevSpark is independently maintained by Mark Hazleton and the open-source community.*

EOF

echo "Generated release notes:"
cat release_notes.md
