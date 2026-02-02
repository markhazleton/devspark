# Spec Kit Spark

*Build high-quality software faster.*

**A community extension of Spec Kit, adding constitution-powered commands that help teams get more value from their project principles.**

---

## About Spec Kit Spark

> **Important**: This is **Spec Kit Spark**, a community extension that builds upon the original Spec Kit project.
>
> Part of the [WebSpark](https://github.com/MarkHazleton?tab=repositories&q=webspark) demonstration suite. Looking for the original? Visit **[github.com/github/spec-kit](https://github.com/github/spec-kit)**

### Why Spec Kit Spark Exists

The original Spec Kit project established an excellent foundation for Spec-Driven Development. Spec Kit Spark builds upon that great work by adding **constitution-powered commands** that help teams get more value from the effort invested in creating a well-crafted project constitution.

### What's Different

| Feature | Original Spec Kit | Spec Kit Spark |
|---------|-------------------|----------------|
| Core SDD Workflow | ✅ Full support | ✅ Full support |
| `/speckit.constitution` | ✅ Included | ✅ Included |
| `/speckit.discover-constitution` | ❌ Not included | ✅ **Added** - Brownfield codebase discovery |
| `/speckit.pr-review` | ❌ Not included | ✅ **Added** - Constitution-based PR review |
| `/speckit.site-audit` | ❌ Not included | ✅ **Added** - Full codebase auditing |
| `/speckit.critic` | ❌ Not included | ✅ **Added** - Adversarial risk analysis |
| Multi-agent support | Limited | ✅ **Expanded** - 17+ AI agents supported |

### Philosophy

The original Spec Kit included the constitution concept to define project principles. Spec Kit Spark extends that investment by adding commands that **continuously leverage your constitution** beyond just the spec workflow:

- **Discover principles** from existing codebases (`/speckit.discover-constitution`)
- **Review every PR** against your established principles (`/speckit.pr-review`)
- **Audit your entire codebase** for compliance violations (`/speckit.site-audit`)
- **Identify risks** before they become production issues (`/speckit.critic`)

### Credit & Attribution

Full credit goes to the GitHub team for creating the Spec-Driven Development methodology and the original Spec Kit toolkit. Spec Kit Spark is an extension of their work, not a replacement. If you're looking for the official, GitHub-maintained version, please visit [github.com/github/spec-kit](https://github.com/github/spec-kit).

---

## What is Spec-Driven Development?

Spec-Driven Development **flips the script** on traditional software development. For decades, code has been king — specifications were just scaffolding we built and discarded once the "real work" of coding began. Spec-Driven Development changes this: **specifications become executable**, directly generating working implementations rather than just guiding them.

## Getting Started

### Greenfield (New Projects)

Starting fresh? Initialize a new project with full Spec Kit scaffolding:

```bash
uvx --from git+https://github.com/MarkHazleton/spec-kit.git specify init <PROJECT_NAME>
```

### Brownfield (Existing Projects)

Adding Spec Kit to an existing codebase? Initialize in your project directory:

```bash
cd /path/to/your-existing-project
uvx --from git+https://github.com/MarkHazleton/spec-kit.git specify init --here
```

After initialization, use `/speckit.discover-constitution` to analyze your existing code patterns and draft a constitution that reflects your established conventions.

### Guides

- [Installation Guide](installation.md) - Detailed setup for all scenarios
- [Quick Start Guide](quickstart.md) - 6-step process walkthrough
- [Upgrade Guide](upgrade.md) - Updating to latest version
- [Local Development](local-development.md) - Contributing to Spec Kit

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

### Discover Constitution (`/speckit.discover-constitution`) - NEW

**For brownfield projects**: Analyze your existing codebase to discover implicit patterns and conventions, then interactively build a constitution through guided questions.

- **Usage**: `/speckit.discover-constitution` or with focus: `/speckit.discover-constitution Focus on security and testing`
- **Output**: Draft constitution at `/.documentation/memory/constitution-draft.md`
- **Key Features**: Pattern detection, interactive questioning, gap analysis, draft generation

**How it works**:
1. Scans codebase for patterns (testing, security, architecture, code quality)
2. Reports high-confidence patterns (>80% consistent) vs. inconsistent areas
3. Asks 8-10 targeted questions to validate findings and fill gaps
4. Generates draft constitution for team review

**Ideal for**: Teams adopting Spec Kit on existing projects where principles exist in code but aren't documented.

### Pull Request Review (`/speckit.pr-review`)

Review any GitHub Pull Request against your project constitution. Works for any PR in any branch without requiring any spec-driven artifacts.

- **Usage**: `/speckit.pr-review #123` or `/speckit.pr-review` (auto-detect from branch)
- **Output**: Detailed review saved to `/.documentation/specs/pr-review/pr-{number}.md`
- **Key Features**: Security analysis, code quality assessment, testing validation, approval recommendation

[Full PR Review Guide](pr-review-usage.md)

### Site Audit (`/speckit.site-audit`)

Perform comprehensive codebase audits against your project constitution and standards. Like PR review, this command only requires a constitution—no specs needed.

- **Usage**: `/speckit.site-audit` or `/speckit.site-audit --scope=constitution`
- **Output**: Audit results saved to `/.documentation/copilot/audit/YYYY-MM-DD_results.md`
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
