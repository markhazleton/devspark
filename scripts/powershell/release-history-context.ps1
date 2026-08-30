#!/usr/bin/env pwsh
#requires -Version 7.0
<#
.SYNOPSIS
    Build release history context from Git.

.DESCRIPTION
    Reads Git history for release notes and contributor context. Git is the v4
    source for previous states; no repository archive folders are read or
    produced by this helper.
#>

param(
    [string]$BaseRef = "",
    [string]$HeadRef = "HEAD",
    [string]$FromDate = "",
    [string]$ToDate = "",
    [switch]$Json
)

. (Join-Path $PSScriptRoot 'common.ps1')

function Invoke-GitSafe {
    param([string[]]$GitArgs)

    try {
        $result = & git @GitArgs 2>$null
        if ($LASTEXITCODE -ne 0) {
            return @()
        }
        return @($result)
    } catch {
        return @()
    }
}

if (-not (Test-HasGit)) {
    throw 'release-history-context requires git.'
}

$repoRoot = Get-RepoRoot
$range = if ($BaseRef) { "$BaseRef..$HeadRef" } else { $HeadRef }
$rawCommits = Invoke-GitSafe @(
    'log',
    $range,
    '--date=short',
    '--pretty=format:%H%x1f%ad%x1f%an%x1f%s'
)

$commits = @()
$contributors = @{}
$prNumbers = New-Object 'System.Collections.Generic.HashSet[int]'

foreach ($line in $rawCommits) {
    $parts = $line -split [char]0x1f, 4
    if ($parts.Count -ne 4) {
        continue
    }
    $sha = $parts[0]
    $date = $parts[1]
    $author = $parts[2]
    $subject = $parts[3]
    if ($FromDate -and $date -lt $FromDate) {
        continue
    }
    if ($ToDate -and $date -gt $ToDate) {
        continue
    }
    $contributors[$author] = 1 + [int]($contributors[$author] ?? 0)
    foreach ($match in ([regex]::Matches($subject, '\(#(\d+)\)|Merge pull request #(\d+)'))) {
        $value = if ($match.Groups[1].Success) { $match.Groups[1].Value } else { $match.Groups[2].Value }
        if ($value) {
            [void]$prNumbers.Add([int]$value)
        }
    }
    $commits += [ordered]@{
        sha = $sha
        date = $date
        author_role = $author
        message = $subject
    }
}

$dates = @($commits | ForEach-Object { $_.date } | Sort-Object)
$releaseFrom = if ($FromDate) { $FromDate } elseif ($dates.Count) { $dates[0] } else { '' }
$releaseTo = if ($ToDate) { $ToDate } elseif ($dates.Count) { $dates[-1] } else { '' }

$result = [ordered]@{
    REPO_ROOT = $repoRoot
    RELEASE_FROM = $releaseFrom
    RELEASE_TO = $releaseTo
    COMMITS = $commits
    CONTRIBUTORS = @($contributors.Keys | Sort-Object)
    CONTRIBUTOR_COUNTS = $contributors
    MERGED_PR_NUMBERS = @($prNumbers | Sort-Object)
    MERGED_PR_COUNT = $prNumbers.Count
    PR_REVIEW_SUMMARY = [ordered]@{
        matched_reviews = 0
        files_changed = 0
        tests_added = 0
        breaking_changes = 0
        resolved_high_findings = 0
    }
}

if ($Json) {
    $result | ConvertTo-Json -Depth 10
} else {
    Write-Output 'Release History Context'
    Write-Output '======================='
    Write-Output "Commits: $($commits.Count)"
    Write-Output "Contributors: $($contributors.Keys.Count)"
    Write-Output "Merged PRs: $($prNumbers.Count)"
    Write-Output "Window: $releaseFrom -> $releaseTo"
}
