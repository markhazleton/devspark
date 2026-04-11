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
AGENT_REGISTRY_FILE="agents-registry.json"

if [[ ! -f "$AGENT_REGISTRY_FILE" ]]; then
  echo "Missing agent registry: $AGENT_REGISTRY_FILE" >&2
  exit 1
fi

# Remove 'v' prefix from version for release title
VERSION_NO_V=${VERSION#v}

assets=()
while IFS= read -r agent; do
  [[ -n $agent ]] || continue
  assets+=(".genreleases/devspark-template-${agent}-sh-${VERSION}.zip")
  assets+=(".genreleases/devspark-template-${agent}-ps-${VERSION}.zip")
done < <(jq -r '.agents[].key' "$AGENT_REGISTRY_FILE")

gh release create "$VERSION" \
  "${assets[@]}" \
  --repo MarkHazleton/devspark \
  --title "DevSpark Templates - $VERSION_NO_V" \
  --notes-file release_notes.md
