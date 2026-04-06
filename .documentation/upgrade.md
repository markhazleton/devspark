# Upgrade Guide

> You have DevSpark installed and want to upgrade to the latest version to get new features, bug fixes, or updated slash commands. The normal path is the remote upgrade prompt in your AI chat. CLI is optional and intended for advanced workflows.

---

## Quick Reference

| What to Upgrade | Command | When to Use |
|----------------|---------|-------------|
| **Project Files (Prompt-First, Recommended)** | Use remote prompt URL: `https://raw.githubusercontent.com/markhazleton/devspark/main/templates/commands/upgrade.md` | Normal upgrade path from AI chat with no CLI install |
| **CLI Tool Only** | `uv tool install devspark-cli --force --from git+https://github.com/MarkHazleton/devspark.git` | Get latest CLI features without touching project files |
| **Project Files (CLI, Advanced)** | `devspark upgrade` | Terminal-driven upgrade for teams that want local automation |
| **Project Files** (Manual) | `devspark init --here --force --ai <your-agent>` | Update when you want to override agent selection |
| **Both** | Run CLI upgrade, then `devspark upgrade` | Recommended for major version updates |

---

## Part 0: Prompt-First Upgrade (Recommended)

Run upgrade directly from AI chat without installing CLI tooling.

1. Open your AI agent chat in the target repository.
1. Paste this URL and ask the agent to follow it:

```text
https://raw.githubusercontent.com/markhazleton/devspark/main/templates/commands/upgrade.md
```

1. Ask for a dry run first, then apply changes.

This is the simplest path and mirrors quickstart installation style.

---

## Part 1: Upgrade the CLI Tool (Advanced)

The CLI tool (`devspark`) is separate from your project files. Upgrade it to get the latest features and bug fixes.

### If you installed with `uv tool install`

```bash
uv tool install devspark-cli --force --from git+https://github.com/MarkHazleton/devspark.git
```

### If you use one-shot `uvx` commands

No upgrade needed—`uvx` always fetches the latest version. Just run your commands as normal:

```bash
uvx --from git+https://github.com/MarkHazleton/devspark.git devspark upgrade
```

### Verify the upgrade

```bash
devspark version
```

This shows CLI and template versions plus system information.

---

## Part 2: Updating Project Files with CLI (Advanced)

Use the `devspark upgrade` command only if you prefer terminal-driven automation or need to script upgrades locally.

### Simple Upgrade

```bash
cd /path/to/your-project
devspark upgrade
```

**What it does:**

1. ✅ Verifies you're in a DevSpark project
2. ✅ Checks for uncommitted git changes
3. ✅ Auto-detects your AI assistant (claude, copilot, etc.)
4. ✅ Detects old structure (.specify/, memory/) and offers to migrate
5. ✅ Downloads and applies latest templates
6. ✅ Preserves your specs/ and constitution

### Upgrade Options

```bash
# Preview changes without modifying files
devspark upgrade --dry-run

# Override auto-detected agent
devspark upgrade --ai claude

# Create backup of constitution before upgrade
devspark upgrade --backup

# Skip automatic migration check
devspark upgrade --skip-migration

# Skip all confirmations
devspark upgrade --force
```

### What gets updated?

The upgrade command updates:

- ✅ **Slash command files** (`.claude/commands/`, `.github/agents/`, etc.)
- ✅ **Script files** (`.documentation/scripts/`)
- ✅ **Template files** (`.documentation/templates/`)
- ✅ **Shared memory files** (`.documentation/memory/`) - **⚠️ See warnings below**

### What stays safe?

These files are **never touched** by the upgrade:

- ✅ **Your specifications** (`specs/`) - **COMPLETELY SAFE**
- ✅ **Your implementation plans** (`specs/*/plan.md`, `tasks.md`, etc.) - **SAFE**
- ✅ **Your source code** - **SAFE**
- ✅ **Your git history** - **SAFE**
- ✅ **Your custom scripts** (preserved in .documentation/scripts/)

The `specs/` directory is completely excluded from upgrades and will never be modified.

---

## Part 3: Alternative Method (Manual CLI Update)

If you prefer manual control or the `upgrade` command isn't available, you can update project files directly:

```bash
devspark init --here --force --ai <your-agent>
```

