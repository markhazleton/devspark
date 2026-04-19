---
classification: full-spec
risk_level: high
target_workflow: specify-full
required_artifacts: spec, plan, tasks
recommended_next_step: plan
required_gates: checklist, analyze, critic
---

# Feature Specification: Harness Delivery Integrity

**Feature Branch**: `001-harness-delivery-integrity`
**Created**: 2026-04-19
**Status**: Draft
**Input**: User description: "review this retrospective on trying to use the cli to complete a spec to pr-review. see what lessons can be learned and if we need to update the code or documentation to make this an easier process."

## Rationale Summary

### Core Problem

The harness can report end-to-end workflow completion even when implementation work did not occur, creating a false sense of delivery readiness and making spec-to-pr-review automation unreliable.

### Decision Summary

DevSpark will add delivery-aware checks and clearer adapter/harness diagnostics so workflow completion reflects both orchestration execution and implementation evidence. The product will also improve documentation and default templates so teams can adopt strict, mutation-aware runs with less trial-and-error.

### Key Drivers

- Reduce false-positive "complete" runs that include no source implementation changes
- Improve trust in automated lifecycle execution from `specify` through `pr-review`
- Lower setup friction and troubleshooting time for harness adoption in real repositories

### Source Inputs

- Harness implementation retrospective dated 2026-04-19 for dependency hygiene feature execution
- Existing DevSpark constitution principles on explicitness, simplicity, and platform parity
- Existing harness artifacts and run records showing adapter gating and validation gaps

### Tradeoffs Considered

- Option A: Keep current behavior and rely on team discipline for manual verification (rejected: high risk of false positives)
- Option B: Enforce mutation requirements only in docs guidance (rejected: inconsistent adoption and weak enforcement)
- Selected: Add first-class delivery validation and readiness diagnostics in product behavior plus docs and template updates

### Architectural Impact

- Harness execution semantics expand from step orchestration success to dual workflow and delivery outcomes
- Adapter capability model becomes explicit for read-only, write-required, and unusable states
- Validation rule model adds mutation-aware checks to reduce shell-script workarounds

### Reviewer Guidance

Reviewers should focus on whether new runner behavior prevents "complete with no implementation" outcomes, whether adapter diagnostics are actionable, and whether docs/templates make strict operation the default path for write-heavy workflows.

## Clarifications

### Session 2026-04-19

