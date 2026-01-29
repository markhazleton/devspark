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
# Spec Kit Spark

A community extension of GitHub Spec Kit with constitution-powered commands for enhanced development workflows. Part of the WebSpark demonstration suite.

## Spark-Specific Features

- **Discover Constitution**: Analyze existing codebases to reverse-engineer project principles
- **PR Review Command**: Constitution-based pull request review workflow
- **Site Audit**: Comprehensive codebase auditing against constitution principles
- **Critic Command**: Adversarial risk analysis for spec artifacts
- **Extended Agent Support**: 17+ AI coding assistants supported

## Using This Release

You can use these releases with your agent of choice. We recommend using the Specify CLI to scaffold your projects, however you can download these independently and manage them yourself.

## Changelog

$COMMITS

---

*Based on upstream GitHub Spec Kit. Spec Kit Spark is a community extension that may contain features not yet available in the upstream project.*

EOF

echo "Generated release notes:"
cat release_notes.md
