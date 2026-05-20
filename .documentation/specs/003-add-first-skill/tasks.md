---
description: "Task list for feature 003-add-first-skill"
---

# Tasks: Add First Agent Skill (write-spec)

**Input**: Design documents from `.documentation/specs/003-add-first-skill/`
**Prerequisites**: plan.md ✓, spec.md ✓, checklists/requirements.md ✓
**Tests**: Test tasks included — required by spec (FR-011, FR-012, SC-002, SC-003).

**Organization**: Tasks grouped by sub-phase (2A → 2B → 2C → 2D, mandatory order)
then by user story within each sub-phase.

## Rationale Summary

### Core Problem

DevSpark's `/devspark.*` slash-command prompts use a DevSpark-specific frontmatter
contract that is not interoperable with the open Agent Skills standard. No DevSpark
capability can be discovered or executed by skills-compatible clients without
bespoke DevSpark tooling.

### Decision Summary

Ship one portable pilot skill (`write-spec`) that complies with the open Agent
Skills specification. Refactor `/devspark.specify` to delegate spec-drafting to
that skill via a documented adapter contract. Add CLI validation and tests that
gate skill contract compliance on every PR.

### Key Drivers

- Interoperability: any skills-compatible client can load and run `write-spec`
  with zero DevSpark-specific configuration.
- Standards awareness: demonstrate first-class support for agentskills.io.
- Context engineering as differentiator: the skill ships with deterministic
  dual-parity context-gathering scripts, not just prompt text.

### Reviewer Guidance

- Check adapter contract clarity (2A) before reviewing the skill (2B).
- Confirm `SKILL.md` has no DevSpark-only frontmatter keys (2B).
- Verify existing integration tests pass unchanged after the command refactor (2D).
- Scope discipline: exactly one skill (`write-spec`, spec-drafting only).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared state dependencies)
- **[Story]**: User story: [US1], [US2], [US3]
- File paths are absolute from repository root

## Path Conventions

