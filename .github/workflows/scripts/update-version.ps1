#!/usr/bin/env pwsh
#requires -Version 7.0
<#
.SYNOPSIS
    Update version in pyproject.toml
.DESCRIPTION
    Update-version.ps1 - Update the version field in pyproject.toml (for release artifacts only)
.PARAMETER Version
    The version to set (e.g., v1.0.0-markhazleton.1)
.EXAMPLE
    .\update-version.ps1 -Version "v1.0.0-markhazleton.1"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

$ErrorActionPreference = 'Stop'

# Remove 'v' prefix for Python versioning
$pythonVersion = $Version -replace '^v', ''

$pyprojectPath = "pyproject.toml"

if (Test-Path $pyprojectPath) {
    # Read the file
    $content = Get-Content $pyprojectPath -Raw
    
    # Replace the version
    $content = $content -replace 'version\s*=\s*"[^"]*"', "version = `"$pythonVersion`""
    
    # Write back to file
    $content | Set-Content $pyprojectPath -NoNewline
    
    Write-Host "Updated pyproject.toml version to $pythonVersion (for release artifacts only)"
} else {
    Write-Warning "pyproject.toml not found, skipping version update"
}
