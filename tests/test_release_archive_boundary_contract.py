"""Contracts for the release-owned DevSpark archival boundary."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_redundant_archive_surface_is_removed() -> None:
    removed_command = "har" + "vest"
    removed = (
        f"templates/commands/{removed_command}.md",
        f"templates/prompts/atomic/{removed_command}.md",
        f"scripts/bash/{removed_command}.sh",
        f"scripts/powershell/{removed_command}.ps1",
        f".claude/commands/devspark.{removed_command}.md",
        f".github/prompts/devspark.{removed_command}.prompt.md",
        f".github/agents/devspark.{removed_command}.agent.md",
        f".knowledge/entities/product-documentation/site/{removed_command}-usage.md",
    )
    assert not [path for path in removed if (ROOT / path).exists()]


def test_release_is_the_archive_boundary() -> None:
    release = _read("templates/commands/release.md")
    implement = _read("templates/commands/implement.md")
    verify = _read("templates/commands/verify.md")

    assert "Release is the only DevSpark command that writes to `.archive/`" in release
    assert "code_ref" in release
    assert "test_ref" in release
    assert "knowledge_ref" in release
    assert "Implementation never writes to `.archive/`" in implement
    assert "never archives a work package" in verify

    for path in (ROOT / "templates" / "commands").glob("*.md"):
        if path.name == "release.md":
            continue
        text = path.read_text(encoding="utf-8")
        assert "archive_devspark_work_path" not in text
        assert "Move-DevSparkWorkPathToArchive" not in text


def test_task_contract_includes_code_test_and_knowledge_linkage() -> None:
    task_template = _read("templates/tasks-template.md")
    schema = json.loads(_read("templates/schemas/devspark-task-linkage.schema.json"))

    for field in ("code_ref", "test_ref", "knowledge_ref"):
        assert f"- {field}: TODO" in task_template
        assert field in schema["required"]


def test_release_prescan_rejects_missing_or_unexplained_linkage(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".devspark").mkdir()
    (tmp_path / ".devspark" / "VERSION").write_text("version: 4.1.0\n", encoding="utf-8")
    specs = tmp_path / ".devspark.work" / "specs"

    missing = specs / "001-missing"
    missing.mkdir(parents=True)
    (missing / "tasks.md").write_text("- [X] T001 Change code\n", encoding="utf-8")

    unexplained = specs / "002-unexplained"
    unexplained.mkdir()
    (unexplained / "tasks.md").write_text(
        "- [X] T001 Change docs\n"
        "  - code_ref: n/a\n"
        "  - test_ref: n/a\n"
        "  - knowledge_ref: .knowledge/entities/docs/architecture.md\n",
        encoding="utf-8",
    )

    eligible = specs / "003-eligible"
    eligible.mkdir()
    (eligible / "tasks.md").write_text(
        "- [X] T001 Change code\n"
        "  - code_ref: src/example.py\n"
        "  - test_ref: tests/test_example.py\n"
        "  - knowledge_ref: n/a — behavior is fully described by existing knowledge\n",
        encoding="utf-8",
    )

    if sys.platform == "win32":
        command = [
            "pwsh",
            "-NoProfile",
            "-File",
            str(ROOT / "scripts/powershell/release-context.ps1"),
            "-Json",
        ]
    else:
        command = ["bash", str(ROOT / "scripts/bash/release-context.sh"), "--json"]

    result = subprocess.run(
        command,
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["RELEASE_ELIGIBLE_WORK_PACKAGES"] == ["003-eligible"]
    assert sorted(payload["BLOCKED_WORK_PACKAGES"]) == ["001-missing", "002-unexplained"]
