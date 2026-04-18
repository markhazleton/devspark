"""Contract tests for the workflow runner (T019, T038).

Covers:
- Ordered step execution
- `pause_after` behavior
- Atomic-prompt id resolution failure surfacing as `WF_PROMPT_UNKNOWN` at validate
- Workflow-context propagation between steps
- Conditional `when` branches: true / false / missing context-key
"""

from __future__ import annotations

from pathlib import Path

import pytest

from devspark_cli.runner.executor import WorkflowRunner
from devspark_cli.runner.loader import (
    Workflow,
    WorkflowStep,
)


def _make_workflow(steps: list[WorkflowStep]) -> Workflow:
    return Workflow(
        id="test",
        name="Test",
        description="t",
        output_type="reviewable-artifact",
        autonomy_level="assisted",
        review_after=[],
        guardrails={},
        steps=steps,
    )


def test_ordered_step_execution_stub_mode() -> None:
    wf = _make_workflow([
        WorkflowStep(id="a", prompt="a"),
        WorkflowStep(id="b", prompt="b"),
        WorkflowStep(id="c", prompt="c"),
    ])
    runner = WorkflowRunner(wf, mode="stub")
    run = runner.run({})
    assert [r.step_id for r in run.results] == ["a", "b", "c"]
    assert all(r.status == "success" for r in run.results)
    assert run.paused is False
    assert run.exit_code == 0


def test_pause_after_halts_execution(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DEVSPARK_RUNS_PATH", str(tmp_path / "runs"))
    wf = _make_workflow([
        WorkflowStep(id="a", prompt="a"),
        WorkflowStep(id="b", prompt="b", pause_after=True),
        WorkflowStep(id="c", prompt="c"),
    ])
    runner = WorkflowRunner(wf, mode="stub", repo_root=tmp_path)
    run = runner.run({})
    assert [r.step_id for r in run.results] == ["a", "b"]
    assert run.paused is True
    assert run.paused_after_step == "b"
    assert run.next_step_id == "c"


def test_workflow_context_propagation_live_mode() -> None:
    captured: list[dict] = []

    def invoker(prompt_id: str, step, context: dict) -> dict:
        captured.append(dict(context))
        return {f"out_{step.id}": prompt_id}

    wf = _make_workflow([
        WorkflowStep(id="first", prompt="p1"),
        WorkflowStep(id="second", prompt="p2"),
    ])
    runner = WorkflowRunner(wf, mode="live", invoker=invoker)
    run = runner.run({"seed": 1})
    # Second step sees first step's context update.
    assert captured[0] == {"seed": 1}
    assert captured[1] == {"seed": 1, "out_first": "p1"}
    assert run.context["out_second"] == "p2"


def test_conditional_when_skips_step_when_false() -> None:
    invocations: list[str] = []

    def invoker(prompt_id, step, context):
        invocations.append(step.id)
        return {}

    wf = _make_workflow([
        WorkflowStep(id="always", prompt="a"),
        WorkflowStep(id="opt", prompt="b", when="context.go == true"),
        WorkflowStep(id="end", prompt="c"),
    ])
    runner = WorkflowRunner(wf, mode="live", invoker=invoker)
    run = runner.run({"go": False})
    assert invocations == ["always", "end"]
    assert any(r.step_id == "opt" and r.status == "skipped" for r in run.results)


def test_conditional_when_true_runs_step() -> None:
    invocations: list[str] = []

    def invoker(prompt_id, step, context):
        invocations.append(step.id)
        return {}

    wf = _make_workflow([
        WorkflowStep(id="opt", prompt="b", when="context.go == true"),
    ])
    runner = WorkflowRunner(wf, mode="live", invoker=invoker)
    runner.run({"go": True})
    assert invocations == ["opt"]


def test_conditional_when_missing_key_treated_as_none() -> None:
    """A missing context key evaluates to None; `None == true` is False, step is skipped."""
    invocations: list[str] = []

    def invoker(prompt_id, step, context):
        invocations.append(step.id)
        return {}

    wf = _make_workflow([
        WorkflowStep(id="opt", prompt="b", when="context.absent == true"),
    ])
    runner = WorkflowRunner(wf, mode="live", invoker=invoker)
    runner.run({})
    assert invocations == []


def test_failure_aborts_by_default() -> None:
    def invoker(prompt_id, step, context):
        if step.id == "boom":
            raise RuntimeError("explode")
        return {}

    wf = _make_workflow([
        WorkflowStep(id="ok", prompt="ok"),
        WorkflowStep(id="boom", prompt="boom"),
        WorkflowStep(id="never", prompt="never"),
    ])
    runner = WorkflowRunner(wf, mode="live", invoker=invoker)
    run = runner.run({})
    assert [r.step_id for r in run.results] == ["ok", "boom"]
    assert run.results[-1].status == "failed"
    assert run.exit_code != 0


def test_on_failure_continue_proceeds() -> None:
    def invoker(prompt_id, step, context):
        if step.id == "boom":
            raise RuntimeError("explode")
        return {}

    wf = _make_workflow([
        WorkflowStep(id="boom", prompt="x", on_failure="continue"),
        WorkflowStep(id="next", prompt="y"),
    ])
    runner = WorkflowRunner(wf, mode="live", invoker=invoker)
    run = runner.run({})
    assert [r.step_id for r in run.results] == ["boom", "next"]


def test_on_failure_pause_persists_state(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DEVSPARK_RUNS_PATH", str(tmp_path / "runs"))

    def invoker(prompt_id, step, context):
        raise RuntimeError("boom")

    wf = _make_workflow([WorkflowStep(id="x", prompt="x", on_failure="pause")])
    runner = WorkflowRunner(wf, mode="live", invoker=invoker, repo_root=tmp_path)
    run = runner.run({})
    assert run.paused is True
    persisted = list((tmp_path / "runs").glob("*.json"))
    assert len(persisted) == 1
