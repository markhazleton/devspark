# Implementation Plan: `/speckit.pr-review` Command

**Version**: 1.0  
**Date**: 2026-01-25  
**Status**: Ready for Implementation

---

## Overview

Create a new speckit command that performs context-aware pull request reviews using the project constitution and GitHub Copilot's capabilities. This command evaluates GitHub PR changes against established project principles and generates actionable feedback reports.

### Key Design Principles

1. **Constitution-Only Requirement**: Only requires `/.documentation/memory/constitution.md` - no spec/plan/tasks needed
2. **Repository-Wide**: Works for any PR in the repository, not tied to specific features
3. **Branch-Agnostic**: Can review PRs targeting any branch (main, develop, feature branches)
4. **Suggestion-Only**: Generates recommendations without making code changes
5. **Persistent Reviews**: Stores reviews in `/.documentation/specs/pr-review/pr-{id}.md` with metadata

---

## Phase 1: Command Template Creation

### 1.1 Create Core Command File

**File**: `templates/commands/pr-review.md`

```markdown
---
description: Perform constitution-aware pull request review with actionable feedback for any PR in the repository
handoffs:
  - label: View Review History
    agent: speckit.pr-review
    prompt: Show me previous PR reviews
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Overview

This command reviews GitHub Pull Requests against the project constitution. It works for **any PR in the repository** regardless of feature branch or target branch. Reviews are stored in `/.documentation/specs/pr-review/pr-{id}.md` for historical reference.

**IMPORTANT**: This command **only provides suggestions** - it does not make any code changes.

## Prerequisites

- Project constitution at `/.documentation/memory/constitution.md` (REQUIRED)
- GitHub repository with PR context
- GitHub CLI (`gh`) installed (recommended) or manual PR number

## Outline

### 1. Initialize Review Context

Run repository detection and PR context extraction:
- Detect if running in GitHub PR environment
- Extract PR number from user input or GitHub context
- Verify constitution exists at `/.documentation/memory/constitution.md`
- Create `/.documentation/specs/pr-review/` directory if it doesn't exist

**PR Number Detection Priority**:
1. User explicitly provides PR number: `/speckit.pr-review #123` or `/speckit.pr-review 123`
2. GitHub environment variables: `GITHUB_PR_NUMBER`, `PR_NUMBER`
3. Current branch PR detection via `gh` CLI
4. Prompt user if unable to detect

### 2. Extract PR Information

Use GitHub CLI (`gh pr view {PR_NUMBER} --json`) to fetch:
- **PR Metadata**: title, number, author, state, created/updated dates
- **Branch Info**: source branch (head), target branch (base)
- **Commit Info**: HEAD commit SHA, commit count, commit messages
- **Files Changed**: List of modified files with change counts
- **PR Body**: Description text for context
- **Diff**: Full diff for analysis

**Fallback** (if `gh` unavailable):
- Use git commands: `git diff origin/{base}...origin/{head}`
- Extract info from git log and branch info
- Prompt user for missing metadata

### 3. Load Review Artifacts

**REQUIRED**:
- Constitution from `/.documentation/memory/constitution.md`
  - Extract core principles
  - Identify MUST/SHOULD requirements
  - Note version and last amended date

**OPTIONAL** (if available):
- Feature spec from `/.documentation/specs/{feature}/spec.md` (if PR branch matches feature pattern)
- Implementation plan from `/.documentation/specs/{feature}/plan.md`
- Match PR changes to specific feature context if applicable

### 4. Perform Constitution-Based Review

For each principle in the constitution:

#### A. Compliance Check
- Review changed files against principle requirements
- Identify violations, partial compliance, or full compliance
- Note specific file/line references for issues

#### B. Severity Classification
- **CRITICAL**: Violates mandatory (MUST) principle
- **HIGH**: Violates recommended (SHOULD) principle significantly
- **MEDIUM**: Partial compliance, improvement needed
- **LOW**: Style/minor improvements suggested