Replace `<your-agent>` with your AI assistant. Refer to the list of [Supported AI Agents](https://github.com/MarkHazleton/devspark#-supported-ai-agents)

**Example:**

```bash
devspark init --here --force --ai copilot
```

### Understanding the `--force` flag

Without `--force`, the CLI warns you and asks for confirmation:

```text
Warning: Current directory is not empty (25 items)
Template files will be merged with existing content and may overwrite existing files
Proceed? [y/N]
```

With `--force`, it skips the confirmation and proceeds immediately.

**Important: Your `specs/` directory is always safe.** The `--force` flag only affects template files (commands, scripts, templates, memory). Your feature specifications, plans, and tasks in `specs/` are never included in upgrade packages and cannot be overwritten.

---

## ⚠️ Important Warnings

### 1. Constitution file may be overwritten

**Recommendation:** Use the `--backup` flag when upgrading to automatically backup your constitution:

```bash
devspark upgrade --backup
```

This creates a timestamped backup at `.documentation/memory/constitution.md.YYYYMMDD_HHMMSS.bak`.

**Manual backup alternative:**

```bash
# 1. Back up your constitution before upgrading
cp .documentation/memory/constitution.md .documentation/memory/constitution-backup.md

# 2. Run the upgrade
devspark upgrade

# 3. If needed, restore your customized constitution
mv .documentation/memory/constitution-backup.md .documentation/memory/constitution.md
```

Or use git to restore it after upgrade:

```bash
# After upgrade, restore from git history if overwritten
git restore .documentation/memory/constitution.md
```

### 2. Custom template modifications

If you customized any templates in `.documentation/templates/`, the upgrade will overwrite them. Back them up first:

```bash
# Back up custom templates
cp -r .documentation/templates .documentation/templates-backup

# Run upgrade
devspark upgrade

# After upgrade, merge your changes back manually
```

### 3. Duplicate slash commands (IDE-based agents)

Some IDE-based agents (like Kilo Code, Windsurf) may show **duplicate slash commands** after upgrading—both old and new versions appear.

**Solution:** Manually delete the old command files from your agent's folder.

**Example for Kilo Code:**

```bash
# Navigate to the agent's commands folder
cd .kilocode/rules/

# List files and identify duplicates
ls -la

# Delete old versions (example filenames - yours may differ)
rm devspark.specify-old.md
rm devspark.plan-v1.md
```

Restart your IDE to refresh the command list.

---

## Common Scenarios

### Scenario 1: "I just want new slash commands"

Run the remote upgrade prompt in your AI chat:

```text
Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/templates/commands/upgrade.md
```

If you use the advanced CLI workflow, run `devspark upgrade` instead.

### Scenario 2: "I customized templates and constitution"

```bash
# 1. Back up customizations
cp .documentation/memory/constitution.md /tmp/constitution-backup.md
cp -r .documentation/templates /tmp/templates-backup

# 2. Apply upgrade
# Preferred: run the remote upgrade prompt from AI chat
# Advanced option: devspark upgrade

# 3. Restore customizations
mv /tmp/constitution-backup.md .documentation/memory/constitution.md
# Manually merge template changes if needed
```

### Scenario 3: "I see duplicate slash commands in my IDE"

This happens with IDE-based agents (Kilo Code, Windsurf, Roo Code, etc.).

```bash
# Find the agent folder (example: .kilocode/rules/)
cd .kilocode/rules/

# List all files
ls -la

# Delete old command files
rm devspark.old-command-name.md

# Restart your IDE
```

### Scenario 4: "I'm working on a project without Git"

If you initialized your project with `--no-git`, you can still upgrade:

```bash
# Manually back up files you customized
cp .documentation/memory/constitution.md /tmp/constitution-backup.md

# Preferred: run the remote upgrade prompt from AI chat
# Advanced option: devspark upgrade

# Restore customizations
mv /tmp/constitution-backup.md .documentation/memory/constitution.md
```

The `--no-git` flag skips git initialization but doesn't affect file updates.

---

## Using `--no-git` Flag

The `--no-git` flag tells DevSpark to **skip git repository initialization**. This is useful when:

- You manage version control differently (Mercurial, SVN, etc.)
- Your project is part of a larger monorepo with existing git setup
- You're experimenting and don't want version control yet

**During initial setup:**

```bash
devspark init my-project --ai copilot --no-git
```

**During upgrade:**

```bash
devspark init --here --force --ai copilot --no-git
```

### What `--no-git` does NOT do

❌ Does NOT prevent file updates
❌ Does NOT skip slash command installation
❌ Does NOT affect template merging

It **only** skips running `git init` and creating the initial commit.

### Working without Git

If you use `--no-git`, you'll need to manage feature directories manually:

**Set the `DEVSPARK_FEATURE` environment variable** before using planning commands:

```bash
# Bash/Zsh
export DEVSPARK_FEATURE="001-my-feature"

# PowerShell
$env:DEVSPARK_FEATURE = "001-my-feature"
```

This tells DevSpark which feature directory to use when creating specs, plans, and tasks.

**Why this matters:** Without git, DevSpark can't detect your current branch name to determine the active feature. The environment variable provides that context manually.

---

## Troubleshooting

### "Slash commands not showing up after upgrade"

**Cause:** Agent didn't reload the command files.

**Fix:**

1. **Restart your IDE/editor** completely (not just reload window)
2. **For CLI-based agents**, verify files exist:

   ```bash
   ls -la .claude/commands/      # Claude Code
   ls -la .gemini/commands/       # Gemini
   ls -la .cursor/commands/       # Cursor
   ```

3. **Check agent-specific setup:**
   - Codex requires `CODEX_HOME` environment variable
   - Some agents need workspace restart or cache clearing

### "I lost my constitution customizations"

**Fix:** Restore from git or backup:

```bash
# If you committed before upgrading
git restore .documentation/memory/constitution.md

# If you backed up manually
cp /tmp/constitution-backup.md .documentation/memory/constitution.md
```

**Prevention:** Always commit or back up `constitution.md` before upgrading.

### "Warning: Current directory is not empty"

**Full warning message:**

```text
Warning: Current directory is not empty (25 items)
Template files will be merged with existing content and may overwrite existing files
Do you want to continue? [y/N]
```

**What this means:**

This warning appears when you run the advanced CLI setup path with `devspark init --here` (or `devspark init .`) in a directory that already has files. It's telling you:

1. **The directory has existing content** - In the example, 25 files/folders
2. **Files will be merged** - New template files will be added alongside your existing files
3. **Some files may be overwritten** - If you already have DevSpark files (`.claude/`, `.documentation/`, etc.), they'll be replaced with the new versions

**What gets overwritten:**

Only DevSpark infrastructure files:

- Agent command files (`.claude/commands/`, `.github/prompts/`, etc.)
- Scripts in `.documentation/scripts/`
- Templates in `.documentation/templates/`
- Memory files in `.documentation/memory/` (including constitution)

**What stays untouched:**

- Your `specs/` directory (specifications, plans, tasks)
- Your source code files
- Your `.git/` directory and git history
- Any other files not part of DevSpark templates

**How to respond:**

- **Type `y` and press Enter** - Proceed with the merge (recommended if upgrading)
- **Type `n` and press Enter** - Cancel the operation
- **Use `--force` flag** - Skip this confirmation entirely:

  ```bash
  devspark init --here --force --ai copilot
  ```

**When you see this warning:**

- ✅ **Expected** when upgrading an existing DevSpark project
- ✅ **Expected** when adding DevSpark to an existing codebase
- ⚠️ **Unexpected** if you thought you were creating a new project in an empty directory

**Prevention tip:** Before upgrading, commit or back up your `.documentation/memory/constitution.md` if you customized it.

### "Advanced CLI upgrade doesn't seem to work"

Verify the installation:

```bash
# Check installed tools
uv tool list

# Should show devspark-cli

# Verify path
which devspark

# Should point to the uv tool installation directory
```

If not found, reinstall:

```bash
uv tool uninstall devspark-cli
uv tool install devspark-cli --from git+https://github.com/MarkHazleton/devspark.git
```

### "Do I need to run devspark every time I open my project?"

**Short answer:** No. For normal use, you bootstrap once with the remote quickstart prompt and update later with the remote upgrade prompt. If you use the advanced CLI path, you only run `devspark init` once per project.

**Explanation:**

The advanced `devspark` CLI tool is used for:

- **Initial setup:** `devspark init` to bootstrap DevSpark in your project
- **Upgrades:** `devspark upgrade` to refresh stock framework files
- **Diagnostics:** `devspark check` to verify tool installation

Once DevSpark has been installed, the slash commands (like `/devspark.specify`, `/devspark.plan`, etc.) are available from your project's agent folders and stock prompt files. Your AI assistant reads those command files directly — no need to keep running CLI for normal use.

**If your agent isn't recognizing slash commands:**

1. **Verify command files exist:**

   ```bash
   # For GitHub Copilot
   ls -la .github/prompts/

   # For Claude
   ls -la .claude/commands/
   ```

2. **Restart your IDE/editor completely** (not just reload window)

3. **Check you're in the correct directory** where DevSpark was installed

4. **For some agents**, you may need to reload the workspace or clear cache

**Related issue:** If Copilot can't open local files or uses PowerShell commands unexpectedly, this is typically an IDE context issue, not related to `devspark`. Try:

- Restarting VS Code
- Checking file permissions
- Ensuring the workspace folder is properly opened

---

## Version Compatibility

DevSpark follows semantic versioning for major releases. The CLI and project files are designed to be compatible within the same major version.

**Best practice:** Keep project files current with the remote upgrade prompt. Only keep CLI in sync as well if your team intentionally uses the advanced CLI workflow.

---

## Next Steps

After upgrading:

- **Test new slash commands:** Run `/devspark.constitution` or another command to verify everything works
- **Review release notes:** Check [GitHub Releases](https://github.com/MarkHazleton/devspark/releases) for new features and breaking changes
- **Update workflows:** If new commands were added, update your team's development workflows
- **Check documentation:** Visit [github.io/devspark](https://github.github.io/devspark/) for updated guides
