# Frequently Asked Questions

Welcome! If you're an experienced developer stepping into the world of AI-assisted, spec-driven development for the first time, you're in the right place. This FAQ covers the questions we hear most often — no jargon overload, just straight answers.

---

## Getting Started

### What exactly is DevSpark?

DevSpark is a set of markdown files — prompt templates and helper scripts — that give your AI coding assistant a repeatable, structured workflow. Think of it as a process framework: it tells your AI agent *how* to help you go from requirements to shipped code, step by step.

It is **not** a program you run, a SaaS subscription, or a VS Code extension. It's just files you drop into your repo.

### What is "spec-driven development" and why should I care?

Spec-driven development (SDD) means you write a short specification (the *what* and *why*) before jumping to code. Your AI assistant then uses that spec to generate a plan, break it into tasks, and implement — all traceable back to the original requirements.

**Why it matters:** Without a spec, AI assistants produce code that *works* but may not do what you actually need. A spec keeps the AI focused, reduces rework, and gives you something concrete to review before a single line of code is written.

### I've been writing software for 20 years without specs for every feature. Isn't this overkill?

Fair concern. DevSpark is designed with **right-sized workflows**:

| Task Size | Recommended Workflow | Overhead |
|-----------|---------------------|----------|
| Typo / one-liner | Just fix it — no process needed | None |
| Bug fix or small change | `/devspark.quickfix` — lightweight, minimal ceremony | ~2 minutes |
| New feature, multi-file | Full planning workflow (`requirements → plan → tasks → implement`) | ~10-15 minutes |
| Architectural change | Full spec + `/devspark.critic` for risk analysis | ~20 minutes |

You wouldn't write a design doc for a CSS tweak, and DevSpark doesn't ask you to. Use the quickfix path for small stuff and the full workflow when the scope justifies it.

### Do I need to learn a new programming language or tool?

No. DevSpark is pure markdown. If you can read a `.md` file, you can use DevSpark. The AI agent does the heavy lifting — you provide the intent and review the output.

---

## AI-Assisted Coding

### I've never used an AI coding assistant before. Where do I start?

1. **Pick an agent.** DevSpark works with 17+ AI agents — GitHub Copilot, Claude Code, Cursor, Gemini CLI, and many others. Start with whatever your editor already supports.
2. **Bootstrap DevSpark with the remote quickstart prompt** (see the [Quick Start Guide](quickstart.md)).
3. **Follow the [Implementation Lifecycle Guide](implementation-lifecycle.md)** — it walks through installation, feature delivery, and updates.

You don't need to be an AI expert. The slash commands (`/devspark.specify`, `/devspark.plan`, etc.) guide you through each step.

### Will the AI write all my code for me?

It can, but that's not the goal. Think of the AI as a very fast junior developer: it produces code quickly, but it needs direction, review, and guardrails. DevSpark provides those guardrails through the **constitution** and **spec workflow**.

You stay in the driver's seat. You write the spec, review the plan, approve the tasks, and review the implementation. The AI accelerates the typing — you keep the thinking.

### How do I know the AI-generated code is any good?

Three mechanisms work together:

1. **The Constitution** — Your project's rules (coding standards, security requirements, test coverage targets) are defined once and enforced by every DevSpark command. The AI checks its own work against your standards.
2. **PR Review** — `/devspark.pr-review` performs a constitution-based code review, catching violations before merge.
3. **Site Audit** — `/devspark.site-audit` does a full-codebase scan against your constitution, surfacing technical debt and standards drift.

None of these replace your own code review. They augment it.

### What if the AI makes a mistake or hallucinates something?

It will. AI assistants sometimes generate incorrect code, invent APIs that don't exist, or misunderstand requirements. This is normal and expected.

DevSpark mitigates this through structure:

- **Specs** catch misunderstandings before coding starts (cheaper to fix a sentence than a module).
- **The constitution** defines hard requirements the AI must follow.
- **The critic command** (`/devspark.critic`) performs adversarial risk analysis on plans before implementation.
- **You review everything.** DevSpark never auto-commits or auto-deploys.

Treat AI output the way you'd treat a pull request from any team member — review it, test it, then merge it.

---

## The Constitution

### What is a "constitution" in this context?

It's a markdown file (`.documentation/memory/constitution.md`) that defines your project's non-negotiable principles: coding standards, security requirements, testing expectations, architecture decisions, and any other rules your codebase should follow.

