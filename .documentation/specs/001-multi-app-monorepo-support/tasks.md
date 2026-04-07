# Tasks: Multi-Application Monorepo Support

**Input**: Design documents from `/.documentation/specs/001-multi-app-monorepo-support/`
**Prerequisites**: plan.md (required), spec.md (required)

## Rationale Summary

### Core Problem

DevSpark assumes a single application boundary per repository. That breaks for monorepos with multiple
applications that have different platforms, risk profiles, and governance needs.

### Decision Summary

Add an authoritative repository registry with optional app-local manifests (`app.json`), app-aware
resolution for constitutions/prompts/scripts/templates, declared + inferred dependency reporting, and
three v1 commands (add, list, validate-registry) — all opt-in and backward compatible.
*(Updated 2026-04-07: reflects leadership decisions Q1-Q5.)*

### Key Drivers

- Monorepo adoption is common; DevSpark must model heterogeneous apps without fragmenting installations
- Governance must remain centralized with additive per-app overlays
- Explicit scope selection avoids hidden inference and review mistakes

### Reviewer Guidance

Focus on task ordering, v1a/v1b boundary adherence, Bash/PowerShell parity coverage, and whether each
user story can be independently tested after its phase completes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Design approval, project structure, and foundational fixtures

- [x] T001 Obtain leadership approval on design contract (authority model, resolution order, v1a/v1b split, profile composition, app-local manifests, dependency inference, CLI scope, shared paths, scaffolding) per Phase 0 of plan.md *(Completed 2026-04-07: all 5 open questions resolved)*
- [x] T002 Create feature branch `001-monorepo-implement`
- [x] T003 [P] Create fixture directory `tests/fixtures/fixture-single-app/` with current single-app repo structure (no registry)
- [x] T004 [P] Create fixture directory `tests/fixtures/fixture-two-api/` with 2 runtime API apps and a minimal `devspark.json`
- [x] T005 [P] Create fixture directory `tests/fixtures/fixture-full-monorepo/` with 6 apps + 1 library matching the registry example in plan.md
- [x] T005a [P] Create fixture directory `tests/fixtures/fixture-20-app/` with 20 registered apps for performance validation (see C2)
- [x] T005b Add `pydantic>=2.0` dependency to `pyproject.toml` under project dependencies (see C1)

---

## Phase 2: Foundational — Registry and Resolution Primitives (v1a, WS1)

**Purpose**: Core configuration model that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create `src/devspark_cli/registry.py` and define Pydantic v2 model for `devspark.json` registry schema (profiles, apps, validation rules)
- [x] T007 Implement field validators: unique ids, path existence, profile reference resolution, dependency cycle detection in `src/devspark_cli/registry.py`
- [x] T008 Implement registry loading function that reads `.documentation/devspark.json` and returns validated model in `src/devspark_cli/registry.py`
- [ ] T009 [P] Add jq-based registry validation helpers (field presence, type checks, unique ids) in `scripts/bash/common.sh`
- [ ] T010 [P] Add ConvertFrom-Json registry validation helpers (field presence, type checks, unique ids) in `scripts/powershell/common.ps1`
- [x] T011 Implement mode detection: if `devspark.json` exists with `"mode": "multi-app"` → multi-app mode; otherwise → single-app mode in `src/devspark_cli/registry.py`
- [x] T012 Create `src/devspark_cli/scope.py` and define standard scope object structure (scope type, primary app, affected apps, impacted downstream)
- [x] T013 Implement repo-scope vs app-scope documentation root resolution: repo uses `.documentation/`, app uses `{app.path}/.documentation/` in `src/devspark_cli/scope.py`
- [ ] T014 [P] Add app-aware helper functions to `scripts/bash/platform.sh` (detect mode, resolve app doc root, resolve scope)
- [ ] T015 [P] Add app-aware helper functions to `scripts/powershell/platform.ps1` (detect mode, resolve app doc root, resolve scope)
- [x] T015a Define Pydantic v2 model for app-local manifest (`{app.path}/app.json`) in `src/devspark_cli/registry.py`: schema allows only `tags`, `hints`, `rules`; identity fields ignored with validation warning *(Added 2026-04-07: FR-B8)*
- [x] T015b Implement app.json loading and merge into resolution chain in `src/devspark_cli/registry.py`: load after profile composition, merge tags (last-writer-wins), rules (additive), hints (last-writer-wins) *(Added 2026-04-07: FR-B8)*
- [ ] T015c Add app.json weakening detection: check app.json rules against mandatory repo-wide rules using same keyword-based detection as constitution overlays in `src/devspark_cli/registry.py` *(Added 2026-04-07: FR-B8)*
- [x] T015d [P] Add app.json fixtures to `tests/fixtures/fixture-full-monorepo/`: valid app.json for 2+ apps, one with identity fields (for warning test), one with weakening rule (for conflict test) *(Added 2026-04-07)*

