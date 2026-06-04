# Implementation Plan: Tiered Prompt and Workflow Engine

**Branch**: `001-interactive-analyze-flow` | **Date**: 2026-04-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/.documentation/specs/001-interactive-analyze-flow/spec.md`
**Status**: Complete — Merged via PR [#28](https://github.com/markhazleton/devspark/pull/28) on 2026-04-18.

## Rationale Summary

### Core Problem

DevSpark today is a curated prompt library with implicit orchestration. Users must hand-stitch sequences (`/devspark.specify` → `/devspark.plan` → `/devspark.tasks` …), autonomy boundaries are unwritten, and there is no shared step-level telemetry or alias entrypoint.

### Decision Summary

Introduce a tiered architecture under `templates/` (atomic prompts, workflow YAML, alias entrypoints), add a workflow runner that enforces autonomy guardrails and emits JSON Lines telemetry, expose three high-level entrypoints (`create-spec`, `execute-plan`, `suggest-improvement`) as aliases, and route improvement issues to the canonical `markhazleton/devspark` repo. Existing slash commands stay 100% functional.

### Key Drivers

- Discoverable, beginner-friendly entrypoints without losing expert atomic access
- Explicit, auditable autonomy and observability for production adoption
- Self-improvement loop (`suggest-improvement`) that converts feedback into tracked work
- Preserve constitutional Backward Compatibility, Ownership Boundary, Platform Parity

### Source Inputs

- [spec.md](spec.md) — 5 user stories, 36 FRs, 10 SCs, 10 clarifications
- DevSpark Constitution v1.1.0 (`.documentation/memory/constitution.md`)
- Spec validation contract (`templates/spec-validation-contract.md`)
- Existing 28 commands under `templates/commands/` (compatibility baseline)
- Existing 3-tier resolver in `src/devspark_cli/resolution.py`

### Tradeoffs Considered

- Option A (rejected): Place new tiers at repo root (`/workflows/`, `/prompts/`). Splits ownership and breaks resolver symmetry.
- Option B (rejected): Move atomic prompts to `.yaml` immediately. High migration cost; breaks Backward Compatibility and existing tests.
- Option C (rejected): Pluggable issue tracker adapter for AzDO/GitLab in this feature. Out-of-scope expansion; deferred per clarification (issues always target `markhazleton/devspark`).
- Selected: All new artifacts under `templates/` with the existing 3-tier resolver extended; atomic prompts remain `.md` + YAML frontmatter; workflows are YAML; runner enforces autonomy; telemetry is JSONL local-first.

### Architectural Impact

- New directories under `templates/`: `prompts/atomic/`, `workflows/`, `aliases/`
- New Python module `src/devspark_cli/runner/` (workflow loader, executor, autonomy enforcer, telemetry writer)
- New Python module `src/devspark_cli/issues.py` for `gh` CLI invocation against `markhazleton/devspark`
- Extend `src/devspark_cli/resolution.py` to resolve workflow / alias / atomic prompt paths through the same personal → team → stock chain
- Extend `src/devspark_cli/commands.py` with `devspark help`, `devspark run <alias|workflow>`, `devspark workflows list`
- Add JSONL telemetry sink at `.documentation/telemetry/workflow-events.jsonl` (env override `DEVSPARK_TELEMETRY_PATH`)
- New PowerShell + Bash parity scripts: `run-workflow.ps1` / `run-workflow.sh`
- Issue template `.github/ISSUE_TEMPLATE/devspark-improvement.md`
- All existing `templates/commands/*.md` continue to resolve unchanged; legacy slash commands map 1:1 to new atomic ids

### Reviewer Guidance

Focus on (1) `templates/` ownership stays intact; (2) resolver extension is additive only; (3) workflow runner is the **only** enforcement layer for autonomy; (4) telemetry schema is identical across all workflows; (5) `gh issue create` always targets `markhazleton/devspark` regardless of caller cwd; (6) PS/Bash parity for new scripts; (7) no `.documentation/` writes by install/upgrade.

## Summary

Re-platform DevSpark from a prompt library into a tiered orchestration engine. Three layers — atomic prompts (`templates/prompts/atomic/*.md`), workflow definitions (`templates/workflows/*.yaml`), alias entrypoints (`templates/aliases/*.yaml`) — are wired together by a Python workflow runner that pauses for review, enforces autonomy guardrails, and writes JSON Lines telemetry. Three flagship workflows ship: `create-spec`, `execute-plan`, `suggest-improvement` (the last always opens issues against `github.com/markhazleton/devspark`). Existing slash commands remain fully functional via mapping to atomic prompts.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: typer, rich, click, PyYAML (already vendored requirement), `gh` CLI (external), pytest
**Storage**: Filesystem (YAML/Markdown artifacts under `templates/`); JSON Lines telemetry under `.documentation/telemetry/`
**Testing**: pytest (existing `tests/` suite); add contract tests for workflow schema, runner, telemetry, autonomy, issue adapter
**Target Platform**: Cross-platform CLI (Windows PowerShell, macOS/Linux Bash); used inside AI agent contexts (Copilot, Claude Code, Cursor, generic)
**Project Type**: CLI library + spec-driven prompt framework
**Performance Goals**: Design intent (verified by Phase 10 benchmark task, not enforced by SC): workflow startup overhead < 200 ms p95 on local SSD; telemetry append < 5 ms per event
**Constraints**: No new runtime deps beyond stdlib + already-listed packages; no network calls except `gh` CLI in `suggest-improvement`; install/upgrade flows MUST never write under `.documentation/` (runtime workflow execution MAY write under `.documentation/telemetry/` and `.documentation/specs/.../gates/` as repo-owned work product — see spec Assumptions)
**Scale/Scope**: ~28 existing commands migrate to atomic prompts; 3 flagship workflows + 3 aliases at GA; telemetry expected ≤ 1k events/day per dev

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Backward Compatibility | PASS | All existing `templates/commands/*.md` and slash commands preserved; aliases map to canonical workflows; legacy entrypoints unchanged (FR-034) |
| II. Explicit Over Implied | PASS | Autonomy is explicit per workflow (FR-013–FR-016); non-interactive runs without policy fail loudly (FR-016); aliases resolve via declared mapping, no heuristic inference |
| III. Ownership Boundary | PASS | All new framework artifacts under `templates/` and `src/devspark_cli/`; telemetry path under `.documentation/` is **read/write at runtime only**, never created or modified by install/upgrade flows. Verified by `tests/test_upgrade_migration_safety.py` extension |
| IV. Governance Authority | PASS | Constitution gates remain authoritative; no per-app weakening introduced |
| V. Simplicity | PASS | Single resolver chain reused; one telemetry sink; one issue target; no plugin system this feature |
| VI. Platform Parity | PASS | New `run-workflow.ps1` + `run-workflow.sh` ship together; YAML schema is platform-neutral |
| VII. PR Review Artifact Commit Discipline | PASS | No change to `address-pr-review` commit-isolation behavior (FR-028) |

**Result**: All gates PASS. No Complexity Tracking entries required.

## Project Structure

### Documentation (this feature)

```text
.documentation/specs/001-interactive-analyze-flow/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── workflow-schema.md
│   ├── alias-schema.md
│   ├── atomic-prompt-frontmatter.md
│   ├── telemetry-event.md
│   └── issue-adapter.md
├── checklists/
│   └── requirements.md  # Already exists
├── gates/               # Populated by analyze/critic/checklist runs
└── tasks.md             # Phase 2 output (/devspark.tasks)
```

### Source Code (repository root)

```text
src/devspark_cli/
├── __init__.py
├── agent_registry.py
├── commands.py                  # Extended: devspark help, devspark run, devspark workflows list
├── inference.py
├── registry.py
├── resolution.py                # Extended: resolve workflows / aliases / atomic prompts via 3-tier chain
├── scope.py
├── issues.py                    # NEW: gh CLI adapter, hardcoded markhazleton/devspark target
├── runner/                      # NEW
│   ├── __init__.py
│   ├── loader.py                # YAML parsing, alias→workflow resolution
│   ├── executor.py              # Step iteration, pause gates, conditional branching
│   ├── autonomy.py              # Pre-step policy + post-step diff guardrails
│   └── telemetry.py             # JSONL writer, schema enforcement
└── harness/                     # Existing

templates/
├── commands/                    # UNCHANGED (28 existing slash commands)
├── prompts/
│   └── atomic/                  # NEW: capture-context.md, classify-improvement.md,
│                                #      create-issue.md, assign-agent.md, plus mappings for
│                                #      existing commands (specify, plan, generate-tasks,
│                                #      analyze, implement, create-pr, review-pr, ...)
├── workflows/                   # NEW
│   ├── create-spec.yaml
│   ├── execute-plan.yaml
│   └── suggest-improvement.yaml
├── aliases/                     # NEW
│   ├── create-spec.yaml
│   ├── execute-plan.yaml
│   └── suggest-improvement.yaml
└── (existing: plan-template.md, spec-template.md, tasks-template.md, ...)

scripts/
├── powershell/
│   ├── run-workflow.ps1         # NEW
│   └── (existing)
└── bash/
    ├── run-workflow.sh          # NEW
    └── (existing)

tests/
├── test_workflow_schema_contract.py        # NEW
├── test_workflow_runner_contract.py        # NEW
├── test_autonomy_enforcement_contract.py   # NEW
├── test_telemetry_event_contract.py        # NEW
├── test_alias_resolution_contract.py       # NEW
├── test_atomic_prompt_frontmatter_contract.py  # NEW
├── test_issue_adapter_contract.py          # NEW
└── (existing tests preserved)

.github/
└── ISSUE_TEMPLATE/
    └── devspark-improvement.md  # NEW
```

**Structure Decision**: Extend existing CLI library (single project) with a new `runner/` subpackage and additive `templates/` directories. No restructure of existing code. All artifact tiers live under `templates/` to preserve Ownership Boundary and reuse the 3-tier resolver.

## Complexity Tracking

> No constitution violations require justification. Section intentionally empty.
