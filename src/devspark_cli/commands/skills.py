"""Skills subcommand group: list and validate DevSpark Agent Skills."""
import os
import re
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table

skills_app = typer.Typer(name="skills", help="Manage and validate DevSpark Agent Skills.")

console = Console()
stderr_console = Console(stderr=True)

# Rules from SKILL-validation-contract.md
_NAME_REGEX = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_VERSION_REGEX = re.compile(r"^\d+\.\d+\.\d+$")
_PROHIBITED_KEYS = {
    "handoffs",
    "scripts",
    "classification",
    "required_gates",
    "recommended_next_step",
    "version",
}
_PROHIBITED_BODY_STRINGS = [
    ".devspark/",
    "{SCRIPT}",
    "FEATURE_DIR",
    "{AGENT_SCRIPT}",
    "handoffs:",
]
_BODY_WARN_LINES = 400
_BODY_FAIL_LINES = 500

# Output format note: --json flag is intentionally omitted in this release.
# The output format is not yet stable for scripting consumption.
# Do not parse this output in scripts until a --json flag is added in a
# future semver release and the format is declared stable.


def _find_skills_root() -> Path:
    """Locate the templates/skills/ directory.

    Resolution order:
    1. DEVSPARK_SKILLS_ROOT env var — explicit override for installed/CI environments.
    2. __file__-relative path — works in source-tree and editable installs only.
       When installed as a wheel, templates/ is not part of the package and this
       path will not exist; a warning is emitted so the user knows to set the env var.
    """
    env_override = os.environ.get("DEVSPARK_SKILLS_ROOT")
    if env_override:
        return Path(env_override)

    # Path(__file__) = src/devspark_cli/commands/skills.py
    # .parent = commands/, .parent = devspark_cli/, .parent = src/, .parent = repo root
    computed = Path(__file__).parent.parent.parent.parent / "templates" / "skills"
    if not computed.exists():
        stderr_console.print(
            f"[yellow]Warning[/yellow]: skills directory not found at {computed}. "
            "Set DEVSPARK_SKILLS_ROOT to the templates/skills/ path for installed environments."
        )
    return computed


def _parse_skill_md(skill_dir: Path):
    """Return (frontmatter_dict, body_lines) or (None, None) on parse failure."""
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        return None, None
    try:
        content = skill_file.read_text(encoding="utf-8")
    except OSError:
        return None, None
    if not content.startswith("---"):
        return {}, content.splitlines()
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content.splitlines()
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}, content.splitlines()
    return fm, parts[2].splitlines()


def _validate_skill(skill_dir: Path, skill_name: str):
    """Validate one skill. Returns (status, findings).

    status: 'pass', 'warn', or 'fail'
    findings: list of (severity, rule, message) tuples
    """
    findings = []

    fm, body_lines = _parse_skill_md(skill_dir)
    if fm is None:
        findings.append(("error", "skill-unreadable", "SKILL.md could not be read"))
        return "fail", findings

    # name
    name = fm.get("name", "")
    if not name:
        findings.append(("error", "name-missing", "frontmatter must contain 'name' field"))
    else:
        if name != skill_name:
            findings.append((
                "error", "name-mismatch",
                f'[name-mismatch] [{name}] name "{name}" does not match directory "{skill_name}"',
            ))
        if not _NAME_REGEX.match(name):
            findings.append((
                "error", "name-format",
                f'[name-format] [{name}] name must match [a-z0-9]+(-[a-z0-9]+)* pattern',
            ))
        if len(name) > 64:
            findings.append((
                "error", "name-length",
                f'[name-length] [{len(name)}] name length {len(name)} exceeds 64',
            ))

    # description
    desc = str(fm.get("description", ""))
    if not desc.strip():
        findings.append(("error", "description-empty", "[description-empty] description must be non-empty"))
    elif len(desc) > 1024:
        findings.append((
            "error", "description-length",
            f'[description-length] [{len(desc)}] description length {len(desc)} exceeds 1024',
        ))

    # metadata.version
    metadata = fm.get("metadata", {})
    if not isinstance(metadata, dict) or "version" not in metadata:
        findings.append(("error", "version-missing", "[version-missing] metadata.version is required"))
    else:
        version = metadata.get("version")
        if not isinstance(version, str):
            findings.append((
                "error", "version-type",
                f'[version-type] [{version!r}] metadata.version must be a quoted string; got {type(version).__name__}',
            ))
        else:
            if not _VERSION_REGEX.match(version):
                findings.append((
                    "error", "version-format",
                    f'[version-format] ["{version}"] metadata.version "{version}" does not match MAJOR.MINOR.PATCH',
                ))

    # prohibited keys
    found_prohibited = _PROHIBITED_KEYS & set(fm.keys())
    for key in sorted(found_prohibited):
        findings.append((
            "error", "prohibited-key",
            f'[prohibited-key] [{key}] frontmatter key "{key}" is not permitted in SKILL.md',
        ))

    # body rules
    if body_lines is not None:
        body = "\n".join(body_lines)
        count = len(body_lines)
        if count > _BODY_FAIL_LINES:
            findings.append((
                "error", "body-length",
                f'[body-length] [{count}] body line count {count} exceeds maximum of {_BODY_FAIL_LINES}',
            ))
        elif count > _BODY_WARN_LINES:
            findings.append((
                "warning", "body-budget",
                f'[body-budget] [{count}] body line count {count} exceeds advisory limit of {_BODY_WARN_LINES}; consider moving content to references/',
            ))

        for bad_string in _PROHIBITED_BODY_STRINGS:
            if bad_string in body:
                findings.append((
                    "error", "body-scan",
                    f'[body-scan] [{bad_string}] body contains DevSpark-specific string "{bad_string}"',
                ))

    errors = [f for f in findings if f[0] == "error"]
    warnings = [f for f in findings if f[0] == "warning"]

    if errors:
        return "fail", findings
    if warnings:
        return "warn", findings
    return "pass", findings