**Checkpoint**: Registry loads, validates (including app.json), and the resolution primitives are operational

---

## Phase 3: User Story 1 — Govern a heterogeneous multi-app repository (Priority: P1) — MVP

**Goal**: DevSpark resolves different app-specific constitution overlays and prompt/script/template overrides while preserving repo-wide governance

**Independent Test**: Configure fixture-full-monorepo with app-specific constitutions for `runtime-api-a` and `admin-web`, run equivalent workflows for both, confirm distinct governance resolution

### Implementation for User Story 1

- [x] T016 [US1] Create `src/devspark_cli/resolution.py` and implement constitution resolution chain: load repo constitution from `.documentation/memory/constitution.md`, then app overlay from `{app.path}/.documentation/memory/constitution.md`
- [x] T017 [US1] Implement keyword-based weakening detection for the **constitution layer only**: emit CONFLICT warnings when an app constitution overlay weakens mandatory repo rules in `src/devspark_cli/resolution.py`
- [x] T018 [US1] Implement prompt resolution chain (app team → repo user → repo team → stock default) in `src/devspark_cli/resolution.py`
- [x] T019 [US1] Implement script resolution chain (app team → repo team → stock default) in `src/devspark_cli/resolution.py`
- [x] T020 [US1] Implement template resolution chain (app team → repo team → stock default) in `src/devspark_cli/resolution.py`
- [x] T021 [US1] Implement **base** profile composition: merge inherited profile tags/rules/hints in declaration order to produce the effective profile for a single app in `src/devspark_cli/resolution.py`. Note: T050 (US5) extends this with multi-profile validation, conflict detection, and cross-app audit.
- [ ] T022 [P] [US1] Add constitution resolution helpers (load repo + app overlay, compose) in `scripts/bash/common.sh`
- [ ] T023 [P] [US1] Add constitution resolution helpers (load repo + app overlay, compose) in `scripts/powershell/common.ps1`
- [x] T024 [US1] Add app-specific constitution fixtures to `tests/fixtures/fixture-full-monorepo/apps/runtime-api-a/.documentation/memory/constitution.md` and `apps/admin-web/.documentation/memory/constitution.md`
- [x] T025 [US1] Validate fixture R3 *constitution resolution* (plan --app runtime-api-a resolves runtime-api-a constitution) and R4 *constitution resolution* (plan --app admin-web resolves admin-web constitution) from Validation Matrix

**Checkpoint**: App-specific governance resolves correctly without cross-contamination

---

## Phase 4: User Story 2 — Execute app-scoped workflows with explicit context (Priority: P1)

**Goal**: Commands target a specific app; artifacts land in the correct app scope; resolution uses the correct chain

**Independent Test**: Run a feature workflow with explicit app context for `admin-api`, verify artifacts are created under `apps/admin-api/.documentation/specs/` and resolution uses the admin-api chain

### Implementation for User Story 2

