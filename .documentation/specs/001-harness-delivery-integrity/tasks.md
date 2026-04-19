# Tasks: Harness Delivery Integrity

**Input**: Design documents from .documentation/specs/001-harness-delivery-integrity/
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: The feature specification does not require a TDD-first workflow. Validation tasks are included as executable verification steps.

**Organization**: Tasks are grouped by user story to preserve independent implementation and validation.

## Rationale Summary

### Core Problem

Harness runs can complete orchestration without proving implementation delivery, and adapter behavior can break unattended execution.

### Decision Summary

Implement delivery-integrity contracts, adapter doctor capability checks, iterative convergence loops, and a true hands-off lifecycle option, with governance and gate enforcement made explicit.

### Key Drivers

- Eliminate false-positive completion
- Guarantee deterministic unattended behavior
- Preserve backward compatibility and interactive paths

### Reviewer Guidance

Focus review on governance gate enforcement, delivery-status gating, iterative convergence correctness, decode fail-soft behavior, and Bash/PowerShell parity.

## Format: [ID] [P?] [Story] Description

- [P]: Can run in parallel (different files, no incomplete dependencies)
- [Story]: User story mapping label ([US1], [US2], [US3], [US4], [US5])
- Every task includes an explicit file path

## Path Conventions

- Runtime code: src/devspark_cli/
- Scripts: scripts/bash/, scripts/powershell/
- Templates/docs: templates/, .documentation/
- Validation artifacts: .documentation/specs/001-harness-delivery-integrity/gates/

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare shared constants, reason codes, and analysis artifact locations.

- [ ] T001 Add feature constants and defaults in src/devspark_cli/harness/config.py
- [ ] T002 Add shared reason-code definitions in src/devspark_cli/harness/spec_models.py
- [ ] T003 [P] Add feature quickstart section in .documentation/specs/001-harness-delivery-integrity/quickstart.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and gates required before user-story execution.

**CRITICAL**: No user story implementation starts before this phase completes.

- [ ] T004 Extend run outcome schema for workflow_status, delivery_status, and create_pr_ready in src/devspark_cli/harness/spec_models.py
- [ ] T005 Add structured delivery check result model in src/devspark_cli/harness/spec_models.py
- [ ] T006 [P] Add mutation-aware validation rule support in src/devspark_cli/harness/validation.py
- [ ] T007 [P] Add lifecycle artifact writer scaffolding in src/devspark_cli/harness/runner.py
- [ ] T008 Implement finding status transitions (open, resolved, deferred) in src/devspark_cli/harness/runner.py
- [ ] T009 Add stage-level failure reason-code mapping in src/devspark_cli/harness/runner.py
- [ ] T010 Implement pre-implement governance approval guard that validates leadership checkpoint evidence before execution starts in src/devspark_cli/commands.py
- [ ] T011 Implement stall-detection evaluator, timeout boundary checks, and non-UTF decode fallback handling in src/devspark_cli/harness/runner.py
- [ ] T012 [P] Emit timeout and decode incident non-fatal events with reason codes in src/devspark_cli/harness/telemetry.py
- [ ] T013 Record governance checkpoint evidence template in .documentation/specs/001-harness-delivery-integrity/gates/governance-approval.md

**Checkpoint**: Foundation complete and governance gate defined.

---

## Phase 3: User Story 1 - Detect Non-Delivery Runs (Priority: P1) MVP

**Goal**: Prevent procedural completion from being treated as implementation delivery.

**Independent Test**: Implement stage with no src or test mutations reports delivery_status unmet and create_pr_ready false.

### Implementation for User Story 1

