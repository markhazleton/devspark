"""upgrade command and its supporting helpers."""

import subprocess
from pathlib import Path
from typing import Optional

import typer

from .._app import app, console, show_banner
from .._upgrade_helpers import read_version_stamp, write_version_stamp  # noqa: F401 (re-exported)
from .._utils import select_with_arrows
from ..agent_registry import AGENT_CONFIG

LEGACY_BACKUP_DIRS = (
    ".specify.old",
    "memory.old",
    "scripts.old",
    "templates.old",
    "specs.old",
)

STRUCTURAL_OVERRIDE_COMMANDS = (
    "specify",
    "plan",
    "tasks",
    "implement",
    "create-pr",
)


# ============================================================================
# Helper Functions for Upgrade Command
# ============================================================================

def is_devspark_project() -> bool:
    """Check if current directory is a DevSpark project."""
    indicators = [
        Path(".devspark").exists(),
        Path(".documentation").exists(),
    ]

    # Check for any agent command directories
    agent_dirs = [
        ".claude/commands",
        ".github/agents",
        ".cursor/commands",
        ".windsurf/workflows",
        ".gemini/commands",
        ".qwen/commands",
        ".opencode",
        ".codex",
        ".kilocode",
        ".augment",
        ".roo",
        ".codebuddy",
        ".qoder",
        ".amazonq",
        ".agents",
        ".shai",
        ".bob",
    ]

    indicators.extend([Path(d).exists() for d in agent_dirs])
    return any(indicators)


def detect_ai_agent() -> Optional[str]:
    """Auto-detect the AI agent from existing setup."""
    # Check against AGENT_CONFIG
    for agent_key, agent_config in AGENT_CONFIG.items():
        folder = agent_config["folder"]
        # Check both the folder itself and common subdirectories
        if Path(folder).exists():
            # For some agents, check if commands subdirectory exists
            if agent_key in ["claude", "copilot", "cursor-agent"]:
                if agent_key == "claude":
                    sub = "commands"
                elif agent_key == "copilot":
                    sub = "agents"
                else:
                    sub = "commands"
                commands_path = Path(folder) / sub
                if commands_path.exists():
                    return agent_key
            else:
                return agent_key

    return None


def needs_migration() -> bool:
    """Check if old structure exists and needs migration."""
    old_paths = [
        Path(".specify"),
        Path("memory") if not Path(".documentation/memory").exists() else None,
        Path("scripts") if not Path(".devspark/scripts").exists() else None,
        Path("templates") if not Path(".devspark/templates").exists() else None,
        Path("specs") if not Path(".documentation/specs").exists() else None,
    ]
    # Filter out None values
    old_paths = [p for p in old_paths if p is not None]
    return any(p.exists() for p in old_paths)


