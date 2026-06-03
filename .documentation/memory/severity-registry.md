---
document: severity-registry
constitution_version: "1.4.0"
last_updated: "2026-06-03"
authoritative_source: .documentation/memory/constitution.md
---

# DevSpark Severity Registry

This document is the authoritative mapping from constitution sections to severity levels
and finding codes used by `/devspark.pr-review` and other governance commands.

## Purpose

Every finding emitted by a DevSpark governance command that references a constitution
principle MUST use a finding code from this registry in the format `§{section}.{LEVEL}`.
This makes findings machine-trackable, audit-ready, and consistent across amendment cycles.

## Maintenance Note

> **IMPORTANT**: If `constitution.md` is amended directly without using
> `/devspark.evolve-constitution`, the author MUST manually verify and update this
> registry in the same PR. The `/devspark.evolve-constitution` workflow enforces this
> via a Review Checklist item (FR-009), but direct edits bypass that gate.

## Severity Levels

| Level | Description | Effect on PR |
|---|---|---|
| `SHOWSTOPPER` | Violates a NON-NEGOTIABLE principle — blocks merge | Hard block |
| `HIGH` | Violates a MUST requirement significantly | Should block merge |
| `MEDIUM` | Partial compliance or process finding | Should be addressed before merge |
| `LOW` | Minor improvement opportunity | Advisory only |

## Registry Entries

| Section | Principle | Severity | Finding Code | Trigger | Remediation Example |
|---|---|---|---|---|---|
| §I | Backward Compatibility | SHOWSTOPPER | `§I.SHOWSTOPPER` | Existing single-app repo forced to restructure or change behavior without opt-in | Revert breaking change; make new capability additive and opt-in only |
| §II | Explicit Over Implied | SHOWSTOPPER | `§II.SHOWSTOPPER` | Scope, review scope, or governance scope inferred from working directory, branch name, or heuristic detection rather than declared explicitly | Add explicit scope declaration; replace heuristic with required argument |
| §III | Ownership Boundary | SHOWSTOPPER | `§III.SHOWSTOPPER` | Install or upgrade flow adds, removes, or modifies files under any `.documentation/` directory | Move all install/upgrade writes to `.devspark/`; never touch `.documentation/` in framework operations |
| §IV | Governance Authority | SHOWSTOPPER | `§IV.SHOWSTOPPER` | Application-level governance weakens a mandatory repo-wide rule from `constitution.md` | Restore the stricter repo-wide rule; app-level governance may only extend or strengthen |
| §VI | Platform Parity | HIGH | `§VI.HIGH` | A script in `scripts/bash/` is updated without a matching update in `scripts/powershell/`, or vice versa; or install/upgrade delivers only one script set | Add the corresponding script in the other language in the same commit |
| §VII | PR Review Artifact Commit Discipline | MEDIUM | `§VII.MEDIUM` | The PR review file (`.documentation/specs/pr-review/pr-NNN.md`) is committed in the same commit as production code, tests, or other docs | Split into two commits: one for the review file only, one for all other changes |
| §VIII | Markdown Quality (CI block) | HIGH | `§VIII.HIGH` | A markdown file with markdownlint errors is merged to the default branch, blocking the CI lint job | Fix all markdownlint errors before merging; run `npx markdownlint-cli2 "**/*.md"` locally first |
| §VIII | Markdown Quality (pre-push) | MEDIUM | `§VIII.MEDIUM` | Markdownlint errors caught locally before push (not yet blocking CI) | Fix errors before pushing; use editor markdownlint integration for real-time feedback |

## Finding Code Format

```text
§{roman-numeral-section}.{SEVERITY}
```

**Examples**: `§VI.HIGH`, `§VII.MEDIUM`, `§VIII.HIGH`, `§I.SHOWSTOPPER`

**For findings not mapped to any constitution section**: emit the finding without a `§`
code and flag it as a `CON` candidate for `/devspark.evolve-constitution`.

## Companion Documents

- [Known Governance Limitations](known-limitations.md)
- [Constitution](constitution.md)
