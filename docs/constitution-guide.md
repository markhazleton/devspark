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

### Greenfield vs. Brownfield Projects

**Greenfield (new project)**: You know what principles you want. Use `/speckit.constitution` directly with your requirements.

**Brownfield (existing codebase)**: Your code already has implicit patterns—you need to discover them first. Use `/speckit.discover-constitution` to analyze your codebase and build a constitution through guided discovery.

```bash
# For new projects - you define the principles
/speckit.constitution Security-first, TDD required, 80% coverage

# For existing projects - discover patterns first
/speckit.discover-constitution
# or with focus areas
/speckit.discover-constitution Focus on security and testing patterns
```

The discover command will:
1. Scan your codebase for patterns (testing, security, architecture, code quality)
2. Report what it finds with confidence levels (high/medium/low consistency)
3. Ask 8-10 targeted questions to validate findings and fill gaps
4. Generate a draft constitution at `/memory/constitution-draft.md`
5. You review the draft and finalize with `/speckit.constitution`

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

### Constitution Creation Commands

| Command | Purpose | Best For |
|---------|---------|----------|
| `/speckit.constitution` | Create/update constitution from your requirements | Greenfield projects, known principles |
| `/speckit.discover-constitution` | Analyze codebase and build constitution interactively | Brownfield projects, existing codebases |

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

## Writing for Automated Review

The `/speckit.pr-review` and `/speckit.site-audit` commands evaluate your codebase against your constitution. Writing principles that work well with automated analysis will make these commands more effective.

### What Works Well in Automated Reviews

Principles that are **verifiable by examining code** work best:

| Effective Principle | Why It Works |
|---------------------|--------------|
| "No hardcoded secrets or API keys" | Can scan for patterns like `password = "..."` |
| "All public functions MUST have JSDoc comments" | Can check for presence of documentation |
| "SQL queries MUST use parameterized statements" | Can detect string concatenation in queries |
| "Test files MUST exist for all source files" | Can verify file existence patterns |
| "Maximum nesting depth: 4 levels" | Can analyze code structure |

### What's Harder to Verify Automatically

Some principles require human judgment or runtime analysis:

| Challenging Principle | Why It's Hard |
|----------------------|---------------|
| "Code should be readable" | Subjective, no clear metric |
| "Use appropriate design patterns" | Requires understanding intent |
| "Performance must be acceptable" | Needs runtime measurement |
| "Follow team conventions" | Conventions may not be documented |

These principles are still valid! The automated commands will flag *potential* issues for human review rather than definitively identifying violations.

### Tips for Auditable Principles

1. **Include specific patterns to check for**:
   ```markdown
   - No `console.log` statements in production code (MUST)
   - No `// TODO` comments older than 30 days (SHOULD)
   ```

2. **Specify file/directory conventions**:
   ```markdown
   - All API routes MUST be in `/src/routes/`
   - Test files MUST be named `*.test.ts` or `*.spec.ts`
   ```

3. **Define measurable thresholds**:
   ```markdown
   - Files MUST NOT exceed 500 lines
   - Functions MUST NOT have more than 5 parameters
   ```

4. **List prohibited patterns explicitly**:
   ```markdown
   - MUST NOT use `eval()`, `Function()`, or `setTimeout(string)`
   - MUST NOT disable ESLint rules inline without justification comment
   ```

## What Belongs in Your Constitution

The constitution should contain **principles**—fundamental rules that define your project's identity. Other types of guidance belong elsewhere.

### The Litmus Test

**Put it in the Constitution if:**
- Violating it would be a showstopper in PR review
- It applies project-wide, not to specific components  
- It's a *principle*, not an implementation detail
- You'd reject a PR that violates it regardless of other merits

### Constitution vs. Other Documents

| Document | Purpose | Examples |
|----------|---------|----------|
| **Constitution** | Non-negotiable principles | "All input MUST be validated", "80% test coverage required" |
| **Architecture Decision Records** | Technical choices with context | "We chose PostgreSQL because...", "We use Repository pattern" |
| **Coding Standards** | Day-to-day conventions | "Use library X for HTTP", "Prefer composition over inheritance" |
| **CONTRIBUTING.md** | How to contribute | PR process, branch naming, commit format |

### Example Separation

```markdown
# Constitution (principle - goes in constitution.md)
### Security First
- All external input MUST be validated before use

# ADR (decision - goes in /docs/adr/)
## ADR-007: Input Validation Library
We use Zod for input validation because of TypeScript integration...

# Coding Standards (convention - goes in /docs/standards.md)
## Validation Patterns  
- Use `validateRequest()` from `/lib/validation.ts`
- Add schemas to `/schemas/` directory
```

### Why This Matters for Automated Review

The PR review and site audit commands work best when the constitution contains **verifiable principles**. Conventions like "always use library X" require semantic understanding of alternatives that's harder for automated analysis.

Keep the constitution focused on *what must be true*, and put *how we do things* in coding standards documentation.

## Integrating with AI Agent Instructions

When using AI coding assistants like GitHub Copilot, Claude Code, or OpenAI Codex, you'll have multiple instruction files. Understanding how these work together with your constitution prevents duplication and conflicts.

### The Instruction File Landscape

| File | Agent | Purpose |
|------|-------|---------|
| `/memory/constitution.md` | All (via Spec Kit) | Project principles, quality standards, governance |
| `.github/copilot-instructions.md` | GitHub Copilot | Agent-specific behavior, coding patterns |
| `CLAUDE.md` or `.claude/settings.json` | Claude Code | Agent-specific context, preferences |
| `.codex/` or `AGENTS.md` | OpenAI Codex | Agent configuration, project context |
| `.cursorrules` | Cursor | Editor-specific AI behavior |
| `.windsurfrules` | Windsurf | IDE-specific AI behavior |

### The Hierarchy: Constitution as Source of Truth

```
┌─────────────────────────────────────────┐
│         /memory/constitution.md          │  ← Principles (WHAT must be true)
│   Non-negotiable, agent-agnostic rules   │
└─────────────────────────────────────────┘
                    │
                    │ references
                    ▼
