---
classification: full-spec
risk_level: medium
risk_profile: internal
archetype: documentation-site
change_type: brownfield
target_workflow: specify-full
required_artifacts: spec, plan, tasks
recommended_next_step: plan
required_gates: checklist, analyze, critic
participants:
  owner: human
  planner: ai
  implementer: ai
  reviewer: human
  critic: ai
  scribe: ai
---

# Feature Specification: AGT-Inspired Governance Improvements

**Feature Branch**: `001-agt-governance-improvements`
**Created**: 2026-06-03
**Status**: Complete <!-- Valid: Draft | In Progress | Complete -->
**Input**: User description: "Incorporate governance improvements inspired by Microsoft AGT analysis: structured severity registry, trust-tiered review depth, explicit limitations documentation, and prompt conformance tests"

## Rationale Summary

### Core Problem

DevSpark's constitution and PR review workflow enforce quality gates, but the findings they produce are informal: severity labels (HIGH/MEDIUM) are scattered across constitution sections with no central registry, review depth does not vary based on whether the spec-driven workflow was actually followed, the framework makes no honest public statement about what it does and does not govern, and command prompt templates have no automated validation to detect constitution drift. These gaps mean governance is harder to measure, easier to bypass, and opaque to new adopters.

### Decision Summary

Extend DevSpark's existing process governance with four targeted improvements borrowed from the Microsoft Agent Governance Toolkit's architectural philosophy: a structured severity registry, trust-tiered review depth, an explicit limitations document, and a prompt conformance lint check. All four improvements are additive and backward-compatible — no existing workflows are removed or restructured.

### Key Drivers

- **Consistency**: PR review findings reference constitution sections inconsistently, making aggregate tracking impossible.
- **Incentive alignment**: Review rigor should reflect actual workflow compliance — a PR backed by a complete spec deserves faster review than one with no spec.
- **Intellectual honesty**: Adopters need to know what DevSpark governs and what it does not, matching AGT's own documented limitations model.
- **Constitution integrity**: Command prompt templates can drift from the constitution after amendments without any automated detection.

### Tradeoffs Considered

- **Option A — Full runtime enforcement (AGT-style)**: Cryptographic audit trails, policy engines, execution rings. Rejected: DevSpark operates in developer workflows with a human always present; runtime enforcement infrastructure is over-engineering for this trust context.
- **Option B — Ignore AGT findings**: Simpler, no changes. Rejected: the four identified gaps are real, lightweight to address, and improve long-term governance coherence.
- **Selected — Targeted process improvements**: Adopt AGT's *philosophy* (structured severity, trust tiers, honest limitations, conformance testing) without adopting its runtime infrastructure. Fits DevSpark's markdown-and-conventions model.

### Architectural Impact

- New file: `.documentation/memory/known-limitations.md` (additive, no existing file displaced)
- New file: `.documentation/memory/severity-registry.md` (additive; becomes the authoritative severity mapping)
- Constitution referenced but not amended — severity registry is a companion document, not a constitution change
- PR review command (`templates/commands/pr-review.md`) updated to reference severity registry and trust-tier logic
- New file: `.documentation/memory/prompt-conformance-manifest.md` — Markdown conformance manifest listing three required sections per command template, evaluated via `/devspark.checklist`; no new tool dependencies
- Updated file: `templates/commands/evolve-constitution.md` — adds two checklist items: severity-registry co-update (FR-009) and known-limitations check (FR-006)

### Reviewer Guidance

Reviewers should verify: (1) the severity registry is consistent with existing constitution section markers; (2) trust-tier thresholds are objective and checkable from git/branch state; (3) the limitations document is honest and does not overstate what DevSpark governs; (4) prompt conformance checks are lightweight enough to not block contribution workflows.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Structured Severity Registry (Priority: P1) ✅ Complete

A DevSpark contributor reviews a PR using `/devspark.pr-review`. The review produces findings, each tagged with a severity code that links back to a specific constitution section (e.g., `§VIII.HIGH`). The contributor can look up any finding in the severity registry to understand its scope, rationale, and remediation guidance without re-reading the full constitution.