Every DevSpark command reads the constitution and uses it as the benchmark for quality. When the AI reviews a PR, it checks against the constitution. When it generates code, it follows the constitution. When it audits your codebase, it reports violations against the constitution.

### I already have coding standards in a wiki somewhere. Do I need a constitution too?

The constitution *is* your coding standards — just in a format your AI assistant can actually use. A wiki page that humans read is great for humans. A constitution that lives in your repo is great for both humans *and* AI agents.

If you have existing standards, use `/devspark.discover-constitution` to analyze your codebase and generate a constitution draft. Then refine it with the principles you already have documented elsewhere.

### Can the constitution change over time?

Absolutely. Codebases evolve, and the constitution should evolve with them. Use `/devspark.evolve-constitution` to propose amendments based on findings from PR reviews and audits. It follows a structured amendment process — no drive-by edits to your project's foundational rules.

### What goes in the constitution? Can you give me an example?

A good constitution typically covers:

- **Architecture**: "This is a monorepo / microservices / modular monolith"
- **Code quality**: "All public functions MUST have typed parameters"
- **Testing**: "Unit test coverage MUST exceed 80%"
- **Security**: "No hardcoded secrets. All SQL queries MUST be parameterized"
- **Dependencies**: "New dependencies MUST be approved in a PR review"
- **Documentation**: "All API endpoints MUST have OpenAPI documentation"

The [Constitution Guide](constitution-guide.md) has detailed examples and best practices.

---

## Workflow & Commands

### What are these slash commands? Where do I type them?

Slash commands like `/devspark.specify` are typed into your AI agent's chat interface — the same place you'd normally talk to your AI assistant. They're not terminal commands.

When you type `/devspark.specify Build a photo album organizer`, your AI agent reads the DevSpark prompt template for the `specify` command and uses it to guide the conversation.

### Do I have to use all 24 commands?

No. Most projects use a small subset regularly. The 3 multi-app commands are only needed for monorepos with multiple applications.

**Everyday commands:**

- `/devspark.quickfix` — Small bug fixes and changes
- `/devspark.specify` → `/devspark.plan` → `/devspark.tasks` → `/devspark.implement` — Feature development
- `/devspark.pr-review` — Code review

**Occasional commands:**

- `/devspark.constitution` — Initial setup and periodic updates
- `/devspark.site-audit` — Periodic codebase health checks
- `/devspark.release` — Release documentation

**Specialized commands:**

- `/devspark.critic` — Risk analysis for complex changes
- `/devspark.harvest` — Knowledge extraction and cleanup
- `/devspark.evolve-constitution` — Constitution amendments

Start with `quickfix` and the basic spec workflow. Add others as your comfort grows.

### What's the difference between `/devspark.quickfix` and the full spec workflow?

**Quickfix** is for small, well-understood changes: "Fix the null reference in `UserService.GetById()`" or "Add a loading spinner to the dashboard page." It skips the full specification and planning steps because the scope is obvious.

**Full spec workflow** is for larger work where the scope, design, or impact isn't immediately clear: "Add multi-tenant support" or "Replace the auth system with OAuth2." The extra upfront thinking pays off by preventing expensive rework mid-implementation.

Rule of thumb: if you can describe the change in one sentence and it touches fewer than 3 files, use quickfix. Otherwise, use the full workflow.

### Can I customize the commands for my team?

Yes. DevSpark uses a three-tier resolution system:

1. **Personal overrides** — `.documentation/{git-user}/commands/` — your individual customizations
2. **Team customizations** — `.documentation/commands/` — shared by the whole team
3. **Stock defaults** — `.devspark/defaults/commands/` — the built-in prompts

Use `/devspark.personalize` to create your own overrides. They're committed to git, so they follow you across machines. Delete the override file to revert to the team or default version.

---

## Agent Compatibility

### Which AI coding assistants does DevSpark work with?

DevSpark is agent-agnostic and works with 17+ AI assistants, including:

- **GitHub Copilot** (VS Code, JetBrains, Neovim)
- **Claude Code** (terminal-based)
- **Cursor** (VS Code fork)
- **Gemini CLI**
- **Windsurf (Codeium)**
- **Amazon Q Developer**
- **Aider**
- And many more — see the [Quick Start Guide](quickstart.md) for the full list

