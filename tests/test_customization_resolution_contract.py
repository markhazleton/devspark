# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for customization resolution through the consumer skills.

A consumer skill resolves the command prompt in order: developer override, team override, stock
default. The first existing file wins and override filenames stay dotted. Existing developer and
team overrides keep working without any edit.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import tests.legacy_retirement_oracle as oracle
from tests.consumer_skill_helpers import (
    CONSUMER_SKILLS,
    ROOT,
    commands,
    consumer_skill,
    expected_resolution,
    first_existing,
    resolution_paths,
    split_skill,
)

UPGRADE = ROOT / "tests" / "fixtures" / "upgrade"
SAMPLE = ("specify", "next", "implement")
GIT_USER = "jdoe"


def _write(tree: Path, relative: str, text: str) -> None:
    target = tree / relative.replace("{git-user}", GIT_USER)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _paths(command: str) -> list[str]:
    path = consumer_skill(command, CONSUMER_SKILLS)
    assert path.is_file(), f"{command} consumer skill is not generated"
    _, body = split_skill(path.read_text(encoding="utf-8"))
    return resolution_paths(body, command)


def test_resolution_helper_picks_the_first_existing_layer(tmp_path: Path) -> None:
    paths = expected_resolution("specify")
    assert first_existing(paths, tmp_path, GIT_USER) is None
    for layer in reversed(paths):
        _write(tmp_path, layer, "x")
        assert first_existing(paths, tmp_path, GIT_USER) == layer


@pytest.mark.parametrize("command", SAMPLE)
def test_skill_lists_the_three_layers_in_order_with_dotted_override_names(command: str) -> None:
    paths = _paths(command)
    assert paths == expected_resolution(command)
    for path in paths:
        assert path.rsplit("/", 1)[1] == f"devspark.{command}.md"


@pytest.mark.parametrize("command", SAMPLE)
def test_each_layer_wins_in_turn_and_removing_it_falls_through(tmp_path: Path, command: str) -> None:
    paths = _paths(command)
    developer, team, default = paths
    for layer in paths:
        _write(tmp_path, layer, layer)
    assert first_existing(paths, tmp_path, GIT_USER) == developer
    (tmp_path / developer.replace("{git-user}", GIT_USER)).unlink()
    assert first_existing(paths, tmp_path, GIT_USER) == team
    (tmp_path / team).unlink()
    assert first_existing(paths, tmp_path, GIT_USER) == default
    (tmp_path / default).unlink()
    assert first_existing(paths, tmp_path, GIT_USER) is None


def test_every_consumer_skill_resolves_the_same_three_layers() -> None:
    generated = {c for c in commands() if consumer_skill(c, CONSUMER_SKILLS).is_file()}
    assert generated == set(commands()), "consumer skills missing"
    for command in generated:
        assert _paths(command) == expected_resolution(command), command


def test_personalize_still_writes_the_developer_override_at_the_dotted_path() -> None:
    text = (ROOT / "templates" / "commands" / "personalize.md").read_text(encoding="utf-8")
    assert ".devspark.work/{git-user}/commands/devspark.{command}.md" in text


def test_existing_overrides_are_untouched_by_the_upgrade(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    for source in (UPGRADE / "_common", UPGRADE / "customized"):
        shutil.copytree(source, root, dirs_exist_ok=True)
    overrides = sorted((root / ".devspark.work").rglob("devspark.*.md"))
    assert overrides, "fixture must carry developer and team overrides"
    before = {p: p.read_bytes() for p in overrides}
    oracle.apply(root)
    for path, data in before.items():
        assert path.read_bytes() == data, path
    relative = {p.relative_to(root).as_posix() for p in overrides}
    assert ".devspark.work/commands/devspark.specify.md" in relative
    assert ".devspark.work/jdoe/commands/devspark.next.md" in relative
