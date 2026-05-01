# Implementation Plan: Harness Delivery Integrity

**Branch**: `001-harness-delivery-integrity` | **Date**: 2026-04-19 | **Spec**: `.documentation/specs/001-harness-delivery-integrity/spec.md`
**Input**: Feature specification from `.documentation/specs/001-harness-delivery-integrity/spec.md`

## Rationale Summary

### Core Problem

Harness runs can complete orchestration without proving implementation delivery, and adapter/runtime behavior can silently undermine fully unattended execution.

### Decision Summary

Introduce delivery-aware run semantics, adapter doctor capability diagnostics, and an optional true hands-off lifecycle mode with iterative analyze/critic convergence rules. Keep interactive/manual policies available, but separate them from unattended execution behavior.

### Key Drivers

- Eliminate false-positive completion for implementation stages
- Make hands-off execution deterministic and auditable
- Reduce adoption friction via strict defaults, clear diagnostics, and better templates/docs

### Source Inputs

- `.documentation/specs/001-harness-delivery-integrity/spec.md`
- `.documentation/memory/constitution.md`
- Harness retrospective findings provided in specification input and clarifications

### Tradeoffs Considered

- Option A: Documentation-only fixes (rejected: weak enforcement)
- Option B: Manual-only confirmations for safety (rejected for hands-off mode)
- Selected: Explicit mode separation and hard gates for unattended flow

### Architectural Impact

- New run outcome model and convergence artifacts
- New and extended harness validation rules and adapter doctor diagnostics
- CLI workflow additions for single-run hands-off lifecycle with fail-fast gating

### Reviewer Guidance

Prioritize verification of hard gate semantics, convergence loop correctness, adapter capability enforcement, and parity across PowerShell/Bash plus template/docs updates.

## Delivery Strategy & Scope Separation

**Two-PR Approach for Risk Mitigation (CR-3 Resolution)**:

### PR1: Delivery Integrity MVP (Phases 1-3, Tasks T001-T018)

**Scope**: Core delivery-status gating and validation evidence model.
**User Stories Delivered**: US1 (Detect Non-Delivery Runs) only.
**Key Features**:

- Dual outcome model (workflow_status, delivery_status)
- Default delivery evidence rule (src/test mutation)
- create-pr-ready readiness blocking
- No-change explainer artifacts
- Governance approval checkpoint enforcement
**Testing**: Includes new contract tests (test_delivery_status_contract.py)
**Value**: Independently deployable, addresses primary false-positive failure mode

### PR2: Advanced Features & Parity (Phases 4-8, Tasks T019-T047)

**Scope**: Adapter doctor, hands-off orchestration, manual gates, templates, parity
**User Stories Delivered**: US2, US3, US4, US5 (Adapter Doctor, Manual Gates, Strict Defaults, Hands-Off Lifecycle)
**Key Features**:

- Adapter doctor probes and capability profiles
- Hands-off lifecycle orchestration (plan → pr-review)
- Manual gate policies with evidence
- Strict harness template
- Bash/PowerShell parity verification
- Full convergence loop (re-validation only in MVP, auto-remediation deferred)
**Testing**: Includes full contract and integration tests
**Value**: Completes vision of unattended end-to-end execution

**Sequencing**: PR1 must merge before PR2 begins. PR1 can be released independently.

## Risk Mitigations Applied (2026-04-29)

### CR-1: Auto-Remediation MVP Scope

**Resolution**: Convergence loop in Phase 1 is **re-validation-only**. After each pass, findings are re-evaluated. Automatic fix generation is deferred to post-MVP (outside this feature). This eliminates the need for an unplanned LLM integration while still proving iterative convergence behavior.

### CR-2: Stall Detection MVP Scope

**Resolution**: Stall detection deferred. MVP implements only total-step-timeout via subprocess.run timeout parameter. 5-minute output-inactivity detection requires async subprocess refactor, deferred to post-MVP infrastructure improvement.

### CR-3: Scope Creep Mitigation

