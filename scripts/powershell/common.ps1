#!/usr/bin/env pwsh
# Common PowerShell functions analogous to common.sh

function Get-RepoRoot {
    try {
        $result = git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $result
        }
    } catch {
        # Git command failed
    }
    
    # Fall back to script location for non-git repos
    return (Resolve-Path (Join-Path $PSScriptRoot "../../..")).Path
}

function Get-CurrentBranch {
    # First check if DEVSPARK_FEATURE environment variable is set
    if ($env:DEVSPARK_FEATURE) {
        return $env:DEVSPARK_FEATURE
    }
    
    # Then check git if available
    try {
        $result = git rev-parse --abbrev-ref HEAD 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $result
        }
    } catch {
        # Git command failed
    }
    
    # For non-git repos, try to find the latest feature directory
    $repoRoot = Get-RepoRoot
    $specsDir = Join-Path $repoRoot ".documentation/specs"
    
    if (Test-Path $specsDir) {
        $latestFeature = ""
        $highest = 0
        
        Get-ChildItem -Path $specsDir -Directory | ForEach-Object {
            if ($_.Name -match '^(\d{3})-') {
                $num = [int]$matches[1]
                if ($num -gt $highest) {
                    $highest = $num
                    $latestFeature = $_.Name
                }
            }
        }
        
        if ($latestFeature) {
            return $latestFeature
        }
    }
    
    # Final fallback
    return "main"
}

