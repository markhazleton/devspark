# Migration Guide: Old Structure to .documentation/

> This guide helps you migrate an existing Spec Kit project from the old `.specify/` directory structure to the new `.documentation/` structure introduced in v1.0.0.

---

## Quick Start

Choose your preferred method:

| Method | When to Use | Command |
|--------|-------------|---------|
| **Automated Script (Bash)** | Linux/Mac/Git Bash | `bash .documentation/scripts/migrate-to-documentation.sh` |
| **Automated Script (PowerShell)** | Windows PowerShell | `.\.documentation\scripts\migrate-to-documentation.ps1` |
| **Manual Migration** | Want full control | Follow step-by-step guide below |

---

## What Changed?

### Directory Structure Changes

| Old Location | New Location | Description |
|--------------|--------------|-------------|
| `.specify/` | `.documentation/` | Main Spec Kit directory |
| `memory/` | `.documentation/memory/` | Constitution and context files |
| `scripts/` | `.documentation/scripts/` | Helper scripts (bash/powershell) |
| `templates/` | `.documentation/templates/` | Spec/plan/task templates |
| `specs/` | `specs/` | **Unchanged** - Your specifications stay here |

### Why the Change?

The migration from `.specify/` to `.documentation/` was made to:

1. **Distinguish Spec Kit Spark from upstream** - Uses a different directory to avoid conflicts
2. **Clearer semantics** - `.documentation/` better describes what lives there
3. **Consolidate AI output** - All AI agent generated content lives under `.documentation/`
4. **Separate concerns** - Documentation and scripts separate from source code

---

## Automated Migration (Recommended)

### Option 1: Bash Script (Linux/Mac/Git Bash)

```bash
# 1. Ensure you're in your project root
cd /path/to/your/project

# 2. Download the migration script (if not already present)
curl -o migrate.sh https://raw.githubusercontent.com/MarkHazleton/spec-kit/main/.documentation/scripts/migrate-to-documentation.sh

# 3. Make it executable
chmod +x migrate.sh

# 4. Run the migration
bash migrate.sh

# 5. Review changes
git status
git diff

# 6. Commit if everything looks good
git add -A
git commit -m "chore: migrate to .documentation/ structure"
```

### Option 2: PowerShell Script (Windows)

```powershell
# 1. Ensure you're in your project root
cd C:\path\to\your\project

# 2. Download the migration script (if not already present)
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/MarkHazleton/spec-kit/main/.documentation/scripts/migrate-to-documentation.ps1" -OutFile "migrate.ps1"

# 3. Run the migration
.\migrate.ps1

# 4. Review changes
git status
git diff

# 5. Commit if everything looks good
git add -A
git commit -m "chore: migrate to .documentation/ structure"
```

### What the Automated Scripts Do

1. **Detect old structure** - Checks if `.specify/`, `memory/`, `scripts/`, or `templates/` exist
2. **Create `.documentation/`** - Sets up the new directory structure
3. **Move files** - Migrates all files to new locations
4. **Update references** - Fixes path references in:
   - Agent command files (`.claude/`, `.github/`, etc.)
   - Script files
   - Configuration files (VS Code settings, etc.)
   - Documentation files
5. **Preserve git history** - Uses `git mv` when possible to maintain history
6. **Backup old structure** - Renames old directories to `.old-*` (can be deleted after verification)
7. **Generate summary report** - Shows what was moved and changed

---

## Manual Migration (Step-by-Step)

If you prefer manual control or the automated scripts don't work for your setup:

### Step 1: Create New Directory Structure

```bash
# Create the new .documentation directory
mkdir -p .documentation/{memory,scripts,templates}
```

### Step 2: Move Files

#### If you have `.specify/` directory:

```bash
# Move all contents from .specify/ to .documentation/
if [ -d ".specify" ]; then
  cp -r .specify/* .documentation/
  mv .specify .specify.old
fi
```

#### If you have top-level `memory/`, `scripts/`, `templates/`:

```bash
# Move memory/
if [ -d "memory" ]; then
  cp -r memory/* .documentation/memory/
  mv memory memory.old
fi

# Move scripts/
if [ -d "scripts" ]; then
  cp -r scripts/* .documentation/scripts/
  mv scripts scripts.old
fi

# Move templates/
if [ -d "templates" ]; then
  cp -r templates/* .documentation/templates/
  mv templates templates.old
fi
```

### Step 3: Update References in Files

You need to update path references in several types of files:

#### Agent Command Files

Find and replace in all agent command files:

```bash
# Examples of paths that need updating:
.specify/ → .documentation/
/memory/ → /.documentation/memory/
/scripts/ → /.documentation/scripts/
/templates/ → /.documentation/templates/
```

**Files to check:**
- `.claude/commands/*.md`
- `.github/agents/*.md`
- `.cursor/commands/*.md`
- `.windsurf/workflows/*.md`
- `.gemini/commands/*.toml`
- `.qwen/commands/*.toml`
- Any other agent-specific directories

#### Script Files

Update references in:
- `.documentation/scripts/bash/*.sh`
- `.documentation/scripts/powershell/*.ps1`

#### VS Code Settings

If you have `.vscode/settings.json`, update:

```json
{
  "files.exclude": {
    ".documentation/": true  // Was ".specify/"
  }
}
```

#### Documentation Files

Update references in:
- `README.md`
- `.documentation/*.md`
- Any other documentation

### Step 4: Test the Migration

```bash
# 1. Try running a slash command
# Example: /speckit.constitution

# 2. Verify scripts work
bash .documentation/scripts/bash/setup-plan.sh

# 3. Check templates are accessible
ls -la .documentation/templates/

# 4. Verify constitution loads
cat .documentation/memory/constitution.md
```

### Step 5: Clean Up Old Directories

After verifying everything works:

```bash
# Remove old directories (be careful!)
rm -rf .specify.old
rm -rf memory.old
rm -rf scripts.old
rm -rf templates.old
```

### Step 6: Commit Changes

```bash
git add -A
git commit -m "chore: migrate to .documentation/ structure

- Moved .specify/ to .documentation/
- Moved memory/, scripts/, templates/ to .documentation/
- Updated all path references in commands and scripts
- Preserves specs/ directory unchanged
"
```

---

## Path Update Patterns

When updating references, use these patterns:

### Bash/Shell Scripts

```bash
# Old patterns
MEMORY_DIR="memory"
SCRIPTS_DIR="scripts"
TEMPLATES_DIR="templates"
SPECIFY_DIR=".specify"

# New patterns
MEMORY_DIR=".documentation/memory"
SCRIPTS_DIR=".documentation/scripts"
TEMPLATES_DIR=".documentation/templates"
SPECIFY_DIR=".documentation"
```

### PowerShell Scripts

```powershell
# Old patterns
$MemoryDir = "memory"
$ScriptsDir = "scripts"
$TemplatesDir = "templates"

# New patterns
$MemoryDir = ".documentation/memory"
$ScriptsDir = ".documentation/scripts"
$TemplatesDir = ".documentation/templates"
```

### Markdown Command Files

```markdown
# Old patterns
`bash scripts/bash/setup-plan.sh`
Read the constitution in `memory/constitution.md`
Use the template in `templates/spec-template.md`

# New patterns
`bash .documentation/scripts/bash/setup-plan.sh`
Read the constitution in `.documentation/memory/constitution.md`
Use the template in `.documentation/templates/spec-template.md`
```

### TOML Command Files

```toml
# Old patterns
{SCRIPT} = "/scripts/bash/setup-plan.sh"

# New patterns
{SCRIPT} = "/.documentation/scripts/bash/setup-plan.sh"
```

---

## Troubleshooting

### "Migration script not found"

The migration scripts are included in Spec Kit v1.0.0+. If you don't have them:

1. **Download from GitHub:**
   ```bash
   curl -o migrate.sh https://raw.githubusercontent.com/MarkHazleton/spec-kit/main/.documentation/scripts/migrate-to-documentation.sh
   ```

2. **Or upgrade your Spec Kit installation:**
   ```bash
   specify init --here --force --ai <your-agent>
   ```

