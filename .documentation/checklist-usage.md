# Checklist Command Guide

## Overview

The `/devspark.checklist` command generates requirements-quality checklists for your feature specification. It treats your spec like code and the checklist like its unit test suite -- validating that requirements are complete, clear, consistent, and measurable.

This is **not** a QA test plan. It does not check whether code works correctly. It checks whether requirements are *written* correctly.

## Prerequisites

- **Required**: Feature specification at `spec.md`
- **Optional**: Implementation plan at `plan.md` (adds technical context)
- **Optional**: Task breakdown at `tasks.md` (adds implementation awareness)

## When to Use

Run `/devspark.checklist` **after** `/devspark.specify` or `/devspark.clarify`, **before** `/devspark.plan`:

```text
/devspark.specify -> /devspark.clarify -> /devspark.checklist -> /devspark.plan
```

Checklist outputs are gate artifacts. The checklist files live under `.documentation/specs/<feature>/checklists/`, and the current aggregate gate summary is persisted at `.documentation/specs/<feature>/gates/checklist.md`. Later commands such as `/devspark.tasks`, `/devspark.implement`, and `/devspark.create-pr` read them, summarize incomplete items, and ask whether you want to fix the gaps first or proceed with an explicit acknowledgement.

Use this command when you want to:

- Validate that a spec is ready for planning
- Find gaps, ambiguities, or conflicts in requirements
- Ensure edge cases and error scenarios are addressed in the spec
- Get a domain-specific quality check (security, UX, API, performance)

## Quick Start

### Basic Usage

```bash
/devspark.checklist
```

The command asks up to 3 clarifying questions about scope, depth, and focus, then generates a checklist file.

### Domain-Specific Checklists

```bash
/devspark.checklist Focus on security requirements
/devspark.checklist UX and accessibility requirements quality
/devspark.checklist API contract completeness
/devspark.checklist Performance requirements clarity
```

Each run creates a separate file in `specs/{feature}/checklists/` named by domain (e.g., `security.md`, `ux.md`, `api.md`).

## What It Checks

The checklist evaluates requirements across these dimensions:

| Dimension | What it asks |
|-----------|-------------|
| **Completeness** | Are all necessary requirements present? |
| **Clarity** | Are requirements specific and unambiguous? |
| **Consistency** | Do requirements align without conflicts? |
| **Measurability** | Can success criteria be objectively verified? |
| **Coverage** | Are all user flows and edge cases addressed? |
| **Dependencies** | Are external dependencies documented? |

## Anti-Pattern: Implementation Testing vs. Requirements Testing

The most common mistake is writing checklist items that test the *implementation* instead of the *requirements*.

| Wrong (tests implementation) | Right (tests requirements) |
|------------------------------|---------------------------|
| "Verify the button clicks correctly" | "Are interaction requirements defined for all clickable elements?" |
| "Test error handling works" | "Are error handling requirements specified for all failure modes?" |
| "Confirm the API returns 200" | "Are expected response formats documented for all endpoints?" |
| "Check that the page loads in under 2s" | "Are performance requirements quantified with specific thresholds?" |

**The rule**: If a checklist item starts with "Verify", "Test", "Confirm", or "Check" followed by a behavior, it's testing implementation. Rewrite it as a question about whether the *requirement* is well-specified.

## Example Output

A security-focused checklist (`checklists/security.md`) looks like:

```markdown
# Security Requirements Quality Checklist

> Purpose: Validate security requirements completeness and clarity
> Created: 2026-04-09 | Focus: Security | Depth: Standard

## Authentication & Authorization

- [ ] CHK001 - Are authentication requirements specified for all protected resources? [Coverage]
- [ ] CHK002 - Are role-based access requirements defined with explicit permission matrices? [Completeness, Spec SS3.1]
- [ ] CHK003 - Is "authorized user" defined with specific criteria? [Clarity, Spec SS3.2]

## Data Protection

- [ ] CHK004 - Are data-at-rest encryption requirements specified? [Gap]
- [ ] CHK005 - Are PII handling requirements consistent with stated compliance obligations? [Consistency]

## Input Validation

- [ ] CHK006 - Are input validation requirements defined for all user-facing inputs? [Coverage]
- [ ] CHK007 - Is "sanitized input" quantified with specific techniques or standards? [Clarity, Spec SS4.1]
```

## Multiple Checklists

Each `/devspark.checklist` run creates a new file. This lets you build domain-specific coverage:

```text
specs/001-my-feature/checklists/
  ux.md           -- UI and accessibility requirements
  security.md     -- Security requirements
  api.md          -- API contract requirements
  performance.md  -- Performance requirements
```

Run the command multiple times with different focus areas to build comprehensive coverage.

## Related Commands

| Command | Relationship |
|---------|-------------|
| `/devspark.specify` | Creates the spec that the checklist validates |
| `/devspark.clarify` | Resolves ambiguities the checklist identifies |
| `/devspark.analyze` | Validates consistency across spec, plan, and tasks |
| `/devspark.critic` | Adversarial risk analysis of the implementation plan |
| `/devspark.create-pr` | Summarizes checklist completion in the PR draft |
