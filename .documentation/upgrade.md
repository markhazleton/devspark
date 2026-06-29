# Upgrade Guide

## Current Release

[![Current Release](https://img.shields.io/github/v/release/markhazleton/devspark?label=current%20release)](https://github.com/markhazleton/devspark/releases/latest)

---

## Prompt-First Upgrade (Recommended)

1. Open your AI agent chat in the target repository.
1. Paste this command:

   ```text
   Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/templates/commands/upgrade.md
   ```

1. Ask for a dry run first, then apply changes.

No CLI required. This is the standard upgrade path.

---

## CLI Upgrade (Advanced)

Use the CLI only if you prefer terminal-driven automation.

### Update the CLI tool

```bash
uv tool install devspark-cli --force --from git+https://github.com/MarkHazleton/devspark.git
```

If you use `uvx`, no CLI upgrade is needed -- it always fetches the latest.

### Update project files

```bash
cd /path/to/your-project
devspark upgrade
```

### CLI options

| Flag | Effect |
|------|--------|
| `--dry-run` | Preview changes without modifying files |
| `--ai claude` | Override auto-detected agent |
| `--skip-migration` | Skip legacy structure migration check |
| `--force` | Skip all confirmations |

---

## What Gets Updated vs. What's Safe

| Updated (framework files) | Never touched (your work) |
|---------------------------|---------------------------|
| `.devspark/defaults/commands/` | `.documentation/memory/constitution.md` |
| `.devspark/scripts/` | `.documentation/specs/` |
| `.devspark/templates/` | `.documentation/commands/` |
| Agent shim files (`.claude/commands/`, `.github/agents/`, etc.) | `.documentation/scripts/` |
| `.devspark/VERSION` | Source code, git history |

If you keep overrides in `.documentation/commands/`, review any upgraded stock prompt that changed its contract, especially route-aware or frontmatter-driven commands such as `/devspark.specify`, `/devspark.plan`, `/devspark.tasks`, `/devspark.implement`, and `/devspark.create-pr`.

If upgrade needs to migrate legacy `.specify/` or root-level support directories, existing files already under `.documentation/` win. DevSpark preserves the legacy copies in `.old/` backups and reports the skipped files instead of overwriting current repo-owned work.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Commands missing after upgrade | Restart your IDE/editor completely (not just reload window) |
| Duplicate slash commands in IDE | Delete old files from agent folder (e.g., `.kilocode/rules/`), restart IDE |
| Constitution missing | Upgrades never touch it. Create one with `/devspark.constitution` or restore with `git restore .documentation/memory/constitution.md` |
| CLI not found after install | Run `uv tool list` to verify, reinstall with `uv tool install devspark-cli --from git+https://github.com/MarkHazleton/devspark.git` |
| "Current directory is not empty" warning | Expected when upgrading. Type `y` to proceed, or use `--force` to skip. Your constitution, specs, and team commands are never overwritten. |

---

## Using `--no-git`

If your project doesn't use Git, set the `DEVSPARK_FEATURE` environment variable before planning commands:

```bash
# Bash/Zsh
export DEVSPARK_FEATURE="001-my-feature"

# PowerShell
$env:DEVSPARK_FEATURE = "001-my-feature"
```

Without Git, DevSpark can't detect your branch name to determine the active feature. The environment variable provides that context.
