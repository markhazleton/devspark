# Adaptive System Life Cycle Development

> An AI-Agent Driven Approach to Software Development Life Cycle Management

---

## Executive Summary

The **Adaptive System Life Cycle Development (ASLCD) Toolkit** extends Spec Kit to manage the complete software development life cycle using AI-driven agents. It addresses critical gaps in traditional spec-driven tools: brownfield implementation support, right-sized workflows for varying task complexity, and documentation lifecycle management.

The toolkit provides a balanced approach combining the rigor of traditional SDLC methodologies with the agility and efficiency of modern AI-driven development practices, creating a truly adaptive system that evolves alongside the applications it manages.

---

## Problem Statement

### Identified Gaps in Traditional Tooling

| Gap | Description | Impact |
|-----|-------------|--------|
| **Greenfield Bias** | Existing spec-driven tools work well for new projects but struggle with brownfield applications | Teams can't adopt structured development on existing codebases |
| **Task Overhead** | Full spec-task-plan workflows are overkill for bug fixes and small features | Unnecessary friction slows production support |
| **Context Management** | Difficulty determining appropriate context levels for AI agents | Token inefficiency or "lost in the middle" degradation |
| **Documentation Drift** | Accumulation of development artifacts that clutter and lose relevance | Outdated specs create confusion |
| **Constitution Staleness** | No formal process for evolving system constitution | Architecture drifts from documented principles |
| **Business Value Disconnect** | Lack of mechanisms to document business value alignment | Development loses connection to business goals |

---

## Design Principles

### 1. Universality over Opinion

Focus on core, universal prompts that can be adapted rather than highly opinionated single-use prompts. This enables teams to customize workflows without losing the framework's benefits.

### 2. Right-Sized Rigor

Match process overhead to task complexity:

| Task Type | Workflow | Overhead |
|-----------|----------|----------|
| Major Feature | Full Spec-Task-Plan | High - complete specification and planning |
| Architectural Change | Full Spec-Task-Plan + Constitution Update | High - includes governance review |
| Minor Feature | Quickfix with validation | Low - lightweight record, targeted validation |
| Bug Fix | Quickfix | Low - minimal documentation |
| Hotfix | Quickfix (expedited) | Minimal - rapid response |
| Configuration Change | Quickfix | Minimal - record only |

### 3. Continuous Compliance

Integrate constitution validation throughout the development process, not just at review time:

- **Creation**: Validate new specs against constitution principles
- **Planning**: Ensure technical choices align with architectural guidelines
- **Implementation**: Targeted validation during quickfixes
- **Review**: Full constitution-based PR review
- **Release**: Constitution version tracking with releases

### 4. Adaptive Evolution

Systems and documentation must evolve together:

- Constitutions must be updated when architecture changes
- Documentation lifecycle managed explicitly at release boundaries
- Historical decisions preserved for future reference

---

## Functional Architecture

### Constitution Management

The constitution serves as the foundational document defining system architecture, coding standards, and development guidelines.

```text
Constitution Lifecycle:
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │ Discover │ → │  Create  │ → │  Evolve  │ → │  Archive │    │
│  │ Patterns │   │   v1.0   │   │ v1.1,1.2 │   │ History  │    │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │
│       ↑                              ↑                         │
│       │                              │                         │
│  Brownfield               PR Review Triggers                   │
│  Analysis                 Evolution Proposals                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Commands:**

- `/speckit.constitution` - Create or update constitution
- `/speckit.discover-constitution` - Generate from existing codebase (brownfield)
- `/speckit.evolve-constitution` - Propose amendments based on findings

### Development Workflow Support

The toolkit provides workflows scaled to task complexity:

```text
Task Complexity Routing:
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    ┌─────────────────┐                         │
│                    │  Task Arrives   │                         │
│                    └────────┬────────┘                         │
│                             │                                   │
│              ┌──────────────┼──────────────┐                   │
│              ▼              ▼              ▼                   │
│     ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│     │  Bug Fix   │  │   Minor    │  │   Major    │            │
│     │  Hotfix    │  │  Feature   │  │  Feature   │            │
│     └──────┬─────┘  └──────┬─────┘  └──────┬─────┘            │
│            │               │               │                   │
│            ▼               ▼               ▼                   │
│     ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│     │ /quickfix  │  │ /quickfix  │  │  /specify  │            │
│     │            │  │    or      │  │  /plan     │            │
│     │            │  │  /specify  │  │  /tasks    │            │
│     └──────┬─────┘  └──────┬─────┘  └──────┬─────┘            │
│            │               │               │                   │
│            └───────────────┼───────────────┘                   │
│                            ▼                                   │
│                   ┌────────────────┐                           │
│                   │  Constitution  │                           │
│                   │  Validation    │                           │
│                   └────────────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Full Spec Workflow:**

```bash
/speckit.specify    # Define requirements
/speckit.plan       # Technical planning
/speckit.tasks      # Task breakdown
/speckit.critic     # Risk analysis
/speckit.implement  # Execute implementation
```

