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

- [X] T001 Add feature constants and defaults in src/devspark_cli/harness/config.py
- [X] T002 Add shared reason-code definitions in src/devspark_cli/harness/spec_models.py
- [X] T003 [P] Add feature quickstart section in .documentation/specs/001-harness-delivery-integrity/quickstart.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and gates required before user-story execution.

**CRITICAL**: No user story implementation starts before this phase completes.

- [X] T004 Extend run outcome schema for workflow_status, delivery_status, and create_pr_ready in src/devspark_cli/harness/spec_models.py
- [X] T005 Add structured delivery check result model with git diff reference strategy in src/devspark_cli/harness/spec_models.py
- [X] T006 [P] Add mutation-aware validation rule support in src/devspark_cli/harness/validation.py
- [X] T007 [P] Add lifecycle artifact writer scaffolding in src/devspark_cli/harness/runner.py
- [X] T008 Implement finding status transitions (open, resolved, deferred) in src/devspark_cli/harness/runner.py
- [X] T009 Add stage-level failure reason-code mapping in src/devspark_cli/harness/runner.py
- [X] T010 Implement pre-implement governance approval guard that validates leadership checkpoint evidence before execution starts in src/devspark_cli/commands.py
- [X] T011 [MVP SCOPE] Implement total-step-timeout and non-UTF decode fallback handling in src/devspark_cli/harness/runner.py (full 5-min stall detection deferred post-MVP pending async subprocess refactor)
- [X] T012 [P] Emit timeout and decode incident non-fatal events with reason codes in src/devspark_cli/harness/telemetry.py
- [X] T013 Record governance checkpoint evidence template in .documentation/specs/001-harness-delivery-integrity/gates/governance-approval.md
- [X] T013a [P] Create test_delivery_status_contract.py with gating and create-pr-ready blocking validation in tests/
- [X] T013b [P] Create test_convergence_loop_contract.py with iteration records and finding state transitions in tests/
- [X] T013c Create CI/CD configuration to run new contract tests in .github/workflows/ (or update existing)
- [X] T013d Perform security audit of subprocess calls with shell=True in validation.py for injection risk in src/devspark_cli/harness/validation.py

**Checkpoint**: Foundation complete, governance gate defined, and new contract tests passing.

---

## Phase 2b: Foundational Runner Orchestration (Blocking for Phase 5)

**Purpose**: Clarify and document runner ownership model for hands-off lifecycle orchestration.

**CRITICAL**: Must complete before Phase 5 hands-off implementation begins.

- [X] T013e Add runner orchestration model documentation to plan.md (workflow runner as top-level, harness runner as subordinate for per-step validation)
- [X] T013f Add AgentAdapter.probe() method signature and ProbeResult model to src/devspark_cli/harness/adapters/__init__.py

**Checkpoint**: Runner model clarified and adapter probe interface defined.

---

## Phase 3: User Story 1 - Detect Non-Delivery Runs (Priority: P1) MVP

**Goal**: Prevent procedural completion from being treated as implementation delivery.

**Independent Test**: Implement stage with no src or test mutations reports delivery_status unmet and create_pr_ready false.

### Implementation for User Story 1

- [X] T014 [US1] Enforce default src/test mutation evidence rule with git diff reference in src/devspark_cli/harness/validation.py
- [X] T015 [US1] Compute create_pr_ready from delivery checks in src/devspark_cli/harness/runner.py
- [X] T016 [P] [US1] Generate no-change explainer section in run artifacts in src/devspark_cli/harness/runner.py
- [X] T017 [P] [US1] Align run outcome contract details in .documentation/specs/001-harness-delivery-integrity/contracts/run-outcome-contract.md
- [X] T018 [US1] Add explicit delivery-status gate before create-pr transition in src/devspark_cli/run_commands.py
- [X] T018a [P] Add parity smoke test for delivery-status enforcement in Bash and PowerShell scripts (bash/powershell)

**Checkpoint**: US1 independently validated. PR1 ready for review.

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

**MVP SCOPE NOTE**: Convergence loop is **re-validation-only** in this release. After each pass, findings are re-evaluated against updated artifacts. Automatic fix generation is deferred to post-MVP. This is achievable without additional LLM infrastructure and still demonstrates iterative convergence behavior. True auto-remediation will be added in a follow-up feature.

