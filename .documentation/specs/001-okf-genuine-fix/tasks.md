---
description: "Task list for OKF Traceability and Genuine Fix Discipline"
participants:
  owner: human
  planner: ai
  implementer: ai
  reviewer: human
  critic: ai
  scribe: ai
---

# Tasks: OKF Traceability and Genuine Fix Discipline

**Input**: Design documents from `C:/GitHub/MarkHazleton/DevSpark/.documentation/specs/001-okf-genuine-fix/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`

**Tests**: Contract tests are required by the feature specification. Write or update tests before implementation tasks in each story.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete work.
- **[Story]**: User story label for story phases only.
- Every task includes an exact repository file path.

## Phase 1: Setup

**Purpose**: Establish common files and test surfaces used by all stories.

- [X] T001 Create schema directory `templates/schemas/` for committed OKF schemas.
- [X] T002 Create shared guidance file `templates/command-preamble-contract.md` with placeholder sections for Genuine Fix Discipline.
- [X] T003 [P] Create contract test file `tests/test_knowledge_document_contract.py` for OKF schema, emission, JSON-baseline, packaging, and coverage validator behavior.
- [X] T004 [P] Create contract test file `tests/test_genuine_fix_discipline_contract.py` for command preamble, required command references, intent fields, constitution hook, command discovery, and verify guard surface.
- [X] T005 [P] Update parity expectations in `tests/test_script_parity_contract.py` for the new `validate-knowledge-coverage` Bash and PowerShell wrappers if explicit tokens are needed beyond stem parity.

**Checkpoint**: Phase complete - setup test surfaces and shared contract locations exist.

---

## Phase 2: Foundational

**Purpose**: Add reusable contracts and cross-platform helpers before story-specific command integration.

- [X] T006 Create OKF frontmatter schema in `templates/schemas/okf-knowledge-document.schema.json`.
- [X] T007 Create shared Python OKF coverage module in `src/devspark_cli/_knowledge.py` using existing `PyYAML` and `jsonschema` dependencies.
- [X] T008 Add Bash knowledge helper functions to `scripts/bash/common.sh` for creating `knowledge/` and writing OKF Markdown without changing JSON output.
- [X] T009 Add PowerShell knowledge helper functions to `scripts/powershell/common.ps1` for creating `knowledge/` and writing OKF Markdown without changing JSON output.
- [X] T010 Create Bash wrapper `scripts/bash/validate-knowledge-coverage.sh` with `--feature-dir` and `--json` support that delegates parsing and coverage aggregation to `src/devspark_cli/_knowledge.py`.
- [X] T011 Create PowerShell wrapper `scripts/powershell/validate-knowledge-coverage.ps1` with `-FeatureDir` and `-Json` support that delegates parsing and coverage aggregation to `src/devspark_cli/_knowledge.py`.
- [X] T012 [P] Add schema-validation fixtures inside `tests/test_knowledge_document_contract.py` for valid and invalid OKF frontmatter examples.
- [X] T013 [P] Add fail-soft and wrapper-parity fixtures inside `tests/test_knowledge_document_contract.py` for present, incomplete, invalid, and absent `knowledge/` directories.
- [X] T014 Re-run `tests/test_script_parity_contract.py` after new scripts exist to confirm Bash and PowerShell parity.

**Checkpoint**: Phase complete - OKF schema, shared parser, helper functions, and both platform wrappers exist before lifecycle scripts emit or consume knowledge documents.

---

## Phase 3: User Story 1 - OKF Knowledge Documents (Priority: P1)

**Goal**: New feature and plan lifecycle scripts emit OKF Markdown knowledge documents in parallel with unchanged JSON contracts.

**Independent Test**: Run feature-generation fixtures and confirm `knowledge/` exists with schema-valid Markdown while JSON output remains byte-for-byte compatible.

### Tests for User Story 1

- [X] T015 [P] [US1] Add Bash `create-new-feature.sh --json` before/after JSON baseline assertions in `tests/test_knowledge_document_contract.py`.
- [X] T016 [P] [US1] Add PowerShell `create-new-feature.ps1 -Json` before/after JSON baseline assertions in `tests/test_knowledge_document_contract.py`.
- [X] T017 [P] [US1] Add Bash `setup-plan.sh --json` before/after JSON baseline assertions in `tests/test_knowledge_document_contract.py`.
- [X] T018 [P] [US1] Add PowerShell `setup-plan.ps1 -Json` before/after JSON baseline assertions in `tests/test_knowledge_document_contract.py`.
- [X] T019 [P] [US1] Add setup-plan OKF emission assertions in `tests/test_knowledge_document_contract.py`.

