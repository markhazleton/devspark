# Spec: Add `specify upgrade` Command

## Problem
Current upgrade process is confusing:
- Users must remember: `specify init --here --force --ai <agent>`
- "init" implies initialization, not upgrade
- Must manually specify the AI agent each time
- No automatic migration detection
- No constitution preservation warnings

## Solution
Add a dedicated `specify upgrade` command that:

### 1. Auto-Detection
- Detects current directory is a Spec Kit project
- Auto-discovers AI agent from existing setup
- Detects if old structure migration needed

### 2. Safety
- Warns about uncommitted git changes
- Offers to backup constitution if customized
- Runs migration automatically if needed
- Preserves user customizations

### 3. User Experience
```bash
# Simple upgrade command
specify upgrade

# With options
specify upgrade --dry-run          # Preview changes
specify upgrade --ai claude        # Override detected agent
specify upgrade --backup           # Create backup before upgrade
```

## Implementation Plan

### Command Definition
```python
@app.command()
def upgrade(
    ai_assistant: str = typer.Option(None, "--ai", help="Override AI assistant (auto-detected if not specified)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without modifying files"),
    backup: bool = typer.Option(False, "--backup", help="Create backup of .documentation/ before upgrade"),
    skip_migration: bool = typer.Option(False, "--skip-migration", help="Skip automatic migration check"),
    github_token: str = typer.Option(None, "--github-token", help="GitHub token for API requests"),
):
    """
    Upgrade an existing Spec Kit project to the latest version.

    This command will:
    1. Detect your current AI assistant setup
    2. Check for old structure (.specify/, memory/, etc.) and migrate if needed
    3. Backup your constitution if customized
    4. Download and apply latest templates
    5. Preserve your specs/ directory and customizations

    Examples:
        specify upgrade                    # Auto-detect and upgrade
        specify upgrade --dry-run          # Preview without changes
        specify upgrade --ai claude        # Override detected agent
        specify upgrade --backup           # Create safety backup
    """
```

### Detection Logic

#### 1. Detect Spec Kit Project
```python
def is_spec_kit_project() -> bool:
    """Check if current directory is a Spec Kit project."""
    indicators = [
        Path(".documentation").exists(),
        Path(".specify").exists(),
        Path("specs").exists(),
        any(Path(d).exists() for d in [
            ".claude/commands", ".github/agents", ".cursor/commands"
        ])
    ]
    return any(indicators)
```

#### 2. Detect AI Agent
```python
def detect_ai_agent() -> Optional[str]:
    """Auto-detect the AI agent from existing setup."""
    agent_paths = {
        "claude": ".claude/commands",
        "copilot": ".github/agents",
        "cursor-agent": ".cursor/commands",
        "windsurf": ".windsurf/workflows",
        "gemini": ".gemini/commands",
        "qwen": ".qwen/commands",
        # ... etc
    }

    for agent, path in agent_paths.items():
        if Path(path).exists():
            return agent

    return None
```

#### 3. Detect Old Structure
```python
def needs_migration() -> bool:
    """Check if old structure exists and needs migration."""
    old_paths = [
        Path(".specify"),
        Path("memory"),
        Path("scripts"),
        Path("templates")
    ]
    return any(p.exists() for p in old_paths)
```

### Upgrade Flow

```python
def upgrade(...):
    show_banner()
    console.print("[bold]Upgrading Spec Kit project...[/bold]\n")

    # 1. Verify we're in a Spec Kit project
    if not is_spec_kit_project():
        console.print("[red]Error:[/red] Current directory is not a Spec Kit project")
        console.print("Run 'specify init --here' to initialize Spec Kit in this directory")
        raise typer.Exit(1)

    # 2. Check for uncommitted changes
    if has_uncommitted_changes():
        console.print("[yellow]Warning:[/yellow] You have uncommitted changes")
        if not dry_run and not typer.confirm("Continue?"):
            raise typer.Exit(0)

    # 3. Auto-detect AI agent if not specified
    if not ai_assistant:
        detected = detect_ai_agent()
        if detected:
            console.print(f"[cyan]Detected AI assistant:[/cyan] {detected}")
            ai_assistant = detected
        else:
            console.print("[yellow]Could not auto-detect AI assistant[/yellow]")
            ai_assistant = prompt_for_agent()

    # 4. Check for old structure migration
    if not skip_migration and needs_migration():
        console.print("[yellow]Old structure detected - migration needed[/yellow]")
        if dry_run:
            console.print("[cyan]Would run migration script[/cyan]")
        else:
            run_migration_script()

    # 5. Backup constitution if requested
    if backup and Path(".documentation/memory/constitution.md").exists():
        backup_path = backup_constitution()
        console.print(f"[green]Constitution backed up to:[/green] {backup_path}")

    # 6. Run the actual upgrade (using init logic)
    if dry_run:
        console.print("\n[cyan]Dry run complete - no changes made[/cyan]")
        show_upgrade_preview()
    else:
        # Call init with --here --force internally
        init(
            project_name=None,
            ai_assistant=ai_assistant,
            here=True,
            force=True,
            github_token=github_token,
            # ... other params
        )

    # 7. Post-upgrade guidance
    console.print("\n[bold green]Upgrade complete![/bold green]")
    console.print("Next steps:")
    console.print("  1. Review changes: git diff")
    console.print("  2. Test slash commands in your AI assistant")
    console.print("  3. Commit changes: git add -A && git commit -m 'chore: upgrade spec-kit'")
```

