---
participants:
  owner: human
  planner: ai
  implementer: ai
  reviewer: human
  critic: ai
  scribe: ai
---

# Implementation Plan: AGT-Inspired Governance Improvements

**Branch**: `001-agt-governance-improvements` | **Date**: 2026-06-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `.documentation/specs/001-agt-governance-improvements/spec.md`

## Rationale Summary

### Core Problem

DevSpark's constitution and PR review workflow produce informal, inconsistent governance output: severity labels are scattered with no central registry, review depth is uniform regardless of spec-workflow compliance, the framework has no honest public statement of its limits, and command templates can drift from the constitution silently.

### Decision Summary

Four additive Markdown artifacts and one targeted command-template update deliver structured severity codes, trust-tiered review depth, explicit limitations documentation, and prompt conformance checking — all without new tool dependencies or constitution amendments.

### Key Drivers

- Severity registry makes findings machine-trackable and audit-ready across amendment cycles.
- Trust tiers create a self-reinforcing incentive for spec-driven development.
- Limitations document builds adopter trust through intellectual honesty.
- Conformance manifest prevents silent constitution drift in command templates.

### Source Inputs

- Spec: `.documentation/specs/001-agt-governance-improvements/spec.md`
- Research: `.documentation/specs/001-agt-governance-improvements/research.md`
- Constitution v1.4.0: `.documentation/memory/constitution.md`
- Microsoft AGT analysis (conversation context)

### Tradeoffs Considered

- Option A — New script pair for trust-tier detection: rejected (triggers §VI Platform Parity, adds maintenance burden for a simple file-presence check).
- Option B — Hard heading-string match in conformance check: rejected (`evolve-constitution.md` uses variant heading; would false-positive and break §I).
- Selected — Inline trust-tier detection in pr-review + semantic conformance check: minimal footprint, no §VI concern, fully backward-compatible.

### Architectural Impact

- 3 new files under `.documentation/memory/` (severity-registry, known-limitations, prompt-conformance-manifest).
- 1 command template updated (`templates/commands/pr-review.md`) — additive sections only.
- 1 command template updated (`templates/commands/evolve-constitution.md`) — adds two checklist items: severity-registry co-update (FR-009) and known-limitations check (FR-006).
- No changes to spec/plan/tasks templates. No new scripts. No new CI jobs.

### Reviewer Guidance

Verify: severity registry entries match constitution section markers exactly; trust-tier logic is file-presence only (no git history); limitations document is honest and does not overstate DevSpark's scope; conformance check uses semantic evaluation not string-matching.

## Summary

Deliver four governance artifacts (severity registry, known-limitations doc, conformance manifest, pr-review command update) that bring structured severity codes, trust-tiered review depth, explicit limitations, and prompt conformance to DevSpark's existing Markdown-and-conventions model — inspired by Microsoft AGT's governance philosophy, scoped to DevSpark's human-in-the-loop context.

## Technical Context

**Language/Version**: Markdown / YAML (no code language; pure documentation and template changes)
**Primary Dependencies**: DevSpark framework conventions; `npx markdownlint-cli2` (already required by §VIII)
**Storage**: `.documentation/memory/` (three new files); `templates/commands/` (two updated files)
**Testing**: Manual validation via `/devspark.checklist`; markdownlint CI (already enforced)
**Target Platform**: Any DevSpark-installed repository; source repo (`c:\GitHub\MarkHazleton\DevSpark`)
**Project Type**: Documentation / governance tooling
**Performance Goals**: N/A — static Markdown files
**Constraints**: No new tool dependencies (§V Simplicity); no `.devspark/` writes (§III); no script changes (avoids §VI parity requirement)
**Scale/Scope**: 5 files total (3 new, 2 updated); ~250–400 lines of Markdown

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| §I Backward Compatibility (NON-NEGOTIABLE) | ✅ Pass | All changes additive; no existing file restructured |
| §II Explicit Over Implied (NON-NEGOTIABLE) | ✅ Pass | Severity codes, trust tiers, and conformance rules are explicit declarations |
| §III Ownership Boundary (NON-NEGOTIABLE) | ✅ Pass | New files in `.documentation/memory/` (repo-owned); no `.devspark/` writes |
| §IV Governance Authority | ✅ Pass | Registry is companion to constitution; constitution remains authoritative |
| §V Simplicity | ✅ Pass | No new tools, no new scripts, `/devspark.checklist` reused |
| §VI Platform Parity (MUST) | ✅ N/A | No new scripts in this plan |
| §VII PR Review Artifact Commit Discipline (MUST) | ✅ Pass | Enforced in tasks as commit isolation requirement |
| §VIII Markdown Quality (MUST) | ✅ Pass | All new `.md` files pass markdownlint before merge; tracked as explicit task |