### Implementation for User Story 5

- [ ] T024 [US5] Add hands-off option parsing and routing in src/devspark_cli/commands.py
- [ ] T025 [US5] Implement full lifecycle orchestrator in runner/executor.py (workflow runner as top-level, sequences plan → tasks → analyze → critic → implement → create-pr → pr-review)
- [ ] T026 [US5] [MVP: RE-VALIDATION ONLY] Implement analyze and critic re-validation loop controller with max 3 passes in src/devspark_cli/harness/runner.py (evaluates findings against updated outputs without auto-fix generation)
- [ ] T027 [US5] Emit convergence status (converged or max-pass-failed) per stage in src/devspark_cli/harness/runner.py
- [ ] T028 [US5] Add max-pass failure convergence report output in src/devspark_cli/harness/runner.py
- [ ] T029 [US5] Persist per-pass iteration records in src/devspark_cli/harness/telemetry.py
- [ ] T030 [US5] Enforce fail-fast rejection for write-incompatible adapters on write-required stages in src/devspark_cli/harness/runner.py
- [ ] T031 [US5] Enforce create-pr and pr-review dual gating (delivery-status plus branch sync) in src/devspark_cli/run_commands.py
- [ ] T032 [P] [US5] Generate final decision packet output in src/devspark_cli/harness/runner.py
- [ ] T025a Create test_adapter_doctor_contract.py with probe results and capability classification in tests/
- [ ] T025b Create test_hands_off_lifecycle_contract.py with full-chain execution and gating validation in tests/

**Checkpoint**: US5 independently validated. PR2 ready for review.

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

- [ ] T042 [P] Add Bash parity updates for delivery-status enforcement and timeout handling in scripts/bash/check-prerequisites.sh
- [ ] T043 [P] Add PowerShell parity updates for delivery-status enforcement and timeout handling in scripts/powershell/check-prerequisites.ps1
- [ ] T044 Update implement command guidance for governance and convergence gates in templates/commands/implement.md
- [ ] T044a [P] Add adapter doctor troubleshooting to .documentation/harness-engineering.md with probe state explanations
- [ ] T045 Run focused validation command set and record results in .documentation/specs/001-harness-delivery-integrity/gates/validation-smoke.md
- [ ] T046 Run full pytest suite and record pass or fail summary in .documentation/specs/001-harness-delivery-integrity/gates/validation-full.md
- [ ] T047 Refresh lifecycle documentation with canonical adapter doctor terminology in .documentation/implementation-lifecycle.md
- [ ] T048 [P] Update CHANGELOG.md with delivery-integrity feature summary and scope notes
- [ ] T049 [P] Run full parity test suite (Bash + PowerShell) for all modified scripts across Windows/macOS/Linux test matrix

**Checkpoint**: Polish complete. Full feature validated. Ready for final review.

## Dependencies and Execution Order

### Phase Dependencies

- Phase 1 starts immediately.
- Phase 2 depends on Phase 1 and Phase 2b (runner model clarification) and blocks all user stories.
- Phase 2b depends on Phase 2 initial completion and must be done before Phase 5 starts.
- Phase 3 (US1 / PR1) depends on Phase 1-2 completion only; can be released independently.
- Phases 4-8 (PR2) depend on Phase 3 (PR1) being merged first.

### User Story Dependencies

- US1 (Phases 1-3) is PR1 and has no dependencies on other user stories; independently deployable and valuable.
- US2 (Phase 4) depends on Phase 2b runner model clarification.
- US5 (Phase 5) depends on Phase 2b runner model + US1 (Phase 3) + US2 baseline (Phase 4).
- US3 (Phase 6) depends on Phase 2 foundational gates + US1 (Phase 3).
- US4 (Phase 7) depends on US1 baseline + US2 + US5.

### Parallel Opportunities (within same PR phase)

**Within PR1 (Phases 1-3)**:
- T003 in parallel with T001, T002
- T013a, T013b in parallel with T013, T013c, T013d
- T016, T017 in parallel after T014, T015

