# Why I Forked GitHub Spec Kit

*Building on the shoulders of giants to unlock the full potential of project constitutions.*

---

## The Starting Point: A Brilliant Foundation

GitHub's [Spec Kit](https://github.com/github/spec-kit) introduced something genuinely innovative—**Spec-Driven Development (SDD)**. The methodology flips traditional software development on its head: instead of treating specifications as disposable scaffolding, SDD makes them the executable source of truth that drives implementation.

The original toolkit includes a powerful concept: the **project constitution**. This document captures your team's governing principles, development guidelines, and quality standards. The AI agent then references this constitution during specification, planning, and implementation phases.

I was immediately drawn to this approach. The constitution concept resonated with how I think about sustainable software development—principles-first, then implementation.

But as I used Spec Kit, I kept asking: *"What else could we do with a well-crafted constitution?"*

---

## The Gap I Saw

The original Spec Kit uses the constitution primarily during the **spec workflow**:

1. **`/speckit.specify`** → Define requirements
2. **`/speckit.plan`** → Create implementation plan
3. **`/speckit.tasks`** → Break down into actionable tasks
4. **`/speckit.implement`** → Execute the plan

This is excellent for greenfield development. But I saw three opportunities:

### 1. Constitutions Should Govern More Than Just New Features

If you invest time writing a thoughtful constitution, why should it only apply during feature development? Every pull request, every code review, every codebase audit should leverage those principles.

### 2. Brownfield Projects Need a Path to SDD

Most teams aren't starting fresh. They have existing codebases with implicit patterns, undocumented conventions, and years of accumulated decisions. How do you retrofit a constitution onto an existing project?

### 3. Risk Analysis Before Implementation

The original workflow focuses on *what to build* and *how to build it*. I wanted a step that asks *what could go wrong*—an adversarial pre-mortem before writing a single line of code.

---

## What Spec Kit Spark Adds

I created **Spec Kit Spark** as a community extension that keeps the original SDD workflow intact while adding four constitution-powered capabilities:

### `/speckit.pr-review` — Constitution-Based Pull Request Reviews

**The problem:** Traditional PR reviews depend on individual reviewer knowledge. Different reviewers catch different issues based on their experience and focus.

**The solution:** Use the constitution as an objective standard. Every PR gets evaluated against the same principles.

**Key design decisions:**
- Works for **any PR in any branch**—not limited to feature branches
- Only requires a constitution—no spec, plan, or tasks needed
- Saves review history to `/specs/pr-review/pr-{number}.md`
- Tracks commit SHAs so you can re-review after changes

This means constitution-powered reviews work for:
- Hotfixes to main
- Documentation updates to develop
- Any contribution, regardless of whether it followed the SDD workflow

### `/speckit.site-audit` — Codebase-Wide Compliance Auditing

**The problem:** Constitution principles mean nothing if they're not enforced consistently across the entire codebase.

**The solution:** A comprehensive audit command that evaluates your entire codebase against constitution principles.

**What it checks:**
- Constitution compliance (principle-by-principle)
- Security vulnerabilities and patterns
- Dependency health (outdated, unused, vulnerable packages)
- Code quality metrics (complexity, duplication)
- Unused code detection

**Key design decisions:**
- Supports scoped audits (`--scope=constitution`, `--scope=packages`, etc.)
- Produces trend-trackable reports in `/docs/copilot/audit/`
- Compares against previous audits to show improvement or regression

### `/speckit.critic` — Adversarial Risk Analysis

**The problem:** Plans and task lists can look perfect on paper but fail spectacularly in production. Teams with limited experience in a new tech stack often miss edge cases.

**The solution:** A skeptical reviewer that identifies showstoppers *before* implementation begins.

**How it differs from `/speckit.analyze`:**
- `/speckit.analyze` = Consistency checking (are artifacts aligned?)
- `/speckit.critic` = Adversarial analysis (what will fail in production?)

**Severity levels:**
- **SHOWSTOPPER** — Will cause production outage, data loss, or security breach
- **CRITICAL** — Major user-facing issues or costly rework
- **HIGH** — Technical debt or operational burden
- **MEDIUM** — Development slowdown or minor issues

**Key design decisions:**
- Constitution violations are automatically SHOWSTOPPER severity
- Provides a clear Go/No-Go recommendation
- Runs after `/speckit.tasks` but before `/speckit.implement`

