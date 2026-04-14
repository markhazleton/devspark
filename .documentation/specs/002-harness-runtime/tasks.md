# Tasks: DevSpark Harness Runtime

**Input**: Design documents from `.documentation/specs/002-harness-runtime/`
**Branch**: `002-harness-runtime`
**Prerequisites**: plan.md ✓, spec.md ✓, data-model.md ✓, contracts/ ✓, research.md ✓

**Contract tests**: Included — existing repo pattern; each phase ships its own standalone contract test script.

**Organization**: Tasks grouped by user story so each story is independently implementable and testable.

---

## Rationale Summary

### Core Problem

DevSpark orchestrates AI-assisted development through manually invoked prompts and slash commands with no mechanism to define repeatable multi-step workflows, validate each step automatically, retry on failure, or produce a traceable audit record.

### Decision Summary

Add an additive `devspark harness` subcommand group and supporting runtime modules. Users author declarative YAML specs; the harness executes steps, validates results, retries with injected feedback, and persists structured run artifacts to `.documentation/devspark/runs/`. Zero existing CLI behavior is changed.

### Key Drivers

- Repeatability: single command executes full specify→plan→implement→validate cycle
- Observability: `events.jsonl` and `result.json` are inspectable after the fact
- CI integration: noop and `--dry-run` support authoring and testing contexts without an AI tool installed

### Reviewer Guidance

Verify: (1) no existing command behavior changes; (2) run artifacts land exclusively in `.documentation/devspark/runs/`; (3) noop adapter succeeds without network or AI access; (4) `--dry-run` exits cleanly on any valid spec; (5) FR-027 version enforcement rejects unsupported `apiVersion` values.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US6)
- Exact file paths are included in every task description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the package skeleton and test infrastructure. No logic yet — just structure.

- [ ] T001 Create `src/devspark_cli/harness/__init__.py` and `src/devspark_cli/harness/adapters/__init__.py` (empty sub-package stubs)
- [ ] T002 Add `PyYAML` to project dependencies in `pyproject.toml` (or `requirements.txt`) — new runtime dependency per plan.md
- [ ] T003 [P] Create `tests/fixtures/harness/` directory with three empty placeholder files: `valid_minimal.yaml`, `valid_all_steps.yaml`, `invalid_missing_field.yaml`

---

## Phase 2: Foundational (Domain Models — blocks all user stories)

**Purpose**: All Pydantic models and the YAML loader. No CLI, no runner — just the data layer that every subsequent phase depends on.

**⚠️ CRITICAL**: All user story phases depend on this phase being complete.

- [ ] T004 Implement all Pydantic domain models in `src/devspark_cli/harness/spec_models.py`: `HarnessSpec` (apiVersion, kind, name, scope, defaults, steps, telemetry), `ScopeDeclaration`, `StepDefaults`, `TelemetryConfig`, `StepSpec` (id, name, type, mode, adapter, prompt_file, inputs, outputs, validation, retry, on_success, on_failure) for the v1 step surface (`agent_task`, `validation`, `human_gate` only), `ValidationRule` (7 rule types), `RetryPolicy` (maxAttempts, backoff, retryOn, requireHumanAfter, repairPrompt), `Run`, `RunContext`, `StepResult`, `ValidationFinding`, `ArtifactDelta`, `RunMetrics`, `TelemetryEvent` — all per data-model.md
- [ ] T005 [P] Implement `src/devspark_cli/harness/spec_loader.py`: `safe_load` YAML / fallback JSON, normalize relative paths against repo_root, enforce `apiVersion == "devspark.ai/v1"` (FR-027), validate required fields, return `HarnessSpec` — errors include field name and corrective suggestion (FR-009)
- [ ] T006 [P] Populate the three fixture files in `tests/fixtures/harness/`: `valid_minimal.yaml` (minimal spec with one step), `valid_all_steps.yaml` (one step per supported type: agent_task, validation, human_gate; includes all rule types, including `command.exit_code`), `invalid_missing_field.yaml` (spec missing `steps` — triggers FR-009 error)
- [ ] T007 Implement `tests/test_harness_spec_contract.py`: contract tests — valid fixtures parse without error; invalid fixture fails with the missing field name in the error message; `apiVersion` mismatch is rejected; `harness.schema.json` is valid JSON Schema draft 2020-12 (depends on T004, T005, T006, T008)
- [ ] T008 [P] Generate `.devspark/schemas/harness.schema.json` by calling `HarnessSpec.model_json_schema()` and writing the output — create `.devspark/schemas/` directory if absent (depends on T004)
- [ ] T009 [P] Create `sample.harness.yaml` at repository root demonstrating all supported step types, all validation rule types, retry policy, scope declaration, and telemetry config — per contracts/harness-spec-yaml.md annotated example (FR-024)

