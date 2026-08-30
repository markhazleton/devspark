"""Contracts for quickstart latest-version detection."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_quickstarts_use_github_releases_for_latest_version() -> None:
    for path in sorted((ROOT / "quickstart").glob("devspark_quickstart_*.md")):
        text = path.read_text(encoding="utf-8")
        assert "https://api.github.com/repos/markhazleton/devspark/releases/latest" in text, (
            f"{path.name} must use GitHub Releases as the primary latest-version source."
        )
        changelog_pos = text.find("https://raw.githubusercontent.com/markhazleton/devspark/main/CHANGELOG.md")
        releases_pos = text.find("https://api.github.com/repos/markhazleton/devspark/releases/latest")
        assert releases_pos != -1
        assert changelog_pos == -1 or releases_pos < changelog_pos, (
            f"{path.name} must treat CHANGELOG latest-version parsing as a fallback."
        )


def test_living_docs_name_current_release_explicitly() -> None:
    current_release_line = (
        "[v4.0.0](https://github.com/markhazleton/devspark/releases/tag/v4.0.0)"
    )
    for rel_path in (
        "README.md",
        ".documentation/README.md",
        ".documentation/about.md",
        ".documentation/index.md",
        ".documentation/installation.md",
        ".documentation/quickstart.md",
        ".documentation/upgrade.md",
    ):
        text = (ROOT / rel_path).read_text(encoding="utf-8")
        assert current_release_line in text, f"{rel_path} must explicitly name v4.0.0"


def test_living_docs_use_v400_command_counts() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    docs_index = (ROOT / ".documentation" / "index.md").read_text(encoding="utf-8")
    templates_readme = (ROOT / "templates" / "README.md").read_text(encoding="utf-8")

    assert "29 stock command prompts" in readme
    assert "29 stock command prompt files" in readme
    assert "29 stock command prompts" in docs_index
    assert "As of v4.0.0, the collection includes 28 active commands plus 1 deprecated compatibility alias." in templates_readme


def test_quickstarts_do_not_reference_stale_240_version() -> None:
    for path in sorted((ROOT / "quickstart").glob("devspark_quickstart_*.md")):
        text = path.read_text(encoding="utf-8")
        assert "2.4" not in text, f"{path.name} must not expose stale v2.4 wording."


def test_quickstart_update_and_repair_modes_include_agent_skills() -> None:
    for path in sorted((ROOT / "quickstart").glob("devspark_quickstart_*.md")):
        text = path.read_text(encoding="utf-8")
        occurrences = text.count("Re-fetch all Agent Skill packages into `.devspark/templates/skills/`")
        assert occurrences >= 2, (
            f"{path.name} must re-fetch Agent Skill packages in both update and repair mode."
        )


def test_quickstart_command_tables_match_current_command_inventory() -> None:
    expected = sorted(path.name for path in (ROOT / "templates" / "commands").glob("*.md"))
    command_row = re.compile(
        r"^\| `([^`]+\.md)` \| `\.devspark/defaults/commands/devspark\.([^`]+)\.md`",
        re.MULTILINE,
    )

    for path in sorted((ROOT / "quickstart").glob("devspark_quickstart_*.md")):
        text = path.read_text(encoding="utf-8")
        rows = command_row.findall(text)
        sources = sorted(source for source, _destination_stem in rows)
        assert sources == expected, f"{path.name} command table is not in sync with templates/commands"
        for source, destination_stem in rows:
            assert source.removesuffix(".md") == destination_stem


def test_quickstart_script_lists_match_current_script_inventory() -> None:
    expected_powershell = sorted(
        f"powershell/{path.name}" for path in (ROOT / "scripts" / "powershell").glob("*.ps1")
    )
    expected_bash = sorted(f"bash/{path.name}" for path in (ROOT / "scripts" / "bash").glob("*.sh"))

    for path in sorted((ROOT / "quickstart").glob("devspark_quickstart_*.md")):
        text = path.read_text(encoding="utf-8")
        powershell = sorted(re.findall(r"^- `(powershell/[^`]+\.ps1)`", text, re.MULTILINE))
        bash = sorted(re.findall(r"^- `(bash/[^`]+\.sh)`", text, re.MULTILINE))
        assert powershell == expected_powershell, f"{path.name} PowerShell script list is stale"
        assert bash == expected_bash, f"{path.name} Bash script list is stale"


def test_quickstarts_include_current_template_surfaces() -> None:
    required_root_templates = {
        "agent-file-template.md",
        "checklist-template.md",
        "command-preamble-contract.md",
        "plan-template.md",
        "quick-spec-template.md",
        "rationale-template.md",
        "README.md",
        "spec-template.md",
        "spec-validation-contract.md",
        "tasks-template.md",
    }
    required_subdirectories = {"knowledge/", "prompts/", "risk-checklists/", "schemas/", "skills/"}

    for path in sorted((ROOT / "quickstart").glob("devspark_quickstart_*.md")):
        text = path.read_text(encoding="utf-8")
        for template in required_root_templates:
            assert f"`{template}`" in text, f"{path.name} must include {template}"
        for directory in required_subdirectories:
            assert f"`{directory}`" in text, f"{path.name} must fetch templates/{directory} recursively"


def test_quickstarts_are_only_devspark_maintenance_path() -> None:
    forbidden = [
        "devspark " + "init",
        "devspark " + "upgrade",
        "devspark-" + "cli",
        "templates/commands/" + "upgrade.md",
        "/devspark." + "upgrade",
    ]

    for path in sorted((ROOT / "quickstart").glob("devspark_quickstart_*.md")):
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden:
            assert phrase not in text, f"{path.name} must not reference {phrase}"
