---
classification: full-spec
risk_level: medium
target_workflow: specify-full
required_artifacts: spec, plan, tasks
recommended_next_step: plan
required_gates: checklist, analyze, critic
---

# Feature Specification: DevSpark Harness Runtime

**Feature Branch**: `002-harness-runtime`
**Created**: 2026-04-14
**Status**: Complete <!-- Valid: Draft | In Progress | Complete -->
**Input**: User description: "DevSpark Harness Runtime — an additive, spec-driven orchestration engine that extends the existing DevSpark CLI without changing any existing behavior."

## Rationale Summary

### Core Problem

DevSpark today coordinates AI-assisted development through prompts and slash commands — each invoked manually, in sequence, by a human. There is no way to define a repeatable, multi-step workflow that can be kicked off with a single command, validated automatically, and retried on failure. This forces users to re-orchestrate the same sequences by hand across projects and teams, leading to inconsistency, skipped steps, and manual error recovery.

### Decision Summary

Add a harness runtime layer to DevSpark that lets users define automated, multi-step AI development workflows in a declarative spec file. The harness executes steps in order, validates each result, retries on failure with injected feedback, and persists a full audit trail. All existing DevSpark behavior is preserved unchanged — the harness is entirely additive.

### Key Drivers

- Teams want repeatable AI-assisted workflows (specify → plan → implement → validate) without manual re-invocation
- Validation failures today require the user to detect and re-run steps manually; automated retry reduces wasted effort
- Users need confidence that harness runs work without an AI tool installed (noop fallback required for CI and testing contexts)

### Source Inputs

- DevSpark Harness Runtime Comprehensive Implementation Specification (2026-04-14)
- Gap analysis and design decision resolution session (2026-04-14)
- DevSpark Constitution v1.0.0 — Backward Compatibility (NON-NEGOTIABLE), Simplicity, Ownership Boundary

### Tradeoffs Considered

- Option A: Rewrite existing slash-command model to be harness-native — rejected; breaks all existing usage, violates the Backward Compatibility principle
- Option B: External orchestration script (shell/PowerShell) — rejected; no validation engine, no retry loop, no artifact persistence, no adapter abstraction
- Selected: Additive harness layer alongside existing CLI — preserves all existing behavior, introduces new capabilities only through new commands and new spec files

### Architectural Impact

- One new `harness` subcommand group added (`devspark harness run/validate/trace`); three top-level commands added (`devspark adapter list/default`, `devspark doctor`); zero existing commands changed
- Run artifacts written to `.documentation/devspark/runs/<run-id>/` — repository-owned transactional records, treated as user work product per the constitution's classification of `.documentation/` as the user-owned directory
- User adapter preference and retention limit persisted to user-level config directory so upgrades cannot clobber them
- New code added alongside existing modules; no existing imports modified
- `devspark init` and `devspark upgrade` are unchanged — `.documentation/` is user-owned and must not be modified by the framework

### Reviewer Guidance

Reviewers should verify: (1) no existing command behavior changes; (2) run artifacts land in `.documentation/devspark/runs/` and never in `.devspark/`; (3) validation failure paths trigger retry correctly and stop at max attempts; (4) noop adapter produces a valid result without any AI tool present.

---

## Clarifications

### Session 2026-04-14

