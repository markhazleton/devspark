"""Contract tests for atomic-prompt frontmatter (contracts/atomic-prompt-frontmatter.md)."""

from __future__ import annotations

from pathlib import Path

import pytest

from devspark_cli.runner.loader import (
    AP_AUDIENCE_INVALID,
    AP_CATEGORY_REQUIRED,
    AP_DESC_INVALID,
    AP_EXPOSED_INVALID,
    AP_FRONTMATTER_MISSING,
    AP_ID_INVALID,
    AP_INPUTS_INVALID,
    AP_LEGACY_UNKNOWN,
    AP_NAME_REQUIRED,
    AP_OUTPUTS_INVALID,
    ValidationError,
    parse_atomic_prompt,
    validate_atomic_prompt,
)


def _write(tmp: Path, name: str, content: str) -> Path:
    p = tmp / name
    p.write_text(content, encoding="utf-8")
    return p


_GOOD = """---
id: capture-context
name: Capture Context
audience: intermediate
exposed: false
category: improvement
description: Gather situational context for an improvement proposal.
inputs:
  - user_input
outputs:
  - context.summary
legacy_command: null
---

## Outline

body
"""


def test_parses_good_frontmatter(tmp_path: Path) -> None:
    path = _write(tmp_path, "capture-context.md", _GOOD)
    p = parse_atomic_prompt(path)
    validate_atomic_prompt(p)
    assert p.id == "capture-context"
    assert p.exposed is False
    assert p.inputs == ["user_input"]
    assert p.outputs == ["context.summary"]


def test_missing_frontmatter(tmp_path: Path) -> None:
    path = _write(tmp_path, "x.md", "no frontmatter\n")
    with pytest.raises(ValidationError) as exc:
        parse_atomic_prompt(path)
    assert exc.value.code == AP_FRONTMATTER_MISSING


def test_id_invalid(tmp_path: Path) -> None:
    bad = _GOOD.replace("id: capture-context", "id: BadId")
    path = _write(tmp_path, "BadId.md", bad)
    p = parse_atomic_prompt(path)
    with pytest.raises(ValidationError) as exc:
        validate_atomic_prompt(p)
    assert exc.value.code == AP_ID_INVALID


def test_id_filename_mismatch(tmp_path: Path) -> None:
    path = _write(tmp_path, "other-name.md", _GOOD)
    p = parse_atomic_prompt(path)
    with pytest.raises(ValidationError) as exc:
        validate_atomic_prompt(p)
    assert exc.value.code == AP_ID_INVALID


def test_name_required(tmp_path: Path) -> None:
    bad = _GOOD.replace("name: Capture Context", "name: ''")
    path = _write(tmp_path, "capture-context.md", bad)
    p = parse_atomic_prompt(path)
    with pytest.raises(ValidationError) as exc:
        validate_atomic_prompt(p)
    assert exc.value.code == AP_NAME_REQUIRED


def test_audience_invalid(tmp_path: Path) -> None:
    bad = _GOOD.replace("audience: intermediate", "audience: wizard")
    path = _write(tmp_path, "capture-context.md", bad)
    p = parse_atomic_prompt(path)
    with pytest.raises(ValidationError) as exc:
        validate_atomic_prompt(p)
    assert exc.value.code == AP_AUDIENCE_INVALID


def test_exposed_must_be_bool(tmp_path: Path) -> None:
    bad = _GOOD.replace("exposed: false", "exposed: 'yes'")
    path = _write(tmp_path, "capture-context.md", bad)
    p = parse_atomic_prompt(path)
    with pytest.raises(ValidationError) as exc:
        validate_atomic_prompt(p)
    assert exc.value.code == AP_EXPOSED_INVALID


def test_category_required(tmp_path: Path) -> None:
    bad = _GOOD.replace("category: improvement", "category: ''")
    path = _write(tmp_path, "capture-context.md", bad)
    p = parse_atomic_prompt(path)
    with pytest.raises(ValidationError) as exc:
        validate_atomic_prompt(p)
    assert exc.value.code == AP_CATEGORY_REQUIRED


def test_description_too_long(tmp_path: Path) -> None:
    bad = _GOOD.replace(
        "description: Gather situational context for an improvement proposal.",
        "description: " + "x" * 250,
    )
    path = _write(tmp_path, "capture-context.md", bad)
    p = parse_atomic_prompt(path)
    with pytest.raises(ValidationError) as exc:
        validate_atomic_prompt(p)
    assert exc.value.code == AP_DESC_INVALID


def test_inputs_must_be_list(tmp_path: Path) -> None:
    bad = _GOOD.replace("inputs:\n  - user_input", "inputs: 42")
    path = _write(tmp_path, "capture-context.md", bad)
    p = parse_atomic_prompt(path)
    with pytest.raises(ValidationError) as exc:
        validate_atomic_prompt(p)
    assert exc.value.code == AP_INPUTS_INVALID


def test_outputs_must_be_list(tmp_path: Path) -> None:
    bad = _GOOD.replace("outputs:\n  - context.summary", "outputs: 7")
    path = _write(tmp_path, "capture-context.md", bad)
    p = parse_atomic_prompt(path)
    with pytest.raises(ValidationError) as exc:
        validate_atomic_prompt(p)
    assert exc.value.code == AP_OUTPUTS_INVALID


def test_legacy_command_unknown(tmp_path: Path) -> None:
    bad = _GOOD.replace("legacy_command: null", "legacy_command: nope")
    path = _write(tmp_path, "capture-context.md", bad)
    p = parse_atomic_prompt(path)
    cmds = tmp_path / "commands"
    cmds.mkdir()
    with pytest.raises(ValidationError) as exc:
        validate_atomic_prompt(p, commands_dir=cmds)
    assert exc.value.code == AP_LEGACY_UNKNOWN


# ---------------------------------------------------------------------------
# Positive 1:1 coverage assertion (T013): every templates/commands/*.md
# has a corresponding atomic-prompt shim with matching legacy_command.
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_every_command_has_atomic_shim() -> None:
    commands_dir = REPO_ROOT / "templates" / "commands"
    atomic_dir = REPO_ROOT / "templates" / "prompts" / "atomic"
    if not commands_dir.is_dir() or not atomic_dir.is_dir():
        pytest.skip("commands or atomic dir missing")

    commands = sorted(p.stem for p in commands_dir.glob("*.md") if not p.name.startswith("_"))
    if not commands:
        pytest.skip("no commands present")

    missing: list[str] = []
    bad_legacy: list[str] = []
    for cmd in commands:
        shim = atomic_dir / f"{cmd}.md"
        if not shim.is_file():
            missing.append(cmd)
            continue
        prompt = parse_atomic_prompt(shim)
        if prompt.legacy_command != cmd:
            bad_legacy.append(f"{cmd}: legacy_command={prompt.legacy_command!r}")

    assert not missing, f"missing atomic shims: {missing}"
    assert not bad_legacy, f"shims with wrong legacy_command: {bad_legacy}"
