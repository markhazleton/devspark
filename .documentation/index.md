# DevSpark

*Build high-quality software faster with AI-driven lifecycle management.*

**An Adaptive System Life Cycle Development (ASLCD) Toolkit** - agent-agnostic, multi-user, and full-lifecycle. A community extension of DevSpark that combines specification-driven development with constitution-powered quality assurance and right-sized workflows for tasks of any complexity.

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

> **Important**: This is **DevSpark**, a community extension that builds upon the original DevSpark project.
>
> Part of the [WebSpark](https://github.com/MarkHazleton?tab=repositories&q=webspark) demonstration suite. Looking for the original? Visit **[github.com/github/spec-kit](https://github.com/github/spec-kit)**

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

### What Makes Spark Different

| Feature | Original devspark | DevSpark |
|---------|-------------------|----------------|
| Core SDD Workflow | ✅ Full support | ✅ Full support |
| `/devspark.constitution` | ✅ Included | ✅ Included |
| `/devspark.discover-constitution` | ❌ | ✅ Brownfield discovery |
| `/devspark.pr-review` | ❌ | ✅ Constitution-based PR review |
| `/devspark.site-audit` | ❌ | ✅ Full codebase auditing |
| `/devspark.critic` | ❌ | ✅ Adversarial risk analysis |
| `/devspark.quickfix` | ❌ | ✅ Lightweight workflow |
| `/devspark.release` | ❌ | ✅ Release documentation |
| `/devspark.evolve-constitution` | ❌ | ✅ Constitution evolution |
| `/devspark.harvest` | ❌ | ✅ Knowledge harvest and cleanup |
| Agent-agnostic architecture | ❌ Duplicated prompts per agent | ✅ Canonical prompts + thin shims |
| Multi-user personalization | ❌ | ✅ `/devspark.personalize` per-user overrides |
| Multi-agent support | Limited | ✅ 17+ AI agents |

Learn more: [Adaptive Lifecycle Documentation](adaptive-lifecycle.md)

---

## Getting Started

### Quick Start

```bash
# Install DevSpark CLI
uv tool install devspark-cli --from git+https://github.com/MarkHazleton/spec-kit.git

# New project (greenfield)
devspark init my-project --ai claude

# Existing project (brownfield)
cd /path/to/existing-project
devspark init --here --ai claude

# Upgrade existing project
devspark upgrade
```

### First Steps by Project Type

#### Greenfield (New Project)

```bash
devspark init my-project --ai claude
cd my-project
/devspark.constitution        # Define governing principles
/devspark.specify             # Create first feature spec
```

#### Brownfield (Existing Project)

```bash
cd /path/to/existing-project
devspark init --here --ai claude
/devspark.discover-constitution   # Analyze existing patterns
/devspark.site-audit              # Baseline technical debt
```

### Guides

- [Installation Guide](installation.md) - Detailed setup for all scenarios
- [Quick Start Guide](quickstart.md) - 6-step process walkthrough
- [Upgrade Guide](upgrade.md) - Updating to latest version
- [Migration Guide](migration-guide.md) - Migrate from old `.specify/` structure
- [Local Development](local-development.md) - Contributing to DevSpark

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
| `/devspark.evolve-constitution` | Propose amendments | [Adaptive Lifecycle](adaptive-lifecycle.md) |

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

See the full [Roadmap](roadmap.md) for details.

---

## Contributing

DevSpark welcomes contributions:

- **Issues**: [Report bugs or request features](https://github.com/MarkHazleton/spec-kit/issues)
- **Discussions**: [Ask questions or share ideas](https://github.com/MarkHazleton/spec-kit/discussions)
- **Pull Requests**: Fork, branch, and submit

See [Local Development](local-development.md) for setup instructions.

---

## Credit & Attribution

Full credit goes to the GitHub team for creating the Spec-Driven Development methodology and the original DevSpark toolkit. DevSpark is an extension of their work, not a replacement. For the official, GitHub-maintained version, visit [github.com/github/spec-kit](https://github.com/github/spec-kit).
