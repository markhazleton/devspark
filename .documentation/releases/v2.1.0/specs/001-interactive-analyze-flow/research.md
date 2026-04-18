# Phase 0 Research

All NEEDS CLARIFICATION items from Technical Context were resolved by the spec's Clarifications session 2026-04-18. This document consolidates the supporting research.

## R1. Tiered artifact location

- **Decision**: Place `prompts/atomic/`, `workflows/`, `aliases/` under `templates/`; resolve via the existing 3-tier override chain (personal → team → stock).
- **Rationale**: Ownership Boundary (constitution §III) — `.documentation/` is repo-owned and must not be touched by install/upgrade. `templates/` is the canonical DevSpark-owned defaults directory. Resolver in `src/devspark_cli/resolution.py` already handles the 3-tier chain for `templates/commands/`.
- **Alternatives considered**: Repo-root `/workflows/` (rejected — splits ownership); `.devspark/` only (rejected — diverges source vs installed repo layout, breaks dogfooding).

## R2. Atomic prompt format

- **Decision**: `.md` files with YAML frontmatter, identical shape to today's `templates/commands/*.md`.
- **Rationale**: Zero-cost migration of 28 existing commands; preserves human-readable prose body; `agent-customization` skill already documents this shape; existing markdownlint config covers it.
- **Alternatives considered**: Pure `.yaml` (rejected — loses prose readability, breaks compatibility); `.md` + sidecar `.yaml` (rejected — two-file complexity violates Simplicity §V).

## R3. Telemetry sink

- **Decision**: JSON Lines, append-only, default path `.documentation/telemetry/workflow-events.jsonl`; override via env `DEVSPARK_TELEMETRY_PATH`.
- **Rationale**: Local-first, zero-config, no external service. JSONL is trivially queryable (`jq`, Kusto-style ingestion later). Aligns with existing `harness` log conventions.
- **Alternatives considered**: stdout (rejected — caller must capture); pluggable sinks (rejected — premature abstraction); both stdout+file (rejected — duplicate writes).
- **Schema enforcement**: Writer validates required keys before append; missing telemetry path is auto-created at runtime (runtime write under `.documentation/` is allowed; install/upgrade still must not touch).

## R4. Autonomy guardrail enforcement

- **Decision**: Workflow runner enforces. Pre-step policy evaluation (path allow/deny, file-change threshold) + post-step diff inspection. Atomic prompts remain enforcement-free.
- **Rationale**: Single chokepoint with full context (autonomy policy + step output); keeps atomic prompts reusable across autonomy levels; consistent with FR-015.
- **Alternatives considered**: Pre-commit hook (rejected — too late, only catches commits); per-prompt enforcement (rejected — duplicates logic, inconsistent across prompts); layered (rejected — dual ownership obscures audit trail).
- **Behavior**: When a guardrail triggers, the runner downgrades to assisted-mode (pause for review) and emits a telemetry event with `guardrail_triggered=true` and the violated rule id.

## R5. Suggest-improvement issue backend

- **Decision**: Always `gh issue create --repo markhazleton/devspark`. No per-call repo override; no platform abstraction in this feature.
- **Rationale**: User-stated requirement — `markhazleton/devspark` is the canonical DevSpark home. Avoids adapter complexity and keeps improvements centralized regardless of which downstream repo invoked the workflow.
- **Alternatives considered**: Caller-repo default (rejected — fragments improvement signal); pluggable adapter (rejected — out of scope, deferred); local markdown file (rejected — no tracking).
- **Failure mode**: If `gh` is not installed or not authenticated, runner exits with `EXIT_GH_UNAVAILABLE` and prints install/auth guidance.

## R6. Backward compatibility for existing slash commands

- **Decision**: Existing `/devspark.*` slash commands continue to resolve to `templates/commands/*.md` unchanged. New atomic prompts under `templates/prompts/atomic/` are added alongside (not as replacements). Workflows reference atomic prompts by id; ids match existing command names where possible (`specify`, `plan`, `generate-tasks`, `analyze`, `implement`, `create-pr`, `pr-review`).
- **Rationale**: Constitutional Backward Compatibility (§I); zero migration burden for existing user repos.
- **Open question for Phase 2**: Whether the atomic prompt files duplicate command content or are thin includes. **Resolution**: Thin reference — atomic prompt files contain only frontmatter + a one-line pointer to the canonical command body, to avoid drift. Tracked as task in Phase 2.

## R7. Workflow YAML schema source-of-truth

- **Decision**: Schema documented in `contracts/workflow-schema.md`; validation implemented in `src/devspark_cli/runner/loader.py` using PyYAML + a hand-rolled validator (no jsonschema dep yet; matches Simplicity §V).
- **Rationale**: Stay within current dependency footprint. Hand validator is < 100 lines for the field set defined.
- **Alternatives considered**: jsonschema (rejected — new dep for trivial validation); pydantic (rejected — same).

## R8. Platform parity for runner invocation

- **Decision**: New `scripts/powershell/run-workflow.ps1` and `scripts/bash/run-workflow.sh` are thin wrappers that shell out to `python -m devspark_cli run <alias|workflow>`. Runner logic lives in Python; scripts only handle env setup and arg passthrough.
- **Rationale**: Constitutional Platform Parity (§VI) without duplicating runner logic.

## Open NEEDS CLARIFICATION items

None. All items from the spec resolved.