#### C. Evidence Collection
- Quote relevant code sections
- Reference constitution section
- Explain rationale for finding

### 5. Additional Review Dimensions

#### Security Analysis
- Check for hardcoded secrets/credentials
- Validate input sanitization
- Review authentication/authorization changes
- Identify potential vulnerability patterns

#### Code Quality Assessment
- Naming conventions per constitution
- Error handling patterns
- Code organization and structure
- Duplication or anti-patterns

#### Testing Validation (if TDD principle exists)
- Verify test coverage for changes
- Check if tests were written first
- Validate test quality and completeness

#### Documentation Review
- Check if changes are documented
- Verify README/docs updates if needed
- Review code comments for clarity

### 6. Generate Review Report

Create comprehensive report at `/.documentation/specs/pr-review/pr-{id}.md`:

```markdown
# Pull Request Review: [PR_TITLE]

## Review Metadata

- **PR Number**: #[PR_NUMBER]
- **Source Branch**: [HEAD_BRANCH]
- **Target Branch**: [BASE_BRANCH]
- **Review Date**: [YYYY-MM-DD HH:MM:SS UTC]
- **Reviewed Commit**: [COMMIT_SHA]
- **Reviewer**: speckit.pr-review
- **Constitution Version**: [VERSION]

## PR Summary

- **Author**: [PR_AUTHOR]
- **Created**: [PR_CREATED_DATE]
- **Status**: [OPEN/CLOSED/MERGED]
- **Files Changed**: [COUNT]
- **Commits**: [COUNT]

## Executive Summary

- ✅ **Constitution Compliance**: [PASS/FAIL] ([X]/[Y] principles checked)
- 🔒 **Security**: [#] issues found
- 📊 **Code Quality**: [#] recommendations
- 🧪 **Testing**: [PASS/FAIL/N/A]
- 📝 **Documentation**: [PASS/FAIL/N/A]

**Approval Recommendation**: [APPROVE/REQUEST CHANGES/REJECT]

## Critical Issues (Blocking)

| ID | Principle | File:Line | Issue | Recommendation |
|----|-----------|-----------|-------|----------------|
| C1 | [Principle Name] | src/api.ts:45 | [Specific violation] | [Specific action] |

## High Priority Issues

[Similar table format]

## Medium Priority Suggestions

[Similar table format]

## Low Priority Improvements

[Similar table format]

## Constitution Alignment Details

| Principle | Status | Evidence | Notes |
|-----------|--------|----------|-------|
| [Name] | ✅ Pass | [File references] | [Explanation] |
| [Name] | ❌ Fail | [File references] | [Explanation] |
| [Name] | ⚠️ Partial | [File references] | [Explanation] |
| [Name] | ⏭️ N/A | - | Not applicable to this PR |

## Security Checklist

- [ ] No hardcoded secrets or credentials
- [ ] Input validation present where needed
- [ ] Authentication/authorization checks appropriate
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] Dependencies reviewed for vulnerabilities

## Code Quality Assessment

### Strengths
- [Positive aspects of the PR]

### Areas for Improvement
- [Specific improvement suggestions]

## Testing Coverage

**Status**: [ADEQUATE/INADEQUATE/N/A]

[Details about test coverage if TDD principle exists]

## Documentation Status

**Status**: [ADEQUATE/INADEQUATE/N/A]

[Details about documentation if principle exists]

## Changed Files Summary

| File | Changes | Type | Constitution Issues |
|------|---------|------|---------------------|
| src/api.ts | +45 -12 | Modified | 2 issues |
| tests/api.test.ts | +120 -0 | Added | None |

## Detailed Findings by File

### src/api.ts

**Lines 45-67**: [Specific issue description]
- **Principle Violated**: [Principle name]
- **Severity**: HIGH
- **Recommendation**: [Specific action]

[Continue for each significant finding]

## Next Steps

1. **Immediate Actions** (Required before merge):
   - [ ] [Action 1]
   - [ ] [Action 2]

2. **Recommended Improvements** (Should address):
   - [ ] [Improvement 1]
   - [ ] [Improvement 2]

3. **Future Considerations** (Optional):
   - [ ] [Enhancement 1]
   - [ ] [Enhancement 2]

## Approval Decision

**Recommendation**: ⚠️ **CHANGES REQUESTED**

**Reasoning**: 
[Explain the decision based on findings. If CRITICAL issues exist, these must be resolved. If only MEDIUM/LOW, approval may be conditional.]

**Estimated Rework Time**: [X hours/days]

---

*Review generated by speckit.pr-review | Constitution-driven code review*
*To update this review after changes: `/speckit.pr-review #[PR_NUMBER]`*
```

### 7. Handle Review Updates

If `pr-{id}.md` already exists:
- Load previous review
- Compare previous commit SHA vs current commit SHA
- If different:
  - Append new review section to file (don't replace)
  - Mark as "Updated Review"
  - Note what changed since last review
- If same commit:
  - Update existing review in place
  - Preserve creation date, update review date

**Multi-Review Format** (when PR updated):
```markdown
# Pull Request Review: [PR_TITLE]

