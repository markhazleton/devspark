---
participants:
  owner: human
  planner: ai
  implementer: ai
  reviewer: human
  critic: ai
  scribe: ai
---

# Implementation Plan: Participant Roles

**Branch**: `001-participant-roles` | **Date**: 2026-05-31 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `.documentation/specs/001-participant-roles/spec.md`

## Rationale Summary

### Core Problem

DevSpark needs a durable term for Squad-style team members without overloading
`agent`, which already means supported AI runtime or client integration.

### Decision Summary

Document `participant` as the team-member concept, keep `agent` reserved for
runtime integrations, and add optional `participants` YAML frontmatter examples
to stock spec, plan, and task templates.

### Key Drivers

- Maintain existing prompt, agent, skill, and customization boundaries.
- Make responsibility context visible in artifacts without changing execution.
- Preserve backward compatibility for artifacts that omit participant metadata.

### Source Inputs

- [spec.md](spec.md)
- [research.md](research.md)
- [data-model.md](data-model.md)
- [contracts/participant-metadata.md](contracts/participant-metadata.md)
- DevSpark constitution v1.4.0

### Tradeoffs Considered

- Reusing `agent` for participants was rejected because it conflicts with the
  current agent registry and supported AI integration docs.
- Creating a team orchestration engine was rejected because the feature only
  needs vocabulary, examples, and optional metadata.
- Participant metadata in YAML frontmatter was selected because it is compact,
  machine-readable, and optional.

### Architectural Impact

- Markdown documentation and stock templates change.
- No Python runtime behavior is required.
- No Bash or PowerShell helper script change is required.
- No command output should print participant metadata in this phase.

### Reviewer Guidance

Review terminology precision, optional metadata behavior, markdown quality, and
absence of changes to existing customization layer precedence.

## Summary

This feature updates DevSpark's documentation and templates so users can
distinguish AI runtime agents from workflow participants. It introduces
optional `participants` YAML frontmatter examples in the stock spec, plan, and
tasks templates using advisory role-to-kind metadata.

## Technical Context

**Language/Version**: Markdown documentation and YAML frontmatter examples
**Primary Dependencies**: markdownlint-cli2, pytest
**Storage**: N/A
**Testing**: markdownlint-cli2, pytest, targeted text checks
**Target Platform**: Any OS supported by DevSpark
**Project Type**: documentation/templates
**Performance Goals**: N/A
**Constraints**: No change to prompt resolution precedence; no new script
behavior; no required participant metadata
**Scale/Scope**: README, lifecycle docs, template docs, spec/plan/tasks
templates, and focused contract tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Backward Compatibility | PASS | Missing participant metadata remains valid. |
| II. Explicit Over Implied | PASS | Participant metadata is explicit when present and silent when absent. |
| III. Ownership Boundary | PASS | Changes are stock source files and feature artifacts only. |
| IV. Governance Authority | PASS | No weakening of repo-wide governance or app-scope rules. |
| V. Simplicity | PASS | Uses optional frontmatter examples, not a new engine or inheritance model. |
| VI. Platform Parity | PASS | No script changes are planned. |
| VII. PR Review Artifact Commit Discipline | PASS | No PR review artifact changes are planned. |
| VIII. Markdown Quality | PASS | Markdownlint will validate changed markdown files. |

## Project Structure

### Documentation (this feature)

```text
.documentation/specs/001-participant-roles/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- participant-metadata.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
README.md
.documentation/
|-- implementation-lifecycle.md
`-- constitution-guide.md
templates/
|-- README.md
|-- spec-template.md
|-- quick-spec-template.md
|-- plan-template.md
|-- tasks-template.md
`-- spec-validation-contract.md
tests/
`-- test_participant_metadata_contract.py
```

**Structure Decision**: This is a documentation and template feature. The
implementation should avoid new runtime modules unless tests show that existing
contract coverage cannot express the required guarantees.

## Phase 0: Research

Research is complete in [research.md](research.md).

Key decisions:

- Use `participant` for team-member concepts.
- Use optional YAML frontmatter, not visible sections.
- Use advisory roles and role-to-kind metadata.
- Allow optional `name` but do not recommend storing personal data.
- Keep metadata silent in command output.

## Phase 1: Design & Contracts

Design artifacts:

- [data-model.md](data-model.md)
- [contracts/participant-metadata.md](contracts/participant-metadata.md)
- [quickstart.md](quickstart.md)

Implementation should update documentation and templates first, then add focused
tests that prevent regressions in terminology and metadata optionality.

## Constitution Check Re-evaluation

| Principle | Status | Notes |
| --------- | ------ | ----- |
| Backward Compatibility | PASS | Existing artifacts and tests without participants remain supported. |
| Explicit Over Implied | PASS | Metadata shape is explicit and advisory. |
| Ownership Boundary | PASS | No `.documentation/` installation or upgrade behavior changes. |
| Simplicity | PASS | No new participant resolution engine. |
| Platform Parity | PASS | No script changes. |

## Complexity Tracking

No constitution violations require justification.
