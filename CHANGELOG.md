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

### Changed (from prior Spec Kit lineage)

- Rebranded from Spec Kit to DevSpark with full identity cleanup
- Version reset from 1.6.0 to 0.1.0 (fresh semantic versioning)
- Separated `.devspark/` (installation) from `.documentation/` (user work)
- `SPECIFY_FEATURE` env var renamed to `DEVSPARK_FEATURE`
- `[specify]` log prefix renamed to `[devspark]`
- All old releases and tags purged

---

## Prior History

DevSpark evolved from [github/spec-kit](https://github.com/github/spec-kit), an open-source project by the GitHub team. Versions 0.0.1 through 1.6.0 were released under the Spec Kit name. Key milestones from that era:

- **v0.0.4** — SOCKS proxy support for corporate environments
- **v0.0.8** — Windsurf IDE support, GitHub token support
- **v0.0.13** — Kilo Code, Augment CLI support
- **v0.0.16** — `--force` flag for init
- **v0.0.17** — `/clarify` and `/analyze` commands
- **v0.0.18** — `devspark.` command prefix, VS Code prompt shortcuts
- **v0.0.20** — Intelligent branch naming with GitHub 244-byte limit enforcement
- **v0.0.22** — VS Code/Copilot agent support, AGENTS.md
- **v0.0.24** — `/discover-constitution` command, DevSpark branding begins
- **v0.0.25** — `/pr-review` and `/site-audit` commands
- **v0.0.91** — `/evolve-constitution` command
- **v1.0.0** — Standard semantic versioning adopted
- **v1.1.0** — `devspark upgrade` command, migration scripts
- **v1.2.4** — `DEVSPARK_VERSION` stamp, `/upgrade` AI command
- **v1.3.0** — Performance optimizations for large repos
- **v1.4.0** — `/harvest` command
- **v1.5.0** — `/repo-story` command
- **v1.6.0** — Agent-agnostic layout, multi-user personalization

Full history of upstream contributions is preserved in git.