**Checkpoint**: `python tests/test_harness_spec_contract.py` exits 0 — foundation ready for all user stories.

---

## Phase 3: User Story 1 + User Story 6 — Run End-to-End + Backward Compatibility (Priority: P1) 🎯 MVP

**Goal (US1)**: `devspark harness run sample.harness.yaml` executes all steps with the noop adapter, writes a complete run artifact directory, and exits 0 — fully traceable without any AI tool.

**Goal (US6)**: All existing commands (`init`, `upgrade`, `registry add/list/validate`) continue to work identically after the harness is wired into the CLI.

**Independent Test (US1)**: Run `devspark harness run sample.harness.yaml` → confirm `.documentation/devspark/runs/<run-id>/result.json` exists with `status: complete` and all expected artifact files present.

**Independent Test (US6)**: Run the existing command suite (`devspark init --help`, `devspark registry list`, etc.) and confirm output is identical to the pre-harness baseline.

### Implementation for User Story 1 + 6

- [ ] T010 [US1] Implement `src/devspark_cli/harness/telemetry.py`: `TelemetrySink` class that appends `TelemetryEvent` JSON objects to `events.jsonl`; support all 7 named event types per contracts/events-schema.md; no-op when `emit_jsonl: false`
- [ ] T011 [US1] Implement `src/devspark_cli/harness/adapters/base.py`: `AgentAdapter` protocol with `name: str`, `is_available() -> bool`, `execute(step: StepSpec, context: RunContext) -> str` (output text); `AgentRequest`/`AgentResponse` types if needed
- [ ] T012 [P] [US1] Implement `src/devspark_cli/harness/adapters/noop.py`: `NoopAdapter` — always available; `execute()` returns empty string immediately; logs `harness.tool.called` event; satisfies SC-001 (noop dry-run < 5s)
- [ ] T013 [P] [US1] Implement `src/devspark_cli/harness/adapters/manual.py`: `ManualAdapter` — renders Rich Panel with step prompt for copy/paste; calls `readchar.readkey()` to wait for completion keypress; when no TTY (`sys.stdout.isatty()` is False) emits `harness.policy.blocked` and fails the step/run with a clear manual-gate-requires-TTY message (FR-036, FR-037)
- [ ] T014 [US1] Implement `src/devspark_cli/harness/runner.py`: `HarnessRunner` — `load_spec()`, `resolve_context()`, `execute_steps()` (sequential, retry loop via RetryPolicy), `write_artifacts()` (spec.resolved.yaml, context.json, per-step prompt.md/output.txt); emit telemetry events for run.started/finished, step.started/finished; handle Ctrl+C → `aborted` status with artifact preservation (FR-026); run retention pruning after each terminal run (FR-028, FR-029)
- [ ] T015 [US1] Implement `devspark harness run` CLI command in `src/devspark_cli/harness/cli.py`: Typer subapp with `run` command; accept `spec_file` + `--dry-run` + `--adapter` options; TTY detection for rich vs plain output (FR-030); exit codes 0/1/2/3 (FR-031); `--dry-run` marks all steps `skipped_dry_run` without executing (FR-034, FR-035); help text documents exit code contract (FR-032)
- [ ] T016 [US6] Wire harness into `src/devspark_cli/__init__.py` with a single `app.add_typer(harness_app, name="harness")` call — this is the only change to any existing file; verify all existing commands still appear in `devspark --help` (FR-021, FR-022, FR-023)
- [ ] T017 [US1] Implement `tests/test_harness_runner_contract.py`: contract tests — `devspark harness run sample.harness.yaml` exits 0 and writes `result.json` with `status: complete`; `--dry-run` writes `skipped_dry_run` steps and exits 0; a no-TTY manual gate path fails clearly, emits `harness.policy.blocked`, and exits non-zero; Ctrl+C path produces `aborted` status and `devspark harness trace <run-id>` renders the partial event log without error (FR-026); noop run completes in under 5 seconds (SC-001); all 5 artifact files present in run directory; `devspark harness run --help` output contains exit code documentation (FR-032); assert `.gitignore` is unmodified before and after every run (FR-033); run existing command suite (`devspark init --help`, `devspark registry list`, `devspark upgrade --help`) and assert output matches pre-harness baseline (SC-002) (depends on T014, T015, T016)

