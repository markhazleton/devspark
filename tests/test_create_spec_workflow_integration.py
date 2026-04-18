"""Integration test for the create-spec workflow (T020).

Loads templates/workflows/create-spec.yaml, executes a stub-runner pass
through all 4 steps, asserts pause-after-analyze with output_type
reviewable-artifact.
"""

from __future__ import annotations

from pathlib import Path

from devspark_cli.runner.executor import WorkflowRunner
from devspark_cli.runner.loader import (
    parse_workflow,
    validate_workflow,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / "templates" / "workflows" / "create-spec.yaml"
ATOMIC_DIR = REPO_ROOT / "templates" / "prompts" / "atomic"


def _resolve_prompt(prompt_id: str) -> Path | None:
    candidate = ATOMIC_DIR / f"{prompt_id}.md"
    return candidate if candidate.is_file() else None


def test_create_spec_workflow_loads_and_validates() -> None:
    wf = parse_workflow(WORKFLOW)
    validate_workflow(wf, resolve_prompt=_resolve_prompt)
    assert wf.id == "create-spec"
    assert wf.output_type == "reviewable-artifact"
    assert wf.autonomy_level == "assisted"
    assert wf.review_after == ["analyze"]
    assert [s.id for s in wf.steps] == ["specify", "plan", "generate-tasks", "analyze"]
    assert wf.steps[-1].pause_after is True


def test_create_spec_pauses_after_analyze(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DEVSPARK_RUNS_PATH", str(tmp_path / "runs"))
    wf = parse_workflow(WORKFLOW)
    validate_workflow(wf, resolve_prompt=_resolve_prompt)
    runner = WorkflowRunner(wf, mode="stub", repo_root=tmp_path)
    run = runner.run({})
    assert [r.step_id for r in run.results] == ["specify", "plan", "generate-tasks", "analyze"]
    assert run.paused is True
    assert run.paused_after_step == "analyze"
    assert run.next_step_id is None