- Q: When a run is interrupted mid-step, should partial artifacts be preserved or discarded, and what status should the run receive? → A: Preserve artifacts; set run status to `aborted` (distinct from `failed`); `devspark harness trace` shows the partial event log.
- Q: When a harness spec declares a version higher than the installed CLI supports, should the CLI refuse or proceed? → A: Refuse to run; report the version mismatch and the minimum CLI version required to run the spec.
- Q: Should old run artifacts be automatically pruned, or is retention management out of scope? → A: Auto-retain the last N runs (default N=20); configurable; oldest run directory deleted automatically after each new run when the count exceeds N.
- Q: How should `devspark harness run` format output in a non-interactive (CI/no-TTY) context? → A: Auto-detect TTY; use plain-text output with structured exit codes in non-TTY environments; use rich formatted output when a TTY is present. Exit code 0 = complete, non-zero = failed or aborted.
- Q: Should DevSpark automatically protect run artifacts from accidental version control exposure? → A: No. Run artifacts are stored in `.documentation/devspark/runs/` as repository-owned transactional user documents, not framework files. The framework must not manage `.gitignore` for this path — version control of run artifacts is the user's decision. *(Revised: original answer assumed `.devspark/` storage; corrected to constitutional classification of runs as user work product in `.documentation/`.)*
- Q: Should harness commands use a `devspark harness` subgroup or live at the top level? → A: Subgroup — `devspark harness run/validate/trace`. Adapter and doctor commands remain top-level.
- Q: Should the `manual` adapter (renders copy/paste blocks for IDE agents) be in Phase 2 alongside noop? → A: Yes — `manual` adapter ships in Phase 2.
- Q: Should the run result file be named `run_result.json` or `result.json`? → A: `result.json`.
- Research integration (2026-04-14): Added `apiVersion`/`kind`/`scope` to HarnessSpec; enriched RetryPolicy with `backoff`, `retryOn`, `requireHumanAfter`; added `ValidationRule` as named entity with 7 built-in rule types; added `TelemetryEvent` entity with named event types; enriched `StepResult` with validation findings and artifact delta; added FR-034–FR-043 covering dry-run, manual adapter, multi-app scope, validation rule types, telemetry event names, and per-step artifact tracking. Note: research sample YAML uses `.devspark/runs` — corrected to `.documentation/devspark/runs/` per constitutional classification.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Run a Harness Spec End-to-End (Priority: P1)

A developer has authored a harness spec file that defines a two-step workflow: an agent task followed by a validation check. They run `devspark harness run my-workflow.yaml` from the project root. The harness loads the spec, executes each step in order, records events to a run log, and reports the final result (pass or fail) to the terminal.

**Why this priority**: This is the primary user-facing capability of the harness. All other commands exist in support of this one. Without it, nothing else has value.

**Independent Test**: Can be fully tested by running `devspark harness run sample.harness.yaml` with the noop adapter and confirming a `result.json` is written to `.documentation/devspark/runs/<run-id>/` with status `complete`.

**Acceptance Scenarios**:

1. **Given** a valid harness spec file exists, **When** the user runs `devspark harness run <spec.yaml>`, **Then** the harness executes all steps in declared order and writes a result file to `.documentation/devspark/runs/<run-id>/result.json`
2. **Given** a step fails its validation check and retries remain, **When** the retry policy allows further attempts, **Then** the harness injects the validation errors as feedback and re-executes the step
3. **Given** a step exhausts all retry attempts, **When** no further retries are allowed, **Then** the harness stops execution, writes a failed result, and reports the failure clearly to the terminal
4. **Given** no adapter is specified in the spec and no user default is set, **When** the user runs `devspark harness run <spec.yaml>`, **Then** the harness uses the noop adapter and completes without error
5. **Given** any valid harness spec, **When** the user runs `devspark harness run <spec.yaml> --dry-run`, **Then** the harness validates the spec, emits a run directory with all expected files, marks every step `skipped_dry_run`, and exits successfully without executing any step actions

---

### User Story 2 — Validate a Spec Before Running (Priority: P2)

A developer has written a new harness spec and wants to confirm it is structurally valid before committing to a full run. They run `devspark harness validate my-workflow.yaml`. The command checks the spec, reports any structural errors with field names and corrective suggestions, and exits without executing any steps.

**Why this priority**: Validation catches authoring errors cheaply. Running an invalid spec wastes time and produces confusing mid-run failures.

**Independent Test**: Can be fully tested by running `devspark harness validate` against both a valid spec and a deliberately malformed spec and confirming correct exit codes and error messages in each case.

**Acceptance Scenarios**:

1. **Given** a structurally valid harness spec, **When** the user runs `devspark harness validate <spec.yaml>`, **Then** the command exits with success and reports no errors
2. **Given** a spec with a missing required field, **When** the user runs `devspark harness validate <spec.yaml>`, **Then** the command names the missing field, suggests a correction, and exits with failure
3. **Given** a spec referencing an unknown step type, **When** the user runs `devspark harness validate <spec.yaml>`, **Then** the command lists the valid step types and exits with failure

