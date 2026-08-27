---
participants:
  owner: human
  planner: ai
  implementer: ai
  reviewer: human
  critic: ai
  scribe: ai
---

# Implementation Plan: OKF Traceability and Genuine Fix Discipline

**Branch**: `001-okf-genuine-fix` | **Date**: 2026-08-27 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/.documentation/specs/001-okf-genuine-fix/spec.md`

## Rationale Summary

### Core Problem

DevSpark can emit JSON contracts for lifecycle automation, but it lacks a human-readable and machine-checkable trace from requirements to tasks to gate evidence. Fix and review commands also need stronger discipline so a metric decrease is not mistaken for a behavioral repair.

### Decision Summary

Implement an additive OKF Markdown knowledge layer with YAML frontmatter, validate it with an advisory coverage script, and pin Genuine Fix Discipline in shared command guidance and affected command outputs. Existing JSON contracts remain unchanged.

### Key Drivers

- Preserve byte-for-byte JSON compatibility for existing command consumers.
- Make traceability reviewable by humans and tools.
- Keep old features unblocked when no knowledge folder exists.
- Bias fix/review/verify workflows toward behavior and intent before metrics.
- Maintain Bash and PowerShell parity.

### Source Inputs

- [spec.md](spec.md)
- Repository constitution at `C:/GitHub/MarkHazleton/DevSpark/.documentation/memory/constitution.md`
- Existing lifecycle scripts under `C:/GitHub/MarkHazleton/DevSpark/scripts/bash/` and `C:/GitHub/MarkHazleton/DevSpark/scripts/powershell/`
- Existing command prompts under `C:/GitHub/MarkHazleton/DevSpark/templates/commands/`
- Existing contract tests under `C:/GitHub/MarkHazleton/DevSpark/tests/`

### Tradeoffs Considered

- Modify existing JSON contracts: rejected because it risks breaking current consumers.
- Dual-write OKF Markdown: selected because it creates traceability without requiring migration.
- Hard-fail coverage gaps: rejected because features predating OKF must not be blocked.
- Per-command anti-gaming prose only: rejected because shared preamble guidance and contract tests keep behavior consistent.

### Architectural Impact

- Adds `templates/schemas/okf-knowledge-document.schema.json`.
- Adds knowledge emission helpers to both script families.
- Adds `validate-knowledge-coverage` validators in both script families.
- Updates command templates to reference the validator and Genuine Fix Discipline.
- Adds focused contract tests for schema, emission, validator behavior, and command guidance.

### Reviewer Guidance

Reviewers should focus on compatibility, cross-platform parity, fail-soft behavior, and whether intent cues are specific enough to prevent metric-only remediation.

## Summary

Add a dual-written OKF knowledge layer under each feature's `knowledge/` directory, validate traceability coverage as advisory evidence in analyze/critic, and require fix/review/verify command surfaces to lead with behavioral intent. The implementation is template-and-script oriented, with Python contract tests validating the surface.

## Technical Context

**Language/Version**: Python 3.11+, Bash, PowerShell, Markdown, YAML, JSON Schema
**Primary Dependencies**: Existing `jsonschema>=4.0`, `PyYAML>=6.0`, pytest
**Storage**: Repository files under `.documentation/specs/<feature>/knowledge/` and `templates/`
**Testing**: `pytest` contract tests plus direct Bash/PowerShell wrapper smoke tests
**Target Platform**: DevSpark source and installed template repositories on Windows, macOS, and Linux
**Project Type**: CLI template/framework repository
**Performance Goals**: Coverage validation completes in under 2 seconds for a typical feature directory with fewer than 100 knowledge documents
**Constraints**: Additive only; existing JSON contract output must remain unchanged; coverage validator must fail-soft when `knowledge/` is absent; Bash and PowerShell validators delegate to shared Python coverage logic
**Scale/Scope**: Per-feature documents and validators; no migration of historical feature artifacts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
| --- | --- | --- |
| I. Backward Compatibility | PASS | Design is dual-write and explicitly forbids JSON contract changes. |
| II. Explicit Over Implied | PASS | Knowledge documents use explicit IDs and traceability links. Validator reports missing links rather than inferring silently. |
| III. Ownership Boundary | PASS | Source templates/scripts may emit repository-owned feature work during lifecycle commands; install/upgrade behavior is not changed. |
| IV. Governance Authority | PASS | Adds a constitution hook and matching principle; task T054 requires amendment rationale, leadership approval, version/sync impact, and migration-plan notes before constitution edits. |
| V. Simplicity | PASS | Uses file-based Markdown/YAML plus one shared Python parser behind thin platform wrappers. |
| VI. Platform Parity | PASS | Bash and PowerShell helpers and validators are both required. |
| VII. PR Review Artifact Commit Discipline | PASS | No PR review artifacts are changed by the plan. |
| VIII. Markdown Quality | PASS | New Markdown artifacts must be lintable or covered by existing committed-source rules. |

No constitution waivers are required.

## Project Structure

### Documentation (this feature)

```text
C:/GitHub/MarkHazleton/DevSpark/.documentation/specs/001-okf-genuine-fix/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- knowledge-document.md
|   |-- knowledge-coverage-validator.md
|   `-- genuine-fix-discipline.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
C:/GitHub/MarkHazleton/DevSpark/
|-- src/
|   `-- devspark_cli/
|       `-- _knowledge.py
|-- scripts/
|   |-- bash/
|   |   |-- common.sh
|   |   |-- create-new-feature.sh
|   |   |-- setup-plan.sh
|   |   `-- validate-knowledge-coverage.sh
|   `-- powershell/
|       |-- common.ps1
|       |-- create-new-feature.ps1
|       |-- setup-plan.ps1
|       `-- validate-knowledge-coverage.ps1
|-- templates/
|   |-- commands/
|   |   |-- analyze.md
|   |   |-- critic.md
|   |   |-- implement.md
|   |   |-- quickfix.md
|   |   |-- pr-review.md
|   |   |-- address-pr-review.md
|   |   |-- site-audit.md
|   |   |-- verify.md
|   |   `-- constitution.md
|   |-- schemas/
|   |   `-- okf-knowledge-document.schema.json
|   `-- command-preamble-contract.md
|-- tests/
|   |-- test_knowledge_document_contract.py
|   `-- test_genuine_fix_discipline_contract.py
`-- .github/
    `-- workflows/
        `-- scripts/
            |-- create-release-packages.sh
            `-- create-release-packages.ps1
