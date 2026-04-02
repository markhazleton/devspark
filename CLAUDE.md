# DevSpark

Spec-driven development process for AI coding assistants. Just markdown files — no install required.

## Constitution

Read `.documentation/memory/constitution.md` before making changes — it defines non-negotiable principles.

## Repository Structure

- `templates/commands/` — 21 slash-command prompt files (the product)
- `scripts/` — Context-gathering scripts (PowerShell + Bash)
- `src/devspark_cli/` — Optional CLI for automated setup
- `quickstart/` — Agent-specific bootstrap guides
- `.documentation/` — Guides, media, and GitHub Pages site

## Commands

Use `/devspark.{command}` to invoke workflows:

- `/devspark.specify` — Define requirements and user stories
- `/devspark.plan` — Create implementation plan
- `/devspark.tasks` — Break plan into actionable tasks
- `/devspark.implement` — Execute tasks
- `/devspark.pr-review` — Constitution-based PR review
- `/devspark.quickfix` — Lightweight bug fix workflow

Full list in `templates/commands/`.

## Coding Standards

- Python 3.11+, typed with typer/rich/click
- Markdown linted via markdownlint-cli2 (config: `.markdownlint-cli2.jsonc`)
- Scripts in both PowerShell and Bash (keep parity)
- Never overwrite `.documentation/` user artifacts during CLI operations
