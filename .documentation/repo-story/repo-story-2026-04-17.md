# Repository Story: DevSpark

> Generated 2026-04-17 | Window: 12 months | Scope: full

## Executive Summary

DevSpark is a structured development process for AI coding assistants — 27 slash-command prompt files, helper templates, and cross-platform scripts that give any supported AI agent a repeatable workflow from requirements through release. It requires no installation; teams copy markdown files into their project and start using `/devspark.*` commands immediately.

In eight months of active development (August 21, 2025 – April 17, 2026), DevSpark has accumulated **761 commits** from **86 contributors**, producing a mature, well-governed codebase. The project has processed **142 merged pull requests**, indicating a disciplined PR-based workflow throughout its lifetime.

Development velocity tells a story of rapid community engagement followed by focused architectural evolution. The project launched in August 2025 and attracted its peak community contribution wave in September (255 commits) and October (184 commits) as the open-source community added integrations for 17 AI agent platforms. After a period of consolidation (November–January), velocity re-accelerated in April 2026 (158 commits) as the team shipped the Harness Runtime — a declarative, adapter-driven execution engine representing the project's most significant technical milestone.

Governance maturity is high. The project operates under a ratified constitution (`v1.0.0`, April 2026) that codifies backward-compatibility, explicit scoping, and ownership-boundary principles. Conventional commit adoption stands at **98.1%** (208 of 212 non-merge commits), and the codebase maintains a healthy test infrastructure with 135 test files and 105 test-related commits.

The release cadence has been consistent and well-documented. The CHANGELOG tracks five major releases — from the initial v1.0.0 foundation through v1.4.0, v1.5.0, v1.6.0, and the flagship v2.0.0 (Harness Runtime, April 16, 2026). Each release is accompanied by detailed notes, validation evidence, and release-readiness documentation, demonstrating delivery discipline suitable for enterprise adoption.

## Technical Analysis

### Development Velocity

Monthly commit distribution reveals three distinct project phases:

| Month | Commits | Phase |
|-------|---------|-------|
| 2025-08 | 22 | **Launch** — Initial commit and foundational scaffolding |
| 2025-09 | 255 | **Community Explosion** — Peak open-source contribution wave |
| 2025-10 | 184 | **Integration Wave** — Continued agent-platform additions |
| 2025-11 | 51 | **Stabilization** — Docs, upgrades, and QoL improvements |
| 2025-12 | 16 | **Quiet** — Holiday slowdown, minor formatting and docs |
| 2026-01 | 10 | **Low** — Focused planning for next evolution |
| 2026-02 | 29 | **Fork & Rebrand** — DevSpark identity established from Spec Kit lineage |
| 2026-03 | 36 | **Architecture** — Multi-app, harvest, 2-tier script resolution |
| 2026-04 | 158 | **Harness Sprint** — v2.0.0 implementation, validation, and release |

The project exhibits a healthy pattern: intense community contribution windows followed by consolidation, then architect-led feature sprints. The April 2026 spike corresponds directly to the Harness Runtime feature branch (`002-harness-runtime`), which landed as the largest single merge (51 files, +6,346/−7 lines) via PR #22.

File-type distribution across all commits shows the project's documentation-first nature: Markdown files were touched 1,450 times (59.7% of all file touches), followed by Shell scripts (322), PowerShell (222), Python (191), YAML (72), and JSON (62). This ratio reflects DevSpark's core identity — the product is markdown prompts, and the code exists to support them.

### Contributor Dynamics

The contributor base is highly distributed, with 86 unique contributors over the project's lifetime. Role distribution (anonymized):

| Role Tier | Contributors | Commits | % of Total |
|-----------|-------------|---------|------------|
| Lead Architect | 1 | 361 | 47.4% |
| Primary Developer (A) | 1 | 137 | 18.0% |
| Active Contributors (B–F) | 5 | 113 | 14.8% |
| Occasional Contributors (G–X) | 17 | 88 | 11.6% |
| Single-Commit Contributors | 62 | 62 | 8.1% |