- [ ] T026 [US2] Add `--app` parameter and `--repo-scope` flag to app-aware script entry points in `scripts/bash/common.sh`
- [ ] T027 [US2] Add `--app` parameter and `--repo-scope` flag to app-aware script entry points in `scripts/powershell/common.ps1`
- [ ] T028 [US2] Implement app context propagation: when `--app` is passed, set scope to that app and route all artifact writes to `{app.path}/.documentation/` in `scripts/bash/common.sh`
- [ ] T029 [US2] Implement app context propagation: when `--app` is passed, set scope to that app and route all artifact writes to `{app.path}/.documentation/` in `scripts/powershell/common.ps1`
- [ ] T030 [US2] When no `--app` and no `--repo-scope` and multiple apps registered: emit error "Multiple apps registered; specify --app or use --repo-scope" in `scripts/bash/common.sh` and `scripts/powershell/common.ps1`
- [ ] T031 [US2] Update `scripts/bash/create-new-feature.sh` to accept app context and create feature dirs under app scope
- [ ] T032 [P] [US2] Update `scripts/powershell/create-new-feature.ps1` to accept app context and create feature dirs under app scope
- [ ] T033 [US2] Update `scripts/bash/setup-plan.sh` to resolve plan artifacts from app-scoped documentation root
- [ ] T034 [P] [US2] Update `scripts/powershell/setup-plan.ps1` to resolve plan artifacts from app-scoped documentation root
- [ ] T035 [US2] Add scope summary output to every workflow execution (print resolved scope, primary app, doc root)
- [ ] T036 [US2] Validate fixture R3 *artifact path* (app-scoped artifacts land at `apps/runtime-api-a/.documentation/specs/`), R5 (no-app error), R6 (repo-scope works) from Validation Matrix

**Checkpoint**: App-scoped workflows execute end-to-end with explicit context and correct artifact placement

---

## Phase 5: User Story 3 — Review cross-application changes safely (Priority: P1)

**Goal**: DevSpark identifies impacted downstream applications for shared changes and scopes reviews correctly

**Independent Test**: Define dependency graph where `admin-web` depends on `admin-api`; run a shared auth change workflow; verify impacted apps are listed in scope report

### Implementation for User Story 3

- [x] T037 [US3] Build inverse dependency lookup from `dependsOn` declarations (which point upstream from consumer → provider) to identify direct downstream consumers of a changed app in `src/devspark_cli/scope.py`
- [x] T037a [US3] Create `src/devspark_cli/inference.py` and implement basic dependency inference: scan source imports (`*.py`, `*.ts`, `*.js`, `*.cs`, `*.java`) and build config files (`package.json`, `pyproject.toml`, `*.csproj`) for references to other registered app paths *(Added 2026-04-07: FR-D8)*
- [x] T037b [US3] Integrate inferred dependencies into scope reporting: report inferred deps separately from declared deps, deduplicate matches, respect `.gitignore` patterns *(Added 2026-04-07: FR-D8)*
- [x] T037c [P] [US3] Add inference test fixtures to `tests/fixtures/fixture-full-monorepo/`: source files with cross-app imports and build configs with project references *(Added 2026-04-07)*
- [ ] T038 [US3] Implement scope report generation: declared scope, detected scope, mismatches, declared downstream impact list, inferred downstream impact list in `src/devspark_cli/scope.py` *(Updated 2026-04-07: includes inferred deps)*
- [ ] T039 [P] [US3] Add dependency reporting helpers to `scripts/bash/common.sh` (read dependsOn, walk direct downstream)
- [ ] T040 [P] [US3] Add dependency reporting helpers to `scripts/powershell/common.ps1` (read dependsOn, walk direct downstream)
- [ ] T041 [US3] Update `scripts/bash/get-pr-context.sh` to include dependency scope report in PR context output
- [ ] T042 [P] [US3] Update `scripts/powershell/get-pr-context.ps1` to include dependency scope report in PR context output
- [ ] T043 [US3] Update `templates/commands/pr-review.md` to consume scope report and apply governance per declared scope
- [ ] T044 [US3] Validate fixture D1 (shared-auth change lists admin-api, client-web as declared impacted), D2 (admin-web-only change shows no downstream), D3 (undeclared import shows as inferred dependency), and D4 (declared dep in imports is deduplicated) from Validation Matrix *(Updated 2026-04-07: D3/D4 added for inference)*

**Checkpoint**: Cross-app impact is reported with declared and inferred dependencies; single-app changes stay scoped locally

---

## Phase 6: User Story 4 — Keep single-application repositories unchanged (Priority: P2)

**Goal**: Existing single-app repos work without any changes to structure or behavior

**Independent Test**: Run existing DevSpark workflows in fixture-single-app with no registry; confirm identical behavior to pre-feature baseline

### Implementation for User Story 4

