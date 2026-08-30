---
id: okf-knowledge-layer-and-genuine-fix-discipline
status: current
constrains: []
evidence:
- type: code
  ref: templates/command-preamble-contract.md
  verified_by: inspection
  test_attempted: false
  fallback_reason: migrated decision constrains framework behavior broadly; targeted
    execution evidence is added as follow-up current-truth work
---

## Migrated Source: ADR-009.md

# ADR-009: OKF Knowledge Layer and Genuine Fix Discipline

## Status

Accepted

## Context

DevSpark lifecycle commands already emit machine-readable JSON contracts that are
consumed by multiple commands and external workflows. Adding traceability by
reshaping those contracts would risk breaking existing consumers.

Separately, fix and review workflows can be gamed when a finding is phrased as a
bare metric. A fix can reduce lint, complexity, or coverage noise without
changing the behavior the check was meant to protect.

## Decision

DevSpark will dual-write an additive OKF knowledge layer under
frontmatter validated by `templates/schemas/okf-knowledge-document.schema.json`.
The existing JSON contracts remain unchanged.

Analyze and critic run advisory knowledge-coverage validation through
`scripts/{bash,powershell}/validate-knowledge-coverage.*`. Missing knowledge
folders skip cleanly, and coverage gaps report fail-soft findings rather than
blocking older features.

Review, fix, audit, analyze, critic, and verify command surfaces now reference
Genuine Fix Discipline from `templates/command-preamble-contract.md` Section 9.
Findings carry behavioral intent cues, `/devspark.site-audit` carries an
`Intent` field, and `/devspark.verify` rejects proof that only shows a metric
decrease while behavior remains unchanged.

## Consequences

### Positive

- Requirement-to-task-to-gate evidence traceability is human-readable and
  mechanically checkable.
- Current JSON consumers remain compatible because the new layer is additive.
- Fix workflows are steered toward behavioral outcomes before metric movement.
- Historical features without knowledge documents remain unblocked.

### Negative

- Feature generation, planning, validation, packaging, and upgrade diagnostics
  now carry additional artifact surfaces to keep in parity.
- Traceability coverage is advisory by default, so teams that want hard
  enforcement must opt into stricter local policy later.