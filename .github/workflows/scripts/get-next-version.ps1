#!/usr/bin/env pwsh
#requires -Version 7.0
<#
.SYNOPSIS
    Calculate the next version based on the latest git tag
.DESCRIPTION
    Get-next-version.ps1 - Calculate the next version and output GitHub Actions variables
    Uses standard semantic versioning (MAJOR.MINOR.PATCH)
.EXAMPLE
    .\get-next-version.ps1
#>

$ErrorActionPreference = 'Stop'

# Get the latest tag, or use v0.0.0 if no tags exist
try {
    $latestTag = git describe --tags --abbrev=0 2>$null
    if (-not $latestTag) { $latestTag = "v0.0.0" }
} catch {
    $latestTag = "v0.0.0"
}

if ($env:GITHUB_OUTPUT) {
    "latest_tag=$latestTag" | Out-File -FilePath $env:GITHUB_OUTPUT -Append -Encoding utf8
}
Write-Host "Latest tag: $latestTag"

# Parse semantic version
if ($latestTag -match '^v(\d+)\.(\d+)\.(\d+)') {
    # Increment patch version
    $major = [int]$matches[1]
    $minor = [int]$matches[2]
    $patch = [int]$matches[3]
    $patch++
    $newVersion = "v$major.$minor.$patch"
} else {
    # First release - start with v1.0.0
    $newVersion = "v1.0.0"
}

if ($env:GITHUB_OUTPUT) {
    "new_version=$newVersion" | Out-File -FilePath $env:GITHUB_OUTPUT -Append -Encoding utf8
}
Write-Host "New version will be: $newVersion"