### Helper Functions

```python
def has_uncommitted_changes() -> bool:
    """Check if git working tree has uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "diff-index", "--quiet", "HEAD", "--"],
            capture_output=True,
            cwd=Path.cwd()
        )
        return result.returncode != 0
    except:
        return False

def run_migration_script():
    """Run the appropriate migration script."""
    if sys.platform == "win32":
        script = ".documentation/scripts/migrate-to-documentation.ps1"
        subprocess.run(["powershell", "-File", script], check=True)
    else:
        script = ".documentation/scripts/migrate-to-documentation.sh"
        subprocess.run(["bash", script], check=True)

def backup_constitution() -> Path:
    """Create backup of constitution file."""
    constitution = Path(".documentation/memory/constitution.md")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = Path(f".documentation/memory/constitution.md.{timestamp}.bak")
    shutil.copy2(constitution, backup_path)
    return backup_path
```

## Benefits

### For Users
- **Clearer intent**: `upgrade` is explicit
- **Less typing**: No need to specify `--here --force`
- **Safer**: Auto-detects agent, warns about changes
- **Automatic migration**: Runs migration if old structure detected
- **Better UX**: Guided process with helpful messages

### For Maintainers
- **Separation of concerns**: Init = new projects, Upgrade = existing
- **Better analytics**: Can track upgrades separately
- **Easier documentation**: Single command to document
- **Flexible**: Can add upgrade-specific logic

## Documentation Updates

### README.md
```markdown
## Upgrading

Upgrade to the latest version:

```bash
# Upgrade CLI tool
uv tool install specify-cli --force --from git+https://github.com/MarkHazleton/spec-kit.git

# Upgrade project files
specify upgrade
```

That's it! The `upgrade` command will:
- Auto-detect your AI assistant
- Migrate old structure if needed
- Update all templates and scripts
- Preserve your specs and customizations
```

### .documentation/upgrade.md
Update guide to use `specify upgrade` instead of `specify init --here --force`

## Migration Path

### Phase 1: Add Command (Backwards Compatible)
- Add `upgrade` command alongside `init --here --force`
- Both work, but document `upgrade` as preferred
- Add deprecation notice to `init --here --force`

### Phase 2: Full Transition
- Update all documentation to use `upgrade`
- Add hint in `init` when used in existing directory:
  ```
  Tip: Use 'specify upgrade' to upgrade existing projects
  ```

### Phase 3: Future
- Consider making `init --here` require explicit confirmation
- Keep `upgrade` as the standard upgrade path

## Testing

```bash
# Test auto-detection
cd existing-project
specify upgrade --dry-run

# Test manual override
specify upgrade --ai claude --dry-run

# Test migration
cd project-with-old-structure
specify upgrade --dry-run

# Test backup
specify upgrade --backup --dry-run
```

## Alternative: Simpler Approach

If full implementation is too complex initially, start with:

```python
@app.command()
def upgrade(
    ai_assistant: str = typer.Option(None, "--ai"),
):
    """Upgrade existing project (shortcut for 'init --here --force')."""

    # Auto-detect agent
    if not ai_assistant:
        ai_assistant = detect_ai_agent() or prompt_for_agent()

    # Just call init
    init(
        project_name=None,
        ai_assistant=ai_assistant,
        here=True,
        force=True,
    )
```

This gives 80% of the benefits with 20% of the code.
