# Specification-Driven Development (SDD)

## Overview

**Specification-Driven Development (SDD)** is a methodology that inverts the traditional relationship between specifications and code. Instead of specifications serving code, code serves specifications. The Product Requirements Document (PRD) isn't a guide for implementation—it's the source that *generates* implementation.

This isn't an incremental improvement to how we build software. It's a fundamental rethinking of what drives development.

## The Power Inversion

For decades, code has been king. Specifications served code—they were the scaffolding we built and then discarded once the "real work" of coding began. We wrote PRDs to guide development, created design docs to inform implementation, drew diagrams to visualize architecture. But these were always subordinate to the code itself.

SDD eliminates the gap between specification and implementation by making specifications executable. When specifications generate code, there is no gap—only transformation.

### Key Principles

| Principle | Description |
|-----------|-------------|
| **Specifications as Lingua Franca** | The specification becomes the primary artifact. Code becomes its expression in a particular language and framework. |
| **Executable Specifications** | Specifications must be precise, complete, and unambiguous enough to generate working systems. |
| **Continuous Refinement** | Consistency validation happens continuously, not as a one-time gate. |
| **Research-Driven Context** | Research agents gather critical context throughout the specification process. |
| **Bidirectional Feedback** | Production reality informs specification evolution. |
| **Branching for Exploration** | Generate multiple implementation approaches from the same specification. |

## The SDD Workflow in Practice

The workflow begins with an idea—often vague and incomplete. Through iterative dialogue with AI, this idea becomes a comprehensive PRD:

1. **Specification Phase**: AI asks clarifying questions, identifies edge cases, and helps define precise acceptance criteria
2. **Research Phase**: Agents gather critical context—library compatibility, performance benchmarks, security implications
3. **Planning Phase**: AI generates implementation plans that map requirements to technical decisions
4. **Code Generation Phase**: Domain concepts become data models, user stories become API endpoints, acceptance scenarios become tests
5. **Feedback Loop**: Production metrics and incidents update specifications for the next regeneration

## Why SDD Matters Now

Three trends make SDD not just possible but necessary:

### 1. AI Capabilities

AI can now understand and implement complex specifications. This isn't about replacing developers—it's about amplifying their effectiveness by automating the mechanical translation from specification to implementation.

### 2. Growing Complexity

Modern systems integrate dozens of services, frameworks, and dependencies. SDD provides systematic alignment through specification-driven generation.

### 3. Accelerating Change

Requirements change far more rapidly than ever before. Pivoting is no longer exceptional—it's expected. SDD transforms requirement changes from obstacles into normal workflow.

## Streamlining SDD with Commands

The SDD methodology is significantly enhanced through powerful commands that automate the specification → planning → tasking workflow.

### Core Spec Workflow Commands

These commands form the backbone of the Spec-Driven Development workflow:

| Command | Purpose |
|---------|---------|
| `/speckit.specify` | Transform a feature description into a complete, structured specification |
| `/speckit.plan` | Create a comprehensive implementation plan from the specification |
| `/speckit.tasks` | Generate an executable task list from the plan |
| `/speckit.implement` | Execute tasks to build the feature |
| `/speckit.analyze` | Check consistency and completeness of spec artifacts |
| `/speckit.critic` | Perform adversarial risk analysis before implementation |

### Constitution-Powered Commands

These commands work independently of the spec workflow—they only require a constitution:

| Command | Purpose |
|---------|---------|
| `/speckit.pr-review` | Constitution-based code review for any GitHub PR |
| `/speckit.site-audit` | Comprehensive codebase audit against constitution |
| `/speckit.constitution` | Create or update project constitution |

For detailed information on constitution-powered commands, see:

- [Constitution Guide](constitution-guide.md)
- [PR Review Guide](pr-review-usage.md)
- [Site Audit Guide](site-audit-usage.md)
- [Critic Guide](critic-usage.md)

## Example: Building a Chat Feature

Here's how these commands transform the traditional development workflow:

### Traditional Approach (≈12 hours)

```text
1. Write a PRD in a document (2-3 hours)
2. Create design documents (2-3 hours)
3. Set up project structure manually (30 minutes)
4. Write technical specifications (3-4 hours)
5. Create test plans (2 hours)
```

### SDD with Commands Approach (≈15 minutes)

