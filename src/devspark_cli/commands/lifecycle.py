"""Lifecycle commands: check, version, doctor, uninstall."""

import shutil
import sys
from pathlib import Path

import typer

from .._app import app, console, show_banner
from .._utils import StepTracker, check_tool
from ..agent_registry import AGENT_CONFIG, load_agent_registry
from .upgrade import is_devspark_project


@app.command()
def check():
    """Check that all required tools are installed."""
    show_banner()
    console.print("[bold]Checking for installed tools...[/bold]\n")

    tracker = StepTracker("Check Available Tools")

    tracker.add("git", "Git version control")
    git_ok = check_tool("git", tracker=tracker)

    agent_results = {}
    for agent_key, agent_config in AGENT_CONFIG.items():
        agent_name = agent_config["name"]
        requires_cli = agent_config["requires_cli"]

        tracker.add(agent_key, agent_name)

        if requires_cli:
            agent_results[agent_key] = check_tool(agent_key, tracker=tracker)
        else:
            # IDE-based agent - skip CLI check and mark as optional
            tracker.skip(agent_key, "IDE-based, no CLI check")
            agent_results[agent_key] = False  # Don't count IDE agents as "found"

    # Check VS Code variants (not in agent config)
    tracker.add("code", "Visual Studio Code")
    code_ok = check_tool("code", tracker=tracker)

    tracker.add("code-insiders", "Visual Studio Code Insiders")
    code_insiders_ok = check_tool("code-insiders", tracker=tracker)

    console.print(tracker.render())

    console.print("\n[bold green]DevSpark CLI is ready to use![/bold green]")

    if not git_ok:
        console.print("[dim]Tip: Install git for repository management[/dim]")

    if not any(agent_results.values()):
        console.print("[dim]Tip: Install an AI assistant for the best experience[/dim]")