Single project layout. Skills surface under `templates/skills/`. CLI under
`src/devspark_cli/commands/`. Tests under `tests/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm directory skeleton exists and markdownlint baseline is green
before authoring any new files.

- [x] T001 Verify `templates/skills/` directory exists with `write-spec/` and
  `references/` subdirectories; create any missing directories; confirm
  `PyYAML>=6.0` is present as a direct dependency in `pyproject.toml`
  (critic-006 — already declared; verification step ensures it stays explicit
  if lockfile is regenerated)
- [x] T002 [P] Run `npx markdownlint-cli2 "**/*.md"` from repo root and confirm
  zero errors as the baseline before new files are added
- [x] T003 [P] Confirm existing test suite passes: `pytest tests/` (establishes
  regression baseline before any code changes)

**Checkpoint**: Phase complete — 2026-05-19

---

## Phase 2: Foundational (Sub-phase 2A — Shared Skills Foundation)

**Purpose**: Contract files and shared guide must exist and be stable before the
skill body (2B), the tests (2C), or the command refactor (2D) can proceed.

**Constitution enforcement**:

- §I Backward Compatibility: FR-016 enforced by regression baseline in T003 and
  confirmed again in T023 and T031 (full suite passes unchanged).
- §VI Platform Parity: FR-009 tasks T013 (PowerShell) and T014 (Bash) require
  dual equivalent scripts; parity verified in T017.
- §VIII Markdown Quality: T010 runs markdownlint after all 2A files are authored.

**⚠️ CRITICAL**: No 2B, 2C, or 2D work can begin until this phase is complete.

- [x] T004 Author `templates/skills/SKILL-validation-contract.md` — upstream
  Agent Skills frontmatter rules (name/description/length limits) + DevSpark
  addendum (required `metadata.version`, required body sections, body-length
  budget, prohibited keys, repair rules consistent with
  `templates/spec-validation-contract.md`); MUST include the three-tier exit-code
  table: `pass` exits 0 (one-line summary on stdout); `warn` exits 0 with
  warning count on stderr and advisory details (body budget pressure does not
  block CI); `fail` exits 1 with diagnostic `[RULE] [OFFENDING-VALUE] message`
  on stderr (critic-002 — prevents CI silently accepting oversized skills)
- [x] T005 Author `templates/skills/ADAPTER-contract.md` — skill discovery rules,
  input mapping (`$FEATURE_DESCRIPTION`, `$CONSTITUTION_PATH`,
  `$PRIOR_SPEC_SUMMARY`), output mapping (draft → SPEC_FILE), responsibility
  split (command vs. skill vs. adapter), backward-compatibility rules
- [x] T006 Complete `templates/skills/references/devspark-skills-guide.md` —
  **SC-005 owner**: this file carries the step-by-step new-skill walkthrough;
  ensure it includes: (a) validation surface section, (b) adding-a-skill workflow
  with numbered steps referencing T004 contracts + write-spec as the worked
  example, (c) review checklist section; content must be sufficient for a new
  contributor to author and pass a second skill on their first PR attempt
  (SC-005); consistent with T004/T005 contracts
- [x] T007 Author `templates/skills/README.md` — pointer-only landing page for
  the `skills/` surface; dual-surface model summary (`command → adapter → skill`);
  links to `ADAPTER-contract.md`, `SKILL-validation-contract.md`, and
  `references/devspark-skills-guide.md` (where the SC-005 walkthrough lives);
  does not duplicate walkthrough content
- [x] T008 Update `README.md` (repo root) — add positioning statement ("DevSpark
  treats skills as portable capability packages within a governed lifecycle
  orchestration system"), dual-surface model description, pointers to
  `templates/skills/README.md` and the two contract files (FR-019)
- [x] T009 Update `CLAUDE.md` — add positioning statement and `command → invokes →
  skill` internal architecture note; pointer to `templates/skills/` (FR-019)
- [x] T010 Run `npx markdownlint-cli2 "**/*.md"` — confirm zero errors after all
  2A files are authored (§VIII gate)

**Checkpoint 2A**: `ADAPTER-contract.md` and `SKILL-validation-contract.md` both
exist and are lint-clean; `devspark-skills-guide.md` is complete; `README.md`
and `CLAUDE.md` carry the FR-019 updates. Proceed to 2B.

**Checkpoint**: Phase complete — 2026-05-19

---

## Phase 3: User Story 1 — Portable skill executes in a non-DevSpark client (P1)

**Goal**: A skills-compatible client with no DevSpark installation can load
`templates/skills/write-spec/` and produce a valid `spec.md` artifact.

**Independent Test**: Copy only `templates/skills/write-spec/` into a fresh
workspace without DevSpark CLI installed. Load into a skills-compatible client
per its standard installation flow. Request a draft spec for a sample feature
description. Verify the produced `spec.md` conforms to
`templates/spec-validation-contract.md`.

**Sub-phase**: 2B — Standalone `write-spec` Skill.

**Completion gate**: `SKILL.md` exists; both context scripts run on this repo
without error; markdownlint passes; FR-004 through FR-010 satisfied.

### Implementation for User Story 1

- [x] T011 [US1] Author `templates/skills/write-spec/SKILL.md` — frontmatter:
  `name: write-spec`, discovery-rich `description` (≤ 1024 chars, includes
  keywords: draft specification, feature spec, requirements document, user
  stories, acceptance criteria), `metadata.version: "0.1.0"`; no DevSpark-only
  keys; body ≤ 500 lines; body instructs agent to: (a) run context-gathering
  scripts and parse JSON output; (b) if script output is empty, non-JSON, or
  the script exits non-zero, treat as fallback
  `{"constitution_summary": null, "prior_specs": [], "skipped_context":
  ["script-error"]}` and proceed without blocking (critic-005 — graceful
  degradation when script fails, not just when git/constitution is unavailable);
  (c) load constitution summary and prior-spec summary from parsed context;
  (d) draft spec per shared validation contract; (e) limit
  `[NEEDS CLARIFICATION]` to max 3; (f) record any skipped context in the
  spec's Assumptions section; (g) set status `Draft` (FR-004–FR-007, FR-010)
- [x] T012 [P] [US1] Author at least one `templates/skills/write-spec/references/`
  file — factor out spec template structure, clarification question format, and
  success criteria guidelines from the skill body; reference with relative paths
  from skill root (FR-007)
- [x] T013 [P] [US1] Author `templates/skills/write-spec/scripts/gather-context.ps1`
  — PowerShell: detect git repo, load constitution (emit summary), list prior
  specs under `.documentation/specs/`; always exit 0 and always emit valid JSON
  (critic-005 — the skill cannot guard against a non-zero exit if the script
  exits non-zero); output JSON schema:
  `{"constitution_summary": string|null, "prior_specs": [...], "skipped_context":
  [...]}` where `skipped_context` lists any context that could not be gathered
  (e.g., `"no-git-repo"`, `"constitution-not-found"`) and remaining fields are
  null/empty; degrade gracefully when git or constitution is unavailable;
  never block skill execution (FR-008, FR-009, FR-010)
- [x] T014 [P] [US1] Author `templates/skills/write-spec/scripts/gather-context.sh`
  — Bash equivalent of T013; functionally identical JSON output schema and
  exit-0 contract (critic-005); handles missing git, missing constitution,
  non-repo context; records skipped context in `skipped_context` array;
  always exits 0 and always emits valid JSON (FR-009, FR-010)
- [x] T015 [US1] Manually validate `SKILL.md` against `SKILL-validation-contract.md`
  (from T004): name matches directory, description within limits, `metadata.version`
  quoted, no prohibited keys, body within budget, degradation documented in
  Assumptions (SC-001, SC-007)
- [x] T016 [P] [US1] Run `npx markdownlint-cli2 "**/*.md"` — confirm zero errors
  after all 2B Markdown files are authored (§VIII, FR-018)
- [x] T017 [P] [US1] Run both context-gathering scripts against the current
  repository: `.\templates\skills\write-spec\scripts\gather-context.ps1` and
  `bash templates/skills/write-spec/scripts/gather-context.sh`; verify JSON
  output contains `constitution_summary` and `prior_specs` keys; verify
  `skipped_context` array present (SC-007)

**Checkpoint 2B / US1**: `write-spec/SKILL.md` is valid; both scripts produce
correct JSON on this repo; markdownlint clean. Proceed to 2C tests.

**Checkpoint**: Phase complete — 2026-05-19

---

## Phase 4: User Story 3 — Maintainer validates a skill before merging (P2)

**Goal**: A contributor can run a single CLI command to validate a skill against
the open spec, the DevSpark addendum, and the adapter contract. CI runs the same
validation on every PR.

**Independent Test**: Run `devspark skills validate` against a valid skill
(exits 0 + summary) and against a deliberately broken skill fixture (exits 1 +
named rule + offending value).

**Note**: US3 is implemented before US2 because the test gate (US3) must exist
before the command refactor (US2/2D). This ordering is required by the spec
(2A → 2B → 2C → 2D).

**Sub-phase**: 2C — Tests and CLI.

### Tests for User Story 3

- [x] T018 [P] [US3] Author `tests/test_skill_contract.py` — discovers all
  directories under `templates/skills/` that contain `SKILL.md`; for each:
  parse YAML frontmatter using `yaml.safe_load()` (SafeLoader — avoids YAML 1.1
  boolean surprises where bare `yes`/`no`/`on`/`off` become Python booleans,
  critic-003); assert `name` matches parent directory; assert `name` matches
  regex `^[a-z0-9]+(-[a-z0-9]+)*$` (no leading/trailing/consecutive hyphens);
  assert `description` is non-empty and `len(description) <= 1024`; assert
  `metadata.version` is of type `str` (not int/float — rejects unquoted `1.0`)
  and matches regex `^\d+\.\d+\.\d+$` (full MAJOR.MINOR.PATCH — rejects `"1.0"`
  missing patch, critic-003); assert no prohibited DevSpark-only keys
  (`handoffs`, `scripts`, `classification`, `required_gates`,
  `recommended_next_step`, `version`) present in frontmatter; assert body line
  count ≤ 500 (fail) and emit warning when > 400 lines (warn tier); assert
  SKILL.md body contains none of the DevSpark-specific strings `.devspark/`,
  `{SCRIPT}`, `FEATURE_DIR`, `{AGENT_SCRIPT}`, `handoffs:` (portability
  body-scan, critic-008 — catches DevSpark leakage before manual portability
  check T032); include a deliberate-violation fixture set: uppercase name,
  description > 1024 chars, unquoted float version, partial semver, prohibited
  key, body with DevSpark-specific string — each fixture must fail with an
  assertion message naming the violated rule (FR-011, SC-002)
- [x] T019 [P] [US3] Author `tests/test_adapter_contract.py` — asserts
  `templates/commands/specify.md` contains a reference to `write-spec` skill;
  asserts `specify.md` does not contain the inline spec-drafting procedure
  post-2D refactor (add as an xfail/skip marker for now, to be enabled in T026
  after T025 refactor completes); **note: FR-012(c) (integration-test pass
  assertion) is a stub here — it is not fully enforced until T027 runs the full
  integration suite against the refactored command; T019 alone does not satisfy
  FR-012(c)**; add cross-file grep assertions that the three named adapter input
  variables (`$FEATURE_DESCRIPTION`, `$CONSTITUTION_PATH`, `$PRIOR_SPEC_SUMMARY`)
  appear in both `specify.md`'s delegation block and `ADAPTER-contract.md`
  (critic-004 — makes the variable contract machine-verifiable) (FR-012, SC-003)

### Implementation for User Story 3

- [x] T020 [US3] Author `src/devspark_cli/commands/skills.py` — implements
  `skills_app = typer.Typer(name="skills")`; subcommand `list`: enumerate all
  directories under `templates/skills/` that contain `SKILL.md`, print Rich
  table (name, version, path, status); **no `--json` flag in this release**
  (critic-007 decision: output format is not yet stable; document in a comment
  that `--json` is deferred and the format should not be parsed by scripts
  until stabilised in a future semver release); subcommand `validate [path]`:
  validate all skills or one supplied path using `yaml.safe_load()` (SafeLoader,
  not default Loader); implement three-tier exit codes: pass → exit 0 + summary
  on stdout; warn → exit 0 + warning count on stderr; fail → exit 1 + diagnostic
  `[RULE] [OFFENDING-VALUE] message` on stderr; parse frontmatter and run all
  rules from `SKILL-validation-contract.md` (FR-013)
- [x] T021 [US3] Wire `skills_app` into `src/devspark_cli/_app.py` — add
  `app.add_typer(skills_app, name="skills")` alongside existing `harness_app`
  and `adapter_app` (FR-013)
- [x] T022 [US3] Run `pytest tests/test_skill_contract.py tests/test_adapter_contract.py`
  — confirm T018/T019 pass; confirm `devspark skills validate` exits 0 against
  current `write-spec` skill; confirm deliberate-violation fixture exits 1 with
  named rule (SC-002)
- [x] T023 [P] [US3] Run full test suite `pytest tests/` — confirm no regressions
  from CLI wiring (SC-006)

**Checkpoint 2C / US3**: Both new test modules pass; `devspark skills list` and
`devspark skills validate` are wired and functional; regression baseline held.
Proceed to 2D.

**Checkpoint**: Phase complete — 2026-05-19

---

## Phase 5: User Story 2 — DevSpark command invokes skill internally (P1)

**Goal**: Running `/devspark.specify "..."` inside a DevSpark-enabled repository
produces the same user-observable artifacts as before, but the spec-drafting
reasoning is now delegated to the `write-spec` skill via the adapter contract.

**Independent Test**: Run the existing `/devspark.specify` integration test suite
(`tests/test_create_spec_workflow_integration.py` and related) against the
refactored command. All tests must pass unchanged. Additionally,
`tests/test_adapter_contract.py` must confirm delegation.

**Sub-phase**: 2D — Thin-Wrapper Command Refactor.

### Implementation for User Story 2

- [x] T024 [US2] Read `templates/commands/specify.md` in full before editing —
  identify the inline spec-drafting procedure section (the block starting at step
  4 "Follow this execution flow" through step 5 "Write the specification")
- [x] T025 [US2] Refactor `templates/commands/specify.md` — retain all DevSpark
  lifecycle steps (route classification at step 0, branch creation at step 2,
  multi-app scoping, artifact placement at step 5, checklist generation at
  step 6, gate enforcement); replace the inline spec-drafting procedure with a
  delegation block that: (a) resolves `templates/skills/write-spec/SKILL.md`
  via the adapter contract, (b) passes `$FEATURE_DESCRIPTION`, `$CONSTITUTION_PATH`,
  and `$PRIOR_SPEC_SUMMARY` as named inputs, (c) places the skill-produced draft
  into `SPEC_FILE`; multi-app scope resolution remains a command responsibility
  and is NOT passed into the skill body (FR-014, FR-015, SC-003)
- [x] T026 [US2] Enable the previously-skipped adapter contract assertion in
  `tests/test_adapter_contract.py` (T019) that verifies `specify.md` references
  `write-spec` and does not duplicate the drafting procedure inline (FR-012)
- [x] T027 [US2] Run `pytest tests/test_create_spec_workflow_integration.py` and
  all related specify integration tests — confirm all pass unchanged after the
  refactor (FR-015, SC-003)
- [x] T028 [US2] Run `pytest tests/test_adapter_contract.py` — confirm delegation
  assertion now passes with the refactored command (FR-012)
- [x] T029 [P] [US2] Run `npx markdownlint-cli2 "**/*.md"` — confirm zero errors
  on modified `specify.md` (§VIII, FR-018)

**Checkpoint 2D / US2**: All existing integration tests pass unchanged; adapter
contract test confirms delegation; markdownlint clean.

**Checkpoint**: Phase complete — 2026-05-19

### User Story 2 ✅ Complete

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation sweep across all surfaces introduced by this feature.

- [x] T030 [P] Run full markdownlint sweep: `npx markdownlint-cli2 "**/*.md"` —
  confirm zero errors across all new and modified Markdown files (§VIII, FR-018,
  SC-004)
- [x] T031 [P] Run full test suite: `pytest tests/` — confirm all tests pass;
  zero regressions in any existing test (SC-006)
- [x] T032 Perform manual portability check: copy only
  `templates/skills/write-spec/` to a temporary directory; open with a
  skills-compatible client; request a draft spec for a sample feature description;
  verify the resulting `spec.md` has valid frontmatter, four mandatory full-spec
  sections, `Draft` status, and ≤ 3 `[NEEDS CLARIFICATION]` markers (SC-001,
  US1 acceptance scenario 1)
- [x] T033 [P] Verify `devspark skills list` output — confirm it enumerates
  `write-spec` with correct name, version `0.1.0`, path, and `pass` status
  (SC-002, FR-013)
- [x] T034 [P] Verify `devspark skills validate` exit code — zero for `write-spec`;
  non-zero with named rule for deliberate-violation fixture (SC-002, US3
  acceptance scenario 2)
- [x] T035 Review `CLAUDE.md` and `README.md` FR-019 updates — confirm positioning
  statement, dual-surface model description, and all four pointers are present
  and links resolve (FR-019)

**Checkpoint**: Phase complete — 2026-05-19

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately.
- **Phase 2 (2A Foundation)**: Depends on Phase 1 — blocks all subsequent phases.
- **Phase 3 (2B / US1)**: Depends on Phase 2 completion — contract files must be
  stable before skill is authored.
- **Phase 4 (2C / US3)**: Depends on Phase 3 completion — skill must exist before
  tests assert on it.
- **Phase 5 (2D / US2)**: Depends on Phase 4 completion — test gate must exist
  before command is refactored.
- **Phase 6 (Polish)**: Depends on Phase 5 completion.

### User Story Dependencies

- **US1 (P1 — Portable skill)**: Depends on 2A foundation only. No dependency on
  US2 or US3.
- **US3 (P2 — Validation)**: Depends on US1 (skill must exist to be validated).
  Implemented before US2 to establish the test gate.
- **US2 (P1 — Command integration)**: Depends on US3 (test gate must exist before
  refactor). Final delivery sub-phase.

### Within Each Phase

- Markdown files in Phase 2: T004 and T005 can be authored in parallel (different
  files); T006 depends on T004/T005 being stable; T007 depends on T006; T008/T009
  can be parallel with T007; T010 runs after all Phase 2 files are authored.
- Scripts in Phase 3: T013 and T014 can be authored in parallel (different files,
  same output schema); both depend on T011 for output schema reference.

### Parallel Opportunities

Within Phase 2 (once started):

- T004 and T005 are parallelizable (different files)
- T008 and T009 are parallelizable (different files)
- T010 is a gate — runs after T004–T009

Within Phase 3 (once T011 is complete):

- T012, T013, T014 are parallelizable (different files)
- T016 and T017 run after T011–T014

Within Phase 4 (once T011 and T004/T005 are complete):

- T018 and T019 can be authored in parallel (different files)
- T020 and T021 are sequential (T021 imports from T020)
- T022 and T023 run after T020/T021

---

## Parallel Example: Phase 3 (User Story 1)

```text
# After T011 (SKILL.md) is complete, launch in parallel:
Task T012: Author write-spec/references/ files
Task T013: Author gather-context.ps1
Task T014: Author gather-context.sh

