"""Contract tests for autonomy enforcement (T028)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from devspark_cli.runner.autonomy import AutonomyEnforcer
from devspark_cli.runner.executor import WorkflowRunner
from devspark_cli.runner.loader import Workflow, WorkflowStep


def _make_wf(level: str = "assisted", review_after=None, guardrails=None) -> Workflow:
    return Workflow(
        id="t",
        name="t",
        description="t",
        output_type="reviewable-artifact",
        autonomy_level=level,
        review_after=review_after or [],
        guardrails=guardrails or {},
        steps=[WorkflowStep(id="x", prompt="x")],
    )


def _git_init(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=str(repo), check=True)
    (repo / "seed.txt").write_text("seed", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=str(repo), check=True)


def test_assisted_pause_at_review_after(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DEVSPARK_RUNS_PATH", str(tmp_path / "runs"))
    wf = _make_wf(review_after=["x"])
    runner = WorkflowRunner(wf, mode="stub", repo_root=tmp_path)
    run = runner.run({})
    assert run.paused is True
    assert run.paused_after_step == "x"


def test_autonomous_max_files_changed_blocks(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DEVSPARK_RUNS_PATH", str(tmp_path / "runs"))
    _git_init(tmp_path)
    enforcer = AutonomyEnforcer(tmp_path, guardrails={"max_files_changed": 1})

    def invoker(prompt_id, step, ctx):
        # Create 3 new files (exceeds limit of 1)
        for i in range(3):
            (tmp_path / f"new_{i}.txt").write_text(str(i), encoding="utf-8")
            subprocess.run(["git", "add", f"new_{i}.txt"], cwd=str(tmp_path), check=True)
        return {}

    wf = _make_wf(level="autonomous", guardrails={"max_files_changed": 1})
    runner = WorkflowRunner(
        wf, mode="live", invoker=invoker, repo_root=tmp_path, autonomy_enforcer=enforcer
    )
    run = runner.run({}, autonomy_level="autonomous")
    assert run.exit_code == 21  # EXIT_GUARDRAIL_BLOCKED


def test_autonomous_restricted_paths_blocks(tmp_path) -> None:
    _git_init(tmp_path)
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "workflows").mkdir()
    (tmp_path / "ok.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "commit", "-q", "-m", "more"], cwd=str(tmp_path), check=True)

    enforcer = AutonomyEnforcer(tmp_path, guardrails={"restricted_paths": [".github/workflows/*"]})

    def invoker(prompt_id, step, ctx):
        (tmp_path / ".github" / "workflows" / "ci.yml").write_text("on: push\n", encoding="utf-8")
        subprocess.run(["git", "add", ".github/workflows/ci.yml"], cwd=str(tmp_path), check=True)
        return {}

    wf = _make_wf(level="autonomous", guardrails={"restricted_paths": [".github/workflows/*"]})
    runner = WorkflowRunner(
        wf, mode="live", invoker=invoker, repo_root=tmp_path, autonomy_enforcer=enforcer
    )
    run = runner.run({}, autonomy_level="autonomous")
    assert run.exit_code == 21


def test_assisted_downgrade_pauses_instead_of_block(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DEVSPARK_RUNS_PATH", str(tmp_path / "runs"))
    _git_init(tmp_path)
    enforcer = AutonomyEnforcer(tmp_path, guardrails={"max_files_changed": 1})

    def invoker(prompt_id, step, ctx):
        for i in range(3):
            (tmp_path / f"f_{i}.txt").write_text(str(i), encoding="utf-8")
            subprocess.run(["git", "add", f"f_{i}.txt"], cwd=str(tmp_path), check=True)
        return {}

    wf = _make_wf(level="assisted", guardrails={"max_files_changed": 1})
    runner = WorkflowRunner(
        wf, mode="live", invoker=invoker, repo_root=tmp_path, autonomy_enforcer=enforcer
    )
    run = runner.run({}, autonomy_level="assisted")
    assert run.paused is True
    assert run.exit_code == 0


def test_absent_guardrails_with_autonomous_aborts() -> None:
    """Validation rule: autonomy.level=autonomous requires guardrails (covered by WF_GUARDRAILS_REQUIRED).

    This test verifies the *runner* side: when a workflow is constructed
    without guardrails but autonomy is autonomous, the validate_workflow
    function (already covered by test_workflow_schema_contract) flags the
    issue. We assert the loader exception code here as a sanity bridge.
    """
    from devspark_cli.runner.loader import (
        WF_GUARDRAILS_REQUIRED,
        ValidationError,
        validate_workflow,
    )

    wf = _make_wf(level="autonomous", guardrails={})
    with pytest.raises(ValidationError) as exc:
        validate_workflow(wf, resolve_prompt=lambda _: Path("/exists"))
    assert exc.value.code == WF_GUARDRAILS_REQUIRED