- [ ] T045 [US4] Ensure mode detection defaults to single-app when `devspark.json` is absent in `src/devspark_cli/registry.py`
- [ ] T046 [US4] Ensure all updated Bash scripts in `scripts/bash/` fall through to current behavior when no registry is detected
- [ ] T047 [P] [US4] Ensure all updated PowerShell scripts in `scripts/powershell/` fall through to current behavior when no registry is detected
- [ ] T048 [US4] Validate fixture R1 (plan in single-app produces repo-scope artifacts at `.documentation/specs/`) and R2 (--app flag errors without registry) from Validation Matrix
- [ ] T049 [US4] Run full single-app regression suite against fixture-single-app

**Checkpoint**: Zero behavioral changes for single-app repositories

---

## Phase 7: User Story 5 — Limit customization drift through profile-based inheritance (Priority: P2)

**Goal**: Apps share rules through profile inheritance; only app-specific deltas need to be declared

**Independent Test**: Configure runtime-api-a, admin-api, admin-web, and qa-harness with profile inheritance; verify resolved rules match expected composition without duplicating base prompts

### Implementation for User Story 5

- [ ] T050 [US5] Extend profile composition (built in T021) with **multi-profile validation and cross-app audit**: verify that all apps using shared profiles resolve consistent effective rules, and validate no profile creates conflicting requirements across apps in `src/devspark_cli/resolution.py`
- [ ] T051 [US5] Implement **profile-layer** override conflict detection: flag when an app's profile overrides attempt to weaken repo-wide mandatory rules inherited through profile `rules` fields in `src/devspark_cli/resolution.py`. Note: T017 handles constitution-layer weakening; this task handles profile-layer weakening.
- [ ] T052 [P] [US5] Add profile resolution helpers to `scripts/bash/common.sh` (resolve inherits chain, merge tags/rules/hints)
- [ ] T053 [P] [US5] Add profile resolution helpers to `scripts/powershell/common.ps1` (resolve inherits chain, merge tags/rules/hints)
- [ ] T054 [US5] Add profile fixtures to `tests/fixtures/fixture-full-monorepo/` validating correct composition for api-profile, web-profile, admin-profile, qa-profile
- [ ] T055 [US5] Validate that all 6 apps + 1 library in fixture-full-monorepo resolve expected effective profiles without duplicated base content

**Checkpoint**: Profile inheritance works; no full-duplication needed per app

---

## Phase 8: User Story 6 — Add a new application to the registry (Priority: P2, v1b)

**Goal**: A guided command registers a new app in the authoritative registry with validation

**Independent Test**: Run `/devspark.add-application` with valid metadata for `payments-api`; verify registry is updated; run `/devspark.list-applications` to confirm the new entry

### Implementation for User Story 6

- [ ] T056 [US6] Create `templates/commands/add-application.md` prompt template with guided metadata collection (id, name, path, kind, purpose, owner, criticality, profiles, dependencies)
- [ ] T057 [US6] Create `src/devspark_cli/commands.py` and implement add-application logic: validate inputs, check duplicate ids, validate path/profile/dependency references, update `.documentation/devspark.json`, always scaffold `{app.path}/.documentation/` with standard subdirectories *(Updated 2026-04-07: always scaffold, no --scaffold flag)*
- [ ] T058 [US6] Create `templates/commands/list-applications.md` prompt template that reads registry and displays human-readable table
- [ ] T059 [US6] Implement list-applications logic: load registry, format table (id, path, kind, owner, criticality, dependencies, doc root) in `src/devspark_cli/commands.py`
- [ ] T059a [US6] Create `templates/commands/validate-registry.md` prompt template for standalone registry validation *(Added 2026-04-07: FR-B9)*
- [ ] T059b [US6] Implement validate-registry logic in `src/devspark_cli/commands.py`: load registry, run all validators (schema, uniqueness, paths, profiles, dependencies, cycles, app.json consistency), produce structured pass/fail output *(Added 2026-04-07: FR-B9)*
- [ ] T060 [US6] Validate fixture C1 (valid new app + scaffold), C2 (duplicate id error), C3 (list shows all apps), C4 (list with no registry), C5 (validate-registry passes valid registry), C6 (validate-registry fails invalid registry), C7 (validate-registry warns on app.json identity fields) from Validation Matrix *(Updated 2026-04-07: renumbered, added validate-registry scenarios)*

