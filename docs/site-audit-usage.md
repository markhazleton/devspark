# Site Audit Command Guide

## Overview

The `/speckit.site-audit` command performs comprehensive codebase audits against your project constitution and development standards. It scans your repository for compliance violations, security issues, code quality concerns, unused dependencies, and architectural problems.

> **Note**: This command is **independent of the Spec-Driven Development workflow**. Unlike commands like `/speckit.specify`, `/speckit.plan`, and `/speckit.tasks`, site-audit does **not** require any spec, plan, or tasks to exist. It only requires a project constitution (`/memory/constitution.md`) and can be run on any codebase at any time.

## Prerequisites

- **Required**: Project constitution at `/memory/constitution.md`
- **Required**: PowerShell 7+ (for script execution)
- **Optional**: pip-audit (for Python security scanning)
- **Optional**: npm audit (for Node.js security scanning)

## Quick Start

### Create Constitution

If you haven't created a project constitution yet:

```bash
/speckit.constitution Create principles for code quality, testing standards, security practices, and documentation requirements
```

### Run Full Audit

```bash
/speckit.site-audit
```

This performs a complete audit covering all categories.

## Audit Scopes

You can focus the audit on specific areas using the `--scope` flag:

### Full Audit (Default)

```bash
/speckit.site-audit --scope=full
```

Runs all checks including constitution compliance, security, packages, quality, unused code, and duplicates.

### Constitution Compliance Only

```bash
/speckit.site-audit --scope=constitution
```

Evaluates codebase against each principle in your constitution.

### Package/Dependency Analysis

```bash
/speckit.site-audit --scope=packages
```

Analyzes dependencies for:
- Outdated packages
- Security vulnerabilities
- Unused dependencies
- Missing dependencies
- License compliance issues

### Code Quality Metrics

```bash
/speckit.site-audit --scope=quality
```

Measures:
- Lines of code and file sizes
- Cyclomatic complexity
- Deep nesting occurrences
- TODO/FIXME comments
- Maintainability indicators

### Unused Code Detection

```bash
/speckit.site-audit --scope=unused
```

Identifies:
- Functions/methods never called
- Classes never instantiated
- Variables assigned but never read
- Imports never used
- Dead files not referenced

### Duplicate Code Detection

```bash
/speckit.site-audit --scope=duplicate
```

Finds:
- Exact duplicate blocks (>10 lines)
- Near-duplicate blocks (>80% similarity)
- Copy-paste patterns across files

## Understanding Audit Output

### Report Location

Audit reports are saved to: `/docs/copilot/audit/YYYY-MM-DD_results.md`

### Report Structure

Each audit report contains:

#### 1. Audit Metadata
- Audit date/time
- Scope executed
- Constitution version
- Repository information

#### 2. Executive Summary

```markdown
### Compliance Score

| Category | Score | Status |
|----------|-------|--------|
| Constitution Compliance | 85% | ⚠️ PARTIAL |
| Security | 100% | ✅ PASS |
| Code Quality | 78% | ⚠️ PARTIAL |
| Test Coverage | 90% | ✅ PASS |
| Documentation | 65% | ⚠️ PARTIAL |
| Dependencies | 95% | ✅ PASS |
```

#### 3. Constitution Compliance

Principle-by-principle evaluation with:
- ✅ PASS - Fully compliant
- ❌ FAIL - Violates principle
- ⚠️ PARTIAL - Partial compliance
- Specific file:line violations
- Recommendations for each finding

#### 4. Security Findings

Categorized security issues:
- Hardcoded secrets/credentials
- Insecure patterns (eval, exec, SQL concatenation)
- Missing input validation
- Exposed sensitive data

#### 5. Package Analysis

Dependency health report:
- Vulnerable packages with CVE references
- Outdated packages with current vs. latest versions
- Unused packages safe to remove
- License compatibility issues

#### 6. Code Quality Metrics

Quantitative measurements:
- Total lines of code
- Average file size
- High complexity function count
- Deep nesting occurrences
- Technical debt indicators

#### 7. Recommendations

Prioritized action items:
- **Immediate Actions** (CRITICAL severity)
- **High Priority** (this sprint)
- **Medium Priority** (next sprint)
- **Low Priority** (backlog)

## Severity Classification

| Severity | Criteria |
|----------|----------|
| **CRITICAL** | Security vulnerability, constitution MUST violation, blocking issue |
| **HIGH** | Constitution SHOULD violation, significant quality issue, vulnerable packages |
| **MEDIUM** | Code quality concern, maintainability issue, missing tests |
| **LOW** | Style suggestion, minor improvement, optimization opportunity |

