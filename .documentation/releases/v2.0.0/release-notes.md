# Release Notes: v2.0.0 — Harness

## Release Metadata

- **Version**: v2.0.0
- **Release Date**: 2026-04-16
- **Release Window**: 2026-04-12 → 2026-04-16
- **Previous Version**: v1.6.0
- **Commits**: 40
- **Contributors**: 3 (Mark Hazleton, copilot-swe-agent[bot], DevSpark Test)
- **Merged PRs**: 4 (#20, #21, #22, #24)
- **Files Changed**: 105
- **Lines Added**: ~9,743
- **Lines Removed**: ~358

## Highlights

DevSpark 2.0 is the largest release since the project's inception. It introduces the **Harness Runtime** — a declarative, adapter-driven execution engine that turns YAML workflow specifications into reproducible, validated AI-agent pipelines. Where DevSpark 1.x gave your AI assistant a vocabulary of 27 slash commands, 2.0 adds the ability to orchestrate those commands into multi-step workflows that execute, validate, retry, and report — all from a single YAML file.

This release also hardens the existing command surface: PR reviews now enforce mandatory testing checks and severity classification, all 20 stock command templates support 2-tier script resolution (team overrides take priority over stock), and the release tooling gains archive-recovery capabilities for reconstructing release context from git history.

The Harness subsystem ships production-ready with five pluggable adapters (Copilot, Claude Code, Cursor, manual, and noop), a validation engine supporting eight rule types, plan/act execution modes, artifact delta tracking, and structured telemetry — backed by 10+ new contract test modules.

## New Features

### Harness Runtime Engine

The centerpiece of v2.0. A complete YAML-driven workflow engine integrated into the DevSpark CLI.

- **`devspark harness run`** — Execute a harness spec end-to-end with automatic retry, validation, and telemetry
- **`devspark harness replay`** — Re-run a completed harness from its saved artifact directory
- **`devspark harness validate`** — Check spec structure without execution
- **`devspark harness trace`** — Inspect the JSONL event log from a prior run
- **`devspark adapter list`** / **`adapter set-default`** / **`adapter get-default`** — Manage preferred adapters
- **`devspark doctor`** — Verify the local environment is ready for harness workflows

**Spec**: [View archived spec](specs/002-harness-runtime/spec.md)

### Declarative YAML Spec Format (`HarnessSpec`)

Define complete workflows in `apiVersion: devspark.ai/v1` documents:

- **Scopes**: Repository-wide (`scope.type: repo`) or app-targeted (`scope.type: app`) from the multi-app registry
- **Steps**: Three step types — `agent_task`, `validation`, `human_gate`
- **Validation Rules**: Eight built-in rule types:
  - `always.pass` — Constant pass (useful for placeholders)
  - `file.exists` — Assert a file is present
  - `file.contains` — Assert a file contains a substring
  - `command.exit_code` — Run a shell command and check exit code
  - `json.schema` — Validate a file against a JSON Schema
  - `git.clean` — Assert no uncommitted changes in a path
  - `regex.match` — Match file content against a regex
  - `llm.rubric` — LLM-evaluated quality rubric (plan-mode aware)
- **Retry Policies**: Per-step `maxAttempts`, `backoff` (none/fixed/exponential), `retryOn` triggers, `requireHumanAfter` threshold, and `repairPrompt` for auto-escalation
- **Telemetry**: JSONL event logs and structured `run.json` under `.documentation/devspark/runs/`

### Pluggable Adapter Architecture

Five built-in adapters ship with v2.0, all implementing the `AgentAdapter` protocol:

| Adapter | Description |
|---------|-------------|
| `copilot` | GitHub Copilot Chat integration |
| `claude_code` | Claude Code CLI integration |
| `cursor` | Cursor Composer integration |
| `manual` | Human-in-the-loop with clipboard prompt delivery |
| `noop` | Dry-run adapter for testing and CI |

Custom adapters can be added by implementing the `AgentAdapter` protocol.

### Execution Modes

- **`--mode act`** (default) — Full write-enabled execution
- **`--mode plan`** — Read-only mode; side-effectful commands (`command.exit_code`) are skipped, agent prompts are prefixed with plan-mode instructions ("do NOT write, create, or modify any files")

### Artifact Delta Tracking

Every step automatically snapshots declared outputs before and after execution, recording:

- **Created** files — new outputs that didn't exist before
- **Modified** files — existing outputs whose mtime or size changed
- **Deleted** files — outputs that disappeared during execution

### Deterministic-First Step Ordering

When dependencies allow, validation-only steps run before agent tasks, providing fast feedback before expensive LLM calls.

### Context Budget Enforcement

Adapters respect `context_budget` hints to keep prompts within model context windows, preventing truncation on large input sets.

### Comprehensive Contract Tests

10+ new test modules validate the harness subsystem end-to-end:

| Test Module | Coverage |
|-------------|----------|
| `test_harness_spec_contract.py` | Spec loading, YAML/JSON parsing, schema validation |
| `test_harness_validation_contract.py` | All 8 validation rule types, enabled/disabled flags, plan-mode behavior |
| `test_harness_adapters_contract.py` | Adapter protocol conformance, registry, plan-mode prefix, context budget |
| `test_harness_runner_contract.py` | Runner lifecycle, CLI help text, exit codes |
| `test_release_context_recovery.py` | Archive recovery, PR review stats, release-history scripts |
| `test_create_pr_preflight.py` | PR preflight validation lifecycle |
| `test_script_parity_contract.py` | Bash/PowerShell script parity |
| `test_script_resolution_contract.py` | 2-tier resolution across 20 templates |
| `test_prompt_gate_contract.py` | Prompt gate validation |

## Improvements

### PR Review Hardened (PR #20)

`/devspark.pr-review` now enforces:

- Mandatory testing checks — PRs without tests are flagged
- Behavioral regression detection — changes to existing behavior require justification
- Severity classification — findings are categorized as Critical, High, Medium, Low

### 2-Tier Script Resolution (PR #21)

All 20 stock command templates now resolve scripts via a two-tier fallback:

1. **Team override**: `.documentation/scripts/{bash|powershell}/{filename}` (checked first)
2. **Stock default**: `.devspark/scripts/{bash|powershell}/{filename}` (fallback)

This enables teams to customize context-gathering scripts without forking the framework.

### Release Context Recovery

Release-context and release-history scripts now recover specs and quickfixes from:

- Archive directories (`.archive/<date>/`)
- Git history (when artifacts have been deleted)
- PR review metadata (files changed, tests added, breaking changes)

### PowerShell Release-History Parity

New `release-history-context.ps1` script matches the Bash `release-history-context.sh` for consistent cross-platform release analysis.

## Bug Fixes

- **pyproject.toml corruption** — Restored canonical `pyproject.toml` after it was overwritten by test fixture commits (was a single-line stub with `name = "test"`)
- **specify.md list numbering** — Script resolution blockquote in `specify.md` indented properly to avoid breaking ordered-list rendering
- **Frontmatter parsing** — Test fixtures hardened with `len(parts)==3` guard to prevent false failures on edge-case YAML frontmatter

## Breaking Changes

This is a **major version bump** (1.x → 2.0) because the Harness Runtime introduces a new subsystem with its own API surface, spec format, and CLI commands. However, there are **no breaking changes to existing behavior**:

- All 27 existing slash commands work identically
- All existing scripts, templates, and workflows are unchanged
- The Harness is purely additive — it extends the CLI without modifying any existing paths

The major version bump reflects the significance and scope of the addition rather than API breakage.

## Merged Pull Requests

| PR | Title | Branch | Type |
|----|-------|--------|------|
| #20 | Harden PR review defaults | `copilot/feat-harden-pr-review-defaults` | Feature |
| #21 | Fix script resolution issue | `copilot/fix-script-resolution-issue` | Fix |
| #22 | Harness runtime implementation | `002-harness-runtime` | Feature (major) |
| #24 | Harness validation & v2 features | `harness_validation` | Feature |

## Commit Breakdown

| Category | Count | Key Commits |
|----------|-------|-------------|
| Harness features | 7 | spec models, validation engine, adapters, runner, CLI, replay, modes |
| Harness tests | 1 | contract tests and v2 implementation plan |
| PR review hardening | 1 | mandatory testing, regression detection, severity |
| Script resolution | 4 | 2-tier resolution in 20 templates, frontmatter fixes |
| Release tooling | 3 | release-history scripts, archive recovery |
| Documentation | 5 | harness engineering guide, README refresh, FAQ updates |
| Infrastructure | 4 | version bumps, pyproject fix, spec validation contract |
| Merge commits | 4 | PRs #20, #21, #22, #24 |

## File Change Summary

| Category | Files | Lines Added | Description |
|----------|-------|-------------|-------------|
| Harness runtime (`src/devspark_cli/harness/`) | 15 | ~2,093 | Core engine: models, loader, runner, validation, CLI, adapters, telemetry, config |
| Harness spec & docs (`.documentation/specs/002-harness-runtime/`) | 10 | ~3,295 | Full spec, plan, tasks, research, contracts, checklists, gates |
| Tests (`tests/`) | 11 | ~1,300 | Contract tests for spec, validation, adapters, runner, recovery, parity |
| Scripts (`scripts/`) | 8 | ~1,400 | Release context/history (Bash + PowerShell), create-pr, archive updates |
| Templates (`templates/commands/`) | 20 | ~240 | 2-tier resolution blocks, pr-review hardening |
| Documentation (`.documentation/`) | 8 | ~340 | Harness engineering guide, FAQ, index, quickstart, installation |
| Schema (`.devspark/`) | 1 | 470 | `harness.schema.json` — full JSON Schema for HarnessSpec |
| Other | 12 | ~200 | README, pyproject, quickstarts, sample.harness.yaml, fixtures |
| **Total** | **105** | **~9,743** | |

## Architectural Decisions

### ADR: Declarative YAML over Imperative Scripts

The Harness uses declarative YAML specs rather than imperative shell scripts for workflow orchestration. This enables validation-before-execution, deterministic ordering, replay, and cross-adapter portability.

**Source**: Spec 002-harness-runtime | **Decision**: Accepted

### ADR: Adapter Protocol Pattern

Agent integrations use a Python Protocol (`AgentAdapter`) with `name`, `is_available()`, and `execute()` methods. This allows adding new agents without modifying the runner and keeps adapters independently testable.

**Source**: Spec 002-harness-runtime | **Decision**: Accepted

### ADR: Plan/Act Execution Modes

Instead of separate "dry-run" and "real" codepaths, the harness uses a single execution flow with mode-aware behavior. Plan mode skips side-effectful validations and prefixes prompts with instructions not to write files.

**Source**: Spec 002-harness-runtime | **Decision**: Accepted

## Metrics

| Metric | Value |
|--------|-------|
| Features Delivered | 1 major (Harness Runtime), 2 enhancements |
| Bugs Fixed | 3 |
| PRs Merged | 4 |
| Files Changed | 105 |
| Lines Added | ~9,743 |
| Lines Removed | ~358 |
| Net New Lines | ~9,385 |
| New Source Files | 15 (harness runtime) |
| New Test Files | 11 |
| ADRs Created | 3 |
| Contributors | 3 |
| Commits | 40 |
| New CLI Commands | 6 (harness run/replay/validate/trace, adapter list/default) |
| Validation Rule Types | 8 |
| Agent Adapters | 5 |

---

*Release documentation generated by /devspark.release*