**Checkpoint**: Add/list/validate commands work; registry stays valid after mutations

---

## Phase 9: PR Scope Validation (v1b, extends US3)

**Purpose**: Enforce declared PR scope against actual changed files

- [ ] T062 Implement PR scope declaration model: `single-app`, `cross-app`, `repo-scope` in `src/devspark_cli/scope.py`
- [ ] T063 Implement changed-path analysis: compare declared scope with actual changed file paths in `src/devspark_cli/scope.py`
- [ ] T064 Define approved shared paths list (e.g., `.github/`, root config files) that don't trigger scope mismatch for single-app PRs
- [ ] T065 Implement scope mismatch detection: single-app PR touching a second registered app path triggers warning in `src/devspark_cli/scope.py`
- [ ] T066 Update `scripts/bash/get-pr-context.sh` to include PR scope validation output
- [ ] T067 [P] Update `scripts/powershell/get-pr-context.ps1` to include PR scope validation output
- [ ] T068 Update `templates/commands/pr-review.md` to consume PR scope validation and enforce three-mode review behavior. Note: this extends the scope report consumption added in T043 (v1a) — do not overwrite those changes.
- [ ] T069 Validate fixtures P1–P5 from PR Scope Validation Matrix

**Checkpoint**: PR scope enforcement catches undeclared cross-app impact

---

## Phase 10: Prompt and Command Template Updates (v1a + v1b, WS2)

**Purpose**: Update all prompt templates to support app-aware paths and scope reporting

- [ ] T070 [P] Update `templates/commands/specify.md` to include app context parameter, scope-aware artifact paths, and Rationale Summary population
- [ ] T071 [P] Update `templates/commands/plan.md` to include app context parameter, scope-aware artifact paths, and rationale carry-forward
- [ ] T072 [P] Update `templates/commands/tasks.md` to include app context parameter, scope-aware artifact paths, and rationale carry-forward
- [ ] T073 [P] Update `templates/commands/implement.md` to include app context parameter and scope-aware artifact resolution
- [ ] T074 [P] Update `templates/commands/quickfix.md` to include app context parameter and scope-aware paths
- [ ] T075 [P] Update `templates/commands/site-audit.md` to include app context parameter
- [ ] T076 [P] Update `templates/commands/release.md` to include app context parameter
- [ ] T077 [P] Update `templates/commands/harvest.md` to include app context parameter
- [ ] T078 [P] Update `templates/commands/critic.md` to add Rationale & Traceability Risks category and rationale red flags checklist

---

## Phase 11: Rationale Capture Pattern (v1a, WS5)

**Purpose**: Surface decision context in every generated artifact

- [ ] T079 [P] Add Rationale Summary block to `templates/spec-template.md` after header metadata, before User Scenarios
- [ ] T080 [P] Add Rationale Summary block to `templates/plan-template.md` after header metadata, before Summary
- [ ] T081 [P] Add Rationale Summary block (Core Problem, Decision Summary, Key Drivers, Reviewer Guidance) to `templates/tasks-template.md` after header metadata, before Format section
- [ ] T082 Create `templates/rationale-template.md` with canonical Rationale Summary block

**Checkpoint**: All templates include rationale; commands reference and populate the block

---

## Phase 12: Remaining Script Updates (v1a + v1b, WS2)

**Purpose**: Update all context-gathering scripts for app-aware execution with Bash/PowerShell parity

