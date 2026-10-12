#!/usr/bin/env pwsh
# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PassThroughArgs
)

$engine = Join-Path (Split-Path $PSScriptRoot -Parent) 'discover-knowledge.py'
& python3 $engine @PassThroughArgs
exit $LASTEXITCODE
