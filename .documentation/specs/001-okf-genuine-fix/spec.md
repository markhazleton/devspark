---
classification: full-spec
risk_level: high
archetype: cli
risk_profile: internal
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

# Feature Specification: OKF Traceability and Genuine Fix Discipline

**Feature Branch**: `001-okf-genuine-fix`
**Created**: 2026-08-27
**Status**: Complete
**Input**: Add an additive per-feature knowledge layer for requirement-to-task-to-gate traceability, plus Genuine Fix Discipline guidance that prevents metric-only fixes from being accepted as behavioral repairs.

## Rationale Summary

### Core Problem

DevSpark lifecycle commands already emit machine-readable JSON contracts per feature, but users do not have a human-checkable, mechanically validatable link between requirements, implementation tasks, and gate evidence. Separately, fix and review workflows can be satisfied by lowering a reported metric, such as lint or complexity, without proving that the intended behavior changed.

### Decision Summary

Add a per-feature knowledge layer in structured Markdown with YAML frontmatter, emitted alongside the current JSON contracts, and add Genuine Fix Discipline guidance across the relevant command surfaces. Coverage validation is advisory and fail-soft so existing and historical features remain usable.

### Key Drivers

- Existing JSON contracts are consumed by multiple commands and must remain byte-for-byte compatible for current consumers.
- Published evaluation evidence indicates that bare metric framing produces a low genuine-fix rate, while behavioral-intent framing substantially improves outcomes.
- Review, fix, and verification workflows need a consistent way to preserve the behavior that a finding is meant to protect.
- Traceability should help humans and automation inspect lifecycle evidence without turning old features into blocked work.

### Source Inputs

- User-provided context, findings, goal, user stories, acceptance criteria, design notes, alternatives, and test notes from the triggering request.
- Repository constitution summary was available from the write-spec context gatherer.
- No prior feature specs were returned by the context gatherer.

### Tradeoffs Considered

- Extend existing JSON contracts: rejected because any schema migration or field reshaping could break current JSON consumers.
- Add a parallel Markdown knowledge layer: selected because it supports human review and machine validation while preserving JSON compatibility.
- Make traceability coverage a hard gate: rejected because features that predate the knowledge layer should not be blocked.
- Keep fix guidance as informal prose only: rejected because intent cues must be pinned to command outputs and verification behavior.

### Architectural Impact

- Lifecycle output gains optional, additive knowledge documents for each feature.
- Analyze and critic workflows gain an advisory coverage pass that reports traceability gaps without failing the gate when knowledge is absent.
- Fix, review, audit, and verify workflows gain shared language for proving behavioral intent, not merely metric movement.
- Existing JSON consumers must observe no contract changes.

### Assumptions

- The OKF knowledge layer is additive metadata and does not replace spec, plan, tasks, gate, or JSON artifacts.
- Fail-soft coverage means validator failures are reported as findings or warnings unless a later command explicitly opts into hard enforcement.
- Gate evidence includes analyze, critic, site-audit, verify, checklist, test, or review evidence that substantiates a requirement/task outcome.
- Skipped context: none.

## User Scenarios & Testing

### User Story 1 - OKF Knowledge Documents (Priority: P1) ✅ Complete

As a DevSpark user creating or planning a feature, I want lifecycle scripts to emit structured knowledge documents in parallel with existing JSON outputs so that requirements, tasks, and gate evidence can be reviewed by humans and checked by tools without disrupting existing consumers.

**Why this priority**: Traceability is the primary value of the feature and must exist before validators or downstream guidance can inspect it.

**Independent Test**: Generate a feature and confirm that the feature has a knowledge folder with Markdown documents whose YAML frontmatter validates against the OKF schema, while existing JSON output remains unchanged.

**Acceptance Scenarios**:

1. **Given** a new feature generation request, **When** the lifecycle script completes, **Then** the feature directory contains a knowledge folder with OKF Markdown documents and the existing JSON response keeps the same fields and values as before.
2. **Given** a generated knowledge document, **When** it is validated against the OKF schema, **Then** required identity, traceability, and evidence fields are present and valid.
3. **Given** an existing JSON consumer, **When** the feature generation script runs after this change, **Then** the consumer can parse the JSON response without code changes.

### User Story 2 - Knowledge Coverage Validation (Priority: P2) ✅ Complete

As a reviewer or feature owner, I want analyze and critic workflows to report requirement, task, and gate-evidence coverage so I can see traceability gaps before implementation or review decisions are made.

**Why this priority**: The knowledge layer is only useful if the lifecycle can surface missing links at the points where quality gates already run.

**Independent Test**: Run coverage validation on a feature with knowledge documents, then on a feature without a knowledge folder, and confirm that coverage is reported in the first case and skipped cleanly in the second.

**Acceptance Scenarios**:

1. **Given** a feature with OKF knowledge documents, **When** analyze or critic runs, **Then** it reports requirement, task, and gate-evidence coverage as an additive advisory pass.
2. **Given** a feature without a knowledge folder, **When** analyze or critic runs, **Then** the coverage validator reports a clean skip and does not fail the gate.
3. **Given** incomplete traceability links, **When** coverage validation runs, **Then** the report identifies uncovered requirements, tasks, or gate evidence without modifying existing lifecycle JSON contracts.

### User Story 3 - Genuine Fix Discipline (Priority: P3) ✅ Complete

As a user relying on fix, review, audit, and verification commands, I want findings and proofs to state behavioral intent before metrics so that a command cannot pass by reducing a number while leaving the user-visible or system behavior unchanged.

**Why this priority**: Anti-gaming guidance protects the quality of fixes after traceability exists and applies across multiple command surfaces.

**Independent Test**: Produce findings and verification proof for a metric-related issue and confirm that findings include behavioral intent cues, site-audit findings include Intent, and verify rejects proof that only shows metric reduction with unchanged behavior.

**Acceptance Scenarios**:

1. **Given** an analyze or critic finding, **When** the command writes the finding, **Then** it carries an intent cue describing the behavior that must be preserved or repaired.
2. **Given** a site audit finding, **When** the command writes the finding, **Then** it includes an Intent field before any metric-focused remediation.
3. **Given** a verification proof that only shows a metric decrease while behavior is unchanged, **When** verify evaluates it, **Then** the proof fails Genuine Fix Guard review.
4. **Given** a fix or review command, **When** it references the shared command preamble guidance, **Then** it prioritizes behavioral intent over satisfying a bare metric.

### Edge Cases

- A feature predates the knowledge layer and has no knowledge folder.
- A knowledge folder exists but contains no valid OKF Markdown documents.
- A requirement is linked to tasks but has no gate evidence.
- Gate evidence exists but references no requirement or task.
- A task resolves a finding by changing a metric while tests, user behavior, or observable outcomes are unchanged.
- A command runs in a repository with app-scoped documentation rather than repository-root documentation.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST emit per-feature OKF knowledge documents in structured Markdown with YAML frontmatter when new feature lifecycle artifacts are generated.
- **FR-002**: The system MUST preserve existing JSON command contracts so current JSON consumers can continue operating without migration.
- **FR-003**: The system MUST provide a schema that validates OKF knowledge document frontmatter and traceability fields.
- **FR-004**: The system MUST support mechanical requirement-to-task-to-gate-evidence traceability checks using the knowledge documents.
- **FR-005**: The system MUST provide coverage validation that reports requirement, task, and gate-evidence coverage.
- **FR-006**: The system MUST run knowledge coverage validation as an additive, fail-soft pass inside analyze and critic workflows.
- **FR-007**: The system MUST skip coverage validation cleanly when a feature has no knowledge folder.
- **FR-008**: The system MUST add Genuine Fix Discipline guidance to the shared command preamble so fix and review workflows resolve behavioral intent before metric movement.
- **FR-009**: The system MUST require analyze and critic findings to carry an intent cue that states the behavior the finding is protecting or repairing.
- **FR-010**: The system MUST require site-audit findings to carry an Intent field.
- **FR-011**: The system MUST add a Genuine Fix Guard to verify so proof based only on a decreased metric with unchanged behavior fails.
- **FR-012**: The system MUST add a constitution-citation hook and matching constitution principle for Genuine Fix Discipline.
- **FR-013**: The system MUST include contract tests that validate the OKF schema/emission surface and the Genuine Fix Discipline command surface.

### Delivery Constraints

- Knowledge documents are a dual-write artifact and must not replace existing JSON, Markdown specs, plans, tasks, or gates.
- Coverage validation is advisory by default and must not block features that lack the new knowledge layer.
- Guidance must be shared from a common preamble contract and referenced by the relevant lifecycle commands.
- The solution must preserve cross-platform behavior for Bash and PowerShell users.

### Out of Scope

- Migrating existing JSON consumers to read OKF documents.
- Requiring old features to backfill knowledge documents before analyze, critic, or verify can run.
- Making knowledge coverage a hard blocking gate by default.
- Redesigning unrelated lifecycle command contracts or changing command routing.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Generating a new feature produces at least one valid OKF knowledge document in the feature's knowledge folder while existing JSON command output remains byte-for-byte unchanged.
- **SC-002**: Coverage validation reports counts for requirements, tasks, linked gate evidence, and uncovered items for a feature with knowledge documents.
- **SC-003**: Coverage validation exits successfully and reports a skip when the target feature has no knowledge folder.
- **SC-004**: Analyze and critic findings include intent cues in their required finding format.
- **SC-005**: Site-audit findings include an Intent field in their required finding format.
- **SC-006**: Verify rejects proof that only shows metric improvement while stating or demonstrating unchanged behavior.
- **SC-007**: Contract tests for OKF knowledge documents and Genuine Fix Discipline pass in the repository test suite.
