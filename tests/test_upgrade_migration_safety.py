"""Validation for legacy migration safety during upgrade.

Run with: python tests/test_upgrade_migration_safety.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

agent_registry_spec = importlib.util.spec_from_file_location(
    "devspark_cli.agent_registry",
    str(SRC / "devspark_cli" / "agent_registry.py"),
)
agent_registry_module = importlib.util.module_from_spec(agent_registry_spec)
sys.modules["devspark_cli.agent_registry"] = agent_registry_module
assert agent_registry_spec.loader is not None
agent_registry_spec.loader.exec_module(agent_registry_module)

cli_spec = importlib.util.spec_from_file_location(
    "devspark_cli",
    str(SRC / "devspark_cli" / "__init__.py"),
    submodule_search_locations=[str(SRC / "devspark_cli")],
)
cli_module = importlib.util.module_from_spec(cli_spec)
sys.modules["devspark_cli"] = cli_module
assert cli_spec.loader is not None
cli_spec.loader.exec_module(cli_module)

collect_script_override_summaries = cli_module.collect_script_override_summaries
collect_structural_override_warnings = cli_module.collect_structural_override_warnings
needs_migration = cli_module.needs_migration
render_upgrade_analysis = cli_module.render_upgrade_analysis
run_migration_script = cli_module.run_migration_script


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        # Simulate a repo already using .documentation overrides while still carrying
        # legacy v1.4-style files that need migration or cleanup reporting.
        _write(root / ".documentation" / "commands" / "devspark.specify.md", "team override\n")
        _write(root / ".documentation" / "scripts" / "bash" / "create-pr.sh", "team script\n")
        _write(root / ".documentation" / "scripts" / "powershell" / "create-pr.ps1", "team ps script\n")
        _write(root / ".devspark" / "scripts" / "bash" / "create-pr.sh", "stock script\n")
        _write(root / ".devspark" / "scripts" / "powershell" / "create-pr.ps1", "stock ps script\n")
        _write(root / ".documentation" / "defaults" / "commands" / "devspark.plan.md", "legacy defaults\n")

        # Legacy files that should migrate without overwriting the current .documentation overrides.
        _write(root / ".specify" / "scripts" / "bash" / "create-pr.sh", "legacy migrated script\n")
        _write(root / ".specify" / "specs" / "001-legacy" / "spec.md", "legacy spec\n")
        _write(root / "scripts" / "powershell" / "create-pr.ps1", "legacy root ps script\n")
        _write(root / "templates" / "plan-template.md", "legacy template\n")
        _write(root / "specs" / "001-old" / "spec.md", "old root spec\n")

        original_cwd = Path.cwd()
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                os_chdir = __import__("os").chdir
                os_chdir(root)
                assert needs_migration() is True
                migrated = run_migration_script()
                assert migrated is True
        finally:
            __import__("os").chdir(original_cwd)

        # Existing repo-owned overrides must win over migrated legacy copies.
        assert (root / ".documentation" / "scripts" / "bash" / "create-pr.sh").read_text(encoding="utf-8") == "team script\n"
        assert (root / ".documentation" / "scripts" / "powershell" / "create-pr.ps1").read_text(encoding="utf-8") == "team ps script\n"
        assert (root / ".specify.old").exists()
        assert (root / "scripts.old").exists()
        assert (root / "templates.old").exists()
        assert (root / "specs.old").exists()
        assert (root / ".documentation" / "specs" / "001-legacy" / "spec.md").exists()
        assert (root / ".documentation" / "specs" / "001-old" / "spec.md").exists()

        warnings = collect_structural_override_warnings(root)
        assert [(name, path.name) for name, path in warnings] == [("specify", "devspark.specify.md")]

        script_overrides = collect_script_override_summaries(root)
        names = sorted((shell, override_path.name) for shell, override_path, _, _ in script_overrides)
        assert names == [("bash", "create-pr.sh"), ("powershell", "create-pr.ps1")]

        analysis = render_upgrade_analysis(root)
        assert analysis["pre_separation"]
        assert analysis["legacy_artifacts"]
        assert len(analysis["script_overrides"]) == 2
        assert len(analysis["structural_overrides"]) == 1

    # T065: install/upgrade flows MUST never write under .documentation/telemetry/
    # or any other .documentation/ subpath that the user owns.
    #
    # Note: This guards INSTALL and UPGRADE only. Runtime workflow execution
    # IS allowed to write under .documentation/telemetry/{workflow-events.jsonl,runs/}
    # per spec Assumptions and constitution §III commentary. The runner's
    # writes are a normal product artifact, not a migration step.
    _assert_install_upgrade_never_writes_under_documentation()

    print("Upgrade migration safety validated.")


def _assert_install_upgrade_never_writes_under_documentation() -> None:
    """Static-grep the install/upgrade code paths to confirm they don't
    target ``.documentation/`` for writes.

    Uses a deliberately narrow inspection: the inference / commands modules
    must not emit ``.documentation/telemetry`` or ``.documentation/runs``
    paths during install or upgrade. They MAY mention ``.documentation/``
    for migration *reads* and for the constitution path; we look only for
    write-target patterns.
    """
    cli_dir = ROOT / "src" / "devspark_cli"
    forbidden = (".documentation/telemetry", ".documentation\\telemetry", ".documentation/runs")
    offenders: list[str] = []
    for py in cli_dir.glob("*.py"):
        text = py.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{py.name} contains {token!r}")
    assert not offenders, (
        "install/upgrade code must not target .documentation/telemetry or "
        f".documentation/runs: {offenders}"
    )


if __name__ == "__main__":
    main()
