"""Contract tests for telemetry events (contracts/telemetry-event.md, T027)."""

from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

import pytest

from devspark_cli.runner.telemetry import (
    EVT_ERROR_CLASS_REQUIRED,
    EVT_ERROR_REQUIRED,
    EVT_ERROR_TOO_LONG,
    EVT_FIELD_MISSING,
    EVT_GUARDRAIL_RULE_REQUIRED,
    EVT_PHASE_INVALID,
    EVT_STATUS_INVALID,
    EVT_TIMESTAMP_INVALID,
    EVT_TOO_LARGE,
    TelemetryError,
    TelemetryWriter,
    default_path,
    validate_event,
)


def _good_event(**overrides):
    base = {
        "schema_version": "1",
        "event_id": str(uuid.uuid4()),
        "timestamp": "2026-04-18T17:42:11.523Z",
        "workflow_id": "create-spec",
        "workflow_run_id": str(uuid.uuid4()),
        "step_id": "analyze",
        "phase": "completed",
        "status": "success",
        "duration_ms": 12,
        "success": True,
        "autonomy_level": "assisted",
        "guardrail_rule": None,
        "error": None,
    }
    base.update(overrides)
    return base


def test_required_field_missing() -> None:
    e = _good_event()
    e.pop("workflow_id")
    with pytest.raises(TelemetryError) as exc:
        validate_event(e)
    assert exc.value.code == EVT_FIELD_MISSING


def test_phase_invalid() -> None:
    with pytest.raises(TelemetryError) as exc:
        validate_event(_good_event(phase="weird"))
    assert exc.value.code == EVT_PHASE_INVALID


def test_status_invalid() -> None:
    with pytest.raises(TelemetryError) as exc:
        validate_event(_good_event(status="weird"))
    assert exc.value.code == EVT_STATUS_INVALID


def test_timestamp_invalid() -> None:
    with pytest.raises(TelemetryError) as exc:
        validate_event(_good_event(timestamp="not-a-time"))
    assert exc.value.code == EVT_TIMESTAMP_INVALID


def test_guardrail_rule_required() -> None:
    with pytest.raises(TelemetryError) as exc:
        validate_event(_good_event(phase="guardrail_triggered", guardrail_rule=None))
    assert exc.value.code == EVT_GUARDRAIL_RULE_REQUIRED


def test_error_required_when_failed() -> None:
    with pytest.raises(TelemetryError) as exc:
        validate_event(_good_event(phase="failed", status="failure", error=None, error_class="X"))
    assert exc.value.code == EVT_ERROR_REQUIRED


def test_error_class_required_when_failed() -> None:
    with pytest.raises(TelemetryError) as exc:
        validate_event(_good_event(phase="failed", status="failure", error="boom"))
    assert exc.value.code == EVT_ERROR_CLASS_REQUIRED


def test_error_too_long() -> None:
    with pytest.raises(TelemetryError) as exc:
        validate_event(
            _good_event(
                phase="failed",
                status="failure",
                error="x" * 600,
                error_class="X",
            )
        )
    assert exc.value.code == EVT_ERROR_TOO_LONG


def test_event_too_large_via_context() -> None:
    huge_ctx = {"k": "x" * 2000}
    with pytest.raises(TelemetryError) as exc:
        validate_event(_good_event(context=huge_ctx))
    assert exc.value.code == EVT_TOO_LARGE


def test_default_path_env_override(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DEVSPARK_TELEMETRY_PATH", str(tmp_path / "custom.jsonl"))
    p = default_path(Path("/nonexistent"))
    assert p == tmp_path / "custom.jsonl"


def test_writer_appends_jsonl(tmp_path) -> None:
    target = tmp_path / "events.jsonl"
    w = TelemetryWriter(target)
    assert w.write(_good_event()) is True
    assert w.write(_good_event(step_id="plan")) is True
    lines = target.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    for line in lines:
        json.loads(line)


def test_writer_fail_soft_on_io_error(tmp_path, monkeypatch) -> None:
    """Simulate write failure and assert workflow continues; file is not corrupted."""
    target = tmp_path / "events.jsonl"
    w = TelemetryWriter(target)
    # First write succeeds
    assert w.write(_good_event()) is True

    # Now patch os.write to raise; second call must return False, not raise.
    real_open = os.open

    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(os, "open", lambda *a, **k: (_ for _ in ()).throw(OSError("disk full")))
    assert w.write(_good_event(step_id="plan")) is False

    # Original line still parses cleanly
    monkeypatch.setattr(os, "open", real_open)
    lines = target.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    json.loads(lines[0])
