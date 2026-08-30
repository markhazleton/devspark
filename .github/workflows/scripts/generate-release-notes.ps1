#!/usr/bin/env pwsh
#requires -Version 7.0
<#
.SYNOPSIS
    Generate release notes from git history
.DESCRIPTION
    Generate-release-notes.ps1 - Create release notes for GitHub releases
.PARAMETER NewVersion
    The new version being released
.PARAMETER LastTag
    The previous tag to compare against
.EXAMPLE
    .\generate-release-notes.ps1 -NewVersion "v4.0.0" -LastTag "v3.9.9"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$NewVersion,
    
    [Parameter(Mandatory=$true)]
    [string]$LastTag
)

$ErrorActionPreference = 'Stop'

# Get commits since last tag
if ($LastTag -eq "v0.0.0") {
    # Check how many commits we have and use that as the limit
    $commitCount = (git rev-list --count HEAD)
    if ($commitCount -gt 10) {
        $commits = git log --oneline --pretty=format:"- %s" HEAD~10..HEAD
    } else {
        try {
            $commits = git log --oneline --pretty=format:"- %s" HEAD~$commitCount..HEAD 2>$null
        } catch {
            $commits = git log --oneline --pretty=format:"- %s"
        }
    }
} else {
    $commits = git log --oneline --pretty=format:"- %s" "$LastTag..HEAD"
}

# Create release notes
$releaseNotes = @"
# DevSpark

DevSpark is an Adaptive System Life Cycle Development (ASLCD) toolkit with constitution-powered commands, prompt-first onboarding, and right-sized workflows for AI coding assistants.

## Highlights

- **Prompt-first lifecycle**: Quickstart and upgrade flows work directly from remote prompt files
- **Constitution-powered workflows**: Requirements, planning, review, and audit flows stay aligned with project rules
- **Agent-agnostic architecture**: Shared stock prompts plus thin shims for 18+ AI coding assistants
- **Safe customization model**: `.devspark/` stays replaceable while `.knowledge/` preserves project work

## Using This Release

For normal use, bootstrap, update, and repair DevSpark from your AI chat using the remote quickstart prompt files.

## Changelog

$commits

---

*DevSpark is independently maintained by Mark Hazleton and the open-source community.*
"@

# Write to file
$releaseNotes | Out-File -FilePath "release_notes.md" -Encoding utf8

Write-Host "Generated release notes:"
Get-Content "release_notes.md"
