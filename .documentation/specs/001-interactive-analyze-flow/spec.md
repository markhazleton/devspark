---
classification: full-spec
risk_level: high
target_workflow: specify-full
required_artifacts: spec, plan, tasks
recommended_next_step: plan
required_gates: checklist, analyze, critic
---

<!-- markdownlint-disable MD036 -->

# Feature Specification: Interactive Review Remediation Consistency

**Feature Branch**: `001-interactive-analyze-flow`
**Created**: 2026-04-18
**Status**: Draft <!-- Valid: Draft | In Progress | Complete -->
**Input**: User description: "update the devspark.analyze process to be more interactive and to actually implmeent the proposed changes after confrimation, this needs to be mroe interactive with an option to just find and fix rather than only advise, this is needed to better automate (using harness engineering) the creation and validation of spec/plan/tasks in a single guided flow."

## Rationale Summary

### Core Problem

DevSpark review prompts are inconsistent across lifecycle stages. `clarify` asks targeted questions and applies changes, while `analyze` and `critic` remain report-only, and `pr-review` creates an advisory document without a built-in resolution loop. This creates different operator expectations at each stage and breaks end-to-end automation.

For harness-driven workflows, this inconsistency is more acute. A harness can sequence `/devspark.specify`, `/devspark.plan`, and `/devspark.tasks`, but review stages do not expose a consistent pattern for findings, action planning, confirmation, execution, and re-validation.

### Decision Summary

Establish a consistent review-remediation contract across the three stages: `spec -> clarify`, `spec/plan/tasks -> analyze and critic`, and `pr -> pr-review`. Analyze, critic, and pr-review must retain advisory-safe behavior but also provide actionable resolution plans and optional automation paths with explicit policy controls, matching the interactive quality already present in clarify.

### Key Drivers

- Users need a single guided flow that can create, validate, and tighten `spec.md`, `plan.md`, and `tasks.md` without manual re-entry between commands
- Harness engineering needs a predictable analysis step that can either stop at findings or continue through remediation
- The existing report-only behavior is safe, but it slows execution because users must manually translate recommendations into artifact edits
- Constitution-aware quality gates are more valuable when they can help users resolve fixable issues instead of only describing them
- Review and remediation behavior should be consistent across pre-implementation and PR review stages so teams can automate with one mental model

### Source Inputs

- User request to correct inconsistent review prompt behavior across clarify, analyze/critic, and pr-review
- Existing `templates/commands/analyze.md` behavior, which is explicitly non-destructive
- `.documentation/harness-engineering.md`, which defines the need for repeatable, guided, validation-driven workflows
- DevSpark Constitution v1.0.0, especially Backward Compatibility, Explicit Over Implied, and Ownership Boundary

### Tradeoffs Considered

- Option A: Keep `/devspark.analyze` strictly advisory and rely on users to edit artifacts manually after review
	Rejected because it preserves the current bottleneck and prevents a true guided validation loop

- Option B: Make all review commands fully automatic with no stage-specific safety controls
	Rejected because it weakens user control, risks over-editing user-authored artifacts, and conflicts with explicit governance

- Selected: Define a shared review-remediation contract for clarify, analyze, critic, and pr-review with stage-appropriate automation and explicit policy controls
	Chosen because it improves automation while keeping control, auditability, and constitutional guardrails intact across all review stages

### Architectural Impact

- Analyze, critic, and pr-review adopt a shared interaction contract: findings, actionable resolution plan, policy-controlled execution, and post-resolution validation output
- The analysis gate artifact remains authoritative, but it must now reflect both detected findings and the outcome of any remediation pass
- `spec.md`, `plan.md`, and `tasks.md` become eligible edit targets after a remediation proposal is presented and the user has a clear chance to opt out
- Harness workflows gain a viable path to perform artifact creation, validation, remediation, and final gate generation within one guided execution sequence
- Existing users who only want advisory analysis must still be able to run `/devspark.analyze` without triggering edits
- PR review workflows gain a first-class resolution plan output and an optional automation handoff instead of ending at advisory findings only

### Reviewer Guidance

