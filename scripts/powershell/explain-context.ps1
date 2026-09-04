#!/usr/bin/env pwsh
#requires -Version 7.0
<#
.SYNOPSIS
    Gather bounded, read-only topic context for /devspark.explain.
#>
[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$DryRun,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$TopicArgs
)

. (Join-Path $PSScriptRoot 'common.ps1')

$topicParts = [System.Collections.Generic.List[string]]::new()
foreach ($arg in @($TopicArgs)) {
    if ($arg -eq '--dry-run') { $DryRun = $true; continue }
    if ($arg -in @('--json', '-Json')) { continue }
    $topicParts.Add($arg)
}

$topic = ($topicParts -join ' ').Trim()
if (-not $topic) {
    Write-Error 'A free-text topic or question is required.'
    exit 2
}

$stopWords = @(
    'how', 'what', 'where', 'when', 'why', 'who', 'the', 'and', 'are', 'was',
    'were', 'does', 'did', 'done', 'for', 'from', 'into', 'with', 'this',
    'that', 'work', 'works', 'implemented', 'implementation'
)
$terms = @(
    [regex]::Matches($topic.ToLowerInvariant(), '[\p{L}\p{N}_-]+') |
        ForEach-Object { $_.Value } |
        Where-Object { $_.Length -ge 3 -and $_ -notin $stopWords } |
        Select-Object -Unique
)
if ($terms.Count -eq 0) { $terms = @($topic.ToLowerInvariant()) }

$repoRoot = Get-RepoRoot
$testPattern = '(^|[/\\])(tests?|specs?)([/\\]|$)|(^|[/\\])(test_[^/\\]*|[^/\\]*(_test|\.test|_spec|\.spec)\.)'
$codeExtensions = @(
    '.py', '.pyi', '.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.cs',
    '.java', '.go', '.rs', '.rb', '.php', '.sh', '.ps1', '.json', '.yaml',
    '.yml', '.toml', '.xml', '.csproj', '.fsproj', '.mod'
)

if (-not (Get-Command rg -ErrorAction SilentlyContinue)) {
    Write-Error 'explain-context requires ripgrep (rg).'
    exit 2
}

function Test-TopicMatch {
    param([System.IO.FileInfo]$File, [string]$RelativePath)
    foreach ($term in $terms) {
        $needles = @($term)
        if ($term.Length -ge 8) { $needles += $term.Substring(0, 4) }
        foreach ($needle in $needles) {
            if ($RelativePath.IndexOf($needle, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
                return $true
            }
        }
    }
    try {
        foreach ($term in $terms) {
            $needles = @($term)
            if ($term.Length -ge 8) { $needles += $term.Substring(0, 4) }
            foreach ($needle in $needles) {
                if (Select-String -LiteralPath $File.FullName -SimpleMatch $needle -Quiet -ErrorAction SilentlyContinue) {
                    return $true
                }
            }
        }
    } catch { }
    return $false
}

$knowledgeMatches = [System.Collections.Generic.List[string]]::new()
$knowledgeRoot = Join-Path $repoRoot '.knowledge'
if (Test-Path -LiteralPath $knowledgeRoot) {
    Push-Location $repoRoot
    try {
        $knowledgeFiles = @(
            & rg --files --hidden `
                --glob '!.knowledge/overrides/**' `
                --glob '!.knowledge/ontology/*.generated.md' `
                -- '.knowledge' 2>$null
        )
    } finally {
        Pop-Location
    }
    foreach ($relative in ($knowledgeFiles | Sort-Object -Unique)) {
        if ($knowledgeMatches.Count -ge 60) { break }
        $file = Get-Item -LiteralPath (Join-Path $repoRoot $relative) -ErrorAction SilentlyContinue
        if ($file -and (Test-TopicMatch -File $file -RelativePath $relative)) {
            $knowledgeMatches.Add($relative.Replace('\', '/'))
        }
    }
}

$codeMatches = [System.Collections.Generic.List[string]]::new()
$testMatches = [System.Collections.Generic.List[string]]::new()
# Explicitly exclude .archive, .devspark.work, and .documentation from retrieval.
Push-Location $repoRoot
try {
    $repoFiles = @(
        & rg --files --hidden `
            --glob '!**/.git/**' `
            --glob '!**/.archive/**' `
            --glob '!**/.devspark.work/**' `
            --glob '!**/.devspark/**' `
            --glob '!**/.knowledge/**' `
            --glob '!**/.documentation/**' `
            --glob '!**/node_modules/**' `
            --glob '!**/.venv/**' `
            --glob '!**/venv/**' `
            --glob '!**/bin/**' `
            --glob '!**/obj/**' `
            --glob '!**/dist/**' `
            --glob '!**/build/**' `
            --glob '!**/.pytest_cache/**' `
            -- '.' 2>$null
    )
} finally {
    Pop-Location
}

foreach ($relative in ($repoFiles | Sort-Object -Unique)) {
    if ($codeMatches.Count -ge 80 -and $testMatches.Count -ge 40) { break }
    $file = Get-Item -LiteralPath (Join-Path $repoRoot $relative) -ErrorAction SilentlyContinue
    if (-not $file -or $file.Extension.ToLowerInvariant() -notin $codeExtensions) { continue }
    $normalized = $relative.Replace('\', '/')
    if (-not (Test-TopicMatch -File $file -RelativePath $normalized)) { continue }
    if ($normalized -match $testPattern) {
        if ($testMatches.Count -lt 40) { $testMatches.Add($normalized) }
    } elseif ($codeMatches.Count -lt 80) {
        $codeMatches.Add($normalized)
    }
}

$result = [ordered]@{
    timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    repo_root = $repoRoot
    topic = $topic
    terms = @($terms)
    dry_run = [bool]$DryRun
    knowledge_matches = @($knowledgeMatches)
    code_matches = @($codeMatches)
    test_matches = @($testMatches)
    counts = [ordered]@{
        knowledge = $knowledgeMatches.Count
        code = $codeMatches.Count
        tests = $testMatches.Count
    }
    constraints = [ordered]@{
        read_only = $true
        archive_ignored = $true
        work_products_ignored = $true
    }
}

$result | ConvertTo-Json -Depth 6