┌─────────────────────────────────────────┐
│     Agent Instruction Files              │  ← Behaviors (HOW to work)
│  .github/copilot-instructions.md         │
│  CLAUDE.md, .cursorrules, etc.           │
└─────────────────────────────────────────┘
                    │
                    │ references
                    ▼
┌─────────────────────────────────────────┐
│     Coding Standards / Style Guides      │  ← Conventions (HOW we code)
│  /docs/standards.md, .editorconfig       │
└─────────────────────────────────────────┘
```

### Best Practice: Reference, Don't Duplicate

**In your agent instruction file** (e.g., `.github/copilot-instructions.md`):

```markdown
## Project Principles

This project follows Spec-Driven Development. Before generating code, 
always consult `/memory/constitution.md` for non-negotiable principles.

Key principles include:
- Security First: All input must be validated
- Test-First: Tests required before implementation
- See constitution for complete requirements and rationale

## Coding Patterns

[Agent-specific patterns go here - these complement the constitution]
```

**Why reference instead of copy?**
- Single source of truth prevents drift
- Constitution updates automatically apply
- No risk of conflicting instructions
- Clearer separation of concerns

### What Goes Where

| Content Type | Constitution | Agent Instructions |
|--------------|--------------|-------------------|
| "All input MUST be validated" | ✅ | Reference only |
| "Use Zod for validation" | ❌ | ✅ |
| "80% test coverage required" | ✅ | Reference only |
| "Prefer vitest over jest" | ❌ | ✅ |
| "No secrets in code" | ✅ | Reference only |
| "Use AWS Secrets Manager" | ❌ | ✅ |
| Security principles | ✅ | Reference only |
| Preferred libraries | ❌ | ✅ |
| Error message format | ❌ | ✅ |
| Logging requirements | ✅ (principle) | ✅ (implementation) |

### Example: Complementary Files

**`/memory/constitution.md`** (principles):
```markdown
### II. Security First

- All user input MUST be validated before processing
- SQL queries MUST use parameterized statements
- No hardcoded secrets or credentials
- Authentication MUST use established libraries
```

**`.github/copilot-instructions.md`** (implementation guidance):
```markdown
## Security Implementation

Follow principles in `/memory/constitution.md` Section II.

When implementing input validation:
- Use Zod schemas in `/src/schemas/`
- Call `validateRequest(schema, req.body)` from `/lib/validation`
- Return 400 with structured error format on validation failure

For database queries:
- Use Prisma ORM (parameterized by default)
- Never use `$queryRawUnsafe()` or string concatenation

For secrets:
- Use `process.env.SECRET_NAME` pattern
- Secrets are loaded from AWS Secrets Manager in production
```

### Handling Multiple AI Agents

If your team uses multiple agents (Copilot, Claude, Cursor), create consistent instruction files:

1. **Shared principles**: All reference `/memory/constitution.md`
2. **Agent-specific behaviors**: Each file can have unique content
3. **Consider a shared include**: Some teams create `/docs/ai-context.md` that all agent files reference

**Example structure**:
```
/memory/
  constitution.md           # Principles (all agents)
  
/docs/
  ai-context.md             # Shared project context (optional)
  coding-standards.md       # Implementation conventions
  
.github/
  copilot-instructions.md   # Copilot-specific + references above
  
CLAUDE.md                   # Claude-specific + references above
AGENTS.md                   # Codex-specific + references above
```

### Resolving Conflicts

If agent instructions conflict with the constitution:

1. **Constitution wins**: It's the authoritative source
2. **Update agent file**: Remove or correct conflicting guidance
3. **Consider intent**: If the agent instruction seems better, propose a constitution amendment instead

**Signs of conflict**:
- Agent suggests a library but constitution requires a different approach
- Agent's code patterns violate constitution principles
- Different files give different answers to the same question

### Cross-Referencing Syntax

Different agents parse references differently. Use clear, consistent references:

```markdown
## Good References

See `/memory/constitution.md` for project principles.
Follow Section III (Code Quality) of the constitution.
Constitution requirement: "All public APIs MUST have documentation"

## Avoid

See the constitution. (which one? where?)
Follow our standards. (what standards?)
```

### Template: Agent Instruction File Header

Use this template at the top of any AI agent instruction file:

```markdown
# [Agent Name] Instructions for [Project Name]

## Foundational Documents

Before generating or reviewing code, consult these documents:

1. **Project Constitution**: `/memory/constitution.md`
   - Contains non-negotiable principles
   - Violations are blocking issues in PR review
   
2. **Coding Standards**: `/docs/coding-standards.md` (if exists)
   - Implementation patterns and conventions
   
3. **Architecture Decisions**: `/docs/adr/` (if exists)
   - Technical choices with rationale

## Agent-Specific Guidance

[Your agent-specific content here]
```

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
