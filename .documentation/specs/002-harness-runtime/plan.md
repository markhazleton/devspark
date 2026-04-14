# Implementation Plan: DevSpark Harness Runtime

**Branch**: `002-harness-runtime` | **Date**: 2026-04-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `.documentation/specs/002-harness-runtime/spec.md`

## Rationale Summary

### Core Problem

DevSpark orchestrates AI-assisted development via prompts and slash commands that a human must invoke manually in sequence. There is no mechanism to define a repeatable, multi-step workflow, validate each step automatically, retry on failure, or produce a traceable audit record.

### Decision Summary

Add an optional `harness` CLI subcommand group and supporting runtime modules to DevSpark. Users author declarative YAML specs; the harness executes steps, validates results, retries with injected feedback, and persists structured run artifacts to `.documentation/devspark/runs/`. All existing CLI behavior is unchanged.

### Key Drivers

- Repeatability: teams want a single command to execute a full specify→plan→implement→validate cycle
- Observability: structured event logs (`events.jsonl`) and result summaries (`result.json`) are inspectable after the fact
- CI integration: noop and manual adapters make harness specs runnable without an AI tool

### Source Inputs

- [spec.md](spec.md) — 43 FRs, 9 entities, 8 success criteria
- [research.md](research.md) — harness engineering patterns, adapter interface, validation best practices, telemetry naming
- DevSpark Constitution v1.0.0
- Existing CLI patterns: `registry.py`, `resolution.py`, `scope.py`, `agent_registry.py`

### Tradeoffs Considered

- Option A: Flat new modules in `src/devspark_cli/` — rejected; runner + adapters + validation + telemetry in flat modules exceeds 600 lines before Phase 3 and is closed to adapter extension
- Option B: Separate installable package — rejected; violates the additive-only constraint; breaks existing imports
- Selected: `src/devspark_cli/harness/` sub-package — clean module boundaries, independently testable, all imports additive

### Architectural Impact

- New `devspark harness` Typer subcommand group wired into existing CLI via one `app.add_typer()` call in `__init__.py`
- Run artifacts written to `.documentation/devspark/runs/<run-id>/` — repository-owned, never under `.devspark/`
- `devspark adapter` and `devspark doctor` added as top-level commands alongside existing `init`, `upgrade`, `registry`
- User config stored via `platformdirs.user_config_dir("devspark")` — survives upgrades
- New dependency: `PyYAML` for YAML spec loading
- No existing module modified beyond one `add_typer()` call; no existing import broken

### Reviewer Guidance

Review for: (1) zero changes to existing command behavior; (2) run artifacts exclusively in `.documentation/devspark/runs/`; (3) noop adapter succeeds without network or AI access; (4) `--dry-run` exits cleanly on any valid spec; (5) FR-027 version enforcement rejects unsupported `apiVersion` values.

---

## Summary

Implement an additive `devspark harness` runtime as a self-contained sub-package with Pydantic domain models, a YAML loader, a step runner, an adapter protocol, a validation engine, and a telemetry sink. Wire harness subcommands and two top-level commands (`adapter`, `doctor`) into the existing CLI. Deliver in four dependency-ordered phases.

---

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: typer, rich, pydantic v2, platformdirs, readchar (all existing); PyYAML (new)
**Storage**: Files only — YAML specs (user-authored), JSONL + JSON run artifacts under `.documentation/devspark/runs/`, JSON Schema under `.devspark/schemas/`
**Testing**: Standalone contract test scripts (existing repo pattern); fixtures under `tests/fixtures/harness/`
**Target Platform**: Windows, macOS, Linux (same as existing CLI)
**Project Type**: CLI tool extension (additive sub-package)
**Performance Goals**: noop dry-run <5s (SC-001); `devspark harness validate` <2s (SC-004)
**Constraints**: Additive only — FR-021–023 enforce zero behavioral changes to existing commands
**Scale/Scope**: Local dev tool; default 20 stored runs; no network required for noop/manual adapters

---

## Constitution Check

*GATE: Evaluated pre-design and confirmed post-design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Backward Compatibility (NON-NEGOTIABLE) | PASS | One `add_typer()` call is the only touch to an existing file |
| Explicit Over Implied (NON-NEGOTIABLE) | PASS | Declarative YAML specs; FR-027 rejects ambiguous apiVersions; scope always explicit |
| Ownership Boundary (NON-NEGOTIABLE) | PASS | Runs → `.documentation/devspark/runs/` (user); schema → `.devspark/schemas/` (framework) |
| Governance Authority | PASS | App-scoped runs (FR-038–039) route constitution via existing `resolution.py` chain |
| Simplicity | JUSTIFIED | `harness/` sub-package: 6 modules with single responsibilities; flat alternative rejected (see Complexity Tracking) |
| Platform Parity | N/A | Harness subcommands are Python CLI only; no shell script equivalents needed |

