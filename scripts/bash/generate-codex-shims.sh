#!/usr/bin/env bash
# Generate deterministic Codex prompt shims from installed DevSpark commands.
set -euo pipefail

repo_root="${1:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
commands_dir="$repo_root/.devspark/defaults/commands"
shim_dir="$repo_root/.codex/prompts"

[[ -d "$commands_dir" ]] || { echo "ERROR: commands directory not found: $commands_dir" >&2; exit 2; }
mkdir -p "$shim_dir"

count=0
shopt -s nullglob
for command_file in "$commands_dir"/devspark.*.md; do
  name="${command_file##*/}"
  name="${name#devspark.}"
  name="${name%.md}"
  target="$shim_dir/devspark.$name.md"
  tmp="$target.tmp"
  cat > "$tmp" <<EOF
---
description: DevSpark $name command shim.
---

## Prompt Resolution

Determine the current git user by running \`git config user.name\`.
Normalize to a folder-safe slug: lowercase, replace spaces with hyphens, strip non-alphanumeric/hyphen chars.

Read and execute the instructions from the **first file that exists**:
1. \`.knowledge/overrides/{git-user}/commands/devspark.$name.md\` (personalized override)
2. \`.knowledge/overrides/commands/devspark.$name.md\` (team customization)
3. \`.devspark/defaults/commands/devspark.$name.md\` (stock default)

## User Input

\$ARGUMENTS

Pass the user input above to the resolved prompt.
EOF
  mv "$tmp" "$target"
  count=$((count + 1))
done
echo "Generated $count Codex prompt shims in $shim_dir."
