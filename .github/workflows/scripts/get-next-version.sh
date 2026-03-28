#!/usr/bin/env bash
set -euo pipefail

# get-next-version.sh
# Calculate release version and output GitHub Actions variables
# Usage: get-next-version.sh [explicit_version]
# Uses standard semantic versioning (MAJOR.MINOR.PATCH)

# Get the latest tag, or use v0.0.0 if no tags exist
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
echo "latest_tag=$LATEST_TAG" >> $GITHUB_OUTPUT

EXPLICIT_VERSION="${1:-}"

normalize_version() {
  local raw="$1"
  raw="${raw#v}"
  if [[ $raw =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "v$raw"
    return 0
  fi
  return 1
}

increment_patch() {
  local tag="$1"
  if [[ $tag =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
    local major="${BASH_REMATCH[1]}"
    local minor="${BASH_REMATCH[2]}"
    local patch="${BASH_REMATCH[3]}"
    patch=$((patch + 1))
    echo "v$major.$minor.$patch"
    return 0
  fi
  echo "v1.0.0"
}

get_pyproject_version() {
  if [[ ! -f "pyproject.toml" ]]; then
    return 1
  fi

  local parsed
  parsed=$(grep -oE '^[[:space:]]*version[[:space:]]*=[[:space:]]*"[0-9]+\.[0-9]+\.[0-9]+"' pyproject.toml | head -n1 | sed -E 's/.*"([0-9]+\.[0-9]+\.[0-9]+)"/\1/')

  if [[ -n "${parsed:-}" ]]; then
    echo "v$parsed"
    return 0
  fi

  return 1
}

# 1) Explicit manual input wins (workflow_dispatch input)
if [[ -n "$EXPLICIT_VERSION" ]]; then
  if NEW_VERSION=$(normalize_version "$EXPLICIT_VERSION"); then
    if PYPROJECT_VERSION=$(get_pyproject_version); then
      if [[ "$NEW_VERSION" != "$PYPROJECT_VERSION" ]]; then
        echo "Explicit version '$NEW_VERSION' does not match pyproject.toml version '$PYPROJECT_VERSION'." >&2
        echo "Update pyproject.toml first to keep Spec Kit Spark and Specify CLI versions in sync." >&2
        exit 1
      fi
    fi

    echo "new_version=$NEW_VERSION" >> $GITHUB_OUTPUT
    echo "New version will be: $NEW_VERSION (source: explicit input)"
    exit 0
  else
    echo "Invalid explicit version '$EXPLICIT_VERSION'. Use MAJOR.MINOR.PATCH (optionally prefixed with v)." >&2
    exit 1
  fi
fi

# 2) Prefer pyproject.toml version when present and not already tagged
if PYPROJECT_VERSION=$(get_pyproject_version); then
  if ! git rev-parse -q --verify "refs/tags/$PYPROJECT_VERSION" >/dev/null 2>&1; then
    echo "new_version=$PYPROJECT_VERSION" >> $GITHUB_OUTPUT
    echo "New version will be: $PYPROJECT_VERSION (source: pyproject.toml)"
    exit 0
  fi
fi

# 3) Fallback: increment latest tag
NEW_VERSION=$(increment_patch "$LATEST_TAG")

echo "new_version=$NEW_VERSION" >> $GITHUB_OUTPUT
echo "New version will be: $NEW_VERSION (source: latest tag increment)"
