# DevSpark Quickstart — GitHub Copilot

You are bootstrapping **DevSpark**, a spec-driven development process, into this repository.
No CLI installation is required. You will pull prompt files from the DevSpark repo and place them in the correct directories.

## Step 1: Gather Project Context

Ask the user these questions before proceeding:

1. **Project name** — What is this project called?
2. **Tech stack** — What languages, frameworks, and tools does this project use?
3. **Script preference** — Does this project use **PowerShell** (`ps`) or **Bash** (`sh`) for scripts? (Default: PowerShell on Windows, Bash on macOS/Linux)
4. **Team or solo?** — Will multiple people use DevSpark on this repo, or just you?
5. **Core principles** — Name 3–5 non-negotiable principles for this project (e.g., "test-first", "accessibility", "API-first", "simplicity"). If unsure, say "use defaults" and you'll get a starter set.

Wait for answers before continuing.

---

## Step 2: Detect Existing Installation

Before creating anything, check for prior legacy / DevSpark installations:

| Check for | What it means |
|---|---|
| `.devspark/` exists | **DevSpark already installed.** See "Version Check" below. |
| `.documentation/` exists | **User artifacts exist.** Preserve everything — never overwrite. |
| `.specify/` exists | **Legacy layout detected.** Needs migration. |
| `.documentation/defaults/commands/` exists | **Pre-separation DevSpark.** Stock commands need to move to `.devspark/`. |
| Root `memory/` (without `.documentation/memory/`) | **Legacy structure.** Needs migration. |
| Root `scripts/` or `templates/` (without `.devspark/scripts/`) | **Legacy structure.** Needs migration. |
| `.github/agents/specify.*.agent.md` files | **Legacy shims detected.** Rename to `devspark.*` prefix. |

**If nothing is found**, skip ahead to Step 3.

### Migration: `.specify/` (legacy layout)

Tell the user what you found and ask for confirmation before proceeding.

1. Copy `.specify/memory/*` → `.documentation/memory/` (skip files that already exist at destination)
2. Copy `.specify/specs/*` → `.documentation/specs/` (skip files that already exist)
3. Copy any `.specify/` root-level `.md` files → `.documentation/` (skip files that already exist)
4. Rename `.specify/` → `.specify.old/` (preserve as backup)
5. Report: "Migrated .specify/ → .documentation/. Backup at .specify.old/"

### Migration: `.documentation/defaults/` (pre-separation DevSpark)

1. Create `.devspark/` directory structure
2. Move `.documentation/defaults/commands/*` → `.devspark/defaults/commands/`
3. Move `.documentation/defaults/templates/*` → `.devspark/templates/` if present
4. Move `.documentation/scripts/*` → `.devspark/scripts/` (only stock DevSpark scripts with framework header comments — leave user-created scripts)
5. Move `.documentation/templates/*` → `.devspark/templates/` (only stock DevSpark templates)
6. Delete empty `.documentation/defaults/` if nothing remains
7. Report: "Migrated framework files from .documentation/ → .devspark/"

### Migration: Root-level directories (legacy layout)

1. Copy `memory/*` → `.documentation/memory/` (skip existing)
2. Copy `specs/*` → `.documentation/specs/` (skip existing)
3. Rename migrated directories → `{name}.old/` (e.g., `memory.old/`)

### Migration: Old agent shims

1. Rename `.github/agents/specify.*.agent.md` → `.github/agents/devspark.*.agent.md`
2. Rename `.github/prompts/specify.*.prompt.md` → `.github/prompts/devspark.*.prompt.md`
3. In all shim files, replace `.documentation/defaults/commands/` → `.devspark/defaults/commands/`
4. Check `.claude/commands/specify.*` and `.cursor/commands/specify.*` — rename to `devspark.*` prefix if found

After migration, continue with Step 3.

### If `.devspark/` already exists — Version Check

1. Read `.devspark/VERSION`. If the file is missing or `version:` is not semver (`X.Y.Z`), treat the installed version as `unknown`.
2. Fetch `https://raw.githubusercontent.com/markhazleton/devspark/main/CHANGELOG.md` and extract the most recent `## [X.Y.Z]` heading as `LATEST_VERSION`.
3. Compare and act:

| Installed version | Latest version | Action |
|---|---|---|
| Same as latest | — | Report: "DevSpark is already at vX.Y.Z — nothing to update." Skip to Step 12 (Verify & Report). |
| Older than latest | Newer | Report the version gap, then run **update mode** below. |
| `unknown` (VERSION missing) | Any | Treat as outdated. Run update mode. |

#### Update Mode

Tell the user: "Updating DevSpark from vX.Y.Z → vY.Y.Y. Your `.documentation/` files will not be touched."

Execute **only** these steps in order, then skip to Step 12 (Verify & Report):

- **Step 4** — Re-fetch all stock prompts into `.devspark/defaults/commands/` (overwrite)
- **Step 5** — Re-fetch all helper templates into `.devspark/templates/` (overwrite)
- **Step 6** — Re-fetch all scripts into `.devspark/scripts/` (overwrite)
- **Step 7** — Re-create all agent shim files (overwrite — shims are framework files)
- **Step 10** — Update `.devspark/VERSION` with new version and today's date

