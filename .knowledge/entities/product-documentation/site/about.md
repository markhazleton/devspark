# About DevSpark

## Current Release

[![Current Release](https://img.shields.io/github/v/release/markhazleton/devspark?label=current%20release)](https://github.com/markhazleton/devspark/releases/latest)

**Current version:** [v4.2.0](https://github.com/markhazleton/devspark/releases/tag/v4.2.0)

DevSpark is a structured development process for AI coding assistants. It
provides 30 stock command prompts plus helper templates and scripts that give
any AI agent a repeatable current-truth workflow.

## What It Is

- **Not a program.** Not a subscription. Just markdown files you copy into your project.
- **Agent-agnostic.** Works with Claude Code, GitHub Copilot, Cursor, Gemini CLI, and 18+ AI agents.
- **Current-truth powered.** Projects keep durable code, `.knowledge`, and governance aligned while release moves completed planning scaffolding under human-only `.archive/YYYY-MM-DD/<topic>/` folders.
- **Multi-app ready.** Optionally manage multiple applications in a monorepo with per-app governance, profiles, and scoped commands.

## Core Idea

Most AI coding assistants are powerful but unstructured. You get great code generation, but without a consistent process, quality varies and context gets lost between sessions.

DevSpark solves this by giving your AI agent a workflow:

1. **Specify** what you want to build (requirements and user stories)
2. **Plan** how to build it (technical design)
3. **Break it down** into tasks
4. **Implement** with constitution-based guardrails
5. **Review** against your project's own principles
6. **Release** with proper documentation

## Design Principles

### Markdown-First

Everything is a markdown file. No proprietary formats, no databases, no lock-in.
Temporary specs and plans live only while work is in flight. Durable current
truth lives in code, `.knowledge`, and governance documents.

### Three-Tier Prompt Resolution

Commands resolve through a priority chain:

1. **Personal overrides** — `.knowledge/overrides/{git-user}/commands/` — your individual tweaks
2. **Team customizations** — `.knowledge/overrides/commands/` — shared by the team
3. **Stock defaults** — `.devspark/defaults/commands/` — the out-of-box prompts

This means teams share a common workflow while individuals can customize any command without affecting others.

### Clean Separation

DevSpark keeps its framework files (`.devspark/`) separate from repository
guides (`.knowledge/`), current truth (`.knowledge/`), and ephemeral work
packages (`.devspark.work/`).

## Who It's For

- **Solo developers** who want a repeatable process when working with AI assistants
- **Teams** that need consistent AI-assisted workflows across different agents and editors
- **Projects of any size** — one-off fix, quick spec, and full spec routes keep the process right-sized
- **Monorepo teams** — optional multi-app support provides per-application governance, profiles, and scoped commands without requiring any changes to single-app repositories

## Origin

DevSpark is an independent project maintained by [Mark Hazleton](https://github.com/markhazleton) and the open-source community. It provides a structured development process for AI coding assistants, covering the full development lifecycle from requirements through release.

## Links

- [GitHub Repository](https://github.com/MarkHazleton/devspark)
- [DevSpark Philosophy](philosophy.md)
- [Implementation Lifecycle Guide](implementation-lifecycle.md)
- [Installation Guide](installation.md)
- [Quick Start Guide](quickstart.md)
- [Contributing](https://github.com/MarkHazleton/devspark/blob/main/CONTRIBUTING.md)