# After all three complete:
Task T015: Manual validation against SKILL-validation-contract.md
Task T016: markdownlint sweep
Task T017: Run both scripts against current repo
```

---

## Gate Acknowledgements

- **Gate**: checklists/requirements.md
- **Concern**: One item marked incomplete — "No [NEEDS CLARIFICATION] markers
  remain" — was flagged based on an earlier pre-clarifications-session state of
  the spec. After review, no actual `[NEEDS CLARIFICATION]` markers remain in
  `spec.md`; the two occurrences found by grep are content references (acceptance
  scenario wording and FR-006 rule text), not open markers. FR-020 distribution
  surface was resolved via the Clarifications session 2026-05-19 (in-repo
  distribution only). The checklist item is stale.
- **Decision**: Proceed — the underlying concern is resolved; the checklist item
  will be updated as part of T035.
- **Recorded By**: /devspark.tasks
- **Date**: 2026-05-19

---

## Implementation Strategy

### MVP First (User Story 1 — Portable Skill)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: 2A Foundation (T004–T010) — **blocks all stories**
3. Complete Phase 3: US1 / 2B Skill (T011–T017)
4. **STOP and VALIDATE**: Manual portability check (T032 preview)
5. Portable skill is usable by any skills-compatible client

### Incremental Delivery

1. Phase 1 + Phase 2 → Contract foundation ready
2. Phase 3 (US1) → Portable `write-spec` skill ships
3. Phase 4 (US3) → Validation CLI + test gate ships
4. Phase 5 (US2) → Command refactor ships; full dual-surface model live
5. Phase 6 (Polish) → Final sweep and portability confirmation

### Single-Developer Sequence

Because the sub-phase ordering is non-negotiable (2A → 2B → 2C → 2D), this
feature is designed as a sequential delivery by one developer, with parallel
opportunities within each phase where marked [P].

---

## Notes

- [P] tasks = different files, no shared state dependencies — safe to run in
  parallel within the same phase
- [US*] label maps each task to a specific user story for traceability
- Sub-phase ordering (2A → 2B → 2C → 2D) is non-negotiable per the spec
- §VIII (Markdown Quality): run markdownlint after every authoring phase, not
  only at the end — T010, T016, T029, T030
- §VI (Platform Parity): T013 and T014 must be functionally equivalent; verify
  JSON output schema matches between PS and Bash scripts
- Tests required by spec: T018, T019, T022, T023, T027, T028 are not optional
- Commit after each phase checkpoint to keep diffs auditable (§VII)
- Avoid: editing `SKILL.md` and `specify.md` in the same commit (reviewer
  clarity); cross-phase work before phase gate is passed