```

**Structure Decision**: Implement this as a source-template and script change in the existing CLI framework layout. Use a small shared Python module in `src/devspark_cli/_knowledge.py` for OKF frontmatter parsing, schema validation, and coverage aggregation; keep Bash and PowerShell validator scripts as thin wrappers.

## Phase 0: Research

See [research.md](research.md).

## Phase 1: Design and Contracts

See [data-model.md](data-model.md), [quickstart.md](quickstart.md), and the contract documents under [contracts/](contracts/).

## Post-Design Constitution Check

| Principle | Status | Evidence |
| --- | --- | --- |
| I. Backward Compatibility | PASS | Contract tests will compare legacy JSON output to the pre-change key set and values. |
| II. Explicit Over Implied | PASS | OKF schema requires explicit document kind, feature ID, requirement IDs, task IDs, and evidence IDs. |
| III. Ownership Boundary | PASS | Runtime lifecycle writes only feature work product under `.documentation/specs/<feature>/knowledge/`. |
| IV. Governance Authority | PASS | `/devspark.constitution` principle and §9.2 citation hook are planned together, with T054 as the required approval and migration-plan precondition. |
| V. Simplicity | PASS | Validator uses frontmatter and simple Markdown conventions, centralized in one Python parser, instead of introducing a database or registry service. |
| VI. Platform Parity | PASS | Every Bash script change has a PowerShell counterpart in the task list. |
| VII. PR Review Artifact Commit Discipline | PASS | No change to PR review archival semantics. |
| VIII. Markdown Quality | PASS | New committed Markdown command/templates/tests are subject to existing lint workflow. |

No unresolved violations remain.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| None | N/A | N/A |

## Implementation Results

- OKF schema, shared coverage core, Bash wrapper, and PowerShell wrapper were implemented.
- Feature lifecycle scripts now dual-write OKF knowledge documents without changing legacy JSON output tokens.
- `/devspark.analyze` and `/devspark.critic` now include advisory, fail-soft knowledge coverage guidance.
- Genuine Fix Discipline is documented in the shared preamble, review/fix/audit command surfaces, `/devspark.verify`, and Constitution §IX.
- Packaging, upgrade diagnostics, command discovery, README, template README, changelog, and quickstart references were updated.
- Validation completed with focused contract tests, broader prompt/release/upgrade discovery tests, direct script parity, wrapper smoke tests, and markdownlint.