### Implementation for User Story 1

- [X] T020 [US1] Update `scripts/bash/create-new-feature.sh` to call the Bash OKF helper after `spec.md` creation without adding, removing, reordering, or mutating JSON fields.
- [X] T021 [US1] Update `scripts/powershell/create-new-feature.ps1` to call the PowerShell OKF helper after `spec.md` creation without adding, removing, reordering, or mutating JSON fields.
- [X] T022 [US1] Update `scripts/bash/setup-plan.sh` to write or refresh a plan-stage OKF document without adding, removing, reordering, or mutating JSON fields.
- [X] T023 [US1] Update `scripts/powershell/setup-plan.ps1` to write or refresh a plan-stage OKF document without adding, removing, reordering, or mutating JSON fields.
- [X] T024 [P] [US1] Document the OKF knowledge document contract in `templates/README.md`.
- [X] T025 [US1] Run `pytest tests/test_knowledge_document_contract.py` and fix schema, emission, or JSON-baseline issues in `templates/schemas/okf-knowledge-document.schema.json`, `src/devspark_cli/_knowledge.py`, and the script files.

**Checkpoint**: Phase complete - User Story 1 lifecycle runs produce valid OKF documents and legacy JSON consumers see no contract change.

---

## Phase 4: User Story 2 - Knowledge Coverage Validation (Priority: P2)

**Goal**: Analyze and critic run advisory coverage validation and skip cleanly when no knowledge layer exists.

**Independent Test**: Run coverage validation against fixture features with complete, incomplete, invalid, and absent knowledge documents, then confirm analyze/critic prompt contracts reference the advisory pass.

### Tests for User Story 2

- [X] T026 [P] [US2] Add Bash wrapper output assertions in `tests/test_knowledge_document_contract.py`.
- [X] T027 [P] [US2] Add PowerShell wrapper output assertions in `tests/test_knowledge_document_contract.py`.
- [X] T028 [P] [US2] Add shared Python coverage-core assertions in `tests/test_knowledge_document_contract.py`.
- [X] T029 [P] [US2] Add analyze and critic prompt-reference assertions in `tests/test_knowledge_document_contract.py`.

### Implementation for User Story 2

- [X] T030 [US2] Implement coverage counting, schema validation, and skip behavior in `src/devspark_cli/_knowledge.py`.
- [X] T031 [US2] Wire `scripts/bash/validate-knowledge-coverage.sh` to the shared Python coverage core and preserve advisory successful exits for `ok`, `warn`, and `skipped`.
- [X] T032 [US2] Wire `scripts/powershell/validate-knowledge-coverage.ps1` to the shared Python coverage core and preserve advisory successful exits for `ok`, `warn`, and `skipped`.
- [X] T033 [US2] Update `templates/commands/analyze.md` to run `validate-knowledge-coverage` as an additive, fail-soft advisory pass.
- [X] T034 [US2] Update `templates/commands/critic.md` to run `validate-knowledge-coverage` as an additive, fail-soft advisory pass.
- [X] T035 [P] [US2] Update `templates/prompts/atomic/analyze.md` only if its frontmatter or shim text must expose new advisory outputs.
- [X] T036 [P] [US2] Update `templates/prompts/atomic/critic.md` only if its frontmatter or shim text must expose new advisory outputs.
- [X] T037 [US2] Run Bash, PowerShell, and Python coverage smoke tests using fixtures created in `tests/test_knowledge_document_contract.py`.

**Checkpoint**: Phase complete - User Story 2 validators are cross-platform equivalent and analyze/critic clearly report coverage without blocking absent knowledge folders.

---

## Phase 5: User Story 3 - Genuine Fix Discipline (Priority: P3)

**Goal**: Fix, review, audit, and verify command surfaces require behavioral intent before metric remediation.

**Independent Test**: Run static contract tests confirming shared guidance, required command references, `intent_cue`/`Intent` fields, constitution hook, command discovery, packaging coverage, and verify guard behavior.

### Tests for User Story 3