---

### User Story 3 — Inspect a Previous Run (Priority: P3)

After a harness run completes or fails, a developer wants to understand what happened — which steps ran, how many attempts each took, and what the final status was. They run `devspark harness trace <run-id>` (or `devspark harness trace latest`). The command reads the persisted run log and displays a structured table of events.

**Why this priority**: Observability is essential for diagnosing failures. Without trace, users must parse raw log files manually.

**Independent Test**: Can be fully tested by running any harness spec then running `devspark harness trace latest` and confirming the output table contains one row per recorded event with the correct columns.

**Acceptance Scenarios**:

1. **Given** a completed run exists, **When** the user runs `devspark harness trace <run-id>`, **Then** a table is displayed showing each step's id, attempt number, final status, and duration
2. **Given** at least one run has been recorded, **When** the user runs `devspark harness trace latest`, **Then** the most recent run is displayed without requiring the run ID
3. **Given** no runs have been recorded, **When** the user runs `devspark harness trace latest`, **Then** the command reports that no runs exist and exits with a helpful message

---

### User Story 4 — Set a Default Execution Adapter (Priority: P3)

A developer works primarily with Claude Code and wants all harness runs on their machine to use the Claude Code adapter by default without specifying it in every spec file. They run `devspark adapter default claude_code`. On future runs, any spec without an explicit adapter uses their saved preference.

**Why this priority**: Most users target a single AI tool. Requiring adapter declaration in every spec file is repetitive friction.

**Independent Test**: Can be fully tested by setting a default adapter, running a spec that omits the adapter field, and confirming the saved adapter appears in the resolved spec artifact in `.documentation/devspark/runs/<run-id>/spec.resolved.yaml`.

**Acceptance Scenarios**:

1. **Given** a valid adapter name, **When** the user runs `devspark adapter default <name>`, **Then** the preference is saved and confirmed in the terminal
2. **Given** a saved adapter preference, **When** a spec is run without an explicit adapter field, **Then** the saved preference is used and visible in the resolved spec artifact
3. **Given** an unknown adapter name, **When** the user runs `devspark adapter default <invalid>`, **Then** the command lists available adapters and exits with failure

---

### User Story 5 — Check System Health (Priority: P4)

A developer setting up DevSpark on a new machine wants to confirm their environment is ready before running harness workflows. They run `devspark doctor`. The command checks each prerequisite, shows pass/fail for each, and — for any failure — prints a specific remediation step or install URL.

**Why this priority**: Environment diagnosis saves significant setup time. Without it, missing prerequisites produce cryptic failures inside a run rather than a clear upfront message.

**Independent Test**: Can be fully tested on both a complete and an intentionally incomplete environment, confirming each check reports the correct status and that failures include actionable remediation hints.

**Acceptance Scenarios**:

1. **Given** all prerequisites are met, **When** the user runs `devspark doctor`, **Then** every check shows pass and the command exits successfully
2. **Given** a required CLI tool is not installed, **When** the user runs `devspark doctor`, **Then** that check shows fail with an install URL or install command for that tool
3. **Given** the user is working from a source checkout that has `.documentation/`, `pyproject.toml`, and `src/devspark_cli/` but no installed `.devspark/` payload, **When** the user runs `devspark doctor`, **Then** the command recognizes the source-checkout layout as valid and does not fail solely because `.devspark/` is absent
4. **Given** neither an installed `.devspark/` payload nor a compatible source-checkout layout is present, **When** the user runs `devspark doctor`, **Then** the command reports the missing layout and instructs the user to run `devspark init`

---

### User Story 6 — Existing Commands Work Unchanged (Priority: P1)

A developer who has never used the harness feature continues using `devspark init`, `devspark upgrade`, and all registry commands exactly as before. No new flags, no migration steps, no configuration changes required.

**Why this priority**: Backward compatibility is a non-negotiable constitutional principle. Any regression here is a showstopper.

