---
description: "Task list for Tiered Prompt and Workflow Engine"
---

# Tasks: Tiered Prompt and Workflow Engine

**Input**: Design documents from `/.documentation/specs/001-interactive-analyze-flow/`
**Prerequisites**: [plan.md](../001-interactive-analyze-flow/plan.md), [spec.md](../001-interactive-analyze-flow/spec.md), [research.md](../001-interactive-analyze-flow/research.md), [data-model.md](../001-interactive-analyze-flow/data-model.md), [contracts/](../001-interactive-analyze-flow/contracts/), [quickstart.md](../001-interactive-analyze-flow/quickstart.md)

**Tests**: INCLUDED. The plan explicitly enumerates contract test files (`tests/test_workflow_schema_contract.py`, etc.) and SC-001..SC-010 require executable verification. Test tasks precede implementation tasks within each phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Rationale Summary

### Core Problem

DevSpark today is a prompt library with implicit orchestration. Users hand-stitch sequences, autonomy is unwritten, and there is no shared step-level telemetry or alias entrypoint.

### Decision Summary

Re-platform DevSpark into a tiered system: atomic prompts (`templates/prompts/atomic/`), workflow YAML (`templates/workflows/`), alias entrypoints (`templates/aliases/`), wired by a Python workflow runner that enforces autonomy guardrails and emits JSON Lines telemetry. Three flagship workflows ship: `create-spec`, `execute-plan`, `suggest-improvement`. Existing slash commands stay 100% functional.

### Key Drivers

- Beginner-discoverable entrypoints without losing expert atomic access
- Explicit, auditable autonomy and observability
- Self-improvement loop targeting `markhazleton/devspark`
- Preserve constitutional Backward Compatibility, Ownership Boundary, Platform Parity

### Reviewer Guidance

Focus on: (1) all new framework artifacts under `templates/` and `src/devspark_cli/`; (2) resolver extension is additive only; (3) workflow runner is the **only** autonomy-enforcement layer; (4) telemetry schema identical across workflows; (5) `gh issue create` always targets `markhazleton/devspark`; (6) PowerShell/Bash parity for new scripts; (7) install/upgrade never writes under `.documentation/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (US1..US5) for story-phase tasks
- All paths are repository-root-relative

## Path Conventions

Single project layout per [plan.md](../001-interactive-analyze-flow/plan.md):

- Source: `src/devspark_cli/`
- Templates: `templates/`
- Tests: `tests/`
- Scripts: `scripts/powershell/` and `scripts/bash/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project scaffolding for new directories and runner package.

- [X] T001 Create directory `templates/prompts/atomic/` with a `.gitkeep` placeholder
- [X] T002 Create directory `templates/workflows/` with a `.gitkeep` placeholder
- [X] T003 Create directory `templates/aliases/` with a `.gitkeep` placeholder
- [X] T004 [P] Create runner package skeleton at `src/devspark_cli/runner/__init__.py` (empty `__all__`)
- [X] T005 [P] Add `pyyaml` to `pyproject.toml` `[project] dependencies` if not already pinned, then re-run `pip install -e .[dev]` validation entry in `pyproject.toml`
- [X] T006 [P] Add tests directory marker: ensure `tests/__init__.py` exists; add empty `tests/runner/__init__.py` for runner-scoped tests
- [X] T007 [P] Update `.markdownlint-cli2.jsonc` ignore patterns (if needed) so `templates/prompts/atomic/*.md` and new contracts dir lint cleanly

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Resolver extension, atomic-prompt frontmatter validator, and shared schema validators that every user story depends on.

**⚠️ CRITICAL**: No user-story work can begin until this phase is complete.