- [ ] T083 [P] Update `scripts/bash/quickfix-context.sh` to accept and propagate app context
- [ ] T084 [P] Update `scripts/powershell/quickfix-context.ps1` to accept and propagate app context
- [ ] T085 [P] Update `scripts/bash/release-context.sh` to accept and propagate app context
- [ ] T086 [P] Update `scripts/powershell/release-context.ps1` to accept and propagate app context
- [ ] T087 [P] Update `scripts/bash/repo-story-context.sh` to accept and propagate app context
- [ ] T088 [P] Update `scripts/powershell/repo-story-context.ps1` to accept and propagate app context
- [ ] T089 [P] Update `scripts/bash/site-audit.sh` to accept and propagate app context
- [ ] T090 [P] Update `scripts/powershell/site-audit.ps1` to accept and propagate app context
- [ ] T091 [P] Update `scripts/bash/evolution-context.sh` to accept and propagate app context
- [ ] T092 [P] Update `scripts/powershell/evolution-context.ps1` to accept and propagate app context
- [ ] T093 [P] Update `scripts/bash/harvest.sh` to accept and propagate app context
- [ ] T094 [P] Update `scripts/powershell/harvest.ps1` to accept and propagate app context
- [ ] T095a [P] Update `scripts/bash/archive-context.sh` to accept and propagate app context (scans `.documentation/` — needs app-scope awareness)
- [ ] T095b [P] Update `scripts/powershell/archive-context.ps1` to accept and propagate app context
- [ ] T095c [P] Update `scripts/bash/update-agent-context.sh` to accept and propagate app context (reads plan.md — needs app-scope path resolution)
- [ ] T095d [P] Update `scripts/powershell/update-agent-context.ps1` to accept and propagate app context
- [ ] T095e [P] Update `scripts/bash/check-prerequisites.sh` to detect multi-app mode and resolve app-scoped FEATURE_DIR when `--app` is passed
- [ ] T095f [P] Update `scripts/powershell/check-prerequisites.ps1` to detect multi-app mode and resolve app-scoped FEATURE_DIR when `--app` is passed

> **Note (C3)**: `scripts/bash/migrate-to-documentation.sh` / `.ps1` is a one-time migration utility for the old→new structure. It does not need app-context propagation.

**Checkpoint**: All scripts propagate app context with Bash/PowerShell parity

---

## Phase 13: Packaging, Quickstarts, and CLI (v1b, WS3)

**Purpose**: Update install/upgrade surfaces and documentation

- [ ] T095g Update `.github/workflows/scripts/create-release-packages.sh` to include multi-app templates and commands (including `validate-registry.md`) in release artifacts *(ID changed from T095 to T095g to avoid collision with Phase 12 T095a-T095f)*
- [ ] T096 [P] Update `quickstart/devspark_quickstart_copilot.md` with multi-app setup guidance
- [ ] T097 [P] Update `quickstart/devspark_quickstart_claudecode.md` with multi-app setup guidance
- [ ] T098 [P] Update `quickstart/devspark_quickstart_cursor.md` with multi-app setup guidance
- [ ] T099 [P] Update `quickstart/devspark_quickstart_generic.md` with multi-app setup guidance
- [ ] T100 Update `src/devspark_cli/__init__.py` with CLI support for initializing or upgrading repos with multi-app mode
- [ ] T101 Update `README.md` with multi-app overview section
- [ ] T102 Update `templates/README.md` to document new `add-application.md`, `list-applications.md`, and `validate-registry.md` commands *(Updated 2026-04-07)*
- [ ] T103 Verify install/upgrade never touches `.documentation/` content (regression test)

**Checkpoint**: Release artifacts, quickstarts, and CLI support multi-app mode

---

## Phase 14: Validation and Hardening (v1a + v1b, WS4)

**Purpose**: Full validation matrix execution and parity checks

- [ ] T104 Validate all Registry Validation scenarios V1–V9 (duplicate id, invalid path, unknown profile, cycle, missing constitution, valid, app.json identity warning, app.json weakening, app.json valid) *(Updated 2026-04-07: V7-V9 added for app.json)*
- [ ] T105 Validate all Resolution scenarios R1–R6 from Validation Matrix
- [ ] T106 Validate all Dependency scenarios D1–D4 from Validation Matrix *(Updated 2026-04-07: D3-D4 added for inference)*
- [ ] T107 Validate all PR Scope scenarios P1–P5 from Validation Matrix (v1b)
- [ ] T108 Validate all Command scenarios C1–C7 from Validation Matrix (v1b) *(Updated 2026-04-07: C5-C7 added for validate-registry)*
- [ ] T109 Run Bash/PowerShell parity validation for all modified script pairs (JSON output comparison)
- [ ] T110 Run single-app regression suite: confirm zero behavioral changes for repos without `devspark.json`
- [ ] T111 Run install/upgrade regression: confirm `.documentation/` is never mutated by framework operations
- [ ] T112 Refine error messages and add migration guidance for common failure scenarios

**Checkpoint**: All validation matrix rows pass; single-app regression clean; parity validated

---

## Phase 15: Polish and Cross-Cutting Concerns