**Why this priority**: The severity registry is foundational to the other improvements. Trust-tiered review depth and prompt conformance both produce findings; without a registry, their outputs are as inconsistent as the current state.

**Independent Test**: Run `/devspark.pr-review` on any open PR. Verify that every finding in the output includes a severity code matching a registry entry, and that the registry file exists at `.documentation/memory/severity-registry.md`.

**Acceptance Scenarios**:

1. **Given** a PR review is generated, **When** a finding is emitted with severity HIGH, **Then** it includes a section reference (e.g., `§VI.HIGH`) that maps to an entry in the severity registry.
2. **Given** the severity registry exists, **When** a user looks up a section reference, **Then** they find: the constitution section, severity level, description, and example remediation.
3. **Given** a constitution amendment is ratified, **When** the amendment introduces or changes a severity marker, **Then** the severity registry is updated in the same PR.

---

### User Story 2 — Trust-Tiered Review Depth (Priority: P2) ✅ Complete

A developer submits a PR on a branch that has a complete spec, plan, and tasks in `.documentation/specs/`. The PR review runs at standard depth. A second developer submits a PR on a branch with no spec artifacts. The review runs at elevated depth, explicitly noting the missing workflow compliance as a finding.

**Why this priority**: Creates a positive incentive to follow the spec-driven workflow. PRs that skip the process get more scrutiny, not less — making the governance self-reinforcing without requiring enforcement machinery.

**Independent Test**: Submit two PRs — one on a branch with complete spec artifacts, one without. Verify the review output for the spec-less branch includes a trust-tier finding and performs a deeper check pass than the spec-complete branch.

**Acceptance Scenarios**:

1. **Given** a PR branch has a `spec.md`, `plan.md`, and tasks file under `.documentation/specs/`, **When** `/devspark.pr-review` runs, **Then** the review runs at standard depth and notes the workflow compliance positively.
2. **Given** a PR branch has no spec artifacts, **When** `/devspark.pr-review` runs, **Then** the review emits a trust-tier finding (MEDIUM severity) and applies an elevated scrutiny pass to all other findings.
3. **Given** a PR branch has a spec but no plan, **When** `/devspark.pr-review` runs, **Then** the review notes partial compliance and applies a moderate scrutiny adjustment.

---

### User Story 3 — Explicit Limitations Documentation (Priority: P3) ✅ Complete

A team evaluating DevSpark reads `.documentation/memory/known-limitations.md` and learns what the framework does and does not govern — before discovering a gap in production. They can make an informed decision about what complementary tooling they need.

**Why this priority**: Intellectual honesty improves trust and reduces support burden. Adopters who understand the boundaries make better architectural decisions.

**Independent Test**: The file `.documentation/memory/known-limitations.md` exists, is non-empty, lists at least four distinct limitations with rationale, and is referenced from `constitution.md` or the project README.

**Acceptance Scenarios**:

1. **Given** a new team evaluates DevSpark, **When** they read `known-limitations.md`, **Then** they find at least four explicitly described governance gaps with honest rationale for why they are out of scope.
2. **Given** a limitation is discovered in a PR review or constitution evolution session, **When** the limitation is confirmed as structural (not a bug), **Then** it is documented in `known-limitations.md` in the same PR.
3. **Given** `known-limitations.md` exists, **When** the constitution is amended, **Then** the amendment process checks whether any new limitations are implied and updates the file if so.

---

### User Story 4 — Prompt Conformance Lint (Priority: P4) ✅ Complete

A contributor edits a command template in `templates/commands/`. Before the PR is merged, a conformance check verifies the template still references required sections (constitution check gate, artifact output format, handoff labels) and has not silently dropped governance-critical content. The check produces a pass/fail report.

**Why this priority**: Command templates are the primary delivery mechanism for DevSpark's governance. If they drift from the constitution, the entire framework degrades silently.

**Independent Test**: Edit a command template to remove a required section (e.g., the Constitution Authority block). Run the conformance check. Verify it reports a failure. Restore the section and verify it passes.

**Acceptance Scenarios**:

1. **Given** a command template has all required sections, **When** the prompt conformance check runs, **Then** it reports all checks passed.
2. **Given** a command template is missing the `Constitution Authority` section, **When** the conformance check runs, **Then** it reports a HIGH severity finding citing `§IV`.
3. **Given** the conformance check runs in CI, **When** any command template fails, **Then** the CI job fails and the PR cannot merge without remediation.

---

### Edge Cases

- What happens when a PR branch name does not follow the `NNN-short-name` convention? The trust-tier check should treat it as no-spec (lowest trust tier) and note the naming gap.
- What happens when a spec artifact exists but is in `Draft` status and the PR touches unrelated files? Standard depth review applies — spec existence matters, not completeness of implementation.
- What happens when the severity registry and a constitution section marker conflict? The constitution is authoritative; the registry must be updated, not the constitution.
- What happens when `constitution.md` is amended by a direct file edit without using `/devspark.evolve-constitution`? The severity registry and `known-limitations.md` are not automatically updated. The severity registry document itself carries a maintenance note requiring the author to manually verify and update both companion documents in the same PR. This gap is documented as L-006 in `known-limitations.md`.
- What happens when a new command is added without a corresponding prompt conformance rule? The conformance manifest defines a default behavior: template files in `templates/commands/` not explicitly listed in the manifest are evaluated against the three universal required elements (Constitution Authority block, `handoffs` frontmatter, artifact output statement) — no special rule needed, and any file failing those elements is flagged as a LOW finding requiring attention.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The severity registry MUST map every constitution section that carries a severity marker (HIGH, MEDIUM) to a structured entry containing: section reference, severity level, description, and example remediation guidance. The registry document MUST use YAML frontmatter for document metadata and a Markdown table (one row per constitution section) for entries — making it both human-readable and parseable by a script without new tool dependencies.
- **FR-002**: The PR review command MUST emit findings in structured YAML format matching the Shared Review Resolution Contract schema (finding_id, severity, description, recommended_action, execution_mode, status, outcome), with severity codes in the format `§{section}.{LEVEL}` matching entries in the severity registry. This enables `/devspark.address-pr-review` and `/devspark.harvest` to act on findings deterministically without new parsing logic.
- **FR-003**: The PR review command MUST detect whether a branch has spec artifacts (spec.md, plan.md, tasks file) and classify the branch into a trust tier (full-compliance, partial-compliance, no-compliance).
- **FR-004**: The PR review command MUST adjust its review depth based on the detected trust tier — no-compliance branches MUST receive an elevated scrutiny pass implemented as: (a) a MEDIUM trust-tier finding using the Shared Review Resolution Contract schema, and (b) an explicit inline reminder to the reviewer to apply heightened attention to all other findings in the report.
- **FR-005**: The `known-limitations.md` file MUST exist at `.documentation/memory/known-limitations.md` and MUST document at least five distinct governance limitations with rationale for why each is out of scope. One entry (L-006) MUST document the direct-constitution-edit bypass gap: that direct edits to `constitution.md` without using `/devspark.evolve-constitution` leave the severity registry and known-limitations doc silently stale.
- **FR-006**: The constitution amendment process MUST include a check for whether the amendment implies new limitations that should be added to `known-limitations.md`.
- **FR-007**: A prompt conformance check MUST exist that validates command templates in `templates/commands/` against three required sections present in every well-formed command: (1) `## Constitution Authority` block, (2) frontmatter `handoffs` block, and (3) at least one artifact output statement. The check is implemented as a Markdown conformance manifest at `.documentation/memory/prompt-conformance-manifest.md` invoked via `/devspark.checklist` — no new scripts or tool dependencies required.
- **FR-008**: The prompt conformance check MUST report findings with severity codes from the severity registry and MUST be runnable without installing external tools beyond what DevSpark already requires. The AI agent reads the conformance manifest and validates each template file inline, producing a structured pass/fail report.
- **FR-009**: The severity registry MUST be updated in the same PR as any constitution amendment that adds, removes, or modifies a severity marker — this co-update MUST be required as a checklist item in the `evolve-constitution` workflow.

### Key Entities

