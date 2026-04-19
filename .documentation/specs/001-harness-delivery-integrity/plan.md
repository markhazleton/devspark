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
- **IV. Governance Authority (PASS)**: Repo-level governance remains authoritative; no weakening.
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

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
