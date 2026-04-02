# DevSpark Prompt Templates

This directory contains the **core deliverable** of DevSpark — prompt templates that give AI coding assistants structured commands for specification-driven development.

## Commands (`commands/`)

Each file in `commands/` is a slash-command prompt (e.g., `/devspark.specify`, `/devspark.plan`). When you run `devspark init`, these are deployed to your project's `.documentation/commands/` directory, where your AI agent picks them up.

| File | Command | Purpose |
|------|---------|---------|
| `specify.md` | `/devspark.specify` | Define requirements and user stories |
| `plan.md` | `/devspark.plan` | Create technical implementation plan |
| `tasks.md` | `/devspark.tasks` | Generate actionable task list |
| `implement.md` | `/devspark.implement` | Execute tasks to build the feature |
| `constitution.md` | `/devspark.constitution` | Establish project principles |
| `pr-review.md` | `/devspark.pr-review` | Review PRs against constitution |
| `site-audit.md` | `/devspark.site-audit` | Comprehensive codebase audit |
| `quickfix.md` | `/devspark.quickfix` | Lightweight bug fix workflow |
| `harvest.md` | `/devspark.harvest` | Clean and archive stale docs |
| `release.md` | `/devspark.release` | Archive artifacts and prepare releases |
| `evolve-constitution.md` | `/devspark.evolve-constitution` | Propose constitution amendments |
| `repo-story.md` | `/devspark.repo-story` | Narrative from commit history |
| `critic.md` | `/devspark.critic` | Adversarial risk analysis |
| `clarify.md` | `/devspark.clarify` | Clarify underspecified areas |
| `analyze.md` | `/devspark.analyze` | Cross-artifact consistency check |
| `checklist.md` | `/devspark.checklist` | Quality validation checklists |
| `personalize.md` | `/devspark.personalize` | Create per-user prompt overrides |
| `archive.md` | `/devspark.archive` | Archive completed work |
| `upgrade.md` | `/devspark.upgrade` | Upgrade project to latest templates |
| `discover-constitution.md` | `/devspark.discover-constitution` | Reverse-engineer principles from code |
| `taskstoissues.md` | `/devspark.taskstoissues` | Convert tasks to GitHub issues |

## Helper Templates

| File | Purpose |
|------|---------|
| `spec-template.md` | Template structure for feature specifications |
| `plan-template.md` | Template structure for implementation plans |
| `tasks-template.md` | Template structure for task breakdowns |
| `checklist-template.md` | Template structure for quality checklists |
| `agent-file-template.md` | Template for agent configuration files |
| `vscode-settings.json` | Recommended VS Code settings |
