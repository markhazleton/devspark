# PR Review Command Guide

## Overview

The `/speckit.pr-review` command performs automated, constitution-driven code reviews for GitHub Pull Requests. It evaluates code changes against your project's established principles and generates detailed feedback reports stored in your repository.

> **Note**: This command is **independent of the Spec-Driven Development workflow**. Unlike commands like `/speckit.specify`, `/speckit.plan`, and `/speckit.tasks`, PR review does **not** require any spec, plan, or tasks to exist. It only requires a project constitution (`/memory/constitution.md`) and works for any PR in any repository—whether or not you're using spec-driven development.

## Prerequisites

- **Required**: Project constitution at `/memory/constitution.md`
- **Required**: GitHub repository with pull requests
- **Required**: GitHub CLI (`gh`) installed and authenticated
- **Optional**: Feature specifications (if using spec-driven development)

## Quick Start

### Install GitHub CLI

If you haven't installed the GitHub CLI yet:

```bash
# macOS
brew install gh

# Windows
winget install --id GitHub.cli

# Linux (Debian/Ubuntu)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# Authenticate
gh auth login
```

### Create Constitution

If you haven't created a project constitution yet:

```bash
/speckit.constitution Create principles for code quality, testing standards, security practices, and documentation requirements
```

## Basic Usage

### Review Current PR

If you're working on a PR branch, simply run:

```bash
/speckit.pr-review
```

The command will:
1. Auto-detect the PR associated with your current branch
2. Fetch PR metadata and changes from GitHub
3. Evaluate changes against constitution principles
4. Generate a comprehensive review report
5. Save the report to `/specs/pr-review/pr-{number}.md`

### Review Specific PR

To review any PR by number:

```bash
/speckit.pr-review #123
```

or without the # symbol:

```bash
/speckit.pr-review 123
```

This works for:
- Your own PRs
- Team member PRs
- PRs targeting any branch (main, develop, feature branches)
- Open, closed, or merged PRs (for historical analysis)

### Re-Review After Changes

When a PR is updated with new commits:

```bash
/speckit.pr-review #123
```

The command will:
- Detect that the commit SHA has changed
- Generate a fresh review for the new commit
- Append it to the existing review file
- Preserve all previous review history
- Show a comparison of what changed

## Understanding Review Output

### Review File Location

Reviews are saved to: `/specs/pr-review/pr-{number}.md`

Example: `/specs/pr-review/pr-123.md`

### Review Structure

Each review contains:

#### 1. Review Metadata
- PR number, title, author
- Source and target branches
- Commit SHA being reviewed
- Review date/time (UTC)
- Constitution version used

#### 2. Executive Summary
Quick overview with pass/fail status:
- Constitution compliance (X/Y principles)
- Security issues count
- Code quality recommendations
- Testing status
- Documentation status
- Overall approval recommendation

#### 3. Issue Categories

**Critical Issues (Blocking)**
- Violates mandatory (MUST) constitution principles
- Security vulnerabilities
- Breaking changes to production
- Must be fixed before merge

**High Priority Issues**
- Violates recommended (SHOULD) principles
- Significant quality concerns
- Creates technical debt
- Should be fixed before merge

**Medium Priority Suggestions**
- Partial compliance with principles
- Improvement opportunities
- Maintainability concerns
- Recommended to address

**Low Priority Improvements**
- Style preferences
- Minor optimizations
- Optional enhancements
- Nice to have

#### 4. Constitution Alignment
Principle-by-principle evaluation:
- ✅ Pass - Fully complies
- ❌ Fail - Violates principle
- ⚠️ Partial - Partially complies
- ⏭️ N/A - Not applicable

#### 5. Security Checklist
Automated checks for:
- Hardcoded secrets/credentials
- Input validation
- Authentication/authorization
- SQL injection risks
- XSS vulnerabilities
- Dependency security

#### 6. Detailed Findings
File-by-file breakdown with:
- Exact line numbers
- Code snippets showing issues
- Constitution principle violated
- Specific actionable recommendations

#### 7. Next Steps
Prioritized action items:
- Immediate actions (required)
- Recommended improvements
- Future considerations (optional)

## Understanding Severity Levels

### Critical (Blocking)
```
❌ Must be resolved before merge
```
- Violates MUST principle in constitution
- Security vulnerabilities
- Will break production
- No exceptions

**Example**: Missing tests when TDD is mandatory

### High Priority
```
⚠️ Strongly recommended to fix
```
- Violates SHOULD principle significantly
- Creates significant technical debt
- Quality concerns
- May block after team discussion

