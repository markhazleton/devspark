---
participants:
  owner: human
  planner: ai
  implementer: ai
  reviewer: human
  critic: ai
  scribe: ai
---

# Tasks: Participant Roles

**Input**: Design documents from `.documentation/specs/001-participant-roles/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Include focused contract tests because the spec requires existing
validation behavior to remain green without participant metadata.

**Organization**: Tasks are grouped by user story to enable independent
implementation and testing of each story.

## Rationale Summary

### Core Problem

DevSpark needs to introduce Squad-style team members without overloading
`agent`, which already means supported AI runtime or client integration.

### Decision Summary

Use `participant` for human or AI-filled team members, keep `agent` reserved
for AI runtimes, and add optional `participants` YAML frontmatter examples to
stock lifecycle templates.

### Key Drivers

- Preserve existing prompt, agent, skill, and customization boundaries.
- Keep participant metadata optional, advisory, and artifact-only.
- Avoid new runtime behavior, routing, inheritance, or validation failures.

### Reviewer Guidance

Review terminology precision, template metadata optionality, test coverage for
non-blocking metadata, markdown quality, and preservation of existing
customization layer precedence.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or has no
  dependency on incomplete tasks.
- **[Story]**: Which user story this task belongs to, such as US1, US2, or US3.
- Include exact file paths in descriptions.

## Path Conventions

- Documentation files live under repository root or `.documentation/`.
- Stock templates live under `templates/`.
- Contract tests live under `tests/`.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish test and documentation targets before changing product
content.

- [X] T001 Review participant metadata contract in `.documentation/specs/001-participant-roles/contracts/participant-metadata.md`
- [X] T002 Review current terminology references in `README.md`, `.documentation/implementation-lifecycle.md`, `.documentation/constitution-guide.md`, and `templates/README.md`
- [X] T003 [P] Inspect current stock template frontmatter in `templates/spec-template.md`, `templates/quick-spec-template.md`, `templates/plan-template.md`, and `templates/tasks-template.md`

**Checkpoint**: Phase complete - 2026-05-31

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add regression tests and shared wording before updating individual
user-story surfaces.

- [X] T004 Create participant terminology and metadata contract tests in `tests/test_participant_metadata_contract.py`
- [X] T005 Add assertions in `tests/test_participant_metadata_contract.py` that existing artifacts without `participants` metadata remain valid by checking representative fixture/spec/template parsing does not require the field
- [X] T006 Add assertions in `tests/test_participant_metadata_contract.py` that stock docs reserve `agent` for AI runtime/client integrations and use `participant` for team-member concepts
- [X] T007 Add assertions in `tests/test_participant_metadata_contract.py` that participant metadata examples do not require personal names, do not recommend storing personally identifying information, and do not mention participant routing, inheritance, or command output behavior

**Checkpoint**: Phase complete - 2026-05-31

**Checkpoint**: Contract tests define the expected vocabulary and optional
metadata behavior before product files are edited.

---

## Phase 3: User Story 1 - Understand Core Vocabulary (Priority: P1)

**Goal**: Users can distinguish prompt, agent, skill, participant, and role in
DevSpark documentation.

**Independent Test**: Read updated documentation and run terminology assertions
in `tests/test_participant_metadata_contract.py`.

### Tests for User Story 1

- [X] T008 [P] [US1] Add test coverage for required glossary terms in `tests/test_participant_metadata_contract.py`

### Implementation for User Story 1

- [X] T009 [US1] Add a glossary section defining `prompt`, `agent`, `skill`, `participant`, and `role` in `README.md`
- [X] T010 [US1] Add lifecycle terminology guidance explaining participant responsibilities in `.documentation/implementation-lifecycle.md`
- [X] T011 [US1] Update template documentation to distinguish prompts, agents, skills, and participants in `templates/README.md`
- [X] T012 [US1] Ensure new team-member guidance uses `participant` instead of redefining `agent` in `README.md`, `.documentation/implementation-lifecycle.md`, and `templates/README.md`

**Checkpoint**: Phase complete - 2026-05-31

**Checkpoint**: Core vocabulary is documented and independently reviewable.

---

## Phase 4: User Story 2 - Preserve Existing Customization Layers (Priority: P2)

**Goal**: Participant guidance explicitly preserves current default, team, and
individual customization behavior.

**Independent Test**: Inspect updated docs and run tests proving the existing
customization text is still present and participant docs do not introduce a new
layer model.

### Tests for User Story 2

- [X] T013 [P] [US2] Add test assertions that `README.md` still documents the existing 3-tier prompt resolution and 2-tier script resolution in `tests/test_participant_metadata_contract.py`
- [X] T014 [P] [US2] Add test assertions that participant documentation does not introduce upstream inheritance or a participant override model in `tests/test_participant_metadata_contract.py`

### Implementation for User Story 2

- [X] T015 [US2] Update `README.md` participant guidance to state that existing customization layers and precedence are unchanged
- [X] T016 [US2] Update `.documentation/implementation-lifecycle.md` to state that participant metadata is advisory and does not affect command, prompt, or script resolution
- [X] T017 [US2] Update `.documentation/constitution-guide.md` only if needed to clarify that participants do not weaken constitution authority or app-level governance

**Checkpoint**: Phase complete - 2026-05-31

**Checkpoint**: Participant docs preserve DevSpark's current customization
process.

---

## Phase 5: User Story 3 - Add Optional Participant Metadata (Priority: P3)

**Goal**: Stock templates show optional `participants` YAML frontmatter examples
without making metadata mandatory.

**Independent Test**: Inspect generated template examples and run tests that
verify metadata is optional and artifact-only.

### Tests for User Story 3

- [X] T018 [P] [US3] Add test assertions that `templates/spec-template.md`, `templates/quick-spec-template.md`, `templates/plan-template.md`, and `templates/tasks-template.md` include optional `participants` YAML frontmatter, and that `templates/plan-template.md` still exposes its `# Implementation Plan` heading after frontmatter is skipped, in `tests/test_participant_metadata_contract.py`
- [X] T019 [P] [US3] Add test assertions that `templates/spec-validation-contract.md` documents optional participant metadata as advisory and non-blocking in `tests/test_participant_metadata_contract.py`

