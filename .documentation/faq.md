# Frequently Asked Questions

## Getting Started

### What exactly is DevSpark?

A set of markdown files -- prompt templates and helper scripts -- that give your AI coding assistant a repeatable workflow. It is not a program, a SaaS subscription, or an extension. Just files you drop into your repo.

### What is "spec-driven development"?

You write a short specification (the *what* and *why*) before jumping to code. Your AI assistant uses that spec to generate a plan, break it into tasks, and implement -- all traceable back to the original requirements.

### Isn't this overkill for small changes?

DevSpark has right-sized workflows:

| Task Size | Workflow | Overhead |
|-----------|---------|----------|
| Typo / one-liner | Just fix it | None |
| Bug fix or small change | `/devspark.quickfix` | ~2 minutes |
| New feature, multi-file | Full spec workflow | ~10-15 minutes |
| Architectural change | Full spec + `/devspark.critic` | ~20 minutes |

`/devspark.specify` is the default intake command. It will recommend the lighter or heavier path before creating artifacts.

### Do I need to learn a new tool?

No. DevSpark is pure markdown. The AI agent does the heavy lifting.

---

## AI-Assisted Coding

### Where do I start with AI coding assistants?

1. Pick an agent (GitHub Copilot, Claude Code, Cursor, Gemini CLI, or any of 17+ supported agents).
2. Bootstrap DevSpark with the [Quick Start Guide](quickstart.md).
3. Follow the [Implementation Lifecycle](implementation-lifecycle.md).

### How do I know the AI-generated code is any good?

