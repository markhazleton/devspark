#!/usr/bin/env pwsh
#requires -Version 7.0
<#
.SYNOPSIS
    Calculate the next release version
.DESCRIPTION
    Get-next-version.ps1 - Calculate the next version and output GitHub Actions variables.
    Behavior mirrors the bash workflow script:
      1. Explicit input version wins (and must match .devspark/VERSION when present)
      2. Otherwise, prefer .devspark/VERSION when not already tagged
      3. Otherwise, increment the latest tag patch version
    Uses standard semantic versioning (MAJOR.MINOR.PATCH)
.PARAMETER ExplicitVersion
    Optional explicit version (e.g., 4.0.0 or v4.0.0)
.EXAMPLE
    .\get-next-version.ps1
.EXAMPLE
    .\get-next-version.ps1 -ExplicitVersion "v4.0.0"
#>

param(
    [string]$ExplicitVersion = ""
)

$ErrorActionPreference = 'Stop'

function Normalize-Version {
    param([string]$Raw)

    if (-not $Raw) {
        return $null
    }

    $trimmed = $Raw -replace '^v', ''
    if ($trimmed -match '^\d+\.\d+\.\d+$') {
        return "v$trimmed"
    }

    return $null
}

function Get-DevSparkVersion {
    $versionPath = ".devspark/VERSION"
    if (-not (Test-Path $versionPath)) {
        return $null
    }

    $match = Select-String -Path $versionPath -Pattern '^\s*version:\s*(\d+\.\d+\.\d+)' | Select-Object -First 1
    if ($match) {
        return "v$($match.Matches[0].Groups[1].Value)"
    }

    return $null
}

function Increment-PatchVersion {
    param([string]$Tag)

    if ($Tag -match '^v(\d+)\.(\d+)\.(\d+)$') {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        $patch = [int]$matches[3] + 1
        return "v$major.$minor.$patch"
    }

    return "v4.0.0"
}

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

# 1) Explicit manual input wins
if ($ExplicitVersion) {
    $newVersion = Normalize-Version $ExplicitVersion
    if (-not $newVersion) {
        throw "Invalid explicit version '$ExplicitVersion'. Use MAJOR.MINOR.PATCH (optionally prefixed with v)."
    }

    $devsparkVersion = Get-DevSparkVersion
    if ($devsparkVersion -and $newVersion -ne $devsparkVersion) {
        throw "Explicit version '$newVersion' does not match .devspark/VERSION '$devsparkVersion'. Update .devspark/VERSION first to keep release assets in sync."
    }

    if ($env:GITHUB_OUTPUT) {
        "new_version=$newVersion" | Out-File -FilePath $env:GITHUB_OUTPUT -Append -Encoding utf8
    }
    Write-Host "New version will be: $newVersion (source: explicit input)"
    exit 0
}

# 2) Prefer .devspark/VERSION when present and not already tagged
$devsparkVersion = Get-DevSparkVersion
if ($devsparkVersion) {
    $tagExists = (& git rev-parse -q --verify "refs/tags/$devsparkVersion" 2>$null)
    if (-not $tagExists) {
        if ($env:GITHUB_OUTPUT) {
            "new_version=$devsparkVersion" | Out-File -FilePath $env:GITHUB_OUTPUT -Append -Encoding utf8
        }
        Write-Host "New version will be: $devsparkVersion (source: .devspark/VERSION)"
        exit 0
    }
}

# 3) Fallback: increment latest tag
$newVersion = Increment-PatchVersion $latestTag

if ($env:GITHUB_OUTPUT) {
    "new_version=$newVersion" | Out-File -FilePath $env:GITHUB_OUTPUT -Append -Encoding utf8
}
Write-Host "New version will be: $newVersion (source: latest tag increment)"
