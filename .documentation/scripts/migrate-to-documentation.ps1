# migrate-to-documentation.ps1
# Migrates Spec Kit projects from old structure (.specify/, memory/, scripts/, templates/)
# to new .documentation/ structure

# Stop on errors
$ErrorActionPreference = "Stop"

# Counters for reporting
$script:DirsMovedCount = 0
$script:FilesUpdatedCount = 0
$script:WarningsCount = 0

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Print-Status {
    param([string]$Message)
    Write-ColorOutput "✓ $Message" "Green"
}

function Print-Warning {
    param([string]$Message)
    Write-ColorOutput "⚠ $Message" "Yellow"
    $script:WarningsCount++
}

function Print-Error {
    param([string]$Message)
    Write-ColorOutput "✗ $Message" "Red"
}

Write-ColorOutput "============================================" "Blue"
Write-ColorOutput "Spec Kit Migration to .documentation/" "Blue"
Write-ColorOutput "============================================" "Blue"
Write-Host ""

# Check if we're in a git repository
$inGitRepo = Test-Path ".git"
if ($inGitRepo) {
    Print-Status "Git repository detected - will preserve history where possible"
} else {
    Print-Warning "Not a git repository - using regular move"
}

# Check if .documentation already exists
if (Test-Path ".documentation") {
    Print-Warning ".documentation/ already exists - will merge with existing content"
}

# Detect what needs to be migrated
$oldStructuresFound = $false

if (Test-Path ".specify") {
    Print-Status "Found .specify/ directory"
    $oldStructuresFound = $true
}

if ((Test-Path "memory") -and -not (Test-Path ".documentation\memory")) {
    Print-Status "Found memory/ directory"
    $oldStructuresFound = $true
}

if ((Test-Path "scripts") -and -not (Test-Path ".documentation\scripts")) {
    Print-Status "Found scripts/ directory"
    $oldStructuresFound = $true
}

if ((Test-Path "templates") -and -not (Test-Path ".documentation\templates")) {
    Print-Status "Found templates/ directory"
    $oldStructuresFound = $true
}

