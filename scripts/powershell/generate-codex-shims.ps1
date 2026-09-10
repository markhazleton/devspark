#!/usr/bin/env pwsh
[CmdletBinding()]
param([string]$RepoRoot)

if (-not $RepoRoot) { $RepoRoot = (Get-Location).Path }
$commandsDir = Join-Path $RepoRoot ".devspark/defaults/commands"
$shimDir = Join-Path $RepoRoot ".codex/prompts"
if (-not (Test-Path $commandsDir)) { Write-Error "Commands directory not found: $commandsDir"; exit 2 }
New-Item -ItemType Directory -Force -Path $shimDir | Out-Null

$count = 0
Get-ChildItem -LiteralPath $commandsDir -Filter "devspark.*.md" | Sort-Object Name | ForEach-Object {
    $name = $_.BaseName.Substring(9)
    $target = Join-Path $shimDir "devspark.$name.md"
    $content = @"
---
description: DevSpark $name command shim.
---

## Prompt Resolution

Determine the current git user by running ``git config user.name``.
Normalize to a folder-safe slug: lowercase, replace spaces with hyphens, strip non-alphanumeric/hyphen chars.

Read and execute the instructions from the **first file that exists**:
1. ``.knowledge/overrides/{git-user}/commands/devspark.$name.md`` (personalized override)
2. ``.knowledge/overrides/commands/devspark.$name.md`` (team customization)
3. ``.devspark/defaults/commands/devspark.$name.md`` (stock default)

## User Input

`$ARGUMENTS

Pass the user input above to the resolved prompt.
"@
    [System.IO.File]::WriteAllText($target, $content.TrimStart() + [Environment]::NewLine)
    $count++
}
Write-Output "Generated $count Codex prompt shims in $shimDir."