**Purpose**: Final cleanup, documentation, and release readiness

- [ ] T113 Review all updated scripts for consistent error handling and user-facing messaging
- [ ] T114 Verify performance targets: resolution and validation under 500ms for fixture-full-monorepo (6 apps) AND fixture-20-app (20 apps); less than 100ms added latency per command (see C2)
- [ ] T115 Update CHANGELOG.md with multi-app monorepo support entry
- [ ] T116 Final review: confirm v1a exit gates (all fixture tests pass, single-app regression clean, leadership approves)
- [ ] T117 Final review: confirm v1b exit gates (PR scope validation, add/list commands, packaging, quickstarts updated)

---

## Dependencies and Execution Order

```text
Phase 1 (Setup)
  └─► Phase 2 (Foundational: Registry + Resolution)
        ├─► Phase 3 (US1: Governance) ─────────► Phase 6 (US4: Backward compat)
        ├─► Phase 4 (US2: App-scoped workflows) ──┐
        ├─► Phase 5 (US3: Cross-app review) ──────┤
        │     └─► Phase 9 (PR Scope, v1b) ────────┤
        └─► Phase 7 (US5: Profile inheritance) ────┤
              └─► Phase 8 (US6: Add/list, v1b) ────┤
                                                    ├─► Phase 10 (Command templates)
                                                    ├─► Phase 11 (Rationale, v1a)
                                                    ├─► Phase 12 (Remaining scripts)
                                                    ├─► Phase 13 (Packaging, v1b)
                                                    └─► Phase 14 (Validation)
                                                          └─► Phase 15 (Polish)
```

### v1a Boundary

Phases 1–7, 10–12 (partial), 14 (partial) — Registry, resolution, governance, app-scoped workflows,
cross-app reporting, profile inheritance, command/template updates, rationale capture, hardening.

### v1b Boundary (requires v1a merged)

Phases 8, 9, 13, remaining portions of 10, 12, 14 — PR scope enforcement, add/list commands,
packaging, quickstarts, CLI, full validation matrix.

## Parallel Execution Opportunities

| Parallel Group | Tasks | Reason |
|---------------|-------|--------|
| Fixtures | T003, T004, T005 | Independent directories |
| Bash/PS registry validation | T009, T010 | Different languages, same logic |
| Bash/PS platform helpers | T014, T015 | Different languages, same logic |
| Constitution Bash/PS | T022, T023 | Different languages, same logic |
| App context Bash/PS | T026+T028 ∥ T027+T029 | Different languages, same logic |
| Feature creation Bash/PS | T031, T032 | Different languages, same logic |
| Dependency helpers Bash/PS | T039, T040 | Different languages, same logic |
| Profile helpers Bash/PS | T052, T053 | Different languages, same logic |
| Command templates | T070–T078 | Independent files |
| Rationale templates | T079–T082 | Independent files |
| Remaining scripts | T083–T094, T095a–T095f (paired) | Independent script files |
| Quickstarts | T096–T099 | Independent files |

## Implementation Strategy

**MVP Scope**: Phases 1–3 (Setup + Foundational + US1) — delivers the registry, resolution primitives,
and governance resolution. This proves the core model works before expanding to workflow propagation.

**Incremental Delivery**:

1. MVP: Registry + governance resolution (Phases 1–3)
2. App-scoped workflows (Phase 4)
3. Cross-app safety (Phase 5)
4. Backward compatibility validation (Phase 6)
5. Profile inheritance (Phase 7)
6. v1b: PR scope, commands, packaging (Phases 8–9, 13)
7. Full template/script updates and hardening (Phases 10–12, 14–15)

## Summary *(Updated 2026-04-07: counts reflect leadership decision additions)*

| Metric | Value |
|--------|-------|
| Total tasks | ~140 |
| Phase count | 15 |
| User stories covered | 6 (US1–US6) |
| Workstreams covered | 5 (WS1–WS5) |
| v1a tasks | ~95 |
| v1b tasks | ~45 |
| Parallel opportunities | 12 groups |
| MVP scope | Phases 1–3 (T001–T025, T015a–T015d) |
| New tasks added 2026-04-07 | T015a–T015d (app.json), T037a–T037c (inference), T059a–T059b (validate-registry), T095g (renumber) |