**Never touch** `.documentation/`, the constitution, `.gitignore`, or platform guide files (VS Code settings, etc.).

---

## Step 3: Create Directory Structure

Create these directories (skip any that already exist):

```text
.devspark/
├── defaults/commands/
├── scripts/
└── templates/

.documentation/
├── memory/
├── specs/
├── commands/          ← team-level overrides (optional)
└── decisions/

.github/
├── agents/
└── prompts/

.vscode/
```

---

## Step 4: Pull Stock Prompts

Fetch each file from `https://raw.githubusercontent.com/markhazleton/devspark/main/templates/commands/` and save to `.devspark/defaults/commands/` with the `devspark.` prefix:

| Source file | Destination |
|---|---|
| `specify.md` | `.devspark/defaults/commands/devspark.specify.md` |
| `plan.md` | `.devspark/defaults/commands/devspark.plan.md` |
| `tasks.md` | `.devspark/defaults/commands/devspark.tasks.md` |
| `implement.md` | `.devspark/defaults/commands/devspark.implement.md` |
| `create-pr.md` | `.devspark/defaults/commands/devspark.create-pr.md` |
| `constitution.md` | `.devspark/defaults/commands/devspark.constitution.md` |
| `pr-review.md` | `.devspark/defaults/commands/devspark.pr-review.md` |
| `quickfix.md` | `.devspark/defaults/commands/devspark.quickfix.md` |
| `harvest.md` | `.devspark/defaults/commands/devspark.harvest.md` |
| `release.md` | `.devspark/defaults/commands/devspark.release.md` |
| `critic.md` | `.devspark/defaults/commands/devspark.critic.md` |
| `clarify.md` | `.devspark/defaults/commands/devspark.clarify.md` |
| `analyze.md` | `.devspark/defaults/commands/devspark.analyze.md` |
| `checklist.md` | `.devspark/defaults/commands/devspark.checklist.md` |
| `personalize.md` | `.devspark/defaults/commands/devspark.personalize.md` |
| `site-audit.md` | `.devspark/defaults/commands/devspark.site-audit.md` |
| `evolve-constitution.md` | `.devspark/defaults/commands/devspark.evolve-constitution.md` |
| `discover-constitution.md` | `.devspark/defaults/commands/devspark.discover-constitution.md` |
| `repo-story.md` | `.devspark/defaults/commands/devspark.repo-story.md` |
| `archive.md` | `.devspark/defaults/commands/devspark.archive.md` |
| `upgrade.md` | `.devspark/defaults/commands/devspark.upgrade.md` |
| `update-pr.md` | `.devspark/defaults/commands/devspark.update-pr.md` |
| `taskstoissues.md` | `.devspark/defaults/commands/devspark.taskstoissues.md` |
| `add-application.md` | `.devspark/defaults/commands/devspark.add-application.md` |
| `list-applications.md` | `.devspark/defaults/commands/devspark.list-applications.md` |
| `validate-registry.md` | `.devspark/defaults/commands/devspark.validate-registry.md` |

---

## Step 5: Pull Helper Templates

Fetch from `https://raw.githubusercontent.com/markhazleton/devspark/main/templates/` and save to `.devspark/templates/`:

- `spec-template.md`
- `plan-template.md`
- `tasks-template.md`
- `quick-spec-template.md`
- `checklist-template.md`
- `agent-file-template.md`
- `vscode-settings.json`

---

## Step 6: Pull Scripts

Fetch scripts from `https://raw.githubusercontent.com/markhazleton/devspark/main/scripts/` based on the user's script preference from Step 1.

For **PowerShell** (`ps`), save to `.devspark/scripts/powershell/`:

- `powershell/common.ps1`
- `powershell/platform.ps1`
- `powershell/check-prerequisites.ps1`
- `powershell/create-new-feature.ps1`
- `powershell/setup-plan.ps1`
- `powershell/get-pr-context.ps1`
- `powershell/create-pr.ps1`
- `powershell/update-agent-context.ps1`
- `powershell/archive-context.ps1`
- `powershell/evolution-context.ps1`
- `powershell/harvest.ps1`
- `powershell/quickfix-context.ps1`
- `powershell/release-context.ps1`
- `powershell/repo-story-context.ps1`
- `powershell/site-audit.ps1`

For **Bash** (`sh`), save to `.devspark/scripts/bash/`:

- `bash/common.sh`
- `bash/platform.sh`
- `bash/check-prerequisites.sh`
- `bash/create-new-feature.sh`
- `bash/setup-plan.sh`
- `bash/get-pr-context.sh`
- `bash/create-pr.sh`
- `bash/update-agent-context.sh`
- `bash/archive-context.sh`
- `bash/evolution-context.sh`
- `bash/harvest.sh`
- `bash/quickfix-context.sh`
- `bash/release-context.sh`
- `bash/repo-story-context.sh`
- `bash/site-audit.sh`

