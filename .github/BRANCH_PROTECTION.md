# Branch Protection Setup Guide

This document describes the recommended branch protection rules for the `main` branch to prevent accidental releases and maintain code quality.

## Recommended Branch Protection Rules

### Navigate to Settings
1. Go to your repository on GitHub
2. Click **Settings** → **Branches**
3. Under "Branch protection rules", click **Add rule**

### Protection Rule Configuration

**Branch name pattern:** `main`

#### Protect matching branches

✅ **Require a pull request before merging**
- Require approvals: `1` (or more if you have collaborators)
- Dismiss stale pull request approvals when new commits are pushed
- Require review from Code Owners (optional - if you set up CODEOWNERS)

✅ **Require status checks to pass before merging**
- Require branches to be up to date before merging
- Status checks to require:
  - `markdownlint` (from lint workflow)
  - `build` (from docs workflow - if DocFX build is critical)

✅ **Require conversation resolution before merging**
- Ensures all PR comments are addressed

❌ **Do not allow bypassing the above settings** (unless you need admin override)

#### Additional Recommendations

✅ **Require signed commits** (optional but recommended for security)

✅ **Require linear history** (prevents merge commits, keeps history clean)

✅ **Lock branch** (only if you want to completely freeze the branch)

### Why These Rules?

1. **Pull Request Requirement**: Prevents direct pushes to `main`, which would trigger immediate releases
2. **Status Checks**: Ensures code quality via linting before merging
3. **Conversation Resolution**: Encourages thorough PR reviews
4. **Up-to-date Branches**: Prevents merge conflicts and ensures tests run on latest code

## Alternative: Development Branch Strategy

If you want more control over releases, consider this workflow:

```
develop (default branch) → main (protected, releases only)
```

**Setup:**
1. Create a `develop` branch: `git checkout -b develop && git push -u origin develop`
2. Set `develop` as default branch in repo settings
3. Apply strict protection rules to `main` (no direct commits)
4. Only merge to `main` when ready to release

**Benefits:**
- `main` only contains released code
- Release workflow only triggers when you explicitly merge
- More control over when versions are published

## Testing Branch Protection

After setting up protection rules:

1. Try to push directly to `main`: `git push origin main`
   - Should be blocked with: `remote: error: GH006: Protected branch update failed`

2. Create a PR instead:
   ```bash
   git checkout -b test-protection
   git commit --allow-empty -m "Test branch protection"
   git push -u origin test-protection
   # Then create PR via GitHub UI
   ```

3. Verify status checks run before merge is allowed

## Current Versioning Strategy

This fork uses custom versioning to distinguish from upstream:
- Format: `v1.0.0-markhazleton.X`
- First release: `v1.0.0-markhazleton.1`
- Subsequent releases increment the fourth number

The versioning script automatically handles this format and distinguishes fork releases from upstream releases.

---

**Note:** Branch protection rules only affect pushes through Git. GitHub Actions workflows running with `GITHUB_TOKEN` can still push to protected branches if they have write permissions.