Reviewers should focus on four points: (1) stage behavior is consistent across clarify, analyze/critic, and pr-review; (2) advisory-safe behavior remains available; (3) actionable resolution plans and automation paths are explicit; and (4) constitution conflicts remain blocking rather than being silently rewritten away.

## Clarifications

### Session 2026-04-18

- Q: How should remediation confirmation work for fixable findings? → A: Fully automatic remediation for fixable findings unless the user opts out.
- Q: How should drift be handled when artifacts change after initial analysis? → A: Auto re-run analysis once, regenerate proposal, then continue with opt-out controls.
- Q: What should opt-out behavior do next? → A: Enter selective approval mode for per-finding decisions.
- Q: How much remediation decision detail should be persisted in the gate artifact? → A: Persist per-finding decisions and outcomes with stable finding IDs.
- Q: How should non-interactive runs handle remediation policy? → A: Require explicit remediation policy input; fail clearly if missing.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review Findings Without Editing (Priority: P1)

A feature author runs `/devspark.analyze` after `/devspark.tasks` and wants a quality review before implementation, but does not want the command to modify any artifacts. They choose the report-only path, receive a severity-ranked report, and keep the current artifacts unchanged.

**Why this priority**: Safe advisory analysis is already part of the current workflow and must remain available for users who want review without automation.

**Independent Test**: Can be fully tested by running `/devspark.analyze` against a feature with known issues, choosing report-only mode, and confirming that `spec.md`, `plan.md`, and `tasks.md` remain unchanged while `gates/analyze.md` is refreshed.

**Acceptance Scenarios**:

1. **Given** `spec.md`, `plan.md`, and `tasks.md` exist for a feature, **When** the user runs `/devspark.analyze` and selects report-only mode, **Then** the command produces findings and updates only the analyze gate artifact
2. **Given** report-only mode is selected, **When** the command finishes, **Then** no edits are made to `spec.md`, `plan.md`, or `tasks.md`

---

### User Story 2 - Approve and Apply Repairs in the Same Session (Priority: P1)

A feature author runs `/devspark.analyze`, reviews the proposed fixes for missing coverage, terminology drift, underspecified tasks, and similar fixable issues, and allows the default remediation flow to proceed. The command updates the affected artifacts and re-runs analysis so the user ends the session with repaired documents and a current gate, while still being able to opt out before edits.

**Why this priority**: This is the new core value of the feature. Without in-session remediation, `/devspark.analyze` still cannot complete the validation loop.

**Independent Test**: Can be fully tested by preparing a feature whose artifacts contain fixable inconsistencies, running `/devspark.analyze`, allowing default remediation to proceed, and confirming that the resulting edits appear in `spec.md`, `plan.md`, and/or `tasks.md` and that a second analysis pass updates `gates/analyze.md`.

**Acceptance Scenarios**:

1. **Given** `/devspark.analyze` finds fixable issues, **When** the user chooses guided remediation, **Then** the command presents a concrete remediation proposal before any artifact is changed
2. **Given** a remediation proposal is shown, **When** the user does not opt out, **Then** the command applies the fixable remediation actions to the affected artifacts
3. **Given** remediation edits were applied, **When** remediation completes, **Then** the command re-runs analysis and records the post-remediation gate result
4. **Given** the user declines the remediation proposal, **When** the command completes, **Then** the original artifacts remain unchanged and the gate reflects the unresolved findings
5. **Given** the user opts out of default auto-remediation, **When** selective approval mode is entered, **Then** the command applies only the findings explicitly approved in that mode and preserves unapproved findings in the final report

---

### User Story 3 - Use Analyze Inside a Harness-Guided Flow (Priority: P2)

A workflow designer wants a harness sequence that can generate `spec.md`, `plan.md`, and `tasks.md`, validate their consistency, and either stop at findings or continue through a repair pass. `/devspark.analyze` provides a predictable decision point that can be incorporated into a guided harness execution instead of breaking the flow with manual out-of-band edits.

**Why this priority**: Harness engineering is the motivating operational use case. The feature is meant to help users automate creation and validation of the core artifacts in one guided sequence.

