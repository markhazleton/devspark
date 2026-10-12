---
document: severity-registry
constitution_version: "1.8.0"
last_updated: "2026-09-30"
authoritative_source: .knowledge/governance/constitution.md
---

# DevSpark Severity Registry

This document is the authoritative mapping from constitution sections to severity levels
and finding codes used by `/devspark-pr-review` and other governance commands.

## Purpose

Every finding emitted by a DevSpark governance command that references a constitution
principle MUST use a finding code from this registry in the format `§{section}.{LEVEL}`.
This makes findings machine-trackable, audit-ready, and consistent across amendment cycles.

## Maintenance Note

> **IMPORTANT**: If `constitution.md` is amended directly without using
> `/devspark-evolve-constitution`, the author MUST manually verify and update this
> registry in the same PR. The `/devspark-evolve-constitution` workflow enforces this
> via its review checklist, but direct edits bypass that gate.

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
| §I | Backward Compatibility | SHOWSTOPPER | `§I.SHOWSTOPPER` | Existing repository is forced to restructure outside an explicit framework-version boundary, or install/upgrade performs migration automatically | Make migration an explicit human-run action at a documented version boundary |
| §II | Explicit Over Implied | SHOWSTOPPER | `§II.SHOWSTOPPER` | Scope, review scope, or governance scope inferred from working directory, branch name, or heuristic detection rather than declared explicitly | Add explicit scope declaration; replace heuristic with required argument |
| §III | Ownership Boundary | SHOWSTOPPER | `§III.SHOWSTOPPER` | Install or upgrade adds, removes, or modifies files under `.devspark.work/`, `.knowledge/`, or `.archive/` | Move framework payload writes to `.devspark/`; keep every repository-owned root untouched |
| §IV | Governance Authority | SHOWSTOPPER | `§IV.SHOWSTOPPER` | Application-level governance weakens a mandatory repo-wide rule from `constitution.md` | Restore the stricter repo-wide rule; app-level governance may only extend or strengthen |
| §VI | Platform Parity | HIGH | `§VI.HIGH` | A script in `scripts/bash/` is updated without a matching update in `scripts/powershell/`, or vice versa; or install/upgrade delivers only one script set | Add the corresponding script in the other language in the same commit |
| §VII | PR Review Artifact Commit Discipline | MEDIUM | `§VII.MEDIUM` | The PR review file (`.devspark.work/pr-review/pr-NNN.md`) is committed in the same commit as production code, tests, or other docs | Split into two commits: one for the review file only, one for all other changes |
| §VIII | Markdown Quality (CI block) | HIGH | `§VIII.HIGH` | A markdown file with markdownlint errors is merged to the default branch, blocking the CI lint job | Fix all markdownlint errors before merging; run `npx markdownlint-cli2 "**/*.md"` locally first |
| §VIII | Markdown Quality (pre-push) | MEDIUM | `§VIII.MEDIUM` | Markdownlint errors caught locally before push (non-blocking in CI) | Fix errors before pushing; use editor markdownlint integration for real-time feedback |
| §IX | Verification Command Discipline (CI block) | HIGH | `§IX.HIGH` | An unbounded or interactive command hangs a CI job, or a test reaches a live service or requires credentials | Add an explicit timeout, make the command non-interactive, and move the test onto recorded fixtures |
| §IX | Verification Command Discipline | MEDIUM | `§IX.MEDIUM` | A test subprocess omits `timeout=`, or verification output is piped through `tail`/`Select-Object -Last`/`Out-File` so failures are hidden until completion | Pass an explicit `timeout=`; stream the output, using `Tee-Object` when a log is also needed |
| §X | Knowledge Currency (divergence) | HIGH | `§X.HIGH` | Durable behavior changed without the Knowledge describing it changing in the same change; derived Knowledge artifacts left out of date; an advisory discovery finding treated as authoritative truth | Update the owning `.knowledge/` document in the same change and regenerate the derived artifacts; accept a finding explicitly before authoring from it |
| §X | Knowledge Currency (bounding) | MEDIUM | `§X.MEDIUM` | Agent context is unbounded or unprovenanced — whole-corpus injection, a private search path outside the canonical pipeline, or a hop budget that differs from the contract | Resolve context through retrieval → projection → judgment and record provenance in `context_resolved` |
| §X | Knowledge Currency (planning leakage) | MEDIUM | `§X.MEDIUM` | Durable code, tests, or `.knowledge/` content references the temporary planning record that produced it | Remove the planning identifier; keep traceability one-directional from the temporary record to code, tests, and Knowledge |

## Finding Code Format

```text
§{roman-numeral-section}.{SEVERITY}
```

**Examples**: `§VI.HIGH`, `§VII.MEDIUM`, `§VIII.HIGH`, `§IX.MEDIUM`, `§X.HIGH`, `§I.SHOWSTOPPER`

**For findings not mapped to any constitution section**: emit the finding without a `§`
code and flag it as a `CON` candidate for `/devspark-evolve-constitution`.

## Companion Documents

- [Known Governance Limitations](known-limitations.md)
- [Constitution](constitution.md)
- [Knowledge Framework Contract](knowledge-framework-contract.md)