@app.command()
def version():
    """Display version and system information."""
    import importlib.metadata
    import platform

    show_banner()

    # Get CLI version from package metadata
    cli_version = "unknown"
    try:
        cli_version = importlib.metadata.version("devspark-cli")
    except Exception:
        # Fallback: try reading from pyproject.toml if running from source
        try:
            import tomllib
            pyproject_path = Path(__file__).parent.parent.parent.parent / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                    cli_version = data.get("project", {}).get("version", "unknown")
        except Exception:
            pass

    from rich.table import Table
    from rich.panel import Panel

    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Key", style="cyan", justify="right")
    info_table.add_column("Value", style="white")

    info_table.add_row("Product", "DevSpark")
    info_table.add_row("CLI", "DevSpark CLI")
    info_table.add_row("Version", cli_version)
    info_table.add_row("", "")
    info_table.add_row("Python", platform.python_version())
    info_table.add_row("Platform", platform.system())
    info_table.add_row("Architecture", platform.machine())
    info_table.add_row("OS Version", platform.version())

    panel = Panel(
        info_table,
        title="[bold cyan]DevSpark Information[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    )

    console.print(panel)
    console.print()


@app.command()
def doctor():
    """Check whether the current environment is ready for DevSpark harness workflows."""
    show_banner()

    cwd = Path.cwd()
    checks: list[tuple[str, bool, str]] = []

    python_ok = sys.version_info >= (3, 11)
    checks.append(("python", python_ok, f"Python {sys.version.split()[0]}" if python_ok else "Python 3.11 or newer is required"))

    try:
        import pydantic  # noqa: F401

        checks.append(("pydantic", True, "pydantic is importable"))
    except Exception:
        checks.append(("pydantic", False, "Install pydantic: pip install pydantic"))

    installed_layout = (cwd / ".devspark").is_dir()
    source_layout = (cwd / ".documentation").is_dir() and (cwd / "pyproject.toml").is_file() and (cwd / "src" / "devspark_cli").is_dir()
    layout_ok = installed_layout or source_layout
    if installed_layout:
        layout_detail = "Installed project layout detected (.devspark/)"
    elif source_layout:
        layout_detail = "Source checkout layout detected (.documentation + pyproject.toml + src/devspark_cli/)"
    else:
        layout_detail = "Missing DevSpark project layout. Run devspark init or use a compatible source checkout."
    checks.append(("layout", layout_ok, layout_detail))

    try:
        load_agent_registry()
        checks.append(("agents-registry", True, "agents-registry.json is readable and valid"))
    except Exception as exc:
        checks.append(("agents-registry", False, f"agents-registry.json invalid: {exc}"))

    git_ok = shutil.which("git") is not None
    checks.append(("git", git_ok, "git available" if git_ok else "Install git: https://git-scm.com/downloads"))

    for agent_key, agent_config in AGENT_CONFIG.items():
        if not agent_config.get("requires_cli"):
            continue
        available = shutil.which(agent_key) is not None
        detail = f"{agent_config['name']} available" if available else f"Install {agent_config['name']}: {agent_config.get('install_url') or 'see vendor docs'}"
        checks.append((agent_key, available, detail))

    failures = [item for item in checks if not item[1]]
    if console.is_terminal:
        for name, ok, detail in checks:
            symbol = "✓" if ok else "✗"
            color = "green" if ok else "red"
            console.print(f"[{color}]{symbol}[/{color}] {name}: {detail}")
    else:
        for name, ok, detail in checks:
            print(f"{'pass' if ok else 'fail'}\t{name}\t{detail}")

    raise typer.Exit(1 if failures else 0)


@app.command()
def uninstall(
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview what would be removed without deleting"),
):
    """
    Remove DevSpark from the current project, leaving your work untouched.

    Removes:
    - .devspark/          (stock prompts, scripts, templates, version stamp)
    - Agent shim dirs     (.claude/commands/, .github/agents/, .cursor/commands/, etc.)
    - .vscode/settings.json entries added by DevSpark (if identifiable)

    Preserves:
    - .documentation/     (constitution, specs, commands, all your work)
    - Any non-DevSpark files in agent directories

    Examples:
        devspark uninstall              # Interactive confirmation
        devspark uninstall --dry-run    # Preview only
        devspark uninstall --force      # Skip confirmation
    """
    show_banner()

    cwd = Path.cwd()

    if not is_devspark_project():
        console.print("[red]Error:[/red] Current directory is not a DevSpark project")
        raise typer.Exit(1)

    # Collect directories to remove
    removals: list[tuple[str, Path]] = []

    devspark_dir = cwd / ".devspark"
    if devspark_dir.exists():
        removals.append(("DevSpark installation", devspark_dir))

    # Collect agent shim directories
    for agent_key, agent_config in AGENT_CONFIG.items():
        agent_dir = cwd / agent_config["folder"]
        if agent_dir.exists():
            removals.append((f"{agent_config['name']} shims", agent_dir))

    # Also check for .github/prompts (Copilot companion files)
    prompts_dir = cwd / ".github" / "prompts"
    if prompts_dir.exists():
        removals.append(("Copilot prompt files", prompts_dir))

    # Old version stamp (legacy location)
    old_stamp = cwd / ".documentation" / "DEVSPARK_VERSION"
    if old_stamp.exists():
        removals.append(("Legacy version stamp", old_stamp))

    if not removals:
        console.print("[yellow]Nothing to remove — no DevSpark installation files found[/yellow]")
        raise typer.Exit(0)

    # Show what will be removed
    console.print("[bold]The following will be removed:[/bold]\n")
    for label, path in removals:
        if path.is_dir():
            count = sum(1 for _ in path.rglob("*") if _.is_file())
            console.print(f"  [red]✗[/red] {label}: [cyan]{path.relative_to(cwd)}[/cyan] ({count} files)")
        else:
            console.print(f"  [red]✗[/red] {label}: [cyan]{path.relative_to(cwd)}[/cyan]")

    console.print()
    console.print("[green]✓[/green] .documentation/ — [bold]untouched[/bold] (your constitution, specs, and customizations)")
    console.print()

    if dry_run:
        console.print("[cyan]DRY RUN — no files were deleted[/cyan]")
        return

    if not force:
        response = typer.confirm("Remove DevSpark from this project?", default=False)
        if not response:
            console.print("[yellow]Uninstall cancelled[/yellow]")
            raise typer.Exit(0)

    # Perform removal
    removed_count = 0
    for label, path in removals:
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            console.print(f"  [green]✓[/green] Removed: {path.relative_to(cwd)}")
            removed_count += 1
        except Exception as e:
            console.print(f"  [red]✗[/red] Failed to remove {path.relative_to(cwd)}: {e}")

    console.print(f"\n[bold green]DevSpark removed.[/bold green] {removed_count} item(s) deleted.")
    console.print("[dim]Your .documentation/ directory and all your work is intact.[/dim]")
    console.print()