**Independent Test**: Can be fully tested by running a harness sequence that reaches `/devspark.analyze`, selecting a remediation path, and confirming that the sequence either exits with a report-only gate or continues with repairs and a refreshed gate.

**Acceptance Scenarios**:

1. **Given** a harness-guided workflow reaches the analysis step, **When** the workflow requests advisory analysis only, **Then** `/devspark.analyze` produces a gate artifact without changing the feature artifacts
2. **Given** a harness-guided workflow reaches the analysis step with remediation enabled, **When** remediation is not opted out, **Then** `/devspark.analyze` applies the fixable repairs and returns a final gate result for downstream steps

---

### User Story 4 - Preserve Safety on Non-Fixable or Sensitive Findings (Priority: P2)

A reviewer runs `/devspark.analyze` on a feature where some issues are not safe to repair automatically, such as constitution conflicts, missing business decisions, or ambiguous scope. The command distinguishes those from straightforward repair candidates and does not pretend it can safely auto-resolve them.

**Why this priority**: The new remediation capability must not blur the line between fixable editorial issues and decisions that still need human direction.

**Independent Test**: Can be fully tested by analyzing a feature with at least one constitution conflict or unresolved scope choice and confirming that the command leaves that item as a blocking finding instead of auto-applying a speculative repair.

**Acceptance Scenarios**:

1. **Given** `/devspark.analyze` detects a constitution conflict, **When** remediation is requested, **Then** the command reports the issue as blocking and does not silently rewrite the artifacts to bypass the conflict
2. **Given** `/devspark.analyze` detects an issue that requires a new product decision, **When** remediation is requested, **Then** the command leaves the issue in advisory or blocking status rather than inventing a requirement on the user's behalf

---

### User Story 5 - Keep Review Prompts Consistent Across Stages (Priority: P1)

A team uses all three review stages in one delivery cycle: clarify during spec refinement, analyze/critic after task generation, and pr-review before merge. They need each stage to produce findings and a concrete resolution path with consistent policy controls so operators and harness workflows do not switch behavior models between stages.

**Why this priority**: Inconsistent stage behavior is the root problem. Fixing only one stage leaves the broader automation and operator consistency gap unresolved.

**Independent Test**: Can be fully tested by executing clarify, analyze, critic, and pr-review on the same feature and verifying each stage emits a findings section, an actionable resolution plan, and a clearly declared execution mode/policy outcome.

**Acceptance Scenarios**:

1. **Given** clarify, analyze, critic, and pr-review are run for the same feature lifecycle, **When** each command finishes, **Then** each output includes findings, an actionable resolution plan, and explicit next actions
2. **Given** a stage is running in advisory-safe mode, **When** findings are produced, **Then** the command still emits a machine-usable action plan rather than only narrative advice
3. **Given** a stage supports automation, **When** the required policy input is present, **Then** execution proceeds under the same policy semantics used by the other automated review stages

---

### Edge Cases

- What happens when `/devspark.analyze` finds issues but none are safe to repair automatically?
- What happens when the user approves only a subset of the proposed remediation actions?
- What happens when artifacts change between analysis and remediation proposal application, including repeated drift after a single automatic re-baseline?
- What happens when `/devspark.analyze` runs in a non-interactive harness session without an explicit remediation policy input?
- What happens when a proposed repair would contradict frontmatter metadata or required section order in the shared validation contract?
- What happens when remediation resolves some issues but surfaces a new blocking issue during the re-analysis pass?
- What happens when one review stage emits findings but does not emit an actionable resolution plan in the shared format?

## Requirements *(mandatory)*

### Functional Requirements

**Analysis Modes**

- **FR-001**: `/devspark.analyze` MUST support an explicit report-only path that performs analysis, refreshes the analyze gate artifact, and does not edit `spec.md`, `plan.md`, or `tasks.md`
- **FR-002**: `/devspark.analyze` MUST support a guided remediation path that can continue from findings into an in-session repair flow with explicit opt-out control
- **FR-003**: The command MUST explain which path is being used before any remediation actions are proposed or applied

**Remediation Proposal**