- [ ] T014 [US1] Enforce default src/test mutation evidence rule in src/devspark_cli/harness/validation.py
- [ ] T015 [US1] Compute create_pr_ready from delivery checks in src/devspark_cli/harness/runner.py
- [ ] T016 [P] [US1] Generate no-change explainer section in run artifacts in src/devspark_cli/harness/runner.py
- [ ] T017 [P] [US1] Align run outcome contract details in .documentation/specs/001-harness-delivery-integrity/contracts/run-outcome-contract.md
- [ ] T018 [US1] Add explicit delivery-status gate before create-pr transition in src/devspark_cli/run_commands.py

**Checkpoint**: US1 independently validated.

---

## Phase 4: User Story 2 - Validate Adapter Doctor Readiness Early (Priority: P1)

**Goal**: Diagnose adapter readiness and non-interactive write capability before execution.

**Independent Test**: Adapter doctor returns normalized state and remediation guidance.

### Implementation for User Story 2

- [ ] T019 [US2] Add adapter capability profile model in src/devspark_cli/harness/spec_models.py
- [ ] T020 [US2] Implement adapter doctor command flow in src/devspark_cli/harness/cli.py
- [ ] T021 [US2] Implement behavior-based adapter doctor probes in src/devspark_cli/harness/adapters/__init__.py
- [ ] T022 [P] [US2] Emit normalized adapter doctor output in src/devspark_cli/harness/runner.py
- [ ] T023 [P] [US2] Normalize adapter doctor terminology in .documentation/specs/001-harness-delivery-integrity/contracts/adapter-doctor-contract.md

**Checkpoint**: US2 independently validated.

---

## Phase 5: User Story 5 - Run Full Lifecycle Hands-Off (Priority: P1)

**Goal**: Execute plan through pr-review in a single unattended run when prerequisites are met.

**Independent Test**: Hands-off mode runs full chain without manual prompts and fails fast on blocking gates.

### Implementation for User Story 5

- [ ] T024 [US5] Add hands-off option parsing and routing in src/devspark_cli/commands.py
- [ ] T025 [US5] Implement full lifecycle orchestrator in src/devspark_cli/runner/executor.py
- [ ] T026 [US5] Implement analyze and critic remediation loop controller with max 3 passes in src/devspark_cli/harness/runner.py
- [ ] T027 [US5] Emit convergence status (converged or max-pass-failed) per stage in src/devspark_cli/harness/runner.py
- [ ] T028 [US5] Add max-pass failure convergence report output in src/devspark_cli/harness/runner.py
- [ ] T029 [US5] Persist per-pass iteration records in src/devspark_cli/harness/telemetry.py
- [ ] T030 [US5] Enforce fail-fast rejection for write-incompatible adapters on write-required stages in src/devspark_cli/harness/runner.py
- [ ] T031 [US5] Enforce create-pr and pr-review dual gating (delivery-status plus branch sync) in src/devspark_cli/run_commands.py
- [ ] T032 [P] [US5] Generate final decision packet output in src/devspark_cli/harness/runner.py

**Checkpoint**: US5 independently validated.

---

## Phase 6: User Story 3 - Use Manual Gates with Evidence Policies (Priority: P2)

**Goal**: Preserve interactive policies while keeping hands-off mode free of manual confirmations.

**Independent Test**: Interactive policy behavior works by mode; hands-off path bypasses prompts.

### Implementation for User Story 3

- [ ] T033 [US3] Implement manual gate policy parsing in src/devspark_cli/harness/config.py
- [ ] T034 [US3] Enforce confirm-with-file-check policy in src/devspark_cli/harness/runner.py
- [ ] T035 [US3] Enforce confirm-with-git-diff-check policy in src/devspark_cli/harness/runner.py
- [ ] T036 [P] [US3] Ensure hands-off mode bypasses manual confirmation prompts in src/devspark_cli/harness/cli.py
- [ ] T037 [P] [US3] Update interactive manual-gate guidance in .documentation/harness-engineering.md

**Checkpoint**: US3 independently validated.

---

## Phase 7: User Story 4 - Adopt Strict Harness Defaults Quickly (Priority: P3)