- [X] T008 Extend `src/devspark_cli/resolution.py` to resolve `templates/prompts/atomic/<id>.md`, `templates/workflows/<id>.yaml`, `templates/aliases/<id>.yaml` through the existing 3-tier override chain (personal → team → stock); add `resolve_atomic_prompt`, `resolve_workflow`, `resolve_alias` functions
- [X] T009 [P] Implement atomic-prompt frontmatter validator in `src/devspark_cli/runner/loader.py` per [contracts/atomic-prompt-frontmatter.md](../001-interactive-analyze-flow/contracts/atomic-prompt-frontmatter.md) (functions: `parse_atomic_prompt`, `validate_atomic_prompt`)
- [X] T010 [P] Implement workflow YAML loader and validator in `src/devspark_cli/runner/loader.py` per [contracts/workflow-schema.md](../001-interactive-analyze-flow/contracts/workflow-schema.md) (functions: `parse_workflow`, `validate_workflow`, error codes `WF_*`)
- [X] T011 [P] Implement alias YAML loader and validator in `src/devspark_cli/runner/loader.py` per [contracts/alias-schema.md](../001-interactive-analyze-flow/contracts/alias-schema.md) (functions: `parse_alias`, `validate_alias`, error codes `ALIAS_*`); enforce no-chain rule and atomic-prompt name-collision check
- [X] T012 Implement workflow `when`-expression parser in `src/devspark_cli/runner/loader.py` (restricted grammar: `==`, `!=`, `&&`, `||`, parens, literals, `context.<key>`); produce error `WF_WHEN_PARSE` on failure
- [X] T013 [P] Author atomic-prompt frontmatter contract test `tests/test_atomic_prompt_frontmatter_contract.py` covering all `AP_*` error codes, the `legacy_command` mapping (negative path), AND a positive 1:1 coverage assertion that enumerates `templates/commands/*.md` and asserts every command has a corresponding `templates/prompts/atomic/<id>.md` shim whose `legacy_command` frontmatter equals the source command id
- [X] T014 [P] Author workflow schema contract test `tests/test_workflow_schema_contract.py` covering all `WF_*` error codes, a happy-path round-trip, AND a `when`-expression fuzz suite asserting that well-known invalid expressions return `WF_WHEN_PARSE` and never silently parse (e.g., `=`, `===`, `context.x AND context.y`, unbalanced parens, attribute traversal `context.x.y`).
- [X] T015 [P] Author alias resolution contract test `tests/test_alias_resolution_contract.py` covering all `ALIAS_*` error codes, no-chain enforcement, and resolver fallback (alias miss → direct workflow)
- [X] T016 [P] Update `tests/test_script_resolution_contract.py` to assert that `resolve_atomic_prompt`, `resolve_workflow`, `resolve_alias` honor the personal → team → stock chain identically to `templates/commands/`
- [X] T017 Implement back-compat atomic prompt generator: scan `templates/commands/*.md` and produce a thin atomic prompt under `templates/prompts/atomic/<command>.md` for each (frontmatter + one-line pointer to the canonical command file). Add helper script `scripts/powershell/generate-atomic-shims.ps1` and Bash parity `scripts/bash/generate-atomic-shims.sh`
- [X] T018 Run T017 generator and commit the produced atomic prompt shim files for all 28 existing commands under `templates/prompts/atomic/`
- [X] T018a Add CI hook (markdownlint-cli2 sibling step or new `.github/workflows/shim-drift.yml`) that runs `generate-atomic-shims --check` and fails when any command in `templates/commands/` lacks a corresponding shim or any shim is stale.
- [X] T018b [P] Spike: validate the thin-shim model is sufficient for at least 3 representative commands carrying significant prose business logic (`address-pr-review`, `harvest`, `commit-audit`). If any command cannot be expressed as a thin shim, document the divergence in `.documentation/architecture/review-stage-divergence.md` (T055a) and add a follow-up task before T018 lands.

**Checkpoint**: Foundation ready — user story implementation can begin.

---

## Phase 3: User Story 1 - Create Spec via Tiered Workflow (Priority: P1) 🎯 MVP

