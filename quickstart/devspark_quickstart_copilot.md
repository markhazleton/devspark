# DevSpark Quickstart — GitHub Copilot

You are bootstrapping **DevSpark**, a spec-driven development process, into this repository.
You will pull prompt files from the DevSpark repo and place them in the correct directories.

## Step 1: Gather Project Context

Detect the current OS to determine the active runtime for the plan preview — **both** shell script sets (PowerShell and Bash) plus Python utility scripts are always installed regardless of OS.

**OS detection** (in priority order):

1. If the workspace path contains a drive letter (e.g., `C:\`) or backslash separators → **Windows** (active runtime: PowerShell)
2. If `$env:OS` is `Windows_NT` or `$IsWindows` is true → **Windows** (active runtime: PowerShell)
3. If the shell environment is bash/zsh/sh → **macOS/Linux** (active runtime: Bash)
4. If none of the above can be determined → assume macOS/Linux

State the detected OS before proceeding:
> *"Detected: Windows — active runtime PowerShell. Installing PowerShell, Bash, and Python utility scripts."*
> *"Detected: macOS/Linux — active runtime Bash. Installing PowerShell, Bash, and Python utility scripts."*

---

## Step 2: Detect Existing Installation

Before creating anything, check for prior legacy / DevSpark installations:

| Check for | What it means |
|---|---|
| `.devspark/` exists | **DevSpark already installed.** See "Version Check" below. |
| `.knowledge/` exists | **User artifacts exist.** Preserve everything — never overwrite. |
| `.specify/` exists | **Legacy layout detected.** Needs migration. |
| `.devspark/defaults/commands/` exists | **Pre-separation DevSpark.** Stock commands need to move to `.devspark/`. |
| Root `memory/` (without `.knowledge/governance/`) | **Legacy structure.** Needs migration. |
| Root `scripts/` or `templates/` (without `.devspark/scripts/`) | **Legacy structure.** Needs migration. |
| `.github/agents/specify.*.agent.md` files | **Legacy shims detected.** Rename to `devspark.*` prefix. |

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

1. Rename `.github/agents/specify.*.agent.md` → `.github/agents/devspark.*.agent.md`
2. Rename `.github/prompts/specify.*.prompt.md` → `.github/prompts/devspark.*.prompt.md`
3. In all shim files, replace `.devspark/defaults/commands/` → `.devspark/defaults/commands/`
4. Check `.claude/commands/specify.*` and `.cursor/commands/specify.*` — rename to `devspark.*` prefix if found

After migration, continue with Step 3.

---

## Step 2b: Announce Mode and Preview Plan

**Before writing any files**, output a mode banner so the user knows exactly what is about to happen.

### Mode Banner

Choose the banner that matches the detected state from Step 2:

| Detected state | Banner to output |
|---|---|
| No `.devspark/` found, no legacy | `▶ Mode: FRESH INSTALL` |
| `.devspark/` found, version older than latest | `▶ Mode: UPDATE (vX.Y.Z → vY.Y.Y)` |
| `.devspark/` found, version matches latest, all files present | `▶ Mode: ALREADY CURRENT (vX.Y.Z) — nothing to do. Skipping to Step 12.` |
| `.devspark/` found, version matches latest, files missing | `▶ Mode: REPAIR (vX.Y.Z — re-fetching missing framework files)` |
| Legacy layout detected | `▶ Mode: MIGRATION → FRESH INSTALL` |

Output the banner, then immediately output a brief **plan preview** — one line per action group:

```text
Plan:
  • Create directories: .devspark/, .knowledge/, .github/, .vscode/
  • Fetch N stock prompts → .devspark/defaults/commands/
  • Fetch N templates → .devspark/templates/
  • Fetch N scripts → .devspark/scripts/bash/ + .devspark/scripts/powershell/ + .devspark/scripts/python/ (full payload)
  • Generate N agent shims → .github/agents/ and .github/prompts/
  • Seed constitution → .knowledge/governance/constitution.md  [if needed]
  • Write VERSION stamp → .devspark/VERSION
  • Update .gitignore
```

For Update and Repair modes, show only the steps that will actually run.

Proceed immediately after outputting the banner and plan — no additional confirmation needed unless you are about to perform a migration that renames or deletes directories.

---

### Constitution bootstrap questions (only if needed — Fresh Install only)

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
| Same as latest | — | Verify framework files. If any stock prompt, template, script, or agent shim is missing, run **repair mode** below. Otherwise report: "DevSpark is already at vX.Y.Z — nothing to update." Skip to Step 12 (Verify & Report). |
| Older than latest | Newer | Report the version gap, then run **update mode** below. |
| `unknown` (VERSION missing) | Any | Treat as outdated. Run **update mode**. |

#### Update Mode

Tell the user: "Updating DevSpark from vX.Y.Z → vY.Y.Y. Your `.knowledge/` files will not be touched."

Execute **only** these steps in order, then skip to Step 12 (Verify & Report):

- **Step 4** — Re-fetch all stock prompts into `.devspark/defaults/commands/` (overwrite)
- **Step 5** — Re-fetch all helper templates into `.devspark/templates/` (overwrite)
- **Step 5.5** — Re-fetch all Agent Skill packages into `.devspark/templates/skills/` (overwrite)
- **Step 6** — Re-fetch all scripts into `.devspark/scripts/` (overwrite)
- **Step 7** — Re-create all agent shim files (overwrite — shims are framework files)
- **Step 10** — Update `.devspark/VERSION` with new version and today's date

**Never touch** `.knowledge/`, the constitution, `.gitignore`, or platform guide files (VS Code settings, etc.).

#### Repair Mode

If the installed version matches `LATEST_VERSION` but framework files are missing, tell the user: "DevSpark is already at vX.Y.Z, but the framework install is incomplete. Re-fetching stock files to repair it. Your `.knowledge/` files will not be touched."

Execute **only** these steps in order, then skip to Step 12 (Verify & Report):

- **Step 4** — Re-fetch all stock prompts into `.devspark/defaults/commands/` (overwrite missing or stale copies)
- **Step 5** — Re-fetch all helper templates into `.devspark/templates/` (overwrite missing or stale copies)
- **Step 5.5** — Re-fetch all Agent Skill packages into `.devspark/templates/skills/` (overwrite missing or stale copies)
- **Step 6** — Re-fetch all scripts into `.devspark/scripts/` (overwrite missing or stale copies)
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

> **Live manifest (preferred):** Before fetching individual files, query the GitHub API to get the authoritative command list:
> `https://api.github.com/repos/markhazleton/devspark/contents/templates/commands`
> Use the `name` field of each returned entry (strip `.md` suffix) as the command list. This keeps the install in sync with the latest release automatically. Fall back to the static table below only if the API is unreachable.

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
| `update-pr.md` | `.devspark/defaults/commands/devspark.update-pr.md` |
| `taskstoissues.md` | `.devspark/defaults/commands/devspark.taskstoissues.md` |
| `add-application.md` | `.devspark/defaults/commands/devspark.add-application.md` |
| `list-applications.md` | `.devspark/defaults/commands/devspark.list-applications.md` |
| `validate-registry.md` | `.devspark/defaults/commands/devspark.validate-registry.md` |
| `commit-audit.md` | `.devspark/defaults/commands/devspark.commit-audit.md` |
| `fix-score.md` | `.devspark/defaults/commands/devspark.fix-score.md` |
| `verify.md` | `.devspark/defaults/commands/devspark.verify.md` |

### Step 4 Validation (required)

After fetching, verify every expected command file landed successfully:

```powershell
$expected = Get-ChildItem .devspark/defaults/commands/devspark.*.md -ErrorAction SilentlyContinue
Write-Host "Commands installed: $($expected.Count)"
$expected | ForEach-Object { if (-not (Test-Path $_.FullName)) { Write-Host "MISSING: $_" } }
```

```bash
count=$(ls .devspark/defaults/commands/devspark.*.md 2>/dev/null | wc -l)
echo "Commands installed: $count"
```

If any command file is missing, re-fetch it before continuing.

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
- `vscode-settings.json`

Also fetch every file recursively under these template subdirectories, preserving the same relative paths under `.devspark/templates/`:

- `knowledge/``r`n- `prompts/`
- `risk-checklists/`
- `schemas/`
- `skills/``r`n
Do not fetch `templates/commands/` in this step — Step 4 installs command prompts into `.devspark/defaults/commands/`. Step 5.5 installs `templates/skills/`.

Also fetch `https://raw.githubusercontent.com/markhazleton/devspark/main/agents-registry.json` and save it to `agents-registry.json` at the repository root.

### Step 5 Validation (required)

After fetching, verify each template file is present:

```powershell
@('spec-template.md','plan-template.md','tasks-template.md','quick-spec-template.md',
  'checklist-template.md','agent-file-template.md','command-preamble-contract.md',
  'rationale-template.md','spec-validation-contract.md','README.md','vscode-settings.json') | ForEach-Object {
    if (-not (Test-Path ".devspark/templates/$_")) { Write-Host "MISSING: $_" }
}
```

```bash
for f in spec-template.md plan-template.md tasks-template.md quick-spec-template.md \
         checklist-template.md agent-file-template.md command-preamble-contract.md \
         rationale-template.md spec-validation-contract.md README.md vscode-settings.json; do
  [ -f ".devspark/templates/$f" ] || echo "MISSING: $f"
done
```

If any file is missing, re-fetch it before continuing.

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
- `powershell/harvest.ps1`
- `powershell/platform.ps1`
- `powershell/quickfix-context.ps1`
- `powershell/release-context.ps1`
- `powershell/release-history-context.ps1`
- `powershell/repo-story-context.ps1`
- `powershell/setup-plan.ps1`
- `powershell/site-audit.ps1`
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
- `bash/harvest.sh`
- `bash/platform.sh`
- `bash/quickfix-context.sh`
- `bash/release-context.sh`
- `bash/release-history-context.sh`
- `bash/repo-story-context.sh`
- `bash/setup-plan.sh`
- `bash/site-audit.sh`
- `bash/update-agent-context.sh`

Save to `.devspark/scripts/python/`:

- `python/build_knowledge_index.py`

**Runtime OS selection:** Commands define both `sh` and `ps` script variants. The AI agent selects the appropriate variant at execution time based on the active OS — PowerShell on Windows, Bash on macOS/Linux. Python utility scripts are invoked directly by prompts that need deterministic ontology checks. Because the full script payload is always installed, switching between machines never requires a reinstall.

**Script override layer:** If the team later needs to customize a script (e.g., for Azure DevOps instead of GitHub), they copy the script to `.knowledge/overrides/scripts/{bash|powershell|python}/` and edit it there. The team copy takes priority over the stock version in `.devspark/scripts/`. Upgrades only overwrite `.devspark/scripts/` and never touch `.knowledge/overrides/scripts/`.

### Step 6 Validation (required)

After fetching, verify both shell script directories are populated and the Python ontology utility exists:

```powershell
$ps = (Get-ChildItem .devspark/scripts/powershell/*.ps1 -ErrorAction SilentlyContinue).Count
$sh = (Get-ChildItem .devspark/scripts/bash/*.sh -ErrorAction SilentlyContinue).Count
$pyOntology = Test-Path .devspark/scripts/python/build_knowledge_index.py
Write-Host "PowerShell scripts: $ps  Bash scripts: $sh  Ontology utility: $pyOntology"
if ($ps -eq 0 -or $sh -eq 0 -or -not $pyOntology) { Write-Host "WARNING: part of the script payload is missing — re-fetch before continuing" }
```

```bash
ps=$(ls .devspark/scripts/powershell/*.ps1 2>/dev/null | wc -l | tr -d ' ')
sh=$(ls .devspark/scripts/bash/*.sh 2>/dev/null | wc -l | tr -d ' ')
py="missing"; [ -f .devspark/scripts/python/build_knowledge_index.py ] && py="present"
echo "PowerShell scripts: $ps  Bash scripts: $sh  Ontology utility: $py"
[ "$ps" -eq 0 ] || [ "$sh" -eq 0 ] || [ "$py" = "missing" ] && echo "WARNING: part of the script payload is missing — re-fetch before continuing"
```

If either count is 0 or the Python ontology utility is missing, re-fetch the missing script payload before continuing.

---

## Step 7: Create Copilot Agent Shims

For each command in `.devspark/defaults/commands/devspark.{name}.md`, create two files:

### `.github/agents/devspark.{name}.agent.md`

```markdown
---
name: devspark.{name}
description: DevSpark {name} command shim
---

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

Important frontmatter rule:

- Use valid YAML scalars for `name` and `description`.
- Never emit doubled quotes such as `""devspark.specify""`.
- If you choose to quote values, use one pair only: `"devspark.specify"`.

### `.github/prompts/devspark.{name}.prompt.md`

Create a companion prompt file with the same 3-tier resolution content (without YAML frontmatter).

### Step 7 Validation (required)

After generating shims, verify no malformed doubled-quote frontmatter exists.

PowerShell:

```powershell
Get-ChildItem .github/agents/devspark.*.agent.md -ErrorAction SilentlyContinue |
  Select-String -Pattern '^name:\s*""|^description:\s*""' |
  ForEach-Object { $_.Path + ":" + $_.LineNumber + " -> " + $_.Line }
```

Bash:

```bash
grep -nE '^name:[[:space:]]*""|^description:[[:space:]]*""' .github/agents/devspark.*.agent.md || true
```

If any matches are found, fix those lines to valid YAML and re-run the check until it reports no matches.

---

## Step 8: VS Code Settings

Copy `.devspark/templates/vscode-settings.json` to `.vscode/settings.json`. If the file already exists, merge the `github.copilot` settings into it without overwriting other settings.

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
method: copilot-quickstart
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

Run a final presence check across all installed framework files and output a structured summary.

### 12a — Presence checks (stop and repair if any fail)

- Every stock prompt from Step 4 exists in `.devspark/defaults/commands/`
- Every helper template from Step 5 exists in `.devspark/templates/`
- The selected script set from Step 6 exists under `.devspark/scripts/`
- Agent shim files from Step 7 exist in both `.github/agents/` and `.github/prompts/`
- Shim frontmatter is valid YAML (no doubled-quote defects)
- `.devspark/VERSION` exists and contains a semver version
- `.gitignore` contains the personal-overrides exclusion

If **any** check fails, run Repair Mode before reporting success. Do not tell the user the setup is done if framework files are broken or missing.

### 12b — Output a structured completion banner

Output the following summary (adapt counts and status to what actually ran):

```text
✔ DevSpark {LATEST_VERSION} — {MODE} complete

Mode:          {FRESH INSTALL | UPDATE vX.Y.Z → vY.Y.Y | REPAIR | MIGRATION → FRESH INSTALL}
Script type:   {PowerShell (Windows) | Bash (macOS/Linux)}

Files written:
  • {N} stock prompts   → .devspark/defaults/commands/
  • {N} templates       → .devspark/templates/
  • {N} scripts         → .devspark/scripts/{powershell|bash}/
  • {N} agent shims     → .github/agents/
  • {N} prompt files    → .github/prompts/
  • VERSION stamp       → .devspark/VERSION
  • .gitignore updated

Files preserved (never touched by DevSpark):
  • .knowledge/    — all user artifacts untouched
  {IF migration: • Backup at .specify.old/ (move to .archive/YYYY-MM-DD/<topic>/ once satisfied)}

Validation:
  • Shim frontmatter — {ok | repaired N file(s)}
  • Framework files  — all present
  • VERSION stamp    — {LATEST_VERSION}

Constitution: {seeded fresh | migrated from .specify/ | already existed — not touched}
```

### 12c — Next steps

Tell the user:

```text
Start DevSpark: type @devspark.specify in Copilot Chat.

Recommended entrypoints (DevSpark v2):
  @devspark.run create-spec     — specify → plan → tasks → analyze
  @devspark.run execute-plan    — implement → create-pr → pr-review
  @devspark.run suggest-improvement  — file an improvement against markhazleton/devspark

To upgrade later:
  @workspace Follow the instructions at
  Use this quickstart prompt again in the target repository for install, upgrade, or repair.`r`n
See .knowledge/entities/product-documentation/site/implementation-lifecycle.md for the full walkthrough.
```

Also explain the 3-tier override system in one sentence:
> Personal overrides in `.knowledge/overrides/{git-user}/commands/` take priority over team overrides in `.knowledge/overrides/commands/`, which take priority over stock prompts in `.devspark/defaults/commands/`. Run `@devspark.personalize {command}` to create a personal override.

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
