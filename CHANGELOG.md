# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to DevSpark are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Aligned all content to v0.1.0 naming and removed legacy spec-kit references
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