- **FR-004**: When fixable issues are detected, the command MUST translate them into a concrete remediation proposal that identifies the affected artifact, the finding being addressed, and the intended outcome of the edit
- **FR-005**: The command MUST distinguish between fixable issues and issues that still require human judgment, such as constitution conflicts, scope decisions, or missing business intent
- **FR-006**: The remediation proposal MUST preserve severity so users can understand which proposed edits address blocking issues versus lower-priority cleanup
- **FR-007**: The command MUST allow the user to decline remediation and keep the session in advisory mode without losing the analysis report

**Confirmation and Edit Safety**

- **FR-008**: `/devspark.analyze` MUST default to applying fixable remediation actions after presenting the remediation proposal, unless the user explicitly opts out
- **FR-009**: The command MUST provide an explicit opt-out path before edits are applied, allowing users to keep report-only behavior or move to selective approval
- **FR-010**: If the user opts out and chooses selective approval mode, the command MUST allow per-finding approve or deny decisions before edits are applied
- **FR-011**: If the user opts out and chooses report-only behavior, the command MUST leave all feature artifacts unchanged
- **FR-012**: The command MUST detect when analyzed artifacts have materially changed before remediation is applied and MUST prevent stale edits from being applied
- **FR-013**: On first detected drift, the command MUST automatically re-run analysis once, regenerate the remediation proposal, and continue with the same opt-out controls
- **FR-014**: If drift is detected again after the single automatic re-baseline, the command MUST stop automated remediation, report the drift as blocking for this session, and require a fresh analysis invocation

**Artifact Repair**

- **FR-015**: Approved remediation actions MUST be able to update `spec.md`, `plan.md`, and `tasks.md` when those edits are necessary to resolve the targeted findings
- **FR-016**: Remediation edits MUST preserve required frontmatter, required section order, and valid lifecycle state in `spec.md`
- **FR-017**: Remediation edits MUST not remove user-authored requirements or tasks solely to make the artifacts appear cleaner unless the user explicitly approves that removal
- **FR-018**: When a finding maps to multiple artifacts, the command MUST coordinate the related edits so terminology, coverage, and sequencing remain consistent across the repaired set

**Re-Analysis and Gate Output**

- **FR-019**: After approved remediation edits are applied, `/devspark.analyze` MUST run a follow-up analysis pass before finalizing the session
- **FR-020**: The final `gates/analyze.md` artifact MUST reflect the latest state of the artifacts after remediation, not only the pre-edit findings
- **FR-021**: The final analysis report MUST clearly separate unresolved findings from issues that were repaired in the same session
- **FR-022**: The final `gates/analyze.md` artifact MUST persist per-finding remediation decisions and outcomes using stable finding IDs so sessions can be audited and compared across reruns

**Harness-Guided Flow Support**

- **FR-023**: `/devspark.analyze` MUST expose a predictable interaction pattern that can be used as a decision point inside a harness-guided spec-to-plan-to-tasks workflow
- **FR-024**: The command MUST support a path where harness-driven workflows can choose advisory analysis only and still receive a final gate artifact suitable for downstream review steps
- **FR-025**: The command MUST support a path where harness-driven workflows can continue through remediation and finish with a refreshed gate artifact suitable for downstream execution or review steps
- **FR-026**: In non-interactive execution contexts, the command MUST require an explicit remediation policy input; if absent, it MUST fail with a clear action-required message rather than assuming a default remediation behavior

**Governance and Compatibility**

- **FR-027**: Constitution conflicts detected during analysis MUST remain blocking findings and MUST NOT be auto-resolved by weakening or bypassing the governing principle
- **FR-028**: The command MUST continue to work for users who want the current analysis-only behavior, preserving backward-compatible access to a non-destructive review flow
- **FR-029**: The command MUST write all remediation-related reporting to repository-owned feature artifacts and MUST NOT add or modify framework-managed content under `.devspark/`

**Cross-Stage Consistency**