**Resolution**: Split into 2 PRs. PR1 (Phases 1-3) is MVP-complete and independently valuable. PR2 (Phases 4-8) builds on PR1. Reduces per-PR complexity and risk.

### HP-2: Git Diff Reference Strategy

**Resolution**: Use `git diff origin/main...HEAD -- src/ test/` for branch-aware diff. Document in DeliveryCheckResult model and validation contracts.

### HP-3: Adapter Probe Protocol

**Resolution**: Add explicit `probe()` method to AgentAdapter protocol. Each adapter implements own probe logic returning ProbeResult with capability flags. No destructive testing needed.

### HP-4: Non-UTF Decode Handling

**Resolution**: Add `errors="replace"` to all subprocess text decoding in validation.py and adapter base. Emit telemetry event on replacement. Update artifacts to show decode incidents as non-fatal step events.

### HP-5: Runner Orchestration Model

**Resolution**: Clarify ownership in plan: workflow runner (executor.py) orchestrates full lifecycle; harness runner (harness/runner.py) handles per-step validation and convergence. Add this to Phase 2 foundational task dependencies.

### HP-6: Platform Parity Timing

**Resolution**: Move parity verification into each phase checkpoint (not Phase-8-only). Phases modifying scripts must include parity smoke check. Full suite runs at Phase 8.

### HP-1: Missing Integration Tests

**Resolution**: Add new Phase 2 foundational contract tests:

- test_delivery_status_contract.py
- test_adapter_doctor_contract.py
- test_convergence_loop_contract.py
- test_hands_off_lifecycle_contract.py
These are Phase 2 gates before user story implementation begins.

## Summary

Implement a delivery-integrity architecture for harness execution: dual status outcomes (`workflow_status`, `delivery_status`), mandatory implementation evidence checks, iterative analyze/critic remediation loops, and an adapter-gated true hands-off lifecycle from plan through pr-review.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: typer, click, rich, pydantic, jsonschema, PyYAML
**Storage**: File-based artifacts under `.documentation/specs/*` and `.documentation/devspark/runs/*`
**Testing**: pytest contract/integration tests in `tests/`
**Target Platform**: Cross-platform CLI (Windows, macOS, Linux)
**Project Type**: CLI + prompt/template framework
**Performance Goals**: Adapter doctor and preflight checks complete within 10 seconds in a typical local environment; stage stall detection fires at configured inactivity threshold (default 5 minutes for write stages)
**Constraints**: Backward compatible additive changes only; explicit mode/adapter behavior; Bash and PowerShell parity; no install/upgrade mutation under `.documentation/`
**Scale/Scope**: Repository-level cross-cutting change touching CLI runtime, templates, scripts, and documentation; dozens of existing tests with new contract coverage required

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Backward Compatibility (PASS)**: Hands-off is opt-in; interactive behavior remains available.
- **II. Explicit Over Implied (PASS)**: Mode semantics, adapter capabilities, failure reason codes, and gate states are explicitly modeled.
- **III. Ownership Boundary (PASS)**: Runtime artifacts remain in repository-owned docs trees already used by runtime; install/upgrade behavior unchanged.
- **IV. Governance Authority (PASS WITH REQUIRED CHECKPOINT)**: Leadership approval checkpoint is required before implementation because this feature is explicitly cross-cutting.
- **V. Simplicity (PASS WITH WATCHPOINT)**: Adds concepts (delivery status, convergence loop) but each addresses a demonstrated failure mode; complexity tracking remains justified.
- **VI. Platform Parity (PASS WITH REQUIRED TESTING)**: Any script/behavior change requires Bash and PowerShell parity tests.
- **VII. PR Review Artifact Commit Discipline (PASS)**: No change to isolation rule; include process tests if workflow logic changes.

Post-Phase-1 Re-check: PASS. No gate violations requiring exception.

### Governance Checkpoint

- Leadership approval is required before `/devspark.implement` begins for this feature.
- Evidence of approval must be recorded in tasks execution notes and referenced in PR context.

## Project Structure

### Documentation (this feature)

