#!/usr/bin/env pwsh
# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
param(
    [Parameter(Position = 0, ValueFromRemainingArguments)]
    [string[]]$Arguments,
    [string]$Root,
    [switch]$Apply,
    [switch]$Json
)

$engine = Join-Path (Split-Path $PSScriptRoot -Parent) 'roadmap-check.py'
$engineArgs = @()
if ($Root) { $engineArgs += @('--root', $Root) }
if ($Apply) { $engineArgs += '--apply' }
if ($Json) { $engineArgs += '--json' }
$engineArgs += $Arguments
& python $engine @engineArgs
exit $LASTEXITCODE
