"""Telemetry output for harness runs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EVENT_TYPES = {
    "harness.run.started",
    "harness.run.finished",
    "harness.run.replayed",
    "harness.step.started",
    "harness.step.finished",
    "harness.step.validation",
    "harness.step.artifacts",
    "harness.step.incident",
    "harness.delivery.check",
    "harness.stage.iteration",
    "harness.tool.called",
    "harness.policy.blocked",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class TelemetrySink:
    """Append-only JSONL sink for harness run telemetry."""

    def __init__(self, events_path: Path, enabled: bool = True) -> None:
        self.events_path = events_path
        self.enabled = enabled
        if self.enabled:
            self.events_path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: str, run_id: str, **payload: Any) -> None:
        if not self.enabled:
            return
        if event not in EVENT_TYPES:
            raise ValueError(f"Unsupported telemetry event: {event}")
        record = {"event": event, "run_id": run_id, "ts": utc_now_iso(), **payload}
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")