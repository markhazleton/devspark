# Spec Kit Spark v1.5.0

Spec Kit Spark is an Adaptive System Life Cycle Development (ASLCD) toolkit with constitution-powered commands and right-sized workflows. Part of the WebSpark demonstration suite.

## Release Highlights

This release (v1.5.0) introduces the new `/speckit.repo-story` command for generating evidence-based repository narratives, completes a branding alignment sweep, and syncs the README roadmap version with the actual CLI version.

### What's New in v1.5.0

- **`/speckit.repo-story` Command**: Analyze full commit history and produce compelling narratives for business and technical audiences
- **Repository History Context Scripts**: Paired Bash and PowerShell scripts generating commit-audit-ready JSON with anonymized roles, velocity metrics, quality signals, and governance maturity scores
- **Branding Alignment**: Consistent "Spec Kit Spark — ASLCD Toolkit" messaging across all documentation, CLI, and release generators
- **Version Sync**: README roadmap updated from stale v0.0.25 to v1.5.0

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