**Bus factor assessment**: The Lead Architect accounts for 47.4% of all commits, concentrated in the initial build-out phase (September–October 2025). Developer A emerged as the primary active developer from January 2026 onward, contributing 137 commits across architecture, rebrand, and feature implementation. The transition from a single-architect model to a multi-contributor model is a positive maturity signal.

**Team evolution**: The project shows clear phase-based contributor patterns. The Lead Architect dominated Aug–Oct 2025 (community launch), a broad community wave added integrations in Sep–Nov 2025, and a smaller, focused team (Developers A–D) drove the architecture and harness work in 2026. This evolution from open-contribution breadth to focused-team depth is typical of maturing open-source projects.

### Quality Signals

**Test infrastructure**: The codebase contains 135 test files, with 105 commits (13.8% of total) explicitly related to testing. Test modules cover contract validation, PR preflight, script parity, upgrade safety, documentation audits, release registry, and harness-specific spec loading, validation rules, adapter contracts, and runner lifecycle.

**Conventional commit adoption**: 208 of 212 non-merge commits (98.1%) use conventional prefixes. The prefix distribution shows balanced engineering activity:

| Category | Commits |
|----------|---------|
| fixes | 168 |
| features | 117 |
| docs | 97 |
| tests | 44 |
| chore | 23 |
| refactor | 19 |
| ci/build | 5 |
| other | 288 |

The high fix-to-feature ratio (1.44:1) is typical of a project that ships features and then immediately hardens them — a positive quality signal.

### Governance & Process Maturity

**PR workflow**: With 142 merged pull requests across 761 commits, the project maintains a consistent PR-based development model. The 10 largest merges range from 220 to 6,353 total lines, all following a feature-branch-to-main merge pattern.

**Constitution**: The project ratified a formal constitution (`v1.0.0`, April 6, 2026) with six non-negotiable principles covering backward compatibility, explicit scoping, ownership boundaries, governance authority, simplicity, and platform parity. Seven governance artifacts are actively maintained.

**Spec-driven development**: The project practices its own methodology. One active spec directory and four archived spec directories demonstrate consistent use of the specify → plan → tasks → implement lifecycle. The most recent spec (`002-harness-runtime`) completed all 32 tasks and was merged via a constitution-compliant PR review before the v2.0.0 release.

**Tag discipline**: No Git tags were found in the repository. Releases are tracked through CHANGELOG entries and release documentation under `.documentation/releases/` rather than Git tags. This is an area where governance could be strengthened — adding semver tags would improve release traceability and enable automated release packaging.

### Architecture & Technology

**Primary stack**:

- **Python 3.11+** — CLI and harness runtime (`src/devspark_cli/`), typed with `typer`/`rich`/`click`
- **PowerShell 7+** — Context-gathering scripts, parity with Bash equivalents
- **Bash** — Cross-platform script pair for every PowerShell script
- **Markdown** — 27 command templates (the core product), documentation, specifications
- **YAML** — Harness spec format (`apiVersion: devspark.ai/v1`), GitHub Actions CI
- **JSON** — Agent registry, extension catalog, release metrics, harness telemetry

**Configuration maturity**: The repository includes `pyproject.toml` for Python packaging, `.markdownlint-cli2.jsonc` for lint rules, GitHub Actions workflows for CI/release, and `.gitignore`/`.gitattributes` for repository hygiene. No Dockerfile is present (expected — DevSpark is a development-time tool, not a deployed service).

**Architectural pattern**: DevSpark uses a 3-tier prompt resolution model (personal → team → stock) and a 2-tier script resolution model (team → stock). The harness runtime adds a pluggable adapter architecture with five built-in adapters and an extensible `AgentAdapter` protocol.

**Hotspot analysis**: The most-modified file is `README.md` (131 changes), reflecting continuous documentation updates as the project evolved through rebrand and feature additions. The second hotspot, `src/specify_cli/__init__.py` (106 changes), is the CLI entry point — heavy churn here is expected as commands were added iteratively. `templates/commands/specify.md` (53 changes) reflects the core specify workflow receiving ongoing refinement.

## Change Patterns

