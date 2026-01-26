#!/usr/bin/env pwsh
#requires -Version 7.0
<#
.SYNOPSIS
    Check if a GitHub release already exists
.DESCRIPTION
    Check-release-exists.ps1 - Verify if a specific version release exists on GitHub
.PARAMETER Version
    The version to check (e.g., v1.0.0-markhazleton.1)
.EXAMPLE
    .\check-release-exists.ps1 -Version "v1.0.0-markhazleton.1"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

$ErrorActionPreference = 'Stop'

# Check if gh CLI is available
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "GitHub CLI (gh) is not installed or not in PATH"
    exit 1
}

# Check if release exists
try {
    gh release view $Version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        if ($env:GITHUB_OUTPUT) {
            "exists=true" | Out-File -FilePath $env:GITHUB_OUTPUT -Append -Encoding utf8
        }
        Write-Host "Release $Version already exists, skipping..."
    } else {
        if ($env:GITHUB_OUTPUT) {
            "exists=false" | Out-File -FilePath $env:GITHUB_OUTPUT -Append -Encoding utf8
        }
        Write-Host "Release $Version does not exist, proceeding..."
    }
} catch {
    if ($env:GITHUB_OUTPUT) {
        "exists=false" | Out-File -FilePath $env:GITHUB_OUTPUT -Append -Encoding utf8
    }
    Write-Host "Release $Version does not exist, proceeding..."
}