**Gate result: PASS — no violations, no waivers required.**

## Project Structure

### Documentation (this feature)

```text
.documentation/specs/001-agt-governance-improvements/
├── spec.md                  ✅ Complete
├── research.md              ✅ Complete (Phase 0)
├── plan.md                  ✅ This file (Phase 1)
├── checklists/
│   └── requirements.md      ✅ Complete
└── tasks.md                 ⬜ Phase 2 (/devspark.tasks)
```

### New Governance Artifacts (repository root)

```text
.documentation/memory/
├── constitution.md                    (existing — unchanged)
├── severity-registry.md               ⬜ NEW — P1 deliverable
├── known-limitations.md               ⬜ NEW — P3 deliverable
└── prompt-conformance-manifest.md     ⬜ NEW — P4 deliverable

templates/commands/
├── pr-review.md                       ⬜ UPDATED — trust-tier + severity code sections
└── evolve-constitution.md             ⬜ UPDATED — severity-registry co-update checklist item
```

**Structure Decision**: All new files under `.documentation/memory/` per §III. Command template changes are in-place edits.

## Complexity Tracking

> No constitution violations requiring justification.

---

## Phase 1: Design & Contracts

### 1. Severity Registry Design

**File**: `.documentation/memory/severity-registry.md`

**YAML frontmatter fields**:

```yaml
---
document: severity-registry
constitution_version: "1.4.0"
last_updated: "2026-06-03"
authoritative_source: .documentation/memory/constitution.md
---
```

**Table columns**: `section` | `principle` | `severity` | `trigger` | `finding_code` | `remediation`

**Entries** (from research.md inventory of all constitution severity markers):

| Section | Principle | Severity | Finding Code |
|---|---|---|---|
| §I | Backward Compatibility | SHOWSTOPPER | `§I.SHOWSTOPPER` |
| §II | Explicit Over Implied | SHOWSTOPPER | `§II.SHOWSTOPPER` |
| §III | Ownership Boundary | SHOWSTOPPER | `§III.SHOWSTOPPER` |
| §IV | Governance Authority | SHOWSTOPPER | `§IV.SHOWSTOPPER` |
| §VI | Platform Parity | HIGH | `§VI.HIGH` |
| §VII | PR Review Artifact Commit Discipline | MEDIUM | `§VII.MEDIUM` |
| §VIII | Markdown Quality (CI block) | HIGH | `§VIII.HIGH` |
| §VIII | Markdown Quality (pre-push) | MEDIUM | `§VIII.MEDIUM` |

### 2. Known Limitations Document Design

**File**: `.documentation/memory/known-limitations.md`

**Entry structure per limitation**:

```text
### L-NNN — [Limitation Name]
**Scope**: What DevSpark does NOT govern here
**Rationale**: Why this is structurally out of scope
**Complementary tooling**: What to use instead (if applicable)
```

**Six limitations to document on day one**:

- L-001: Runtime agent behavior (use Microsoft AGT for production enforcement)
- L-002: Outcome verification (DevSpark records compliance attempts, not production outcomes)
- L-003: Cross-session workflow sequences (individual PR compliance only, not epic ordering)
- L-004: Technical enforcement (gates are advisory; enforcement relies on team culture + optional CI hooks)
- L-005: AI context provenance (DevSpark reviews artifacts, not what context the AI used to produce them)
- L-006: Direct-constitution-edit bypass (direct edits to `constitution.md` without `/devspark.evolve-constitution` leave severity registry and known-limitations silently stale; mitigation: severity-registry.md carries a maintenance note)

