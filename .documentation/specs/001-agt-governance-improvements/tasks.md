---
description: "Task list for AGT-Inspired Governance Improvements"
participants:
  owner: human
  planner: ai
  implementer: ai
  reviewer: human
  critic: ai
  scribe: ai
---

# Tasks: AGT-Inspired Governance Improvements

**Input**: Design documents from `.documentation/specs/001-agt-governance-improvements/`
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Rationale Summary

### Core Problem

DevSpark's constitution and PR review workflow produce informal, inconsistent governance output: no central severity registry, uniform review depth regardless of spec compliance, no explicit limitations document, and no conformance check for command template drift.

### Decision Summary

Five files (3 new, 2 updated) deliver all four improvements with no new tool dependencies, no new scripts, and no constitution amendments — all additive and backward-compatible.

### Key Drivers

- Severity registry: machine-trackable findings across amendment cycles
- Trust tiers: self-reinforcing incentive for spec-driven development
- Limitations doc: adopter trust through intellectual honesty
- Conformance manifest: prevents silent constitution drift in command templates

### Reviewer Guidance

Verify: severity codes match constitution markers exactly; trust-tier logic is file-presence only; limitations document does not overstate DevSpark's scope; pr-review insertions are purely additive (no existing content removed); markdownlint passes on all new files.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)

---

## Phase 1: Setup

**Purpose**: Verify scaffold and confirm markdownlint configuration covers new file paths.

- [x] T001 Confirm `.markdownlint-cli2.jsonc` does not need updating for `.documentation/memory/` paths (read the file; verify new files will be linted automatically, not excluded)

**Checkpoint**: Phase complete — 2026-06-03

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core governance artifact that all other improvements reference.

**⚠️ CRITICAL**: T002 must be complete before US2, US3, and US4 work can begin — all other stories emit findings that reference the registry.

- [x] T002 Create `.documentation/memory/severity-registry.md` with YAML frontmatter and Markdown table containing all 8 severity entries from research.md (§I–§VIII, SHOWSTOPPER/HIGH/MEDIUM, finding codes, triggers, and remediation examples). Include a self-referential maintenance note in the document: "If `constitution.md` is amended directly without using `/devspark.evolve-constitution`, the author MUST manually verify and update this registry in the same PR."

**Checkpoint**: Severity registry complete — US2, US3, US4 phases can now begin (all can run in parallel after this point).

**Checkpoint**: Phase complete — 2026-06-03

---

## Phase 3: User Story 1 — Structured Severity Registry (Priority: P1) 🎯 MVP

**Goal**: The severity registry exists and pr-review emits `§{section}.{LEVEL}` codes matching registry entries.

**Independent Test**: Run `/devspark.pr-review` on any PR; verify every finding includes a severity code; look up that code in `.documentation/memory/severity-registry.md` and find a matching entry.

### Implementation for User Story 1