[Latest review content here]

---

## Previous Review History

### Review 2: 2026-01-24 10:30:00 UTC
**Commit**: abc123def

[Previous review summary]

### Review 1: 2026-01-23 14:15:00 UTC
**Commit**: 789xyz012

[First review summary]
```

### 8. Output Summary

Display to user:
- Review completion confirmation
- Path to saved review file
- Executive summary of findings
- Approval recommendation
- Next steps

**Example Output**:
```
✅ PR Review Complete!

📄 Review saved: /.documentation/specs/pr-review/pr-123.md
🔍 Reviewed commit: abc123def456
📅 Review date: 2026-01-25 15:30:00 UTC

Executive Summary:
- ❌ 2 Critical issues found
- ⚠️  4 High priority suggestions
- ℹ️  7 Medium priority improvements

Recommendation: REQUEST CHANGES

Critical issues must be resolved before merge:
- C1: TDD principle violated (no tests for new API endpoints)
- C2: Security issue (hardcoded API key in config)

View full review: /.documentation/specs/pr-review/pr-123.md
```

## Guidelines

### Constitution Authority

The constitution is **non-negotiable**. All findings must:
- Reference specific constitution section
- Explain how change violates/complies with principle
- Use constitution language (MUST/SHOULD) for severity

### Evidence-Based Feedback

All issues must include:
- **Specific file and line reference** (not "multiple files")
- **Code snippet quote** showing the issue
- **Constitution reference** explaining why it's an issue
- **Actionable recommendation** with specific fix

### Graceful Handling

**If constitution missing**:
- Error message with clear guidance
- Explain that constitution is required
- Show how to create one with `/speckit.constitution`

**If PR not found**:
- Clear error message
- Show how to specify PR number
- Suggest checking `gh` CLI installation

**If no GitHub context**:
- Offer manual mode with PR number input
- Guide user through providing PR details

### Review Objectivity

- Focus on facts, not opinions
- Reference constitution for all judgments
- Avoid subjective terms ("ugly", "bad")
- Use constitution-defined criteria

## Technical Notes

### GitHub CLI Commands

```bash
# Fetch PR information
gh pr view {PR_NUMBER} --json number,title,body,state,author,headRefName,baseRefName,commits,files,createdAt,updatedAt

# Get PR diff
gh pr diff {PR_NUMBER}

# Get HEAD commit SHA
gh pr view {PR_NUMBER} --json commits --jq '.commits[-1].oid'

# Check if PR exists
gh pr view {PR_NUMBER} --json number 2>/dev/null
```

### Git Fallback Commands

```bash
# Get current PR branch
git rev-parse --abbrev-ref HEAD

# Get target branch (common patterns)
git show-ref --verify refs/heads/main || git show-ref --verify refs/heads/master

# Get diff
git diff origin/{base}...origin/{head}