**Example**: Poor error handling, missing documentation

### Medium Priority
```
ℹ️ Improvement opportunity
```
- Partial compliance with principles
- Code could be cleaner
- Maintainability concern
- Fix if time permits

**Example**: Code duplication, naming improvements

### Low Priority
```
💡 Optional enhancement
```
- Style preferences
- Minor optimizations
- Nice to have
- Address in future work

**Example**: Refactoring suggestions, comment improvements

## Common Workflows

### Workflow 1: Feature Development

```bash
# 1. Create feature spec and implementation
/speckit.specify Build user authentication feature
/speckit.plan Use Node.js with JWT tokens
/speckit.implement

# 2. Create PR on GitHub
git push origin feature/auth
gh pr create --title "Add user authentication" --body "Implements JWT-based auth"

# 3. Review PR against constitution
/speckit.pr-review

# 4. Address feedback
# ... make changes ...
git push

# 5. Re-review to verify fixes
/speckit.pr-review
```

### Workflow 2: Code Review

```bash
# Team member creates PR #456
# You want to review it

# 1. Check out the PR
gh pr checkout 456

# 2. Run constitution-based review
/speckit.pr-review #456

# 3. View the generated review
cat specs/pr-review/pr-456.md

# 4. Discuss findings with team
# 5. Request changes via GitHub if needed
```

### Workflow 3: Quality Audit

```bash
# Review recent merged PRs for quality trends

/speckit.pr-review #100
/speckit.pr-review #101
/speckit.pr-review #102

# Analyze patterns in specs/pr-review/ directory
ls specs/pr-review/
```

## Review Updates and History

### First Review
When you first review a PR, a new file is created:
```
specs/pr-review/pr-123.md
```

### Subsequent Reviews (Same Commit)
If you re-review the same commit:
- File is updated in place
- "Last Updated" timestamp changes
- Review date shows when first created

### Updates (New Commits)
When PR has new commits:
- New review appears at top of file
- Previous review moves to "Previous Review History" section
- Each review tracks its own commit SHA
- Easy to see what changed between reviews

Example structure:
```markdown
# Pull Request Review: Add Authentication

[Latest review for commit xyz789]

---

## Previous Review History

### Review 2: 2026-01-24 10:30:00 UTC
**Commit**: abc123

[Previous review summary]

### Review 1: 2026-01-23 14:15:00 UTC
**Commit**: def456

[First review summary]
```

## Working with Constitution

The review is entirely driven by your constitution. The quality and relevance of reviews depends on having clear, specific principles.

### Good Constitution Example

```markdown
## Core Principles

### I. Test-First Development (MANDATORY)
- All production code MUST have tests written first
- Tests MUST fail before implementation
- Red-Green-Refactor cycle strictly enforced
- Minimum 80% code coverage required

### II. Security First
- No hardcoded secrets or credentials (MUST)
- All user input MUST be validated
- SQL queries MUST use parameterized statements
- Authentication MUST use established libraries
```

This produces specific, actionable reviews:
- "Violates Test-First (MANDATORY): src/api.ts has no corresponding test"
- "Security violation: config.js:12 contains hardcoded API key"

### Weak Constitution Example

```markdown
## Principles
- Write good code
- Be secure
- Test your code
```

This produces vague reviews:
- "Code quality could be better"
- "Consider adding tests"

**Tip**: Use specific, measurable principles with MUST/SHOULD language.

## Troubleshooting

### "Constitution not found"

**Problem**: `/memory/constitution.md` doesn't exist

**Solution**:
```bash
/speckit.constitution Create project principles
```

### "PR not found" or "Failed to fetch PR"

**Problem**: Cannot access PR data

**Solutions**:
1. Verify PR number: `gh pr list`
2. Check authentication: `gh auth status`
3. Re-authenticate if needed: `gh auth login`
4. Confirm repository access

### "GitHub CLI not installed"

**Problem**: `gh` command not found

**Solution**: Install GitHub CLI (see Quick Start section above)

### "Unable to detect PR number"

**Problem**: Not on a PR branch and no number provided

**Solution**: Provide PR number explicitly:
```bash
/speckit.pr-review #123
```

### Review seems incomplete or superficial

**Problem**: Constitution lacks specific principles

**Solution**: Enhance your constitution with:
- Specific MUST/SHOULD requirements
- Measurable criteria
- Clear examples
- Detailed standards

Then re-run: `/speckit.pr-review #123`

### Large PR takes too long

