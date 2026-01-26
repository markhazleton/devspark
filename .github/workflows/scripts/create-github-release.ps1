#!/usr/bin/env pwsh
#requires -Version 7.0
<#
.SYNOPSIS
    Create a GitHub release with template zip files
.DESCRIPTION
    Create-github-release.ps1 - Create a new GitHub release and upload all agent template packages
.PARAMETER Version
    The version to release (e.g., v1.0.0-markhazleton.1)
.EXAMPLE
    .\create-github-release.ps1 -Version "v1.0.0-markhazleton.1"
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

# Remove 'v' prefix from version for release title
$versionNoV = $Version -replace '^v', ''

# Define all agents
$agents = @(
    'copilot', 'claude', 'gemini', 'cursor-agent', 'opencode', 'qwen',
    'windsurf', 'codex', 'kilocode', 'auggie', 'roo', 'codebuddy',
    'qoder', 'amp', 'shai', 'q', 'bob'
)

# Build the list of files to upload
$files = @()
foreach ($agent in $agents) {
    $files += ".genreleases/spec-kit-template-$agent-sh-$Version.zip"
    $files += ".genreleases/spec-kit-template-$agent-ps-$Version.zip"
}

# Check if release_notes.md exists
if (-not (Test-Path "release_notes.md")) {
    Write-Error "release_notes.md not found. Run generate-release-notes.ps1 first."
    exit 1
}

# Create the release
Write-Host "Creating release $Version..."
gh release create $Version `
    $files `
    --title "Spec Kit Templates - $versionNoV" `
    --notes-file release_notes.md

if ($LASTEXITCODE -eq 0) {
    Write-Host "Successfully created release $Version"
} else {
    Write-Error "Failed to create release $Version"
    exit 1
}
