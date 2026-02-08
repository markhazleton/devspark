# Spec Kit Spark

*Build high-quality software faster with AI-driven lifecycle management.*

**An Adaptive System Life Cycle Development (ASLCD) Toolkit** - a community extension of Spec Kit that combines specification-driven development with constitution-powered quality assurance and right-sized workflows for tasks of any complexity.

---

## About Spec Kit Spark

> **Important**: This is **Spec Kit Spark**, a community extension that builds upon the original Spec Kit project.
>
> Part of the [WebSpark](https://github.com/MarkHazleton?tab=repositories&q=webspark) demonstration suite. Looking for the original? Visit **[github.com/github/spec-kit](https://github.com/github/spec-kit)**

### The ASLCD Vision

Traditional spec-driven development works well for greenfield projects with major features. But real-world development includes bug fixes, hotfixes, brownfield codebases, and documentation that drifts over time. **Adaptive System Life Cycle Development** addresses these gaps:

| Challenge | ASLCD Solution |
|-----------|----------------|
| Greenfield bias | `/speckit.discover-constitution` generates constitutions from existing code |
| Task overhead | `/speckit.quickfix` provides lightweight workflow for small tasks |
| Documentation drift | `/speckit.release` archives artifacts and maintains living documentation |
| Constitution staleness | `/speckit.evolve-constitution` proposes amendments from PR findings |
| Context management | Right-sized workflows optimize AI agent effectiveness |

### What Makes Spark Different

| Feature | Original Spec Kit | Spec Kit Spark |
|---------|-------------------|----------------|
| Core SDD Workflow | ✅ Full support | ✅ Full support |
| `/speckit.constitution` | ✅ Included | ✅ Included |
| `/speckit.discover-constitution` | ❌ | ✅ Brownfield discovery |
| `/speckit.pr-review` | ❌ | ✅ Constitution-based PR review |
| `/speckit.site-audit` | ❌ | ✅ Full codebase auditing |
| `/speckit.critic` | ❌ | ✅ Adversarial risk analysis |
| `/speckit.quickfix` | ❌ | ✅ Lightweight workflow |
| `/speckit.release` | ❌ | ✅ Release documentation |
| `/speckit.evolve-constitution` | ❌ | ✅ Constitution evolution |
| Multi-agent support | Limited | ✅ 17+ AI agents |

Learn more: [Adaptive Lifecycle Documentation](adaptive-lifecycle.md)

---

## Getting Started

### Quick Start

```bash
# Install Specify CLI
uv tool install specify-cli --from git+https://github.com/MarkHazleton/spec-kit.git

# New project (greenfield)
specify init my-project --ai claude

# Existing project (brownfield)
cd /path/to/existing-project
specify init --here --ai claude

# Upgrade existing project
specify upgrade
```

### First Steps by Project Type

#### Greenfield (New Project)

```bash
specify init my-project --ai claude
cd my-project
/speckit.constitution        # Define governing principles
/speckit.specify             # Create first feature spec
```

#### Brownfield (Existing Project)

```bash
cd /path/to/existing-project
specify init --here --ai claude
/speckit.discover-constitution   # Analyze existing patterns
/speckit.site-audit              # Baseline technical debt
```

### Guides

- [Installation Guide](installation.md) - Detailed setup for all scenarios
- [Quick Start Guide](quickstart.md) - 6-step process walkthrough
- [Upgrade Guide](upgrade.md) - Updating to latest version (NEW in v1.1.0)
- [Migration Guide](migration-guide.md) - Migrate from old `.specify/` structure (NEW in v1.1.0)
- [Local Development](local-development.md) - Contributing to Spec Kit

---

## Core Concepts

### The Constitution

The **constitution** is the foundational document defining your project's architecture, coding standards, and development guidelines. All Spec Kit commands reference the constitution for validation.

- **Create**: `/speckit.constitution` - Define principles for new projects
- **Discover**: `/speckit.discover-constitution` - Generate from existing code
- **Evolve**: `/speckit.evolve-constitution` - Propose amendments
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
| `/speckit.constitution` | Create/update constitution | [Constitution Guide](constitution-guide.md) |
| `/speckit.discover-constitution` | Generate from existing code | [Constitution Guide](constitution-guide.md) |
| `/speckit.evolve-constitution` | Propose amendments | [Adaptive Lifecycle](adaptive-lifecycle.md) |

### Full Spec Workflow

For major features and architectural changes.

| Command | Purpose | Next Step |
|---------|---------|-----------|
| `/speckit.specify` | Define requirements | `/speckit.plan` |
| `/speckit.plan` | Technical planning | `/speckit.tasks` |
| `/speckit.tasks` | Task breakdown | `/speckit.critic` |
| `/speckit.critic` | Risk analysis | `/speckit.implement` |
| `/speckit.implement` | Execute tasks | PR Review |

### Lightweight Workflow

For bug fixes, hotfixes, and small features.

| Command | Purpose |
|---------|---------|
| `/speckit.quickfix` | Create, validate, and track quick fixes |

### Quality Assurance

Constitution-powered quality commands that work independently.

| Command | Purpose | Guide |
|---------|---------|-------|
| `/speckit.pr-review` | Review PRs against constitution | [PR Review Guide](pr-review-usage.md) |
| `/speckit.site-audit` | Codebase compliance audit | [Site Audit Guide](site-audit-usage.md) |
| `/speckit.critic` | Adversarial risk analysis | [Critic Guide](critic-usage.md) |

### Lifecycle Commands

| Command | Purpose |
|---------|---------|
| `/speckit.release` | Archive artifacts, generate release docs |
| `/speckit.clarify` | Clarify specification requirements |
| `/speckit.checklist` | Generate quality checklists |
| `/speckit.analyze` | Artifact consistency checking |

---

## Development Phases

| Phase | Commands | Activities |
|-------|----------|------------|
| **Project Initiation** | `constitution`, `discover-constitution` | Establish governing principles |
| **Baseline Assessment** | `site-audit` | Quantify technical debt |
| **Feature Development** | `specify`, `plan`, `tasks`, `implement` | Full spec workflow |
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

Spec Kit Spark is actively developed with plans for:

- **Enhanced Debt Tracking** - Structured metrics storage and visualization
- **Business Value Alignment** - Link features to business goals
- **CI/CD Integration** - Run audits as pipeline steps
- **Cross-Project Governance** - Organizational-level consistency

See the full [Roadmap](roadmap.md) for details.

---

## Contributing

Spec Kit Spark welcomes contributions:

- **Issues**: [Report bugs or request features](https://github.com/MarkHazleton/spec-kit/issues)
- **Discussions**: [Ask questions or share ideas](https://github.com/MarkHazleton/spec-kit/discussions)
- **Pull Requests**: Fork, branch, and submit

See [Local Development](local-development.md) for setup instructions.

---

## Credit & Attribution

Full credit goes to the GitHub team for creating the Spec-Driven Development methodology and the original Spec Kit toolkit. Spec Kit Spark is an extension of their work, not a replacement. For the official, GitHub-maintained version, visit [github.com/github/spec-kit](https://github.com/github/spec-kit).