- **Severity Registry**: A structured document (YAML frontmatter + Markdown table, one row per constitution section) mapping constitution sections to severity levels, descriptions, and remediation guidance. Lives at `.documentation/memory/severity-registry.md`.
- **Trust Tier**: A classification (full-compliance / partial-compliance / no-compliance) assigned to a PR branch based on the presence of spec artifacts. Determined at review time from branch file state.
- **Known Limitations**: A document cataloguing what DevSpark does not govern, with honest rationale. Lives at `.documentation/memory/known-limitations.md`.
- **Prompt Conformance Rule**: A defined assertion about a required section or structural element in a command template. Rules are maintained in a Markdown conformance manifest at `.documentation/memory/prompt-conformance-manifest.md` and evaluated by an AI agent via `/devspark.checklist` — no new scripts or tooling required.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every PR review finding produced by `/devspark.pr-review` includes a severity code matching an entry in the severity registry — verifiable by reading any review output against the registry.
- **SC-002**: A PR on a branch with no spec artifacts receives a trust-tier finding (MEDIUM) and at least one additional scrutiny pass not present in a spec-complete PR review — verifiable by comparing two review outputs side-by-side.
- **SC-003**: `known-limitations.md` documents at least four limitations on day one of merge, and grows monotonically as new gaps are identified in constitution evolution sessions.
- **SC-004**: The prompt conformance check correctly identifies a missing `Constitution Authority` section in a command template — verifiable by a deliberate test edit and check run.
- **SC-005**: All four improvements are additive — no existing PR reviews, specs, plans, or tasks are invalidated or require migration after merge.
- **SC-006**: The severity registry co-update checklist item is present in `evolve-constitution.md` at merge — verifiable by reading the template. Forward-looking: the next constitution amendment PR demonstrates the checklist item being exercised, verifiable from PR history.

## Clarifications

### Session 2026-06-03

- Q: What format should the severity registry document use? → A: YAML frontmatter for document metadata plus a Markdown table (one row per constitution section) — human-readable and script-parseable without new tool dependencies.
- Q: Should PR review findings be structured or freeform? → A: Structured YAML findings block matching the existing Shared Review Resolution Contract schema (finding_id, severity, description, recommended_action, execution_mode, status, outcome) — consistent with clarify and address-pr-review commands.
- Q: How should the prompt conformance check be invoked? → A: AI agent reads a Markdown conformance manifest and validates each template via `/devspark.checklist` — no new scripts or tool dependencies; CI wiring is a future follow-on.
- Q: Which sections are required in every command template per the conformance manifest? → A: Three sections: `## Constitution Authority` block, frontmatter `handoffs` block, and at least one artifact output statement — present in all existing well-formed commands.
- Q: Where should the conformance manifest live? → A: `.documentation/memory/prompt-conformance-manifest.md` — co-located with `severity-registry.md` and `known-limitations.md` in the governance memory directory, consistent with §III Ownership Boundary.

## Assumptions

- The source repo structure (scripts in `scripts/`, commands in `templates/commands/`) applies throughout — no `.devspark/` prefix needed for script paths.
- The current constitution version (1.4.0) is the baseline; no new constitution amendment is required to ship these improvements (the severity registry is a companion document, not a constitution change).
- Prompt conformance checks are implemented as a Markdown conformance manifest evaluated by an AI agent via `/devspark.checklist` — no new scripts or CI tool dependencies in this iteration.
- Trust tier detection relies on file presence in `.documentation/specs/{branch-name}/` — no git history analysis required.
- The `evolve-constitution` command template is in scope for a minor update to add two checklist items: the severity-registry co-update (FR-009) and the known-limitations check (FR-006).

## Out of Scope

- Runtime enforcement of governance (cryptographic identity, policy engines, execution rings) — DevSpark operates in human-in-the-loop developer workflows where this infrastructure is unnecessary.
- Automated CI integration for prompt conformance in this iteration — the check is defined and runnable manually; CI wiring is a follow-on.
- Changes to existing spec, plan, or tasks templates — improvements are additive to review and meta-documentation only.
- Trust scoring with numeric decay or behavioral regime detection (AGT-style) — binary/ternary tier classification is sufficient for DevSpark's workflow context.
- OWASP, NIST, or EU AI Act compliance mapping — DevSpark governs developer process, not production AI agent behavior.