### Can I use multiple AI agents on the same project?

Yes, and this is a key design goal. DevSpark's canonical prompts live in `.documentation/commands/` — a single source of truth. Each agent gets thin adapter files (shims) that point back to the canonical prompts.

This means one team member can use Copilot while another uses Claude Code, and both follow the same spec-driven process with the same standards.

### I'm already using GitHub Copilot for code completion. How is this different?

Copilot's inline code completion (the gray ghost text) is great for line-by-line suggestions. DevSpark works at a higher level — it structures your *workflow*, not just your code completions.

Think of it this way:

- **Copilot completions** = autocomplete on steroids (tactical)
- **DevSpark + Copilot Chat** = a structured development process with AI assistance (strategic)

They complement each other. You use DevSpark commands in Copilot Chat to plan and manage work, while Copilot completions help you type faster in the editor.

---

## Project Setup

### How do I add DevSpark to an existing project?

Open your AI agent in the existing project and run the matching remote quickstart prompt from the [Quick Start Guide](quickstart.md).

If you prefer the advanced CLI path instead, navigate to your project directory and run:

```bash
cd /path/to/your-project
uvx --from git+https://github.com/MarkHazleton/devspark.git devspark init --here
```

Then use `/devspark.discover-constitution` in your AI chat to generate a constitution based on your existing code patterns. This is the **brownfield** path — it respects what's already there instead of imposing new patterns blindly.

### What files does DevSpark add to my repo?

DevSpark creates two directories:

- **`.devspark/`** — Framework files (prompt defaults, scripts). Think of this as the "engine."
- **`.documentation/`** — Your project artifacts (specs, plans, constitution, decisions). Think of this as "your stuff."

The separation is intentional: you can uninstall DevSpark (delete `.devspark/`) without losing any of your specifications, constitutions, or architectural decisions.

### Will DevSpark conflict with my existing tooling?

No. DevSpark doesn't modify your build system, CI/CD pipeline, linter config, or any existing project files. It only adds its own directories (`.devspark/` and `.documentation/`) and optionally a few agent config files (like `.github/copilot-instructions.md`).

### Can I use DevSpark with any programming language?

Yes. DevSpark is language-agnostic. The specifications, plans, and constitutions are all markdown. The AI agent handles the language-specific implementation. Whether your project is Python, C#, TypeScript, Rust, Go, Java, or anything else makes no difference to the process.

---

## Common Concerns

### Isn't this just over-engineered documentation?

We understand the skepticism. Here's the key difference: traditional documentation describes what *was* built (and often drifts out of date). DevSpark specs describe what *will* be built and are consumed by your AI agent in real-time during implementation.

The specs are working documents that drive code generation, not shelf-ware that nobody reads after sprint planning.

### Does this slow me down?

For trivial changes, it would — which is why `/devspark.quickfix` exists for those cases.

For non-trivial work, the upfront investment in defining requirements and planning typically *saves* time by reducing:

- Rework from misunderstood requirements
- AI hallucinations from vague prompts
- Inconsistent code quality across features
- "What was the decision and why?" conversations months later

Most teams report that the time spent on requirements definition is recovered several times over during implementation and review.

### What if I'm a solo developer? Is this overkill for one person?

Solo developers are actually the primary audience. When you're working alone with an AI assistant, there's no team to catch misunderstandings or review your approach. The spec workflow serves as your thinking process, forcing you to clarify requirements before throwing them at the AI.

The constitution is especially valuable for solo developers — it's your "future self" documentation. When you come back to a project after six months, the constitution tells you exactly what standards you set and why.

### How is this different from just writing good prompts?

Good prompts help for individual tasks. DevSpark provides a *system*:

- **Continuity** — Specs and plans persist across chat sessions. Your AI doesn't forget what you discussed yesterday.
- **Consistency** — The constitution ensures the same standards apply whether you're implementing feature A or fixing bug B.
- **Traceability** — You can trace any piece of code back through tasks → plan → spec → requirements.
- **Evolution** — The harvest and release commands keep your documentation current as the codebase changes.

A good prompt gets you good code. A good process gets you a good codebase.

### Is my code or data sent anywhere?

DevSpark itself sends nothing anywhere. It's just markdown files in your repo. However, when you use an AI coding assistant (Copilot, Claude, etc.), your code and prompts are processed by that AI provider according to their terms of service and privacy policy.