The top 5 most-modified files and what they reveal:

| File | Changes | Interpretation |
|------|---------|---------------|
| `README.md` | 131 | Project identity evolved rapidly — rebrand from Spec Kit, agent additions, feature documentation. High churn here is expected for a project whose README is both documentation and marketing. |
| `src/specify_cli/__init__.py` | 106 | CLI entry point accumulated commands iteratively. This file may benefit from modularization if it hasn't already been split. |
| `CHANGELOG.md` | 68 | Healthy signal — releases are consistently documented. Append-only pattern confirmed. |
| `pyproject.toml` | 62 | Version bumps, dependency additions, and metadata refinement. One corruption incident (fixed in v2.0.0 prep) is noted. |
| `.github/workflows/scripts/create-release-packages.sh` | 58 | Release packaging evolved significantly as agent-count grew from 3 to 17. |

**Directory-level patterns**: Templates (`templates/commands/`) dominate change activity with 12+ files exceeding 10 changes each. Scripts (`scripts/powershell/`, `scripts/bash/`) show balanced dual-platform evolution. The `.documentation/` directory shows healthy living-documentation maintenance.

## Milestone Timeline

No Git tags are present in the repository. Release milestones are tracked via CHANGELOG entries:

| Date | Version | Description |
|------|---------|-------------|
| 2025-09 (est.) | v1.0.0 | Initial release — core specify/plan/tasks/implement workflow |
| 2026-04-01 | v1.4.0 | (CHANGELOG entry exists; workflow maturity release) |
| 2026-04-10 | v1.5.0 | Workflow evolution — route-aware intake, shared agent registry, frontmatter contracts |
| 2026-04-12 | v1.6.0 | Install hardening — prompt consistency, quickstart repair flows, framework template resolution |
| 2026-04-16 | v2.0.0 | **Harness Runtime** — declarative YAML specs, pluggable adapters, validation engine, telemetry |

The April 2026 release burst (v1.5.0 → v1.6.0 → v2.0.0 in 6 days) shows intense pre-release activity. Commit velocity spiked in the two weeks before v2.0.0, with the harness feature branch contributing 51 files in a single merge. Post-release, activity shifted to dogfooding documentation and source-direct shim setup.

## Constitution Alignment

The DevSpark constitution (`v1.0.0`, ratified 2026-04-06) defines six principles. Here is how the commit history reflects each:

| Principle | Evidence | Alignment |
|-----------|----------|-----------|
| **I. Backward Compatibility** | All major features (multi-app, harness) are explicitly additive. README and docs consistently state "single-app repos need nothing here." No breaking migration was forced. | **Strong** |
| **II. Explicit Over Implied** | `--app <id>` scoping for multi-app, `--mode act/plan` for harness, explicit route confirmation in `/devspark.specify`. Constitution requires clear errors over guesses. | **Strong** |
| **III. Ownership Boundary** | Clean `.devspark/` vs `.documentation/` separation is documented, tested (`test_upgrade_migration_safety.py`), and enforced in all quickstart and upgrade flows. | **Strong** |
| **IV. Governance Authority** | Constitution reviews in PR workflow. PR #22 (harness) received a constitution-based review before merge. 7 governance artifacts actively maintained. | **Strong** |
| **V. Simplicity** | 3-tier prompt resolution is simple and documented. However, the 86-contributor anonymization in the script produces noisy role labels — a minor complexity issue in tooling, not core product. | **Good** |
| **VI. Platform Parity** | `test_script_parity_contract.py` validates Bash/PowerShell equivalence. Every script has a dual-platform pair. | **Strong** |

**Gap**: The absence of Git tags slightly weakens governance traceability. Adding semver tags at release points would strengthen Principle IV (Governance Authority) by making release boundaries machine-queryable.

## Developer FAQ

### What does this project do?

DevSpark provides a structured development process for AI coding assistants through 27 slash-command prompt files. You copy these markdown files (plus helper templates and scripts) into your project, and your AI agent gets a repeatable workflow covering specification, planning, task breakdown, implementation, PR creation, review, and release. It works with 17 supported AI agents including Claude, Copilot, Cursor, and Gemini.

