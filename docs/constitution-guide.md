# Constitution Guide

## Overview

The **project constitution** is the foundational document that defines your project's core principles, standards, and governance rules. It serves as the authoritative source of truth that all Spec Kit commands reference when making decisions, reviewing code, or auditing your codebase.

The constitution lives at `/memory/constitution.md` in your project root.

## Why a Constitution?

Without clear guiding principles, AI agents and developers can make inconsistent decisions. The constitution provides:

- **Consistency**: All code reviews, audits, and implementations follow the same standards
- **Clarity**: Explicit MUST/SHOULD requirements remove ambiguity
- **Governance**: Clear rules for how principles can be amended
- **Accountability**: Every finding references specific constitution sections

## Creating Your Constitution

Use the `/speckit.constitution` command to create or update your constitution:

```bash
/speckit.constitution Create principles for code quality, testing standards, security practices, and documentation requirements
```

### Example Prompts

**Security-focused project**:
```bash
/speckit.constitution Security-first principles: no hardcoded secrets, mandatory input validation, parameterized SQL queries, rate limiting required on all public endpoints
```

**TDD-focused project**:
```bash
/speckit.constitution Strict TDD with test-first development, minimum 80% coverage, integration tests for all API endpoints, red-green-refactor cycle enforced
```

**Enterprise project**:
```bash
/speckit.constitution Enterprise standards: code review required, documentation for all public APIs, changelog updates mandatory, semantic versioning, accessibility compliance
```

## Constitution Structure

A well-structured constitution includes:

### Core Principles

Named, numbered principles with clear requirements:

```markdown
### I. Security First (MANDATORY)

- No hardcoded secrets or credentials (MUST)
- All user input MUST be validated
- SQL queries MUST use parameterized statements
- Authentication MUST use established libraries
```

### Requirement Levels

Use consistent language to indicate requirement strength:

| Term | Meaning | Severity in Audits |
|------|---------|-------------------|
| **MUST** | Non-negotiable, mandatory | CRITICAL if violated |
| **MUST NOT** | Prohibited, never allowed | CRITICAL if violated |
| **SHOULD** | Strongly recommended | HIGH if violated |
| **SHOULD NOT** | Discouraged | HIGH if violated |
| **MAY** | Optional, permitted | LOW or informational |

### Governance Section

Define how the constitution itself is managed:

```markdown
## Governance

- Constitution supersedes all other practices
- Amendments require documentation and approval
- All PRs must verify compliance
- Complexity must be justified

**Version**: 1.0.0 | **Ratified**: 2025-01-15 | **Last Amended**: 2025-01-15
```

## Example Constitution

```markdown
# MyProject Constitution

## Core Principles

### I. Test-First Development (MANDATORY)

- All production code MUST have tests written first
- Tests MUST fail before implementation (Red phase)
- Red-Green-Refactor cycle strictly enforced
- Minimum 80% code coverage required

### II. Security First

- No hardcoded secrets or credentials (MUST)
- All user input MUST be validated
- SQL queries MUST use parameterized statements
- Authentication MUST use established libraries (SHOULD)

### III. Code Quality

- Maximum function length: 50 lines (SHOULD)
- Maximum nesting depth: 4 levels (SHOULD)
- All public APIs MUST have documentation
- No TODO comments in production code (SHOULD)

### IV. Observability

- Structured logging MUST be used
- Error tracking MUST be configured
- Health check endpoints MUST exist for services

## Governance

- Constitution supersedes all other practices
- Amendments require team approval and documentation
- All code reviews MUST verify compliance

**Version**: 1.0.0 | **Ratified**: 2025-01-15
```

## Commands That Use the Constitution

### Constitution-Powered Commands (No Spec Required)

These commands only need a constitution and work on any codebase:

| Command | How It Uses Constitution |
|---------|-------------------------|
| `/speckit.pr-review` | Evaluates PR changes against each principle |
| `/speckit.site-audit` | Scans entire codebase for principle violations |

### Spec Workflow Commands

These commands also reference the constitution:

| Command | How It Uses Constitution |
|---------|-------------------------|
| `/speckit.plan` | Ensures implementation plan aligns with principles |
| `/speckit.critic` | Flags constitution violations as SHOWSTOPPERS |
| `/speckit.implement` | Follows principles during code generation |

## Best Practices

### 1. Be Specific and Measurable

**Bad**: "Write good code"

**Good**: "Functions MUST NOT exceed 50 lines. Cyclomatic complexity MUST stay below 10."

### 2. Use MUST/SHOULD Consistently

Reserve MUST for truly non-negotiable requirements. Overusing MUST dilutes its meaning.

### 3. Include Rationale

Explain why principles exist to help with edge case decisions:

```markdown
### III. No Direct Database Access from UI

UI components MUST NOT access the database directly. 
All data access MUST go through the service layer.

**Rationale**: Maintains separation of concerns, enables caching, 
simplifies testing, and prevents N+1 query issues.
```

### 4. Version Your Constitution

Track changes with version numbers and dates. This helps understand which version was used for past reviews.

### 5. Keep It Focused

A constitution with 50 principles is hard to follow. Focus on 5-10 core principles that matter most.

### 6. Review and Update

Periodically review your constitution:
- Are principles being followed?
- Are any principles causing friction without value?
- Have new concerns emerged that need principles?

## Troubleshooting

### "Constitution not found"

Commands require `/memory/constitution.md` to exist:

```bash
/speckit.constitution Create initial project principles
```

### Findings seem irrelevant

Your constitution may be too vague. Add specific, measurable criteria.

### Too many violations

Start with fewer MUST requirements. Migrate MUST to SHOULD for guidelines that allow exceptions.

### Team disagrees on findings

The constitution is the source of truth. If the team disagrees with a finding, update the constitution rather than ignoring findings.

## Next Steps

- [PR Review Guide](pr-review-usage.md) - See how constitution drives PR reviews
- [Site Audit Guide](site-audit-usage.md) - Learn about codebase auditing
- [Critic Guide](critic-usage.md) - Understand risk analysis

---

*The constitution is your project's DNA. Invest time in making it clear, specific, and actionable.*
