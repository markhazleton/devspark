# DevSpark

Spec-driven development process for AI coding assistants. Just markdown files — no install required.

## Constitution

Read `.documentation/memory/constitution.md` before making changes — it defines non-negotiable principles.

## Repository Structure

- `templates/commands/` — 27 slash-command prompt files (the product)
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
- `/devspark.create-pr` — Draft or update a pull request
- `/devspark.pr-review` — Constitution-based PR review
- `/devspark.quickfix` — Lightweight bug fix workflow
- `/devspark.add-application` — Register app in multi-app registry (optional)
- `/devspark.list-applications` — Display registered applications (optional)
- `/devspark.validate-registry` — Validate registry consistency (optional)

Full list in `templates/commands/`.

## Git Workflow Rules

- **HARD RULE — Branch Sync**: Before creating a PR or running `/devspark.pr-review`, the source (head) branch **MUST** be fully in sync with the target (base) branch. If the source branch is behind the target, do **NOT** proceed — rebase or merge first.
  - Check: `git fetch origin && git status`
  - Fix: `git rebase origin/main` or `gh pr update-branch {PR_NUMBER}`

## Coding Standards

- Python 3.11+, typed with typer/rich/click
- Markdown linted via markdownlint-cli2 (config: `.markdownlint-cli2.jsonc`)
- Scripts in both PowerShell and Bash (keep parity); context scripts support GitHub, AzDO, and GitLab
- Never overwrite `.documentation/` user artifacts during CLI operations