- Q: What should count as implementation evidence? → A: Require at least one changed file in src/** or test/** for delivery status to pass implement-stage evidence.
- Q: How should create-pr readiness behave when delivery status is unmet? → A: Block create-pr readiness whenever delivery status is unmet.
- Q: What is the default stall timeout strategy for write-producing steps? → A: Trigger stall after 5 minutes with no output.
- Q: What should be the default manual gate policy for implement? → A: Use confirm-only as the default policy.
- Q: How should runner behavior handle a write-required step when the selected adapter is write-incompatible? → A: Hard fail before step execution with actionable remediation.
- Q: Should DevSpark support a true hands-off lifecycle option from plan through pr-review? → A: Yes, with no manual confirmations in the execution path and human intervention only at final PR accept/reject.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Detect Non-Delivery Runs (Priority: P1)

As a maintainer running a full lifecycle harness, I need the run result to indicate whether implementation actually occurred so I can trust readiness for create-pr and review stages.

**Why this priority**: This directly addresses the primary failure mode where completion status did not indicate real delivery progress.

**Independent Test**: Run a harness where steps execute but no source files are changed; verify workflow status can be complete while delivery status is not met and includes explicit failure reasons.

**Acceptance Scenarios**:

1. **Given** a completed run with passing command checks and no `src/**` or `test/**` file mutations, **When** result artifacts are produced, **Then** delivery status reports unmet implementation evidence and create-pr readiness is blocked.
2. **Given** a completed run with required source/test mutations and passing checks, **When** result artifacts are produced, **Then** delivery status is met and the run is marked create-pr ready.

---

### User Story 2 - Validate Adapter Doctor Readiness Early (Priority: P1)

As an engineer choosing an automation adapter, I need an adapter doctor diagnosis before a long run so I avoid stalls and unusable adapter modes.

**Why this priority**: Adapter mismatch and write approval gating caused major delays and ambiguity in the retrospective.

**Independent Test**: Execute adapter doctor for installed adapters and verify each adapter is classified with executable capability states and suggested actions.

**Acceptance Scenarios**:

1. **Given** an adapter that can execute read-only prompts but requires interactive write approval, **When** adapter doctor runs, **Then** it is marked as write-approval-required with mitigation guidance.
2. **Given** an adapter that is registered but not actually executable, **When** adapter doctor runs, **Then** it is marked unusable with concrete setup or fallback instructions.

---

### User Story 3 - Use Manual Gates with Evidence Policies (Priority: P2)

As an operator using manual steps, I need policy-based confirmations tied to evidence checks so keypress-only progression cannot hide missing deliverables.

**Why this priority**: Manual gate semantics currently allow procedural pass-through unless downstream checks happen to fail.

**Independent Test**: Run manual-gated implement step under each policy mode and verify continuation is blocked until required evidence conditions are satisfied.

**Acceptance Scenarios**:

1. **Given** manual implement gate with confirm-with-git-diff-check, **When** no qualifying source changes exist, **Then** gate continuation is denied with instructions to satisfy requirements.
2. **Given** manual implement gate with confirm-with-file-check and required artifacts present, **When** operator confirms, **Then** step passes with persisted evidence summary in run artifacts.

---

### User Story 4 - Adopt Strict Harness Defaults Quickly (Priority: P3)

As a new adopter, I need a strict implementation harness template and clearer docs so I can configure meaningful delivery validation without reverse engineering internals.

**Why this priority**: Better defaults and documentation reduce misconfiguration risk and improve onboarding speed.

**Independent Test**: Bootstrap using strict template and docs only, then verify a first run produces clear pass/fail outcomes for planning artifacts, source mutation, tests, build, and changelog evidence.

**Acceptance Scenarios**:

1. **Given** a new strict template-based harness, **When** implement produces no source changes, **Then** delivery status fails with a "why no changes" explainer.
2. **Given** a strict template run with required outputs and source deltas, **When** run completes, **Then** operator receives explicit create-pr readiness confirmation.

---

### User Story 5 - Run Full Lifecycle Hands-Off (Priority: P1)

As a maintainer, I need an optional true hands-off mode that runs plan through pr-review without manual confirmations so human effort is limited to accepting or rejecting the final PR outcome.

**Why this priority**: This is the desired operating model and removes the current gap between automated orchestration and practical delivery automation.

**Independent Test**: Execute a full lifecycle run in hands-off mode using a write-capable adapter and verify the system runs `plan -> tasks -> analyze -> critic -> implement -> create-pr -> pr-review` without manual prompts.

**Acceptance Scenarios**:

1. **Given** hands-off mode is enabled and adapter preflight passes write capability checks, **When** a lifecycle run starts, **Then** all configured stages execute sequentially without manual gate interaction.
2. **Given** hands-off mode is enabled and a stage fails a required gate, **When** execution reaches that stage, **Then** the run fails with machine-actionable diagnostics and does not silently downgrade to manual confirmation.
3. **Given** hands-off mode completes through review, **When** results are emitted, **Then** the system produces PR readiness and review findings for human accept/reject decision.

### Edge Cases

- How should delivery validation behave when only documentation files are changed but code tasks explicitly require `src/**` or `test/**` mutation?
- How should adapter diagnostics classify environments where adapter commands exist but prompt for deferred installation at runtime?
- How should stalled-step detection avoid false positives during legitimately long operations that still produce intermittent output?
- How should Windows decoding errors be represented in run artifacts without masking true step outcomes?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The harness result model MUST include both `workflow_status` and `delivery_status` as distinct fields with documented semantics, and `create_pr_ready` MUST be false whenever `delivery_status` is unmet.
- **FR-002**: The harness MUST support mutation-aware validation rules that can assert changed file count and path-pattern matches from git diff state, with a default delivery evidence rule requiring at least one changed file in `src/**` or `test/**`.
- **FR-003**: The harness MUST provide a built-in post-run explainer when workflow status is complete but delivery status is unmet, including which checks passed and which delivery requirements failed.
- **FR-004**: The harness MUST support manual gate policy modes: `confirm-only`, `confirm-with-file-check`, and `confirm-with-git-diff-check` for interactive workflows, with interactive default set to `confirm-only`, while hands-off mode MUST execute without manual confirmation gates.
- **FR-005**: Manual gate policies for write-producing steps MUST prevent continuation when configured evidence checks fail.
- **FR-006**: DevSpark MUST provide an adapter doctor command that evaluates executable availability and capability classes before run execution.
- **FR-007**: Adapter doctor MUST classify each adapter into explicit states: `available`, `read-only-works`, `write-approval-required`, or `unusable`.
- **FR-008**: Step execution MUST support timeout and stall detection with structured events and actionable guidance, with a default write-step stall threshold of 5 minutes of output inactivity.
- **FR-009**: Step metadata MUST allow declaring write-permission requirements so incompatible adapters are rejected before execution.
- **FR-013**: If a step declares write-permission requirements and the selected adapter is write-incompatible, the runner MUST fail before executing the step and emit actionable remediation guidance.
- **FR-014**: DevSpark MUST provide a true hands-off lifecycle option that executes `plan -> tasks -> analyze -> critic -> implement -> create-pr -> pr-review` in one run when prerequisites are satisfied.
- **FR-015**: In hands-off mode, analyze and critic stages MUST apply configured auto-remediation rules and re-validate outcomes before advancing.
- **FR-016**: In hands-off mode, create-pr and pr-review MUST be gated by delivery-status success and branch sync checks; if unmet, the run MUST fail with explicit reason codes.
- **FR-017**: Hands-off mode MUST produce a final decision packet summarizing implementation evidence, review findings, and merge recommendation for human PR accept/reject action.
- **FR-018**: In hands-off mode, analyze and critic MUST run iterative remediation loops with a default maximum of 3 remediation passes per stage.
- **FR-019**: After each remediation pass, the stage MUST re-run its checks and evaluate finding states using canonical statuses: `open`, `resolved`, and `deferred`.
- **FR-020**: A stage MUST advance only when no `open` findings remain at or above the configured severity threshold for that stage.
- **FR-021**: If a remediation pass introduces new findings, those findings MUST be incorporated into the same stage loop and evaluated against the same threshold before advancing.
- **FR-022**: If the maximum pass count is reached and blocking findings remain, the run MUST fail with a structured convergence report that includes unresolved findings, attempted remediations, and recommended manual actions.
- **FR-023**: Each pass in analyze and critic MUST persist an iteration record in run artifacts including pass index, finding deltas, remediation actions attempted, and re-validation outcome.
- **FR-024**: For cross-cutting changes, implementation MUST be gated by an explicit leadership approval checkpoint before `/devspark.implement` execution begins.
- **FR-010**: DevSpark MUST provide a strict implementation harness template with default checks for planning artifacts, source/test mutation, tests/build, and changelog update evidence.
- **FR-011**: DevSpark documentation MUST include a troubleshooting path for adapter readiness, stalled steps, manual gates, and interpreting workflow vs delivery outcomes.
- **FR-012**: Harness output capture MUST handle non-UTF terminal bytes fail-softly and record decode incidents as non-fatal step events.

### Key Entities *(include if feature involves data)*

- **Run Outcome**: Canonical run summary containing workflow status, delivery status, and create-pr readiness indicators.
- **Delivery Check Result**: Structured evaluation record for each delivery requirement (source mutation, artifact presence, test/build checks), including pass/fail and evidence.
- **Adapter Capability Profile**: Diagnostic profile for an adapter including executable health, read capability, write capability, and remediation guidance.
- **Manual Gate Policy**: Configurable gate behavior defining required evidence checks before operator confirmation can advance a step.
- **Stall Event**: Structured event emitted when a step is considered stalled, including threshold, last output timestamp, and suggested next actions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of runs that produce no required source/test mutations are reported as delivery unmet, even when orchestration steps complete.
- **SC-002**: At least 90% of adapter setup failures are identified by pre-run diagnostics before full lifecycle execution begins.
- **SC-003**: Median time to diagnose stalled harness execution is reduced by at least 50% compared with baseline retrospective sessions.
- **SC-004**: At least 80% of first-time strict template adopters complete a valid end-to-end run without manual schema troubleshooting.
- **SC-005**: 100% of completed runs emit an explicit create-pr readiness statement derived from delivery requirements.
- **SC-006**: In hands-off mode, at least 95% of successful runs complete from plan through pr-review without human intervention prior to final PR decision.
- **SC-007**: In hands-off mode, 100% of analyze and critic stage outcomes include explicit convergence status (`converged` or `max-pass-failed`) with iteration evidence in run artifacts.
- **SC-008**: At least 90% of blocking findings detected in analyze or critic are automatically resolved within the configured maximum pass count in eligible repositories.

## Assumptions

- Teams can specify which path patterns count as implementation evidence for their repository context.
- Existing repositories may choose progressive adoption, but strict delivery checks are available without custom scripting.
- Documentation changes can ship alongside code changes to keep operator guidance synchronized with runtime behavior.