# Get HEAD commit
git rev-parse HEAD

# Get commit messages
git log origin/{base}..origin/{head} --oneline
```

### Directory Structure

```
.documentation/specs/
  pr-review/
    pr-1.md
    pr-2.md
    pr-123.md
    ...
```

Created automatically on first review, persists across reviews.
```

### 1.2 Review Report Metadata Schema

**Required Fields**:
- `PR Number`: Integer
- `Source Branch`: String
- `Target Branch`: String
- `Review Date`: ISO 8601 datetime with UTC
- `Reviewed Commit`: Git SHA (full or abbreviated)
- `Constitution Version`: String (from constitution file)

**Optional Fields**:
- `Feature Context`: If PR maps to a spec feature
- `Previous Review Date`: If updating existing review
- `Changes Since Last Review`: Summary if re-reviewing

---

## Phase 2: Script Enhancement

### 2.1 Create PR Context Script

**New File**: `scripts/bash/get-pr-context.sh`

```bash
#!/usr/bin/env bash
# Extract PR context for review

set -e
set -u
set -o pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PR_NUMBER="${1:-}"

# Try to detect PR number if not provided
if [[ -z "$PR_NUMBER" ]]; then
    # Check environment variables
    if [[ -n "${GITHUB_PR_NUMBER:-}" ]]; then
        PR_NUMBER="$GITHUB_PR_NUMBER"
    elif [[ -n "${PR_NUMBER:-}" ]]; then
        PR_NUMBER="$PR_NUMBER"
    else
        # Try to get from current branch using gh CLI
        if command -v gh &>/dev/null; then
            PR_NUMBER=$(gh pr view --json number --jq '.number' 2>/dev/null || echo "")
        fi
    fi
fi

# Validate PR number
if [[ -z "$PR_NUMBER" ]]; then
    echo "ERROR: Unable to detect PR number" >&2
    echo "Usage: $0 <PR_NUMBER>" >&2
    exit 1
fi

# Check if gh CLI is available
if ! command -v gh &>/dev/null; then
    echo "ERROR: GitHub CLI (gh) is required but not installed" >&2
    echo "Install from: https://cli.github.com/" >&2
    exit 1
fi

# Fetch PR data
PR_DATA=$(gh pr view "$PR_NUMBER" --json number,title,body,state,author,headRefName,baseRefName,commits,files,createdAt,updatedAt 2>/dev/null)

if [[ -z "$PR_DATA" ]]; then
    echo "ERROR: PR #$PR_NUMBER not found" >&2
    exit 1
fi

# Extract commit SHA
COMMIT_SHA=$(echo "$PR_DATA" | jq -r '.commits[-1].oid')

# Get PR diff
PR_DIFF=$(gh pr diff "$PR_NUMBER" 2>/dev/null || echo "")

# Build JSON output
cat <<EOF
{
  "REPO_ROOT": "$REPO_ROOT",
  "PR_CONTEXT": {
    "enabled": true,
    "pr_number": $(echo "$PR_DATA" | jq '.number'),
    "pr_title": $(echo "$PR_DATA" | jq -r '.title' | jq -Rs .),
    "pr_body": $(echo "$PR_DATA" | jq -r '.body // ""' | jq -Rs .),
    "pr_state": $(echo "$PR_DATA" | jq -r '.state' | jq -Rs .),
    "pr_author": $(echo "$PR_DATA" | jq -r '.author.login' | jq -Rs .),
    "source_branch": $(echo "$PR_DATA" | jq -r '.headRefName' | jq -Rs .),
    "target_branch": $(echo "$PR_DATA" | jq -r '.baseRefName' | jq -Rs .),
    "commit_sha": "$COMMIT_SHA",
    "commit_count": $(echo "$PR_DATA" | jq '.commits | length'),
    "files_changed": $(echo "$PR_DATA" | jq '[.files[].path]'),
    "created_at": $(echo "$PR_DATA" | jq -r '.createdAt' | jq -Rs .),
    "updated_at": $(echo "$PR_DATA" | jq -r '.updatedAt' | jq -Rs .),
    "diff_available": $([ -n "$PR_DIFF" ] && echo "true" || echo "false")
  },
  "CONSTITUTION_PATH": "$REPO_ROOT/.documentation/memory/constitution.md",
  "REVIEW_DIR": "$REPO_ROOT/.documentation/specs/pr-review"
}
EOF
```