**Lightweight Workflow:**

```bash
/speckit.quickfix   # Create, validate, implement, complete
```

### Pull Request Integration

PRs serve dual purposes: code review and constitution evolution triggers.

```text
PR Review Flow:
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ┌──────────┐   ┌───────────────┐   ┌──────────────────────┐  │
│  │   PR     │ → │  /pr-review   │ → │  Review Report       │  │
│  │ Created  │   │               │   │  /.documentation/    │  │
│  └──────────┘   └───────┬───────┘   │  specs/pr-review/    │  │
│                         │           └──────────────────────┘  │
│                         │                                      │
│                         ▼                                      │
│              ┌────────────────────┐                           │
│              │ Constitution Check │                           │
│              └─────────┬──────────┘                           │
│                        │                                       │
│         ┌──────────────┼──────────────┐                       │
│         ▼              ▼              ▼                       │
│    ┌─────────┐   ┌──────────┐   ┌──────────────┐             │
│    │  PASS   │   │ VIOLATION│   │ EVOLUTION    │             │
│    │ Approve │   │ Request  │   │ TRIGGER      │             │
│    │         │   │ Changes  │   │ (Arch Change)│             │
│    └─────────┘   └──────────┘   └──────┬───────┘             │
│                                         │                      │
│                                         ▼                      │
│                              ┌──────────────────┐             │
│                              │/evolve-constitution            │
│                              │ Propose Amendment│             │
│                              └──────────────────┘             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Adaptive Documentation

Documentation lifecycle management ensures artifacts remain current:

```text
Documentation Lifecycle:
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  DEVELOPMENT PHASE                    RELEASE PHASE            │
│  ─────────────────                    ─────────────            │
│                                                                 │
│  ┌────────────┐                       ┌────────────┐           │
│  │ spec.md    │ ──────────────────▶  │ ARCHIVE    │           │
│  │ plan.md    │      /release         │ releases/  │           │
│  │ tasks.md   │                       │ v{X.Y.Z}/  │           │
│  │ research.md│                       └────────────┘           │
│  └────────────┘                              │                  │
│        │                                     │                  │
│        │                                     ▼                  │
│        │                              ┌────────────┐           │
│        │                              │   ADR      │           │
│        │                              │ Extraction │           │
│        │                              └────────────┘           │
│        │                                     │                  │
│        ▼                                     ▼                  │
│  ┌────────────┐                       ┌────────────┐           │
│  │ Active     │                       │ CHANGELOG  │           │
│  │ Development│                       │ Release    │           │
│  │ Artifacts  │                       │ Notes      │           │
│  └────────────┘                       └────────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Principle**: Development artifacts (specs, plans, tasks) are working documents. At release boundaries, they are:

1. Archived with the release version
2. Key decisions extracted as ADRs
3. Summarized in release notes
4. Cleared for next development cycle

---

## Command Reference

### Constitution Commands

| Command | Purpose | Requires |
|---------|---------|----------|
| `/speckit.constitution` | Create/update constitution | - |
| `/speckit.discover-constitution` | Generate from existing code | Existing codebase |
| `/speckit.evolve-constitution` | Propose amendments | Constitution, PR reviews |

### Development Workflow Commands

| Command | Purpose | Requires |
|---------|---------|----------|
| `/speckit.specify` | Create feature specification | Constitution |
| `/speckit.plan` | Technical implementation plan | Spec |
| `/speckit.tasks` | Task breakdown | Plan |
| `/speckit.implement` | Execute implementation | Tasks |
| `/speckit.quickfix` | Lightweight fix workflow | Constitution |

### Quality Assurance Commands

| Command | Purpose | Requires |
|---------|---------|----------|
| `/speckit.pr-review` | Review PR against constitution | Constitution, PR |
| `/speckit.site-audit` | Codebase compliance audit | Constitution |
| `/speckit.critic` | Adversarial risk analysis | Spec, Plan, Tasks |
| `/speckit.analyze` | Artifact consistency check | Spec, Plan, Tasks |

### Lifecycle Commands

| Command | Purpose | Requires |
|---------|---------|----------|
| `/speckit.release` | Archive artifacts, generate release docs | Completed specs |
| `/speckit.clarify` | Clarify specification requirements | Spec |
| `/speckit.checklist` | Generate quality checklists | Spec |

---

## Process Lifecycle Integration

### Phase Mapping

| Phase | Primary Commands | Key Activities |
|-------|-----------------|----------------|
| **Project Initiation** | `constitution`, `discover-constitution` | Establish or discover governing principles |
| **Baseline Assessment** | `site-audit` | Quantify existing technical debt |
| **Feature Development** | `specify`, `plan`, `tasks`, `implement` | Full specification-driven development |
| **Production Support** | `quickfix` | Rapid fixes with targeted validation |
| **Code Review** | `pr-review` | Constitution compliance, evolution triggers |
| **Risk Analysis** | `critic` | Pre-implementation risk assessment |
| **Release** | `release` | Archive artifacts, update documentation |
| **Maintenance** | `site-audit`, `evolve-constitution` | Monitor drift, update governance |

