#!/usr/bin/env pwsh
#requires -Version 7.0
<#
.SYNOPSIS
    Create a GitHub release with template zip files
.DESCRIPTION
    Create-github-release.ps1 - Create a new GitHub release and upload all agent template packages
.PARAMETER Version
    The version to release (e.g., v1.0.0)
.EXAMPLE
    .\create-github-release.ps1 -Version "v1.0.0"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

$ErrorActionPreference = 'Stop'
$AgentRegistryFile = 'agents-registry.json'

# Check if gh CLI is available
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "GitHub CLI (gh) is not installed or not in PATH"
    exit 1
}

if (-not (Test-Path $AgentRegistryFile)) {
    Write-Error "Missing agent registry: $AgentRegistryFile"
    exit 1
}

# Remove 'v' prefix from version for release title
$versionNoV = $Version -replace '^v', ''

$agents = (Get-Content -LiteralPath $AgentRegistryFile -Raw -Encoding utf8 | ConvertFrom-Json).agents |
    ForEach-Object { $_.key }

# Build the list of files to upload
$files = @()
foreach ($agent in $agents) {
    $files += ".genreleases/devspark-template-$agent-sh-$Version.zip"
    $files += ".genreleases/devspark-template-$agent-ps-$Version.zip"
}

# Check if release_notes.md exists
if (-not (Test-Path "release_notes.md")) {
    Write-Error "release_notes.md not found. Run generate-release-notes.ps1 first."
    exit 1
}

# Create the release
Write-Host "Publishing release $Version..."
gh release view $Version --repo MarkHazleton/devspark *> $null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Release $Version already exists; refreshing assets with --clobber."
    gh release upload $Version `
        $files `
        --repo MarkHazleton/devspark `
        --clobber

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to upload release assets for $Version"
        exit 1
    }

    gh release edit $Version `
        --repo MarkHazleton/devspark `
        --title "DevSpark Templates - $versionNoV" `
        --notes-file release_notes.md
} else {
    gh release create $Version `
        $files `
        --repo MarkHazleton/devspark `
        --title "DevSpark Templates - $versionNoV" `
        --notes-file release_notes.md
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "Successfully published release $Version"
} else {
    Write-Error "Failed to publish release $Version"
    exit 1
}