- [X] T038 [P] [US3] Add preamble Section 9, Section 9.1 table, and Section 9.2 citation hook assertions in `tests/test_genuine_fix_discipline_contract.py`.
- [X] T039 [P] [US3] Add required command-reference assertions for `templates/commands/implement.md`, `templates/commands/quickfix.md`, `templates/commands/pr-review.md`, and `templates/commands/address-pr-review.md` in `tests/test_genuine_fix_discipline_contract.py`.
- [X] T040 [P] [US3] Add finding-field assertions for `templates/commands/analyze.md`, `templates/commands/critic.md`, and `templates/commands/site-audit.md` in `tests/test_genuine_fix_discipline_contract.py`.
- [X] T041 [P] [US3] Add verify guard assertions for `templates/commands/verify.md` and `templates/prompts/atomic/verify.md` in `tests/test_genuine_fix_discipline_contract.py`.
- [X] T042 [P] [US3] Add constitution-principle assertions for `templates/commands/constitution.md` and `.documentation/memory/constitution.md` in `tests/test_genuine_fix_discipline_contract.py`.
- [X] T043 [P] [US3] Add command-discovery and atomic-shim coverage assertions for `/devspark.verify` in `tests/test_genuine_fix_discipline_contract.py`.

### Implementation for User Story 3

- [X] T044 [US3] Fill `templates/command-preamble-contract.md` with Section 9 Genuine Fix Discipline, Section 9.1 intent-cue table, cross-language note, and Section 9.2 constitution-citation hook.
- [X] T045 [US3] Update `templates/commands/implement.md` to reference Genuine Fix Discipline before resolving findings or task-linked gates.
- [X] T046 [US3] Update `templates/commands/quickfix.md` to reference Genuine Fix Discipline before metric-focused remediation.
- [X] T047 [US3] Update `templates/commands/pr-review.md` to reference Genuine Fix Discipline and require behavioral intent in review findings.
- [X] T048 [US3] Update `templates/commands/address-pr-review.md` to reference Genuine Fix Discipline when resolving PR review findings.
- [X] T049 [US3] Update `templates/commands/analyze.md` so findings include `intent_cue`.
- [X] T050 [US3] Update `templates/commands/critic.md` so findings include `intent_cue`.
- [X] T051 [US3] Update `templates/commands/site-audit.md` so findings include an `Intent` field.
- [X] T052 [US3] Create `templates/commands/verify.md` with a Genuine Fix Guard that fails metric-only proof with unchanged behavior.
- [X] T053 [US3] Create atomic shim `templates/prompts/atomic/verify.md` that delegates to `templates/commands/verify.md`.
- [X] T054 [US3] Record constitution amendment rationale, leadership approval, version/sync impact report, and migration-plan notes before changing constitution files in `.documentation/specs/001-okf-genuine-fix/contracts/genuine-fix-discipline.md`.
- [X] T055 [US3] Update `templates/commands/constitution.md` with the Genuine Fix Discipline principle surface after T054 is complete.
- [X] T056 [US3] Amend `.documentation/memory/constitution.md` with a matching Genuine Fix Discipline principle and sync impact report after T054 is complete.
- [X] T057 [US3] Run `pytest tests/test_genuine_fix_discipline_contract.py` and fix command-surface gaps.

**Checkpoint**: Phase complete - User Story 3 command contracts make metric-only fixes invalid unless behavioral intent and proof are satisfied.

---

## Phase 6: Packaging, Upgrade, and Discovery

**Purpose**: Ensure source-repo changes ship to installed and upgraded DevSpark users.

- [X] T058 [P] Add release-package assertions proving `templates/schemas/okf-knowledge-document.schema.json` ships in template packages.
- [X] T059 [P] Add release-package assertions proving `templates/command-preamble-contract.md` ships in template packages.
- [X] T060 [P] Add release-package assertions proving `templates/commands/verify.md` and `templates/prompts/atomic/verify.md` ship in template packages.
- [X] T061 [P] Add upgrade/preflight assertions proving missing schema, validator, preamble, and verify command files are surfaced in upgrade diagnostics.
- [X] T062 [P] Add command-discovery assertions proving `/devspark.verify` is discoverable through the same command listing path as other commands.
- [X] T063 [P] Update `README.md` with `/devspark.verify` documentation if the command is user-facing.
- [X] T064 [P] Update `templates/README.md` with schema, validator, and Genuine Fix Discipline guidance locations.

**Checkpoint**: Phase complete - packaging, upgrade diagnostics, and command discovery cover the new files.

---

## Phase 7: Polish and Cross-Cutting Concerns

**Purpose**: Validate the whole feature, documentation quality, and compatibility surface.