- **FR-030**: DevSpark review stages (`clarify`, `analyze`, `critic`, and `pr-review`) MUST follow a shared output contract containing findings, actionable resolution plan entries, and explicit next actions
- **FR-031**: `analyze` and `critic` MUST provide optional remediation execution paths in addition to advisory mode, with policy controls consistent with clarify-style interactive behavior
- **FR-032**: `pr-review` MUST include an actionable resolution plan artifact mapped to finding IDs and MUST provide an explicit automation handoff path for applying approved fixes
- **FR-033**: All review stages that support automation MUST enforce explicit policy input for non-interactive execution and fail clearly when policy is missing
- **FR-034**: Resolution plan entries across stages MUST be machine-usable and include stable finding ID, recommended action, target artifact, and execution eligibility (`manual`, `automated`, `blocked`)
- **FR-035**: Stage-specific differences are allowed only when documented as explicit constraints; undocumented divergence in review/remediation behavior across stages MUST be treated as a defect

### Key Entities *(feature involves data)*

- **Analysis Finding**: A normalized issue identified across `spec.md`, `plan.md`, and `tasks.md`, including category, severity, location, summary, and whether the issue is fixable or requires human judgment
- **Remediation Proposal**: A set of one or more candidate edits derived from analysis findings, each tied to a specific artifact and expected repair outcome, presented with explicit opt-out controls before application
- **Confirmation Decision**: The user's recorded choice for the current remediation session, including whether they selected report-only review, approved remediation, declined remediation, or approved only a subset of proposed actions
- **Remediation Session**: The full guided interaction that starts with findings, moves through proposal and opt-out decision, optionally applies repairs, then ends with a refreshed analysis result and gate artifact
- **Analyze Gate Report**: The persisted `gates/analyze.md` artifact containing final gate metadata, findings summary, per-finding remediation decisions and outcomes (keyed by stable finding IDs), repaired-items summary, unresolved issues, and next actions for the latest analysis session
- **Review Resolution Contract**: A shared stage output model that requires each review command to emit stable finding IDs, actionable resolution entries, execution mode metadata, and post-resolution status

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can run `/devspark.analyze`, choose either report-only or guided remediation, and reach a final gate result in a single session without manually restating the findings in another command
- **SC-002**: For a feature with fixable cross-artifact inconsistencies, a remediation pass reduces unresolved fixable findings to zero in at least 90% of test scenarios after one follow-up analysis pass
- **SC-003**: In report-only mode, `spec.md`, `plan.md`, and `tasks.md` remain unchanged in 100% of validation runs while `gates/analyze.md` is still refreshed
- **SC-004**: In guided remediation mode, users are shown a clear opt-out control before edits, and both report-only and selective-approval opt-out choices are honored in 100% of validation runs
- **SC-005**: When artifact drift is detected before remediation, the command auto re-baselines once and proceeds with a refreshed proposal in 100% of compliant runs; repeated drift is surfaced as blocking rather than applying stale edits
- **SC-006**: A harness-guided flow can create `spec.md`, `plan.md`, `tasks.md`, run `/devspark.analyze`, and finish with a usable final gate artifact without requiring manual out-of-band edits between the workflow steps
- **SC-007**: Constitution conflicts and unresolved scope decisions are preserved as blocking or advisory findings rather than being silently rewritten away in 100% of governance validation runs
- **SC-008**: In remediation-enabled sessions, 100% of findings recorded in `gates/analyze.md` include a stable finding ID and a terminal decision state (`applied`, `denied`, `deferred`, or `blocked`)
- **SC-009**: In non-interactive runs, sessions without explicit remediation policy input fail fast with a clear action-required message in 100% of validation runs
- **SC-010**: In lifecycle validation runs, 100% of clarify, analyze, critic, and pr-review outputs include the shared resolution contract fields (stable finding IDs, actionable resolution entries, and explicit next actions)
- **SC-011**: In automation-enabled stage runs, policy handling and terminal decision states are consistent across analyze, critic, and pr-review in 100% of conformance tests

## Assumptions

- The initial scope focuses on repairing artifact-quality issues that can be derived from the existing documents, not inventing new product intent
- Some findings will remain advisory because they require user judgment rather than deterministic repair
- Harness-driven flows can provide the required opt-out or policy signal at the guided decision point so automatic remediation behavior remains explicit
- The feature continues to operate on repository-owned work products under `.documentation/` and does not expand DevSpark ownership into `.devspark/`