**Script override layer:** If the team later needs to customize a script (e.g., for Azure DevOps instead of GitHub), they copy the script to `.documentation/scripts/{bash|powershell}/` and edit it there. The team copy takes priority over the stock version in `.devspark/scripts/`. Upgrades only overwrite `.devspark/scripts/` and never touch `.documentation/scripts/`.

---

## Step 7: Create Copilot Agent Shims

For each command in `.devspark/defaults/commands/devspark.{name}.md`, create two files:

### `.github/agents/devspark.{name}.agent.md`

```markdown
---
name: "devspark.{name}"
description: "{one-line description of the command}"
---

## Prompt Resolution

Determine the current git user by running `git config user.name`.
Normalize to a folder-safe slug: lowercase, replace spaces with hyphens, strip non-alphanumeric/hyphen chars.

Read and execute the instructions from the **first file that exists**:
1. `.documentation/{git-user}/commands/devspark.{name}.md` (personalized override)
2. `.documentation/commands/devspark.{name}.md` (team customization)
3. `.devspark/defaults/commands/devspark.{name}.md` (stock default)

## User Input

{{input}}

Pass the user input above to the resolved prompt.
```

### `.github/prompts/devspark.{name}.prompt.md`

Create a companion prompt file with the same 3-tier resolution content (without YAML frontmatter).

---

## Step 8: VS Code Settings

Copy `.devspark/templates/vscode-settings.json` to `.vscode/settings.json`. If the file already exists, merge the `github.copilot` settings into it without overwriting other settings.

---

## Step 9: Seed the Constitution

If `.documentation/memory/constitution.md` does not already exist, fetch `https://raw.githubusercontent.com/markhazleton/devspark/main/.documentation/memory/constitution.md` and save it there.

If the file was migrated from `.specify/` or already existed, preserve it and do not overwrite it.

Using the project name and principles from Step 1, customize `.documentation/memory/constitution.md`:

- Replace `[PROJECT_NAME]` with the actual project name
- Fill in the core principles the user provided
- Add the tech stack as a "Technology" or "Stack" section

---

## Step 10: Write VERSION Stamp

Use the `LATEST_VERSION` you already fetched in Step 2.

Create `.devspark/VERSION`:

```text
version: {LATEST_VERSION}
installed: {today's date YYYY-MM-DD}
method: copilot-quickstart
migrated-from: {legacy-layout | documentation-defaults | fresh}
```

---

## Step 11: Update .gitignore

Append to `.gitignore` if not already present:

```text
# DevSpark — personal overrides (never commit)
.documentation/*/commands/
```

---

## Step 12: Verify & Report

Confirm the installation:

- **Migration summary**: What was migrated and where backups live (`.specify.old/`, etc.)
- Number of stock commands in `.devspark/defaults/commands/`
- Number of agent shims in `.github/agents/`
- Constitution status: seeded fresh, migrated, or already existed
- Explain the 3-tier override system and that `@devspark.personalize {command}` creates personal overrides
- If backup directories exist (`.specify.old/`, `memory.old/`), remind the user they can delete them once satisfied

Tell the user: type `@devspark.specify` (or any command) in Copilot Chat to start using DevSpark.

Add maintenance guidance (prompt-first):

- Basic (recommended): run the remote upgrade prompt in chat
- `@workspace Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/templates/commands/upgrade.md`
- Advanced (optional): if CLI is installed, run `devspark upgrade`

For either path, upgrades refresh `.devspark/` stock files and preserve `.documentation/` customizations.

---

## Multi-App Monorepo Support (Optional)

> **This section is entirely optional.** If your repository contains a single application, skip this section — DevSpark works perfectly without it.

For repositories containing **multiple applications** with different platforms, runtimes, or governance rules, DevSpark offers opt-in multi-app support.

### When to Consider Multi-App

- Your monorepo has apps with different tech stacks (e.g., .NET API + React UI)
- Different apps need different governance rules or risk profiles
- You want per-app constitutions, profiles, or code review scopes

### Quick Setup

1. Run `/devspark.add-application` to create a registry at `.documentation/devspark.json` interactively
2. Each application gets its own `.documentation/` directory at `{app-path}/.documentation/`
3. Use `--app <id>` with any DevSpark command to scope it to a specific application
4. Use `--repo-scope` for repository-wide operations

### Key Concepts

- **Registry**: `.documentation/devspark.json` defines all applications, profiles, and dependencies
- **Profiles**: Reusable rule bundles (e.g., `api-profile`, `web-profile`) that apps inherit
- **App-local manifest**: Optional `{app-path}/app.json` for app-specific overrides
- **Scope**: Every workflow runs in `repo`, `single-app`, or `cross-app` scope

### Commands

| Command | Purpose |
|---------|--------|
| `/devspark.add-application` | Register a new application in the registry |
| `/devspark.list-applications` | View all registered applications and profiles |
| `/devspark.validate-registry` | Validate registry schema, references, and consistency |

For details, see the [Multi-App Specification](https://github.com/markhazleton/devspark/blob/main/.documentation/specs/001-multi-app-monorepo-support/spec.md).
