#!/usr/bin/env bash
set -euo pipefail

# create-github-release.sh
# Create a GitHub release with all template zip files
# Usage: create-github-release.sh <version>

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>" >&2
  exit 1
fi

VERSION="$1"

# Remove 'v' prefix from version for release title
VERSION_NO_V=${VERSION#v}

gh release create "$VERSION" \
  .genreleases/spec-kit-spark-template-copilot-sh-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-copilot-ps-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-claude-sh-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-claude-ps-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-gemini-sh-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-gemini-ps-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-cursor-agent-sh-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-cursor-agent-ps-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-opencode-sh-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-opencode-ps-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-qwen-sh-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-qwen-ps-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-windsurf-sh-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-windsurf-ps-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-codex-sh-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-codex-ps-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-kilocode-sh-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-kilocode-ps-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-auggie-sh-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-auggie-ps-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-roo-sh-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-roo-ps-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-codebuddy-sh-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-codebuddy-ps-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-qodercli-sh-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-qodercli-ps-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-amp-sh-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-amp-ps-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-shai-sh-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-shai-ps-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-q-sh-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-q-ps-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-bob-sh-"$VERSION".zip \
  .genreleases/spec-kit-spark-template-bob-ps-"$VERSION".zip \
  --repo MarkHazleton/spec-kit \
  --title "Spec Kit Spark Templates - $VERSION_NO_V" \
  --notes-file release_notes.md
