# DevSpark

*Build high-quality software faster with AI-driven lifecycle management.*

**An Adaptive System Life Cycle Development (ASLCD) Toolkit** — agent-agnostic, multi-user, and full-lifecycle. DevSpark combines specification-driven development with constitution-powered quality assurance and right-sized workflows for tasks of any complexity.

<video controls width="100%">
  <source src="https://github.com/markhazleton/devspark/releases/download/v0.1.0/DevSpark__Giving_Your_AI_a_Process.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

---

## Three Pillars

### 🔀 Agent-Agnostic by Default

Every AI coding assistant is a first-class citizen. Canonical command prompts live in `.documentation/commands/` — a single source of truth — while each platform receives only thin shims. Switch agents, use multiple agents on the same project, or onboard new team members on different tools.

### 👥 Multi-User Personalization

Teams share prompts, but individuals can customize any command via `/devspark.personalize`. Personalized overrides live in `.documentation/{git-user}/commands/`, are committed to git, and take priority over shared defaults. Delete the override to revert.

### 🔄 Full Lifecycle Coverage

From greenfield creation through brownfield discovery, ongoing maintenance, documentation cleanup, release management, and constitution evolution — every phase of the SDLC is supported.

---

## About DevSpark

> **DevSpark** is a structured development process for AI coding assistants — 24 prompt templates + helper scripts that give any AI agent a repeatable workflow from requirements through release.

### The ASLCD Vision

Traditional spec-driven development works well for greenfield projects with major features. But real-world development includes bug fixes, hotfixes, brownfield codebases, and documentation that drifts over time. **Adaptive System Life Cycle Development** addresses these gaps:

| Challenge | ASLCD Solution |
|-----------|----------------|
| Greenfield bias | `/devspark.discover-constitution` generates constitutions from existing code |
| Task overhead | `/devspark.quickfix` provides lightweight workflow for small tasks |
| Documentation drift | `/devspark.release` archives artifacts and maintains living documentation |
| Repo clutter | `/devspark.harvest` consolidates knowledge and archives obsolete artifacts |
| Constitution staleness | `/devspark.evolve-constitution` proposes amendments from PR findings |
| Context management | Right-sized workflows optimize AI agent effectiveness |

### What's Included

| Feature | Status |
|---------|--------|
| Core SDD Workflow | ✅ Full support |
| `/devspark.constitution` | ✅ Included |
| `/devspark.discover-constitution` | ✅ Brownfield discovery |
| `/devspark.pr-review` | ✅ Constitution-based PR review |
| `/devspark.site-audit` | ✅ Full codebase auditing |
| `/devspark.critic` | ✅ Adversarial risk analysis |
| `/devspark.quickfix` | ✅ Lightweight workflow |
| `/devspark.release` | ✅ Release documentation |
| `/devspark.evolve-constitution` | ✅ Constitution evolution |
| `/devspark.harvest` | ✅ Knowledge harvest and cleanup |
| Agent-agnostic architecture | ✅ Canonical prompts + thin shims |
| Multi-user personalization | ✅ `/devspark.personalize` per-user overrides |
| Multi-agent support | ✅ 17+ AI agents |
| Multi-app monorepo support | ✅ Optional — profile-based inheritance, scoped commands |

---

## Getting Started

### Prompt Bootstrap — The Fastest Way

No installation required. Open a chat with your AI agent in your target repository and paste the command for your agent:

| Agent | Command to paste |
|-------|-----------------|
| **GitHub Copilot** | `@workspace Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_copilot.md` |
| **Claude Code** | `Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_claudecode.md` |
| **Cursor** | `Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_cursor.md` |
| **Any other agent** | `Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_generic.md` |

The agent asks a few questions about your project, then scaffolds the full DevSpark structure. See the [Quick Start Guide](quickstart.md) for the full workflow.

For updates, use the same prompt-first approach:

```text
Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/templates/commands/upgrade.md
```

This is the normal way to keep DevSpark current. CLI is optional and intended for advanced automation only.

> **Need advanced or terminal-driven setup?** See [Other Ways to Get Started](installation.md) for manual and CLI options.

### Guides

- [Implementation Lifecycle Guide](implementation-lifecycle.md) — Prompt-first quickstart, feature workflow, and updates
- [Quick Start Guide](quickstart.md) — Prompt bootstrap + 5-step workflow
- [Other Ways to Get Started](installation.md) — Advanced manual and CLI options
- [Upgrade Guide](upgrade.md) — Prompt-first updates, CLI optional
- [Monorepo Guide](monorepo-guide.md) — Optional multi-application monorepo support

---

## Core Concepts

### The Constitution

The **constitution** is the foundational document defining your project's architecture, coding standards, and development guidelines. All DevSpark commands reference the constitution for validation.

- **Create**: `/devspark.constitution` - Define principles for new projects
- **Discover**: `/devspark.discover-constitution` - Generate from existing code
- **Evolve**: `/devspark.evolve-constitution` - Propose amendments
- **Learn More**: [Constitution Guide](constitution-guide.md)

### Right-Sized Workflows

Match process overhead to task complexity:

| Task Type | Workflow | When to Use |
|-----------|----------|-------------|
| Major Feature | Full Spec | Multiple files, architectural impact |
| Bug Fix | Quickfix | Single file, clear root cause |
| Hotfix | Quickfix (expedited) | Production emergency |
| Minor Feature | Quickfix or Spec | Depends on scope |

### Adaptive Documentation

Documentation evolves with your system:

1. **Development**: Specs, plans, tasks guide implementation
2. **Release**: Artifacts archived, decisions extracted as ADRs
3. **Maintenance**: Constitution updated as architecture evolves

---

## Command Categories

### Constitution Commands

| Command | Purpose | Guide |
|---------|---------|-------|
| `/devspark.constitution` | Create/update constitution | [Constitution Guide](constitution-guide.md) |
| `/devspark.discover-constitution` | Generate from existing code | [Constitution Guide](constitution-guide.md) |
| `/devspark.evolve-constitution` | Propose amendments | [Constitution Guide](constitution-guide.md) |

### Full Spec Workflow

For major features and architectural changes.

| Command | Purpose | Next Step |
|---------|---------|-----------|
| `/devspark.specify` | Define requirements | `/devspark.plan` |
| `/devspark.plan` | Technical planning | `/devspark.tasks` |
| `/devspark.tasks` | Task breakdown | `/devspark.critic` |
| `/devspark.critic` | Risk analysis | `/devspark.implement` |
| `/devspark.implement` | Execute tasks | PR Review |

### Lightweight Workflow

For bug fixes, hotfixes, and small features.

| Command | Purpose |
|---------|---------|
| `/devspark.quickfix` | Create, validate, and track quick fixes |

### Quality Assurance

Constitution-powered quality commands that work independently.

| Command | Purpose | Guide |
|---------|---------|-------|
| `/devspark.pr-review` | Review PRs against constitution | [PR Review Guide](pr-review-usage.md) |
| `/devspark.site-audit` | Codebase compliance audit | [Site Audit Guide](site-audit-usage.md) |
| `/devspark.critic` | Adversarial risk analysis | [Critic Guide](critic-usage.md) |

### Lifecycle Commands

| Command | Purpose |
|---------|---------|
| `/devspark.release` | Archive artifacts, generate release docs |
| `/devspark.harvest` | Knowledge-preserving cleanup for stale docs |
| `/devspark.repo-story` | Evidence-based repository narrative generation |
| `/devspark.clarify` | Clarify specification requirements |
| `/devspark.checklist` | Generate quality checklists |
| `/devspark.analyze` | Artifact consistency checking |
| `/devspark.personalize` | Create per-user prompt customizations |

### Multi-App Commands (Optional)

For repositories containing multiple applications with different platforms or governance rules. Single-app repositories can skip these entirely.

| Command | Purpose |
|---------|---------|
| `/devspark.add-application` | Register a new application in the multi-app registry |
| `/devspark.list-applications` | Display all registered applications and profiles |
| `/devspark.validate-registry` | Validate registry schema, references, and consistency |

> **Opt-in only**: Multi-app support is activated by creating a registry at `.documentation/devspark.json`. Without it, DevSpark operates in standard single-app mode with no behavior changes.

---

## Development Phases

| Phase | Commands | Activities |
|-------|----------|------------|
| **Project Initiation** | `constitution`, `discover-constitution` | Establish governing principles |
| **Baseline Assessment** | `site-audit` | Quantify technical debt |
| **Feature Development** | `devspark`, `plan`, `tasks`, `implement` | Full spec workflow |
| **Production Support** | `quickfix` | Rapid fixes with validation |
| **Code Review** | `pr-review` | Constitution compliance |
| **Risk Analysis** | `critic` | Pre-implementation assessment |
| **Release** | `release` | Archive and document |
| **Maintenance** | `site-audit`, `evolve-constitution` | Monitor and evolve |

---

## Technical Debt as a Metric

Site audits quantify technical debt through compliance scores:

```markdown
| Category | Score | Status |
|----------|-------|--------|
| Constitution Compliance | 87% | ⚠️ PARTIAL |
| Security | 95% | ✅ PASS |
| Code Quality | 72% | ⚠️ PARTIAL |
| Dependencies | 85% | ⚠️ PARTIAL |
```

Track trends over time by running regular audits and comparing results.

---

## Future Direction

DevSpark is actively developed with plans for:

- **Enhanced Debt Tracking** - Structured metrics storage and visualization
- **Business Value Alignment** - Link features to business goals
- **CI/CD Integration** - Run audits as pipeline steps
- **Cross-Project Governance** - Organizational-level consistency

---

## Contributing

DevSpark welcomes contributions:

- **Issues**: [Report bugs or request features](https://github.com/MarkHazleton/devspark/issues)
- **Discussions**: [Ask questions or share ideas](https://github.com/MarkHazleton/devspark/discussions)
- **Pull Requests**: Fork, branch, and submit

See [CONTRIBUTING.md](https://github.com/MarkHazleton/devspark/blob/main/CONTRIBUTING.md) for setup instructions.

---

## Credit & Attribution

DevSpark is maintained by [Mark Hazleton](https://github.com/markhazleton) and the open-source community.
