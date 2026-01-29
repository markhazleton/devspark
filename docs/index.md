# Spec Kit

*Build high-quality software faster.*

**An effort to allow organizations to focus on product scenarios rather than writing undifferentiated code with the help of Spec-Driven Development.**

---

## About This Fork

> **Important**: This is **Spec Kit - Mark Hazleton Edition**, a community fork that extends the original project.
>
> Looking for the original? Visit the official GitHub Spec Kit at: **[github.com/github/spec-kit](https://github.com/github/spec-kit)**

### Why This Fork Exists

The original Spec Kit project established an excellent foundation for Spec-Driven Development. This fork builds upon that great work by adding **constitution-powered commands** that help teams get more value from the effort invested in creating a well-crafted project constitution.

### What's Different

| Feature | Original Spec Kit | This Fork |
|---------|-------------------|-----------|
| Core SDD Workflow | ✅ Full support | ✅ Full support |
| `/speckit.pr-review` | ❌ Not included | ✅ **Added** - Constitution-based PR review |
| `/speckit.site-audit` | ❌ Not included | ✅ **Added** - Full codebase auditing |
| `/speckit.critic` | ❌ Not included | ✅ **Added** - Adversarial risk analysis |
| `/speckit.constitution` | ❌ Not included | ✅ **Added** - Constitution creation helper |
| Multi-agent support | Limited | ✅ **Expanded** - 17+ AI agents supported |

### Philosophy

When you invest time writing a thorough project constitution—defining your security standards, testing requirements, code quality expectations, and governance rules—that document should work hard for you. This fork introduces commands that continuously leverage your constitution to:

- **Review every PR** against your established principles
- **Audit your entire codebase** for compliance violations
- **Identify risks** before they become production issues
- **Maintain consistency** across your team's work

### Credit & Attribution

Full credit goes to the GitHub team for creating the Spec-Driven Development methodology and the original Spec Kit toolkit. This fork is an extension of their work, not a replacement. If you're looking for the official, GitHub-maintained version, please visit [github.com/github/spec-kit](https://github.com/github/spec-kit).

---

## What is Spec-Driven Development?

Spec-Driven Development **flips the script** on traditional software development. For decades, code has been king — specifications were just scaffolding we built and discarded once the "real work" of coding began. Spec-Driven Development changes this: **specifications become executable**, directly generating working implementations rather than just guiding them.

## Getting Started

- [Installation Guide](installation.md)
- [Quick Start Guide](quickstart.md)
- [Upgrade Guide](upgrade.md)
- [Local Development](local-development.md)

## Core Philosophy

Spec-Driven Development is a structured process that emphasizes:

- **Intent-driven development** where specifications define the "*what*" before the "*how*"
- **Rich specification creation** using guardrails and organizational principles
- **Multi-step refinement** rather than one-shot code generation from prompts
- **Heavy reliance** on advanced AI model capabilities for specification interpretation

## Development Phases

| Phase | Focus | Key Activities |
|-------|-------|----------------|
| **0-to-1 Development** ("Greenfield") | Generate from scratch | <ul><li>Start with high-level requirements</li><li>Generate specifications</li><li>Plan implementation steps</li><li>Build production-ready applications</li></ul> |
| **Creative Exploration** | Parallel implementations | <ul><li>Explore diverse solutions</li><li>Support multiple technology stacks & architectures</li><li>Experiment with UX patterns</li></ul> |
| **Iterative Enhancement** ("Brownfield") | Brownfield modernization | <ul><li>Add features iteratively</li><li>Modernize legacy systems</li><li>Adapt processes</li></ul> |
| **Code Review & Quality** | Constitution-based review | <ul><li>Automated PR review with `/speckit.pr-review`</li><li>Codebase auditing with `/speckit.site-audit`</li><li>Risk analysis with `/speckit.critic`</li><li>Track review history and trends</li></ul> |

## Experimental Goals

Our research and experimentation focus on:

### Technology Independence

- Create applications using diverse technology stacks
- Validate the hypothesis that Spec-Driven Development is a process not tied to specific technologies, programming languages, or frameworks

### Enterprise Constraints

- Demonstrate mission-critical application development
- Incorporate organizational constraints (cloud providers, tech stacks, engineering practices)
- Support enterprise design systems and compliance requirements

### User-Centric Development

- Build applications for different user cohorts and preferences
- Support various development approaches (from vibe-coding to AI-native development)

### Creative & Iterative Processes

- Validate the concept of parallel implementation exploration
- Provide robust iterative feature development workflows
- Extend processes to handle upgrades and modernization tasks

## Constitution-Powered Commands (Independent of Spec Workflow)

Spec Kit provides powerful commands that leverage your project constitution for quality assurance. These commands are **independent of the Spec-Driven Development workflow**—they don't require any spec, plan, or tasks to exist. They only need a constitution and can be used on any codebase.

### Pull Request Review (`/speckit.pr-review`)

Review any GitHub Pull Request against your project constitution. Works for any PR in any branch without requiring any spec-driven artifacts.

- **Usage**: `/speckit.pr-review #123` or `/speckit.pr-review` (auto-detect from branch)
- **Output**: Detailed review saved to `/specs/pr-review/pr-{number}.md`
- **Key Features**: Security analysis, code quality assessment, testing validation, approval recommendation

[Full PR Review Guide](pr-review-usage.md)

### Site Audit (`/speckit.site-audit`)

Perform comprehensive codebase audits against your project constitution and standards. Like PR review, this command only requires a constitution—no specs needed.

- **Usage**: `/speckit.site-audit` or `/speckit.site-audit --scope=constitution`
- **Output**: Audit results saved to `/docs/copilot/audit/YYYY-MM-DD_results.md`
- **Key Features**: Security scanning, dependency analysis, code quality metrics, compliance scoring

**Scope Options**:
- `--scope=full` (default) - Complete audit
- `--scope=constitution` - Constitution compliance only
- `--scope=packages` - Package/dependency analysis
- `--scope=quality` - Code quality metrics
- `--scope=unused` - Unused code detection
- `--scope=duplicate` - Duplicate code detection

## Spec Workflow Commands

### Critic (`/speckit.critic`)

Perform adversarial risk analysis identifying technical flaws, implementation hazards, and failure modes. Unlike PR review and site audit, this command **requires the spec workflow**—it analyzes your spec.md, plan.md, and tasks.md files.

- **Usage**: `/speckit.critic` (after `/speckit.tasks`, before `/speckit.implement`)
- **Output**: Risk assessment with Go/No-Go recommendation
- **Key Features**: Showstopper detection, stack-specific risks, constitutional compliance, production failure analysis

**Severity Levels**:
- **SHOWSTOPPER** - Will cause production outage, data loss, or security breach
- **CRITICAL** - Will cause major user-facing issues or costly rework
- **HIGH** - Will cause technical debt or operational burden
- **MEDIUM** - Will slow development or cause minor issues

## Contributing

Please see our [Contributing Guide](https://github.com/MarkHazleton/spec-kit/blob/main/CONTRIBUTING.md) for information on how to contribute to this project.

## Support

For support, please check our [Support Guide](https://github.com/MarkHazleton/spec-kit/blob/main/SUPPORT.md) or open an issue on GitHub.
