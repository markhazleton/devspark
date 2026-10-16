---
source: "DevSpark — © 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com"
description: "Task list template for feature implementation"
devspark_version: "<version that authored this task list; omit if undeterminable>"
plan_semantic_hash: null
participants:
  owner: human
  planner: ai
  implementer: ai
  reviewer: human
  critic: ai
  scribe: ai
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/.devspark.work/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), spec.md (required for user stories); research.md, data-model.md, contracts/ and quickstart.md only when the plan created them

**Tests**: The examples below include test tasks. Every behavior change considers its Tests impact; the delta is add, update, retire or none, so include test tasks for any delta that is not none, and never assume every change adds tests.

**Pre-PR only**: in every derivation, with or without `qa-acceptance.md`, derive only work that can finish before the PR or merge. Never add a task that waits for deployment, runs QA after merge, needs post-deployment sign-off, belongs to a later sprint, or depends on defects not yet found. A specification delivers a releasable change, not the product release itself; tasks must not include release packaging, version publication, or product deployment. **Post-merge capture** applies to all derivations: a `stage: post-deploy` obligation is not a task; it is carried as a deferred requirement with an owner and an existing durable `captured_as` record.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description (Implements: FR-###[, FR-###])`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- **Implements**: Trailing `(Implements: FR-001, FR-003)` naming the functional requirement ID(s) from `spec.md` that this task satisfies. This makes spec↔task traceability explicit and deterministically checkable by `/devspark-analyze` (coverage gaps + traceability hallucinations). Omit only for pure setup/infrastructure tasks that implement no specific requirement.
- **Linkage**: Every generated task ends with `(code_ref: pending | knowledge_ref: pending)`. After implementation, `code_ref` must list every affected production-code and test path, and `knowledge_ref` every affected current `.knowledge/` path. These references remain in the temporary task record; durable files must never reference `spec.md`, `plan.md`, `tasks.md`, quickfix records, or other temporary work products.
- Include exact file paths in descriptions
- Describe only the implementation or verification delta. Cite requirement and acceptance IDs instead of paraphrasing their text; do not repeat the Spec rationale, research evidence, or Plan decisions.

## Phase 1: Setup

[Include only required setup work; omit an empty phase.]

## Phase 2: Foundational

[Include only blocking shared prerequisites; omit an empty phase.]

## Phase 3: User Story 1 — [Title] (Priority: P1)

**Goal**: [Short implementation outcome; do not repeat the story or acceptance text.]

**Independent Test**: [Reference the relevant Spec acceptance/SC ids; state only additional test context.]

### Tests for User Story 1

[Include only when the Tests delta is not none.]

### Implementation for User Story 1

- [ ] T001 [US1] [Implementation delta and file path] (Implements: FR-001)

**Checkpoint**: [Completion evidence specific to this story.]

## Final Phase: Polish & Cross-Cutting Concerns

[Include only required verification, Knowledge, or linkage work.]

---

## Dependencies

List only actual task/story dependencies not already implied by phase order. Mark parallel tasks with `[P]`; omit this section when no additional dependency exists.

## Gate Acknowledgements

Record any explicit human decisions to proceed despite unresolved checklist, analyze, or critic findings.

- Gate: [checklist|analyze|critic]
- Concern: [concise unresolved issue]
- Decision: [proceed/fix later/escalate]
- Recorded By: [name or role]
- Date: [YYYY-MM-DD]

---
