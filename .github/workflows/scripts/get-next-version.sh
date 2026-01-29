#!/usr/bin/env bash
set -euo pipefail

# get-next-version.sh
# Calculate the next version based on the latest git tag and output GitHub Actions variables
# Usage: get-next-version.sh
# Spec Kit Spark: Uses v1.0.0-spark.X versioning to distinguish from upstream

# Get the latest tag, or use v0.0.0 if no tags exist
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
echo "latest_tag=$LATEST_TAG" >> $GITHUB_OUTPUT

# Check if this is a Spark version
if [[ $LATEST_TAG =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+)-spark\.([0-9]+)$ ]]; then
  # Increment the Spark version number
  MAJOR=${BASH_REMATCH[1]}
  MINOR=${BASH_REMATCH[2]}
  PATCH=${BASH_REMATCH[3]}
  SPARK_VERSION=${BASH_REMATCH[4]}
  SPARK_VERSION=$((SPARK_VERSION + 1))
  NEW_VERSION="v$MAJOR.$MINOR.$PATCH-spark.$SPARK_VERSION"
else
  # First Spark release or upstream version - start with v1.0.0-spark.1
  NEW_VERSION="v1.0.0-spark.1"
fi

echo "new_version=$NEW_VERSION" >> $GITHUB_OUTPUT
echo "New version will be: $NEW_VERSION"