**Goal**: A single high-level entrypoint `create-spec` orchestrates `specify` → `plan` → `generate-tasks` → `analyze` and pauses after `analyze`.

**Independent Test**: `devspark run create-spec "<feature>"` produces spec.md, plan.md, tasks.md, and an analyze gate, then pauses without progressing to implementation.

### Tests for User Story 1

- [X] T019 [P] [US1] Author runner contract test `tests/test_workflow_runner_contract.py` covering: ordered step execution, `pause_after` behavior, atomic-prompt id resolution failure, and workflow-context propagation between steps
- [X] T020 [P] [US1] Author integration test `tests/test_create_spec_workflow_integration.py` that loads `templates/workflows/create-spec.yaml`, executes a stub-runner pass through all 4 steps, and asserts pause-after-analyze with `output_type=reviewable-artifact`

### Implementation for User Story 1

- [X] T021 [P] [US1] Implement workflow executor in `src/devspark_cli/runner/executor.py`: ordered step iteration, context dict, `pause_after` honoring, `when` evaluation, `on_failure` semantics, AND a stub-execution mode (`mode="stub"`) that records step ids without invoking atomic prompts (required dependency for T019/T020/T034 deterministic CI tests). On every pause, print `Paused. Resume with: devspark resume <workflow_run_id>` to stderr (FR-007c).
- [X] T022 [US1] Wire executor to loader from T010/T012 (constructor injection); expose `WorkflowRunner.run(workflow, context)` entry point in `src/devspark_cli/runner/executor.py`
- [X] T023 [P] [US1] Author workflow definition `templates/workflows/create-spec.yaml` per [contracts/workflow-schema.md](../001-interactive-analyze-flow/contracts/workflow-schema.md): steps `specify`, `plan`, `generate-tasks`, `analyze`; `pause_after: true` on `analyze`; `output_type: reviewable-artifact`; `autonomy.level: assisted`; `review_after: [analyze]`
- [X] T024 [P] [US1] Author alias definition `templates/aliases/create-spec.yaml` pointing to workflow `create-spec`
- [X] T025 [US1] Add `devspark run <alias|workflow>` subcommand in `src/devspark_cli/commands.py` that resolves alias → workflow, instantiates `WorkflowRunner`, and prints output-type summary
- [X] T026 [US1] Add Bash wrapper `scripts/bash/run-workflow.sh` that shells to `python -m devspark_cli run "$@"` (PowerShell parity wrapper added in T063 below)

**Checkpoint**: `create-spec` workflow runs end-to-end and pauses after `analyze`. SC-001 verifiable.

---

## Phase 4: User Story 5 - Govern Automation with Autonomy and Observability (Priority: P1)

**Goal**: Workflows obey explicit autonomy levels enforced by the runner; every step emits structured telemetry.

**Independent Test**: Run any workflow with `autonomy.level=assisted`; observe pause at `review_after`. Run with `autonomy.level=autonomous` and a guardrail-violating step; observe `guardrail_triggered` event and downgrade. Inspect `.documentation/telemetry/workflow-events.jsonl` for required fields.

> Sequenced before US2 because US2's `execute-plan` depends on autonomy + telemetry being live.

### Tests for User Story 5

- [X] T027 [P] [US5] Author telemetry contract test `tests/test_telemetry_event_contract.py` covering all required fields, all `phase` enum values, all `EVT_*` error codes (including `EVT_ERROR_CLASS_REQUIRED` and `EVT_ERROR_TOO_LONG`), `DEVSPARK_TELEMETRY_PATH` override, AND fail-soft behavior: simulate write failure (read-only path / disk-full) and assert the workflow does not abort and the JSONL file is not corrupted (FR-019 edge case)
- [X] T028 [P] [US5] Author autonomy enforcement contract test `tests/test_autonomy_enforcement_contract.py` covering: assisted-mode pause at `review_after`, autonomous-mode `max_files_changed` block, `restricted_paths` block, `max_total_lines_changed` block, downgrade-to-assisted behavior, and absent-guardrails-with-autonomous abort

