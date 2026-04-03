# About DevSpark

DevSpark is a structured development process for AI coding assistants. It provides 21 prompt templates and helper scripts that give any AI agent a repeatable workflow — from requirements through release.

## What It Is

- **Not a program.** Not a subscription. Just markdown files you copy into your project.
- **Agent-agnostic.** Works with Claude Code, GitHub Copilot, Cursor, Gemini CLI, and 13+ other AI agents.
- **Constitution-powered.** Every project defines its principles once; all commands enforce them automatically.

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

Everything is a markdown file. No proprietary formats, no databases, no lock-in. Your specs, plans, and constitutions are plain text that lives in your repository alongside your code.

### Three-Tier Prompt Resolution

Commands resolve through a priority chain:

1. **Personal overrides** — `.documentation/{git-user}/commands/` — your individual tweaks
2. **Team customizations** — `.documentation/commands/` — shared by the team
3. **Stock defaults** — `.devspark/defaults/commands/` — the out-of-box prompts

This means teams share a common workflow while individuals can customize any command without affecting others.

### Clean Separation

DevSpark keeps its framework files (`.devspark/`) completely separate from your project artifacts (`.documentation/`). Uninstall removes DevSpark without touching your specs, constitutions, or decisions.

## Who It's For

- **Solo developers** who want a repeatable process when working with AI assistants
- **Teams** that need consistent AI-assisted workflows across different agents and editors
- **Projects of any size** — the quickfix workflow handles small tasks; the full spec workflow handles major features

## Origin

DevSpark is an independent project maintained by [Mark Hazleton](https://github.com/markhazleton) and the open-source community. It provides a structured development process for AI coding assistants, covering the full development lifecycle from requirements through release.

## Links

- [GitHub Repository](https://github.com/MarkHazleton/devspark)
- [Installation Guide](installation.md)
- [Quick Start Guide](quickstart.md)
- [Contributing](https://github.com/MarkHazleton/devspark/blob/main/CONTRIBUTING.md)