**New File**: `scripts/powershell/get-pr-context.ps1`

```powershell
#!/usr/bin/env pwsh
# Extract PR context for review

param(
    [Parameter(Position=0)]
    [string]$PrNumber
)

$ErrorActionPreference = "Stop"

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path "$scriptPath\..\..")

# Try to detect PR number if not provided
if ([string]::IsNullOrWhiteSpace($PrNumber)) {
    # Check environment variables
    if ($env:GITHUB_PR_NUMBER) {
        $PrNumber = $env:GITHUB_PR_NUMBER
    } elseif ($env:PR_NUMBER) {
        $PrNumber = $env:PR_NUMBER
    } else {
        # Try to get from current branch using gh CLI
        if (Get-Command gh -ErrorAction SilentlyContinue) {
            try {
                $prData = gh pr view --json number 2>$null | ConvertFrom-Json
                $PrNumber = $prData.number
            } catch {}
        }
    }
}

# Validate PR number
if ([string]::IsNullOrWhiteSpace($PrNumber)) {
    Write-Error "Unable to detect PR number. Usage: $($MyInvocation.MyCommand.Name) <PR_NUMBER>"
    exit 1
}

# Check if gh CLI is available
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "GitHub CLI (gh) is required but not installed. Install from: https://cli.github.com/"
    exit 1
}

# Fetch PR data
try {
    $prDataJson = gh pr view $PrNumber --json number,title,body,state,author,headRefName,baseRefName,commits,files,createdAt,updatedAt 2>$null
    $prData = $prDataJson | ConvertFrom-Json
} catch {
    Write-Error "PR #$PrNumber not found"
    exit 1
}

# Extract commit SHA
$commitSha = $prData.commits[-1].oid

# Get PR diff
try {
    $prDiff = gh pr diff $PrNumber 2>$null
    $diffAvailable = $true
} catch {
    $prDiff = ""
    $diffAvailable = $false
}

# Get files changed
$filesChanged = $prData.files | ForEach-Object { $_.path }

# Build JSON output
$output = @{
    REPO_ROOT = $repoRoot.Path
    PR_CONTEXT = @{
        enabled = $true
        pr_number = $prData.number
        pr_title = $prData.title
        pr_body = $prData.body ?? ""
        pr_state = $prData.state
        pr_author = $prData.author.login
        source_branch = $prData.headRefName
        target_branch = $prData.baseRefName
        commit_sha = $commitSha
        commit_count = $prData.commits.Count
        files_changed = $filesChanged
        created_at = $prData.createdAt
        updated_at = $prData.updatedAt
        diff_available = $diffAvailable
    }
    CONSTITUTION_PATH = Join-Path $repoRoot.Path ".documentation\memory\constitution.md"
    REVIEW_DIR = Join-Path $repoRoot.Path ".documentation\specs\pr-review"
} | ConvertTo-Json -Depth 10 -Compress

Write-Output $output
```

---

## Phase 3: Multi-Agent Command Generation

### 3.1 GitHub Copilot

**File**: `.github/agents/pr-review.md`

```markdown
---
description: "Perform constitution-aware pull request review"
mode: speckit.pr-review
---

[Same content as templates/commands/pr-review.md]
```

### 3.2 Claude Code

**File**: `.claude/commands/pr-review.md`

```markdown
---
description: Perform constitution-aware pull request review with actionable feedback
---

[Same content as templates/commands/pr-review.md with SCRIPT placeholders]
```

### 3.3 Other Agents

