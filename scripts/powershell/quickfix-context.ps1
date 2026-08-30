#!/usr/bin/env pwsh
# Quickfix context gathering script
# Supports rapid bug fixes and small features without full spec overhead

param(
    [Parameter(Position = 0, ValueFromRemainingArguments)]
    [string[]]$Arguments,
    [switch]$Json
)

. (Join-Path $PSScriptRoot 'common.ps1')

# Multi-app support (T084)
if (-not (Get-Command Detect-DevSparkMode -ErrorAction SilentlyContinue)) {
    . "$PSScriptRoot/common.ps1"
}

# Parse arguments
$action = "create"
$quickfixId = ""
$description = @()

foreach ($arg in $Arguments) {
    switch -Regex ($arg) {
        "^complete$" { $action = "complete" }
        "^list$" { $action = "list" }
        "^QF-" { $quickfixId = $arg }
        default { $description += $arg }
    }
}
$descriptionText = $description -join " "

# Get repository context
$repoRoot = Get-RepoRoot
$constitutionPath = Join-Path $repoRoot ".knowledge/governance/constitution.md"
$legacyConstitutionPath = Join-Path $repoRoot ".knowledge/governance/constitution.md"
if (-not (Test-Path $constitutionPath) -and (Test-Path $legacyConstitutionPath)) {
    $constitutionPath = $legacyConstitutionPath
}
$quickfixDir = Join-Path $repoRoot ".devspark.work/quickfixes"
$currentBranch = Get-CurrentBranch

# Check constitution exists
$constitutionExists = Test-Path $constitutionPath

# Calculate next quickfix work-package ID
$year = Get-Date -Format "yyyy"
$nextNum = 1

if (Test-Path $quickfixDir) {
    $existingFiles = Get-ChildItem -Path $quickfixDir -Directory -Filter "qf-$year-*" -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending |
        Select-Object -First 1

    if ($existingFiles) {
        if ($existingFiles.Name -match "qf-$year-(\d+)") {
            $currentNum = [int]$matches[1]
            $nextNum = $currentNum + 1
        }
    }
}
$nextId = "qf-{0}-{1:D3}" -f $year, $nextNum

# Get git user for attribution
$gitUser = "unknown"
if (Test-HasGit) {
    try {
        $gitUser = git config user.name 2>$null
        if (-not $gitUser) { $gitUser = "unknown" }
    } catch {
        $gitUser = "unknown"
    }
}

# Get timestamp
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

# Auto-classify based on description keywords
$classification = "minor-feature"
$riskLevel = "LOW"
$maxEffort = "4 hours"

if ($descriptionText) {
    $descLower = $descriptionText.ToLower()

    if ($descLower -match "(urgent|critical|emergency|production|hotfix)") {
        $classification = "hotfix"
        $riskLevel = "HIGH"
        $maxEffort = "2 hours"
    }
    elseif ($descLower -match "(fix|bug|error|crash|broken|issue|null|exception)") {
        $classification = "bug-fix"
        $riskLevel = "MEDIUM"
        $maxEffort = "4 hours"
    }
    elseif ($descLower -match "(config|setting|environment|flag|env)") {
        $classification = "config-change"
        $riskLevel = "LOW"
        $maxEffort = "1 hour"
    }
    elseif ($descLower -match "(doc|readme|comment|documentation)") {
        $classification = "docs-update"
        $riskLevel = "LOW"
        $maxEffort = "2 hours"
    }
}

# List existing quickfix work packages
$quickfixes = @()
if (Test-Path $quickfixDir) {
    $quickfixes = Get-ChildItem -Path $quickfixDir -Directory -ErrorAction SilentlyContinue |
        ForEach-Object { $_.Name }
}

# Output
if ($Json) {
    @{
        REPO_ROOT           = $repoRoot
        CONSTITUTION_PATH   = $constitutionPath
        CONSTITUTION_EXISTS = $constitutionExists
        WORK_PACKAGE_DIR    = (Join-Path $quickfixDir $nextId)
        QUICKFIX_DIR        = $quickfixDir
        CURRENT_BRANCH      = $currentBranch
        NEXT_ID             = $nextId
        GIT_USER            = $gitUser
        TIMESTAMP           = $timestamp
        ACTION              = $action
        QUICKFIX_ID         = $quickfixId
        DESCRIPTION         = $descriptionText
        CLASSIFICATION      = $classification
        RISK_LEVEL          = $riskLevel
        MAX_EFFORT          = $maxEffort
        QUICKFIXES          = $quickfixes
    } | ConvertTo-Json
}
else {
    Write-Output "Quickfix Context"
    Write-Output "================"
    Write-Output "Repository: $repoRoot"
    Write-Output "Constitution: $constitutionPath (exists: $constitutionExists)"
    Write-Output "Quickfix Work Root: $quickfixDir"
    Write-Output "Work Package: $(Join-Path $quickfixDir $nextId)"
    Write-Output "Current Branch: $currentBranch"
    Write-Output "Next ID: $nextId"
    Write-Output "Action: $action"
    if ($descriptionText) {
        Write-Output "Description: $descriptionText"
        Write-Output "Classification: $classification"
        Write-Output "Risk Level: $riskLevel"
        Write-Output "Max Effort: $maxEffort"
    }
}
