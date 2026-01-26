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
    .\generate-release-notes.ps1 -NewVersion "v1.0.0-markhazleton.1" -LastTag "v0.0.90"
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
# Mark Hazleton's Spec Kit Fork

This is a fork of the GitHub Spec Kit with additional features and enhancements.

## Fork-Specific Features

- **PR Review Command**: Enhanced constitution-based pull request review workflow
- **Extended Agent Support**: Additional integrations and customizations
- **Custom Templates**: Tailored templates for specific development workflows

## Using This Release

You can use these releases with your agent of choice. We recommend using the Specify CLI to scaffold your projects, however you can download these independently and manage them yourself.

## Changelog

$commits

---

*Based on upstream GitHub Spec Kit. This fork is maintained independently and may contain features not yet available in the upstream project.*
"@

# Write to file
$releaseNotes | Out-File -FilePath "release_notes.md" -Encoding utf8

Write-Host "Generated release notes:"
Get-Content "release_notes.md"