### "Slash commands not working after migration"

1. **Restart your IDE/editor completely**
2. **Verify command files updated:**
   ```bash
   grep -r "\.specify" .claude/commands/  # Should return nothing
   grep -r "/memory/" .claude/commands/   # Should return nothing
   ```
3. **Re-run the migration script** if some references were missed

### "Scripts returning 'file not found' errors"

Check that script paths were updated:

```bash
# Search for old path patterns
grep -r "scripts/bash" .
grep -r "scripts/powershell" .

# Should all point to .documentation/scripts/ instead
```

### "Git history lost for some files"

If you used `cp` instead of `git mv`, history may not be preserved. To fix:

```bash
# Git can often detect renames after the fact
git log --follow .documentation/memory/constitution.md

# If not detected, you can't recover history without re-doing migration with git mv
```

### "Old directories still exist"

The migration script renames them with `.old` suffix for safety. After verifying everything works:

```bash
rm -rf .specify.old memory.old scripts.old templates.old
```

---

## Verification Checklist

After migration, verify:

- [ ] `.documentation/` directory exists and contains `memory/`, `scripts/`, `templates/`
- [ ] `specs/` directory unchanged (your specifications intact)
- [ ] Constitution file at `.documentation/memory/constitution.md`
- [ ] Scripts at `.documentation/scripts/bash/` and `.documentation/scripts/powershell/`
- [ ] Templates at `.documentation/templates/`
- [ ] Agent command files updated (no references to old paths)
- [ ] Slash commands work in your AI assistant
- [ ] Scripts execute successfully
- [ ] No `memory/`, `scripts/`, `templates/`, `.specify/` directories in project root
- [ ] Git status shows changes ready to commit

---

## FAQ

### Do I need to migrate?

**Yes, if you want the latest features.** Spec Kit v1.0.0+ uses `.documentation/` exclusively. Old versions using `.specify/` or root-level directories are deprecated.

### Will my specs be affected?

**No.** The `specs/` directory is never touched during migration. Your specifications, plans, and tasks are completely safe.

### Can I migrate mid-project?

**Yes.** You can migrate at any time. Your active feature specs won't be affected. However, it's recommended to:
1. Commit any pending work first
2. Run migration on a clean working tree
3. Test thoroughly before continuing development

### What if I have custom scripts?

The migration will move them to `.documentation/scripts/`. You'll need to update any references to those scripts:

```bash
# Old
./scripts/my-custom-script.sh

# New
./.documentation/scripts/my-custom-script.sh
```

### Can I keep both structures during transition?

**Not recommended.** Having both will cause confusion. The automated scripts and manual guide both move (not copy) files to ensure single source of truth.

### What about `.gitignore`?

Update your `.gitignore` to reference new paths:

```diff
- .specify/
+ .documentation/

# If you ignored specific subdirectories:
- memory/
- scripts/
- templates/
+ .documentation/memory/
+ .documentation/scripts/
+ .documentation/templates/
```

However, typically `.documentation/` should be committed to git (except for `_site/` build output).

---

## Next Steps

After successful migration:

1. **Upgrade to latest Spec Kit:**
   ```bash
   uv tool install specify-cli --force --from git+https://github.com/MarkHazleton/spec-kit.git
   ```

2. **Update project files:**
   ```bash
   specify init --here --force --ai <your-agent>
   ```

3. **Review new features:**
   - [Upgrade Guide](.documentation/upgrade.md)
   - [ASLCD Toolkit](.documentation/adaptive-lifecycle.md)
   - [Roadmap](.documentation/roadmap.md)

---

## Support

If you encounter issues during migration:

- **GitHub Issues:** [github.com/MarkHazleton/spec-kit/issues](https://github.com/MarkHazleton/spec-kit/issues)
- **Discussions:** [github.com/MarkHazleton/spec-kit/discussions](https://github.com/MarkHazleton/spec-kit/discussions)
- **Documentation:** [markhazleton.github.io/spec-kit/](https://markhazleton.github.io/spec-kit/)

---

*Last updated: 2026-02-08*
