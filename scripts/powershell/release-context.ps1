#!/usr/bin/env pwsh
#requires -Version 7.0
<#
.SYNOPSIS
    Build release context for DevSpark v4 current-truth releases.

.DESCRIPTION
    Emits repository version, git, and in-flight work-package state. Release is
    the sole archival trigger after code, tests, knowledge, and task linkage
    validate.
#>

param(
    [string]$Version = "",
    [string]$From = "",
    [switch]$DryRun,
    [switch]$Json
)

. (Join-Path $PSScriptRoot 'common.ps1')

function Get-JsonArray {
    param([object[]]$Items)
    return ,@($Items | Where-Object { $_ } | Sort-Object -Unique)
}

function Test-CompletedTaskLinkage {
    param([string]$Content)

    $taskMatches = [regex]::Matches(
        $Content,
        '^\s*-\s+\[[xX]\]\s+T\d+.*?(?=^\s*-\s+\[[ xX]\]\s+T\d+|\z)',
        [System.Text.RegularExpressions.RegexOptions]::Multiline -bor
        [System.Text.RegularExpressions.RegexOptions]::Singleline
    )
    if ($taskMatches.Count -eq 0) { return $false }

    foreach ($taskMatch in $taskMatches) {
        foreach ($field in @('code_ref', 'test_ref', 'knowledge_ref')) {
            $valueMatch = [regex]::Match(
                $taskMatch.Value,
                "(?m)^\s*-\s+$field\s*:\s*(.+?)\s*$"
            )
            if (-not $valueMatch.Success) { return $false }
            $value = $valueMatch.Groups[1].Value.Trim()
            if (-not $value -or $value -ieq 'TODO') { return $false }
            if ($value -match '^(?i:n/a)') {
                $reason = $value -replace '^(?i:n/a)\s*[-—:]\s*', ''
                if (-not $reason -or $reason -ieq 'n/a') { return $false }
            }
        }
    }
    return $true
}

$repoRoot = Get-RepoRoot
$workDir = Join-Path $repoRoot '.devspark.work'
$workPackagesDir = Join-Path $workDir 'specs'
$quickfixesDir = Join-Path $workDir 'quickfixes'
$releaseCandidatesDir = Join-Path $workDir 'release-candidates'
$knowledgeDir = Join-Path $repoRoot '.knowledge'
$constitutionPath = Join-Path $knowledgeDir 'governance/constitution.md'
$devsparkVersionPath = Join-Path $repoRoot '.devspark/VERSION'

$currentVersion = '0.0.0'
$versionSource = 'default'
if (Test-Path $devsparkVersionPath) {
    $versionLine = Get-Content $devsparkVersionPath -ErrorAction SilentlyContinue |
        Where-Object { $_ -match '^version:\s*(\S+)' } |
        Select-Object -First 1
    if ($versionLine -match '^version:\s*(\S+)') {
        $currentVersion = $matches[1]
        $versionSource = '.devspark/VERSION'
    }
}

$lastTag = ''
$lastReleaseDate = ''
$commitsSince = 0
if (Test-HasGit) {
    try { $lastTag = (& git describe --tags --abbrev=0 2>$null) } catch { $lastTag = '' }
    if ($lastTag) {
        try { $lastReleaseDate = (& git log -1 --format=%ci $lastTag 2>$null) } catch { $lastReleaseDate = '' }
        try { $commitsSince = [int](& git rev-list "$lastTag..HEAD" --count 2>$null) } catch { $commitsSince = 0 }
    } else {
        try { $commitsSince = [int](& git rev-list HEAD --count 2>$null) } catch { $commitsSince = 0 }
    }
}

$releaseDate = Get-Date -Format 'yyyy-MM-dd'
$archiveRoot = Join-Path $repoRoot '.archive'
$archiveDate = $releaseDate
$timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$releaseFrom = $From
if (-not $releaseFrom -and $lastReleaseDate) {
    $releaseFrom = $lastReleaseDate.Substring(0, 10)
}
$releaseTo = $releaseDate

$inFlight = @()
$releaseEligible = @()
$blocked = @()
$stagedReleaseCandidates = @()
$inFlightQuickfixes = @()
$releaseEligibleQuickfixes = @()
$blockedQuickfixes = @()
if (Test-Path $workPackagesDir) {
    Get-ChildItem -Path $workPackagesDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $packageName = $_.Name
        $inFlight += $packageName
        $tasksFile = Join-Path $_.FullName 'tasks.md'
        if (Test-Path $tasksFile) {
            $content = Get-Content $tasksFile -Raw -ErrorAction SilentlyContinue
            $unchecked = ([regex]::Matches($content, '^\s*-\s+\[ \]\s+T\d+', 'Multiline')).Count
            $checked = ([regex]::Matches($content, '^\s*-\s+\[[xX]\]\s+T\d+', 'Multiline')).Count
            $linkageComplete = Test-CompletedTaskLinkage -Content $content
            if ($unchecked -eq 0 -and $checked -gt 0 -and $linkageComplete) {
                $releaseEligible += $packageName
            } else {
                $blocked += $packageName
            }
        } else {
            $blocked += $packageName
        }
    }
}