## Common Workflows

### Workflow 1: Pre-Release Audit

```bash
# Before releasing, run full audit
/speckit.site-audit

# Review critical issues
# Address all CRITICAL findings
# Document any accepted risks

# Re-run to verify fixes
/speckit.site-audit
```

### Workflow 2: Security Focus

```bash
# Check for security issues and vulnerable dependencies
/speckit.site-audit --scope=packages

# Then check for code-level security issues
/speckit.site-audit --scope=constitution
```

### Workflow 3: Code Health Monitoring

```bash
# Weekly quality check
/speckit.site-audit --scope=quality

# Monthly duplicate check
/speckit.site-audit --scope=duplicate

# Compare with previous audit reports for trends
```

### Workflow 4: Cleanup Sprint

```bash
# Find unused code and dependencies
/speckit.site-audit --scope=unused

# Remove identified dead code
# Re-audit to verify cleanup

/speckit.site-audit --scope=unused
```

## Working with Constitution

The audit is entirely driven by your constitution. The quality and relevance of findings depends on having clear, specific principles.

### Good Constitution Example

```markdown
## Core Principles

### I. Security First (MANDATORY)
- No hardcoded secrets or credentials (MUST)
- All user input MUST be validated
- SQL queries MUST use parameterized statements
- Authentication MUST use established libraries

### II. Code Quality
- Maximum function length: 50 lines (SHOULD)
- Maximum nesting depth: 4 levels (SHOULD)
- All public APIs MUST have documentation
- No TODO comments in production code (SHOULD)
```

This produces specific, actionable findings.

### Weak Constitution Example

```markdown
## Principles
- Write secure code
- Keep code clean
```

This produces vague, less actionable findings.

## Historical Comparison

When previous audits exist, the report includes trend analysis:

```markdown
## Comparative Analysis

| Metric | Previous | Current | Trend |
|--------|----------|---------|-------|
| Critical Issues | 5 | 2 | ↓ Improved |
| Code Quality Score | 72% | 85% | ↑ Improved |
| Test Coverage | 80% | 78% | ↓ Degraded |
```

This helps track improvement over time.

## Troubleshooting

### "Constitution not found"

**Problem**: `/memory/constitution.md` doesn't exist

**Solution**:
```bash
/speckit.constitution Create project principles
```

### "Script execution failed"

**Problem**: PowerShell script cannot execute

**Solutions**:
1. Ensure PowerShell 7+ is installed
2. Check execution policy: `Get-ExecutionPolicy`
3. Run from repository root directory

### "pip-audit not available"

**Problem**: Python security scanning skipped

**Solution**:
```bash
pip install pip-audit
```

### Audit takes too long

**Problem**: Full audit is slow on large codebase

**Mitigation**:
- Use specific scope flags to focus on areas of interest
- Run comprehensive audits less frequently (weekly)
- Run focused audits more frequently (daily)

## Best Practices

### 1. Regular Audits
- Run full audit weekly or before releases
- Run constitution audit after major changes
- Run security audit before deployments

### 2. Address Critical Issues First
- Fix all CRITICAL issues immediately
- HIGH issues should be addressed within the sprint
- MEDIUM/LOW can be scheduled

### 3. Track Trends
- Keep audit history in `/docs/copilot/audit/`
- Compare scores over time
- Celebrate improvements

### 4. Improve Your Constitution
- If audits miss important issues, enhance constitution
- Add new principles based on incidents
- Keep principles specific and measurable

### 5. Automate
- Consider running audits in CI/CD pipelines
- Set up alerts for critical regressions
- Generate reports automatically

## Integration with Development Workflow

### During Development

```bash
# After completing a feature
/speckit.site-audit --scope=constitution

# Before creating PR
/speckit.site-audit --scope=quality
```

### Code Review

```bash
# Audit before review
/speckit.site-audit

# Include audit findings in review discussion
```

### Continuous Integration

Integrate audit into your pipeline to catch issues early.

## Support

If you encounter issues:
- Check [Troubleshooting](#troubleshooting) section above
- Review [Spec Kit Issues](https://github.com/MarkHazleton/spec-kit/issues)

---

*Part of the Spec Kit - Spec-Driven Development Toolkit*  
*For more information: https://github.com/MarkHazleton/spec-kit*