if (-not $oldStructuresFound) {
    Write-Host ""
    Print-Error "No old structure found to migrate."
    Write-Host "Looking for: .specify/, memory/, scripts/, or templates/"
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "This script will:"
Write-Host "  1. Create .documentation/ directory structure"
Write-Host "  2. Move files from old locations to new"
Write-Host "  3. Update path references in files"
Write-Host "  4. Rename old directories with .old suffix"
Write-Host ""
Write-ColorOutput "Press Enter to continue, or Ctrl+C to cancel..." "Yellow"
Read-Host

Write-Host ""
Write-ColorOutput "Step 1: Creating .documentation/ structure" "Blue"

# Create directory structure
New-Item -ItemType Directory -Path ".documentation\memory" -Force | Out-Null
Print-Status "Created .documentation/memory/"

New-Item -ItemType Directory -Path ".documentation\scripts\bash" -Force | Out-Null
New-Item -ItemType Directory -Path ".documentation\scripts\powershell" -Force | Out-Null
Print-Status "Created .documentation/scripts/"

New-Item -ItemType Directory -Path ".documentation\templates" -Force | Out-Null
Print-Status "Created .documentation/templates/"

Write-Host ""
Write-ColorOutput "Step 2: Moving files" "Blue"

function Move-Directory {
    param(
        [string]$Source,
        [string]$Destination,
        [string]$Name
    )

    if (Test-Path $Source) {
        # Copy all contents
        Get-ChildItem -Path $Source -Recurse | ForEach-Object {
            $targetPath = $_.FullName.Replace($Source, $Destination)
            $targetDir = Split-Path $targetPath -Parent

            if (-not (Test-Path $targetDir)) {
                New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
            }

            if ($_.PSIsContainer -eq $false) {
                Copy-Item $_.FullName -Destination $targetPath -Force
            }
        }

        # Rename old directory
        Rename-Item -Path $Source -NewName "$Source.old" -Force
        $script:DirsMovedCount++
        Print-Status "Moved $Name to $Destination"
    }
}

# Move .specify/ if exists
if (Test-Path ".specify") {
    # .specify might contain memory, scripts, templates subdirectories
    if (Test-Path ".specify\memory") {
        Get-ChildItem ".specify\memory" -Recurse | ForEach-Object {
            $target = $_.FullName.Replace(".specify\memory", ".documentation\memory")
            if ($_.PSIsContainer -eq $false) {
                $targetDir = Split-Path $target -Parent
                if (-not (Test-Path $targetDir)) {
                    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
                }
                Copy-Item $_.FullName -Destination $target -Force
            }
        }
    }

    if (Test-Path ".specify\scripts") {
        Get-ChildItem ".specify\scripts" -Recurse | ForEach-Object {
            $target = $_.FullName.Replace(".specify\scripts", ".documentation\scripts")
            if ($_.PSIsContainer -eq $false) {
                $targetDir = Split-Path $target -Parent
                if (-not (Test-Path $targetDir)) {
                    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
                }
                Copy-Item $_.FullName -Destination $target -Force
            }
        }
    }

    if (Test-Path ".specify\templates") {
        Get-ChildItem ".specify\templates" -Recurse | ForEach-Object {
            $target = $_.FullName.Replace(".specify\templates", ".documentation\templates")
            if ($_.PSIsContainer -eq $false) {
                $targetDir = Split-Path $target -Parent
                if (-not (Test-Path $targetDir)) {
                    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
                }
                Copy-Item $_.FullName -Destination $target -Force
            }
        }
    }

    # Copy any other files in .specify root
    Get-ChildItem ".specify" -File | ForEach-Object {
        Copy-Item $_.FullName -Destination ".documentation\" -Force
    }

    Rename-Item -Path ".specify" -NewName ".specify.old" -Force
    $script:DirsMovedCount++
    Print-Status "Moved .specify/ contents to .documentation/"
}

# Move top-level directories
Move-Directory "memory" ".documentation\memory" "memory/"
Move-Directory "scripts" ".documentation\scripts" "scripts/"
Move-Directory "templates" ".documentation\templates" "templates/"

Write-Host ""
Write-ColorOutput "Step 3: Updating path references in files" "Blue"

function Update-FileReferences {
    param([string]$FilePath)

    if (-not (Test-Path $FilePath)) {
        return
    }

    # Read file content
    $content = Get-Content -Path $FilePath -Raw

    # Store original for comparison
    $originalContent = $content

    # Update references using regex
    $content = $content -replace '(/?)\.specify/', '$1.documentation/'
    $content = $content -replace '(^|\s|`)/memory/', '$1/.documentation/memory/'
    $content = $content -replace '(^|\s|`)/scripts/', '$1/.documentation/scripts/'
    $content = $content -replace '(^|\s|`)/templates/', '$1/.documentation/templates/'
    $content = $content -replace 'memory/constitution\.md', '.documentation/memory/constitution.md'

    # Write back if changed
    if ($content -ne $originalContent) {
        Set-Content -Path $FilePath -Value $content -NoNewline
        $script:FilesUpdatedCount++
        Print-Status "Updated references in $FilePath"
    }
}

# Update agent command files
$agentDirs = @('.claude', '.github', '.cursor', '.windsurf', '.gemini', '.qwen', '.opencode',
               '.codex', '.kilocode', '.augment', '.roo', '.codebuddy', '.qoder', '.amazonq',
               '.agents', '.shai', '.bob')

foreach ($dir in $agentDirs) {
    if (Test-Path $dir) {
        Get-ChildItem -Path $dir -Recurse -Include "*.md", "*.toml" | ForEach-Object {
            Update-FileReferences $_.FullName
        }
    }
}

# Update script files
if (Test-Path ".documentation\scripts") {
    Get-ChildItem -Path ".documentation\scripts" -Recurse -Include "*.sh", "*.ps1" | ForEach-Object {
        Update-FileReferences $_.FullName
    }
}

# Update documentation files
$docsToUpdate = @("README.md")
if (Test-Path ".documentation") {
    $docsToUpdate += Get-ChildItem -Path ".documentation" -Filter "*.md" | Select-Object -ExpandProperty FullName
}
if (Test-Path ".vscode\settings.json") {
    $docsToUpdate += ".vscode\settings.json"
}

foreach ($file in $docsToUpdate) {
    if (Test-Path $file) {
        Update-FileReferences $file
    }
}

Write-Host ""
Write-ColorOutput "Step 4: Creating .gitignore entry" "Blue"

# Add .documentation build output to .gitignore if needed
if (Test-Path ".gitignore") {
    $gitignoreContent = Get-Content ".gitignore" -Raw
    if ($gitignoreContent -notmatch ".documentation/_site") {
        Add-Content -Path ".gitignore" -Value "`n# Spec Kit documentation build output`n.documentation/_site/"
        Print-Status "Added .documentation/_site/ to .gitignore"
    } else {
        Print-Status ".gitignore already configured"
    }
}

Write-Host ""
Write-ColorOutput "============================================" "Green"
Write-ColorOutput "Migration Complete!" "Green"
Write-ColorOutput "============================================" "Green"
Write-Host ""
Write-Host "Summary:"
Write-Host "  - Directories moved: $script:DirsMovedCount"
Write-Host "  - Files updated: $script:FilesUpdatedCount"
Write-Host "  - Warnings: $script:WarningsCount"
Write-Host ""
Write-Host "Next steps:"
Write-ColorOutput "  1. Review changes: git status and git diff" "Yellow"
Write-Host "  2. Test slash commands in your AI assistant"
Write-ColorOutput "  3. Test scripts: .\.documentation\scripts\powershell\setup-plan.ps1" "Yellow"
Write-Host "  4. If everything works, commit:"
Write-ColorOutput "     git add -A" "Yellow"
Write-ColorOutput "     git commit -m 'chore: migrate to .documentation/ structure'" "Yellow"
Write-Host "  5. Delete old backups:"
Write-ColorOutput "     Remove-Item .specify.old, memory.old, scripts.old, templates.old -Recurse -Force" "Yellow"
Write-Host ""

if ($script:WarningsCount -gt 0) {
    Write-ColorOutput "⚠ Please review warnings above before committing" "Yellow"
    Write-Host ""
}

Print-Status "Migration script completed successfully"