**Independent Test**: Run the full existing command suite and confirm output and behavior are identical to the pre-harness baseline across all supported commands.

**Acceptance Scenarios**:

1. **Given** an existing DevSpark installation, **When** the harness feature is added, **Then** all pre-existing commands (`init`, `upgrade`, `registry add/list/validate`) produce identical output and behavior
2. **Given** a repository with no harness spec file, **When** any pre-existing DevSpark command is run, **Then** no harness-related messages, prompts, or errors appear

---

### Edge Cases

- What happens when a harness spec references a prompt file that does not exist on disk?
- What happens when the run artifacts directory is not writable?
- When a `human_gate` step is encountered in a non-interactive (CI) context, the run fails with a clear manual-gate-requires-TTY message rather than skipping the gate; users should use `--dry-run` for CI authoring checks.
- When the user interrupts a run mid-step (Ctrl+C), the harness preserves all artifacts written so far, sets the run status to `aborted`, and `devspark harness trace` displays the partial event log up to the point of interruption.
- What happens when `devspark harness trace latest` is called but the most recent run's event log is corrupted or incomplete?
- What happens when `devspark adapter default` is called with a valid adapter name whose CLI is not currently installed?

---

## Requirements *(mandatory)*

### Functional Requirements

**Harness Execution**

- **FR-001**: The system MUST load and parse a harness spec file when the user runs `devspark harness run <spec.yaml>`
- **FR-002**: The system MUST execute steps in the order declared in the harness spec
- **FR-003**: The system MUST validate each step's output according to the validation rules declared for that step
- **FR-004**: On validation failure, the system MUST inject the failure details as feedback and retry the step, up to the maximum attempts declared in the step's retry policy
- **FR-005**: The system MUST stop execution and write a failed result when a step exhausts its retry attempts
- **FR-006**: The system MUST write run artifacts to `.documentation/devspark/runs/<run-id>/` for every run, including the resolved spec, event log, per-step outputs, and final result
- **FR-007**: The system MUST use the noop adapter when no adapter is specified in the spec and no user default is set

**Spec Validation**

- **FR-008**: The system MUST validate a harness spec file against the declared schema when the user runs `devspark harness validate <spec.yaml>`
- **FR-009**: The system MUST report each validation error with the field name and a corrective suggestion
- **FR-010**: The system MUST exit without executing any steps when running `devspark harness validate`

**Run Inspection**

- **FR-011**: The system MUST display the event log of a run as a structured table when the user runs `devspark harness trace <run-id>`
- **FR-012**: The system MUST accept `latest` as a valid run-id, resolving to the most recently recorded run
- **FR-013**: The event table MUST include at minimum: step id, attempt number, status, and duration

**Adapter Management**

- **FR-014**: The system MUST list all available execution adapters when the user runs `devspark adapter list`
- **FR-015**: The system MUST save the user's adapter preference to a user-level config location when the user runs `devspark adapter default <name>`
- **FR-016**: The saved adapter preference MUST survive `devspark upgrade` (stored outside the framework install directory)
- **FR-017**: The system MUST validate the adapter name and report available options if the name is unknown

**System Health**

- **FR-018**: The system MUST check each prerequisite and display a pass/fail status when the user runs `devspark doctor`
- **FR-019**: For each failed check, the system MUST display a specific remediation step or install URL
- **FR-020**: `devspark doctor` MUST be read-only and MUST NOT modify any files or system state

**Backward Compatibility**

- **FR-021**: All existing CLI commands (`init`, `upgrade`, `registry add`, `registry list`, `registry validate`) MUST produce identical behavior after this feature is added
- **FR-022**: All existing imports from the `devspark_cli` package MUST remain valid without modification
- **FR-023**: The harness runtime MUST NOT require configuration or migration from repositories not using harness specs

**Reference Materials**

