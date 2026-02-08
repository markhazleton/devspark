# Migration Quick Reference

**Migrating from old Spec Kit structure to .documentation/**

---

## One-Line Migration

### Bash (Linux/Mac/Git Bash)
```bash
curl -sSL https://raw.githubusercontent.com/MarkHazleton/spec-kit/main/.documentation/scripts/migrate-to-documentation.sh | bash
```

### PowerShell (Windows)
```powershell
iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/MarkHazleton/spec-kit/main/.documentation/scripts/migrate-to-documentation.ps1'))
```

---

## What Gets Migrated

| Old Location | New Location |
|--------------|--------------|
| `.specify/` | `.documentation/` |
| `memory/` | `.documentation/memory/` |
| `scripts/` | `.documentation/scripts/` |
| `templates/` | `.documentation/templates/` |
| `specs/` | `specs/` (unchanged) |

---

## Manual Migration (If Scripts Fail)

### 1. Create Structure
```bash
mkdir -p .documentation/{memory,scripts,templates}
```

### 2. Move Files
```bash
# If you have .specify/
cp -r .specify/* .documentation/ && mv .specify .specify.old

# If you have root-level directories
cp -r memory/* .documentation/memory/ && mv memory memory.old
cp -r scripts/* .documentation/scripts/ && mv scripts scripts.old
cp -r templates/* .documentation/templates/ && mv templates templates.old
```

### 3. Find & Replace
Search and replace in all files:
- `.specify/` → `.documentation/`
- `/memory/` → `/.documentation/memory/`
- `/scripts/` → `/.documentation/scripts/`
- `/templates/` → `/.documentation/templates/`

### 4. Update These Files
- [ ] `.claude/commands/*.md`
- [ ] `.github/agents/*.md` (or `.github/prompts/*.md`)
- [ ] `.cursor/commands/*.md`
- [ ] `.documentation/scripts/**/*`
- [ ] `README.md`
- [ ] `.vscode/settings.json`

### 5. Commit
```bash
git add -A
git commit -m "chore: migrate to .documentation/ structure"
```

---

## Verification Checklist

After migration, check:

- [ ] `.documentation/memory/constitution.md` exists
- [ ] `.documentation/scripts/bash/` has scripts
- [ ] `.documentation/templates/` has templates
- [ ] `specs/` directory untouched
- [ ] Slash commands work
- [ ] No references to old paths in command files
- [ ] Scripts execute without errors

---

## Troubleshooting

### Slash Commands Not Working
1. Restart IDE completely
2. Check command files updated:
   ```bash
   grep -r "\.specify" .claude/  # Should return nothing
   ```

### Script Errors
```bash
# Re-run with verbose output (bash)
bash -x .documentation/scripts/migrate-to-documentation.sh
```

### Manual Path Updates
```bash
# Find all references to old paths
grep -r "\.specify" .
grep -r "/memory/" .
grep -r "/scripts/" .
grep -r "/templates/" .
```

---

## Full Documentation

For detailed guide see: [.documentation/migration-guide.md](.documentation/migration-guide.md)

---

*Quick reference for Spec Kit v1.0.0+ migration*
