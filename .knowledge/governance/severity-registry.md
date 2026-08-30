---
document: severity-registry
constitution_version: "4.0.0"
last_verified: "2026-08-30"
evidence:
  - type: code
    ref: templates/schemas/devspark-evidence.schema.json/ontology.py
    verified_by: inspection
    test_attempted: true
    fallback_reason: "Severity mapping is governance policy; ontology tests verify required evidence mechanics"
---

# Severity Registry

Findings that cite the DevSpark constitution must use a stable severity and a
clear behavioral intent cue.

## Severity Levels

| Level | Meaning | Expected Disposition |
|---|---|---|
| `SHOWSTOPPER` | Violates a non-negotiable current-truth or safety rule | Block until fixed |
| `HIGH` | Violates a mandatory rule with material workflow or quality risk | Should block merge |
| `MEDIUM` | Partial compliance, weak evidence, or process risk | Address or explicitly accept |
| `LOW` | Improvement opportunity | Advisory |

## Registry Entries

| Constitution Principle | Severity | Trigger |
|---|---|---|
| Current Truth Over Lifecycle History | SHOWSTOPPER | Permanent files preserve or depend on ephemeral lifecycle artifacts |
| Evidence Required | SHOWSTOPPER | Knowledge or governance claim has no evidence |
| Evidence Required | MEDIUM | Inspection evidence lacks a fallback reason |
| Closed Permanent Reference Graph | SHOWSTOPPER | Source comments, knowledge, or governance point back to ephemeral repository artifacts |
| Verify Before Delete | SHOWSTOPPER | A work package is moved out of `.devspark.work` before task linkage verifies |
| One Decision Per Topic | HIGH | Multiple current decisions govern the same topic |
| Explicit Over Implied | SHOWSTOPPER | Scope-affecting context is guessed instead of declared |
| Ownership Boundary | SHOWSTOPPER | Install or upgrade overwrites repository-owned current truth or active work state |
| Platform Parity | HIGH | Bash and PowerShell behavior diverge |
| Genuine Fix Discipline | HIGH | A finding is marked fixed by metric movement without behavioral proof |
| Backward-Compatible Migration | HIGH | Migration overwrites or deletes without dry-run/conflict visibility |

## Finding Codes

Use `principle-slug.severity`, for example:

- `current-truth.showstopper`
- `evidence.medium`
- `platform-parity.high`
- `genuine-fix.high`
