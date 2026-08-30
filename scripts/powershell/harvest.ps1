#!/usr/bin/env pwsh
#requires -Version 7.0
<#
.SYNOPSIS
    Build DevSpark v4 harvest context.

.DESCRIPTION
    Scans ephemeral .devspark.work packages and reports which ones can be
    archived after verification.
#>

param(
    [string]$Scope = "all",
    [switch]$Json
)

. (Join-Path $PSScriptRoot 'common.ps1')

$repoRoot = Get-RepoRoot
$workDir = Join-Path $repoRoot '.devspark.work'
$workPackagesDir = Join-Path $workDir 'specs'
$knowledgeDir = Join-Path $repoRoot '.knowledge'
$archiveRoot = Join-Path $repoRoot '.archive'
$archiveDate = Get-Date -Format 'yyyy-MM-dd'
$timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

$workPackages = @()
$archiveCandidates = @()
$archiveTargets = @()
$blockedPackages = @()

if (Test-Path $workPackagesDir) {
    Get-ChildItem -Path $workPackagesDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $packageName = $_.Name
        $tasksFile = Join-Path $_.FullName 'tasks.md'
        $status = 'blocked'
        if (Test-Path $tasksFile) {
            $content = Get-Content $tasksFile -Raw -ErrorAction SilentlyContinue
            $unchecked = ([regex]::Matches($content, '^\s*- \[ \]', 'Multiline')).Count
            $checked = ([regex]::Matches($content, '^\s*- \[[xX]\]', 'Multiline')).Count
            $missingLinkage = ([regex]::Matches($content, 'code_ref:\s*$|knowledge_ref:\s*$|code_ref:\s*TODO|knowledge_ref:\s*TODO', 'Multiline')).Count
            if ($unchecked -eq 0 -and $checked -gt 0 -and $missingLinkage -eq 0) {
                $status = 'archive-after-verification'
                $archiveCandidates += $packageName
                $archiveTargets += [ordered]@{
                    id = $packageName
                    source = ".devspark.work/specs/$packageName"
                    target = ".archive/$archiveDate/$packageName"
                }
            } else {
                $blockedPackages += $packageName
            }
        } else {
            $blockedPackages += $packageName
        }
        $workPackages += [ordered]@{
            id = $packageName
            status = $status
        }
    }
}

$result = [ordered]@{
    repo_root = $repoRoot
    scope = $Scope
    work_dir = $workDir
    archive_root = $archiveRoot
    archive_date = $archiveDate
    knowledge_dir = $knowledgeDir
    work_packages = $workPackages
    archive_candidates = @($archiveCandidates | Sort-Object -Unique)
    archive_targets = @($archiveTargets | Sort-Object { $_.id } -Unique)
    blocked_packages = @($blockedPackages | Sort-Object -Unique)
    timestamp = $timestamp
}

if ($Json) {
    $result | ConvertTo-Json -Depth 10
} else {
    Write-Output 'DevSpark v4 Harvest Context'
    Write-Output '==========================='
    Write-Output "Repository: $repoRoot"
    Write-Output "Scope: $Scope"
    Write-Output "Archive Root: $archiveRoot"
    Write-Output "Archive Date: $archiveDate"
    Write-Output "Work packages: $($workPackages.Count)"
    Write-Output "Archive after verification: $($result.archive_candidates.Count)"
    Write-Output "Blocked packages: $($result.blocked_packages.Count)"
}