Use standard Markdown format for:
- Cursor (`.cursor/commands/pr-review.md`)
- opencode (`.opencode/command/pr-review.md`)
- Windsurf (`.windsurf/workflows/pr-review.md`)
- Amp (`.agents/commands/pr-review.md`)
- Others following the pattern

Use TOML format for:
- Gemini (`.gemini/commands/pr-review.toml`)
- Qwen (`.qwen/commands/pr-review.toml`)

---

## Phase 4: Documentation

### 4.1 Update README.md

Add to command table:

```markdown
| `/speckit.pr-review` | Review PRs against constitution | After PR creation, before merge |
```

Add usage examples:

```markdown
### PR Review Command

The `/speckit.pr-review` command performs constitution-based code reviews on GitHub Pull Requests:

```bash
# Review current PR (auto-detect)
/speckit.pr-review

# Review specific PR by number
/speckit.pr-review #123
/speckit.pr-review 123

# Re-review after changes
/speckit.pr-review #123
```

**Key Features**:
- Works for any PR in the repository
- Only requires project constitution
- Stores reviews in `/.documentation/specs/pr-review/pr-{id}.md`
- Tracks commit SHA and review timestamp
- Updates existing reviews if PR changes
- Provides actionable, line-specific feedback
```

### 4.2 Create Usage Guide

**File**: `.documentation/pr-review-usage.md`

```markdown
# PR Review Command Guide

## Overview

The `/speckit.pr-review` command performs automated, constitution-driven code reviews for GitHub Pull Requests. It evaluates code changes against your project's established principles and generates detailed feedback reports.

## Prerequisites

- Project constitution at `/.documentation/memory/constitution.md`
- GitHub repository
- GitHub CLI (`gh`) installed and authenticated
- Pull request in the repository

## Basic Usage

### Review Current PR

If you're working on a PR branch:

```bash
/speckit.pr-review
```

The command will auto-detect the PR associated with your current branch.

### Review Specific PR

To review any PR by number:

```bash
/speckit.pr-review #123
# or
/speckit.pr-review 123
```

### Re-Review After Changes

When a PR is updated with new commits:

```bash
/speckit.pr-review #123
```

The command will:
- Detect if the commit has changed
- Append an updated review to the existing file
- Show what changed since the last review

## Review Output

Reviews are saved to `/.documentation/specs/pr-review/pr-{id}.md` with:
- **Metadata**: PR details, commit SHA, review timestamp
- **Executive Summary**: Overall assessment and recommendation
- **Categorized Issues**: Critical, High, Medium, Low priority
- **Constitution Alignment**: Principle-by-principle evaluation
- **Security Checklist**: Security-specific concerns
- **Next Steps**: Actionable recommendations

## Understanding Review Severity

- **CRITICAL**: Violates mandatory (MUST) constitution principle - must fix before merge
- **HIGH**: Violates recommended (SHOULD) principle - strongly recommend fixing
- **MEDIUM**: Partial compliance or improvement opportunity
- **LOW**: Style suggestions or minor improvements

## Working with Reviews

### Viewing Past Reviews

All PR reviews are stored in `/.documentation/specs/pr-review/` directory:

```bash
ls .documentation/specs/pr-review/
# pr-1.md
# pr-2.md
# pr-123.md
```

### Review History

When a PR is reviewed multiple times, the file contains:
- Latest review at the top
- Previous review history at the bottom
- Commit SHA for each review
- Timestamp for each review

### Acting on Feedback

1. Read the review report in `/.documentation/specs/pr-review/pr-{id}.md`
2. Address CRITICAL issues first (required for merge)
3. Consider HIGH priority suggestions strongly
4. Address MEDIUM/LOW as time permits
5. Re-run `/speckit.pr-review` to verify fixes

## Common Scenarios

### First-Time Setup

If `/speckit.pr-review` fails because constitution doesn't exist:

```bash
/speckit.constitution Create project principles for code quality, testing, and security
```

Then retry the review.

### No GitHub CLI

If `gh` CLI is not installed:

```bash
# Install GitHub CLI
# macOS
brew install gh