def has_uncommitted_changes() -> bool:
    """Check if git working tree has uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "diff-index", "--quiet", "HEAD", "--"],
            capture_output=True,
            cwd=Path.cwd(),
            timeout=5
        )
        return result.returncode != 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def run_migration_script() -> bool:
    """Migrate old project structure to .documentation/ using Python.

    Moves the following into .documentation/ and renames originals to *.old:
      .specify/  ->  .specify.old/  (contents copied into .documentation/)
      memory/    ->  memory.old/
      scripts/   ->  scripts.old/
      templates/ ->  templates.old/
      specs/     ->  specs.old/
    """
    import shutil

    cwd = Path.cwd()
    doc_dir = cwd / ".documentation"
    doc_dir.mkdir(exist_ok=True)

    moved = 0
    skipped_overwrites: list[tuple[Path, Path]] = []

    def _merge_into(src: Path, dst: Path) -> None:
        """Copy src tree into dst without overwriting existing .documentation files.

        Legacy files should replace stock files created during init, but they must
        never clobber repo-owned work that already exists under .documentation/.
        """
        dst.mkdir(parents=True, exist_ok=True)
        for item in src.rglob("*"):
            if item.is_file():
                rel = item.relative_to(src)
                dst_file = dst / rel
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                if dst_file.exists():
                    skipped_overwrites.append((item, dst_file))
                    continue
                shutil.copy2(str(item), str(dst_file))

    # Handle legacy hidden folder (.specify/) — copy known subdirs then root files, then rename
    legacy_spec_dir = cwd / ".specify"
    if legacy_spec_dir.exists():
        for sub in ["memory", "scripts", "templates", "specs"]:
            src = legacy_spec_dir / sub
            if src.exists():
                _merge_into(src, doc_dir / sub)
        # Copy any root-level files in .specify
        for item in legacy_spec_dir.iterdir():
            if item.is_file():
                dst_file = doc_dir / item.name
                if not dst_file.exists():
                    shutil.copy2(str(item), str(dst_file))
                else:
                    skipped_overwrites.append((item, dst_file))
        legacy_spec_dir.rename(cwd / ".specify.old")
        console.print("[green]>[/green] .specify/ -> .specify.old/")
        moved += 1

    # Handle root-level directories
    for src_name in ["memory", "scripts", "templates", "specs"]:
        src = cwd / src_name
        dst = doc_dir / src_name
        if src.exists():
            _merge_into(src, dst)
            src.rename(cwd / f"{src_name}.old")
            console.print(f"[green]>[/green] {src_name}/ -> .documentation/{src_name}/ (original -> {src_name}.old/)")
            moved += 1

    if moved == 0:
        console.print("[yellow]Nothing to migrate — old directories not found.[/yellow]")
        return False

    if skipped_overwrites:
        console.print("[yellow]Preserved existing .documentation files during migration:[/yellow]")
        for src_file, dst_file in skipped_overwrites[:10]:
            console.print(
                f"  - kept {dst_file.relative_to(cwd)}; skipped legacy copy from {src_file.relative_to(cwd)}"
            )
        if len(skipped_overwrites) > 10:
            console.print(f"  - ... and {len(skipped_overwrites) - 10} more preserved file(s)")
        console.print("[dim]Review legacy *.old/ backups and merge any skipped content manually if needed.[/dim]")

    console.print(f"[green]Migration complete.[/green] Moved {moved} item(s). Old directories renamed to *.old/")
    console.print("[dim]After verifying, delete *.old/ directories when ready.[/dim]")
    return True


def _line_diff_count(path_a: Path, path_b: Path) -> int:
    """Return a simple line delta count between two text files."""
    try:
        lines_a = path_a.read_text(encoding="utf-8").splitlines()
        lines_b = path_b.read_text(encoding="utf-8").splitlines()
    except Exception:
        return 0

    max_len = max(len(lines_a), len(lines_b))
    changed = 0
    for index in range(max_len):
        left = lines_a[index] if index < len(lines_a) else ""
        right = lines_b[index] if index < len(lines_b) else ""
        if left != right:
            changed += 1
    return changed


def collect_legacy_artifacts(project_path: Path) -> list[tuple[str, Path]]:
    """Collect stale legacy artifacts that the user may want to clean up manually."""
    artifacts: list[tuple[str, Path]] = []

    for rel_path in LEGACY_BACKUP_DIRS:
        path = project_path / rel_path
        if path.exists():
            artifacts.append(("Legacy backup", path))

    legacy_defaults = project_path / ".documentation" / "defaults"
    if legacy_defaults.exists():
        artifacts.append(("Pre-separation stock defaults", legacy_defaults))

    legacy_version = project_path / ".documentation" / "DEVSPARK_VERSION"
    if legacy_version.exists():
        artifacts.append(("Legacy version stamp", legacy_version))

    for pattern in (
        ".claude/commands/devspark.*-old.md",
        ".github/agents/devspark.*-old.agent.md",
        ".github/prompts/devspark.*-old.prompt.md",
        ".cursor/commands/devspark.*-old.md",
        ".windsurf/workflows/devspark.*-old.md",
    ):
        for match in project_path.glob(pattern):
            artifacts.append(("Legacy shim duplicate", match))

    return artifacts


def collect_structural_override_warnings(project_path: Path) -> list[tuple[str, Path]]:
    """Return override files that can mask structural stock command changes."""
    warnings: list[tuple[str, Path]] = []
    for command_name in STRUCTURAL_OVERRIDE_COMMANDS:
        team_override = project_path / ".documentation" / "commands" / f"devspark.{command_name}.md"
        if team_override.exists():
            warnings.append((command_name, team_override))
    return warnings


def collect_script_override_summaries(project_path: Path) -> list[tuple[str, Path, Path | None, int]]:
    """Compare team script overrides to stock scripts for upgrade reporting."""
    overrides: list[tuple[str, Path, Path | None, int]] = []
    for shell in ("bash", "powershell"):
        override_dir = project_path / ".documentation" / "scripts" / shell
        stock_dir = project_path / ".devspark" / "scripts" / shell
        if not override_dir.exists():
            continue
        for override_path in sorted(p for p in override_dir.iterdir() if p.is_file()):
            stock_path = stock_dir / override_path.name
            diff_count = _line_diff_count(override_path, stock_path) if stock_path.exists() else 0
            overrides.append((shell, override_path, stock_path if stock_path.exists() else None, diff_count))
    return overrides


def collect_pre_separation_framework_artifacts(project_path: Path) -> list[tuple[str, Path]]:
    """Detect old framework-managed files that still live under .documentation/."""
    findings: list[tuple[str, Path]] = []
    for rel_path in (
        ".documentation/defaults/commands",
        ".documentation/defaults/templates",
    ):
        path = project_path / rel_path
        if path.exists():
            findings.append(("Pre-separation framework content", path))
    return findings


def render_upgrade_analysis(project_path: Path) -> dict:
    """Collect upgrade analysis data for reporting before and after upgrade."""
    return {
        "legacy_artifacts": collect_legacy_artifacts(project_path),
        "pre_separation": collect_pre_separation_framework_artifacts(project_path),
        "structural_overrides": collect_structural_override_warnings(project_path),
        "script_overrides": collect_script_override_summaries(project_path),
        "stamp": read_version_stamp(project_path),
    }


def print_upgrade_analysis(analysis: dict, project_path: Path, ai_assistant: str, dry_run: bool = False) -> None:
    """Render upgrade analysis guidance for dry-run and real upgrade flows."""
    stamp = analysis.get("stamp") or {}
    if stamp:
        method = stamp.get("method") or stamp.get("agent") or "unknown"
        console.print(
            f"[bold]Installed Version:[/bold] {stamp.get('version', 'unknown')}  "
            f"[bold]Method:[/bold] {method}"
        )
        if stamp.get("migrated-from"):
            console.print(f"[dim]Migration marker:[/dim] {stamp['migrated-from']}")
        console.print()

    pre_separation = analysis.get("pre_separation", [])
    if pre_separation:
        console.print("[yellow]Pre-separation framework files detected under .documentation/:[/yellow]")
        for label, path in pre_separation:
            console.print(f"  - {path.relative_to(project_path)} ({label})")
        console.print("[dim]Upgrade will refresh stock files under .devspark/ and leave these legacy copies untouched for manual cleanup.[/dim]\n")

    structural_overrides = analysis.get("structural_overrides", [])
    if structural_overrides:
        console.print("[yellow]Team overrides that may mask structural stock changes:[/yellow]")
        for command_name, path in structural_overrides:
            console.print(f"  - /devspark.{command_name} -> {path.relative_to(project_path)}")
        console.print("[dim]Review diffs against .devspark/defaults/commands/ after upgrade before assuming the new contract is active.[/dim]\n")

    script_overrides = analysis.get("script_overrides", [])
    if script_overrides:
        console.print("[cyan]Team script overrides preserved during upgrade:[/cyan]")
        for shell, override_path, stock_path, diff_count in script_overrides:
            if stock_path is None:
                console.print(f"  - {override_path.relative_to(project_path)} ({shell}, no stock counterpart)")
            else:
                console.print(
                    f"  - {override_path.relative_to(project_path)} ({shell}, {diff_count} differing line(s) vs stock)"
                )
        console.print()

    legacy_artifacts = analysis.get("legacy_artifacts", [])
    if legacy_artifacts:
        heading = "Legacy artifacts to review after upgrade:" if not dry_run else "Legacy artifacts already present:"
        console.print(f"[yellow]{heading}[/yellow]")
        for label, path in legacy_artifacts:
            console.print(f"  - {path.relative_to(project_path)} ({label})")
        console.print("[dim]DevSpark will not delete these automatically. Remove them manually after verification.[/dim]\n")


# ============================================================================
# Upgrade Command
# ============================================================================

@app.command()
def upgrade(
    ai_assistant: str = typer.Option(None, "--ai", help="Override AI assistant (auto-detected if not specified)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without modifying files"),
    skip_migration: bool = typer.Option(False, "--skip-migration", help="Skip automatic migration check"),
    force: bool = typer.Option(False, "--force", help="Skip all confirmations"),
    github_token: str = typer.Option(None, "--github-token", help="GitHub token for API requests"),
    script_type: str = typer.Option(None, "--script", help="Script type to use: sh or ps"),
    ignore_agent_tools: bool = typer.Option(False, "--ignore-agent-tools", help="Skip checks for AI agent tools"),
    no_git: bool = typer.Option(False, "--no-git", help="Skip git repository operations"),
):
    """
    Upgrade an existing DevSpark project to the latest version.

    This command will:
    1. Detect your current AI assistant setup
    2. Check for old structure (.specify/, memory/, etc.) and migrate if needed
    3. Download and apply latest templates (to .devspark/)
    4. Preserve your constitution, specs, and team command customizations

    Your customizations are NEVER overwritten:
    - .documentation/ is entirely user-owned and never touched
    - .devspark/ is the removable installation — fully replaced on upgrade

    Examples:
        devspark upgrade                    # Auto-detect and upgrade
        devspark upgrade --dry-run          # Preview without changes
        devspark upgrade --ai claude        # Override detected agent
        devspark upgrade --skip-migration   # Skip old structure migration
    """

    show_banner()
    console.print("[bold]Upgrading DevSpark project...[/bold]\n")

    # Step 1: Verify we're in a DevSpark project
    console.print("[cyan]→[/cyan] Verifying DevSpark project...")
    if not is_devspark_project():
        console.print("[red]✗ Error:[/red] Current directory is not a DevSpark project")
        console.print("[dim]Run 'devspark init --here' to initialize DevSpark in this directory[/dim]")
        raise typer.Exit(1)
    console.print("[green]✓[/green] DevSpark project detected\n")

    # Step 2: Check for uncommitted changes
    if not no_git:
        console.print("[cyan]→[/cyan] Checking git status...")
        if has_uncommitted_changes():
            console.print("[yellow]⚠ Warning:[/yellow] You have uncommitted changes in your repository")
            console.print("[dim]It's recommended to commit or stash changes before upgrading[/dim]")
            if not dry_run and not force:
                response = typer.confirm("Continue anyway?", default=False)
                if not response:
                    console.print("[yellow]Upgrade cancelled[/yellow]")
                    raise typer.Exit(0)
        else:
            console.print("[green]✓[/green] Working tree is clean\n")

    # Step 3: Auto-detect AI agent if not specified
    console.print("[cyan]→[/cyan] Detecting AI assistant...")
    if not ai_assistant:
        detected = detect_ai_agent()
        if detected:
            agent_name = AGENT_CONFIG[detected]["name"]
            console.print(f"[green]✓[/green] Detected AI assistant: [cyan]{agent_name}[/cyan] ({detected})\n")
            ai_assistant = detected
        else:
            console.print("[yellow]⚠[/yellow] Could not auto-detect AI assistant")
            if dry_run:
                console.print("[cyan]In actual run, you would be prompted to select an agent[/cyan]\n")
                ai_assistant = "claude"  # Default for dry run
            else:
                console.print("\n[bold]Please select your AI assistant:[/bold]")
                ai_choices = {key: config["name"] for key, config in AGENT_CONFIG.items()}
                selected_ai = select_with_arrows(ai_choices, "Choose your AI assistant:", "copilot")
                ai_assistant = selected_ai
                console.print()
    else:
        if ai_assistant not in AGENT_CONFIG:
            console.print(f"[red]✗ Error:[/red] Invalid AI assistant '{ai_assistant}'")
            console.print(f"[dim]Choose from: {', '.join(AGENT_CONFIG.keys())}[/dim]")
            raise typer.Exit(1)
        agent_name = AGENT_CONFIG[ai_assistant]["name"]
        console.print(f"[green]✓[/green] Using AI assistant: [cyan]{agent_name}[/cyan] ({ai_assistant})\n")

    # Step 4: Check for old structure migration (deferred — runs after templates are installed)
    migration_needed = False
    migration_confirmed = False
    pre_upgrade_analysis = render_upgrade_analysis(Path.cwd())
    if not skip_migration:
        console.print("[cyan]→[/cyan] Checking for old structure...")
        if needs_migration():
            migration_needed = True
            console.print("[yellow]⚠[/yellow] Old structure detected (.specify/, memory/, scripts/, or templates/)")
            console.print("[dim]Migration to .documentation/ structure will run after templates are installed[/dim]")

            if dry_run:
                console.print("[cyan]Would run migration after templates are installed[/cyan]\n")
            elif force:
                console.print("[cyan]Migration will run automatically after templates are installed (--force)...[/cyan]\n")
                migration_confirmed = True
            else:
                migration_confirmed = typer.confirm("Run migration after templates are installed?", default=True)
                if not migration_confirmed:
                    console.print("[yellow]Skipping migration - you can run it later[/yellow]")
                    console.print("[dim]See .documentation/upgrade.md for manual steps[/dim]\n")
        else:
            console.print("[green]✓[/green] Already using .documentation/ structure\n")

    print_upgrade_analysis(pre_upgrade_analysis, Path.cwd(), ai_assistant, dry_run=dry_run)

    # Step 5: Show upgrade preview for dry run
    if dry_run:
        console.print("\n" + "="*60)
        console.print("[bold cyan]DRY RUN COMPLETE - No changes made[/bold cyan]")
        console.print("="*60 + "\n")

        console.print("[bold]What would happen in actual upgrade:[/bold]")
        console.print("  1. Download latest DevSpark templates from GitHub")
        console.print(f"  2. Update {AGENT_CONFIG[ai_assistant]['folder']} agent shims")
        console.print("  3. Update .devspark/ with latest stock prompts, scripts, templates, and VERSION stamp")
        if migration_needed:
            console.print("  4. Run legacy .specify/root-structure migration into .documentation/")
        console.print("  [green]✓[/green] .documentation/ — entirely user-owned, NEVER touched")
        console.print()
        console.print("[bold]To perform the actual upgrade:[/bold]")
        console.print(f"  [cyan]devspark upgrade --ai {ai_assistant}[/cyan]")
        console.print()
        return

    # Step 7: Run the actual upgrade (using init logic)
    console.print("[cyan]→[/cyan] Downloading and applying latest templates...\n")

    # Import here to avoid a circular import at module level:
    # upgrade.py is loaded by __init__.py before commands/init.py, so importing
    # init at the top of upgrade.py would create an import cycle through __init__.py.
    from .init import init

    try:
        # Call init with --here --force internally
        init(
            project_name=None,
            ai_assistant=ai_assistant,
            script_type=script_type,
            ignore_agent_tools=ignore_agent_tools,
            no_git=no_git,
            here=True,
            force=True,  # Always force to skip confirmation since we already confirmed in upgrade
            skip_tls=False,
            debug=False,
            github_token=github_token,
        )
    except Exception as e:
        console.print(f"\n[red]✗ Upgrade failed:[/red] {e}")
        raise typer.Exit(1)

    # Step 7.5: Run migration now that templates (including migration scripts) are installed
    if migration_needed and migration_confirmed:
        console.print("[cyan]→[/cyan] Running migration to .documentation/ structure...")
        success = run_migration_script()
        if success:
            console.print("[green]✓[/green] Migration completed\n")
        else:
            console.print("[yellow]⚠[/yellow] Migration had issues. See .documentation/upgrade.md for manual steps.\n")

    # Step 8: Post-upgrade guidance
    post_upgrade_analysis = render_upgrade_analysis(Path.cwd())

    console.print("\n" + "="*60)
    console.print("[bold green]✓ Upgrade Complete![/bold green]")
    console.print("="*60 + "\n")

    # Show the stamped version
    stamp = read_version_stamp(Path.cwd())
    if stamp:
        console.print(f"[green]✓[/green] Version stamp written: [cyan].devspark/VERSION[/cyan]")
        console.print(
            f"  Version: [bold]{stamp.get('version', 'unknown')}[/bold]  "
            f"Method: {stamp.get('method', stamp.get('agent', 'unknown'))}  "
            f"Date: {stamp.get('installed', 'unknown')}"
        )
        if stamp.get("migrated-from"):
            console.print(f"  Migrated From: {stamp.get('migrated-from')}\n")
        else:
            console.print()

    print_upgrade_analysis(post_upgrade_analysis, Path.cwd(), ai_assistant)

    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Review changes: [cyan]git status[/cyan] and [cyan]git diff[/cyan]")
    console.print("  2. Test slash commands in your AI assistant (e.g., [cyan]/devspark.constitution[/cyan])")
    console.print("  3. Diff stock vs overrides where needed: [cyan].devspark/defaults/commands/[/cyan] vs [cyan].documentation/commands/[/cyan]")
    console.print("  4. Verify your specs are intact: [cyan]ls .documentation/specs/[/cyan]")
    console.print("  5. If everything looks good, commit:")
    console.print("     [cyan]git add -A[/cyan]")
    console.print("     [cyan]git commit -m 'chore: upgrade to latest devspark version'[/cyan]")

    console.print()