### Implementation for User Story 5

- [X] T029 [P] [US5] Implement telemetry writer in `src/devspark_cli/runner/telemetry.py` per [contracts/telemetry-event.md](../001-interactive-analyze-flow/contracts/telemetry-event.md): JSONL append, schema validation including `error ≤ 500 chars` and `error_class` required when `phase=failed`, env-var override, fail-soft on write error, AND OS-level exclusive file lock around each append (`fcntl.flock` POSIX / `msvcrt.locking` Windows). Reject events > 4 KB or `context` > 1 KB with `EVT_TOO_LARGE`.
- [X] T029a [P] [US5] Author concurrent-append contract test `tests/test_telemetry_concurrency_contract.py`: spawn 50 concurrent processes appending events to the same path; assert (a) line count matches expected, (b) every line is independently valid JSON, (c) no event is truncated or interleaved.
- [X] T030 [P] [US5] Implement autonomy enforcer in `src/devspark_cli/runner/autonomy.py`: pre-step working-tree baseline capture (HEAD + index snapshot), post-step diff against baseline, evaluation of `max_files_changed` / `restricted_paths` / `max_total_lines_changed`, git-stash rollback of offending changes (or hard-reset for untracked-only), `guardrail_triggered` event emission with `guardrail_rule`, and downgrade-to-assisted-pause vs `EXIT_GUARDRAIL_BLOCKED` per policy (FR-015). Refuse start when working tree is dirty unless `--allow-dirty` is supplied (FR-015a).
- [X] T031 [US5] Wire `TelemetryWriter` and `AutonomyEnforcer` into `WorkflowRunner` from T022; emit `started` / `completed` / `paused` / `failed` / `guardrail_triggered` events at the documented phases
- [X] T032 [US5] Implement non-interactive policy gate in `src/devspark_cli/commands.py`: when `--non-interactive` is set and the workflow needs autonomy input that wasn't supplied, fail with exit code `EXIT_AUTONOMY_REQUIRED` (per [contracts/exit-codes.md](../001-interactive-analyze-flow/contracts/exit-codes.md)) and an action-required message that names all three input channels: `--autonomy` flag, `DEVSPARK_AUTONOMY` env var, `.devspark/autonomy.yaml` file (FR-016, SC-006)
- [X] T032a [P] [US5] Implement pause-state persistence in `src/devspark_cli/runner/executor.py`: on `pause_after` or guardrail-downgrade pause, serialize `schema_version=1`, `workflow_id`, `workflow_run_id`, `last_completed_step_id`, `next_step_id`, `context`, `autonomy_level`, `paused_at` (ISO 8601 UTC), and `context_checksum` (SHA-256 over serialized context) to `.documentation/telemetry/runs/<workflow_run_id>.json` (env override `DEVSPARK_RUNS_PATH`). Writes MUST be atomic: open `<file>.tmp`, write, fsync, `os.replace` to final path. Honor FR-007a.
- [X] T032b [US5] Add `devspark resume <workflow_run_id>` subcommand in `src/devspark_cli/commands.py`: load persisted state, validate `schema_version`, recompute and verify `context_checksum`, re-resolve workflow definition, validate persisted `workflow_id` matches resolved id, reconstruct `WorkflowRunner`, continue from `next_step_id`, reuse original `workflow_run_id`. On any check failure exit `EXIT_RESUME_FAILED` with a message naming the failing check. Honor FR-007b.
- [X] T032c [P] [US5] Author pause-resume contract test `tests/test_pause_resume_contract.py`: pause writes documented JSON shape with all required fields (incl. `schema_version`, `context_checksum`); atomic write survives crash mid-write (simulate by killing during `.tmp` phase — final file is untouched OR fully valid); resume reads it, verifies checksum, continues at `next_step_id`, and emits telemetry under the same `workflow_run_id`; resume fails with `EXIT_RESUME_FAILED` when (a) workflow definition no longer resolves, (b) persisted `workflow_id` mismatches, (c) checksum is wrong.
- [X] T033 [US5] Add `.documentation/telemetry/.gitignore` containing `workflow-events.jsonl` and `runs/` so local telemetry and resumable run state never get committed