**Checkpoint**: US6 complete. US1 partial — **acceptance scenarios 1, 4, 5** (basic run, noop default, dry-run) are shippable; **scenarios 2 and 3** (retry on validation failure, stop at max attempts) require Phase 7 (T024). Do not mark US1 complete until T024 is done.

---

## Phase 4: User Story 2 — Validate a Spec Before Running (Priority: P2)

**Goal**: `devspark harness validate my-harness.yaml` reports structural errors with field names and corrective suggestions without executing any steps. Completes in < 2 seconds (SC-004).

**Independent Test**: Run `devspark harness validate tests/fixtures/harness/valid_minimal.yaml` → exit 0; run against `invalid_missing_field.yaml` → exit 1 with the field name in the error output.

### Implementation for User Story 2

- [ ] T018 [US2] Implement `devspark harness validate` command in `src/devspark_cli/harness/cli.py`: calls `spec_loader.load()`, reports each validation error with field name and corrective suggestion (FR-009), TTY-aware output (FR-030), exits 0 on valid / 1 on invalid (FR-010); add `validate` to the Typer subapp; add timing assertion to `test_harness_spec_contract.py` (T007): validate against all three fixture files must complete in < 2 seconds each (SC-004)

**Checkpoint**: US2 independently functional — validate catches missing fields, unknown step types, bad apiVersion; exits cleanly with no execution.

---

## Phase 5: User Story 3 — Inspect a Previous Run (Priority: P3)

**Goal**: `devspark harness trace latest` renders the event log of the most recent run as a Rich table showing step id, attempt, status, duration. Accepts explicit run IDs.

**Independent Test**: Run `sample.harness.yaml` then run `devspark harness trace latest` → confirm table output with one row per recorded event including the correct columns.

### Implementation for User Story 3

- [ ] T019 [US3] Implement `devspark harness trace` command in `src/devspark_cli/harness/cli.py`: reads `events.jsonl` from run directory; renders Rich table with columns: timestamp, step_id, attempt, status, duration_ms (FR-011, FR-013); accepts explicit run ID or `latest` alias (resolves to most recent directory by mtime, FR-012); handles missing run ID, missing events.jsonl, and corrupted/incomplete log gracefully; add `trace` to the Typer subapp

**Checkpoint**: US3 independently functional — trace renders a complete event table for any stored run.

---

## Phase 6: User Story 4 — Set a Default Execution Adapter (Priority: P3)

**Goal**: `devspark adapter default claude_code` persists the preference to user config, which is applied on every subsequent run where the spec omits an explicit adapter. Preference survives `devspark upgrade` (SC-006).

**Independent Test**: Run `devspark adapter default noop`, then run a spec with no adapter field, then inspect `spec.resolved.yaml` in the run directory to confirm the saved adapter was applied.

