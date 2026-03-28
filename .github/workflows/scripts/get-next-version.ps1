#!/usr/bin/env pwsh
#requires -Version 7.0
<#
.SYNOPSIS
    Calculate the next release version
.DESCRIPTION
    Get-next-version.ps1 - Calculate the next version and output GitHub Actions variables.
    Behavior mirrors the bash workflow script:
      1. Explicit input version wins (and must match pyproject.toml when present)
      2. Otherwise, prefer pyproject.toml version when not already tagged
      3. Otherwise, increment the latest tag patch version
    Uses standard semantic versioning (MAJOR.MINOR.PATCH)
.PARAMETER ExplicitVersion
    Optional explicit version (e.g., 1.4.6 or v1.4.6)
.EXAMPLE
    .\get-next-version.ps1
.EXAMPLE
    .\get-next-version.ps1 -ExplicitVersion "v1.4.6"
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

function Get-PyprojectVersion {
    $pyprojectPath = "pyproject.toml"
    if (-not (Test-Path $pyprojectPath)) {
        return $null
    }

    $match = Select-String -Path $pyprojectPath -Pattern '^\s*version\s*=\s*"(\d+\.\d+\.\d+)"' | Select-Object -First 1
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

    return "v1.0.0"
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

    $pyprojectVersion = Get-PyprojectVersion
    if ($pyprojectVersion -and $newVersion -ne $pyprojectVersion) {
        throw "Explicit version '$newVersion' does not match pyproject.toml version '$pyprojectVersion'. Update pyproject.toml first to keep Spec Kit Spark and Specify CLI versions in sync."
    }

    if ($env:GITHUB_OUTPUT) {
        "new_version=$newVersion" | Out-File -FilePath $env:GITHUB_OUTPUT -Append -Encoding utf8
    }
    Write-Host "New version will be: $newVersion (source: explicit input)"
    exit 0
}

# 2) Prefer pyproject.toml version when present and not already tagged
$pyprojectVersion = Get-PyprojectVersion
if ($pyprojectVersion) {
    $tagExists = (& git rev-parse -q --verify "refs/tags/$pyprojectVersion" 2>$null)
    if (-not $tagExists) {
        if ($env:GITHUB_OUTPUT) {
            "new_version=$pyprojectVersion" | Out-File -FilePath $env:GITHUB_OUTPUT -Append -Encoding utf8
        }
        Write-Host "New version will be: $pyprojectVersion (source: pyproject.toml)"
        exit 0
    }
}

# 3) Fallback: increment latest tag
$newVersion = Increment-PatchVersion $latestTag

if ($env:GITHUB_OUTPUT) {
    "new_version=$newVersion" | Out-File -FilePath $env:GITHUB_OUTPUT -Append -Encoding utf8
}
Write-Host "New version will be: $newVersion (source: latest tag increment)"