if (Test-Path $quickfixesDir) {
    Get-ChildItem -LiteralPath $quickfixesDir -File -Filter '*.md' -ErrorAction SilentlyContinue |
        ForEach-Object {
            $inFlightQuickfixes += $_.Name
            $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
            $unchecked = ([regex]::Matches($content, '^\s*-\s+\[ \]\s+T\d+', 'Multiline')).Count
            $checked = ([regex]::Matches($content, '^\s*-\s+\[[xX]\]\s+T\d+', 'Multiline')).Count
            if ($unchecked -eq 0 -and $checked -gt 0 -and (Test-CompletedTaskLinkage -Content $content)) {
                $releaseEligibleQuickfixes += $_.Name
            } else {
                $blockedQuickfixes += $_.Name
            }
        }
}

if (Test-Path $releaseCandidatesDir) {
    Get-ChildItem -LiteralPath $releaseCandidatesDir -Force -ErrorAction SilentlyContinue |
        ForEach-Object {
            $stagedReleaseCandidates += [System.IO.Path]::GetRelativePath($repoRoot, $_.FullName).Replace('\', '/')
        }
}

$nextVersion = $Version.TrimStart('v')
$versionBump = 'patch'
if (-not $nextVersion) {
    $parts = $currentVersion.Split('.')
    $major = if ($parts.Count -gt 0) { [int]$parts[0] } else { 0 }
    $minor = if ($parts.Count -gt 1) { [int]$parts[1] } else { 0 }
    $patch = if ($parts.Count -gt 2) { [int]($parts[2] -replace '[^0-9].*$', '') } else { 0 }
    $nextVersion = "$major.$minor.$($patch + 1)"
}

$contributors = @()
if (Test-HasGit) {
    try {
        if ($lastTag) {
            $contributors = @(& git log "$lastTag..HEAD" --format='%aN' 2>$null | Sort-Object -Unique)
        } else {
            $contributors = @(& git log --format='%aN' 2>$null | Sort-Object -Unique | Select-Object -First 20)
        }
    } catch {
        $contributors = @()
    }
}

$result = [ordered]@{
    REPO_ROOT = $repoRoot
    WORK_DIR = $workDir
    WORK_PACKAGES_DIR = $workPackagesDir
    QUICKFIXES_DIR = $quickfixesDir
    RELEASE_CANDIDATES_DIR = $releaseCandidatesDir
    ARCHIVE_ROOT = $archiveRoot
    ARCHIVE_DATE = $archiveDate
    KNOWLEDGE_DIR = $knowledgeDir
    CONSTITUTION_PATH = $constitutionPath
    CURRENT_VERSION = $currentVersion
    VERSION_SOURCE = $versionSource
    NEXT_VERSION = $nextVersion
    VERSION_BUMP = $versionBump
    RELEASE_FROM = $releaseFrom
    RELEASE_TO = $releaseTo
    IN_FLIGHT_WORK_PACKAGES = Get-JsonArray $inFlight
    RELEASE_ELIGIBLE_WORK_PACKAGES = Get-JsonArray $releaseEligible
    BLOCKED_WORK_PACKAGES = Get-JsonArray $blocked
    STAGED_RELEASE_CANDIDATES = Get-JsonArray $stagedReleaseCandidates
    IN_FLIGHT_QUICKFIXES = Get-JsonArray $inFlightQuickfixes
    RELEASE_ELIGIBLE_QUICKFIXES = Get-JsonArray $releaseEligibleQuickfixes
    BLOCKED_QUICKFIXES = Get-JsonArray $blockedQuickfixes
    LAST_TAG = $lastTag
    LAST_RELEASE_DATE = $lastReleaseDate
    COMMITS_SINCE_RELEASE = $commitsSince
    CONTRIBUTORS = Get-JsonArray $contributors
    TIMESTAMP = $timestamp
    RELEASE_DATE = $releaseDate
    DRY_RUN = [bool]$DryRun
    DEVSPARK_VERSION_PATH = $devsparkVersionPath
    INSTALLED_VERSION = $currentVersion
}

if ($Json) {
    $result | ConvertTo-Json -Depth 10
} else {
    Write-Output 'Release Context'
    Write-Output '==============='
    Write-Output "Repository: $repoRoot"
    Write-Output "Current Version: $currentVersion (from $versionSource)"
    Write-Output "Next Version: $nextVersion ($versionBump bump)"
    Write-Output "Last Release: $lastTag ($lastReleaseDate)"
    Write-Output "Release Window: $releaseFrom -> $releaseTo"
    Write-Output "Archive Root: $archiveRoot"
    Write-Output "Archive Date: $archiveDate"
    Write-Output "Commits Since: $commitsSince"
    Write-Output "In-flight Work Packages: $($result.IN_FLIGHT_WORK_PACKAGES.Count)"
    Write-Output "Release-eligible Work Packages: $($result.RELEASE_ELIGIBLE_WORK_PACKAGES.Count)"
    Write-Output "Blocked Work Packages: $($result.BLOCKED_WORK_PACKAGES.Count)"
    Write-Output "Staged Release Candidates: $($result.STAGED_RELEASE_CANDIDATES.Count)"
    Write-Output "In-flight Quickfixes: $($result.IN_FLIGHT_QUICKFIXES.Count)"
    Write-Output "Release-eligible Quickfixes: $($result.RELEASE_ELIGIBLE_QUICKFIXES.Count)"
    Write-Output "Blocked Quickfixes: $($result.BLOCKED_QUICKFIXES.Count)"
    Write-Output "Contributors: $($result.CONTRIBUTORS.Count)"
    if ($DryRun) {
        Write-Output ''
        Write-Output '** DRY RUN MODE - No changes will be made **'
    }
}