**Within PR2 (Phases 4-8)**:
- T022, T023 in parallel after T019-T021
- T036, T037 in parallel after T033-T035
- T040, T041 in parallel after T038, T039
- T042, T043 in parallel
- T048 in parallel with Phase 8 work
- T025a, T025b in parallel with T024-T032

---

## Implementation Strategy

### PR1: MVP Delivery Integrity (Phases 1-3, Tasks T001-T018 + T013a-d + T018a)

**Scope**: Core delivery-status gating and validation evidence model.
**User Stories Delivered**: US1 (Detect Non-Delivery Runs) only.
**Standalone Value**: Independently fixes the primary false-positive failure mode.
**Effort**: ~2-3 weeks for single developer or small team.
**Testing**: Includes new contract tests from Phase 2.
**Can be released** as v1.5.1 or similar patch to establish MVP value before PR2.

### PR2: Advanced Features (Phases 4-8, Tasks T019-T049)

**Scope**: Adapter doctor, hands-off orchestration, manual gates, templates, parity, polish.
**Depends On**: PR1 merged and passing.
**User Stories Delivered**: US2, US3, US4, US5 (Adapter Doctor, Manual Gates, Strict Defaults, Hands-Off Lifecycle).
**Effort**: ~4-5 weeks for small team (2-3 developers).
**Testing**: Full contract + integration tests.

### MVP First (PR1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 2b (runner model clarification for future reference).
3. Complete US1 (Phase 3).
4. Validate delivery-status and create_pr_ready behavior.
5. Release PR1.
6. Start PR2 work after PR1 merges.

### Incremental Delivery Strategy (After PR1 Merge)

1. PR1 delivers US1 (delivery integrity MVP).
2. PR2 begins with Phase 2b clarification already documented.
3. Phase 4 (US2 adapter doctor) in parallel with Phase 5 (US5 hands-off) since Phase 5 depends on Phase 2b + US1 already done.
4. Phases 6-7 (US3, US4) can run in parallel after Phase 4 baseline.
5. Phase 8 polish and parity validation across all user stories.

### Parallel Team Strategy (for PR2)

- **Developer A**: Phase 5 (US5 hands-off orchestrator + convergence loop) + Phase 4 adapter doctor probe protocol implementation
- **Developer B**: Phase 6 (US3 manual gates) + Phase 7 (US4 templates) + documentation
- **Developer C**: Phase 8 (parity, validation, polish, CHANGELOG)

---

## Implementation Notes

### MVP Scope Clarifications

- **Convergence Loop (T026-T028)**: Re-validation-only in MVP. After each pass, findings are re-evaluated. Auto-remediation (LLM-driven fix generation) is deferred to post-MVP feature work.
- **Stall Detection (T011)**: Total-step-timeout only in MVP. 5-minute output-inactivity detection requires async subprocess refactor; deferred post-MVP.
- **Git Diff Strategy (T005, T014)**: Use `git diff origin/main...HEAD -- src/ test/` for branch-aware detection.
- **Non-UTF Decode (T011-T012)**: Add `errors="replace"` to all subprocess text decoding; emit telemetry events on replacement.
- **Adapter Probe Protocol (T013f)**: Each adapter implements `probe()` method returning `ProbeResult` with capability flags. Non-destructive, no LLM integration required.

### Risk Mitigation Summary

- **CR-1 (Auto-Remediation)**: Scoped as re-validation-only MVP; eliminates unplanned LLM infrastructure work.
- **CR-2 (Stall Detection)**: Scoped as total-step-timeout only; achievable with current subprocess architecture.
- **CR-3 (Scope Creep)**: Split into 2 PRs; PR1 is independently valuable and can be released.
- **HP-1 through HP-6**: All addressed with explicit task additions, clarifications, or scope adjustments.

---

## Notes

- All tasks follow strict checklist format with explicit paths.
- Canonical term is adapter doctor across artifacts.
- Governance approval is a required pre-implementation checkpoint for PR1 (cross-cutting at phase 1-3 scope).
- PR1 release is independent; PR2 can follow after PR1 merges and is approved.
- No unresolved gate acknowledgements are carried forward; all critic findings have been addressed in this plan update.