### Implementation for User Story 4

- [ ] T020 [US4] Implement `src/devspark_cli/harness/config.py`: `read_user_config() -> dict` and `write_user_config(data: dict) -> None`; read/write `platformdirs.user_config_dir("devspark") / "config.json"` with fields `default_adapter` and `run_retention_limit`; gracefully handles missing file by applying defaults; config path must be under `platformdirs.user_config_dir()` only — must NOT be under `.devspark/` or any path modified by `devspark upgrade` (verify this in a comment or assertion) (FR-015, FR-016, FR-029, SC-006)
- [ ] T021 [P] [US4] Implement `devspark adapter list` top-level command in `src/devspark_cli/__init__.py`: lists all registered adapters; calls `adapter.is_available()` for each; shows availability status; displays current default from user config; TTY-aware output (FR-014) — add `adapter_app.add_command()` or inline command
- [ ] T022 [P] [US4] Implement `devspark adapter default <name>` top-level command in `src/devspark_cli/__init__.py`: validates adapter name against registered set; saves to user config; reports save path; exits 1 with available adapter list on unknown name (FR-015, FR-017, SC-006)

**Checkpoint**: US4 independently functional — adapter default persists, survives upgrade, is reflected in resolved spec artifact.

---

## Phase 7: User Story 5 — Validation Engine + System Health Doctor (Priority: P4)

**Goal (validation engine)**: All 7 validation rule types working; `error`-severity failures trigger retry with repair prompt injection; `warning`-severity findings recorded but don't block.

**Goal (US5 doctor)**: `devspark doctor` reports pass/fail for every prerequisite check and prints a specific install URL for each failing tool (SC-005, FR-018–020).

**Independent Test (validation)**: Spec with a `file.exists` rule on a missing path — confirm it triggers retry to `maxAttempts`, then `devspark harness trace latest` shows multiple attempt rows for the step.

**Independent Test (US5)**: Run `devspark doctor` on both a complete environment and one with a missing CLI tool; confirm correct status and that failures include actionable remediation hints.

### Implementation for User Story 5 + Validation Engine

- [ ] T023 [US5] Implement `src/devspark_cli/harness/validation.py`: `ValidationEngine.evaluate(rule: ValidationRule, context: RunContext) -> ValidationFinding` supporting all 7 rule types — `always.pass` (unconditional), `file.exists` (path on disk), `file.contains` (substring check), `command.exit_code` (subprocess.run shell=True, capture stdout/stderr to `steps/<step-id>/stdout.txt`), `json.schema` (jsonschema validate), `git.clean` (git status --porcelain), `regex.match` (re.search); severity enforcement: `error` → blocks, `warning` → recorded only (FR-040, FR-041)
- [ ] T024 [US1] Integrate `ValidationEngine` into `src/devspark_cli/harness/runner.py` retry loop: after each step attempt, evaluate all validation rules; on `error`-severity failure with remaining attempts → load `repairPrompt` file, append `## Validation Errors\n<bullet list>` block, pass augmented prompt to next adapter `execute()` call; emit `harness.step.validation` event per rule; emit `harness.policy.blocked` when step is blocked (FR-003, FR-004, FR-005, FR-042, FR-043)
- [ ] T025 [US5] Implement `tests/test_harness_validation_contract.py`: contract tests — each of the 7 rule types evaluated in isolation; `error`-severity failure on a valid step triggers retry; `warning`-severity failure does not block; repair prompt is injected on retry; `requireHumanAfter` pauses execution at the correct attempt (depends on T023, T024)
- [ ] T026 [US5] Implement `devspark doctor` top-level command in `src/devspark_cli/__init__.py`: read-only checks in order — Python ≥ 3.11 (`sys.version_info`), pydantic importable, compatible project layout present (`.devspark/` for installed projects, or `.documentation/` + `pyproject.toml` + `src/devspark_cli/` for source checkouts), `agents-registry.json` readable and valid JSON, `git` available (`shutil.which("git")`), per-agent `requires_cli` checks from registry with `install_url` on failure; TTY-aware output; exits 0 if all pass, 1 if any fail (FR-018, FR-019, FR-020, SC-005)