```text
.documentation/specs/001-harness-delivery-integrity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── run-outcome-contract.md
│   └── adapter-doctor-contract.md
├── gates/
└── tasks.md
```

### Source Code (repository root)

```text
src/devspark_cli/
├── __init__.py
├── __main__.py
└── ... (CLI runtime modules)

scripts/bash/
├── setup-plan.sh
├── check-prerequisites.sh
└── ...

scripts/powershell/
├── setup-plan.ps1
├── check-prerequisites.ps1
└── ...

templates/
├── commands/
├── workflows/
└── ...

tests/
├── fixtures/
├── runner/
└── test_*_contract.py
```

**Structure Decision**: Keep existing single-project repository layout. Implement runtime logic under `src/devspark_cli/` and enforce parity/contract behavior via updates to `scripts/*`, `templates/*`, and `tests/*`.

## Runner Orchestration Model

### Phase 2b Clarification: Ownership and Responsibility

The DevSpark harness runtime has two distinct runner components with clear ownership boundaries:

### Workflow Runner (executor.py) — Top-Level Orchestrator

**Responsibility**: Sequences the end-to-end workflow from plan through pr-review.

**Location**: `src/devspark_cli/runner/executor.py`

**Capabilities**:

- Parses workflow YAML definitions
- Schedules stages in order (e.g., plan → tasks → analyze → critic → implement → create-pr → pr-review)
- Handles pause/resume and autonomy-level enforcement
- Coordinates telemetry across all stages
- Not responsible for stage-internal validation or finding management

**Ownership Model**: DevSpark framework layer; handles orchestration semantics, not validation logic.

### Harness Runner (harness/runner.py) — Per-Step Validator

**Responsibility**: Executes individual harness steps within the implement stage and validates each step's outcomes.

**Location**: `src/devspark_cli/harness/runner.py`

**Capabilities**:

- Loads and parses harness spec YAML
- Executes each step via selected adapter
- Validates step output against declared rules
- Computes delivery checks and finding status
- Manages lifecycle artifacts (findings, convergence state, stage iterations)
- Emits per-step and per-run telemetry
- Not responsible for cross-stage orchestration or workflow routing

**Ownership Model**: Harness subsystem; handles per-step validation and delivery integrity semantics.

### Collaboration Pattern

```text
WorkflowRunner (Top-Level)
  └─ Calls: implement stage
       └─ Invokes: HarnessRunner
            ├─ Loads: harness spec
            ├─ For each step:
            │  ├─ Executes: adapter.run()
            │  ├─ Validates: rules + delivery checks
            │  └─ Emits: step telemetry
            ├─ Computes: delivery_status + create_pr_ready
            └─ Returns: Run outcome to WorkflowRunner
  └─ Checks: create_pr_ready gate
  └─ Continues: if gate passes
```

### Design Rationale

**Separation of Concerns**:

- Workflow runner handles sequencing and cross-stage decisions
- Harness runner handles validation and per-step evidence
- Each is independently testable and deployable

**Hand-Off Semantic** (for Phase 5 hands-off implementation):

- WorkflowRunner reads run outcome and delivery_status from HarnessRunner
- If delivery_status is unmet, WorkflowRunner blocks create-pr and pr-review transitions
- Re-validation loop (Phase 5 convergence) runs within HarnessRunner, not WorkflowRunner

**Adapter Capability Model** (Phase 4+):

- Adapters report probe() results to HarnessRunner
- HarnessRunner may signal WorkflowRunner to skip write-required stages if adapter is read-only
- This allows graceful degradation in non-write environments (e.g., review-only runs)

### Future Extension: Probe Protocol

**Phase 4 Addition**: Each adapter will implement a `probe()` method returning:

```python
@dataclass
class ProbeResult:
    can_read: bool  # Can execute read steps
    can_write: bool  # Can execute write steps (commits, PRs)
    is_interactive: bool  # Requires user prompts
    ready: bool  # All prerequisites met
    diagnostics: list[str]  # Readiness issues if not ready
```

This allows WorkflowRunner to make routing decisions based on adapter capability without executing trial steps.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
