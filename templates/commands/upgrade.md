---
description: Check the installed DevSpark version, identify stale framework files, and guide a safe upgrade to the latest release
---

<!-- markdownlint-disable MD040 -->

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). Supported options:

| Option | Description |
|--------|-------------|
| `--dry-run` | Show what would change without modifying files |
| `--backup` | Backup `constitution.md` before upgrading |
| `--force` | Skip confirmations |

---

## Overview

This command checks whether the consumer project's installed DevSpark matches the
latest available version and guides you through a safe upgrade. It:

1. Reads `.documentation/DEVSPARK_VERSION` to find the installed version
2. Detects the latest version from `CHANGELOG.md` or `pyproject.toml`
3. Classifies files under `.documentation/` as framework-owned vs. user-owned
4. Identifies stale or missing framework files
5. Runs `devspark upgrade` (or `devspark init --here --force`) to apply updates
6. Verifies the stamp file was updated after the upgrade

---

## Outline

### 1. Read Installed Version

Check for `.documentation/DEVSPARK_VERSION`:

```text
.documentation/DEVSPARK_VERSION
```

Expected format (three lines):

```
<version>
installed: <YYYY-MM-DD>
agent: <agent-key>
```

**If the file is missing:**

- Report: `DEVSPARK_VERSION not found — version unknown`
- The project was installed before v1.2.4 or the stamp was not written
- Proceed to Step 2 to determine what version is actually present

**If the file exists**, extract:

- `INSTALLED_VERSION` — e.g., `1.1.0`
- `INSTALL_DATE` — e.g., `2026-02-08`
- `INSTALLED_AGENT` — e.g., `copilot`

### 2. Detect Latest Available Version

Read `CHANGELOG.md` at the repo root (or `.documentation/CHANGELOG.md`):

- Find the most recent `## [X.Y.Z]` heading
- That is `LATEST_VERSION`

Fallback: read `pyproject.toml` `version = "..."` if CHANGELOG is absent.

### 3. Compare Versions

| Condition | Status |
|-----------|--------|
| `INSTALLED_VERSION == LATEST_VERSION` | Up to date |
| `INSTALLED_VERSION < LATEST_VERSION` | Upgrade available |
| `DEVSPARK_VERSION` absent | Unknown — treat as upgrade needed |

Display the comparison result clearly:

```
Installed : 1.1.0  (2026-02-08, agent: copilot)
Latest    : 1.2.4
Status    : UPGRADE AVAILABLE
```

If up to date, skip to Step 6 (Verify Files).

### 4. Classify Files Under `.documentation/`

Separate framework-owned files (overwritten on upgrade) from user-owned files (never
touched). Use this classification:

#### Framework-owned (safe to overwrite)

These come from the DevSpark release package and should match the latest version:

- `.documentation/scripts/bash/*.sh`
- `.documentation/scripts/powershell/*.ps1`
- `.documentation/templates/`
- `.documentation/DEVSPARK_VERSION`
- `.documentation/README.md`
- `.documentation/index.md`
- `.documentation/upgrade.md`
- `.documentation/migration-guide.md`
- `.documentation/MIGRATION-QUICKREF.md`
- Agent command files:
  - `.github/agents/*.agent.md`
  - `.github/prompts/*.prompt.md`
  - `.claude/commands/devspark.*.md`
  - `.cursor/commands/devspark.*.md`
  - `.windsurf/workflows/devspark.*.md`
  - *(and equivalents for other supported agents)*

#### User-owned (NEVER overwritten)

These are written by the project team and must be preserved:

- `.documentation/specs/` — all feature specifications, plans, and tasks
- `.documentation/memory/constitution.md` — project constitution
- `.documentation/copilot/` — session artifacts and audit history
- `.documentation/decisions/` — ADRs
- `.documentation/releases/` — release archives
- `.documentation/quickfixes/` — active quickfixes
- `CHANGELOG.md` (repo root)
- Any file not listed in the framework-owned category

### 5. Identify Stale Files

Scan for signs that the install is outdated. Flag any of the following:

| Check | Issue | Severity |
|-------|-------|----------|
| `.documentation/DEVSPARK_VERSION` absent | No version stamp | HIGH |
| Agent command files reference old paths (`.specify/`, root `memory/`, `scripts/`, `templates/`, or `specs/`) | Pre-migration paths | HIGH |
| `.specify/` directory exists | Pre-v1.0 structure | HIGH |
| Root-level `memory/`, `scripts/`, `templates/`, or `specs/` directories exist | Pre-v1.0 structure | HIGH |
| `DEVSPARK_VERSION` present but older than `LATEST_VERSION` | Out of date | MEDIUM |
| Old `devspark.*-old.md` command files in agent folder | Leftover duplicates | LOW |

