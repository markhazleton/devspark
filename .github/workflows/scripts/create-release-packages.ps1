#!/usr/bin/env pwsh
#requires -Version 7.0

<#
.SYNOPSIS
    Build DevSpark template release archives for each supported AI assistant and script type.

.DESCRIPTION
    create-release-packages.ps1 (workflow-local)
    Build DevSpark template release archives for each supported AI assistant and script type.
    
.PARAMETER Version
    Version string with leading 'v' (e.g., v1.0.0)

.PARAMETER Agents
    Comma or space separated subset of agents to build (default: all)
    Valid agents: claude, gemini, copilot, cursor-agent, qwen, opencode, windsurf, codex, kilocode, auggie, roo, codebuddy, amp, shai, q, bob, qodercli, antigravity

.PARAMETER Scripts
    Comma or space separated subset of script types to build (default: both)
    Valid scripts: sh, ps

.EXAMPLE
    .\create-release-packages.ps1 -Version v1.0.0

.EXAMPLE
    .\create-release-packages.ps1 -Version v1.0.0 -Agents claude,copilot -Scripts sh

.EXAMPLE
    .\create-release-packages.ps1 -Version v1.0.0 -Agents claude -Scripts ps
#>

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Version,
    
    [Parameter(Mandatory=$false)]
    [string]$Agents = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Scripts = ""
)

$ErrorActionPreference = "Stop"

# Validate version format
if ($Version -notmatch '^v\d+\.\d+\.\d+$') {
    Write-Error "Version must look like v1.0.0 (standard semantic versioning)"
    exit 1
}

Write-Host "Building release packages for $Version"

$AgentRegistryFile = "agents-registry.json"
if (-not (Test-Path $AgentRegistryFile)) {
    Write-Error "Missing agent registry: $AgentRegistryFile"
    exit 1
}

