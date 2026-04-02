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
  .genreleases/devspark-template-copilot-sh-"$VERSION".zip \
  .genreleases/devspark-template-copilot-ps-"$VERSION".zip \
  .genreleases/devspark-template-claude-sh-"$VERSION".zip \
  .genreleases/devspark-template-claude-ps-"$VERSION".zip \
  .genreleases/devspark-template-gemini-sh-"$VERSION".zip \
  .genreleases/devspark-template-gemini-ps-"$VERSION".zip \
  .genreleases/devspark-template-cursor-agent-sh-"$VERSION".zip \
  .genreleases/devspark-template-cursor-agent-ps-"$VERSION".zip \
  .genreleases/devspark-template-opencode-sh-"$VERSION".zip \
  .genreleases/devspark-template-opencode-ps-"$VERSION".zip \
  .genreleases/devspark-template-qwen-sh-"$VERSION".zip \
  .genreleases/devspark-template-qwen-ps-"$VERSION".zip \
  .genreleases/devspark-template-windsurf-sh-"$VERSION".zip \
  .genreleases/devspark-template-windsurf-ps-"$VERSION".zip \
  .genreleases/devspark-template-codex-sh-"$VERSION".zip \
  .genreleases/devspark-template-codex-ps-"$VERSION".zip \
  .genreleases/devspark-template-kilocode-sh-"$VERSION".zip \
  .genreleases/devspark-template-kilocode-ps-"$VERSION".zip \
  .genreleases/devspark-template-auggie-sh-"$VERSION".zip \
  .genreleases/devspark-template-auggie-ps-"$VERSION".zip \
  .genreleases/devspark-template-roo-sh-"$VERSION".zip \
  .genreleases/devspark-template-roo-ps-"$VERSION".zip \
  .genreleases/devspark-template-codebuddy-sh-"$VERSION".zip \
  .genreleases/devspark-template-codebuddy-ps-"$VERSION".zip \
  .genreleases/devspark-template-qodercli-sh-"$VERSION".zip \
  .genreleases/devspark-template-qodercli-ps-"$VERSION".zip \
  .genreleases/devspark-template-amp-sh-"$VERSION".zip \
  .genreleases/devspark-template-amp-ps-"$VERSION".zip \
  .genreleases/devspark-template-shai-sh-"$VERSION".zip \
  .genreleases/devspark-template-shai-ps-"$VERSION".zip \
  .genreleases/devspark-template-q-sh-"$VERSION".zip \
  .genreleases/devspark-template-q-ps-"$VERSION".zip \
  .genreleases/devspark-template-bob-sh-"$VERSION".zip \
  .genreleases/devspark-template-bob-ps-"$VERSION".zip \
  --repo MarkHazleton/devspark \
  --title "DevSpark Templates - $VERSION_NO_V" \
  --notes-file release_notes.md