# Windows
winget install --id GitHub.cli

# Linux
# See: https://github.com/cli/cli#installation

# Authenticate
gh auth login
```

### PR Not Auto-Detected

If the command can't detect your PR:

```bash
# Find your PR number
gh pr list

# Review it explicitly
/speckit.pr-review #<number>
```

## Best Practices

1. **Review Early**: Run reviews when PR is created, not just before merge
2. **Review Often**: Re-review after significant changes
3. **Address Blocking Issues**: Fix CRITICAL issues immediately
4. **Keep History**: Don't delete review files - they provide valuable history
5. **Share Reviews**: Review files are great for team discussions

## Limitations

- Requires GitHub CLI (`gh`) - no fallback mode currently
- Works with GitHub repositories only
- Reviews are suggestion-only - no automated fixes
- Large diffs (>1000 files) may be slow

## Troubleshooting

### "Constitution not found"

Create one: `/speckit.constitution`

### "PR not found"

- Check PR number is correct
- Ensure  `gh` CLI is authenticated: `gh auth status`
- Verify you have access to the repository

### "No permission to read PR"

Authenticate with GitHub CLI: `gh auth login`

### Review seems incomplete

- Check constitution has clear principles
- Ensure PR diff is accessible
- Try re-running the command

## Examples

### Example 1: Constitution Violation

```markdown
## Critical Issues (Blocking)

| ID | Principle | File:Line | Issue | Recommendation |
|----|-----------|-----------|-------|----------------|
| C1 | Test-First (TDD) | src/api.ts:45 | New API endpoint added without tests | Add tests in tests/api.test.ts before implementation |
```

**Action**: Write tests, then re-review.

### Example 2: Security Issue

```markdown
## High Priority Issues

| ID | Principle | File:Line | Issue | Recommendation |
|----|-----------|-----------|-------|----------------|
| H1 | Security | config.ts:12 | Hardcoded API key visible | Move to environment variable or secret manager |
```

**Action**: Refactor credentials, then re-review.

### Example 3: Clean PR

```markdown
## Executive Summary

- ✅ **Constitution Compliance**: PASS (8/8 principles)
- 🔒 **Security**: No issues found
- 📊 **Code Quality**: No issues found

**Approval Recommendation**: ✅ **APPROVE**
```

**Action**: Proceed with merge!

---

For more information, see the [Spec-Driven Development Guide](https://github.com/MarkHazleton/spec-kit/blob/main/spec-driven.md).
```

### 4.3 Update AGENTS.md

Add section on pr-review command:

```markdown
## PR Review Command Implementation

The `/speckit.pr-review` command follows standard speckit patterns but with unique considerations:

### Key Differences from Other Commands

1. **No Feature Context**: Works repository-wide, not tied to specific features
2. **External Data Source**: Pulls from GitHub PR API via `gh` CLI
3. **Persistent Output**: Creates/updates files in `/.documentation/specs/pr-review/`
4. **Metadata Tracking**: Includes commit SHA and timestamps
5. **Update Logic**: Handles multiple reviews of same PR

### Script Integration

The command uses `scripts/{bash,powershell}/get-pr-context.{sh,ps1}` to:
- Extract PR metadata from GitHub
- Get commit SHA for review tracking
- Fetch diff and changed files
- Validate constitution exists

### Agent-Specific Notes

- **GitHub Copilot**: Best integration due to native PR context
- **Claude/Gemini**: Work well with explicit PR numbers
- **IDE-based agents**: May have limitations in PR context access
```

---

## Phase 5: Testing Strategy

### 5.1 Test Scenarios

**Scenario 1: Clean PR**
- Constitution: Basic principles
- PR: Well-tested, documented changes
- Expected: All checks pass, approval recommended

**Scenario 2: TDD Violation**
- Constitution: Mandatory TDD principle
- PR: New code without tests
- Expected: CRITICAL issue flagged

