#!/usr/bin/env pwsh
#requires -Version 7.0
<#
.SYNOPSIS
    Update the framework version stamp
.DESCRIPTION
    Update-version.ps1 - Update .devspark/VERSION.
.PARAMETER Version
    The version to set (e.g., v4.0.0)
.EXAMPLE
    .\update-version.ps1 -Version "v4.0.0"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

$ErrorActionPreference = 'Stop'

$versionNoV = $Version -replace '^v', ''
$today = Get-Date -Format 'yyyy-MM-dd'

$versionPath = ".devspark/VERSION"

if (Test-Path $versionPath) {
    "version: $versionNoV`ninstalled: $today`n" | Set-Content $versionPath -NoNewline
    Write-Host "Updated .devspark/VERSION to $versionNoV"
} else {
    Write-Warning ".devspark/VERSION not found, skipping version update"
}
