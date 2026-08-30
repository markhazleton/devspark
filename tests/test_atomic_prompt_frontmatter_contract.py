"""Contract tests for atomic-prompt frontmatter."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


def _frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing frontmatter")
    _start, raw, _body = text.split("---", 2)
    parsed = yaml.safe_load(raw) or {}
    if not isinstance(parsed, dict):
        raise ValueError("frontmatter must be a mapping")
    return parsed


def test_every_command_has_atomic_shim() -> None:
    commands_dir = REPO_ROOT / "templates" / "commands"
    atomic_dir = REPO_ROOT / "templates" / "prompts" / "atomic"

    commands = sorted(p.stem for p in commands_dir.glob("*.md") if not p.name.startswith("_"))
    assert commands, "no command prompts present"

    missing: list[str] = []
    bad_legacy: list[str] = []
    for command in commands:
        shim = atomic_dir / f"{command}.md"
        if not shim.is_file():
            missing.append(command)
            continue
        data = _frontmatter(shim)
        if data.get("legacy_command") != command:
            bad_legacy.append(f"{command}: legacy_command={data.get('legacy_command')!r}")

    assert not missing, f"missing atomic shims: {missing}"
    assert not bad_legacy, f"shims with wrong legacy_command: {bad_legacy}"


@pytest.mark.parametrize("path", sorted((REPO_ROOT / "templates" / "prompts" / "atomic").glob("*.md")))
def test_atomic_prompt_frontmatter_shape(path: Path) -> None:
    data = _frontmatter(path)

    assert isinstance(data.get("id"), str) and data["id"] == path.stem
    assert isinstance(data.get("name"), str) and data["name"].strip()
    assert data.get("audience") in {"beginner", "intermediate", "expert"}
    assert isinstance(data.get("exposed"), bool)
    assert isinstance(data.get("category"), str) and data["category"].strip()
    assert isinstance(data.get("description"), str) and len(data["description"]) <= 200
    assert isinstance(data.get("inputs"), list)
    assert isinstance(data.get("outputs"), list)