### What tech stack does it use?

The core product is **Markdown** (27 command templates). Supporting infrastructure uses **Python 3.11+** (CLI and harness runtime, built with `typer`/`rich`/`click`), **PowerShell 7+** and **Bash** (context-gathering scripts maintained in lockstep), **YAML** (harness spec format and GitHub Actions CI), and **JSON** (agent registry, extension catalog, telemetry). The project uses `pyproject.toml` for Python packaging and `markdownlint-cli2` for markdown linting.

### Where do I start?

Start with `README.md` (131 changes — the most actively maintained file in the repo) for the overall structure. The core workflow templates live in `templates/commands/`, with `specify.md` (53 changes) as the primary entry point. For the CLI, `src/devspark_cli/` contains the Python package. The `quickstart/` directory has agent-specific bootstrap guides for Copilot, Claude Code, Cursor, and a generic fallback.

### How do I run it locally?

For prompt-only use, no installation is needed — copy the files and use slash commands. For the CLI: `uv tool install devspark-cli --from git+https://github.com/markhazleton/devspark.git`, then `devspark init my-project` or `devspark init --here --ai copilot`. For development on DevSpark itself, clone the repo and run `uv sync` or `pip install -e .` to set up the development environment with the `.venv` virtual environment.

### How do I run the tests?

Tests use **pytest** and live in the `tests/` directory (135 test files). Run `pytest` from the repository root with the virtual environment activated. Key test modules cover contract validation (`test_harness_spec_contract.py`, `test_harness_validation_contract.py`), PR preflight (`test_create_pr_preflight.py`), script parity (`test_script_parity_contract.py`), upgrade safety (`test_upgrade_migration_safety.py`), and documentation audits (`test_documentation_audit.py`).

### What is the branching/PR workflow?

DevSpark uses a PR-based merge workflow with 142 merged pull requests across 761 commits. Feature branches follow a naming convention (e.g., `002-harness-runtime`, `001-monorepo-implement`). PRs receive constitution-based reviews via `/devspark.pr-review` before merge. The `CLAUDE.md` enforces a hard rule: feature branches must be fully in sync with `main` before PR creation or review — rebase or merge first.

### Who do I ask when I'm stuck?

The Lead Architect (47.4% of all commits, dominant in the foundational Aug–Oct 2025 period) and Developer A (18.0%, primary active developer from Jan 2026 onward) are the most knowledgeable contributors. Together they account for 65.4% of the commit history. For harness-specific questions, Developers A and D drove the v2.0.0 implementation in April 2026.

### What areas of the code change most often?

The three highest-churn areas are: (1) `README.md` (131 changes) — project identity and documentation hub; (2) `templates/commands/` — the 27 command templates, especially `specify.md` (53), `tasks.md` (40), `plan.md` (37), and `implement.md` (34); and (3) `scripts/` — context-gathering scripts for PowerShell and Bash, especially `update-agent-context` (48/47 changes) and `create-new-feature` (30/24).

### Are there coding standards I must follow?

Yes. Conventional commit messages are required (98.1% adoption rate). Markdown is linted via `markdownlint-cli2` (config: `.markdownlint-cli2.jsonc`). Python code targets 3.11+ and must be typed with `typer`/`rich`/`click`. Scripts must be maintained in both PowerShell and Bash with functional parity (enforced by `test_script_parity_contract.py`). The project constitution at `.documentation/memory/constitution.md` defines six non-negotiable principles that all PRs must comply with.

### What version is currently released?

The latest release is **v2.0.0 — Harness Runtime**, released April 16, 2026. This major release introduced the declarative harness execution engine with YAML specs, pluggable adapters (Copilot, Claude Code, Cursor, manual, noop), a validation engine with 8 rule types, execution modes (act/plan), artifact delta tracking, telemetry, and comprehensive contract tests. Note: no Git tags are present — releases are tracked via CHANGELOG entries.

---

### Generated by /devspark.repo-story | DevSpark v2.0.0 - Adaptive System Life Cycle Development
