---
classification: full-spec
risk_level: high
target_workflow: specify-full
required_artifacts: spec, plan, tasks
recommended_next_step: plan
required_gates: checklist, analyze, critic
---

<!-- markdownlint-disable MD036 -->

# Feature Specification: Tiered Prompt and Workflow Engine

**Feature Branch**: `001-interactive-analyze-flow`
**Created**: 2026-04-18
**Status**: Complete — Merged
**Merged**: PR [#28](https://github.com/markhazleton/devspark/pull/28) on 2026-04-18
**Input**: User description: "Expand DevSpark from a prompt library into an orchestrated, self-improving workflow system with tiered prompt architecture, workflow definitions, aliases, autonomy controls, observability, CLI UX simplification, prompt metadata, and contribution loops."

## Rationale Summary

### Core Problem

DevSpark currently behaves mostly as a prompt library with partial orchestration patterns layered on top. Users can run individual commands effectively, but the repository does not yet provide a first-class, standardized workflow model that separates atomic capability, orchestrated flow, human-friendly entrypoints, and governance controls.

This gap creates operational friction at scale: contributors must manually stitch prompt sequences, consistency varies across lifecycle stages, autonomy boundaries are implicit, and observability signals are not standardized for workflow-level analysis.

### Decision Summary

Re-architect DevSpark into a tiered system with explicit atomic prompts, workflow definitions, alias entrypoints, autonomy policy, and step-level observability. Keep existing prompt behavior backward-compatible while introducing composable workflow artifacts (`create-spec`, `execute-plan`, `suggest-improvement`) and a shared execution contract that supports both assisted and autonomous modes.

### Key Drivers

- Separate concerns between atomic prompt capability and orchestrated workflow composition
- Make common workflows easier to discover and execute than advanced low-level prompt entrypoints
- Enable improvement-loop workflows that convert repo feedback into structured issues and optional implementation triggers
- Introduce explicit autonomy levels and guardrails so governance is configurable and auditable
- Emit structured step telemetry to support reliability analysis, Kusto-style querying, and staged autonomy expansion
- Preserve existing slash-command compatibility while introducing a cleaner future architecture

### Source Inputs

- User proposal for tiered prompt architecture (`prompts/atomic`, `workflows`, `aliases`)
- User proposal for first-class orchestrated workflows (`create-spec`, `execute-plan`, `suggest-improvement`)
- User proposal for autonomy policy, observability events, and adoption-focused CLI/UX improvements
- Existing DevSpark command templates and harness direction in `.documentation/harness-engineering.md`
- DevSpark Constitution v1.1.0, especially Backward Compatibility, Explicit Over Implied, Ownership Boundary, and Platform Parity

### Tradeoffs Considered

- Option A: Keep DevSpark as a prompt-first command collection and document suggested command sequences
  Rejected because sequence reliability, observability, and autonomy policy remain implicit and inconsistent

- Option B: Move immediately to fully autonomous workflows with hard default execution
  Rejected because governance maturity and operator trust require staged autonomy with explicit review gates

- Selected: Introduce tiered architecture with assisted defaults, explicit workflow pauses, and optional autonomy expansion
  Chosen because it provides structural clarity and governance while preserving existing command compatibility

### Architectural Impact

- Add first-class repo structure for atomic prompts, workflow definitions, and alias entrypoints
- Introduce workflow schema fields for autonomy, pause gates, conditional branching, and output typing
- Define step-level telemetry contract for all workflow executions
- Add prompt metadata for audience exposure, categorization, and discoverability
- Add contribution artifacts for prompt improvement feedback loops
- Preserve existing command compatibility through alias and migration mapping rather than destructive replacement

### Reviewer Guidance

Reviewers should focus on five points: (1) tier boundaries are clear and enforced; (2) workflow definitions are reusable and non-duplicative; (3) autonomy behavior is explicit and auditable; (4) observability payloads are consistent and useful; and (5) backward-compatible prompt paths remain intact.

## Clarifications

### Session 2026-04-18

- Q: How should remediation confirmation work for fixable findings? → A: Fully automatic remediation for fixable findings unless the user opts out.
- Q: How should drift be handled when artifacts change after initial analysis? → A: Auto re-run analysis once, regenerate proposal, then continue with opt-out controls.
- Q: What should opt-out behavior do next? → A: Enter selective approval mode for per-finding decisions.
- Q: How much remediation decision detail should be persisted in the gate artifact? → A: Persist per-finding decisions and outcomes with stable finding IDs.
- Q: How should non-interactive runs handle remediation policy? → A: Require explicit remediation policy input; fail clearly if missing.
- Q: Should DevSpark adopt a tiered prompt/workflow/alias architecture as the primary model? → A: Yes, with backward-compatible atomic access retained.
- Q: Should orchestrated workflows become first-class repository artifacts? → A: Yes, define workflows as versioned YAML assets.
- Q: Should improvement suggestions support optional auto-assignment and implementation trigger paths? → A: Yes, behind explicit conditional workflow logic.
- Q: Should autonomy be explicit per workflow with assisted default? → A: Yes, assisted by default with configurable guardrails.
- Q: Should workflow telemetry be emitted at each step for analysis and governance? → A: Yes, emit structured events for every step outcome.
- Q: Where should the new tiered artifacts physically live? → A: Under `templates/` (`templates/prompts/atomic/`, `templates/workflows/`, `templates/aliases/`); resolver extends the existing 3-tier override chain (personal → team → stock).
- Q: What on-disk format should atomic prompts use? → A: `.md` files with YAML frontmatter, matching the existing `templates/commands/*.md` shape; metadata fields added to frontmatter.
- Q: Where should workflow telemetry events be written? → A: JSON Lines, append-only, to `.documentation/telemetry/workflow-events.jsonl` (path overridable via env var); local-first, no external service required.
- Q: Which layer enforces autonomy guardrails? → A: The workflow runner enforces, performing pre-step policy checks and post-step diff inspection; atomic prompts remain enforcement-free.
- Q: Where should `suggest-improvement` create issues? → A: Always create GitHub issues in `github.com/markhazleton/devspark` (the canonical DevSpark home) via `gh` CLI, regardless of the calling repo; no per-repo or platform-adapter configuration in this feature.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create Spec via Tiered Workflow (Priority: P1)

A developer runs a single high-level entrypoint (`create-spec`) and receives a complete, reviewable artifact chain (`spec`, `plan`, `tasks`, `analyze`) without manually invoking each atomic prompt.

**Why this priority**: This is the primary onboarding and adoption path for most users.

**Independent Test**: Can be fully tested by executing `create-spec` and verifying all expected step outputs are produced and pause behavior occurs after `analyze`.

**Acceptance Scenarios**:

1. **Given** the workflow definition `create-spec.yaml` exists, **When** the user executes `create-spec`, **Then** steps run in the declared order: `specify`, `plan`, `generate-tasks`, `analyze`
2. **Given** `create-spec` reaches the configured pause point, **When** execution stops after `analyze`, **Then** the output is a reviewable artifact package rather than immediate implementation execution

---

### User Story 2 - Execute Plan Workflow with Governance Pauses (Priority: P1)

A developer runs `execute-plan` to orchestrate `implement`, `create-pr`, and `review-pr` while preserving mandatory review pauses and governance checks.

**Why this priority**: This provides the production path from approved plan to PR while keeping control gates explicit.

**Independent Test**: Can be fully tested by executing `execute-plan` and verifying pause occurs after `create-pr` with correct pull-request-oriented output.

**Acceptance Scenarios**:

1. **Given** `execute-plan.yaml` defines workflow steps and pause policy, **When** execution reaches `create-pr`, **Then** the workflow pauses for human review if configured
2. **Given** autonomy mode is `assisted`, **When** review gates are unmet, **Then** the workflow does not continue to unrestricted autonomous progression

---

### User Story 3 - Submit Improvement Suggestions as Workflow (Priority: P1)

A contributor uses `suggest-improvement` to capture context, classify improvement type, create an issue, and optionally trigger assignment and implementation steps.

**Why this priority**: This establishes the self-improving feedback loop that turns ideas into actionable work.

**Independent Test**: Can be fully tested by running `suggest-improvement` with and without `assign_agent` enabled and verifying conditional behavior.

**Acceptance Scenarios**:

1. **Given** `suggest-improvement.yaml` declares core steps, **When** the workflow runs, **Then** it emits an issue-link output after context capture, classification, and issue creation
2. **Given** `assign_agent` is true, **When** conditional branching is evaluated, **Then** `assign-agent` and `trigger-implementation` steps run in order

---

### User Story 4 - Discover Workflows Through Aliases and Metadata (Priority: P2)

A new user runs `devspark help` and sees `create-spec`, `execute-plan`, and `suggest-improvement` as primary entrypoints, while advanced users can still access atomic prompts directly.

**Why this priority**: Adoption depends on clear, ergonomic entrypoints and discoverability metadata.

**Independent Test**: Can be fully tested by checking help output and metadata filtering behavior for exposed prompts.

**Acceptance Scenarios**:

1. **Given** alias definitions exist, **When** users invoke aliases, **Then** alias resolution maps to canonical workflow definitions without duplicating atomic logic
2. **Given** prompt metadata contains audience and exposure flags, **When** help output is rendered, **Then** prompts are filtered and grouped by intended audience and category

---

### User Story 5 - Govern Automation with Autonomy and Observability (Priority: P1)

A team configures workflow autonomy to `assisted`, requires reviews after sensitive steps, and consumes step telemetry to evaluate reliability before expanding autonomy.

**Why this priority**: Governance and observability are required to scale automation safely in production environments.

**Implementation Sequencing Note**: Although US5 is listed last in this section, `tasks.md` schedules it before US2 because the `execute-plan` workflow (US2) depends on the autonomy enforcement and telemetry infrastructure introduced by US5.

**Independent Test**: Can be fully tested by running workflows with autonomy settings and verifying pause behavior plus structured step events.

**Acceptance Scenarios**:

1. **Given** autonomy level is `assisted`, **When** a configured review checkpoint is reached, **Then** workflow execution pauses and records the pause reason
2. **Given** a workflow step completes, **When** telemetry is emitted, **Then** it includes workflow id, step id, status, duration, and success flag in structured format
3. **Given** future autonomous mode is enabled, **When** guardrail limits are exceeded, **Then** execution is blocked or downgraded according to policy

---

### Edge Cases

- What happens when an alias points to a missing or invalid workflow definition?
- What happens when a workflow references an atomic prompt that does not exist or is not exposed?
- What happens when conditional steps depend on missing context keys?
- What happens when autonomy policy is not defined for a non-interactive run?
- What happens when telemetry emission fails mid-workflow?
- What happens when backward-compatible legacy commands and new aliases are both invoked in the same session?

## Requirements *(mandatory)*

### Functional Requirements

**Tiered Architecture and Repository Structure**

- **FR-001**: The repository MUST define a tiered prompt structure with first-class artifact locations under `templates/prompts/atomic/`, `templates/workflows/`, and `templates/aliases/`, resolved through the existing 3-tier override chain (personal → team → stock defaults) so they remain DevSpark-owned and Ownership-Boundary compliant
- **FR-002**: Atomic prompt definitions MUST be authored as Markdown files with YAML frontmatter (`.md`) matching the existing `templates/commands/*.md` shape, MUST be reusable, and MUST be independent from specific workflow sequencing logic
- **FR-003**: Workflow definitions MUST reference atomic prompt capabilities rather than duplicating prompt logic inline
- **FR-004**: Alias entrypoints MUST map to canonical workflows and MUST NOT create divergent behavior from direct workflow invocation

**Core Workflow Definitions**

- **FR-005**: DevSpark MUST define `create-spec` as a workflow that orchestrates `specify`, `plan`, `generate-tasks`, and `analyze`
- **FR-006**: DevSpark MUST define `execute-plan` as a workflow that orchestrates `implement`, `create-pr`, and `review-pr`
- **FR-007**: Workflow definitions MUST support explicit pause points (for example after `analyze` or `create-pr`) that can require review before continuation
- **FR-007a**: Paused workflow runs MUST persist resumable state to disk (default `.documentation/telemetry/runs/<workflow_run_id>.json`, env-overridable via `DEVSPARK_RUNS_PATH`) capturing `schema_version` (=1), `workflow_id`, `workflow_run_id`, `last_completed_step_id`, `next_step_id`, full `context` snapshot, `autonomy_level`, ISO 8601 `paused_at` timestamp, and a SHA-256 `context_checksum` over the serialized context. Writes MUST be atomic: write to `<file>.tmp`, fsync, then `os.replace` to the final path. A partially written `.tmp` MUST never be loaded by resume.
- **FR-007b**: DevSpark MUST provide a `devspark resume <workflow_run_id>` entrypoint that loads the persisted state, validates `schema_version`, recomputes and verifies `context_checksum`, validates the source workflow definition still resolves AND that the persisted `workflow_id` matches the resolved workflow id, then continues execution from `next_step_id`. Resumed runs MUST reuse the original `workflow_run_id` for telemetry continuity. On any validation failure the runner MUST exit with `EXIT_RESUME_FAILED` and a message naming the failing check.
- **FR-007c**: When the runner pauses (whether via `pause_after`, `review_after`, or guardrail downgrade) it MUST print `Paused. Resume with: devspark resume <workflow_run_id>` to stderr and emit a `paused` telemetry event with the `workflow_run_id` populated.
- **FR-008**: Workflow definitions MUST declare output type semantics (for example `reviewable-artifact`, `pull-request`, `issue-link`)

**Suggest-Improvement Workflow**

- **FR-009**: DevSpark MUST define `suggest-improvement` as a first-class workflow artifact
- **FR-010**: `suggest-improvement` MUST include core steps for context capture, improvement classification, and issue creation; the issue creation step MUST always target the canonical DevSpark repository at `github.com/markhazleton/devspark` via the `gh` CLI, regardless of the repository the workflow is invoked from. The adapter MUST guarantee canonical-repo targeting against prompt-injection of competing flags by using `gh api repos/markhazleton/devspark/issues` with a JSON payload (no flag-parsing surface for user/model-generated text). Before invoking `gh`, the adapter MUST display the resolved repo, title, and labels and require interactive confirmation; `--yes` skips confirmation in non-interactive runs.
- **FR-011**: `suggest-improvement` MUST support conditional execution for agent assignment and implementation triggering when explicitly enabled
- **FR-012**: DevSpark MUST provide atomic prompt definitions for `capture-context`, `classify-improvement`, `create-issue`, and `assign-agent`

**Autonomy Governance**

- **FR-013**: Workflow schema MUST support an explicit `autonomy` block with at least `assisted` and `autonomous` levels
- **FR-014**: Assisted mode MUST support configured review checkpoints after specified steps
- **FR-015**: Autonomous mode MUST support explicit guardrails including file-change thresholds and restricted path policies. Because atomic prompts in this repository edit the working tree directly, the workflow runner MUST establish a per-step boundary using a git stash/restore pattern: before each step the runner records the working-tree HEAD + index state; after the step it diffs against the recorded baseline; if the diff violates `max_files_changed`, `restricted_paths`, or `max_total_lines_changed` the runner MUST `git stash` (or hard-reset for untracked-only changes) the offending changes, emit a `guardrail_triggered` telemetry event with the violated `guardrail_rule`, and either downgrade to assisted-mode pause (default) or abort with `EXIT_GUARDRAIL_BLOCKED` if downgrade is disabled. Atomic prompts MUST NOT be responsible for enforcement.
- **FR-015a**: Workflow runs MUST refuse to start when the working tree has uncommitted changes that the runner cannot safely distinguish from step output, unless `--allow-dirty` is supplied. The intent is to keep the per-step diff baseline well-defined.
- **FR-016**: Non-interactive executions that require autonomy policy MUST fail with a clear action-required message when policy input is missing. Autonomy policy input MUST be accepted from any of the following channels (highest precedence first): (1) CLI flag `--autonomy assisted|autonomous`; (2) environment variable `DEVSPARK_AUTONOMY`; (3) optional repo-local file `.devspark/autonomy.yaml` with key `default_level`. If none provide a value AND the run is non-interactive AND the workflow lacks an explicit `autonomy.level`, the runner MUST exit non-zero with a message naming all three channels.

**Observability and Telemetry**

- **FR-017**: Each workflow step execution MUST emit a structured telemetry event (workflow id, step id, status, duration, success indicator) appended as a single JSON Lines record to `.documentation/telemetry/workflow-events.jsonl` by default; the destination path MUST be overridable via environment variable
- **FR-018**: Workflow telemetry format MUST be consistent JSON Lines across all workflows so logs can be aggregated and queried reliably with standard tooling (`jq`, Kusto-style ingestion). The writer MUST acquire an OS-level exclusive file lock (`fcntl.flock` on POSIX, `msvcrt.locking` on Windows) around each single-event append so that concurrent `devspark run` invocations sharing the same destination produce a fully parseable JSONL file. Each serialized event MUST be ≤ 4 KB; the optional `context` blob MUST be ≤ 1 KB.
- **FR-019**: Failed step events MUST include sufficient context to identify failing step and workflow path without parsing raw prompt text. Concretely, the telemetry `error` field MUST be ≤ 500 characters and a populated `error_class` field (string, e.g., `WF_PROMPT_UNKNOWN`, `EXIT_GH_UNAVAILABLE`) MUST accompany every `phase=failed` event for machine grouping.

**CLI and UX Layer**

- **FR-020**: CLI help output MUST prioritize high-level workflow aliases (`create-spec`, `execute-plan`, `suggest-improvement`) for onboarding
- **FR-021**: CLI help output MUST still expose advanced atomic operations for expert users
- **FR-022**: DevSpark SHOULD recommend workflow aliases when repeated atomic command sequences are detected. The recognition heuristic MUST trigger when a user invokes 3 or more consecutive atomic prompts within a 30-minute window that match the first 3 ordered steps of a known workflow definition. The recommendation is advisory only and MUST NOT alter execution.

**Prompt Metadata and Discoverability**

- **FR-023**: Atomic prompt definitions MUST support metadata fields for `name`, `audience`, `exposed`, and `category` declared in YAML frontmatter of the prompt `.md` file
- **FR-024**: Metadata MUST support filtering and grouping of prompts in CLI or UI discovery surfaces
- **FR-025**: Prompts not marked exposed MUST remain available for internal orchestration but hidden from default beginner-oriented listings

**Review and Remediation Consistency**

- **FR-026**: Review stages (`clarify`, `analyze`, `critic`, `pr-review`, and `address-pr-review`) MUST follow a shared resolution contract containing findings, actionable next actions, and explicit execution status
- **FR-027**: Stage outputs MUST include stable finding identifiers and machine-usable action entries where applicable
- **FR-028**: Existing PR-stage commit-isolation behavior introduced by `address-pr-review` MUST remain intact under the new workflow model

**Contribution and Improvement Loop**

- **FR-029**: Repository MUST include a standardized issue template for prompt/workflow improvement submissions
- **FR-030**: Improvement submissions MUST capture context, current behavior, expected behavior, and optional suggested fix fields
- **FR-031**: Improvement loop artifacts MUST integrate with the `suggest-improvement` workflow outputs

**Documentation and Adoption**

- **FR-032**: Documentation MUST include sections for Getting Started workflows, Advanced atomic usage, Workflow Architecture, Autonomy Model, and Improvement Loop
- **FR-033**: Documentation MUST explain relationship between aliases, workflows, and atomic prompts with migration-safe examples

**Backward Compatibility and Migration**

- **FR-034**: Existing slash-command entrypoints MUST continue to work during migration to tiered architecture
- **FR-035**: Migration MUST preserve constitutional constraints, including Ownership Boundary and Platform Parity
- **FR-036**: Stage-specific behavior differences MUST be documented explicitly; undocumented divergence from shared workflow semantics MUST be treated as a defect

### Key Entities *(feature involves data)*

- **Atomic Prompt**: A single-purpose prompt definition that performs one bounded capability and can be reused across multiple workflows
- **Workflow Definition**: A declarative orchestration artifact that defines ordered steps, pauses, conditions, autonomy behavior, and output semantics
- **Alias Entrypoint**: A user-facing command mapping that resolves to a canonical workflow without changing underlying workflow semantics
- **Autonomy Policy**: A workflow configuration describing execution level, review requirements, and guardrails for automated progression
- **Workflow Event**: A structured telemetry record emitted for each step execution with workflow, step, status, duration, and success data
- **Improvement Proposal**: A captured suggestion artifact containing context, classification, and linked issue output, optionally extended with assignment/execution triggers
- **Review Resolution Contract**: A shared stage output model that requires review commands to emit stable finding IDs, actionable resolution entries, execution mode metadata, and post-resolution status

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete spec generation through a single `create-spec` workflow entrypoint with correct ordered outputs in at least 95% of validation runs
- **SC-002**: Users can execute implementation-to-review flow through a single `execute-plan` workflow with configured pause after `create-pr` in 100% of policy-compliant runs
- **SC-003**: `suggest-improvement` generates a linked issue artifact and optional conditional assignment path in at least 95% of test runs
- **SC-004**: CLI help surfaces high-level aliases for onboarding while preserving access to advanced atomic prompts in 100% of UX conformance checks
- **SC-005**: All workflow steps emit structured telemetry events conforming to the shared event schema in 100% of execution tests
- **SC-006**: Non-interactive workflow runs without required autonomy policy input fail fast with explicit action-required messaging in 100% of governance tests
- **SC-007**: Shared review resolution contract fields are present across clarify, analyze, critic, pr-review, and address-pr-review outputs in 100% of lifecycle conformance runs
- **SC-008**: Backward-compatible command entrypoints continue to function during migration in 100% of regression tests for supported legacy flows
- **SC-009**: Prompt/workflow improvement submissions use the standardized issue template structure in 100% of sampled improvement tickets
- **SC-010**: Documentation includes required architecture, autonomy, workflow, and improvement-loop sections before feature status can advance from Draft

## Assumptions

- Workflow artifacts are represented as version-controlled YAML definitions and validated by repository tooling
- Existing command templates remain available during transition to prevent disruptive migration for current contributors
- Telemetry emission can be implemented in a way that supports current logging pipelines without requiring immediate external service integration
- The feature continues to operate on repository-owned work products under `.documentation/` and does not expand DevSpark ownership into `.devspark/`
- **Runtime vs install/upgrade ownership of `.documentation/`**: Constitution §III prohibits install and upgrade flows from writing under any `.documentation/` directory. Runtime workflow execution is a separate concern and MAY create or append repo-owned work product (telemetry events, run state, gate artifacts) under `.documentation/`. The boundary is enforced by `tests/test_upgrade_migration_safety.py` (install/upgrade) and is left unconstrained for runtime.