- [x] T003 [US1] Update `templates/commands/pr-review.md` — two insertions: (a) Append a "#### Severity Code Format" subsection immediately after the line `| Constitution needs updating (not code) | CON | Governance improvement |` in the "Guidelines > Severity Guidelines" section: mandate `§{section}.{LEVEL}` format for all constitution-linked findings, document examples (`§VI.HIGH`, `§VII.MEDIUM`, `§VIII.HIGH`, `§I.SHOWSTOPPER`), add rule that non-constitution findings emit without a `§` code and are flagged as CON candidates; (b) In step "### 2. Load Constitution", add a sub-bullet: "Load `.documentation/memory/severity-registry.md` if it exists; use its entries to validate `§{section}.{LEVEL}` codes when emitting findings." Verify after editing: run `grep -c "^###" templates/commands/pr-review.md` — count should increase by 0 (no new ### headings from this insertion); confirm file still passes markdownlint.
- [x] T004 [US1] Run `npx markdownlint-cli2 ".documentation/memory/severity-registry.md"` and fix any lint errors before committing

**Checkpoint**: US1 complete — pr-review now references severity codes and the registry is the authoritative lookup.

**Checkpoint**: Phase complete — 2026-06-03

---

## Phase 4: User Story 2 — Trust-Tiered Review Depth (Priority: P2)

**Goal**: pr-review detects branch spec-artifact presence, classifies trust tier, and adjusts scrutiny accordingly.

**Independent Test**: Run `/devspark.pr-review` on a branch with no spec artifacts; verify the output includes a `trust-tier-01` finding with MEDIUM severity and a recommendation to run `/devspark.specify`.

### Implementation for User Story 2

- [x] T005 [US2] Update `templates/commands/pr-review.md` — insert new step "### 1b. Trust-Tier Classification" immediately after the closing paragraph of "### 1. Initialize Review Context" and before the line "### 2. Load Constitution" (use the exact anchor: insert before the line that begins `### 2. Load Constitution`). Content: detect `head_branch`, derive spec dir `.documentation/specs/{head_branch}/`, check for `spec.md`/`plan.md`/`tasks.md`, classify as `full-compliance`/`partial-compliance`/`no-compliance`, emit MEDIUM finding for no-compliance using Shared Review Resolution Contract schema (`finding_id: trust-tier-01`, `severity: medium`, `execution_mode: manual`), and include an explicit reviewer note: "⚠️ No spec artifacts detected — apply heightened attention to all findings in this report." Also search for any existing cross-references to "step 1" or "step 2" in the file and verify they remain accurate after insertion. Verify after editing: run `grep -c "^### [0-9]" templates/commands/pr-review.md` — count should increase by exactly 1 (the new 1b step); confirm markdownlint passes.
- [x] T006 [US2] Run `npx markdownlint-cli2 "templates/commands/pr-review.md"` and fix any lint errors before committing

**Checkpoint**: US2 complete — pr-review now varies scrutiny based on spec-workflow compliance. T003 (US1) must be complete first so severity codes are in place for the trust-tier finding.

**Checkpoint**: Phase complete — 2026-06-03

---

## Phase 5: User Story 3 — Explicit Limitations Documentation (Priority: P3)

**Goal**: `known-limitations.md` exists with at least five honest, well-rationale'd limitations.

**Independent Test**: Read `.documentation/memory/known-limitations.md`; verify at least five limitations with `**Scope**`, `**Rationale**`, and `**Complementary tooling**` fields; verify the file is referenced from `constitution.md` or the project README.

### Implementation for User Story 3

- [x] T007 [P] [US3] Create `.documentation/memory/known-limitations.md` with document header, scope statement, and six limitation entries (L-001 through L-006) from plan.md plus critic-004: L-001 runtime agent behavior, L-002 outcome verification, L-003 cross-session sequences, L-004 technical enforcement, L-005 AI context provenance, L-006 direct-constitution-edit bypass (direct edits to `constitution.md` without using `/devspark.evolve-constitution` leave severity registry and known-limitations silently stale; mitigation: severity-registry.md carries a maintenance note)
- [x] T008 [US3] Add a reference to `known-limitations.md` in `.documentation/memory/constitution.md` — insert a `## Companion Documents` section immediately before the `**Version**:` metadata line at the bottom of the file, containing one bullet: `- [Known Governance Limitations](known-limitations.md)`. Do not append after the version/ratified/last-amended lines.
- [x] T009 [US3] Run `npx markdownlint-cli2 ".documentation/memory/known-limitations.md" ".documentation/memory/constitution.md"` and fix any lint errors before committing

**Checkpoint**: US3 complete — adopters can read limitations alongside the constitution.

**Checkpoint**: Phase complete — 2026-06-03

---

## Phase 6: User Story 4 — Prompt Conformance Lint (Priority: P4)

**Goal**: The conformance manifest exists and can be evaluated against all command templates in `templates/commands/` via `/devspark.checklist`.

**Independent Test**: Open `.documentation/memory/prompt-conformance-manifest.md`; invoke `/devspark.checklist` with the manifest against `templates/commands/`; deliberately remove `## Constitution Authority` from one command template; verify the check reports a HIGH finding citing `§IV`; restore the section and verify the check passes.

### Implementation for User Story 4

- [x] T010 [P] [US4] Create `.documentation/memory/prompt-conformance-manifest.md` with: document header, the three required element checks (Constitution Authority block, frontmatter `handoffs` key, artifact output statement), the conformance check procedure using Shared Review Resolution Contract schema, the known variant headings section (documenting `evolve-constitution.md`'s "## Lifecycle Position" as acceptable), finding ID pattern `conformance-{command-name}-{01|02|03}`, a default behavior rule (any unlisted template is evaluated against the three universal elements; failures flagged as LOW), and deterministic string-match anchors for each check: (1) Constitution Authority passes if the file contains the string `constitution.md` AND the word `non-negotiable` within 15 lines of each other — OR is listed in the Known Variant Headings section with its qualifying text documented; (2) `handoffs` passes if the YAML frontmatter block contains the key `handoffs:`; (3) artifact output statement passes if the file contains at least one of the phrases: "Write", "Save", "Create", "Generate", "Output" within a section describing what the command produces. These string-match anchors make evaluation reproducible across agent runs.
- [x] T011 [US4] Update `templates/commands/evolve-constitution.md` — add two checklist items to the "Review Checklist" block in Step 5 (Proposal Generation): (1) "If the amendment adds, removes, or modifies a severity marker, `.documentation/memory/severity-registry.md` is updated in the same PR (FR-009)" and (2) "Check whether the amendment implies new governance limitations; if so, update `.documentation/memory/known-limitations.md` in the same PR (FR-006)"
- [x] T012 [US4] Run `npx markdownlint-cli2 ".documentation/memory/prompt-conformance-manifest.md" "templates/commands/evolve-constitution.md"` and fix any lint errors before committing
- [x] T013 [US4] Perform baseline conformance check: invoke `/devspark.checklist` with the conformance manifest against all files in `templates/commands/`; document the baseline pass/fail results as a comment in the manifest file. Also manually verify 3 known-good templates (e.g., `specify.md`, `plan.md`, `pr-review.md`) pass all three checks as a sanity test before accepting the full baseline. Note in the manifest: "Re-run this check before any PR that modifies files in `templates/commands/`."

**Checkpoint**: US4 complete — conformance manifest is live and the baseline has been established.

**Checkpoint**: Phase complete — 2026-06-03

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final markdownlint sweep, commit isolation verification, and spec status update.

- [x] T014 [P] Run full markdownlint sweep: `npx markdownlint-cli2 "**/*.md"` from repo root; fix any errors introduced by this feature's files before creating the PR
- [x] T015 Update `.documentation/specs/001-agt-governance-improvements/spec.md` — change `**Status**: Draft` to `**Status**: Complete` now that all tasks are done
- [x] T016 Verify commit isolation discipline (§VII): ensure the PR review file (if one exists at `.documentation/specs/pr-review/pr-NNN.md`) is committed in its own isolated commit, separate from the governance artifact commits

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2 — T002)**: Depends on Setup; **BLOCKS US2, US3, US4 finding emission** (registry must exist before other improvements reference it)
- **US1 Phase (Phase 3 — T003–T004)**: Depends on T002; no dependency on US2/US3/US4
- **US2 Phase (Phase 4 — T005–T006)**: Depends on T002 and T003 (severity codes must be defined before trust-tier finding references them)
- **US3 Phase (Phase 5 — T007–T009)**: Depends on T002; can run in parallel with US1 and US4
- **US4 Phase (Phase 6 — T010–T013)**: Depends on T002; can run in parallel with US1 and US3
- **Polish (Phase 7)**: Depends on all user story phases complete

### User Story Dependencies

- **US1 (P1)**: Depends on T002 (registry) — no other story dependencies
- **US2 (P2)**: Depends on T002 + T003 (severity code format must be established before trust-tier finding references it)
- **US3 (P3)**: Depends on T002 only — fully independent of US1/US2/US4
- **US4 (P4)**: Depends on T002 only — fully independent of US1/US2/US3

### Parallel Opportunities

After T002 (registry) is complete:

- T003+T004 (US1), T007 (US3 part 1), T010 (US4 part 1) can all start in parallel
- T005+T006 (US2) can start after T003 completes
- T008+T009 (US3 part 2) can start after T007 completes

---

## Parallel Example: After Foundational Complete

```text
# Once T002 is done, launch in parallel:
Task T003: Update pr-review.md severity code guidance   [US1]
Task T007: Create known-limitations.md                  [US3]
Task T010: Create prompt-conformance-manifest.md        [US4]

# After T003 completes, start:
Task T005: Update pr-review.md trust-tier step          [US2]
```

---

## Gate Acknowledgements

- **Gate**: analyze, critic
- **Concern**: `required_gates: checklist, analyze, critic` — analyze and critic have not run yet at task generation time. The spec and plan are complete; these gates are appropriate to run before or during implementation, not as a pre-condition to generating tasks.
- **Decision**: Proceed to implementation. Run `/devspark.analyze` and `/devspark.critic` before creating the PR.
- **Recorded By**: planner (ai)
- **Date**: 2026-06-03

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002) — creates severity registry
3. Complete Phase 3: User Story 1 (T003–T004) — pr-review emits severity codes
4. **STOP and VALIDATE**: Run `/devspark.pr-review` on a test PR; confirm `§VI.HIGH`-style codes appear in findings
5. Continue to remaining stories if validated