**Checkpoint**: All 7 validation rule types functional; retry loop injects repair prompts; doctor reports each check with remediation hints.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Real AI agent adapters (Phase 4 plan deliverable), spec lifecycle update, and final wiring.

- [ ] T027 [P] Implement `src/devspark_cli/harness/adapters/claude_code.py`: `ClaudeCodeAdapter` — `is_available()` via `shutil.which("claude")`; `execute()` via `subprocess.run(["claude", "--print", prompt_text])`, capture output to step artifact `output.txt` (plan Phase 4 key decision)
- [ ] T028 [P] Implement `src/devspark_cli/harness/adapters/copilot.py` and `src/devspark_cli/harness/adapters/cursor.py`: same pattern as `claude_code.py` with their respective CLI names; `is_available()` guards runtime invocation (plan Phase 4)
- [ ] T029 Integrate app-scope support in `src/devspark_cli/harness/runner.py`: when `spec.scope.type == "app"`, load the multi-app registry, resolve explicit scope via existing `scope.resolve_scope()` validation, then derive `doc_root` from the resolved app definition via `scope.resolve_doc_root(app, repo_root)` (FR-038, FR-039, plan Phase 4)
- [ ] T030 [P] Update `sample.harness.yaml` at repository root to exercise real adapters and app scope after Phase 4 adapters are complete
- [ ] T031 Update spec.md status from `Draft` to `In Progress` and confirm all 8 success criteria are verifiable against the delivered implementation
- [ ] T032 Implement `tests/test_harness_adapters_contract.py`: contract tests — for each real adapter (claude_code, copilot, cursor): `is_available()` returns `False` when the CLI is absent (`shutil.which` returns None); `execute()` invokes the correct subprocess command with expected arguments when available; adapter output is captured to step artifact `output.txt`; app-scope run resolves `doc_root` via `load_registry()` + `scope.resolve_scope()` + `scope.resolve_doc_root()`; unknown app IDs and multi-app ambiguity fail through the existing scope-validation path rather than a custom harness resolver (FR-038, FR-039) (depends on T027, T028, T029)

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational: Domain Models)    ← blocks ALL user stories
    ↓
Phase 3 (US1 + US6: Run + Backward Compat) ← P1 — MVP
    ↓
Phase 4 (US2: Validate) ← P2
Phase 5 (US3: Trace)    ← P3 — can start after Phase 3
Phase 6 (US4: Adapter)  ← P3 — can start after Phase 3
    ↓
Phase 7 (US5: Doctor + Validation Engine) ← P4 — depends on runner (Phase 3)
    ↓
Phase 8 (Polish: Real Adapters + Scope)
```

### User Story Dependencies

| Story | Priority | Depends on | Can parallel with |
|-------|----------|------------|-------------------|
| US6 (Backward Compat) | P1 | Phase 2 | Shares Phase 3 with US1 |
| US1 (Run End-to-End) | P1 | Phase 2 | Shares Phase 3 with US6 |
| US2 (Validate Spec) | P2 | Phase 3 (US1) | US3, US4 |
| US3 (Inspect Run) | P3 | Phase 3 (US1) | US2, US4 |
| US4 (Adapter Default) | P3 | Phase 3 (US1) | US2, US3 |
| US5 (Doctor) | P4 | Phase 3 (runner) | Phase 8 Polish |

### Within Each Phase

- T004 (spec_models.py) before T005 (spec_loader.py) — loader imports models
- T004 before T008 (schema generation) — schema generated from models
- T010–T013 (telemetry + adapters) before T014 (runner) — runner orchestrates them
- T014 (runner) before T015 (CLI run command) — CLI delegates to runner
- T015 before T016 (__init__.py wiring) — can only wire the Typer subapp after it exists
- T020 (user config) before T021, T022 (adapter commands) — commands read/write config
- T023 (validation engine) before T024 (runner integration)

---

## Parallel Opportunities

### Phase 2 (after T004 completes)

```
T005 (spec_loader.py)           │  T006 (fixtures)
T008 (schema generation)        │  T009 (sample.harness.yaml)
```

### Phase 3 (after T010, T011 complete)

```
T012 (noop adapter)   │  T013 (manual adapter)
```

### Phase 6 (after T020 completes)

```
T021 (adapter list)   │  T022 (adapter default)
```

### Phase 8

```
T027 (claude_code)   │  T028 (copilot + cursor)
T030 (sample update) │  T031 (spec status update)
T032 (adapters contract test — depends on T027, T028, T029)
```

---

## Parallel Example: User Story 1

```
# After T004 completes, launch in parallel:
Task T005: "Implement spec_loader.py"
Task T006: "Populate fixture files"
Task T008: "Generate harness.schema.json"
Task T009: "Create sample.harness.yaml"

