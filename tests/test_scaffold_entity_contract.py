# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for scripts/scaffold-entity.py (assisted _entity.yaml + layer doc drafting)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "scripts" / "scaffold-entity.py"
INDEX_ENGINE = ROOT / "scripts" / "build_knowledge_index.py"


def _run(repo: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(ENGINE),
            "--repo-root",
            str(repo),
            "--entity-id",
            "widget",
            "--type",
            "subsystem",
            "--owner",
            "team-x",
            "--source",
            "src/widget.py",
            "--layer",
            "architecture",
            *extra_args,
        ],
        text=True,
        capture_output=True,
    )


def _seed_source(repo: Path, docstring: str | None = "Widget module docstring.") -> None:
    src = repo / "src" / "widget.py"
    src.parent.mkdir(parents=True, exist_ok=True)
    if docstring:
        src.write_text(f'"""{docstring}"""\n\nclass Widget:\n    pass\n', encoding="utf-8")
    else:
        src.write_text("class Widget:\n    pass\n", encoding="utf-8")


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    _seed_source(tmp_path)
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / ".knowledge/entities/widget/_entity.yaml").exists()
    assert "DRY RUN" in result.stdout


def test_write_creates_entity_yaml_and_layer_doc(tmp_path: Path) -> None:
    _seed_source(tmp_path)
    result = _run(tmp_path, "--write")
    assert result.returncode == 0, result.stderr
    entity_yaml = tmp_path / ".knowledge/entities/widget/_entity.yaml"
    layer_doc = tmp_path / ".knowledge/entities/widget/architecture.md"
    assert entity_yaml.read_text(encoding="utf-8") == "id: widget\ntype: subsystem\nowner: team-x\n"
    assert "Widget module docstring." in layer_doc.read_text(encoding="utf-8")


def test_overwrite_without_force_is_refused(tmp_path: Path) -> None:
    _seed_source(tmp_path)
    first = _run(tmp_path, "--write")
    assert first.returncode == 0, first.stderr
    second = _run(tmp_path, "--write")
    assert second.returncode != 0
    assert "already exists" in str(second.stderr) + str(second.stdout)


def test_overwrite_with_force_succeeds(tmp_path: Path) -> None:
    _seed_source(tmp_path)
    assert _run(tmp_path, "--write").returncode == 0
    result = _run(tmp_path, "--write", "--force")
    assert result.returncode == 0, result.stderr


def test_invalid_layer_is_rejected(tmp_path: Path) -> None:
    _seed_source(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(ENGINE),
            "--repo-root",
            str(tmp_path),
            "--entity-id",
            "widget",
            "--type",
            "subsystem",
            "--owner",
            "team-x",
            "--source",
            "src/widget.py",
            "--layer",
            "not-a-real-layer",
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "layer must be one of" in result.stdout


def test_nonexistent_source_is_rejected(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "does not exist" in result.stdout


def test_forbidden_reference_source_is_rejected(tmp_path: Path) -> None:
    forbidden = tmp_path / ".devspark.work/specs/001-foo/plan.md"
    forbidden.parent.mkdir(parents=True, exist_ok=True)
    forbidden.write_text("plan\n", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ENGINE),
            "--repo-root",
            str(tmp_path),
            "--entity-id",
            "widget",
            "--type",
            "subsystem",
            "--owner",
            "team-x",
            "--source",
            ".devspark.work/specs/001-foo/plan.md",
            "--layer",
            "architecture",
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert ".devspark.work/ or .archive/" in result.stdout


def test_docstring_extraction_falls_back_to_placeholder_when_absent(tmp_path: Path) -> None:
    _seed_source(tmp_path, docstring=None)
    result = _run(tmp_path, "--write")
    assert result.returncode == 0, result.stderr
    layer_doc = tmp_path / ".knowledge/entities/widget/architecture.md"
    assert "TODO: describe current behavior here" in layer_doc.read_text(encoding="utf-8")


def test_written_output_passes_build_knowledge_index_validation(tmp_path: Path) -> None:
    _seed_source(tmp_path)
    assert _run(tmp_path, "--write").returncode == 0
    result = subprocess.run(
        [sys.executable, str(INDEX_ENGINE), "--repo-root", str(tmp_path), "--stdout"],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    index = json.loads(result.stdout)
    assert any(node.get("entity") == "widget" for node in index["nodes"])
