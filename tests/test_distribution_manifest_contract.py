# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for how skills are distributed: the published install index and the packages.

The install index and the per-agent packages must agree on what a consumer receives. Copilot
receives skills (and no prompt or agent shims); the other agents receive hyphenated entry points;
data paths such as override and default command files stay dotted.
"""

from __future__ import annotations

import re
import subprocess
import tomllib
import zipfile
from pathlib import Path

import pytest

from tests.conftest import INDEX_TIMEOUT, _extract_function
from tests.consumer_skill_helpers import ROOT, bash_path, commands

SKILL_CATEGORY = "skill"
SKILL_DEST_DIR = ".github/skills"


def test_index_never_publishes_python_bytecode(tmp_path: Path) -> None:
    bash = bash_path()
    if bash is None:
        pytest.skip("bash not available")
    (tmp_path / "scripts" / "__pycache__").mkdir(parents=True)
    (tmp_path / "templates").mkdir()
    (tmp_path / "agents-registry.json").write_text("{}", encoding="utf-8")
    (tmp_path / "scripts" / "tool.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "scripts" / "__pycache__" / "tool.cpython-311.pyc").write_bytes(b"\x00")
    function = _extract_function((ROOT / "azure-pipelines.yml").read_text(encoding="utf-8"), "build_install_index")
    script = tmp_path / "index.sh"
    script.write_bytes((function + "\nbuild_install_index\n").encode("utf-8"))
    result = subprocess.run(
        [bash, str(script)], cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", timeout=INDEX_TIMEOUT
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "scripts/tool.py" in result.stdout
    assert "__pycache__" not in result.stdout and ".pyc" not in result.stdout


def _zip_names(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        return sorted(n for n in archive.namelist() if not n.endswith("/"))


def test_index_still_maps_every_command_to_its_dotted_default(install_index) -> None:
    command_rows = {(s, d) for s, d, c in install_index.rows if c == "command"}
    assert command_rows == {
        (f"templates/commands/{n}.md", f".devspark/defaults/commands/devspark.{n}.md") for n in commands()
    }
    assert len(command_rows) == 39


def test_index_categories_are_a_known_closed_set(install_index) -> None:
    assert {c for _, _, c in install_index.rows} <= {"command", "template", "script", "registry", SKILL_CATEGORY}


def test_index_installs_each_consumer_skill_into_the_skills_directory(install_index) -> None:
    skill_rows = {(s, d) for s, d, c in install_index.rows if c == SKILL_CATEGORY}
    assert skill_rows == {
        (
            f"templates/consumer-skills/devspark-{n}/SKILL.md",
            f"{SKILL_DEST_DIR}/devspark-{n}/SKILL.md",
        )
        for n in commands()
    }
    assert len(skill_rows) == 39


def test_index_never_places_consumer_skills_under_the_templates_data_tree(install_index) -> None:
    assert any(c == SKILL_CATEGORY for _, _, c in install_index.rows), "no skill entries published"
    offenders = [d for s, d, c in install_index.rows if c != SKILL_CATEGORY and "consumer-skills" in (s + d)]
    assert offenders == []
    assert not any(d.startswith(".devspark/templates/consumer-skills") for _, d, _ in install_index.rows)


def test_index_skill_sources_exist_in_the_repository(install_index) -> None:
    sources = [s for s, _, c in install_index.rows if c == SKILL_CATEGORY]
    assert sources, "no skill entries published"
    for source in sources:
        assert (install_index.work / source).is_file()


def test_copilot_package_still_contains_the_registry_and_core_data(package_build) -> None:
    names = _zip_names(package_build.zips["copilot"])
    assert ".devspark/defaults/commands/devspark.specify.md" in names
    assert any(n.startswith(".devspark/scripts/") for n in names)


def test_copilot_package_ships_skills_and_no_shims(package_build) -> None:
    names = _zip_names(package_build.zips["copilot"])
    skills = sorted(n for n in names if n.startswith(f"{SKILL_DEST_DIR}/"))
    assert skills == sorted(f"{SKILL_DEST_DIR}/devspark-{n}/SKILL.md" for n in commands())
    assert not any(n.startswith((".github/prompts/", ".github/agents/")) for n in names)


def test_package_never_exposes_consumer_skills_as_template_data(package_build) -> None:
    for agent, zip_path in package_build.zips.items():
        names = _zip_names(zip_path)
        assert not any("consumer-skills" in n for n in names), agent
    names = _zip_names(package_build.zips["copilot"])
    assert any(n.startswith(f"{SKILL_DEST_DIR}/") for n in names), "skills missing from package"


def test_md_and_toml_packages_use_hyphenated_entry_points_and_dotted_data(package_build) -> None:
    md = _zip_names(package_build.zips["claude"])
    toml = _zip_names(package_build.zips["gemini"])
    assert ".claude/commands/devspark-specify.md" in md
    assert ".gemini/commands/devspark-specify.toml" in toml
    assert not any(n.startswith(".claude/commands/devspark.") for n in md)
    assert not any(n.startswith(".gemini/commands/devspark.") for n in toml)
    assert ".devspark/defaults/commands/devspark.specify.md" in md
    assert ".devspark/defaults/commands/devspark.specify.md" in toml


def test_toml_entry_points_parse_and_keep_the_template_description(package_build) -> None:
    with zipfile.ZipFile(package_build.zips["gemini"]) as archive:
        for name in commands():
            entry = tomllib.loads(archive.read(f".gemini/commands/devspark-{name}.toml").decode("utf-8"))
            template = (ROOT / "templates" / "commands" / f"{name}.md").read_text(encoding="utf-8")
            expected = re.search(r"(?m)^description:\s*(.+)$", template).group(1).rstrip("\r")
            assert entry["description"] == expected, name


def test_manifest_installed_and_package_installed_skills_are_byte_identical(package_build, install_index) -> None:
    skill_rows = [(s, d) for s, d, c in install_index.rows if c == SKILL_CATEGORY]
    assert skill_rows, "no skill entries published"
    with zipfile.ZipFile(package_build.zips["copilot"]) as archive:
        for source, dest in skill_rows:
            assert (install_index.work / source).read_bytes() == archive.read(dest)