# After T010 + T011 complete, launch in parallel:
Task T012: "Implement NoopAdapter"
Task T013: "Implement ManualAdapter"
```

---

## Gate Acknowledgements

| Gate | Status | Concern | Decision | Date |
|------|--------|---------|----------|------|
| checklist | PASS | All items satisfied | Proceed | 2026-04-14 |
| analyze | PASS (warn) | 2 HIGH, 6 MEDIUM, 5 LOW findings — all resolved in-place | All findings applied: spec.md FR-027 (H1,H2) and FR-042 (M3) corrected; T017 hardened (M1,M2,L4,L5); T018 timing assertion added (L2); T020 file location fixed (M4,L3); Phase 3 checkpoint clarified (M5); T032 added (M6) | 2026-04-14 |
| critic | NOT RUN | No `critic.md` exists — required gate per spec frontmatter | Proceed without — run before Phase 3 implementation begins | 2026-04-14 |

---

## Implementation Strategy

### MVP First (Phase 1 + 2 + 3 only — US1 + US6)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational Domain Models (T004–T009)
3. Complete Phase 3: Run End-to-End (T010–T017)
4. **STOP and VALIDATE**: `python tests/test_harness_runner_contract.py` exits 0; `devspark harness run sample.harness.yaml` writes `result.json` with `status: complete`; all existing commands pass
5. This is a shippable increment — full harness execution with noop adapter, TTY/CI output, dry-run, and backward compatibility

### Incremental Delivery

1. Phase 1–2 → Models + loader ready
2. Phase 3 → `devspark harness run` working (MVP, US1 + US6)
3. Phase 4 → `devspark harness validate` (US2)
4. Phase 5 → `devspark harness trace` (US3)
5. Phase 6 → `devspark adapter list/default` (US4)
6. Phase 7 → Full validation engine + `devspark doctor` (US5)
7. Phase 8 → Real AI adapters (Claude Code, Copilot, Cursor) + app scope

### Parallel Team Strategy

With multiple developers after Phase 2 completes:

- **Developer A**: Phase 3 (runner, adapters, CLI run)
- **Developer B**: Phases 4–5 (validate + trace commands in cli.py)
- **Developer C**: Phase 6 (adapter default commands + user config)

All converge for Phase 7 (validation engine + doctor).

---

## Notes

- [P] tasks operate on different files and have no dependencies on incomplete tasks in the same phase
- [Story] label traces each task to the user story it satisfies
- Contract test files are standalone scripts — `python tests/test_*.py` exits 0; no test framework required
- Commit after each checkpoint — each checkpoint is a shippable increment
- The only modification to an existing file is one `app.add_typer()` call in `src/devspark_cli/__init__.py` (T016)
- Run artifacts are written exclusively to `.documentation/devspark/runs/` — never to `.devspark/`
- `analyze` and `critic` gates are recommended before Phase 3 implementation begins (see Gate Acknowledgements)