```bash
# Step 1: Create the feature specification (5 minutes)
/speckit.specify Real-time chat system with message history and user presence

# This automatically:
# - Creates branch "003-chat-system"
# - Generates specs/003-chat-system/spec.md
# - Populates it with structured requirements

# Step 2: Generate implementation plan (5 minutes)
/speckit.plan WebSocket for real-time messaging, PostgreSQL for history, Redis for presence

# Step 3: Generate executable tasks (5 minutes)
/speckit.tasks
```

In 15 minutes, you have:

- A complete feature specification with user stories and acceptance criteria
- A detailed implementation plan with technology choices and rationale
- API contracts and data models ready for code generation
- Comprehensive test scenarios for both automated and manual testing
- All documents properly versioned in a feature branch

## Template-Driven Quality

The true power of Spec Kit lies in how templates guide LLM behavior toward higher-quality specifications. The templates act as sophisticated prompts that constrain output in productive ways:

### 1. Preventing Premature Implementation Details

Templates explicitly focus on WHAT users need, not HOW to implement. This separation ensures specifications remain stable even as implementation technologies change.

### 2. Forcing Explicit Uncertainty Markers

Both templates mandate `[NEEDS CLARIFICATION]` markers, preventing the common LLM behavior of making plausible but potentially incorrect assumptions.

### 3. Structured Thinking Through Checklists

Templates include comprehensive checklists that act as "unit tests" for the specification, forcing systematic self-review.

### 4. Constitutional Compliance Through Gates

Implementation plan templates enforce architectural principles through phase gates that must be passed or documented.

### 5. Test-First Thinking

Templates enforce test-first development by requiring test files to be created before source files.

## The Constitutional Foundation

At the heart of SDD lies a constitution—a set of immutable principles that govern how specifications become code. See the [Constitution Guide](constitution-guide.md) for details.

### The Nine Articles of Development

| Article | Principle | Summary |
|---------|-----------|---------|
| I | Library-First | Every feature begins as a standalone library |
| II | CLI Interface | All libraries expose functionality through CLI |
| III | Test-First | No implementation code before tests |
| IV | Documentation | Concurrent documentation with implementation |
| V | Version Control | Semantic versioning and branching |
| VI | Code Quality | Static analysis and linting |
| VII | Simplicity | Maximum 3 projects for initial implementation |
| VIII | Anti-Abstraction | Use frameworks directly, minimal wrapping |
| IX | Integration-First | Prefer real environments over mocks |

### Constitutional Enforcement

The implementation plan template operationalizes these articles through concrete checkpoints:

```markdown
### Phase -1: Pre-Implementation Gates

#### Simplicity Gate (Article VII)

- [ ] Using ≤3 projects?
- [ ] No future-proofing?

#### Anti-Abstraction Gate (Article VIII)

- [ ] Using framework directly?
- [ ] Single model representation?

#### Integration-First Gate (Article IX)

- [ ] Contracts defined?
- [ ] Contract tests written?
```

## Benefits of SDD

### Consistency

- Checklists ensure nothing is forgotten
- Constitutional principles are enforced uniformly

### Quality

- Forced clarification markers highlight uncertainties
- Test-first thinking baked into the process
- Proper abstraction levels maintained

### Velocity

- Specifications stay in sync with code because they generate it
- Change requirements and regenerate plans in minutes, not days
- Pivots become systematic regenerations rather than manual rewrites

### Traceability

- Every technical choice links back to specific requirements
- Living documentation that evolves with the code

## The Transformation

This isn't about replacing developers or automating creativity. It's about:

- **Amplifying human capability** by automating mechanical translation
- **Creating tight feedback loops** where specifications, research, and code evolve together
- **Maintaining alignment** between intent and implementation through executable specifications

Software development needs better tools for maintaining alignment between intent and implementation. SDD provides the methodology for achieving this alignment through executable specifications that generate code rather than merely guiding it.

## Getting Started

1. **Install Spec Kit**: Follow the [Installation Guide](installation.md)
2. **Create Your Constitution**: See the [Constitution Guide](constitution-guide.md)
3. **Try the Quick Start**: Follow the [Quick Start Guide](quickstart.md)

## Additional Resources

- [Quick Start Guide](quickstart.md)
- [Constitution Guide](constitution-guide.md)
- [PR Review Guide](pr-review-usage.md)
- [Site Audit Guide](site-audit-usage.md)
- [Critic Guide](critic-usage.md)

---

> Part of the Spec Kit - Spec-Driven Development Toolkit
