#!/usr/bin/env pwsh
[CmdletBinding()] param([Parameter(Mandatory=$true)][ValidateSet('codex','claude','cursor','antigravity')][string]$Agent,[string]$RepoRoot)
if (-not $RepoRoot) { $RepoRoot = (Get-Location).Path }
$commands = Join-Path $RepoRoot '.devspark/defaults/commands'
if (-not (Test-Path $commands)) { Write-Error "Commands directory not found: $commands"; exit 2 }
$relative = @{codex='.codex/prompts'; claude='.claude/commands'; cursor='.cursor/commands'; antigravity='.gemini/commands'}[$Agent]
$dir = Join-Path $RepoRoot $relative; New-Item -ItemType Directory -Force $dir | Out-Null
Get-ChildItem $commands -Filter 'devspark.*.md' | ForEach-Object {
  $n = $_.BaseName.Substring(9); $out = Join-Path $dir "devspark.$n.md"
  $body = @"
---
description: DevSpark $n command shim.
---

## Prompt Resolution

Read and execute the first existing file below:
1. ``.knowledge/overrides/{git-user}/commands/devspark.$n.md``
2. ``.knowledge/overrides/commands/devspark.$n.md``
3. ``.devspark/defaults/commands/devspark.$n.md``

## User Input

`$ARGUMENTS

Pass the user input to the resolved prompt.
"@
  [IO.File]::WriteAllText($out, $body.TrimStart() + [Environment]::NewLine)
}
Write-Output "Generated $Agent Markdown shims in $dir."