**Checkpoint**: All workflow steps emit valid telemetry; autonomy guardrails enforced. SC-005, SC-006 verifiable.

---

## Phase 5: User Story 2 - Execute Plan Workflow with Governance Pauses (Priority: P1)

**Goal**: A single entrypoint `execute-plan` runs `implement` → `create-pr` → `review-pr` with a mandatory pause after `create-pr` in assisted mode.

**Independent Test**: `devspark run execute-plan` runs `implement` and `create-pr`, pauses for review, and only continues to `review-pr` after explicit continue. PR is opened on continue.

### Tests for User Story 2

- [X] T034 [P] [US2] Author integration test `tests/test_execute_plan_workflow_integration.py` validating ordered execution, pause after `create-pr`, and `output_type: pull-request`

### Implementation for User Story 2

- [X] T035 [P] [US2] Author workflow definition `templates/workflows/execute-plan.yaml`: steps `implement`, `create-pr`, `review-pr`; `pause_after: true` on `create-pr`; `output_type: pull-request`; `autonomy.level: assisted`; `review_after: [create-pr]`
- [X] T036 [P] [US2] Author alias definition `templates/aliases/execute-plan.yaml` pointing to workflow `execute-plan`

**Checkpoint**: `execute-plan` workflow runs end-to-end with governance pause. SC-002 verifiable.

---

## Phase 6: User Story 3 - Submit Improvement Suggestions as Workflow (Priority: P1)

**Goal**: `suggest-improvement` captures context, classifies, and creates an issue in `markhazleton/devspark`. Conditional steps assign agent and trigger implementation when enabled.

**Independent Test**: `devspark run suggest-improvement` produces a GitHub issue URL in `markhazleton/devspark`. With `--assign-agent`, conditional steps run and emit telemetry.

### Tests for User Story 3

- [X] T037 [P] [US3] Author issue adapter contract test `tests/test_issue_adapter_contract.py` covering: hardcoded `repos/markhazleton/devspark/issues` endpoint, classification → label mapping, body template rendering, `EXIT_GH_*` exit codes, JSON-payload-via-stdin (no flags carry user/model content), AND adversarial title=`--repo evil/owner` test asserting the issue still files in `markhazleton/devspark` because no flag-parsing surface exists; AND interactive-confirmation prompt is shown unless `--yes` is supplied; non-interactive without `--yes` exits `EXIT_AUTONOMY_REQUIRED`.
- [X] T038 [P] [US3] Author conditional-execution contract test in `tests/test_workflow_runner_contract.py` (extend the file from T019): `when` true vs false branches, missing context-key handling

### Implementation for User Story 3

