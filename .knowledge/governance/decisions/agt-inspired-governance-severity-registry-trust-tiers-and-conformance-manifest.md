---
id: agt-inspired-governance-severity-registry-trust-tiers-and-conformance-manifest
status: current
constrains: []
evidence:
- type: code
  ref: .knowledge/governance/severity-registry.md
  verified_by: inspection
  test_attempted: false
  fallback_reason: migrated decision constrains framework behavior broadly; targeted
    execution evidence is added as follow-up current-truth work
---

## Migrated Source: ADR-006.md

# ADR-006: AGT-Inspired Governance — Severity Registry, Trust Tiers, and Conformance Manifest

## Status

Accepted

## Context

DevSpark's constitution and PR review workflow produced informal, inconsistent governance output. Severity labels were scattered with no central registry, review depth was uniform regardless of spec-workflow compliance, the framework lacked an honest public statement of its limits, and command templates could drift from the constitution silently. Microsoft AGT's governance model inspired a more structured approach adapted to DevSpark's human-in-the-loop, Markdown-conventions context.

## Decision

Deliver four additive Markdown governance artifacts without new scripts, tool dependencies, or constitution amendments:

1. **Severity registry** (`.documentation/memory/severity-registry.md`): machine-trackable finding codes in `§{section}.{LEVEL}` format matching constitution section markers.
2. **Known-limitations document** (`.documentation/memory/known-limitations.md`): honest, public statement of DevSpark's scope boundaries.
3. **Prompt conformance manifest** (`.documentation/memory/prompt-conformance-manifest.md`): semantic checklist verifying command templates retain required governance sections.
4. **`pr-review.md` update**: additive trust-tier logic — PRs backed by complete spec artifacts receive standard review depth; spec-less PRs receive elevated scrutiny with a MEDIUM trust-tier finding.

Trust-tier detection uses file-presence only (no git history inspection).

## Consequences

### Positive

- Severity codes are now machine-trackable and audit-ready across amendment cycles.
- Trust tiers create a self-reinforcing incentive for spec-driven development.
- Known-limitations document builds adopter trust through intellectual honesty.
- Conformance manifest prevents silent constitution drift in command templates.

### Negative

- Introduces three new memory files to maintain when constitution sections change.