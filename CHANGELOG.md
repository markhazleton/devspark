# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to DevSpark are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