## Complexity Tracking

| Addition | Why Needed | Simpler Alternative Rejected Because |
|----------|------------|--------------------------------------|
| `harness/` sub-package (6 modules) | Runner, adapters, validation, and telemetry have distinct extension points | Single `harness.py` would exceed 600 lines before Phase 3; adapter extension would require touching core runner |
| `ValidationRule` entity with 7 types | Each rule has distinct inputs and deterministic, independently testable behavior | Single `validate()` with if/elif chain is closed to new rule types and untestable per-rule |
| Separate `telemetry.py` | Event emission must be independently testable and replaceable (future OTel) | Inline event writes in `runner.py` would couple telemetry to runner, blocking future OTel integration |

---

## Project Structure

### Documentation (this feature)

```text
.documentation/specs/002-harness-runtime/
├── plan.md                          ← this file
├── spec.md
├── research.md                      ← Phase 0 (complete)
├── data-model.md                    ← Phase 1 output
├── contracts/
│   ├── harness-spec-yaml.md         ← HarnessSpec YAML format
│   ├── cli-commands.md              ← CLI input/output contracts
│   └── events-schema.md             ← events.jsonl + result.json
├── checklists/
│   └── requirements.md
└── tasks.md                         ← /devspark.tasks output (not created here)
```

### Source Code

```text
src/devspark_cli/
├── harness/                         ← NEW sub-package
│   ├── __init__.py
│   ├── spec_models.py               ← Pydantic domain models (Phase 1)
│   ├── spec_loader.py               ← YAML/JSON loader + path resolution (Phase 1)
│   ├── runner.py                    ← HarnessRunner orchestration (Phase 2)
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py                  ← AgentAdapter protocol (Phase 2)
│   │   ├── noop.py                  ← NoopAdapter (Phase 2)
│   │   └── manual.py               ← ManualAdapter copy/paste (Phase 2)
│   ├── validation.py                ← ValidationEngine + 7 rule types (Phase 3)
│   ├── telemetry.py                 ← TelemetrySink → events.jsonl (Phase 2)
│   └── cli.py                       ← Typer subapp: harness run/validate/trace (Phase 2)
├── __init__.py                      ← MODIFIED: add_typer(harness_app) + adapter/doctor (Phase 2/4)
├── [all existing modules — UNCHANGED]

tests/
├── fixtures/harness/
│   ├── valid_minimal.yaml           ← minimal valid spec (Phase 1)
│   ├── valid_all_steps.yaml         ← all step types (Phase 1)
│   └── invalid_missing_field.yaml   ← triggers FR-009 error (Phase 1)
├── test_harness_spec_contract.py    ← Phase 1
├── test_harness_runner_contract.py  ← Phase 2
└── test_harness_validation_contract.py  ← Phase 3

sample.harness.yaml                  ← repo root reference file (Phase 1)

.devspark/schemas/
└── harness.schema.json              ← generated from Pydantic models (Phase 1)

.documentation/devspark/runs/        ← runtime output, user-owned (created on first run)
```

---

## Implementation Phases

### Phase 1 — Domain Models, Schema, Sample File

**Goal**: All Pydantic models, YAML loader, JSON Schema file, sample spec, and contract tests. No CLI changes.

**Deliverables**:
- `src/devspark_cli/harness/__init__.py`, `spec_models.py`, `spec_loader.py`
- `.devspark/schemas/harness.schema.json`
- `sample.harness.yaml`
- `tests/fixtures/harness/` (3 fixtures)
- `tests/test_harness_spec_contract.py`

**Acceptance**: `python tests/test_harness_spec_contract.py` exits 0; valid fixtures parse without error; invalid fixture fails with the missing field name in the error message; `harness.schema.json` is valid JSON Schema draft 2020-12.

**Key decisions**:
- `apiVersion: devspark.ai/v1` only; CLI constant `SUPPORTED_API_VERSION = "devspark.ai/v1"`; any other value → FR-027 error
- YAML loaded with `PyYAML` `safe_load`; JSON as fallback detected by `.json` extension
- Relative paths in spec normalized to absolute against `repo_root` at load time
- Schema generated via `HarnessSpec.model_json_schema()` and written by a `make-schema` helper or Phase 2 `validate` command

---

### Phase 2 — Runner, Adapters, CLI, Telemetry, Artifact Persistence

**Goal**: `devspark harness run`, `devspark harness validate`, `devspark harness trace`, and `devspark adapter` working end-to-end with noop and manual adapters.

**Deliverables**:
- `harness/runner.py` — HarnessRunner: load spec → resolve context → execute steps → write artifacts
- `harness/adapters/base.py`, `noop.py`, `manual.py`
- `harness/telemetry.py` — TelemetrySink emitting 7 named event types to `events.jsonl`
- `harness/cli.py` — Typer subapp: `run [--dry-run]`, `validate`, `trace <run-id|latest>`
- `__init__.py` — `app.add_typer(harness_app, name="harness")` + `adapter list/default` commands
- `tests/test_harness_runner_contract.py`