- [X] T039 [P] [US3] Implement issue adapter in `src/devspark_cli/issues.py` per [contracts/issue-adapter.md](../001-interactive-analyze-flow/contracts/issue-adapter.md): `subprocess.run(["gh", "api", "repos/markhazleton/devspark/issues", "-X", "POST", "--input", "-"], input=json.dumps(payload), check=True)` with the payload built as a Python dict (no string interpolation into argv); classification → label map fixed; body template; `EXIT_GH_*` codes; pre-call confirmation prompt shown unless `--yes`; abort with `EXIT_AUTONOMY_REQUIRED` if non-interactive without `--yes`.
- [X] T040 [P] [US3] Author atomic prompt `templates/prompts/atomic/capture-context.md` per [contracts/atomic-prompt-frontmatter.md](../001-interactive-analyze-flow/contracts/atomic-prompt-frontmatter.md): `audience: intermediate`, `exposed: false`, `category: improvement`, outputs `context.summary`, `context.classification_hint`
- [X] T041 [P] [US3] Author atomic prompt `templates/prompts/atomic/classify-improvement.md`: outputs `proposal.classification`, `proposal.title`
- [X] T042 [P] [US3] Author atomic prompt `templates/prompts/atomic/create-issue.md`: invokes adapter from T039; outputs `proposal.issue_url`
- [X] T043 [P] [US3] Author atomic prompt `templates/prompts/atomic/assign-agent.md`: gated by `context.assign_agent == true`
- [X] T044 [P] [US3] Author workflow definition `templates/workflows/suggest-improvement.yaml`: steps `capture-context`, `classify-improvement`, `create-issue`, conditional `assign-agent` (`when: context.assign_agent == true`), conditional `implement` (`when: context.assign_agent == true`); `output_type: issue-link`; `autonomy.level: assisted`
- [X] T045 [P] [US3] Author alias definition `templates/aliases/suggest-improvement.yaml` pointing to workflow `suggest-improvement`
- [X] T046 [P] [US3] Author GitHub issue template `.github/ISSUE_TEMPLATE/devspark-improvement.md` matching the body template in [contracts/issue-adapter.md](../001-interactive-analyze-flow/contracts/issue-adapter.md) (FR-029, FR-030)

**Checkpoint**: `suggest-improvement` opens issues in `markhazleton/devspark`. SC-003, SC-009 verifiable.

---

## Phase 7: User Story 4 - Discover Workflows Through Aliases and Metadata (Priority: P2)

**Goal**: `devspark help` surfaces high-level aliases first, advanced atomic prompts second, hidden prompts only with `--all`. Filtering by audience and category works.

**Independent Test**: Default `devspark help` lists `create-spec`, `execute-plan`, `suggest-improvement` at the top with descriptions. `devspark help --all` adds hidden prompts. `devspark help --category improvement` filters correctly.

### Tests for User Story 4

- [X] T047 [P] [US4] Author CLI help test `tests/test_help_discovery_contract.py`: default view ordering (aliases first), `--all` flag includes `exposed: false`, `--category` filter, `--audience` filter

### Implementation for User Story 4

- [X] T048 [P] [US4] Implement `devspark help`, `devspark workflows list`, `devspark workflows validate`, and `devspark runs list` subcommands in `src/devspark_cli/commands.py`: enumerate aliases, workflows, atomic prompts via resolver from T008; `validate` parses every YAML under `templates/workflows/` and `templates/aliases/` without executing; `runs list` enumerates `.documentation/telemetry/runs/*.json`. Respect `exposed`, group by `category`, sort by `audience`.
- [X] T049 [US4] Implement repeated-sequence detection hint in `src/devspark_cli/commands.py` (FR-022): track recent atomic invocations in a small in-process ring buffer; trigger advisory "Tip: try `devspark run <alias>`" when 3 or more consecutive atomic invocations within a 30-minute window match the first 3 ordered steps of a known workflow definition. SHOULD-level only; no behavior change.

**Checkpoint**: Discovery UX matches spec. SC-004 verifiable.

---

## Phase 8: Review Resolution Contract (Cross-Cutting, P1)

**Goal**: `clarify`, `analyze`, `critic`, `pr-review`, `address-pr-review` all emit findings in the shared resolution contract shape.

**Independent Test**: Each review command produces an artifact whose findings include `finding_id`, `severity`, `description`, `recommended_action`, `execution_mode`, `status`, `outcome` (post-resolution).

### Tests

- [X] T050 [P] Author review-resolution contract test `tests/test_review_resolution_contract.py` covering required fields and stable-id uniqueness across the five review prompts

### Implementation