**Scenario 3: Security Issue**
- Constitution: Security principles
- PR: Hardcoded credentials
- Expected: HIGH/CRITICAL security issue

**Scenario 4: Multiple Reviews**
- First review: Issues found
- PR updated with fixes
- Second review: Shows improvement, issues resolved

**Scenario 5: No Constitution**
- PR ready for review
- No constitution exists
- Expected: Clear error message, guidance to create constitution

### 5.2 Edge Cases

- **Closed/Merged PR**: Review still works, notes PR state
- **Very Large PR**: Handle gracefully, may need summarization
- **Empty PR**: Handle PRs with no file changes
- **Binary Files**: Skip review of binary files
- **No Diff Available**: Use git fallback or prompt user

---

## Phase 6: Implementation Checklist

### Core Functionality
- [ ] Create `templates/commands/pr-review.md`
- [ ] Create `scripts/bash/get-pr-context.sh`
- [ ] Create `scripts/powershell/get-pr-context.ps1`
- [ ] Add `/.documentation/specs/pr-review/` directory creation logic
- [ ] Implement review report generation
- [ ] Add metadata tracking (commit SHA, timestamp)
- [ ] Handle existing review updates

### GitHub Integration
- [ ] Test with GitHub CLI (`gh pr view`)
- [ ] Test with GitHub CLI (`gh pr diff`)
- [ ] Handle authentication errors gracefully
- [ ] Test PR auto-detection from branch
- [ ] Test explicit PR number input

### Constitution Integration
- [ ] Parse constitution principles
- [ ] Extract MUST vs SHOULD requirements
- [ ] Map code changes to principles
- [ ] Generate constitution-aligned feedback

### Multi-Agent Support
- [ ] Generate `.github/agents/pr-review.md`
- [ ] Generate `.claude/commands/pr-review.md`
- [ ] Generate `.gemini/commands/pr-review.toml`
- [ ] Generate `.cursor/commands/pr-review.md`
- [ ] Test with each agent type

### Documentation
- [ ] Update README.md with command info
- [ ] Create `.documentation/pr-review-usage.md`
- [ ] Update AGENTS.md with implementation notes
- [ ] Add examples to documentation

### Quality Assurance
- [ ] Test all scenarios from 5.1
- [ ] Test all edge cases from 5.2
- [ ] Verify review file format consistency
- [ ] Test review updates correctly
- [ ] Validate commit SHA tracking

### Release Preparation
- [ ] Update CHANGELOG.md
- [ ] Bump version in pyproject.toml
- [ ] Update release scripts if needed
- [ ] Create release notes
- [ ] Test end-to-end workflow

---

## Success Criteria

The `/speckit.pr-review` command is successful when:

1. ✅ Requires only constitution (no spec/plan/tasks needed)
2. ✅ Works for any PR in any branch
3. ✅ Accurately detects constitution violations
4. ✅ Generates actionable, line-specific feedback
5. ✅ Saves reviews to `/.documentation/specs/pr-review/pr-{id}.md`
6. ✅ Tracks commit SHA and review timestamp
7. ✅ Handles review updates correctly (appends, not replaces)
8. ✅ Works across all supported AI agents
9. ✅ Handles errors gracefully with clear guidance
10. ✅ Provides consistent, reproducible results

---

## Future Enhancements (Out of Scope for v1)

- **Inline Comments**: Post review findings as PR comments via GitHub API
- **Team Reviews**: Multi-reviewer collaboration workflows
- **Review Templates**: Custom review checklists beyond constitution
- **Metrics Dashboard**: Track review trends over time
- **Auto-Approve**: Trusted PRs that pass all checks
- **CI/CD Integration**: Run reviews automatically in GitHub Actions
- **Non-GitHub Support**: GitLab, Bitbucket, etc.
- **Diff-Based Reviews**: Only review changed lines, not full files

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-25  
**Status**: Ready for Implementation
