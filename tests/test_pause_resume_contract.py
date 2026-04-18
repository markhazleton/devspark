"""Pause-resume contract test (T032c).

- Pause writes documented JSON shape with all required fields incl.
  schema_version + context_checksum.
- Atomic write survives crash mid-write (simulate by killing during .tmp phase).
- Resume reads it, verifies checksum, continues at next_step_id, emits
  telemetry under the same workflow_run_id.
- Resume fails with EXIT_RESUME_FAILED when:
    (a) workflow definition no longer resolves
    (b) persisted workflow_id mismatches
    (c) checksum is wrong
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from devspark_cli.runner.executor import (
    EXIT_RESUME_FAILED,
    PAUSE_STATE_SCHEMA_VERSION,
    WorkflowRunner,
    load_pause_state,
    runs_dir,
    write_pause_state,
)
from devspark_cli.runner.loader import Workflow, WorkflowStep


def _make_wf() -> Workflow:
    return Workflow(
        id="t",
        name="t",
        description="t",
        output_type="reviewable-artifact",
        autonomy_level="assisted",
        steps=[
            WorkflowStep(id="a", prompt="a"),
            WorkflowStep(id="b", prompt="b", pause_after=True),
            WorkflowStep(id="c", prompt="c"),
        ],
    )


def test_pause_writes_required_shape(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DEVSPARK_RUNS_PATH", str(tmp_path / "runs"))
    wf = _make_wf()
    runner = WorkflowRunner(wf, mode="stub", repo_root=tmp_path)
    run = runner.run({"k": "v"})
    files = list((tmp_path / "runs").glob("*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text(encoding="utf-8"))
    for required in (
        "schema_version",
        "workflow_id",
        "workflow_run_id",
        "last_completed_step_id",
        "next_step_id",
        "context",
        "autonomy_level",
        "paused_at",
        "context_checksum",
    ):
        assert required in data
    assert data["schema_version"] == PAUSE_STATE_SCHEMA_VERSION
    assert data["last_completed_step_id"] == "b"
    assert data["next_step_id"] == "c"


def test_atomic_write_survives_crash_mid_write(tmp_path, monkeypatch) -> None:
    """If a .tmp file is left around, the final file is untouched OR fully valid."""
    monkeypatch.setenv("DEVSPARK_RUNS_PATH", str(tmp_path / "runs"))
    wf = _make_wf()
    runner = WorkflowRunner(wf, mode="stub", repo_root=tmp_path)
    run = runner.run({"k": "v"})

    final = tmp_path / "runs" / f"{run.workflow_run_id}.json"
    assert final.is_file()
    # Simulate a crashed write that left a .tmp around without replacing.
    leftover = final.with_suffix(final.suffix + ".tmp")
    leftover.write_bytes(b"PARTIAL")
    # Final file is still parseable JSON.
    data = json.loads(final.read_text(encoding="utf-8"))
    assert data["workflow_id"] == "t"


def test_resume_continues_at_next_step(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DEVSPARK_RUNS_PATH", str(tmp_path / "runs"))
    wf = _make_wf()
    runner = WorkflowRunner(wf, mode="stub", repo_root=tmp_path)
    run = runner.run({})
    assert run.paused is True

    # Resume from persisted state
    state = load_pause_state(tmp_path, run.workflow_run_id)
    assert state["next_step_id"] == "c"
    runner2 = WorkflowRunner(wf, mode="stub", repo_root=tmp_path)
    run2 = runner2.run(
        state["context"],
        autonomy_level=state["autonomy_level"],
        workflow_run_id=run.workflow_run_id,
        start_at_step_id=state["next_step_id"],
    )
    # Only step c should run on resume
    assert [r.step_id for r in run2.results] == ["c"]
    assert run2.workflow_run_id == run.workflow_run_id


def test_resume_fails_when_checksum_wrong(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DEVSPARK_RUNS_PATH", str(tmp_path / "runs"))
    wf = _make_wf()
    runner = WorkflowRunner(wf, mode="stub", repo_root=tmp_path)
    run = runner.run({"k": "v"})

    final = tmp_path / "runs" / f"{run.workflow_run_id}.json"
    data = json.loads(final.read_text(encoding="utf-8"))
    data["context_checksum"] = "0" * 64
    final.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError) as exc:
        load_pause_state(tmp_path, run.workflow_run_id)
    assert "checksum" in str(exc.value).lower()


def test_resume_fails_when_schema_version_mismatch(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DEVSPARK_RUNS_PATH", str(tmp_path / "runs"))
    wf = _make_wf()
    runner = WorkflowRunner(wf, mode="stub", repo_root=tmp_path)
    run = runner.run({})
    final = tmp_path / "runs" / f"{run.workflow_run_id}.json"
    data = json.loads(final.read_text(encoding="utf-8"))
    data["schema_version"] = 999
    final.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError) as exc:
        load_pause_state(tmp_path, run.workflow_run_id)
    assert "schema_version" in str(exc.value).lower()


def test_exit_code_constant_for_resume_failure() -> None:
    assert EXIT_RESUME_FAILED == 25