Report findings before proceeding.

### 6. Verify Framework Files (even if up to date)

Even when the version matches, check that all expected framework files are present.
List any that are **missing** from the expected locations.

Missing framework files should be reported as:

```
MISSING: .documentation/scripts/powershell/setup-plan.ps1
MISSING: .github/agents/devspark.specify.agent.md
```

### 7. Perform the Upgrade

**If `--dry-run`**: Display the full plan and stop. Do not modify files.

**Otherwise:**

#### 7a. Backup constitution (if `--backup` or constitution has been customized)

Check if `constitution.md` differs from a template default — if the user has made
substantial edits, recommend backing up:

```bash
cp .documentation/memory/constitution.md \
   .documentation/memory/constitution.md.YYYYMMDD.bak
```

Or instruct the user to run:

```bash
devspark upgrade --backup
```

#### 7b. Run the CLI upgrade

Prefer `devspark upgrade` (v1.1.0+). Fall back to `devspark init --here --force --ai <INSTALLED_AGENT>` if needed.

**Check for CLI availability:**

```bash
devspark version
```

If available, run:

```bash
devspark upgrade --ai <INSTALLED_AGENT>
```

If not installed, provide the install command:

```bash
uv tool install devspark-cli --force \
  --from git+https://github.com/MarkHazleton/spec-kit.git
```

#### 7c. Handle old structure migration

If stale paths were found in Step 5 (`.specify/`, root `memory/` etc.):

```bash
# Windows
.\.documentation\scripts\powershell\migrate-to-documentation.ps1

# Linux/Mac
bash .documentation/scripts/bash/migrate-to-documentation.sh
```

Or ask the user to approve: "Migration detected. Run migration script now? [y/N]"

### 8. Post-Upgrade Verification

After the upgrade completes:

1. **Read `.documentation/DEVSPARK_VERSION` again** — confirm version changed to `LATEST_VERSION`
2. **Check agent command files** — confirm they no longer reference old paths
3. **Confirm `.documentation/specs/` is untouched** — user data must be preserved
4. **Confirm `constitution.md` is intact** (or restored from backup)

Report a post-upgrade summary:

```
Post-Upgrade Verification
  DEVSPARK_VERSION : 1.2.4  (was 1.1.0)
  Agent commands  : updated
  .documentation/specs/ : unchanged
  constitution.md : preserved
```

### 9. Output Final Summary

#### Upgrade performed

```
DevSpark Upgrade Summary
  Previous Version : <INSTALLED_VERSION>
  New Version      : <LATEST_VERSION>
  Agent            : <INSTALLED_AGENT>
  Date             : <TODAY>

Framework files updated. User files preserved.

Next steps:
  1. git diff — review changes
  2. Test /devspark.constitution in your AI assistant
  3. git add -A && git commit -m "chore: upgrade devspark to vX.Y.Z"
```

#### Already up to date

```
DevSpark is up to date.
  Version : <INSTALLED_VERSION>
  Agent   : <INSTALLED_AGENT>
  Date    : <INSTALL_DATE>
```

#### Dry run

```
Dry Run — No changes made.

Would upgrade: <INSTALLED_VERSION> -> <LATEST_VERSION>
Framework files to update: <N>
User files preserved: .documentation/specs/, constitution.md, session artifacts

To apply:
  devspark upgrade --ai <INSTALLED_AGENT>
```

---

## Guidelines

### User Data is Sacred

Never modify or delete:

- `.documentation/specs/` and all contents
- `constitution.md`
- `.documentation/copilot/`
- `.documentation/decisions/`
- `.documentation/releases/`
- Any file the user created that is not a DevSpark framework file

### Non-Destructive by Default

Always check before replacing framework files. If `--dry-run` is specified,
produce only the plan — never modify files.

### Version Stamp is Authoritative

`.documentation/DEVSPARK_VERSION` is the single source of truth for the installed
version in a consumer project. After any successful upgrade, verify the stamp was
updated. If the stamp is absent after an upgrade, warn the user and suggest
re-running `devspark upgrade`.

### Constitution Backup Recommendation

If `constitution.md` has been customized (differs from the template default), always
recommend a backup before upgrading — even if `--backup` was not specified.

## Context

$ARGUMENTS
