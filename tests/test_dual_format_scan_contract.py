# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests that no artifact the framework ships can re-create the dual command format.

A "dual-format" artifact is one that lets a consumer end up with both the old dotted entry points
and the new hyphenated ones: a dotted entry-point file, a prompt companion, or text that names a
legacy-mode switch or a migration marker/flag. The scans below cover generator output, the
published packages and the install index destinations.

Entry-point rule: a file is an entry point when it sits outside the data trees (`.devspark/`,
`.devspark.work/`, `.knowledge/`, `.archive/`, `templates/commands/`) and either has a basename
starting with `devspark.`, ends in `.prompt.md`, or lives under `.github/agents/`.
"""

from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

import pytest

import tests.legacy_retirement_oracle as oracle
from tests.consumer_skill_helpers import (
    bash_path,
    copy_generation_repo,
    run_generator,
    tree_bytes,
)

UPGRADE = Path(__file__).resolve().parent / "fixtures" / "upgrade"

DATA_TREES = (".devspark/", ".devspark.work/", ".knowledge/", ".archive/", "templates/commands/")
# Assignment-form keys only, so prose such as "no migration marker is written" never matches.
MODE_KEY = re.compile(
    r"(?im)^\s*[\"']?(?:legacy[_-]?command[s]?|(?:legacy|compat(?:ibility)?)[_-]?(?:mode|switch|flag))[\"']?\s*[:=]"
)
MIGRATION_KEY = re.compile(r"(?im)^\s*[\"']?migration[_-]?(?:marker|state|flag|done)[\"']?\s*[:=]")
TEXT_SUFFIXES = (".md", ".toml", ".json", ".yml", ".yaml", ".sh", ".ps1", ".py", ".txt")


def is_entry_point(rel: str) -> bool:
    if rel.startswith(DATA_TREES):
        return False
    name = rel.rsplit("/", 1)[-1]
    return name.startswith("devspark.") or name.endswith(".prompt.md") or rel.startswith(".github/agents/")


def mode_or_marker_hits(rel: str, text: str) -> list[str]:
    return [f"{rel}: {m.group(0).strip()}" for rx in (MODE_KEY, MIGRATION_KEY) for m in rx.finditer(text)]


def _zip_text(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as archive:
        return {
            n: archive.read(n).decode("utf-8", errors="replace")
            for n in archive.namelist()
            if not n.endswith("/") and n.endswith(TEXT_SUFFIXES)
        }


def test_entry_point_rule_classifies_representative_paths() -> None:
    assert is_entry_point(".github/agents/devspark.specify.agent.md")
    assert is_entry_point(".github/prompts/devspark.specify.prompt.md")
    assert is_entry_point(".claude/commands/devspark.specify.md")
    assert is_entry_point(".gemini/commands/devspark.specify.toml")
    assert not is_entry_point(".claude/commands/devspark-specify.md")
    assert not is_entry_point(".github/skills/devspark-specify/SKILL.md")
    assert not is_entry_point(".devspark/defaults/commands/devspark.specify.md")
    assert not is_entry_point(".devspark.work/commands/devspark.specify.md")
    assert not is_entry_point("templates/commands/specify.md")


def test_mode_and_marker_patterns_match_assignments_not_prose() -> None:
    assert mode_or_marker_hits("x", "legacy_command: true\n")
    assert mode_or_marker_hits("x", "compat-mode = on\n")
    assert mode_or_marker_hits("x", 'migration_marker: "done"\n')
    assert not mode_or_marker_hits("x", "No migration marker or flag is written; the upgrade is stateless.\n")
    assert not mode_or_marker_hits("x", "There is no legacy mode.\n")


def test_install_index_destinations_contain_no_dotted_entry_points(install_index) -> None:
    offenders = [d for _, d, _ in install_index.rows if is_entry_point(d)]
    assert offenders == []
    assert not any(d.endswith(".prompt.md") for _, d, _ in install_index.rows)


@pytest.mark.parametrize("agent", ["copilot", "claude", "gemini"])
def test_packages_contain_no_dotted_entry_points(agent: str, package_build) -> None:
    with zipfile.ZipFile(package_build.zips[agent]) as archive:
        names = [n for n in archive.namelist() if not n.endswith("/")]
    assert [n for n in names if is_entry_point(n)] == []


@pytest.mark.parametrize("agent", ["copilot", "claude", "gemini"])
def test_packages_carry_no_legacy_mode_switch_or_migration_marker(agent: str, package_build) -> None:
    hits = [h for rel, text in _zip_text(package_build.zips[agent]).items() for h in mode_or_marker_hits(rel, text)]
    assert hits == []


@pytest.mark.parametrize("shell", ["bash", "pwsh"])
def test_generator_output_is_only_consumer_skills_and_source_skills(shell: str, tmp_path: Path) -> None:
    if shell == "bash" and bash_path() is None or shell == "pwsh" and shutil.which("pwsh") is None:
        pytest.skip(f"{shell} not available")
    repo = copy_generation_repo(tmp_path / "repo")
    before = tree_bytes(repo)
    result = run_generator(shell, repo)
    assert result.returncode == 0, result.stdout + result.stderr
    after = tree_bytes(repo)
    produced = sorted(rel for rel, data in after.items() if before.get(rel) != data)
    assert produced, "generator produced nothing"
    allowed = re.compile(r"^(?:\.github/skills|templates/consumer-skills)/devspark-[a-z0-9-]+/SKILL\.md$")
    assert [rel for rel in produced if not allowed.match(rel)] == []
    assert [rel for rel in produced if is_entry_point(rel)] == []
    assert any(rel.startswith("templates/consumer-skills/") for rel in produced)
    hits = [h for rel in produced for h in mode_or_marker_hits(rel, after[rel].decode("utf-8"))]
    assert hits == []


def test_extracting_the_copilot_package_over_a_retired_tree_recreates_nothing(tmp_path: Path, package_build) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    for source in (UPGRADE / "_common", UPGRADE / "plain-copilot"):
        shutil.copytree(source, root, dirs_exist_ok=True)
    assert oracle.apply(root).delete, "fixture must contain entry points to retire"
    with zipfile.ZipFile(package_build.zips["copilot"]) as archive:
        archive.extractall(root)
    again = oracle.plan(root)
    assert again.delete == [] and again.quarantine == [] and again.report == []
