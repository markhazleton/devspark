# Release Notes: v2.5.0

## Release Metadata

- **Version**: v2.5.0
- **Release Date**: 2026-06-05
- **Release Window**: 2026-04-18 → 2026-06-05
- **Previous Version**: v2.4.0
- **Commit Range**: `1eb4f46c..297b6ab5` (`v2.4.0..HEAD`)
- **Commits**: 22
- **Contributors**: 4
- **Merged PRs**: 7 (#41, #42, #43, #44, #46, #47, #48, #49)

## Highlights

v2.5.0 re-platforms DevSpark from a curated prompt library into a governed orchestration engine. The headline delivery is the **Tiered Prompt and Workflow Engine** — three new artifact layers (atomic prompts, workflow YAML, alias entrypoints) wired by a Python workflow runner that enforces autonomy guardrails, pauses for human review, and writes structured telemetry. Three flagship aliases (`create-spec`, `execute-plan`, `suggest-improvement`) give beginners discoverable entrypoints without disrupting the expert atomic command surface.

This release also introduces two vocabulary and governance advances. **Participant Roles** resolves a long-standing terminology ambiguity: `participant` now denotes human or AI-filled team members while `agent` remains reserved for AI runtime integrations. **AGT-Inspired Governance Improvements** bring structured severity codes, trust-tiered PR review depth, a known-limitations document, and a prompt conformance manifest — all as additive Markdown artifacts with no new tool dependencies.

Four architectural decisions (ADR-004 through ADR-007) are ratified and stored in `.documentation/decisions/`, providing durable context for every significant choice made during this cycle.

## New Features

### Tiered Prompt and Workflow Engine

DevSpark now ships three orchestration layers under `templates/`:

- `templates/prompts/atomic/` — 28 atomic prompt shims (one per legacy command)
- `templates/workflows/` — YAML workflow definitions (`create-spec.yaml`, `execute-plan.yaml`, `suggest-improvement.yaml`)
- `templates/aliases/` — Alias entrypoints mapping high-level names to workflows

The Python workflow runner (`src/devspark_cli/runner/`) enforces autonomy guardrails, evaluates `when` expressions, pauses at `review_after` steps, and writes JSON Lines telemetry. A shim-drift CI job ensures atomic prompts never fall out of sync with command sources.

**New CLI**: `devspark run <alias|workflow>`, `devspark workflows`, `devspark runs`, `devspark resume`, `devspark help`.

**Spec**: [View archived spec](specs/001-interactive-analyze-flow/spec.md)

### Participant Roles

Introduces `participant` as the canonical vocabulary for team members carrying workflow responsibility. Optional `participants` YAML frontmatter can now appear in any spec, plan, or task file:

```yaml
participants:
  owner: human
  planner: ai
  implementer: ai
  reviewer: human
  critic: ai
  scribe: ai
```

Metadata is advisory only — it does not affect prompt resolution, command behavior, or backward compatibility.

**Spec**: [View archived spec](specs/001-participant-roles/spec.md)

### AGT-Inspired Governance Improvements

Four additive governance artifacts inspired by Microsoft AGT's governance philosophy:

- **Severity registry** — finding codes in `§{section}.{LEVEL}` format matching constitution markers
- **Known-limitations document** — honest public statement of DevSpark's scope boundaries
- **Prompt conformance manifest** — semantic checklist for command template governance drift
- **Trust-tier PR review** — spec-backed PRs: standard depth; spec-less PRs: elevated scrutiny + MEDIUM finding

**Spec**: [View archived spec](specs/001-agt-governance-improvements/spec.md)

## Bug Fixes

- **Agent Skills install gap** (#42, #43, #44): `templates/skills/` was not installed by any quickstart or upgrade. All five quickstart guides now include Step 5.5 fetching the full skills tree.
- **Cross-platform script install** (#46): All quickstarts now unconditionally install both Bash and PowerShell script sets. `address-pr-review.md` `sh` variant fixed to use the native Bash script.

## Breaking Changes

None.

## Deprecations

None.

## Architectural Decisions

- **ADR-004**: Tiered Prompt and Workflow Architecture — [View](../../decisions/ADR-004.md)
- **ADR-005**: Participant Vocabulary — Reserving `agent` for AI Runtimes — [View](../../decisions/ADR-005.md)
- **ADR-006**: AGT-Inspired Governance — Severity Registry, Trust Tiers, and Conformance Manifest — [View](../../decisions/ADR-006.md)
- **ADR-007**: Harness Workflow Fixture as Spec Lifecycle Compliance Artifact — [View](../../decisions/ADR-007.md)

## Deferred Features

None — all specs in this cycle are complete.

## Upgrade Guide

No breaking changes. To upgrade existing consumer projects:

```bash
devspark upgrade
```

The upgrade will install the new `templates/prompts/atomic/`, `templates/workflows/`, and `templates/aliases/` surfaces plus updated scripts. All existing `/devspark.*` slash commands continue to resolve unchanged.

## Metrics

| Metric | Value |
|--------|-------|
| Features Delivered | 4 |
| Bugs Fixed | 2 |
| PRs Merged | 8 |
| ADRs Created | 4 |
| Contributors | 4 |
| Commits | 22 |
| Breaking Changes | 0 |

---

Release documentation generated by /devspark.release v1.0