DevSpark doesn't add any additional data transmission, telemetry, or phone-home behavior. It's entirely local to your repository.

---

## Troubleshooting

### The slash commands aren't working in my editor

Make sure you've completed the setup for your specific AI agent. Each agent has a slightly different configuration:

- **GitHub Copilot**: Needs `.github/copilot-instructions.md` and prompt files in `.github/copilot/`
- **Claude Code**: Needs `CLAUDE.md` at the repo root
- **Cursor**: Needs `.cursor/rules/` directory with rule files

Re-run the agent-specific remote quickstart prompt from the [Quick Start Guide](quickstart.md) to refresh the expected DevSpark files for your editor. Use `devspark init --ai ...` only if you intentionally want the advanced CLI path.

### I ran the advanced CLI setup but nothing seems different

After CLI initialization, the DevSpark files are in your repo but your AI agent may not be aware of them yet. Try:

1. Restart your editor or reload the window
2. Open a new AI chat session
3. Type a DevSpark command like `/devspark.constitution` in the chat

If your agent doesn't recognize the command, check that the agent-specific shim files were created (see the quickstart guide for your agent).

### The AI isn't following my constitution

A few things to check:

- **Is the constitution file present?** Check `.documentation/memory/constitution.md` exists and isn't empty.
- **Is it too vague?** Principles like "write good code" aren't actionable. Use specific, testable requirements: "All public API endpoints MUST return proper HTTP status codes."
- **Is the AI context window full?** Very large codebases can push the constitution out of the AI's context. Try working in smaller scopes or referencing specific constitution sections.

### How do I upgrade DevSpark without losing my work?

For normal use, run the remote upgrade prompt in your AI chat:

```text
Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/templates/commands/upgrade.md
```

If you explicitly use the advanced CLI workflow, run:

```bash
devspark upgrade
```

This updates the framework files in `.devspark/` while preserving your artifacts in `.documentation/`. Your constitution, specs, plans, and decisions are untouched.

> [!TIP]
> **Important:** After upgrading, verify your constitution file wasn't overwritten. If it was, restore from the `.bak` backup that the upgrade process creates. See the [Upgrade Guide](upgrade.md) for details.

---

## Multi-App Monorepo Support

### What is multi-app support?

Multi-app support lets DevSpark manage repositories containing multiple applications — for example, a monorepo with a .NET API, a React frontend, and a Python data pipeline. Each application can have its own constitution, governance rules, and code review scope while sharing a common repository.

### Do I need multi-app support?

**Most projects do not.** If your repository contains a single application, or a monorepo where all applications share the same conventions, standard DevSpark is all you need. Multi-app is entirely optional and changes nothing for single-app repositories.

Consider multi-app when:

- Your monorepo has applications with **different tech stacks** (e.g., .NET API + React UI)
- Different applications need **different governance rules** (e.g., PCI-compliant service vs. internal tooling)
- You want **per-app constitutions** that extend the repo-wide constitution with app-specific rules
- You need **scoped code reviews** that understand which applications a PR affects

### How do I enable multi-app support?

1. Run `/devspark.add-application` in your AI agent chat — it creates a registry at `.documentation/devspark.json` and scaffolds the app's documentation directory
2. Repeat for each application in your repository
3. Use `--app <id>` with any DevSpark command to scope it to a specific application

### Can I add multi-app support to an existing DevSpark project?

Yes. Multi-app is additive — it builds on top of your existing DevSpark setup without requiring any migration or restructuring. Your existing constitution, specs, and decisions remain untouched.

### What are profiles?

Profiles are reusable rule bundles that applications can inherit. For example, you might define an `api-profile` with API-specific governance rules and a `web-profile` for frontend conventions. Applications declare which profiles they use, and DevSpark composes the rules automatically.

### Does multi-app change how single-app repositories work?

**No.** This is a non-negotiable design principle. Single-app repositories continue to work exactly as before with zero changes required. Multi-app functionality only activates when a registry file exists at `.documentation/devspark.json`.

---

## Still Have Questions?

- Browse the [Getting Started](quickstart.md) guide for a hands-on walkthrough
- Read the [Constitution Guide](constitution-guide.md) to understand the governance model
- Check the [About page](about.md) for the project's design philosophy
- Visit the [GitHub repository](https://github.com/MarkHazleton/devspark) to open an issue or start a discussion
