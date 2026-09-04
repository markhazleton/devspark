# DevSpark Quickstart — Cursor

You are bootstrapping **DevSpark**, a spec-driven development process, into this repository.
You will pull prompt files from the DevSpark repo and place them in the correct directories.

## Step 1: Gather Project Context

No install-critical questions are needed before proceeding — **both** shell script sets (PowerShell and Bash) plus Python utility scripts are always installed regardless of OS. Detect the current OS to display in the plan preview.

**OS detection** (in priority order):

1. If the workspace path contains a drive letter (e.g., `C:\`) or backslash separators → **Windows** (active runtime: PowerShell)
2. If the shell environment is bash/zsh/sh → **macOS/Linux** (active runtime: Bash)

State the detected OS before proceeding:
> *"Detected: Windows — active runtime PowerShell. Installing PowerShell, Bash, and Python utility scripts."*
> *"Detected: macOS/Linux — active runtime Bash. Installing PowerShell, Bash, and Python utility scripts."*

---

## Step 2: Detect Existing Installation

Before creating anything, check for prior legacy / DevSpark installations:

| Check for | What it means |
|---|---|
| `.devspark/` exists | **DevSpark already installed.** See "Version Check" below. |
| `.knowledge/` exists | **User artifacts exist.** Preserve authored files; initialize missing entity and ontology scaffolding. |
| `.specify/` exists | **Legacy layout detected.** Needs migration. |
| `.documentation/` or `.documenation/` exists | **Documentation intake detected.** Classify into `.knowledge/` or `.devspark.work/`; obsolete inputs wait under `.devspark.work/release-candidates/` for release. |
| `.devspark/defaults/commands/` exists | **Pre-separation DevSpark.** Stock commands need to move to `.devspark/`. |
| Root `memory/` (without `.knowledge/governance/`) | **Legacy structure.** Needs migration. |
| Root `scripts/` or `templates/` (without `.devspark/scripts/`) | **Legacy structure.** Needs migration. |
| `.cursor/commands/specify.*.md` files | **Legacy shims detected.** Rename to `devspark.*` prefix. |

**If nothing is found**, skip ahead to Step 3.

### Migration: `.specify/` (legacy layout)

Tell the user what you found and ask for confirmation before proceeding.

1. Copy `.specify/memory/*` → `.knowledge/governance/` (skip files that already exist at destination)
2. Copy `.specify/specs/*` → `.devspark.work/specs/` (skip files that already exist)
3. Copy any `.specify/` root-level `.md` files → `.knowledge/` (skip files that already exist)
4. Rename `.specify/` → `.specify.old/` (preserve as backup)
5. Report: "Migrated .specify/ → .knowledge/. Backup at .specify.old/"

### Migration: `.devspark/` (pre-separation DevSpark)

1. Create `.devspark/` directory structure
2. Move `.devspark/defaults/commands/*` → `.devspark/defaults/commands/`
3. Move `.devspark/templates/*` → `.devspark/templates/` if present
4. Move `.knowledge/overrides/scripts/*` → `.devspark/scripts/` (only stock DevSpark scripts with framework header comments — leave user-created scripts)
5. Move `.knowledge/overrides/templates/*` → `.devspark/templates/` (only stock DevSpark templates)
6. Delete empty `.devspark/` if nothing remains
7. Report: "Migrated framework files from .knowledge/ → .devspark/"

### Migration: Root-level directories (legacy layout)

1. Copy `memory/*` → `.knowledge/governance/` (skip existing)
2. Copy `specs/*` → `.devspark.work/specs/` (skip existing)
3. Rename migrated directories → `{name}.old/` (e.g., `memory.old/`)

### Migration: Old agent shims

1. Rename `.cursor/commands/specify.*.md` → `.cursor/commands/devspark.*.md`
2. In all shim files, replace `.devspark/defaults/commands/` → `.devspark/defaults/commands/`
3. Check `.github/agents/specify.*` and `.claude/commands/specify.*` — rename to `devspark.*` prefix if found

After migration, continue with Step 3.

### Constitution bootstrap questions (only if needed)

After detection and any migration work above, check whether `.knowledge/governance/constitution.md` already exists.

- If it exists already, or was migrated into place, **do not** ask for project name, tech stack, or core principles.
- If it does not exist, ask these additional questions before Step 3:
  1. **Project name** — What is this project called?
  2. **Tech stack** — What languages, frameworks, and tools does this project use?
  3. **Core principles** — Name 3–5 non-negotiable principles for this project (e.g., "test-first", "accessibility", "API-first", "simplicity"). If unsure, say "use defaults" and you'll get a starter set.

### If `.devspark/` already exists — Version Check

1. Read `.devspark/VERSION`. If the file is missing or `version:` is not semver (`X.Y.Z`), treat the installed version as `unknown`.
2. Fetch `https://api.github.com/repos/markhazleton/devspark/releases/latest`, read `tag_name`, and strip the leading `v` to get `LATEST_VERSION`. Only if the Releases API is unreachable, fetch `https://raw.githubusercontent.com/markhazleton/devspark/main/CHANGELOG.md` and extract the most recent `## [vX.Y.Z]` or `## [X.Y.Z]` heading as a fallback.
3. Compare and act:

| Installed version | Latest version | Action |
|---|---|---|
| Same as latest | — | Verify framework files. If any stock prompt, template, script, or command shim is missing, run **repair mode** below. Otherwise run **Step 6.5** to initialize or repair `.knowledge/`, then report: "DevSpark is already at vX.Y.Z — framework files are current; knowledge initialization checked." Skip to Step 12 (Verify & Report). |
| Older than latest | Newer | Report the version gap, then run **update mode** below. |
| `unknown` (VERSION missing) | Any | Treat as outdated. Run **update mode**. |

#### Update Mode

Tell the user: "Updating DevSpark from vX.Y.Z → vY.Y.Y. Existing `.knowledge/` files will be preserved; missing or incomplete knowledge scaffolding will be initialized."

Execute **only** these steps in order, then skip to Step 12 (Verify & Report):

- **Step 4** — Re-fetch all stock prompts into `.devspark/defaults/commands/` (overwrite)
- **Step 5** — Re-fetch all helper templates into `.devspark/templates/` (overwrite)
- **Step 5.5** — Re-fetch all Agent Skill packages into `.devspark/templates/skills/` (overwrite)
- **Step 6** — Re-fetch all scripts into `.devspark/scripts/` (overwrite)
- **Step 6.5** — Initialize or repair `.knowledge/entities/` and `.knowledge/ontology/`, and classify `.documentation/` intake if present
- **Step 7** — Re-create all agent shim files (overwrite — shims are framework files)
- **Step 10** — Update `.devspark/VERSION` with new version and today's date

**Preserve existing authored files** in `.knowledge/`, the constitution, `.gitignore`, and platform guide files (`.cursorrules`, etc.). Only create missing knowledge scaffolding, regenerate generated ontology files, or assimilate `.documentation/` content after review.

#### Repair Mode

If the installed version matches `LATEST_VERSION` but framework files are missing, tell the user: "DevSpark is already at vX.Y.Z, but the framework install is incomplete. Re-fetching stock files and checking knowledge initialization. Existing `.knowledge/` files will be preserved."

Execute **only** these steps in order, then skip to Step 12 (Verify & Report):

- **Step 4** — Re-fetch all stock prompts into `.devspark/defaults/commands/` (overwrite missing or stale copies)
- **Step 5** — Re-fetch all helper templates into `.devspark/templates/` (overwrite missing or stale copies)
- **Step 5.5** — Re-fetch all Agent Skill packages into `.devspark/templates/skills/` (overwrite missing or stale copies)
- **Step 6** — Re-fetch all scripts into `.devspark/scripts/` (overwrite missing or stale copies)
- **Step 6.5** — Initialize or repair `.knowledge/entities/` and `.knowledge/ontology/`, and classify `.documentation/` intake if present
- **Step 7** — Re-create all agent shim files (overwrite missing or stale copies)
- **Step 10** — Re-write `.devspark/VERSION` using the current `LATEST_VERSION` and today's date

---

## Step 3: Create Directory Structure

Create these directories (skip any that already exist):

```text
.devspark/
├── defaults/commands/
├── scripts/
└── templates/

.knowledge/
├── entities/
├── governance/
│   └── decisions/
├── ontology/
└── overrides/
    └── commands/          ← team-level overrides (optional)

.cursor/
└── commands/
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
| `address-pr-review.md` | `.devspark/defaults/commands/devspark.address-pr-review.md` |
| `quickfix.md` | `.devspark/defaults/commands/devspark.quickfix.md` |
| `release.md` | `.devspark/defaults/commands/devspark.release.md` |
| `critic.md` | `.devspark/defaults/commands/devspark.critic.md` |
| `clarify.md` | `.devspark/defaults/commands/devspark.clarify.md` |
| `analyze.md` | `.devspark/defaults/commands/devspark.analyze.md` |
| `checklist.md` | `.devspark/defaults/commands/devspark.checklist.md` |
| `personalize.md` | `.devspark/defaults/commands/devspark.personalize.md` |
| `site-audit.md` | `.devspark/defaults/commands/devspark.site-audit.md` |
| `explain.md` | `.devspark/defaults/commands/devspark.explain.md` |
| `next.md` | `.devspark/defaults/commands/devspark.next.md` |
| `evolve-constitution.md` | `.devspark/defaults/commands/devspark.evolve-constitution.md` |
| `discover-constitution.md` | `.devspark/defaults/commands/devspark.discover-constitution.md` |
| `discover-knowledge.md` | `.devspark/defaults/commands/devspark.discover-knowledge.md` |
| `repo-story.md` | `.devspark/defaults/commands/devspark.repo-story.md` |
| `update-pr.md` | `.devspark/defaults/commands/devspark.update-pr.md` |
| `taskstoissues.md` | `.devspark/defaults/commands/devspark.taskstoissues.md` |
| `add-application.md` | `.devspark/defaults/commands/devspark.add-application.md` |
| `list-applications.md` | `.devspark/defaults/commands/devspark.list-applications.md` |
| `validate-registry.md` | `.devspark/defaults/commands/devspark.validate-registry.md` |
| `commit-audit.md` | `.devspark/defaults/commands/devspark.commit-audit.md` |
| `fix-score.md` | `.devspark/defaults/commands/devspark.fix-score.md` |
| `verify.md` | `.devspark/defaults/commands/devspark.verify.md` |

---

## Step 5: Pull Helper Templates

Fetch from `https://raw.githubusercontent.com/markhazleton/devspark/main/templates/` and save to `.devspark/templates/`:

- `spec-template.md`
- `plan-template.md`
- `tasks-template.md`
- `quick-spec-template.md`
- `checklist-template.md`
- `agent-file-template.md`
- `command-preamble-contract.md`
- `rationale-template.md`
- `spec-validation-contract.md`
- `README.md`

Also fetch every file recursively under these template subdirectories, preserving the same relative paths under `.devspark/templates/`:

- `knowledge/`
- `prompts/`
- `risk-checklists/`
- `schemas/`
- `skills/`

Do not fetch `templates/commands/` in this step — Step 4 installs command prompts into `.devspark/defaults/commands/`. Do not fetch `templates/vscode-settings.json`.

Also fetch `https://raw.githubusercontent.com/markhazleton/devspark/main/agents-registry.json` and save it to `agents-registry.json` at the repository root.

---

## Step 5.5: Pull Agent Skills

Current DevSpark releases delegate some command reasoning to portable **Agent Skill** packages under `.devspark/templates/skills/`. `/devspark.specify` requires the `write-spec` skill — without it, the command silently degrades to legacy inline behaviour.

Fetch each file below from `https://raw.githubusercontent.com/markhazleton/devspark/main/` and save it to the matching path under `.devspark/templates/skills/` (preserve the subdirectory structure):

- `templates/skills/README.md`
- `templates/skills/ADAPTER-contract.md`
- `templates/skills/SKILL-validation-contract.md`
- `templates/skills/references/devspark-skills-guide.md`
- `templates/skills/write-spec/SKILL.md`
- `templates/skills/write-spec/references/spec-template.md`
- `templates/skills/write-spec/scripts/gather-context.ps1`
- `templates/skills/write-spec/scripts/gather-context.sh`

> Skills are framework-owned and safe to overwrite on every install or upgrade. They never touch `.knowledge/`.

### Step 5.5 Validation (required)

After fetching, verify the critical skill files landed:

```powershell
@(
  'ADAPTER-contract.md',
  'SKILL-validation-contract.md',
  'write-spec/SKILL.md',
  'write-spec/scripts/gather-context.ps1',
  'write-spec/scripts/gather-context.sh',
  'write-spec/references/spec-template.md'
) | ForEach-Object {
  if (-not (Test-Path ".devspark/templates/skills/$_")) { Write-Host "MISSING: skills/$_" }
}
```

```bash
for f in ADAPTER-contract.md SKILL-validation-contract.md \
         write-spec/SKILL.md write-spec/scripts/gather-context.ps1 \
         write-spec/scripts/gather-context.sh write-spec/references/spec-template.md; do
  [ -f ".devspark/templates/skills/$f" ] || echo "MISSING: skills/$f"
done
```

If any skill file is missing, re-fetch it before continuing. A missing `write-spec/SKILL.md` will cause `/devspark.specify` to silently fall back to legacy inline behaviour.

---

## Step 6: Pull Scripts

Fetch the script payload from `https://raw.githubusercontent.com/markhazleton/devspark/main/scripts/` — always install both PowerShell and Bash script sets plus Python utility scripts, regardless of the current OS. This ensures the repository works for developers on macOS, Linux, and Windows without requiring a reinstall when switching machines.

Save to `.devspark/scripts/powershell/`:

- `powershell/address-pr-review.ps1`
- `powershell/check-prerequisites.ps1`
- `powershell/common.ps1`
- `powershell/create-new-feature.ps1`
- `powershell/create-pr.ps1`
- `powershell/delivery-status-smoke-test.ps1`
- `powershell/evolution-context.ps1`
- `powershell/fix-score-context.ps1`
- `powershell/generate-atomic-shims.ps1`
- `powershell/get-pr-context.ps1`
- `powershell/platform.ps1`
- `powershell/quickfix-context.ps1`
- `powershell/release-context.ps1`
- `powershell/release-history-context.ps1`
- `powershell/repo-story-context.ps1`
- `powershell/setup-plan.ps1`
- `powershell/site-audit.ps1`
- `powershell/explain-context.ps1`
- `powershell/next-context.ps1`
- `powershell/update-agent-context.ps1`

Save to `.devspark/scripts/bash/`:

- `bash/address-pr-review.sh`
- `bash/check-prerequisites.sh`
- `bash/common.sh`
- `bash/create-new-feature.sh`
- `bash/create-pr.sh`
- `bash/delivery-status-smoke-test.sh`
- `bash/evolution-context.sh`
- `bash/fix-score-context.sh`
- `bash/generate-atomic-shims.sh`
- `bash/get-pr-context.sh`
- `bash/platform.sh`
- `bash/quickfix-context.sh`
- `bash/release-context.sh`
- `bash/release-history-context.sh`
- `bash/repo-story-context.sh`
- `bash/setup-plan.sh`
- `bash/site-audit.sh`
- `bash/explain-context.sh`
- `bash/next-context.sh`
- `bash/update-agent-context.sh`

Save to `.devspark/scripts/python/`:

- `python/build_knowledge_index.py`

**Runtime OS selection:** Commands define both `sh` and `ps` script variants. The AI agent selects the appropriate variant at execution time based on the active OS — PowerShell on Windows, Bash on macOS/Linux. Python utility scripts are invoked directly by prompts that need deterministic ontology checks. Because the full script payload is always installed, switching between machines never requires a reinstall.

**Script override layer:** If the team later needs to customize a script (e.g., for Azure DevOps instead of GitHub), they copy the script to `.knowledge/overrides/scripts/{bash|powershell|python}/` and edit it there. The team copy takes priority over the stock version in `.devspark/scripts/`. Upgrades only overwrite `.devspark/scripts/` and never touch `.knowledge/overrides/scripts/`.

---

## Step 6.5: Initialize Knowledge Current Truth

Run this step on **every quickstart execution**: fresh install, migration, update, repair, and already-current verification. This step is repository-owned current-truth maintenance, not a framework overwrite.

1. Create these directories if they are missing: `.knowledge/entities/`, `.knowledge/governance/decisions/`, `.knowledge/ontology/`, `.knowledge/overrides/commands/`, `.devspark.work/`, and `.devspark.work/release-candidates/`. Release creates `.archive/` only when it has validated work to archive.
2. Seed missing knowledge scaffolding from the fetched templates without overwriting authored files:
   - `.devspark/templates/knowledge/entities/README.md` -> `.knowledge/entities/README.md`
   - `.devspark/templates/knowledge/ontology/schema.md` -> `.knowledge/ontology/schema.md`
   - `.devspark/templates/knowledge/governance/decisions/README.md` -> `.knowledge/governance/decisions/README.md`
3. If those template files were not fetched yet, fetch the same paths from `https://raw.githubusercontent.com/markhazleton/devspark/main/templates/knowledge/` and save only when the destination is missing.
4. Inspect `.knowledge/entities/` and `.knowledge/ontology/` for completeness. Treat knowledge as incomplete when no entity folder contains `_entity.yaml`, required entity layer documents are missing, generated ontology files are missing or stale, or `.documentation/` / `.documenation/` intake exists.
5. If knowledge is incomplete, execute the installed `discover-knowledge` command in bootstrap mode by reading and following `.devspark/defaults/commands/devspark.discover-knowledge.md` with `--bootstrap`. If agent shims already exist, `/devspark.discover-knowledge --bootstrap` is equivalent. The command body is authoritative for source-code scanning, entity creation, documentation intake classification, evidence updates, and ontology refresh.
6. If knowledge is already complete, run the ontology generator only when generated files are stale or missing:
   - Preferred: `python .devspark/scripts/python/build_knowledge_index.py --write`
   - Fallback in the DevSpark source repository: `python scripts/python/build_knowledge_index.py --write`
   - If Python or dependencies are unavailable, report the exact command the user must run and continue without fabricating generated reports.
7. Do not delete documentation intake files. When `discover-knowledge` moves intake files, it must preserve relative paths and avoid overwriting by adding a numeric suffix if the target path already exists.
8. Do not write to `.archive/`. Stage obsolete intake under `.devspark.work/release-candidates/`; `/devspark.release` is the sole archive writer.
9. If generated ontology output changed, include that in the final summary.

---

## Step 7: Create Cursor Command Shims

For each command in `.devspark/defaults/commands/devspark.{name}.md`, create a file at `.cursor/commands/devspark.{name}.md`:

```markdown
## Prompt Resolution

Determine the current git user by running `git config user.name`.
Normalize to a folder-safe slug: lowercase, replace spaces with hyphens, strip non-alphanumeric/hyphen chars.

Read and execute the instructions from the **first file that exists**:
1. `.knowledge/overrides/{git-user}/commands/devspark.{name}.md` (personalized override)
2. `.knowledge/overrides/commands/devspark.{name}.md` (team customization)
3. `.devspark/defaults/commands/devspark.{name}.md` (stock default)

## User Input

{{input}}

Pass the user input above to the resolved prompt.
```

Replace `{name}` with the actual command name (e.g., `constitution`, `plan`, `implement`).

---

## Step 8: Create .cursorrules

If `.cursorrules` does not exist in the project root, create it:

```markdown
# DevSpark — Spec-Driven Development

This project uses DevSpark for structured, spec-driven development.

## Constitution
Before making changes, read `.knowledge/governance/constitution.md` — it defines the project's non-negotiable principles.

## Available Commands
Use `/devspark.{command}` to invoke DevSpark workflows:
- /devspark.specify — Define requirements and user stories
- /devspark.plan — Create implementation plan
- /devspark.tasks — Break plan into actionable tasks
- /devspark.implement — Execute tasks
- /devspark.create-pr — Draft or update a pull request
- /devspark.pr-review — Constitution-based PR review
- /devspark.quickfix — Lightweight bug fix workflow

See `.devspark/defaults/commands/` for the full command list.
```

If `.cursorrules` already exists, append the DevSpark section.

---

## Step 9: Seed the Constitution

If `.knowledge/governance/constitution.md` does not already exist, fetch `https://raw.githubusercontent.com/markhazleton/devspark/main/.knowledge/governance/constitution.md` and save it there.

If the file was migrated from `.specify/` or already existed, preserve it and do not overwrite it.

Only when creating a new constitution, use the project name, tech stack, and core principles collected after Step 2 to customize `.knowledge/governance/constitution.md`:

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
method: cursor-quickstart
migrated-from: {legacy-layout | documentation-defaults | fresh}
```

---

## Step 11: Update .gitignore

Append to `.gitignore` if not already present:

```text
# DevSpark — personal overrides (never commit)
.knowledge/overrides/*/commands/
```

---

## Step 12: Verify & Report

Confirm the installation:

- Check that every stock prompt from Step 4 exists in `.devspark/defaults/commands/`
- Check that every helper template from Step 5 exists in `.devspark/templates/`
- Check that both shell script sets and Python utility scripts from Step 6 exist under `.devspark/scripts/`
- Check that `.knowledge/entities/` and `.knowledge/ontology/schema.md` exist, and report any `.documentation/` intake files classified
- Check that the expected command shim files from Step 7 exist in `.cursor/commands/`
- If any expected framework file is missing, stop and run **Repair Mode** before reporting success

- **Migration summary**: What was migrated and where backups live (`.specify.old/`, etc.)
- Number of stock commands in `.devspark/defaults/commands/`
- Number of command shims in `.cursor/commands/`
- Constitution status: seeded fresh, migrated, or already existed
- Knowledge initialization status: scaffolded, repaired, already complete, or blocked with the exact command needed
- Documentation intake summary: staged for release, moved to `.devspark.work/`, assimilated to `.knowledge/`, or not present
- Repair status: not needed, or repaired missing framework files
- Explain the 3-tier override system and that `/devspark.personalize {command}` creates personal overrides
- If backup directories exist, remind the user they can stage them under `.devspark.work/release-candidates/` for the next `/devspark.release`

Tell the user: type `/devspark.specify` (or any command) in Cursor to start using DevSpark.

Add maintenance guidance (prompt-first):

- Basic (recommended): run the remote upgrade prompt in chat
- Re-run this quickstart prompt in the target repository for install, upgrade, or repair.`r`n
Quickstart-driven upgrades refresh `.devspark/` stock files, preserve authored `.knowledge/` customizations, and repair missing knowledge scaffolding.

---

## Multi-App Monorepo Support (Optional)

> **This section is entirely optional.** If your repository contains a single application, skip this section — DevSpark works perfectly without it.

For repositories containing **multiple applications** with different platforms, runtimes, or governance rules, DevSpark offers opt-in multi-app support.

### When to Consider Multi-App

- Your monorepo has apps with different tech stacks (e.g., .NET API + React UI)
- Different apps need different governance rules or risk profiles
- You want per-app constitutions, profiles, or code review scopes

### Quick Setup

1. Run `/devspark.add-application` to create a registry at `.knowledge/entities/application-registry/registry.json` interactively
2. Each application gets its own `.knowledge/` directory at `{app-path}/.knowledge/`
3. Use `--app <id>` with any DevSpark command to scope it to a specific application
4. Use `--repo-scope` for repository-wide operations

### Key Concepts

- **Registry**: `.knowledge/entities/application-registry/registry.json` defines all applications, profiles, and dependencies
- **Profiles**: Reusable rule bundles (e.g., `api-profile`, `web-profile`) that apps inherit
- **App-local manifest**: Optional `{app-path}/app.json` for app-specific overrides
- **Scope**: Every workflow runs in `repo`, `single-app`, or `cross-app` scope

### Commands

| Command | Purpose |
|---------|--------|
| `/devspark.add-application` | Register a new application in the registry |
| `/devspark.list-applications` | View all registered applications and profiles |
| `/devspark.validate-registry` | Validate registry schema, references, and consistency |

For details, see the [Multi-App Specification](https://github.com/markhazleton/devspark/blob/main/.devspark.work/specs/001-multi-app-monorepo-support/spec.md).