Three mechanisms: the **constitution** (your project's rules, enforced by every command), **PR review** (`/devspark.pr-review` checks code against the constitution), and **site audit** (`/devspark.site-audit` scans the full codebase). None replace your own review -- they augment it.

### What if the AI makes a mistake?

It will. Specs catch misunderstandings before coding starts. The constitution defines hard requirements. The critic command (`/devspark.critic`) performs adversarial risk analysis. You review everything -- DevSpark never auto-commits or auto-deploys.

---

## The Constitution

### What is a "constitution"?

A markdown file (`.documentation/memory/constitution.md`) that defines your project's non-negotiable principles: coding standards, security requirements, testing expectations. Every DevSpark command reads and enforces it.

### I already have coding standards in a wiki. Do I need this too?

The constitution *is* your coding standards in a format your AI assistant can use. If you have existing standards, use `/devspark.discover-constitution` to generate a draft from your codebase.

### Can the constitution change over time?

Yes. Use `/devspark.evolve-constitution` to propose amendments based on PR review findings. See the [Constitution Guide](constitution-guide.md) for details.

### What goes in the constitution?

Architecture, code quality, testing, security, dependencies, and documentation rules. Example:

- "All public functions MUST have typed parameters"
- "Unit test coverage MUST exceed 80%"
- "No hardcoded secrets. All SQL queries MUST be parameterized"

See the [Constitution Guide](constitution-guide.md) for full examples.

---

## Workflow and Commands

### Where do I type slash commands?

In your AI agent's chat interface -- the same place you normally talk to your assistant. They are not terminal commands.

### Do I have to use all 27 commands?

No. Most projects use a small subset of the 27 stock commands:

**Everyday:** `/devspark.quickfix`, `/devspark.specify` -> `/devspark.plan` -> `/devspark.tasks` -> `/devspark.implement`, `/devspark.pr-review`

**Occasional:** `/devspark.constitution`, `/devspark.site-audit`, `/devspark.release`

**Specialized:** `/devspark.critic`, `/devspark.harvest`, `/devspark.evolve-constitution`

### What is the spec status lifecycle?

Every spec has a `**Status**:` field that transitions through three states:

| Status | Set by | Meaning |
|--------|--------|---------|
| **Draft** | `/devspark.specify` | Spec created, not yet implementing |
| **In Progress** | `/devspark.implement` (start) | Implementation underway |
| **Complete** | `/devspark.implement` (all tasks done) | Ready for PR review and merge |

PR review blocks approval unless the spec is `Complete` with all tasks checked off. Site audit flags incomplete specs on main as critical anti-patterns.

### What's the difference between quickfix and the full workflow?

**Quickfix** is for small, well-understood changes (one sentence, fewer than 3 files). **Full spec workflow** is for larger work where scope or design isn't immediately clear.

A middle path also exists: `quick-spec`. That route keeps intent, scope, constraints, and an action plan without the full specification overhead.

### Can I customize commands for my team?

Yes. DevSpark uses three-tier resolution:

1. **Personal** -- `.documentation/{git-user}/commands/`
2. **Team** -- `.documentation/commands/`
3. **Stock** -- `.devspark/defaults/commands/`

Use `/devspark.personalize` to create personal overrides.

---

## Agent Compatibility

### Which AI assistants work with DevSpark?

17+ agents including GitHub Copilot, Claude Code, Cursor, Gemini CLI, Windsurf, Amazon Q Developer, and more. See the [Quick Start Guide](quickstart.md) for the full list.

### Can I use multiple agents on the same project?

Yes. Stock prompts live in `.devspark/defaults/commands/`, repo overrides live in `.documentation/commands/`, and each agent gets thin shims that resolve personal, team, then stock prompts.

---

## Project Setup

### How do I add DevSpark to an existing project?

Run the matching quickstart prompt from the [Quick Start Guide](quickstart.md). Then use `/devspark.discover-constitution` to generate a constitution from your existing code patterns.

### What files does DevSpark add?

- **`.devspark/`** -- Framework files (prompt defaults, scripts). The "engine."
- **`.documentation/`** -- Your project artifacts (specs, plans, constitution). "Your stuff."
- **Agent shims** -- Platform-specific command files such as `.claude/commands/` or `.github/agents/`

Uninstall removes `.devspark/` without touching your work.

### Will DevSpark conflict with my existing tooling?

No. It only adds `.devspark/`, `.documentation/`, and optionally a few agent config files. It doesn't modify your build system, CI/CD, or linter config.

### Can I use DevSpark with any programming language?

Yes. Specs and constitutions are markdown. The AI agent handles language-specific implementation.

### Is my code sent anywhere?

DevSpark itself sends nothing anywhere. When you use an AI assistant, your code is processed by that AI provider per their terms. DevSpark adds no telemetry or data transmission.

---

## Multi-App Monorepo Support

### Do I need multi-app support?

**Most projects do not.** Consider it only when your monorepo has applications with different tech stacks, different governance rules, or needs per-app constitutions.

### How do I enable it?

1. Run `/devspark.add-application` for each application.
2. Use `--app <id>` with any command to scope it.
3. Run `/devspark.validate-registry` to verify consistency.

Multi-app is additive -- it doesn't change existing single-app behavior. See the [Monorepo Guide](monorepo-guide.md).

---

## Troubleshooting

For upgrade-specific issues, see the [Upgrade Guide](upgrade.md#troubleshooting).

### Slash commands aren't working

1. Restart your IDE/editor completely (not just reload window).
2. Verify agent files exist (e.g., `ls .claude/commands/` or `ls .github/prompts/`).
3. Re-run the quickstart prompt from the [Quick Start Guide](quickstart.md) to refresh files.

### The AI isn't following my constitution

- Verify `.documentation/memory/constitution.md` exists and isn't empty.
- Make principles specific and testable: "All public API endpoints MUST return proper HTTP status codes" not "write good code."
- For large codebases, try working in smaller scopes.

---

## Still Have Questions?

- [Quick Start Guide](quickstart.md) -- hands-on walkthrough
- [Constitution Guide](constitution-guide.md) -- governance model
- [About](about.md) -- design philosophy
- [GitHub Issues](https://github.com/MarkHazleton/devspark/issues) -- report bugs or request features
