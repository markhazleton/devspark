"""Integration test for the execute-plan workflow (T034)."""

from __future__ import annotations

from pathlib import Path

import pytest

from devspark_cli.runner.executor import WorkflowRunner
from devspark_cli.runner.loader import (
    parse_alias,
    parse_workflow,
    validate_alias,
    validate_workflow,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _resolve_prompt(prompt_id: str) -> Path:
    p = REPO_ROOT / "templates" / "prompts" / "atomic" / f"{prompt_id}.md"
    if p.is_file():
        return p
    raise FileNotFoundError(prompt_id)


def _load_workflow():
    wf_path = REPO_ROOT / "templates" / "workflows" / "execute-plan.yaml"
    wf = parse_workflow(wf_path)
    validate_workflow(wf, resolve_prompt=_resolve_prompt)
    return wf


def test_alias_resolves_to_workflow():
    alias_path = REPO_ROOT / "templates" / "aliases" / "execute-plan.yaml"
    alias = parse_alias(alias_path)
    wf = _load_workflow()
    validate_alias(alias, resolve_workflow=lambda wid: wf if wid == alias.target_workflow else None)
    assert alias.target_workflow == "execute-plan"


def test_execute_plan_pauses_after_create_pr(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVSPARK_RUNS_PATH", str(tmp_path / "runs"))
    wf = _load_workflow()
    runner = WorkflowRunner(wf, mode="stub", repo_root=tmp_path)
    run = runner.run({})
    assert run.paused is True
    assert run.paused_after_step == "create-pr"
    assert [r.step_id for r in run.results] == ["implement", "create-pr"]