# Create and use .genreleases directory for all build artifacts
$GenReleasesDir = ".genreleases"
if (Test-Path $GenReleasesDir) {
    Remove-Item -Path $GenReleasesDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $GenReleasesDir -Force | Out-Null

function Rewrite-Paths {
    param([string]$Content)

    # DevSpark uses .devspark/ for framework files and .documentation/ for user work
    $Content = $Content -replace '(/?)\.specify/', '$1.documentation/'
    $Content = $Content -replace '(^|\s|`)/specs/', '$1/.documentation/specs/'
    $Content = $Content -replace '(^|\s|`)/memory/', '$1/.documentation/memory/'
    $Content = $Content -replace '(^|\s|`)/scripts/', '$1/.devspark/scripts/'
    $Content = $Content -replace '(^|\s|`)/templates/', '$1/.devspark/templates/'
    return $Content
}

function Get-AgentRegistry {
    Get-Content -LiteralPath $AgentRegistryFile -Raw -Encoding utf8 | ConvertFrom-Json
}

function Get-RegisteredAgents {
    (Get-AgentRegistry).agents | ForEach-Object { $_.key }
}

function Get-AgentMetadata {
    param([string]$Agent)
    return (Get-AgentRegistry).agents | Where-Object { $_.key -eq $Agent } | Select-Object -First 1
}

function Copy-AgentSupportFiles {
    param(
        [string]$Agent,
        [string]$BaseDir
    )

    $metadata = Get-AgentMetadata -Agent $Agent
    foreach ($supportFile in @($metadata.release.support_files)) {
        if (-not $supportFile) {
            continue
        }
        if (-not (Test-Path $supportFile.source)) {
            continue
        }
        $destinationPath = Join-Path $BaseDir $supportFile.destination
        $destinationDir = Split-Path -Parent $destinationPath
        if (-not (Test-Path $destinationDir)) {
            New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
        }
        Copy-Item -Path $supportFile.source -Destination $destinationPath -Force
    }
}

function Generate-CanonicalCommands {
    # Generate canonical command files in .devspark/defaults/commands/ (stock, upgrade-safe)
    param(
        [string]$OutputDir,
        [string]$ScriptVariant
    )
    
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    
    $templates = Get-ChildItem -Path "templates/commands/*.md" -File -ErrorAction SilentlyContinue
    
    foreach ($template in $templates) {
        $name = [System.IO.Path]::GetFileNameWithoutExtension($template.Name)
        
        # Read file content and normalize line endings
        $fileContent = (Get-Content -Path $template.FullName -Raw) -replace "`r`n", "`n"
        
        # Extract script command from YAML frontmatter
        $scriptCommand = ""
        if ($fileContent -match "(?m)^\s*${ScriptVariant}:\s*(.+)$") {
            $scriptCommand = $matches[1]
        }
        
        if ([string]::IsNullOrEmpty($scriptCommand)) {
            Write-Warning "No script command found for $ScriptVariant in $($template.Name)"
            $scriptCommand = "(Missing script command for $ScriptVariant)"
        }
        
        # Extract agent_script command from YAML frontmatter if present
        $agentScriptCommand = ""
        if ($fileContent -match "(?ms)agent_scripts:.*?^\s*${ScriptVariant}:\s*(.+?)$") {
            $agentScriptCommand = $matches[1].Trim()
        }
        
        # Replace {SCRIPT} placeholder with the script command
        $body = $fileContent -replace '\{SCRIPT\}', $scriptCommand
        
        # Replace {AGENT_SCRIPT} placeholder with the agent script command if found
        if (-not [string]::IsNullOrEmpty($agentScriptCommand)) {
            $body = $body -replace '\{AGENT_SCRIPT\}', $agentScriptCommand
        }
        
        # Remove the scripts: and agent_scripts: sections from frontmatter
        $lines = $body -split "`n"
        $outputLines = @()
        $inFrontmatter = $false
        $skipScripts = $false
        $dashCount = 0
        
        foreach ($line in $lines) {
            if ($line -match '^---$') {
                $outputLines += $line
                $dashCount++
                if ($dashCount -eq 1) {
                    $inFrontmatter = $true
                } else {
                    $inFrontmatter = $false
                }
                continue
            }
            
            if ($inFrontmatter) {
                if ($line -match '^(scripts|agent_scripts):$') {
                    $skipScripts = $true
                    continue
                }
                if ($line -match '^[a-zA-Z].*:' -and $skipScripts) {
                    $skipScripts = $false
                }
                if ($skipScripts -and $line -match '^\s+') {
                    continue
                }
            }
            
            $outputLines += $line
        }
        
        $body = $outputLines -join "`n"
        
        # Apply argument substitution (canonical uses $ARGUMENTS as default) and path rewriting
        $body = $body -replace '\{ARGS\}', '$ARGUMENTS'
        $body = Rewrite-Paths -Content $body
        
        $outputFile = Join-Path $OutputDir "devspark.$name.md"
        Set-Content -Path $outputFile -Value $body -NoNewline
    }
}

function Generate-Shims {
    # Generate thin platform shims that resolve personal -> team -> stock command files
    param(
        [string]$Agent,
        [string]$Extension,
        [string]$ArgFormat,
        [string]$OutputDir
    )
    
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    
    $templates = Get-ChildItem -Path "templates/commands/*.md" -File -ErrorAction SilentlyContinue
    
    foreach ($template in $templates) {
        $name = [System.IO.Path]::GetFileNameWithoutExtension($template.Name)
        
        # Read file content and normalize line endings
        $fileContent = (Get-Content -Path $template.FullName -Raw) -replace "`r`n", "`n"
        
        # Extract description from YAML frontmatter
        $description = ""
        if ($fileContent -match '(?m)^description:\s*(.+)$') {
            $description = $matches[1]
        }
        
        # Extract handoffs block from YAML frontmatter (for Copilot)
        $handoffsBlock = ""
        $inHandoffs = $false
        foreach ($line in ($fileContent -split "`n")) {
            if ($line -match '^handoffs:') {
                $inHandoffs = $true
                $handoffsBlock += "$line`n"
                continue
            }
            if ($inHandoffs -and $line -match '^  ') {
                $handoffsBlock += "$line`n"
                continue
            }
            if ($inHandoffs -and $line -match '^[a-zA-Z]') {
                $inHandoffs = $false
            }
        }
        
        $outputFile = Join-Path $OutputDir "devspark.$name.$Extension"
        
        switch ($Extension) {
            'toml' {
                $shimContent = @"
description = "$description"

prompt = """`n## Prompt Resolution

Determine the current git user by running ``git config user.name``.
Normalize to a folder-safe slug: lowercase, replace spaces with hyphens, strip non-alphanumeric/hyphen chars.

Read and execute the instructions from the **first file that exists**:
1. ``.documentation/{git-user}/commands/devspark.$name.md`` (personalized override)
2. ``.documentation/commands/devspark.$name.md`` (team customization)
3. ``.devspark/defaults/commands/devspark.$name.md`` (stock default)

Where ``{git-user}`` is the normalized slug from step above.

## User Input

``````text
$ArgFormat
``````

Pass the user input above to the resolved prompt.
"""
"@
                Set-Content -Path $outputFile -Value $shimContent -NoNewline
            }
            { $_ -eq 'md' -or $_ -eq 'agent.md' } {
                $shimLines = @()
                $shimLines += "---"
                $shimLines += "description: $description"
                if (-not [string]::IsNullOrEmpty($handoffsBlock.Trim())) {
                    $shimLines += $handoffsBlock.TrimEnd()
                }
                $shimLines += "---"
                $shimLines += ""
                $shimLines += "## Prompt Resolution"
                $shimLines += ""
                $shimLines += "Determine the current git user by running ``git config user.name``."
                $shimLines += "Normalize to a folder-safe slug: lowercase, replace spaces with hyphens, strip non-alphanumeric/hyphen chars."
                $shimLines += ""
                $shimLines += "Read and execute the instructions from the **first file that exists**:"
                $shimLines += "1. ``.documentation/{git-user}/commands/devspark.$name.md`` (personalized override)"
                $shimLines += "2. ``.documentation/commands/devspark.$name.md`` (team customization)"
                $shimLines += "3. ``.devspark/defaults/commands/devspark.$name.md`` (stock default)"
                $shimLines += ""
                $shimLines += "Where ``{git-user}`` is the normalized slug from step above."
                $shimLines += ""
                $shimLines += "## User Input"
                $shimLines += ""
                $shimLines += '```text'
                $shimLines += $ArgFormat
                $shimLines += '```'
                $shimLines += ""
                $shimLines += "Pass the user input above to the resolved prompt."
                
                $shimContent = $shimLines -join "`n"
                Set-Content -Path $outputFile -Value $shimContent -NoNewline
            }
        }
    }
}

function Generate-Commands {
    param(
        [string]$Agent,
        [string]$Extension,
        [string]$ArgFormat,
        [string]$OutputDir,
        [string]$ScriptVariant
    )
    
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    
    $templates = Get-ChildItem -Path "templates/commands/*.md" -File -ErrorAction SilentlyContinue
    
    foreach ($template in $templates) {
        $name = [System.IO.Path]::GetFileNameWithoutExtension($template.Name)
        
        # Read file content and normalize line endings
        $fileContent = (Get-Content -Path $template.FullName -Raw) -replace "`r`n", "`n"
        
        # Extract description from YAML frontmatter
        $description = ""
        if ($fileContent -match '(?m)^description:\s*(.+)$') {
            $description = $matches[1]
        }
        
        # Extract script command from YAML frontmatter
        $scriptCommand = ""
        if ($fileContent -match "(?m)^\s*${ScriptVariant}:\s*(.+)$") {
            $scriptCommand = $matches[1]
        }
        
        if ([string]::IsNullOrEmpty($scriptCommand)) {
            Write-Warning "No script command found for $ScriptVariant in $($template.Name)"
            $scriptCommand = "(Missing script command for $ScriptVariant)"
        }
        
        # Extract agent_script command from YAML frontmatter if present
        $agentScriptCommand = ""
        if ($fileContent -match "(?ms)agent_scripts:.*?^\s*${ScriptVariant}:\s*(.+?)$") {
            $agentScriptCommand = $matches[1].Trim()
        }
        
        # Replace {SCRIPT} placeholder with the script command
        $body = $fileContent -replace '\{SCRIPT\}', $scriptCommand
        
        # Replace {AGENT_SCRIPT} placeholder with the agent script command if found
        if (-not [string]::IsNullOrEmpty($agentScriptCommand)) {
            $body = $body -replace '\{AGENT_SCRIPT\}', $agentScriptCommand
        }
        
        # Remove the scripts: and agent_scripts: sections from frontmatter
        $lines = $body -split "`n"
        $outputLines = @()
        $inFrontmatter = $false
        $skipScripts = $false
        $dashCount = 0
        
        foreach ($line in $lines) {
            if ($line -match '^---$') {
                $outputLines += $line
                $dashCount++
                if ($dashCount -eq 1) {
                    $inFrontmatter = $true
                } else {
                    $inFrontmatter = $false
                }
                continue
            }
            
            if ($inFrontmatter) {
                if ($line -match '^(scripts|agent_scripts):$') {
                    $skipScripts = $true
                    continue
                }
                if ($line -match '^[a-zA-Z].*:' -and $skipScripts) {
                    $skipScripts = $false
                }
                if ($skipScripts -and $line -match '^\s+') {
                    continue
                }
            }
            
            $outputLines += $line
        }
        
        $body = $outputLines -join "`n"
        
        # Apply other substitutions
        $body = $body -replace '\{ARGS\}', $ArgFormat
        $body = $body -replace '__AGENT__', $Agent
        $body = Rewrite-Paths -Content $body
        
        # Generate output file based on extension
        $outputFile = Join-Path $OutputDir "devspark.$name.$Extension"
        
        switch ($Extension) {
            'toml' {
                $body = $body -replace '\\', '\\'
                $output = "description = `"$description`"`n`nprompt = `"`"`"`n$body`n`"`"`""
                Set-Content -Path $outputFile -Value $output -NoNewline
            }
            'md' {
                Set-Content -Path $outputFile -Value $body -NoNewline
            }
            'agent.md' {
                Set-Content -Path $outputFile -Value $body -NoNewline
            }
        }
    }
}

function Generate-CopilotPrompts {
    param(
        [string]$AgentsDir,
        [string]$PromptsDir
    )
    
    New-Item -ItemType Directory -Path $PromptsDir -Force | Out-Null
    
    $agentFiles = Get-ChildItem -Path "$AgentsDir/devspark.*.agent.md" -File -ErrorAction SilentlyContinue
    
    foreach ($agentFile in $agentFiles) {
        $basename = $agentFile.Name -replace '\.agent\.md$', ''
        $promptFile = Join-Path $PromptsDir "$basename.prompt.md"
        
        $content = @"
---
agent: $basename
---
"@
        Set-Content -Path $promptFile -Value $content
    }
}

function Build-Variant {
    param(
        [string]$Agent,
        [string]$Script
    )
    
    $baseDir = Join-Path $GenReleasesDir "sdd-${Agent}-package-${Script}"
    Write-Host "Building $Agent ($Script) package..."
    New-Item -ItemType Directory -Path $baseDir -Force | Out-Null
    
    # Framework files go into .devspark/ (removable installation)
    $devsparkDir = Join-Path $baseDir ".devspark"
    New-Item -ItemType Directory -Path $devsparkDir -Force | Out-Null
    
    # Constitution is user-owned and never included in release packages.
    # Users create it via /devspark.constitution or /devspark.discover-constitution.
    
    # ADR-001 / Constitution §VI: Always copy both script sets regardless of build variant.
    # The sh|ps variant only controls which {SCRIPT} path gets baked into command files.
    if (Test-Path "scripts") {
        $scriptsDestDir = Join-Path $devsparkDir "scripts"
        New-Item -ItemType Directory -Path $scriptsDestDir -Force | Out-Null

        if (Test-Path "scripts/bash") {
            Copy-Item -Path "scripts/bash" -Destination $scriptsDestDir -Recurse -Force
            Write-Host "Copied scripts/bash -> .devspark/scripts"
        }
        if (Test-Path "scripts/powershell") {
            Copy-Item -Path "scripts/powershell" -Destination $scriptsDestDir -Recurse -Force
            Write-Host "Copied scripts/powershell -> .devspark/scripts"
        }
        
        # Copy any script files that aren't in variant-specific directories
        Get-ChildItem -Path "scripts" -File -ErrorAction SilentlyContinue | ForEach-Object {
            Copy-Item -Path $_.FullName -Destination $scriptsDestDir -Force
        }
    }
    
    # Copy templates (excluding commands directory and vscode-settings.json)
    if (Test-Path "templates") {
        $templatesDestDir = Join-Path $devsparkDir "templates"
        New-Item -ItemType Directory -Path $templatesDestDir -Force | Out-Null
        
        Get-ChildItem -Path "templates" -Recurse -File | Where-Object {
            $_.FullName -notmatch 'templates[/\\]commands[/\\]' -and $_.Name -ne 'vscode-settings.json'
        } | ForEach-Object {
            $relativePath = $_.FullName.Substring((Resolve-Path "templates").Path.Length + 1)
            $destFile = Join-Path $templatesDestDir $relativePath
            $destFileDir = Split-Path $destFile -Parent
            New-Item -ItemType Directory -Path $destFileDir -Force | Out-Null
            Copy-Item -Path $_.FullName -Destination $destFile -Force
        }
        Write-Host "Copied templates -> .devspark/templates"
    }
    
    # Generate canonical command prompts in .devspark/defaults/commands/ (stock, upgrade-safe)
    $canonicalDir = Join-Path $devsparkDir "defaults/commands"
    Generate-CanonicalCommands -OutputDir $canonicalDir -ScriptVariant $Script
    Write-Host "Generated canonical commands -> .devspark/defaults/commands"
    
    $metadata = Get-AgentMetadata -Agent $Agent
    if (-not $metadata -or -not $metadata.release.commands_dir -or -not $metadata.release.extension -or -not $metadata.release.arg_format) {
        Write-Error "Incomplete release metadata for agent '$Agent'"
        exit 1
    }

    $cmdDir = Join-Path $baseDir $metadata.release.commands_dir
    Generate-Shims -Agent $Agent -Extension $metadata.release.extension -ArgFormat $metadata.release.arg_format -OutputDir $cmdDir

    if ($metadata.release.prompt_dir) {
        $promptsDir = Join-Path $baseDir $metadata.release.prompt_dir
        Generate-CopilotPrompts -AgentsDir $cmdDir -PromptsDir $promptsDir
    }

    Copy-AgentSupportFiles -Agent $Agent -BaseDir $baseDir
    
    # Create zip archive
    $zipFile = Join-Path $GenReleasesDir "devspark-template-${Agent}-${Script}-${Version}.zip"
    Compress-Archive -Path "$baseDir/*" -DestinationPath $zipFile -Force
    Write-Host "Created $zipFile"
}

# Define all agents and scripts
$AllAgents = @(Get-RegisteredAgents)
$AllScripts = @('sh', 'ps')

function Normalize-List {
    param([string]$Input)
    
    if ([string]::IsNullOrEmpty($Input)) {
        return @()
    }
    
    # Split by comma or space and remove duplicates while preserving order
    $items = $Input -split '[,\s]+' | Where-Object { $_ } | Select-Object -Unique
    return $items
}

function Validate-Subset {
    param(
        [string]$Type,
        [string[]]$Allowed,
        [string[]]$Items
    )
    
    $ok = $true
    foreach ($item in $Items) {
        if ($item -notin $Allowed) {
            Write-Error "Unknown $Type '$item' (allowed: $($Allowed -join ', '))"
            $ok = $false
        }
    }
    return $ok
}

# Determine agent list
if (-not [string]::IsNullOrEmpty($Agents)) {
    $AgentList = Normalize-List -Input $Agents
    if (-not (Validate-Subset -Type 'agent' -Allowed $AllAgents -Items $AgentList)) {
        exit 1
    }
} else {
    $AgentList = $AllAgents
}

# Determine script list
if (-not [string]::IsNullOrEmpty($Scripts)) {
    $ScriptList = Normalize-List -Input $Scripts
    if (-not (Validate-Subset -Type 'script' -Allowed $AllScripts -Items $ScriptList)) {
        exit 1
    }
} else {
    $ScriptList = $AllScripts
}

Write-Host "Agents: $($AgentList -join ', ')"
Write-Host "Scripts: $($ScriptList -join ', ')"

# Build all variants
foreach ($agent in $AgentList) {
    foreach ($script in $ScriptList) {
        Build-Variant -Agent $agent -Script $script
    }
}

Write-Host "`nArchives in ${GenReleasesDir}:"
Get-ChildItem -Path $GenReleasesDir -Filter "devspark-template-*-${Version}.zip" | ForEach-Object {
    Write-Host "  $($_.Name)"
}