- [X] T051 [P] Update `templates/commands/clarify.md` output template to emit findings in the shared shape (additive only; preserve existing prose)
- [X] T052 [P] Update `templates/commands/analyze.md` output template to emit findings with stable IDs and `execution_mode` field; preserve current remediation behavior captured in the prior analyze-flow clarifications
- [X] T053 [P] Update `templates/commands/critic.md` output template to emit findings in the shared shape
- [X] T054 [P] Update `templates/commands/pr-review.md` output template to emit findings with stable IDs and `execution_mode`
- [X] T055 [P] Update `templates/commands/address-pr-review.md` to consume `finding_id` and write `status` + `outcome` updates back into the review artifact (preserves commit-isolation behavior per FR-028)
- [X] T055a [P] Author `.documentation/architecture/review-stage-divergence.md` enumerating any per-stage behavior differences across `clarify`, `analyze`, `critic`, `pr-review`, `address-pr-review` (FR-036). If no divergences exist, the document MUST state so explicitly. Add a contract test `tests/test_review_stage_divergence_contract.py` that fails when a stage prompt contains a marker `<!-- DIVERGENT: ... -->` not also referenced in the divergence document.

**Checkpoint**: Review artifacts conform to the contract. SC-007 verifiable.

---

## Phase 9: Documentation & Adoption (Cross-Cutting)

**Purpose**: Ship the documentation gates required by SC-010 before status can advance from Draft.

- [X] T056 [P] Add Getting Started workflows guide at `.documentation/workflows/getting-started.md` covering `create-spec`, `execute-plan`, `suggest-improvement` (FR-032)
- [X] T056a [P] Add Threat Model document at `.documentation/architecture/threat-model.md` covering: prompt-output-as-untrusted-input (issue adapter argv flooding mitigation), pause-state corruption (atomic write + checksum), telemetry concurrent-write (file lock), gh token scope (interactive confirmation), and dirty-working-tree assumption (FR-015a). Single page, ~1–2 KB.
- [X] T056b [P] Add Concurrency Model note to `.documentation/architecture/tiered-workflow-engine.md` (T057): single repo MAY run multiple `devspark run` invocations concurrently; telemetry writer is concurrency-safe; pause-state files are run-id-scoped; guardrail enforcement assumes per-process working-tree boundary.
- [X] T057 [P] Add Workflow Architecture overview at `.documentation/architecture/tiered-workflow-engine.md` covering the three tiers, the resolver chain, AND a paragraph describing how the tiered engine interacts with multi-app mode (`.documentation/devspark.json mode: multi-app`): aliases and workflows resolve from `{app.path}/templates/` first when `--app <id>` is supplied (FR-032, FR-033)
- [X] T058 [P] Add Autonomy Model guide at `.documentation/autonomy/autonomy-model.md` covering levels, guardrails, runner enforcement, telemetry signals (FR-032)
- [X] T059 [P] Add Improvement Loop guide at `.documentation/improvement-loop/overview.md` covering `suggest-improvement`, the canonical issue target, and the GitHub issue template (FR-031, FR-032)
- [X] T060 [P] Add Advanced Atomic Usage guide at `.documentation/workflows/advanced-atomic-usage.md` covering direct atomic prompt invocation for expert users (FR-021, FR-033)
- [X] T061 Update `README.md` and `quickstart/devspark_quickstart_copilot.md` to mention the three flagship aliases as the recommended entrypoints
- [X] T062 Update `CLAUDE.md` Commands section to list the three new aliases under `/devspark.{command}` ordering

---

## Phase 10: Polish & Cross-Cutting Concerns