### 3. Prompt Conformance Manifest Design

**File**: `.documentation/memory/prompt-conformance-manifest.md`

**Three required elements** evaluated with deterministic string-match anchors per command template:

1. **Constitution authority block**: file contains the string `constitution.md` AND the word `non-negotiable` within 15 lines of each other — OR the file is listed in the Known Variant Headings section with its qualifying text documented
2. **Frontmatter `handoffs` key**: the YAML frontmatter block contains the key `handoffs:`
3. **Artifact output statement**: file contains at least one of the phrases `Write`, `Save`, `Create`, `Generate`, or `Output` within a section describing what the command produces

These anchors make evaluation reproducible across different agent runs without requiring exact heading matches.

**Known variant headings** (pre-documented to prevent false positives):

- `evolve-constitution.md` uses `## Lifecycle Position` instead of `## Constitution Authority` — semantically equivalent

**Finding ID pattern**: `conformance-{command-name}-{01|02|03}`

### 4. PR Review Command Update Design

**File**: `templates/commands/pr-review.md` — two additive insertions:

**Insertion A — Trust-Tier Classification step** (new step 1b, between Initialize Review Context and Load Constitution):

- Detect branch, derive spec dir, check 3 file presences (spec.md, plan.md, tasks.md)
- Classify: full-compliance / partial-compliance / no-compliance
- Emit MEDIUM finding for no-compliance using Shared Review Resolution Contract schema
- `finding_id`: `trust-tier-01`, `severity`: medium, `execution_mode`: manual

**Insertion B — Severity Code Format guidance** (append to Severity Guidelines section after the line `| Constitution needs updating (not code) | CON | Governance improvement |`):

- Mandate `§{section}.{LEVEL}` format for all constitution-linked findings
- Document examples: `§VI.HIGH`, `§VII.MEDIUM`, `§VIII.HIGH`, `§I.SHOWSTOPPER`
- Rule for non-constitution findings: no `§` code, flag as CON candidate

**Insertion C — Registry load instruction** (add sub-bullet to step "### 2. Load Constitution"):

- "Load `.documentation/memory/severity-registry.md` if it exists; use its entries to validate `§{section}.{LEVEL}` codes when emitting findings" — makes the registry visible to the AI agent performing the review, not just to human readers

### 5. Evolve-Constitution Command Update Design

**File**: `templates/commands/evolve-constitution.md` — two checklist items added to the Review Checklist in Step 5:

```text
- [ ] If the amendment adds, removes, or modifies a severity marker,
      `.documentation/memory/severity-registry.md` is updated in the same PR (FR-009)
- [ ] Check whether the amendment implies new governance limitations; if so,
      update `.documentation/memory/known-limitations.md` in the same PR (FR-006)
```

---

## Interface Contracts

### Severity Code Contract

Format: `§{roman-numeral}.{SEVERITY}` where SEVERITY ∈ {SHOWSTOPPER, HIGH, MEDIUM, LOW}

- Registry at `.documentation/memory/severity-registry.md` is the authoritative lookup.
- Commands that cannot map a finding to a registry entry MUST NOT invent a `§` code.
- Un-mapped findings are emitted without a `§` code and optionally flagged as CON candidates.

### Trust Tier Contract

- Computed fresh on each `/devspark.pr-review` run — not persisted.
- File-presence only — no git history analysis, no lifecycle state check.
- A Draft-status spec.md counts as present (existence matters, not lifecycle state).
- Not a gate — adjusts scrutiny and emits a finding; does not block the review.

### Conformance Manifest Evaluation Contract

- Evaluation is semantic — agent reads each template and determines governance content presence.
- `finding_id` pattern: `conformance-{command-name}-{N}` (e.g., `conformance-pr-review-01`)
- Pass = no findings. Fail = one finding per missing element per template.
- The manifest itself is not evaluated against itself.
