#!/usr/bin/env pwsh
#requires -Version 7.0
<#
.SYNOPSIS
    Build release context for DevSpark v4 current-truth releases.

.DESCRIPTION
    Emits repository version, git, and in-flight work-package state. DevSpark v4
    moves verified work packages to dated human-only .archive folders after
    their code and knowledge deltas land.
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

$repoRoot = Get-RepoRoot
$workDir = Join-Path $repoRoot '.devspark.work'
$workPackagesDir = Join-Path $workDir 'specs'
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
$verifyReady = @()
$blocked = @()
if (Test-Path $workPackagesDir) {
    Get-ChildItem -Path $workPackagesDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $packageName = $_.Name
        $inFlight += $packageName
        $tasksFile = Join-Path $_.FullName 'tasks.md'
        if (Test-Path $tasksFile) {
            $content = Get-Content $tasksFile -Raw -ErrorAction SilentlyContinue
            $unchecked = ([regex]::Matches($content, '^\s*- \[ \]', 'Multiline')).Count
            $checked = ([regex]::Matches($content, '^\s*- \[[xX]\]', 'Multiline')).Count
            $missingLinkage = ([regex]::Matches($content, 'code_ref:\s*$|knowledge_ref:\s*$|code_ref:\s*TODO|knowledge_ref:\s*TODO', 'Multiline')).Count
            if ($unchecked -eq 0 -and $checked -gt 0 -and $missingLinkage -eq 0) {
                $verifyReady += $packageName
            } else {
                $blocked += $packageName
            }
        } else {
            $blocked += $packageName
        }
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
    VERIFY_READY_WORK_PACKAGES = Get-JsonArray $verifyReady
    BLOCKED_WORK_PACKAGES = Get-JsonArray $blocked
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
    Write-Output "Verify-ready Work Packages: $($result.VERIFY_READY_WORK_PACKAGES.Count)"
    Write-Output "Blocked Work Packages: $($result.BLOCKED_WORK_PACKAGES.Count)"
    Write-Output "Contributors: $($result.CONTRIBUTORS.Count)"
    if ($DryRun) {
        Write-Output ''
        Write-Output '** DRY RUN MODE - No changes will be made **'
    }
}