- [X] T063 [P] PowerShell parity wrapper `scripts/powershell/run-workflow.ps1` matching the Bash wrapper from T026; verify behavior with `tests/test_script_parity_contract.py` extension
- [X] T064 [P] Extend `tests/test_script_parity_contract.py` to assert PS/Bash parity for `run-workflow.*` and `generate-atomic-shims.*`
- [X] T065 [P] Extend `tests/test_upgrade_migration_safety.py` to assert install/upgrade flows never write under `.documentation/telemetry/` or any other `.documentation/` subpath. Test MUST include a comment block explicitly noting that runtime workflow execution is allowed to write under `.documentation/` per spec Assumptions and constitution §III commentary (the test guards install/upgrade only).
- [X] T065a [P] Add micro-benchmark task `tests/test_runner_performance_intent.py` measuring (a) workflow startup overhead and (b) per-event telemetry append latency on a stub workflow; emit a warning (not a hard failure) if startup > 200 ms p95 or append > 5 ms per event (FR/Plan design intent only).
- [X] T066 Run [quickstart.md](../001-interactive-analyze-flow/quickstart.md) steps 1–10 end-to-end and capture results into `gates/quickstart-validation.md`
- [X] T067 Run `markdownlint-cli2` across all new markdown artifacts under `templates/prompts/atomic/`, `.documentation/specs/001-interactive-analyze-flow/contracts/`, and the four new `.documentation/` guides
- [X] T068 Run full pytest suite and ensure all new contract tests pass; capture summary into the PR description

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Phase 1; BLOCKS all user-story phases
- **US1 / US5 / US2 / US3 / US4 (Phases 3–7)**: Depend on Phase 2
  - US5 (Phase 4) MUST complete before US2 (Phase 5) so `execute-plan` can rely on autonomy + telemetry
  - US1, US3, US4 are independent of US5 once Phase 2 is done (they exercise the runner but tolerate basic telemetry)
- **Review Resolution Contract (Phase 8)**: Depends on Phase 2 only; runs in parallel with user-story phases
- **Documentation (Phase 9)**: Depends on Phases 3–8 being functionally complete (docs reference real behavior)
- **Polish (Phase 10)**: Depends on all desired user stories

### Critical Path (MVP)

`Phase 1 → Phase 2 → Phase 3 (US1)` is the MVP slice. Demonstrates tiered architecture end-to-end with a single workflow.

### Parallel Execution Examples

**Phase 2 parallel batch** (after T008 lands): T009, T010, T011, T013, T014, T015, T016 can all run in parallel (different files).

**Phase 6 parallel batch**: T039, T040, T041, T042, T043, T044, T045, T046 can all run in parallel (different files; T039 has no test-time dep on the prompts).

**Phase 9 parallel batch**: T056, T057, T058, T059, T060 are all independent doc files.

### Within Each User Story

Tests precede implementation. Within implementation, atomic prompts and YAML files (different paths) are parallelizable; CLI wiring tasks that touch `commands.py` are sequential to each other.

---

## Implementation Strategy

1. **MVP**: Phases 1 + 2 + 3. Delivers `devspark run create-spec` end-to-end with the tiered resolver and the back-compat shim layer. All existing slash commands continue to work unchanged.
2. **Production-readiness slice**: Add Phase 4 (autonomy + telemetry) and Phase 5 (`execute-plan`). At this point the platform supports governed automation.
3. **Self-improvement slice**: Add Phase 6 (`suggest-improvement`) and Phase 8 (review resolution contract). The system can now consume its own feedback.
4. **Adoption slice**: Add Phase 7 (discovery UX) and Phase 9 (documentation). Status advances from Draft.
5. **Hardening**: Phase 10 polish + parity tests + quickstart validation.

---

## Gate Acknowledgements

- **`analyze` gate** (required by spec frontmatter): Not yet produced. Recommended action: run `/devspark.analyze` after this `tasks.md` is committed; the handoff is the standard next step from `/devspark.tasks`.
- **`critic` gate** (required by spec frontmatter): Not yet produced. Recommended action: run `/devspark.critic` after `analyze`. Implementation MUST NOT begin until both gates are satisfied.
- **`checklists/requirements.md` gate**: All items checked; no unresolved findings.