### `/speckit.discover-constitution` — Brownfield Constitution Discovery

**The problem:** Existing codebases have implicit patterns and conventions baked into the code. Teams adopting SDD need a way to extract these patterns into a constitution.

**The solution:** Analyze the codebase, discover patterns, and guide teams through interactive questions to formalize a constitution.

**How it works:**
1. Scans for patterns (testing frameworks, security practices, architecture conventions)
2. Reports high-confidence patterns (>80% consistent) vs. inconsistent areas
3. Asks 8-10 targeted questions to validate findings
4. Generates a draft constitution at `/memory/constitution-draft.md`

**Key design decisions:**
- Discovery-first: analyze code before asking questions
- Draft output: produces a starting point for team review, not a final document
- Respects existing work: treats discovered patterns as valuable

---

## Additional Improvements

Beyond the four major features, Spec Kit Spark includes:

### PowerShell Parity

Every bash script has a corresponding PowerShell script. Windows developers get first-class support.

| Script | Purpose |
|--------|---------|
| `site-audit.ps1` | Codebase auditing |
| `get-pr-context.ps1` | PR data extraction via GitHub CLI |
| `create-github-release.ps1` | Release management |
| `generate-release-notes.ps1` | Automated changelog generation |

### Repository Health Analysis

Integrated Git Spark reports provide insights into:
- Contributor activity and bus factor
- File hotspots (high churn, many authors)
- Governance scores (commit message quality, traceability)
- Risk analysis based on code churn patterns

### Enhanced Documentation

- Constitutional governance guide with examples
- PR review usage documentation
- Site audit usage guide
- Critic command documentation
- Local development instructions

---

## The Philosophy: Continuous Constitution Value

The core philosophy of Spec Kit Spark is simple:

> **A project constitution should provide value continuously, not just during feature development.**

If you write a constitution that says "All public APIs must have input validation," that principle should:
- Guide new feature development (original Spec Kit)
- Catch violations in pull requests (`/speckit.pr-review`)
- Identify existing violations in the codebase (`/speckit.site-audit`)
- Flag missing validation as a risk before implementation (`/speckit.critic`)

This creates a **closed loop** where constitution principles are enforced at every stage of the development lifecycle.

---

## Attribution and Relationship to Original

Full credit goes to the GitHub team—particularly [Den Delimarsky](https://github.com/localden) and [John Lam](https://github.com/jflam)—for creating the Spec-Driven Development methodology and the original Spec Kit toolkit.

**Spec Kit Spark is an extension, not a replacement.** The original SDD workflow remains unchanged. All additions are additive and maintain backward compatibility.

If you're looking for the official, GitHub-maintained version, visit [github.com/github/spec-kit](https://github.com/github/spec-kit).

Spec Kit Spark is part of the [WebSpark](https://github.com/MarkHazleton?tab=repositories&q=webspark) demonstration suite—a collection of projects exploring modern development practices.

---

## Try It Yourself

Install Spec Kit Spark:

```bash
uv tool install specify-cli --from git+https://github.com/MarkHazleton/spec-kit.git
```

Initialize in your existing project (brownfield):

```bash
cd /path/to/your-project
specify init --here --ai copilot

# Discover patterns and draft a constitution
# (use /speckit.discover-constitution in your AI agent)
```

Or start fresh (greenfield):

```bash
specify init my-project --ai claude
```

Then try the constitution-powered commands:
- `/speckit.discover-constitution` — Draft a constitution from existing code
- `/speckit.pr-review #123` — Review a PR against your constitution
- `/speckit.site-audit` — Audit your entire codebase
- `/speckit.critic` — Identify risks before implementation

---

## Summary

| Why I Forked | What I Added |
|--------------|--------------|
| Constitutions should govern more than specs | `/speckit.pr-review` for any PR |
| Existing codebases need a path to SDD | `/speckit.discover-constitution` for brownfield |
| Risk analysis should happen before coding | `/speckit.critic` for pre-mortems |
| Codebase-wide compliance matters | `/speckit.site-audit` for auditing |
| Windows developers deserve parity | PowerShell scripts for all operations |

The goal is simple: **maximize the return on investment for crafting a thoughtful project constitution**.

---

*— Mark Hazleton*

*Part of the [WebSpark](https://github.com/MarkHazleton?tab=repositories&q=webspark) demonstration suite*