@skills_app.command("list")
def list_skills():
    """List all Agent Skills found under templates/skills/."""
    skills_root = _find_skills_root()
    if not skills_root.exists():
        console.print(f"[yellow]No skills directory found at {skills_root}[/yellow]")
        raise typer.Exit(0)

    skill_dirs = sorted(
        [d for d in skills_root.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
    )

    if not skill_dirs:
        console.print("[yellow]No skills found.[/yellow]")
        raise typer.Exit(0)

    table = Table(title="DevSpark Agent Skills", show_lines=True)
    table.add_column("Name", style="bold cyan")
    table.add_column("Version", style="green")
    table.add_column("Path", style="dim")
    table.add_column("Status")

    for skill_dir in skill_dirs:
        skill_name = skill_dir.name
        fm, _ = _parse_skill_md(skill_dir)
        if fm is None:
            table.add_row(skill_name, "-", str(skill_dir), "[red]unreadable[/red]")
            continue
        version = str((fm.get("metadata") or {}).get("version", "-"))
        status, findings = _validate_skill(skill_dir, skill_name)
        status_display = (
            "[green]pass[/green]" if status == "pass"
            else "[yellow]warn[/yellow]" if status == "warn"
            else "[red]fail[/red]"
        )
        table.add_row(skill_name, version, str(skill_dir.relative_to(skill_dir.parent.parent)), status_display)

    console.print(table)


@skills_app.command("validate")
def validate_skills(
    path: str = typer.Argument(None, help="Path to a single skill directory to validate, or omit to validate all skills."),
):
    """Validate Agent Skills against the SKILL validation contract.

    Exits 0 on pass or warn; exits 1 on any failure.
    Warn diagnostics go to stderr; fail diagnostics go to stderr.
    """
    skills_root = _find_skills_root()

    if path:
        skill_path = Path(path)
        if not skill_path.is_absolute():
            skill_path = Path.cwd() / skill_path
        skill_dirs = [(skill_path, skill_path.name)] if skill_path.exists() else []
        if not skill_dirs:
            stderr_console.print(f"[red]Skill path not found: {skill_path}[/red]")
            raise typer.Exit(1)
    else:
        if not skills_root.exists():
            stderr_console.print(f"[red]No skills directory found at {skills_root}[/red]")
            raise typer.Exit(1)
        skill_dirs = [
            (d, d.name)
            for d in sorted(skills_root.iterdir())
            if d.is_dir() and (d / "SKILL.md").exists()
        ]

    if not skill_dirs:
        console.print("[yellow]No skills found to validate.[/yellow]")
        raise typer.Exit(0)

    any_fail = False
    warn_count = 0

    for skill_dir, skill_name in skill_dirs:
        status, findings = _validate_skill(skill_dir, skill_name)
        fm, _ = _parse_skill_md(skill_dir)
        version = str((fm or {}).get("metadata", {}).get("version", "-")) if fm else "-"

        if status == "pass":
            console.print(f"[green]PASS[/green] {skill_name} {version}")
        elif status == "warn":
            warnings = [f for f in findings if f[0] == "warning"]
            warn_count += len(warnings)
            console.print(f"[yellow]WARN[/yellow] {skill_name} {version}")
            for _, _, msg in warnings:
                stderr_console.print(f"  [yellow]warn[/yellow]: {msg}")
        else:
            any_fail = True
            console.print(f"[red]FAIL[/red] {skill_name} {version}")
            errors = [f for f in findings if f[0] == "error"]
            for _, _, msg in errors:
                stderr_console.print(f"  [red]fail[/red]: {msg}")

    if warn_count > 0:
        stderr_console.print(f"\n{warn_count} warning(s). Run with a specific path for details.")

    if any_fail:
        raise typer.Exit(1)

    raise typer.Exit(0)
