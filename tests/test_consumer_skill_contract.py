# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for the published consumer skills and the generator that produces them.

Every stock command ships one `templates/consumer-skills/devspark-<command>/SKILL.md`. A consumer
skill is a thin, generated entry point: fixed frontmatter, a fixed path-free marker, the developer,
team, default resolution instruction over the existing override filenames, and pass-through of the
text typed after the skill name. It never carries source-repository routing or STOP text.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from tests.consumer_skill_helpers import (
    CONSUMER_KEYS,
    CONSUMER_SKILLS,
    PLANNING_ID,
    SKILL_MARKER,
    bash_path,
    commands,
    consumer_skill,
    copy_generation_repo,
    expected_resolution,
    resolution_paths,
    run_generator,
    split_skill,
    template_description,
    tree_bytes,
)

BOTH_SHELLS = pytest.mark.skipif(bash_path() is None or shutil.which("pwsh") is None, reason="both shells required")
FORBIDDEN_TEXT = ("templates/", ".github/agents", "STOP", "source repository")


@pytest.fixture(scope="module")
def generated(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Run each generator twin once on its own copy of the generator inputs."""
    repos: dict[str, Path] = {}
    for shell in ("bash", "pwsh"):
        repo = copy_generation_repo(tmp_path_factory.mktemp(f"consumer-{shell}") / "repo")
        result = run_generator(shell, repo)
        assert result.returncode == 0, result.stdout + result.stderr
        repos[shell] = repo
    return repos


def test_one_skill_folder_per_stock_command() -> None:
    cmds = commands()
    assert len(cmds) == 38
    folders = {p.name for p in CONSUMER_SKILLS.glob("devspark-*") if p.is_dir()}
    assert folders == {f"devspark-{c}" for c in cmds}
    for command in cmds:
        assert [p.name for p in consumer_skill(command).parent.iterdir()] == ["SKILL.md"]


@pytest.mark.parametrize("command", commands())
def test_frontmatter_is_exactly_the_four_documented_keys(command: str) -> None:
    skill = consumer_skill(command)
    assert skill.is_file(), f"missing {skill}"
    frontmatter, _ = split_skill(skill.read_text(encoding="utf-8"))
    assert set(frontmatter) == CONSUMER_KEYS
    assert "handoffs" not in frontmatter
    assert frontmatter["name"] == skill.parent.name == f"devspark-{command}"
    assert frontmatter["description"] == template_description(command)
    assert frontmatter["user-invocable"] is True
    assert frontmatter["disable-model-invocation"] is True


@pytest.mark.parametrize("command", commands())
def test_body_has_marker_resolution_order_and_input_pass_through(command: str) -> None:
    skill = consumer_skill(command)
    assert skill.is_file(), f"missing {skill}"
    _, body = split_skill(skill.read_text(encoding="utf-8"))
    assert body.count(SKILL_MARKER) == 1
    assert body.lstrip("\n").startswith(SKILL_MARKER)
    assert resolution_paths(body, command) == expected_resolution(command)
    lowered = body.lower()
    assert "first" in lowered and "exist" in lowered, "resolution must say the first existing file wins"
    assert "typed" in lowered or "user input" in lowered or "arguments" in lowered
    assert "pass" in lowered or "as the command input" in lowered


@pytest.mark.parametrize("command", commands())
def test_consumer_skill_contains_no_forbidden_content(command: str) -> None:
    skill = consumer_skill(command)
    assert skill.is_file(), f"missing {skill}"
    text = skill.read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_TEXT:
        assert forbidden not in text, forbidden
    assert PLANNING_ID.search(text) is None


@BOTH_SHELLS
def test_generator_twins_emit_identical_consumer_skills(generated: dict[str, Path]) -> None:
    outputs = {shell: tree_bytes(repo / "templates" / "consumer-skills") for shell, repo in generated.items()}
    assert len(outputs["bash"]) == 38, sorted(outputs["bash"])
    assert outputs["bash"] == outputs["pwsh"]
    for command in commands():
        committed = consumer_skill(command)
        assert committed.read_bytes() == outputs["bash"][f"devspark-{command}/SKILL.md"]


@pytest.mark.parametrize("shell", ["bash", "pwsh"])
def test_check_fails_on_a_mutated_consumer_skill(shell: str, generated: dict[str, Path], tmp_path: Path) -> None:
    if shell == "bash" and bash_path() is None or shell == "pwsh" and shutil.which("pwsh") is None:
        pytest.skip(f"{shell} not available")
    repo = tmp_path / "repo"
    shutil.copytree(generated[shell], repo)
    skill = consumer_skill("specify", repo / "templates" / "consumer-skills")
    assert skill.is_file(), "generator did not emit the specify consumer skill"
    assert run_generator(shell, repo, check=True).returncode == 0
    original = skill.read_bytes()
    skill.write_bytes(original + b"hand edit\n")
    result = run_generator(shell, repo, check=True)
    assert result.returncode == 1 and "devspark-specify" in result.stdout
    assert skill.read_bytes() == original + b"hand edit\n", "check must not write"


def _fixture_repo(tmp_path: Path, *, with_description: bool, stop_for: str | None) -> Path:
    repo = tmp_path / "repo"
    for rel in ("scripts/bash", "scripts/powershell"):
        shutil.copytree(Path(__file__).resolve().parent.parent / rel, repo / rel, ignore=shutil.ignore_patterns("__pycache__"))
    commands_dir = repo / "templates" / "commands"
    commands_dir.mkdir(parents=True)
    description = "description: Alpha command.\n" if with_description else ""
    (commands_dir / "alpha.md").write_bytes(f"---\n{description}---\n\nBody\n".encode("utf-8"))
    (commands_dir / "personalize.md").write_bytes(b"---\ndescription: Personalize.\n---\n\nBody\n")
    agents = repo / ".github" / "agents"
    agents.mkdir(parents=True)
    for name in ("alpha", "personalize"):
        (agents / f"devspark.{name}.agent.md").write_bytes(
            f"---\nname: devspark.{name}\ndescription: x\n---\n\nRead and follow `templates/commands/{name}.md`.\n".encode("utf-8")
        )
    stops = repo / "eng" / "skills" / "source-stop"
    stops.mkdir(parents=True)
    if stop_for:
        (stops / f"{stop_for}.md").write_bytes(b"**STOP - source repository.**\n")
    return repo


@pytest.mark.parametrize("shell", ["bash", "pwsh"])
def test_generator_fails_fast_when_a_template_lacks_a_description(shell: str, tmp_path: Path) -> None:
    if shell == "bash" and bash_path() is None or shell == "pwsh" and shutil.which("pwsh") is None:
        pytest.skip(f"{shell} not available")
    repo = _fixture_repo(tmp_path, with_description=False, stop_for="personalize")
    result = run_generator(shell, repo)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "alpha" in result.stdout + result.stderr
    assert tree_bytes(repo / "templates" / "consumer-skills") == {}


@pytest.mark.parametrize("shell", ["bash", "pwsh"])
def test_generator_fails_fast_when_a_source_stop_body_is_missing(shell: str, tmp_path: Path) -> None:
    if shell == "bash" and bash_path() is None or shell == "pwsh" and shutil.which("pwsh") is None:
        pytest.skip(f"{shell} not available")
    repo = _fixture_repo(tmp_path, with_description=True, stop_for=None)
    result = run_generator(shell, repo)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "personalize" in result.stdout + result.stderr
    assert tree_bytes(repo / "templates" / "consumer-skills") == {}
    assert tree_bytes(repo / ".github" / "skills") == {}
