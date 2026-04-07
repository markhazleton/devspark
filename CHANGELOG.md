# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to DevSpark are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - Multi-App Monorepo Support

**Explicit multi-application monorepo support with profile-based inheritance and dependency-aware scoping.**

### Added

- Multi-app registry at `.documentation/devspark.json` with Pydantic v2 validation
- App-local manifest support (`{app.path}/app.json`) for app-specific overrides
- Profile-based inheritance model with tags/rules/hints composition
- Constitution resolution with additive app overlays and weakening detection
- Prompt, script, and template resolution chains with app-specific override tiers
- Dependency-aware scope reporting (declared + inferred from imports/build config)
- PR scope validation with `single-app`, `cross-app`, and `repo-scope` modes
- `/devspark.add-application` command with automatic scaffolding
- `/devspark.list-applications` command for registry overview
- `/devspark.validate-registry` command for CI-friendly validation
- Rationale Summary block in spec, plan, and tasks templates
- Rationale & Traceability Risks category in `/devspark.critic`
- App context propagation (`--app`, `--repo-scope`) across all Bash and PowerShell scripts
- Four fixture repositories for testing (single-app, two-api, full-monorepo, 20-app)

### Changed

- All command templates updated with multi-app support instructions
- `scripts/bash/platform.sh` script resolution now includes app-specific override tier
- `pydantic>=2.0` added as a project dependency

### Compatibility

- Full backward compatibility: single-app repositories require zero changes
- Multi-app mode is opt-in via `.documentation/devspark.json`

## [0.1.2] - 2026-04-06

**Prompt-first lifecycle, release tooling alignment, and branding cleanup.**

### Added

- Prompt-first [implementation lifecycle guide](.documentation/implementation-lifecycle.md) covering quickstart, delivery workflow, and updates
- Explicit remote-prompt upgrade path across README, quickstart guides, and GitHub Pages source docs

### Changed

- Repositioned quickstart and upgrade flows so remote prompt files are the primary experience and CLI is clearly advanced/optional
- Quickstart prompts now stamp `.devspark/VERSION` with the latest semantic DevSpark version instead of `quickstart`
- Updated GitHub Pages source docs for consistent prompt-first messaging across landing, quickstart, upgrade, installation, FAQ, and about pages
- Completed DevSpark branding pass in CLI banner and user-facing setup text
- Aligned upgrade command documentation around `.devspark/VERSION` as the authoritative installed-version stamp with legacy fallback support
- Updated release workflow inputs, examples, and documentation to reflect `v0.1.2` and current DevSpark positioning

### Fixed

- Removed remaining legacy `Spec Kit` and non-essential `specify` branding from docs and onboarding copy
- Corrected documentation architecture references for stock prompts, templates, and override layers
- Resolved markdownlint issues introduced during prompt-first documentation updates

---

## [0.1.1] - 2026-04-05

**Bug fixes, macOS compatibility, and CI hardening.**

### Fixed

- macOS Bash 3.2 compatibility across all `scripts/bash/` scripts (harvest.sh, archive-context.sh, common.sh, and others)
- BSD tool compatibility fixes for `find`, `sed`, and other POSIX utilities on macOS
- Restored accidentally removed `latest_feature` declaration in common.sh
- Excluded `docs/` from harvest scan and truncated text fields to prevent malformed JSON
- Resolved all ShellCheck warnings across bash scripts and CI workflows
- Resolved all markdownlint errors across 8 documentation files
- Flexible digit pattern in `find` to match original `ls|grep` behavior

### Added

- ShellCheck CI job with bash version check for automated lint enforcement
- Platform adapter and 2-tier script override system for team customization
- Quickstart files now re-runnable with version-aware update logic
- Developer FAQ section and README link step in `/devspark.repo-story`
- Video embed on GitHub Pages home page
- About page for documentation site
- SC1091 exclusion comment in shellcheck workflow for clarity
- Branch-sync hard rule enforcement for PR creation, review, and approval

### Changed

- Updated CLAUDE.md with branch-sync hard rule and platform support note
- Aligned all content to v0.1.0 naming and removed legacy fork terminology
- Updated installation and quickstart guides for improved clarity and accessibility
- Fixed documentation site navigation and removed self-referencing language

### Removed

- 12 fork-era files consolidated into new structure
- 7 stale `.documentation` files with broken references cleaned up
- `.devcontainer/` directory (unnecessary for markdown-first product)
- Local cruft and gitignored Claude settings and `_site/`

---

## [0.1.0] - 2026-04-02

**DevSpark Alpha — First standalone release.**

DevSpark is now an independent project, no longer positioned as a fork. This release resets versioning and establishes the product identity.

### What's Included

#### 21 Slash Commands

- `/devspark.constitution` — Establish project principles and guidelines
- `/devspark.specify` — Define requirements and user stories
- `/devspark.plan` — Create technical implementation plan
- `/devspark.tasks` — Break plan into actionable task lists
- `/devspark.implement` — Execute tasks and build the feature
- `/devspark.pr-review` — Constitution-based pull request review
- `/devspark.site-audit` — Codebase compliance audit
- `/devspark.quickfix` — Lightweight bug fix workflow
- `/devspark.harvest` — Knowledge-preserving cleanup for stale docs
- `/devspark.release` — Release documentation and archival
- `/devspark.critic` — Adversarial risk analysis
- `/devspark.clarify` — Structured clarification questions
- `/devspark.analyze` — Cross-artifact consistency check
- `/devspark.checklist` — Quality validation checklists
- `/devspark.personalize` — Per-user prompt overrides
- `/devspark.discover-constitution` — Reverse-engineer constitution from code
- `/devspark.evolve-constitution` — Constitution amendment proposals
- `/devspark.repo-story` — Evidence-based repository narrative
- `/devspark.archive` — Archive completed spec artifacts
- `/devspark.upgrade` — Pull latest DevSpark prompts
- `/devspark.taskstoissues` — Convert tasks to GitHub issues

#### Architecture

- **No install required** — Copy prompt files or use agent quickstart guides
- **`.devspark/`** installation directory — framework files, safe to remove
- **`.documentation/`** user artifacts — specs, constitution, decisions (never touched by DevSpark)
- **3-tier override system** — personal > team > stock defaults
- **17+ AI agents supported** — Copilot, Claude Code, Cursor, Windsurf, Gemini CLI, and more
- **Agent quickstart guides** — Point your agent at a quickstart prompt to bootstrap without CLI
- **Optional CLI** (`devspark-cli`) — automates setup via `devspark init` / `devspark upgrade`
- **`devspark uninstall`** — clean removal that leaves user work intact

### Architecture

- `.devspark/` (installation) is separate from `.documentation/` (user work)
- `DEVSPARK_FEATURE` env var for feature context
- `[devspark]` log prefix
- 3-tier prompt resolution: personal > team > stock defaults