### Incremental Delivery

1. Setup + Foundational → registry live
2. US1 → severity codes in pr-review → validate
3. US2 → trust tiers in pr-review → validate
4. US3 → limitations document live → validate
5. US4 → conformance manifest + evolve-constitution update → validate baseline
6. Polish → clean sweep → PR ready

### Single-Developer Sequence (Recommended)

```text
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016
```

---

**Checkpoint**: Phase complete — 2026-06-03

## Notes

- No [P] tasks share files — all parallel tasks touch distinct files
- §VII commit discipline: each logical unit (registry, pr-review update, known-limitations, conformance manifest) should be its own commit
- All new `.md` files must pass markdownlint before the PR is opened (tracked as T004, T006, T009, T012, T014)
- Trust-tier insertion in pr-review (T005) is purely additive — verify no existing content is removed; use the exact anchor text in T005 and check heading count after insertion
- Baseline conformance check (T013) may surface existing gaps in command templates; document findings without blocking this PR's merge
- **Contributor obligation (ongoing)**: Run `/devspark.checklist` against `.documentation/memory/prompt-conformance-manifest.md` before any PR that modifies files in `templates/commands/` — this is the re-run trigger for the conformance baseline
- **markdownlint environment**: Requires Node.js + `npx`, or a locally installed `markdownlint-cli2` binary — document this prerequisite in CONTRIBUTING.md if not already present
- **Direct constitution edits**: If `constitution.md` is amended without `/devspark.evolve-constitution`, the author must manually update `severity-registry.md` and check `known-limitations.md` in the same PR (documented as L-006)