- **FR-024**: A sample harness spec file MUST be included in the repository demonstrating all supported step types
- **FR-025**: A machine-readable schema for harness spec files MUST be placed at `.devspark/schemas/harness.schema.json`
- **FR-026**: When a run is interrupted by the user (e.g., Ctrl+C), the system MUST preserve all run artifacts written so far, set the run status to `aborted`, and ensure `devspark harness trace` can display the partial event log
- **FR-027**: The system MUST refuse to load or execute a harness spec whose declared `apiVersion` does not equal the CLI's supported version constant (`devspark.ai/v1`), and MUST report the mismatch along with the supported version value
- **FR-028**: After each completed run (any terminal status), the system MUST delete the oldest run directories in `.documentation/devspark/runs/` when the stored run count exceeds the configured retention limit
- **FR-029**: The run retention limit MUST default to 20 and MUST be overridable via the user-level config (the same config file used by `devspark adapter default`)

**Output & Exit Codes**

- **FR-030**: All harness commands MUST auto-detect whether a TTY is attached and adjust output accordingly: rich formatted output when a TTY is present; plain-text output when no TTY is detected (CI, piped output)
- **FR-031**: `devspark harness run` MUST exit with code 0 when a run reaches status `complete`, and a non-zero exit code when the run reaches status `failed` or `aborted`
- **FR-032**: The exit code contract MUST be documented in the CLI help text for `devspark harness run`

**Security**

- **FR-033**: Run artifacts in `.documentation/devspark/runs/` are repository-owned user documents; the framework MUST NOT add, modify, or remove any `.gitignore` entries for this path — version control of run artifacts is the user's decision

**Dry-Run Mode**

- **FR-034**: `devspark harness run --dry-run` MUST validate the spec, emit a run directory with `events.jsonl` and `result.json`, and mark all steps as `skipped_dry_run` without executing any adapter, shell command, or validation rule
- **FR-035**: Dry-run MUST succeed on any valid spec regardless of adapter availability or system state, making it safe to use in spec authoring and CI pre-checks

**Manual Adapter**

- **FR-036**: The `manual` adapter MUST render a formatted prompt block to the terminal that the user can copy and paste into any IDE agent; it MUST NOT require any installed AI tool or CLI
- **FR-037**: When a step uses the `manual` adapter in an interactive session, the run MUST pause and wait for the user to signal completion (e.g., press a key) before recording the step result and continuing; when no TTY is present, the run MUST fail with a clear explanation rather than skipping the gate

**Multi-App Scope**

- **FR-038**: A harness spec MAY declare `scope: type: app` along with an app identifier to run within the context of a registered application from the multi-app registry
- **FR-039**: When `scope: app` is declared, the harness MUST resolve context, constitution, and output paths relative to that application's documentation root (consistent with `--app <id>` conventions elsewhere in the CLI)

**Validation Rules**

- **FR-040**: The validation engine MUST support the following built-in rule types: `file.exists`, `file.contains`, `command.exit_code`, `json.schema`, `git.clean`, `regex.match`, `always.pass`
- **FR-041**: Each validation rule MUST declare a severity (`error` or `warning`); `error`-severity failures MUST stop the run (triggering retry or failure); `warning`-severity findings MUST be recorded but MUST NOT block execution

**Telemetry**

- **FR-042**: Every run MUST emit the following named event types to `events.jsonl`: `harness.run.started`, `harness.run.finished`, `harness.step.started`, `harness.step.finished`, `harness.step.validation`, `harness.tool.called`, `harness.policy.blocked`
- **FR-043**: Each `StepResult` in `result.json` MUST include the per-rule validation findings and an artifact delta recording which files were created, modified, or deleted during that step

### Key Entities *(feature involves data)*

