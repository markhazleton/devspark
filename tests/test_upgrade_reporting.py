"""Validation for upgrade reporting helpers and version stamps.

Run with: python tests/test_upgrade_reporting.py
"""

from __future__ import annotations

import importlib.util
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


collect_legacy_artifacts = cli_module.collect_legacy_artifacts
collect_pre_separation_framework_artifacts = cli_module.collect_pre_separation_framework_artifacts
collect_script_override_summaries = cli_module.collect_script_override_summaries
collect_structural_override_warnings = cli_module.collect_structural_override_warnings
read_version_stamp = cli_module.read_version_stamp
render_upgrade_analysis = cli_module.render_upgrade_analysis
write_version_stamp = cli_module.write_version_stamp


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        write_version_stamp(root, "copilot", release_version="v1.5.0")
        stamp = read_version_stamp(root)
        assert stamp is not None
        assert stamp["version"] == "1.5.0"
        assert stamp["method"] == "copilot-quickstart"
        assert stamp["agent"] == "copilot"
        assert stamp["migrated-from"] == "fresh"

        _write(
            root / ".devspark" / "VERSION",
            "1.4.2\ninstalled: 2026-04-01\nagent: claude\n",
        )
        legacy_stamp = read_version_stamp(root)
        assert legacy_stamp is not None
        assert legacy_stamp["version"] == "1.4.2"
        assert legacy_stamp["agent"] == "claude"
        assert legacy_stamp["method"] == "claude-quickstart"

        _write(root / ".documentation" / "commands" / "devspark.specify.md", "team override\n")
        _write(root / ".documentation" / "scripts" / "bash" / "create-pr.sh", "echo team\n")
        _write(root / ".devspark" / "scripts" / "bash" / "create-pr.sh", "echo stock\n")
        _write(root / ".documentation" / "defaults" / "commands" / "devspark.plan.md", "legacy stock\n")
        _write(root / ".documentation" / "DEVSPARK_VERSION", "1.4.0\n")
        (root / "scripts.old").mkdir()

        overrides = collect_structural_override_warnings(root)
        assert [(name, path.name) for name, path in overrides] == [("specify", "devspark.specify.md")]

        pre_separation = collect_pre_separation_framework_artifacts(root)
        assert [path.as_posix().endswith(".documentation/defaults/commands") for _, path in pre_separation] == [True]

        script_overrides = collect_script_override_summaries(root)
        assert len(script_overrides) == 1
        shell, override_path, stock_path, diff_count = script_overrides[0]
        assert shell == "bash"
        assert override_path.name == "create-pr.sh"
        assert stock_path is not None and stock_path.name == "create-pr.sh"
        assert diff_count > 0

        legacy_artifacts = collect_legacy_artifacts(root)
        legacy_paths = {path.as_posix() for _, path in legacy_artifacts}
        assert any(path.endswith("scripts.old") for path in legacy_paths)
        assert any(path.endswith(".documentation/defaults") for path in legacy_paths)
        assert any(path.endswith(".documentation/DEVSPARK_VERSION") for path in legacy_paths)

        analysis = render_upgrade_analysis(root)
        assert len(analysis["structural_overrides"]) == 1
        assert len(analysis["script_overrides"]) == 1
        assert len(analysis["pre_separation"]) == 1
        assert len(analysis["legacy_artifacts"]) >= 3

    print("Upgrade reporting helpers validated.")


if __name__ == "__main__":
    main()
