#!/usr/bin/env pwsh
# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PassThroughArgs
)

$engine = Join-Path (Split-Path $PSScriptRoot -Parent) 'knowledge-integrity.py'
& python3 $engine @PassThroughArgs
exit $LASTEXITCODE