- **HarnessSpec**: A declarative definition of a multi-step automated workflow. Fields: `apiVersion` (e.g. `devspark.ai/v1`), `kind` (`HarnessSpec`), `name`, `scope` (repo or app), `defaults`, `steps`, and `telemetry`. The `apiVersion` field is enforced: a spec whose declared `apiVersion` does not equal the CLI's supported version constant is rejected with a clear mismatch error rather than silently misinterpreted. The `scope` field integrates with the multi-app registry so a harness spec can be scoped to a specific registered application using `--app <id>`.
- **Step**: A single unit of work within a HarnessSpec. Has a type (`agent_task`, `validation`, `human_gate`), an execution mode (`agent`, `manual`), an optional adapter override, an optional prompt reference, explicit `inputs` and `outputs` file lists, validation rules, a retry policy, and routing for success and failure. Validation steps are rule-driven and do not invoke an adapter.
- **ValidationRule**: A single check applied after a step completes. Supported types: `file.exists`, `file.contains`, `command.exit_code`, `json.schema`, `git.clean`, `regex.match`, `always.pass`. Each rule has a severity (`error` stops the run; `warning` is recorded but does not block). Higher-level validations (build, unit-tests, lint) are expressed as `command.exit_code` rules rather than standalone shell/function steps in v1.
- **RetryPolicy**: Declares `maxAttempts`, `backoff` strategy (`none`, `fixed`, `exponential`), `retryOn` triggers (`validation_fail`, `tool_error`, `timeout`), `requireHumanAfter` (attempt threshold at which execution pauses for human review), and an optional `repairPrompt` file injected on retry.
- **Run**: A single execution of a HarnessSpec. Has a unique ID, a status (`running`, `complete`, `failed`, `aborted`), start/finish timestamps, summary metrics, and a list of StepResults. Status `aborted` is set when the user interrupts execution; status `failed` is set when a step exhausts its retry attempts.
- **StepResult**: The outcome of one attempt at a step. Records attempt number, status, duration, adapter used, per-rule validation findings, and artifact delta (`created`, `modified`, `deleted` file lists).
- **Adapter**: The execution target for `agent_task` steps. Three built-in adapters: `noop` (always succeeds, no AI required — for wiring and CI); `manual` (renders a formatted copy/paste prompt block for the user to execute in their IDE agent and blocks the run when no TTY is present); named adapters (`claude_code`, `copilot`, `cursor`) that invoke the corresponding agent CLI (Phase 4).
- **TelemetryEvent**: A single append-only entry in `events.jsonl`. Named event types: `harness.run.started`, `harness.run.finished`, `harness.step.started`, `harness.step.finished`, `harness.step.validation`, `harness.tool.called`, `harness.policy.blocked`.
- **RunArtifact**: The complete set of files written to `.documentation/devspark/runs/<run-id>/` for a given run, including `spec.resolved.yaml`, `context.json`, `events.jsonl`, per-step outputs under `steps/`, and `result.json`. The system retains at most N run directories (default 20, configurable); the oldest is deleted when the limit is exceeded.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can execute a complete multi-step harness workflow with no AI tool installed (noop adapter) and receive a well-formed result in under 5 seconds
- **SC-002**: All existing DevSpark commands produce identical output after the harness feature ships — zero behavioral regressions detectable by running the existing command suite
- **SC-003**: A harness spec with a failing validation step is automatically retried; the retry count and final status are visible via `devspark harness trace latest` without additional user action
- **SC-004**: `devspark harness validate` catches a malformed spec with a missing required field, names the field, and exits in under 2 seconds — before any execution begins
- **SC-005**: `devspark doctor` reports a specific install URL for every missing CLI tool that declares an install URL, requiring no manual lookup by the user
- **SC-006**: A user's `devspark adapter default` preference survives `devspark upgrade` and is applied on the next run without re-entry
- **SC-007**: The sample harness spec and generated schema together are sufficient for a new user to author a valid harness spec without reading source code
- **SC-008**: A CI pipeline can integrate `devspark harness run` using only the exit code (0 = success, non-zero = failure) with no TTY-specific configuration required

---

## Assumptions

- If the CLI is running against an installed project layout, the framework install directory (`.devspark/`) is writable by the user running the CLI
- The user-level config directory is writable on all supported platforms (Windows, macOS, Linux)
- Concurrent run safety is out of scope for Phases 1–3; run IDs use timestamp and random suffix to avoid collision in practice
- `context.kind: registry` is deferred — not in scope for Phases 1–3
- Stretch goals (run replay, output diff, telemetry export, parallel step execution) are out of scope for this spec