function Test-HasGit {
    try {
        git rev-parse --show-toplevel 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Test-FeatureBranch {
    param(
        [string]$Branch,
        [bool]$HasGit = $true
    )
    
    # For non-git repos, we can't enforce branch naming but still provide output
    if (-not $HasGit) {
        Write-Warning "[devspark] Warning: Git repository not detected; skipped branch validation"
        return $true
    }
    
    if ($Branch -notmatch '^[0-9]{3}-') {
        Write-Output "ERROR: Not on a feature branch. Current branch: $Branch"
        Write-Output "Feature branches should be named like: 001-feature-name"
        return $false
    }
    return $true
}

function Get-FeatureDir {
    param([string]$RepoRoot, [string]$Branch)
    Join-Path $RepoRoot ".documentation/specs/$Branch"
}

function Get-FeaturePathsEnv {
    $repoRoot = Get-RepoRoot
    $currentBranch = Get-CurrentBranch
    $hasGit = Test-HasGit
    $featureDir = Get-FeatureDir -RepoRoot $repoRoot -Branch $currentBranch
    
    [PSCustomObject]@{
        REPO_ROOT     = $repoRoot
        CURRENT_BRANCH = $currentBranch
        HAS_GIT       = $hasGit
        FEATURE_DIR   = $featureDir
        FEATURE_SPEC  = Join-Path $featureDir 'spec.md'
        IMPL_PLAN     = Join-Path $featureDir 'plan.md'
        TASKS         = Join-Path $featureDir 'tasks.md'
        RESEARCH      = Join-Path $featureDir 'research.md'
        DATA_MODEL    = Join-Path $featureDir 'data-model.md'
        QUICKSTART    = Join-Path $featureDir 'quickstart.md'
        CONTRACTS_DIR = Join-Path $featureDir 'contracts'
    }
}

function Test-FileExists {
    param([string]$Path, [string]$Description)
    if (Test-Path -Path $Path -PathType Leaf) {
        Write-Output "  ✓ $Description"
        return $true
    } else {
        Write-Output "  ✗ $Description"
        return $false
    }
}

function Test-DirHasFiles {
    param([string]$Path, [string]$Description)
    if ((Test-Path -Path $Path -PathType Container) -and (Get-ChildItem -Path $Path -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer } | Select-Object -First 1)) {
        Write-Output "  ✓ $Description"
        return $true
    } else {
        Write-Output "  ✗ $Description"
        return $false
    }
}

# ---------------------------------------------------------------------------
# Multi-app support helpers (T010, T015, T023, T027, T029)
# ---------------------------------------------------------------------------

# Detect multi-app or single-app mode (T015)
function Detect-DevSparkMode {
    $repoRoot = Get-RepoRoot
    $registryPath = Join-Path $repoRoot '.documentation/devspark.json'

    if (Test-Path $registryPath) {
        try {
            $config = Get-Content $registryPath -Raw | ConvertFrom-Json
            if ($config.mode -eq 'multi-app') {
                return 'multi-app'
            }
        } catch {
            # Invalid JSON
        }
    }
    return 'single-app'
}

# Validate registry basics using ConvertFrom-Json (T010)
function Test-RegistryJson {
    param([string]$RegistryPath)

    if (-not (Test-Path $RegistryPath)) {
        return [PSCustomObject]@{ valid = $false; error = "Registry file not found" }
    }

    try {
        $config = Get-Content $RegistryPath -Raw | ConvertFrom-Json
    } catch {
        return [PSCustomObject]@{ valid = $false; error = "Invalid JSON" }
    }

    # Check version
    if ($config.version -ne 1) {
        return [PSCustomObject]@{ valid = $false; error = "Unsupported version: $($config.version)" }
    }

    # Check unique IDs
    $ids = $config.apps | ForEach-Object { $_.id }
    $uniqueIds = $ids | Sort-Object -Unique
    if ($ids.Count -ne $uniqueIds.Count) {
        return [PSCustomObject]@{ valid = $false; error = "Duplicate app IDs detected" }
    }

    # Check profile references
    $profileKeys = $config.profiles.PSObject.Properties.Name
    $badProfiles = @()
    foreach ($app in $config.apps) {
        if ($app.inherits) {
            foreach ($prof in $app.inherits) {
                if ($prof -notin $profileKeys) {
                    $badProfiles += $prof
                }
            }
        }
    }
    if ($badProfiles.Count -gt 0) {
        return [PSCustomObject]@{ valid = $false; error = "Unknown profiles: $($badProfiles -join ', ')" }
    }

    return [PSCustomObject]@{
        valid    = $true
        apps     = $config.apps.Count
        profiles = $profileKeys.Count
    }
}

# Resolve app documentation root (T015)
function Resolve-AppDocRoot {
    param(
        [string]$RepoRoot,
        [string]$AppId
    )

    if (-not $AppId) {
        return Join-Path $RepoRoot '.documentation'
    }

    $registryPath = Join-Path $RepoRoot '.documentation/devspark.json'
    if (-not (Test-Path $registryPath)) {
        throw "No multi-app registry found"
    }

    $config = Get-Content $registryPath -Raw | ConvertFrom-Json
    $app = $config.apps | Where-Object { $_.id -eq $AppId } | Select-Object -First 1

    if (-not $app) {
        $available = ($config.apps | ForEach-Object { $_.id }) -join ', '
        throw "Unknown application: $AppId. Available: $available"
    }

    return Join-Path $RepoRoot "$($app.path)/.documentation"
}

# Parse --app and --repo-scope arguments (T027)
function Parse-AppContext {
    param([string[]]$Arguments)

    $result = [PSCustomObject]@{
        AppId     = ''
        RepoScope = $false
        Remaining = @()
    }

    $i = 0
    while ($i -lt $Arguments.Count) {
        switch ($Arguments[$i]) {
            '--app' {
                $i++
                if ($i -ge $Arguments.Count -or $Arguments[$i].StartsWith('--')) {
                    throw "--app requires an application ID"
                }
                $result.AppId = $Arguments[$i]
            }
            '--repo-scope' {
                $result.RepoScope = $true
            }
            default {
                $result.Remaining += $Arguments[$i]
            }
        }
        $i++
    }

    return $result
}

# Resolve scope and validate (T029)
function Resolve-AppScope {
    param(
        [string]$AppId = '',
        [bool]$RepoScope = $false
    )

    $repoRoot = Get-RepoRoot
    $mode = Detect-DevSparkMode

    $result = [PSCustomObject]@{
        Scope   = ''
        DocRoot = ''
        AppId   = ''
        Error   = ''
    }

    if ($mode -eq 'single-app') {
        if ($AppId) {
            $result.Error = "No multi-app registry found. Cannot use --app."
            return $result
        }
        $result.Scope = 'repo'
        $result.DocRoot = Join-Path $repoRoot '.documentation'
        return $result
    }

    # Multi-app mode
    if ($RepoScope) {
        $result.Scope = 'repo'
        $result.DocRoot = Join-Path $repoRoot '.documentation'
        return $result
    }

    if ($AppId) {
        try {
            $docRoot = Resolve-AppDocRoot -RepoRoot $repoRoot -AppId $AppId
            $result.Scope = 'single-app'
            $result.DocRoot = $docRoot
            $result.AppId = $AppId
        } catch {
            $result.Error = $_.Exception.Message
        }
        return $result
    }

    # No explicit scope
    $registryPath = Join-Path $repoRoot '.documentation/devspark.json'
    $config = Get-Content $registryPath -Raw | ConvertFrom-Json
    $appCount = $config.apps.Count

    if ($appCount -gt 1) {
        $available = ($config.apps | ForEach-Object { $_.id }) -join ', '
        $result.Error = "Multiple apps registered; specify --app <id> or use --repo-scope. Available: $available"
        return $result
    }

    if ($appCount -eq 1) {
        $app = $config.apps[0]
        $result.Scope = 'single-app'
        $result.AppId = $app.id
        $result.DocRoot = Join-Path $repoRoot "$($app.path)/.documentation"
        return $result
    }

    $result.Scope = 'repo'
    $result.DocRoot = Join-Path $repoRoot '.documentation'
    return $result
}

# Resolve constitution with app overlay (T023)
function Resolve-Constitution {
    param(
        [string]$RepoRoot,
        [string]$AppId = ''
    )

    $repoConst = Join-Path $RepoRoot '.documentation/memory/constitution.md'
    if (-not (Test-Path $repoConst)) {
        throw "Repository constitution required at $repoConst"
    }

    $output = Get-Content $repoConst -Raw

    if ($AppId) {
        $appDocRoot = Resolve-AppDocRoot -RepoRoot $RepoRoot -AppId $AppId
        $appConst = Join-Path $appDocRoot 'memory/constitution.md'

        if (Test-Path $appConst) {
            $appText = Get-Content $appConst -Raw
            $output = "$output`n`n---`n`n## Application Overlay: $AppId`n`n$appText"
        }
    }

    return $output
}

# Print scope summary (T035)
function Write-ScopeSummary {
    param([PSCustomObject]$Scope)

    Write-Output "--- DevSpark Scope ---"
    Write-Output "scope: $($Scope.Scope)"
    Write-Output "doc-root: $($Scope.DocRoot)"
    if ($Scope.AppId) {
        Write-Output "app: $($Scope.AppId)"
    }
    Write-Output "mode: $(Detect-DevSparkMode)"
    Write-Output "---"
}

# App-aware feature paths (T029)
function Get-FeaturePathsAppAware {
    param([PSCustomObject]$Scope)

    $repoRoot = Get-RepoRoot
    $currentBranch = Get-CurrentBranch
    $hasGit = Test-HasGit

    $docRoot = if ($Scope -and $Scope.DocRoot) { $Scope.DocRoot } else { Join-Path $repoRoot '.documentation' }
    $specsDir = Join-Path $docRoot 'specs'
    $featureDir = Join-Path $specsDir $currentBranch

    return [PSCustomObject]@{
        REPO_ROOT      = $repoRoot
        CURRENT_BRANCH = $currentBranch
        HAS_GIT        = $hasGit
        DEVSPARK_SCOPE = if ($Scope) { $Scope.Scope } else { 'repo' }
        DEVSPARK_APP   = if ($Scope) { $Scope.AppId } else { '' }
        DOC_ROOT       = $docRoot
        FEATURE_DIR    = $featureDir
        FEATURE_SPEC   = Join-Path $featureDir 'spec.md'
        IMPL_PLAN      = Join-Path $featureDir 'plan.md'
        TASKS          = Join-Path $featureDir 'tasks.md'
        RESEARCH       = Join-Path $featureDir 'research.md'
        DATA_MODEL     = Join-Path $featureDir 'data-model.md'
        QUICKSTART     = Join-Path $featureDir 'quickstart.md'
        CONTRACTS_DIR  = Join-Path $featureDir 'contracts'
    }
}

