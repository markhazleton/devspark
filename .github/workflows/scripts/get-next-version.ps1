#!/usr/bin/env pwsh
#requires -Version 7.0
<#
.SYNOPSIS
    Calculate the next version based on the latest git tag
.DESCRIPTION
    Get-next-version.ps1 - Calculate the next version and output GitHub Actions variables
    Spec Kit Spark: Uses v1.0.0-spark.X versioning to distinguish from upstream
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

# Check if this is a Spark version
if ($latestTag -match '^v(\d+)\.(\d+)\.(\d+)-spark\.(\d+)$') {
    # Increment the Spark version number
    $major = $matches[1]
    $minor = $matches[2]
    $patch = $matches[3]
    $sparkVersion = [int]$matches[4]
    $sparkVersion++
    $newVersion = "v$major.$minor.$patch-spark.$sparkVersion"
} else {
    # First Spark release or upstream version - start with v1.0.0-spark.1
    $newVersion = "v1.0.0-spark.1"
}

if ($env:GITHUB_OUTPUT) {
    "new_version=$newVersion" | Out-File -FilePath $env:GITHUB_OUTPUT -Append -Encoding utf8
}
Write-Host "New version will be: $newVersion"