**Acceptance**: `devspark harness run sample.harness.yaml` writes `result.json` with `status: complete`; `--dry-run` writes `skipped_dry_run` steps; `devspark harness trace latest` renders table; exit code 0 on complete, non-zero on failed/aborted; `devspark adapter list` prints registered adapters.

**Key decisions**:
- Run ID: `run_<YYYYMMDDTHHMMSSZ>_<6-char-hex>` e.g. `run_20260414T193000Z_a1b2c3`
- Retention: after each run, scan `.documentation/devspark/runs/`, sort by mtime, delete oldest when count > limit; never delete status `running`
- Manual adapter: render Rich Panel with step prompt, call `readchar.readkey()` (existing dep) to wait for keypress, then record `complete`; if no TTY → record `skipped_no_tty` without blocking
- TTY detection: `sys.stdout.isatty()` → rich output when True, plain-text when False
- User config: `platformdirs.user_config_dir("devspark") / "config.json"` as JSON dict

---

### Phase 3 — Validation Engine, Feedback Loop, doctor

**Goal**: All 7 validation rule types; retry loop injects errors into repair prompt; `devspark doctor` health checks.

**Deliverables**:
- `harness/validation.py` — ValidationEngine + rule implementations
- `runner.py` updated — retry loop: on `error`-severity failure → render repair prompt → re-execute step
- `__init__.py` — `devspark doctor` command
- `tests/test_harness_validation_contract.py`

**Acceptance**: Spec with a `file.exists` rule on a missing path triggers retry to `maxAttempts`; `devspark harness trace latest` shows multiple attempt rows per step; `devspark doctor` exits 0 on healthy system; exits non-zero with install URL for any missing `requires_cli` tool.

**Key decisions**:
- Repair prompt injection: load `retryPolicy.repairPrompt` file, append `## Validation Errors\n<bullet list>` block, pass as augmented prompt to next adapter `execute()` call
- `command.exit_code`: `subprocess.run(shell=True)`; stdout/stderr captured to `steps/<step-id>/stdout.txt`
- `git.clean`: `git status --porcelain`; fail if non-empty output; configurable path filter via rule `path` field
- `always.pass`: returns `passed` unconditionally (wiring and dry-run testing)
- `doctor` checks (in order): Python ≥3.11, pydantic importable, `.devspark/` exists, `agents-registry.json` readable, git (`shutil.which("git")`), then per-agent checks from registry `requires_cli` + `install_url`

---

### Phase 4 — Real Agent Adapters, Multi-App Scope

**Goal**: Claude Code, Copilot, Cursor adapters; harness specs scoped to registered applications.

**Deliverables**:
- `harness/adapters/claude_code.py`, `copilot.py`, `cursor.py`
- `runner.py` updated — if spec `scope.type == "app"`, load registry, resolve app doc root via `scope.resolve_doc_root()`
- `adapter list` shows `is_available()` status per adapter

**Acceptance**: All Phase 1–3 acceptance criteria still pass; `devspark harness run` with `adapter: claude_code` invokes claude CLI; spec with `scope.app: my-app` resolves constitution from `my-app/.documentation/memory/constitution.md`.

**Key decisions**:
- Claude Code adapter: `subprocess.run(["claude", "--print", prompt_text])`, capture output to step artifact
- `is_available()`: `shutil.which(agent_cli_name) is not None`
- App scope resolution: reuse `scope.resolve_doc_root(app, repo_root)` from existing `scope.py` — no new resolution logic needed

---

## Dependency Map

```
Phase 1: spec_models.py, spec_loader.py
            ↓
Phase 2: runner.py + adapters/* + telemetry.py + cli.py + __init__.py wiring
            ↓
Phase 3: validation.py (integrated into runner.py) + doctor command
            ↓
Phase 4: adapters/claude_code.py + copilot.py + cursor.py + scope integration
```

Each phase is independently shippable. Phase N can be in production while Phase N+1 is in development.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| `__init__.py` change breaks existing commands | Low | High | Single `add_typer()` only; run full existing command suite in contract tests |
| Path separator differences on Windows | Medium | Medium | All paths via `pathlib.Path`; test fixtures use forward-slash strings |
| `manual` adapter blocks indefinitely in CI | Medium | High | TTY detection before `readchar`; no-TTY path records `skipped_no_tty` without blocking |
| PyYAML `safe_load` rejects valid YAML edge cases | Low | Low | Pydantic validation gives clear field-level errors regardless |
| Retention pruning deletes in-use run directory | Low | Medium | Never delete status `running`; sort by mtime; atomic directory rename before delete |
| Phase 4 agent CLIs change their invocation API | Medium | Medium | Adapter per agent; change is isolated to one file; `is_available()` guards at runtime |
