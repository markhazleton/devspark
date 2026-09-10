#!/usr/bin/env bash
# shellcheck disable=SC1083
set -euo pipefail
agent="${1:-}"
root="${2:-$(pwd)}"
commands="$root/.devspark/defaults/commands"
[[ -d "$commands" ]] || { echo "ERROR: $commands not found" >&2; exit 2; }
case "$agent" in
  codex) dir="$root/.codex/prompts"; suffix=".md";;
  claude) dir="$root/.claude/commands"; suffix=".md";;
  cursor) dir="$root/.cursor/commands"; suffix=".md";;
  antigravity) dir="$root/.gemini/commands"; suffix=".md";;
  *) echo "Usage: $0 {codex|claude|cursor|antigravity} [repo-root]" >&2; exit 2;;
esac
mkdir -p "$dir"
for f in "$commands"/devspark.*.md; do
  n="${f##*/}"; n="${n#devspark.}"; n="${n%.md}"; out="$dir/devspark.$n$suffix"; tmp="$out.tmp"
  cat > "$tmp" <<EOF
---
description: DevSpark $n command shim.
---

## Prompt Resolution

Read and execute the first existing file below:
1. `.knowledge/overrides/{git-user}/commands/devspark.$n.md`
2. `.knowledge/overrides/commands/devspark.$n.md`
3. `.devspark/defaults/commands/devspark.$n.md`

## User Input

\$ARGUMENTS

Pass the user input to the resolved prompt.
EOF
  mv "$tmp" "$out"
done
echo "Generated $agent Markdown shims in $dir."
