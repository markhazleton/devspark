"""Micro-benchmark intent test (T065a).

Measures workflow startup overhead and per-event telemetry append latency.
Emits warnings (not failures) when targets are exceeded so design intent
remains visible without becoming flaky in CI.
"""

from __future__ import annotations

import time
import uuid
import warnings
from pathlib import Path

from devspark_cli.runner.executor import WorkflowRunner
from devspark_cli.runner.loader import Workflow, WorkflowStep
from devspark_cli.runner.telemetry import TelemetryWriter


_STARTUP_BUDGET_MS = 200.0
_APPEND_BUDGET_MS = 5.0


def _make_wf() -> Workflow:
    return Workflow(
        id="bench",
        name="bench",
        description="bench",
        output_type="reviewable-artifact",
        autonomy_level="assisted",
        steps=[WorkflowStep(id=f"s{i}", prompt=f"s{i}") for i in range(3)],
    )


def test_workflow_startup_overhead_intent(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DEVSPARK_RUNS_PATH", str(tmp_path / "runs"))
    wf = _make_wf()
    samples = []
    for _ in range(20):
        t0 = time.perf_counter()
        runner = WorkflowRunner(wf, mode="stub", repo_root=tmp_path)
        runner.run({})
        samples.append((time.perf_counter() - t0) * 1000.0)
    samples.sort()
    p95 = samples[int(len(samples) * 0.95) - 1]
    if p95 > _STARTUP_BUDGET_MS:
        warnings.warn(
            f"workflow startup p95={p95:.1f} ms > {_STARTUP_BUDGET_MS} ms (design intent)",
            stacklevel=2,
        )


def test_telemetry_append_latency_intent(tmp_path) -> None:
    target = tmp_path / "events.jsonl"
    w = TelemetryWriter(target)
    samples = []
    for _ in range(100):
        event = {
            "schema_version": "1",
            "event_id": str(uuid.uuid4()),
            "timestamp": "2026-04-18T00:00:00.000Z",
            "workflow_id": "bench",
            "workflow_run_id": "bench",
            "step_id": "s",
            "phase": "completed",
            "status": "success",
            "duration_ms": 1,
            "success": True,
            "autonomy_level": "assisted",
            "guardrail_rule": None,
            "error": None,
        }
        t0 = time.perf_counter()
        w.write(event)
        samples.append((time.perf_counter() - t0) * 1000.0)
    avg = sum(samples) / len(samples)
    if avg > _APPEND_BUDGET_MS:
        warnings.warn(
            f"telemetry append avg={avg:.2f} ms > {_APPEND_BUDGET_MS} ms (design intent)",
            stacklevel=2,
        )