- [X] T065 [P] Update `CHANGELOG.md` with an unreleased entry for OKF traceability and Genuine Fix Discipline.
- [X] T066 Run `pytest tests/test_knowledge_document_contract.py tests/test_genuine_fix_discipline_contract.py tests/test_script_parity_contract.py` from `C:/GitHub/MarkHazleton/DevSpark`.
- [X] T067 Run the broader relevant contract suite with `pytest tests/test_prompt_gate_contract.py tests/test_atomic_prompt_frontmatter_contract.py tests/test_script_parity_contract.py tests/test_template_release_fallback.py tests/test_upgrade_preflight.py` from `C:/GitHub/MarkHazleton/DevSpark`.
- [X] T068 Run Markdown lint command `npx markdownlint-cli2 "**/*.md"` from `C:/GitHub/MarkHazleton/DevSpark`.
- [X] T069 Review `git diff -- templates scripts src tests .documentation/memory/constitution.md README.md CHANGELOG.md` to confirm JSON contract output remains additive only.
- [X] T070 Update `.documentation/specs/001-okf-genuine-fix/quickstart.md` with final command examples if implementation changes script flags.

**Checkpoint**: Phase complete - polish, validation, and compatibility review completed.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational helpers, schema, and shared parser.
- **User Story 2 (Phase 4)**: Depends on the shared parser and platform wrappers.
- **User Story 3 (Phase 5)**: Depends on the shared preamble file from Setup. T055 and T056 depend on T054.
- **Packaging, Upgrade, and Discovery (Phase 6)**: Depends on command, schema, wrapper, and shim surfaces existing.
- **Polish (Phase 7)**: Depends on selected user stories and packaging/discovery work being complete.

### User Story Dependencies

- **US1**: Can be delivered independently once schema, helper functions, and JSON-baseline tests exist.
- **US2**: Depends on the shared coverage core and wrappers; does not require US1 emission to be complete if fixtures provide knowledge documents.
- **US3**: Independent of OKF emission and coverage validation after shared preamble exists; constitution edits require T054 approval evidence first.

### MVP Scope

The MVP is **US1 only**: schema plus lifecycle dual-write knowledge documents with unchanged JSON output. US2 and US3 can follow as independent increments.

## Parallel Opportunities

- T003, T004, and T005 can run in parallel after T001 and T002 are created.
- T008 and T009 can run in parallel after T006.
- T010 and T011 can run in parallel after T007.
- T015 through T019 can run in parallel.
- T026 through T029 can run in parallel.
- T038 through T043 can run in parallel.
- T058 through T064 can run in parallel after command and schema surfaces exist.

## Parallel Example: User Story 1

```bash
# JSON baseline tests can be assigned together:
Task: "T015 Add Bash create-new-feature JSON baseline assertions in tests/test_knowledge_document_contract.py"
Task: "T016 Add PowerShell create-new-feature JSON baseline assertions in tests/test_knowledge_document_contract.py"
Task: "T017 Add Bash setup-plan JSON baseline assertions in tests/test_knowledge_document_contract.py"
Task: "T018 Add PowerShell setup-plan JSON baseline assertions in tests/test_knowledge_document_contract.py"
```

## Parallel Example: User Story 3

```bash
# Command-surface contract tests can be assigned together:
Task: "T038 Add preamble assertions in tests/test_genuine_fix_discipline_contract.py"
Task: "T039 Add required command-reference assertions in tests/test_genuine_fix_discipline_contract.py"
Task: "T040 Add finding-field assertions in tests/test_genuine_fix_discipline_contract.py"
Task: "T041 Add verify guard assertions in tests/test_genuine_fix_discipline_contract.py"
```

## Gate Acknowledgements

Analyze and critic findings were applied to this revised task list on 2026-08-27.

- Gate: analyze
- Concern: Installed-template delivery, JSON byte-for-byte proof, and constitution governance gaps.
- Decision: Apply all remediation actions before implementation.
- Recorded By: ai
- Date: 2026-08-27

- Gate: critic
- Concern: Missing metadata, constitution governance, validator parser divergence, and verify delivery risk.
- Decision: Apply all remediation actions before implementation.
- Recorded By: ai
- Date: 2026-08-27

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 for OKF emission.
3. Run the US1 contract tests and script parity checks.
4. Stop and validate that JSON output is unchanged for all four lifecycle-script baselines.

### Incremental Delivery

1. Deliver US1 for knowledge document emission and JSON compatibility.
2. Deliver US2 for shared-core coverage reporting in analyze and critic.
3. Deliver US3 for Genuine Fix Discipline command surfaces and verify guard.
4. Deliver packaging, upgrade, and discovery coverage.
5. Run polish tasks and full contract checks.

## Notes

- Keep script edits paired across Bash and PowerShell in the same implementation slice.
- Do not modify existing JSON output fields for `create-new-feature` or `setup-plan`.
- Keep coverage validator failure modes advisory unless a future spec introduces strict mode.
- Every metric-related fix example must name the behavioral intent it proves.
- Constitution amendments cannot proceed until T054 is complete.
