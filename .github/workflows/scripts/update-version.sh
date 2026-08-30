#!/usr/bin/env bash
set -euo pipefail

# update-version.sh
# Update the framework version stamp.
# Usage: update-version.sh <version>

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>" >&2
  exit 1
fi

VERSION="$1"

VERSION_NO_V=${VERSION#v}
TODAY=$(date +%F)

if [ -f ".devspark/VERSION" ]; then
  {
    echo "version: $VERSION_NO_V"
    echo "installed: $TODAY"
  } > .devspark/VERSION
  echo "Updated .devspark/VERSION to $VERSION_NO_V"
else
  echo "Warning: .devspark/VERSION not found, skipping version update"
fi
