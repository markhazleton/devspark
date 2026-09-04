"""Contracts for the state-aware /devspark.next workflow navigator."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts/bash/next-context.sh"


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _run_next(repo: Path, *args: str, env: dict[str, str] | None = None) -> dict:
    completed = subprocess.run(
        ["bash", str(SCRIPT), *args, "--json"],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def _init_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "next@example.test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Next Contract"], cwd=tmp_path, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", "001-next-test"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text(".devspark.work/\n.test-bin/\n", encoding="utf-8")
    constitution = tmp_path / ".knowledge/governance/constitution.md"
    constitution.parent.mkdir(parents=True)
    constitution.write_text("# Constitution\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore", ".knowledge"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "test baseline"], cwd=tmp_path, check=True)
    return tmp_path


def _write_spec(repo: Path, *, status: str = "Draft") -> Path:
    feature = repo / ".devspark.work/specs/001-next-test"
    feature.mkdir(parents=True, exist_ok=True)
    (feature / "spec.md").write_text(
        "---\n"
        "required_gates: checklist, analyze, critic\n"
        "---\n\n"
        f"**Status**: {status}\n",
        encoding="utf-8",
    )
    return feature


def _write_gate(feature: Path, name: str, status: str = "pass", blocking: bool = False) -> None:
    gates = feature / "gates"
    gates.mkdir(exist_ok=True)
    (gates / f"{name}.md").write_text(
        f"gate: {name}\nstatus: {status}\nblocking: {str(blocking).lower()}\n",
        encoding="utf-8",
    )


def test_next_prompt_has_confirmation_auto_and_human_boundary_contracts() -> None:
    command = _read("templates/commands/next.md")
    assert "next-context.sh $ARGUMENTS --json" in command
    assert "next-context.ps1 $ARGUMENTS -Json" in command
    assert "ask exactly one yes/no confirmation" in command
    assert "Maximum 10 dispatched commands" in command
    assert "Re-run detection after every command" in command
    for boundary in ("branch creation", "commits", "pushes", "rebases", "branch sync", "merges"):
        assert boundary in command
    assert "/devspark.address-pr-review` is a commit boundary" in command
    assert "Release is deliberately not auto-appended after merge" in command


def test_next_surfaces_and_parity_scripts_are_present() -> None:
    expected = {
        ".claude/commands/devspark.next.md": "templates/commands/next.md",
        ".github/agents/devspark.next.agent.md": "templates/commands/next.md",
        ".github/prompts/devspark.next.prompt.md": "devspark.next",
        "templates/prompts/atomic/next.md": "templates/commands/next.md",
        ".knowledge/entities/product-documentation/site/next-usage.md": "/devspark.next",
    }
    for relative, token in expected.items():
        assert (ROOT / relative).is_file(), relative
        assert token in _read(relative)

    bash = _read("scripts/bash/next-context.sh")
    powershell = _read("scripts/powershell/next-context.ps1")
    for token in (
        "RECOMMENDED_COMMAND",
        "RECOMMENDATION_REASON",
        "SAFE_TO_AUTO",
        "HUMAN_BOUNDARY",
        "MANUAL_COMMAND",
        "READ_ONLY",
    ):
        assert token in bash
        assert token in powershell


@pytest.mark.skipif(
    any(shutil.which(tool) is None for tool in ("git", "jq", "rg")),
    reason="next-context smoke tests require git, jq, and rg",
)
def test_next_detects_spec_plan_tasks_gates_and_implementation(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    feature = _write_spec(repo)

    state = _run_next(repo)
    assert state["RECOMMENDED_COMMAND"] == "/devspark.plan"
    assert state["SAFE_TO_AUTO"] is True

    (feature / "plan.md").write_text("# Plan\n", encoding="utf-8")
    state = _run_next(repo)
    assert state["RECOMMENDED_COMMAND"] == "/devspark.tasks"

    (feature / "tasks.md").write_text("- [ ] T001 Implement behavior\n", encoding="utf-8")
    state = _run_next(repo, "--auto")
    assert state["AUTO"] is True
    assert state["RECOMMENDED_COMMAND"] == "/devspark.checklist"

    _write_gate(feature, "checklist")
    state = _run_next(repo)
    assert state["RECOMMENDED_COMMAND"] == "/devspark.analyze"

    _write_gate(feature, "analyze")
    state = _run_next(repo)
    assert state["RECOMMENDED_COMMAND"] == "/devspark.critic"

    _write_gate(feature, "critic")
    state = _run_next(repo)
    assert state["RECOMMENDED_COMMAND"] == "/devspark.implement"
    assert state["TASKS"]["incomplete"] == 1


@pytest.mark.skipif(
    any(shutil.which(tool) is None for tool in ("git", "jq", "rg")),
    reason="next-context smoke tests require git, jq, and rg",
)
def test_next_stops_auto_at_commit_and_failed_gate_boundaries(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    feature = _write_spec(repo, status="Complete")
    (feature / "plan.md").write_text("# Plan\n", encoding="utf-8")
    (feature / "tasks.md").write_text("- [x] T001 Implement behavior\n", encoding="utf-8")
    _write_gate(feature, "checklist")
    _write_gate(feature, "analyze")
    _write_gate(feature, "critic", status="fail", blocking=True)

    state = _run_next(repo, "--auto")
    assert state["ORIENTATION_STATE"] == "critic-blocked"
    assert state["ACTION_KIND"] == "manual"
    assert state["SAFE_TO_AUTO"] is False
    assert state["HUMAN_BOUNDARY"] == "gate"

    _write_gate(feature, "critic")
    source = repo / "src.py"
    source.write_text("value = 1\n", encoding="utf-8")
    state = _run_next(repo, "--auto")
    assert state["ORIENTATION_STATE"] == "commit-required"
    assert state["HUMAN_BOUNDARY"] == "commit"
    assert state["MANUAL_COMMAND"].startswith("git status --short")
    assert state["READ_ONLY"] is True


@pytest.mark.skipif(
    any(shutil.which(tool) is None for tool in ("git", "jq", "rg")),
    reason="next-context smoke tests require git, jq, and rg",
)
def test_next_uses_pr_review_state_and_never_merges(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    feature = _write_spec(repo, status="Complete")
    (feature / "plan.md").write_text("# Plan\n", encoding="utf-8")
    (feature / "tasks.md").write_text("- [x] T001 Implement behavior\n", encoding="utf-8")
    for gate in ("checklist", "analyze", "critic"):
        _write_gate(feature, gate)

    origin = repo.parent / f"{repo.name}-origin.git"
    subprocess.run(["git", "init", "--bare", "-q", str(origin)], cwd=repo, check=True)
    subprocess.run(["git", "remote", "add", "origin", str(origin)], cwd=repo, check=True)
    subprocess.run(["git", "push", "-q", "-u", "origin", "HEAD"], cwd=repo, check=True)

    fake_bin = repo / ".test-bin"
    fake_bin.mkdir()
    fake_gh = fake_bin / "gh"
    fake_gh.write_text(
        "#!/bin/sh\n"
        "if [ \"$1 $2\" = \"auth status\" ]; then exit 0; fi\n"
        "if [ \"$1 $2\" = \"pr view\" ]; then printf '%s\\n' \"$FAKE_GH_PR_JSON\"; exit 0; fi\n"
        "exit 1\n",
        encoding="utf-8",
    )
    fake_gh.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["FAKE_GH_PR_JSON"] = json.dumps(
        {
            "number": 42,
            "state": "OPEN",
            "url": "https://example.test/pr/42",
            "baseRefName": "main",
            "reviewDecision": "",
            "mergeStateStatus": "CLEAN",
        }
    )

    state = _run_next(repo, "--auto", env=env)
    assert state["RECOMMENDED_COMMAND"] == "/devspark.pr-review"
    assert state["SAFE_TO_AUTO"] is True

    review = repo / ".devspark.work/pr-reviews/pr-42.md"
    review.parent.mkdir(parents=True)
    review.write_text("gate: pr-review\nstatus: pass\nblocking: false\n", encoding="utf-8")
    state = _run_next(repo, "--auto", env=env)
    assert state["ORIENTATION_STATE"] == "merge-ready"
    assert state["ACTION_KIND"] == "manual"
    assert state["HUMAN_BOUNDARY"] == "merge"
    assert state["MANUAL_COMMAND"] == "gh pr merge 42"
