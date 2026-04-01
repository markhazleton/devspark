# Spec Kit Spark v1.6.0

Spec Kit Spark is an Adaptive System Life Cycle Development (ASLCD) toolkit with constitution-powered commands and right-sized workflows. Part of the WebSpark demonstration suite.

## Release Highlights

This release (v1.6.0) introduces agent-agnostic canonical layout, multi-user personalization, and a comprehensive documentation refresh emphasizing Spec Kit's three pillars.

### What's New in v1.6.0

- **Agent-Agnostic Canonical Layout**: Command prompts now live in `.documentation/commands/` as a single source of truth. Platform directories (`.claude/`, `.github/`, `.cursor/`, etc.) contain only thin shims that redirect to canonical content with user-override resolution. Switch agents freely or use multiple agents on the same project.
- **Multi-User Personalization**: New `/speckit.personalize` command creates per-user prompt overrides in `.documentation/{git-user}/commands/`. Customize any command without affecting team defaults — personalized files are committed to git for team transparency.
- **Three Pillars Documentation**: All repository and site documentation updated to consistently communicate agent-agnostic architecture, multi-user personalization, and full lifecycle coverage as the three reinforcing design pillars.

## Spark-Specific Features

- **Agent-Agnostic Architecture**: Canonical prompts in `.documentation/commands/` with thin platform shims — every AI assistant is a first-class citizen
- **Multi-User Personalization**: `/speckit.personalize` creates per-user command overrides in `.documentation/{git-user}/commands/` — team governance with individual customization
- **Full Lifecycle Coverage**: From greenfield (`/speckit.specify`) through brownfield (`/speckit.discover-constitution`), maintenance (`/speckit.quickfix`), cleanup (`/speckit.harvest`), release (`/speckit.release`), and evolution (`/speckit.evolve-constitution`)
- **Repo Story**: Generate evidence-based repository narratives from commit history
- **Discover Constitution**: Analyze existing codebases to reverse-engineer project principles
- **PR Review Command**: Constitution-based pull request review workflow
- **Site Audit**: Comprehensive codebase auditing against constitution principles
- **Critic Command**: Adversarial risk analysis for spec artifacts
- **Harvest**: Knowledge-preserving cleanup for stale docs and completed specs
- **Extended Agent Support**: 17+ AI coding assistants supported

## Using This Release

You can use these releases with your agent of choice. We recommend using the Specify CLI to scaffold your projects, however you can download these independently and manage them yourself.

## Recent Changes

### Version 1.5.0 (March 28, 2026)

- New `/speckit.repo-story` command for repository narrative generation
- Paired `repo-story-context.sh` and `repo-story-context.ps1` context scripts
- Branding sweep: "Spec Kit Spark — ASLCD Toolkit" across all files
- README roadmap synced to v1.5.0

### Version 1.4.6 (March 26, 2026)

- PowerShell runtime safety and compatibility hardening
- Markdownlint workflow fixes
- Spark command template path alignment
- Documentation branding consistency updates

### Version 1.4.5 (March 25, 2026)

- Fixed `specify upgrade` crash when AI assistant auto-detection fails

### Version 1.4.0 (March 25, 2026)

- New `/speckit.harvest` command with knowledge-preserving cleanup
- `harvest.ps1` pre-scan script for spec completion and doc taxonomy

### Version 1.1.0 (February 8, 2026)

- New `specify upgrade` command for simplified project upgrades
- Migration scripts for Windows (PowerShell) and Linux/Mac (Bash)
- Comprehensive migration documentation and guides
- Auto-detection of AI assistants and migration needs
- Dry-run mode and safety checks for upgrade process

### Version 1.0.3 (February 6, 2026)

- Fixed critical double documentation path bug
- Enhanced path transformation regex patterns

### Version 1.0.0 (February 3, 2026)

- First major release with standard semantic versioning
- Transition to `.documentation/` directory structure
- Constitution-powered commands
- Extended agent support (17+ AI assistants)

---

*Maintained as a fork of github/spec-kit. Spec Kit Spark is independently evolved and may contain Spark-specific capabilities not present upstream.*