### Implementation for User Story 3

- [X] T020 [US3] Add optional `participants` YAML frontmatter examples to `templates/spec-template.md`
- [X] T021 [US3] Add optional `participants` YAML frontmatter examples to `templates/quick-spec-template.md`
- [X] T022 [US3] Add optional `participants` YAML frontmatter examples to `templates/plan-template.md` while preserving `# Implementation Plan` as the first body heading
- [X] T023 [US3] Add optional `participants` YAML frontmatter examples to `templates/tasks-template.md`
- [X] T024 [US3] Update `templates/spec-validation-contract.md` to state that `participants` is optional advisory metadata and absence must not fail validation
- [X] T025 [US3] Update `templates/README.md` helper template documentation to mention optional participant metadata in stock lifecycle templates

**Checkpoint**: Phase complete - 2026-05-31

**Checkpoint**: Stock templates carry optional participant metadata examples and
existing artifacts without the metadata remain valid.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate the full documentation/template change and prepare it for
review.

- [X] T026 [P] Run `npx markdownlint-cli2 "README.md" ".documentation/**/*.md" "templates/**/*.md"` and fix markdown issues in changed files
- [X] T027 Run `.\.venv\Scripts\python -m pytest -q tests/test_participant_metadata_contract.py` and fix failures
- [X] T028 Run `.\.venv\Scripts\python -m pytest -q` and confirm existing test suite passes without participant metadata in fixtures
- [X] T029 Run `git diff --check` and fix whitespace or line-ending issues in changed files
- [X] T030 Update `.documentation/specs/001-participant-roles/quickstart.md` with final validation notes if commands differ from the planned verification steps

**Checkpoint**: Phase complete - 2026-05-31

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks user-story implementation.
- **User Story 1 (Phase 3)**: Depends on Foundational tests.
- **User Story 2 (Phase 4)**: Depends on User Story 1 terminology where docs refer to participants.
- **User Story 3 (Phase 5)**: Depends on Foundational metadata contract tests.
- **Polish (Phase 6)**: Depends on all desired user stories.

### User Story Dependencies

- **User Story 1 (P1)**: First because all later docs rely on the canonical vocabulary.
- **User Story 2 (P2)**: Can proceed after US1 wording exists.
- **User Story 3 (P3)**: Can proceed after metadata tests exist; it can run partly in parallel with US2.

### Parallel Opportunities

- T003 can run in parallel with T001 and T002.
- T008, T013, T014, T018, and T019 can be split across test file sections after T004.
- T020 through T023 can be implemented in parallel because they touch separate template files.
- T026 can run after documentation/template edits; T027 can run after tests are added.

---

## Parallel Example: User Story 3

```text
Task: "Add optional participants YAML frontmatter examples to templates/spec-template.md"
Task: "Add optional participants YAML frontmatter examples to templates/quick-spec-template.md"
Task: "Add optional participants YAML frontmatter examples to templates/plan-template.md"
Task: "Add optional participants YAML frontmatter examples to templates/tasks-template.md"
```

---

## Gate Acknowledgements

- `checklist`: No unresolved findings.
- `analyze`: Findings I1 and I2 resolved in
  `.documentation/specs/001-participant-roles/gates/analyze.md`.
- `critic`: Findings `critic-001`, `critic-002`, and `critic-003` resolved by
  explicit spec metadata and strengthened implementation test tasks.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete User Story 1 documentation.
3. Run focused terminology tests and markdownlint on changed docs.
4. Validate that users can distinguish prompt, agent, skill, participant, and
   role before extending templates.

### Incremental Delivery

1. Establish tests and vocabulary.
2. Preserve customization layer guidance.
3. Add optional metadata examples to stock templates.
4. Validate markdown and tests.

### Review Strategy

1. Check for accidental redefinition of `agent`.
2. Check that participant metadata remains optional.
3. Check that no task adds routing, inheritance, or command-output behavior.
4. Check that no script parity work is needed because scripts are unchanged.

## Notes

- Participant metadata is artifact-only in this phase.
- Do not add a participant registry.
- Do not modify prompt or script resolution precedence.
- Do not require personal names in examples.