**Problem**: PR with 100+ files is slow to review

**Mitigation**:
- Break large PRs into smaller ones
- Focus on critical files first
- Consider reviewing incrementally as commits are added

## Best Practices

### 1. Review Early and Often
- Run review when PR is first created
- Re-review after addressing each round of feedback
- Don't wait until just before merge

### 2. Address Critical Issues First
- Fix all CRITICAL issues before requesting re-review
- High priority issues should be addressed before merge
- Medium/Low can be addressed or deferred with justification

### 3. Keep Reviews as Historical Records
- Don't delete review files from `/specs/pr-review/`
- They provide valuable history and patterns
- Use for onboarding and pattern recognition

### 4. Improve Your Constitution
- If reviews miss important issues, enhance constitution
- Add new principles as project evolves
- Keep principles specific and measurable

### 5. Use Reviews in Team Discussions
- Share review reports in PR comments
- Use specific finding IDs (C1, H2, etc.) in discussions
- Link to review file: `/specs/pr-review/pr-123.md`

### 6. Review All PRs Consistently
- Main branch merges
- Feature branch merges
- Hotfix PRs
- Dependency updates

### 7. Learn from Patterns
- Periodically review multiple PR reviews
- Identify common issues
- Update constitution to prevent recurring problems
- Share learnings with team

## Integration with Spec-Driven Development

If using the full spec-kit workflow:

### Feature PRs
When PR branch matches a feature (e.g., `001-user-auth`):
- Review will reference feature spec if available
- Can cross-check implementation against spec requirements
- Links implementation to original requirements

### Non-Feature PRs
For refactoring, fixes, or maintenance:
- Review works perfectly without any spec
- Constitution-only review is comprehensive
- No feature context needed

## Examples

### Example 1: Clean PR

```markdown
## Executive Summary

- ✅ **Constitution Compliance**: PASS (8/8 principles)
- 🔒 **Security**: 0 issues found
- 📊 **Code Quality**: 0 issues found
- 🧪 **Testing**: PASS (95% coverage)
- 📝 **Documentation**: PASS

**Approval Recommendation**: ✅ **APPROVE**

Excellent PR! All constitution principles followed, comprehensive test coverage,
clear documentation. Strong work! Ready to merge.
```

### Example 2: Needs Work

```markdown
## Executive Summary

- ❌ **Constitution Compliance**: FAIL (5/8 principles)
- 🔒 **Security**: 2 issues found
- 📊 **Code Quality**: 4 recommendations
- 🧪 **Testing**: FAIL (no tests)
- 📝 **Documentation**: FAIL (missing)

**Approval Recommendation**: ⚠️ **REQUEST CHANGES**

Critical issues found that must be resolved before merge.

## Critical Issues (Blocking)

| ID | Principle | File:Line | Issue | Recommendation |
|----|-----------|-----------|-------|----------------|
| C1 | Test-First (MANDATORY) | src/auth.ts:all | No tests for new authentication code | Add comprehensive tests to tests/auth.test.ts |
| C2 | Security | config/database.ts:15 | Hardcoded database password | Move to environment variable |
```

### Example 3: Incremental Improvement

```markdown
# Pull Request Review: Add Authentication

## Review Metadata
- **Review Date**: 2026-01-25 15:30:00 UTC
- **Reviewed Commit**: xyz789abc

## Executive Summary
- ✅ **Constitution Compliance**: PASS (8/8 principles)

**Note**: Previous critical issues (C1, C2) have been resolved. Excellent work!

---

## Previous Review History

### Review 1: 2026-01-24 10:00:00 UTC
**Commit**: abc123def

- ❌ **Constitution Compliance**: FAIL (5/8 principles)

**Critical Issues**:
- C1: Missing tests ➜ ✅ FIXED
- C2: Hardcoded password ➜ ✅ FIXED
```

## Additional Resources

- [Constitution Guide](constitution-guide.md)
- [Site Audit Guide](site-audit-usage.md)
- [Critic Guide](critic-usage.md)
- [GitHub CLI Documentation](https://cli.github.com/manual/)
- [Spec Kit on GitHub](https://github.com/github/spec-kit)

## Support

If you encounter issues or have questions:
- Check [Troubleshooting](#troubleshooting) section above
- Review [Spec Kit Issues](https://github.com/github/spec-kit/issues)
- Consult [GitHub CLI Manual](https://cli.github.com/manual/)

---

*Part of the Spec Kit - Spec-Driven Development Toolkit*  
*For more information: https://github.com/github/spec-kit*
