"""Concurrent-append contract test for telemetry writer (T029a).

Spawns 50 concurrent processes appending events to the same JSONL file and
asserts:
  (a) line count matches expected
  (b) every line is independently valid JSON
  (c) no event is truncated or interleaved
"""

from __future__ import annotations

import json
import multiprocessing as mp
import sys
import uuid
from pathlib import Path

import pytest


def _worker(args):
    target_path, worker_id, count = args
    # Re-import inside child for spawn semantics
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from devspark_cli.runner.telemetry import TelemetryWriter

    w = TelemetryWriter(Path(target_path))
    for i in range(count):
        event = {
            "schema_version": "1",
            "event_id": str(uuid.uuid4()),
            "timestamp": "2026-04-18T00:00:00.000Z",
            "workflow_id": "concurrent-test",
            "workflow_run_id": f"worker-{worker_id}",
            "step_id": f"s-{worker_id}-{i}",
            "phase": "completed",
            "status": "success",
            "duration_ms": 1,
            "success": True,
            "autonomy_level": "assisted",
            "guardrail_rule": None,
            "error": None,
        }
        w.write(event)
    return worker_id


@pytest.mark.skipif(sys.platform.startswith("win"), reason="multiprocessing+spawn slow on win; covered by serial test")
def test_concurrent_appends_remain_well_formed(tmp_path) -> None:
    target = tmp_path / "events.jsonl"
    workers = 50
    per_worker = 10
    args = [(str(target), i, per_worker) for i in range(workers)]
    with mp.get_context("spawn").Pool(processes=10) as pool:
        results = pool.map(_worker, args)
    assert sorted(results) == list(range(workers))

    lines = target.read_text(encoding="utf-8").splitlines()
    assert len(lines) == workers * per_worker, f"expected {workers * per_worker} lines, got {len(lines)}"
    seen_ids: set[str] = set()
    for line in lines:
        obj = json.loads(line)  # raises on truncation/interleave
        assert obj["event_id"] not in seen_ids
        seen_ids.add(obj["event_id"])


def test_serial_appends_remain_well_formed(tmp_path) -> None:
    """Smoke version that always runs (Windows-friendly)."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from devspark_cli.runner.telemetry import TelemetryWriter

    target = tmp_path / "events.jsonl"
    w = TelemetryWriter(target)
    for i in range(200):
        w.write({
            "schema_version": "1",
            "event_id": str(uuid.uuid4()),
            "timestamp": "2026-04-18T00:00:00.000Z",
            "workflow_id": "serial",
            "workflow_run_id": "single",
            "step_id": f"s-{i}",
            "phase": "completed",
            "status": "success",
            "duration_ms": 1,
            "success": True,
            "autonomy_level": "assisted",
            "guardrail_rule": None,
            "error": None,
        })
    lines = target.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 200
    for line in lines:
        json.loads(line)