**Goal**: Reduce setup friction with strict defaults and clear guidance.

**Independent Test**: Strict harness template yields meaningful pass/fail signals without schema debugging.

### Implementation for User Story 4

- [ ] T038 [US4] Add strict harness template in templates/workflows/harness-strict-template.md
- [ ] T039 [US4] Add strict template wiring in src/devspark_cli/commands.py
- [ ] T040 [P] [US4] Document strict template usage in .documentation/quickstart.md
- [ ] T041 [P] [US4] Add no-change explainer troubleshooting docs in .documentation/harness-engineering.md

**Checkpoint**: US4 independently validated.

---

## Phase 8: Polish and Cross-Cutting Concerns

**Purpose**: Parity, docs consistency, and concrete validation execution.

- [ ] T042 [P] Add Bash parity updates for hands-off and adapter doctor preflight in scripts/bash/check-prerequisites.sh
- [ ] T043 [P] Add PowerShell parity updates for hands-off and adapter doctor preflight in scripts/powershell/check-prerequisites.ps1
- [ ] T044 Update implement command guidance for governance and convergence gates in templates/commands/implement.md
- [ ] T045 Run focused validation command set and record results in .documentation/specs/001-harness-delivery-integrity/gates/validation-smoke.md
- [ ] T046 Run full pytest suite and record pass or fail summary in .documentation/specs/001-harness-delivery-integrity/gates/validation-full.md
- [ ] T047 Refresh lifecycle documentation with canonical adapter doctor terminology in .documentation/implementation-lifecycle.md

---

## Dependencies and Execution Order

### Phase Dependencies

- Phase 1 starts immediately.
- Phase 2 depends on Phase 1 and blocks all user stories.
- Phase 3 through Phase 7 depend on Phase 2 completion.
- Phase 8 depends on completion of target user stories.

### User Story Dependencies

- US1 depends only on foundational delivery contracts.
- US2 depends on foundational models and adapter interfaces.
- US5 depends on US1 and US2 baseline behavior.
- US3 depends on foundational gate framework and can start after US1 baseline.
- US4 depends on stable behavior from US1, US2, and US5.

### Parallel Opportunities

- T003 in parallel with T001 and T002
- T006 and T007 in parallel after T004 and T005
- T011 and T012 in parallel after core runner wiring is in place
- T016 and T017 in parallel after T014 and T015
- T022 and T023 in parallel after T019 through T021
- T036 and T037 in parallel after T033 through T035
- T040 and T041 in parallel after T038 and T039
- T042 and T043 in parallel

---

## Parallel Example: User Story 5

```bash
Task: "T027 [US5] Emit convergence status in src/devspark_cli/harness/runner.py"
Task: "T029 [US5] Persist per-pass iteration records in src/devspark_cli/harness/telemetry.py"
Task: "T032 [P] [US5] Generate final decision packet output in src/devspark_cli/harness/runner.py"
```

---

## Implementation Strategy

### MVP First (US1)

1. Complete Phase 1 and Phase 2.
2. Complete US1 (Phase 3).
3. Validate delivery-status and create_pr_ready behavior before advancing.

### Incremental Delivery

1. Deliver US1 then US2.
2. Deliver US5 hands-off orchestration and convergence behavior.
3. Deliver US3 interactive policy refinements.
4. Deliver US4 strict-template and docs refinements.
5. Complete phase 8 parity and validation.

### Parallel Team Strategy

1. Team completes foundational phase together.
2. Developer A: US1 plus US5 orchestration and convergence.
3. Developer B: US2 adapter doctor plus US3 policies.
4. Developer C: US4 docs/templates and phase 8 parity and validation tasks.

---

## Notes

- All tasks follow strict checklist format with explicit paths.
- Canonical term is adapter doctor across artifacts.
- Governance approval is a required pre-implementation checkpoint for this cross-cutting feature.
- No unresolved gate acknowledgements are carried forward.