### Workflow Selection Guide

```text
Should I use full spec workflow or quickfix?
─────────────────────────────────────────────

                    ┌──────────────────────┐
                    │ Is this a bug fix or │
                    │ production hotfix?   │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │ YES                            │ NO
              ▼                                ▼
      ┌───────────────┐              ┌───────────────────┐
      │ Use /quickfix │              │ Does it change    │
      │               │              │ multiple files or │
      │               │              │ system behavior?  │
      └───────────────┘              └─────────┬─────────┘
                                               │
                            ┌──────────────────┼──────────────────┐
                            │ YES                               │ NO
                            ▼                                   ▼
                    ┌───────────────┐                   ┌───────────────┐
                    │ Use full spec │                   │ Use /quickfix │
                    │ workflow      │                   │ (with review) │
                    └───────────────┘                   └───────────────┘
```

---

## Technical Debt Management

The ASLCD approach treats technical debt as measurable and trackable:

### Definition

> **Technical Debt** = Code that does not adhere to constitution standards, requiring future remediation.

### Quantification

Site audits produce compliance scores:

```markdown
| Category | Score | Status |
|----------|-------|--------|
| Constitution Compliance | 87% | ⚠️ PARTIAL |
| Security | 95% | ✅ PASS |
| Code Quality | 72% | ⚠️ PARTIAL |
| Test Coverage | 68% | ⚠️ PARTIAL |
| Documentation | 90% | ✅ PASS |
| Dependencies | 85% | ⚠️ PARTIAL |
```

### Tracking Over Time

Each site audit is saved with a timestamp, enabling trend analysis:

```text
Technical Debt Trend:
┌─────────────────────────────────────────────────────────────────┐
│ Compliance %                                                    │
│     100 ┤                                                       │
│      90 ┤                    ╭──────────────╮                   │
│      80 ┤     ╭──────────────╯              │                   │
│      70 ┤─────╯                             │                   │
│      60 ┤                                   │                   │
│         └───────────────────────────────────┼───────────────▶   │
│          Jan    Feb    Mar    Apr    May    Jun                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## AI Agent Context Optimization

Effective AI agent utilization requires careful context management:

### Context Sizing by Task Type

| Task Type | Context Level | What to Include |
|-----------|---------------|-----------------|
| Quickfix | Minimal | Constitution principles for task type, affected file(s) |
| Minor Feature | Targeted | Relevant spec sections, affected components |
| Major Feature | Comprehensive | Full spec, plan, constitution, related code |
| Site Audit | Broad | Constitution, file categorization, metrics |
| PR Review | Focused | Constitution, PR diff, changed files only |

### Avoiding "Lost in the Middle"

AI agents experience degradation when relevant context is buried among irrelevant information. The ASLCD commands:

1. **Extract only relevant principles** - Quickfix only loads principles for the task type
2. **Scope searches appropriately** - Site audit uses categorized file lists
3. **Provide focused context** - PR review includes diff, not entire codebase

---

## Success Criteria

The ASLCD toolkit succeeds when:

- ✅ Brownfield implementations can generate actionable constitutions within one iteration
- ✅ Bug fixes and small features complete without full spec overhead
- ✅ Technical debt is measurable and trackable over time
- ✅ Documentation remains current with less than 10% obsolete artifacts
- ✅ Constitution evolves in sync with architectural changes
- ✅ AI agent effectiveness maintained across task types with optimized context

---

## Glossary

| Term | Definition |
|------|------------|
| **Constitution** | The foundational document defining system architecture, coding standards, and development guidelines |
| **Adaptive Documentation** | Documentation that evolves continuously alongside the system it describes, maintaining relevance through active management |
| **Brownfield** | An existing application or codebase that must be analyzed and documented rather than built from scratch |
| **Greenfield** | A new project starting from scratch with no existing codebase constraints |
| **Site Audit** | Analysis of codebase compliance against the constitution to quantify technical debt |
| **Technical Debt** | Code that does not adhere to constitution standards, requiring future remediation |
| **Lost in the Middle** | AI agent performance degradation when relevant context is buried among irrelevant information |
| **Right-Sized** | Appropriate level of process overhead and context for a given task complexity |
| **ADR** | Architecture Decision Record - permanent documentation of a key technical decision |
| **CAP** | Constitution Amendment Proposal - formal proposal to modify constitution |

---

## Learn More

- [Quick Start Guide](quickstart.md) - Get started in 6 steps
- [Constitution Guide](constitution-guide.md) - Creating effective project principles
- [PR Review Guide](pr-review-usage.md) - Constitution-based code review
- [Site Audit Guide](site-audit-usage.md) - Codebase compliance auditing
- [Critic Guide](critic-usage.md) - Adversarial risk analysis
