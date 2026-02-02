# Local Testing Scripts (PowerShell)

This directory contains PowerShell versions of the GitHub Actions workflow scripts for local testing on Windows.

## Prerequisites

- PowerShell 7.0 or later
- Git installed and available in PATH
- GitHub CLI (`gh`) installed for release operations

## Scripts Overview

| Script | Purpose | Parameters |
|--------|---------|------------|
| `get-next-version.ps1` | Calculate next version tag | None |
| `generate-release-notes.ps1` | Generate release notes from commits | `-NewVersion`, `-LastTag` |
| `check-release-exists.ps1` | Check if release exists on GitHub | `-Version` |
| `create-github-release.ps1` | Create GitHub release with packages | `-Version` |
| `update-version.ps1` | Update pyproject.toml version | `-Version` |
| `create-release-packages.ps1` | Create all agent template packages | `-Version` |

## Testing the Release Process Locally

### 1. Check What Version Will Be Generated

```powershell
# From repository root
.\.github\workflows\scripts\get-next-version.ps1
```

**Expected output:**

```text
Latest tag: v0.0.90
New version will be: v1.0.0-spark.1
```

### 2. Generate Release Notes

```powershell
.\.github\workflows\scripts\generate-release-notes.ps1 `
    -NewVersion "v1.0.0-spark.1" `
    -LastTag "v0.0.90"
```

This creates `release_notes.md` with your fork-specific branding.

### 3. Check If Release Already Exists

```powershell
.\.github\workflows\scripts\check-release-exists.ps1 `
    -Version "v1.0.0-spark.1"
```

### 4. Create Release Packages (Local Test)

```powershell
.\.github\workflows\scripts\create-release-packages.ps1 `
    -Version "v1.0.0-spark.1"
```

This creates all agent-specific ZIP packages in `.genreleases/` directory.

### 5. Update pyproject.toml Version

```powershell
.\.github\workflows\scripts\update-version.ps1 `
    -Version "v1.0.0-spark.1"
```

**Note:** This is typically only needed for PyPI releases.

### 6. Create GitHub Release (Requires `gh` CLI)

```powershell
# Ensure you're authenticated with gh CLI
gh auth status

# Create the release
.\.github\workflows\scripts\create-github-release.ps1 `
    -Version "v1.0.0-spark.1"
```

## Full Local Test Workflow

To test the entire release process locally without actually creating a release:

```powershell
# 1. Get version
$version = (.\.github\workflows\scripts\get-next-version.ps1 | Select-String "New version will be: (.+)").Matches.Groups[1].Value

# 2. Get latest tag
$latestTag = git describe --tags --abbrev=0

# 3. Generate release notes
.\.github\workflows\scripts\generate-release-notes.ps1 -NewVersion $version -LastTag $latestTag

# 4. Check if release exists (optional)
.\.github\workflows\scripts\check-release-exists.ps1 -Version $version

# 5. Create packages (this is safe - just creates local files)
.\.github\workflows\scripts\create-release-packages.ps1 -Version $version

# 6. Verify packages were created
Get-ChildItem .genreleases -Filter "*$version.zip"

Write-Host "`nRelease testing complete! Review .genreleases/ and release_notes.md"
Write-Host "To actually create the release, run:"
Write-Host ".\.github\workflows\scripts\create-github-release.ps1 -Version $version"
```

## Notes

- **GitHub Actions uses bash scripts** (`.sh` files) on `ubuntu-latest` runners
- **PowerShell scripts** (`.ps1` files) are for local Windows testing only
- Both versions are kept in sync for the same functionality
- The versioning format `v1.0.0-spark.X` distinguishes Spark releases from upstream

## Differences from GitHub Actions

When running locally vs in GitHub Actions:

| Feature | GitHub Actions | Local PowerShell |
|---------|---------------|------------------|
| `$GITHUB_OUTPUT` | Sets workflow variables | Ignored (no effect) |
| Authentication | Automatic via `GITHUB_TOKEN` | Requires `gh auth login` |
| Triggering | Automatic on push to `main` | Manual execution |
| Environment | Ubuntu Linux | Windows |

## Troubleshooting

### "execution of scripts is disabled on this system"

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### "gh: command not found"

- Install GitHub CLI: `winget install GitHub.cli`
- Or download from: <https://cli.github.com/>

### "Git tag not found"

- Ensure you have at least one commit
- The script will default to `v0.0.0` if no tags exist
- For Spark versioning, any non-Spark tag triggers `v1.0.0-spark.1`
