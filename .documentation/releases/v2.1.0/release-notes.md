# Release Notes: v2.1.0 — Workflow Engine Foundation

## Release Metadata

- **Version**: v2.1.0
- **Release Date**: 2026-04-18
- **Release Window**: 2026-04-16 → 2026-04-18 (since v2.0.0)
- **Previous Version**: v2.0.0
- **Bump Type**: Minor (additive features, no breaking changes)
- **Commits in window**: 184 (April 2026 sprint total — see `.documentation/copilot/commit-audit-2026-04-18.md`)
- **Contributors**: 3 (Mark Hazleton, DevSpark Test, copilot-swe-agent[bot])
- **Merged PRs in window**: 1 ([#28](https://github.com/markhazleton/devspark/pull/28))

## Highlights

DevSpark v2.1.0 adds a **tiered prompt and workflow engine** on top of the v2.0.0 Harness Runtime, completing the architectural pair that defines DevSpark v2: Harness handles declarative *adapter-driven* execution; the Workflow Engine handles declarative *prompt composition*. The two layers share an autonomy contract, telemetry schema, and pause/resume semantics so that any orchestration — from a single slash command to a fully autonomous multi-step workflow — emits consistent observability signals and respects the same human-in-the-loop gates.

This release introduces the `devspark run / resume / workflows / runs / help` CLI subcommands, three workflow YAML aliases (`create-spec`, `execute-plan`, `suggest-improvement`), 28 backward-compatible legacy atomic shims, and the `/devspark.address-pr-review` command that closes the PR-review loop with commit-isolation enforcement (Constitution Principle VII). A Shared Review Resolution Contract now produces consistent resolution output across five review commands.

All v1.x commands continue to work unchanged through the shim layer — Constitution Principle I (Backward Compatibility) holds.

## New Features

### Tiered Workflow Engine

Loader / executor / telemetry / autonomy modules with full contract test coverage. Workflows are now declarative YAML artifacts under `templates/workflows/`, executed by a runner that emits standardized telemetry events at each step boundary.

**Spec**: [specs/001-interactive-analyze-flow/spec.md](specs/001-interactive-analyze-flow/spec.md)

### `devspark run` CLI Surface

New subcommands:

- `devspark run <alias>` — execute a workflow by alias
- `devspark resume <run-id>` — resume a paused workflow at the next step
- `devspark workflows` — list available workflows and their aliases
- `devspark runs` — inspect recent run history and outcomes
- `devspark help` — discover commands, workflows, and aliases

### Workflow YAML Aliases

Three new flagship aliases ship with v2.1.0:

| Alias | Composition | Pause point |
|-------|-------------|-------------|
| `create-spec` | `specify → plan → tasks → analyze` | After `analyze` |
| `execute-plan` | `implement → create-pr → pr-review` | After `create-pr` |
| `suggest-improvement` | File a structured improvement issue | None |

### GitHub Issue Adapter

Bridges GitHub issues into workflow inputs, enabling external orchestration: an issue labeled appropriately becomes a workflow trigger.

### 28 Legacy Atomic Shims + 4 Improvement-Loop Atomic Prompts

All v1.x slash commands now resolve via auto-generated atomic shims sourced from canonical command prompts. The shim-drift CI workflow guards against prompt/shim divergence. Four new atomic prompts back the improvement loop.

### `/devspark.address-pr-review`

Author-side PR review remediation command with commit-isolation gates. Enforces Constitution Principle VII (PR Review Artifact Commit Discipline): review-file edits and code fixes land in separate commits so revision diffs remain auditable.

### Shared Review Resolution Contract

Standardized resolution output across five review commands (`pr-review`, `address-pr-review`, `analyze`, `critic`, `clarify`) so reviewers and authors can mechanically reconcile findings.

### Comprehensive v2 Documentation

New living docs added to `.documentation/`:

- `getting-started.md` — onboarding path for new users
- `architecture.md` — tiered runtime + harness overview
- `autonomy.md` — autonomy policy and pause/resume semantics
- `improvement-loop.md` — the suggest-improvement workflow lifecycle
- `threat-model.md` — adversarial use cases and mitigations

## Bug Fixes

- Lint hardening on PR-touched files (markdown rules MD047 / MD036 / MD001 + pyflakes warnings cleared)
- Bash shim generator aligned to single backticks for consistent code-fence output

## Breaking Changes

**None.** All v1.x and v2.0.x command surfaces continue to work unchanged via shims.

## Deprecations

None in this release. The legacy atomic shim layer remains a permanent compatibility surface per Constitution Principle I.

## Architectural Decisions

- **ADR-001**: Tiered Prompt and Workflow Architecture — [View](../../decisions/ADR-001.md)

## Deferred Features

None. No incomplete or in-progress specs at release time.

## Upgrade Guide

For consumer projects:

```bash
uvx --from git+https://github.com/markhazleton/devspark.git devspark upgrade
```

This refreshes `.devspark/` (framework payload), regenerates atomic shims, and stamps `.devspark/VERSION` with `2.1.0`. Your `.documentation/` is untouched (Constitution Principle III — Ownership Boundary).

For maintainers tagging the release:

```bash
git tag v2.1.0
git push origin v2.1.0
```

The release workflow will publish packaged templates and a GitHub Release.

## Metrics

| Metric | Value |
|--------|-------|
| Features Delivered (specs in release window) | 1 (spec 001 — spec 002 shipped in v2.0.0) |
| Bugs Fixed | 2 (lint + shim formatting) |
| PRs Merged in window | 1 (#28) |
| New Atomic Prompts | 4 |
| Legacy Shims Generated | 28 |
| Workflow Aliases Added | 3 |
| ADRs Created | 1 |
| Contributors | 3 |
| Commits (April 2026 sprint) | 184 |
| Constitution Principles upheld | 7/7 |
| Site Audit Issues (today) | 0 critical, 0 high, 3 medium (oversized files — follow-up specs queued) |

---

*Release documentation generated by /devspark.release v2.1.0*
