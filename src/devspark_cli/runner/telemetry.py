"""DevSpark workflow runner — telemetry writer.

JSONL append with OS-level exclusive file lock. See
contracts/telemetry-event.md for the wire format.
"""

from __future__ import annotations

import json
import os
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator


# Error codes (mirror contracts/telemetry-event.md)
EVT_FIELD_MISSING = "EVT_FIELD_MISSING"
EVT_TIMESTAMP_INVALID = "EVT_TIMESTAMP_INVALID"
EVT_PHASE_INVALID = "EVT_PHASE_INVALID"
EVT_STATUS_INVALID = "EVT_STATUS_INVALID"
EVT_GUARDRAIL_RULE_REQUIRED = "EVT_GUARDRAIL_RULE_REQUIRED"
EVT_ERROR_REQUIRED = "EVT_ERROR_REQUIRED"
EVT_ERROR_CLASS_REQUIRED = "EVT_ERROR_CLASS_REQUIRED"
EVT_ERROR_TOO_LONG = "EVT_ERROR_TOO_LONG"
EVT_TOO_LARGE = "EVT_TOO_LARGE"


_REQUIRED_FIELDS = {
    "schema_version",
    "event_id",
    "timestamp",
    "workflow_id",
    "workflow_run_id",
    "step_id",
    "phase",
    "status",
    "duration_ms",
    "success",
    "autonomy_level",
}

_PHASES = {"started", "completed", "paused", "failed", "guardrail_triggered"}
_STATUSES = {"pending", "success", "failure"}

_MAX_EVENT_BYTES = 4 * 1024
_MAX_CONTEXT_BYTES = 1 * 1024
_MAX_ERROR_CHARS = 500


class TelemetryError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def default_path(repo_root: Path) -> Path:
    """Resolve the default telemetry path. Honors DEVSPARK_TELEMETRY_PATH."""
    override = os.environ.get("DEVSPARK_TELEMETRY_PATH")
    if override:
        return Path(override)
    return repo_root / ".documentation" / "telemetry" / "workflow-events.jsonl"


# ---------------------------------------------------------------------------
# Cross-platform exclusive file lock
# ---------------------------------------------------------------------------

@contextmanager
def _exclusive_lock(fd: int) -> Iterator[None]:
    """Acquire and release an exclusive OS-level lock on the given file descriptor."""
    if os.name == "nt":
        import msvcrt

        # Lock 1 byte from current position; the file was opened append-only.
        try:
            msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
            yield
        finally:
            try:
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
    else:
        import fcntl

        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_event(event: dict[str, Any]) -> None:
    """Validate an event dict. Raises TelemetryError on any violation."""
    missing = [k for k in _REQUIRED_FIELDS if k not in event]
    if missing:
        raise TelemetryError(EVT_FIELD_MISSING, f"missing required fields: {sorted(missing)}")

    ts = event["timestamp"]
    if not isinstance(ts, str):
        raise TelemetryError(EVT_TIMESTAMP_INVALID, f"timestamp must be ISO 8601 string, got {ts!r}")
    try:
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        raise TelemetryError(EVT_TIMESTAMP_INVALID, f"timestamp not parseable: {ts!r}")
    if parsed.tzinfo is None:
        raise TelemetryError(EVT_TIMESTAMP_INVALID, f"timestamp must include timezone offset, got {ts!r}")

    if event["phase"] not in _PHASES:
        raise TelemetryError(EVT_PHASE_INVALID, f"phase={event['phase']!r} not in {_PHASES}")

    if event["status"] not in _STATUSES:
        raise TelemetryError(EVT_STATUS_INVALID, f"status={event['status']!r} not in {_STATUSES}")

    if event["phase"] == "guardrail_triggered" and not event.get("guardrail_rule"):
        raise TelemetryError(EVT_GUARDRAIL_RULE_REQUIRED, "guardrail_rule required when phase=guardrail_triggered")

    if event["phase"] == "failed":
        if not event.get("error"):
            raise TelemetryError(EVT_ERROR_REQUIRED, "error required when phase=failed")
        if not event.get("error_class"):
            raise TelemetryError(EVT_ERROR_CLASS_REQUIRED, "error_class required when phase=failed")

    err = event.get("error")
    if isinstance(err, str) and len(err) > _MAX_ERROR_CHARS:
        raise TelemetryError(EVT_ERROR_TOO_LONG, f"error exceeds {_MAX_ERROR_CHARS} chars")

    serialized = json.dumps(event, sort_keys=True).encode("utf-8")
    if len(serialized) > _MAX_EVENT_BYTES:
        raise TelemetryError(EVT_TOO_LARGE, f"serialized event exceeds {_MAX_EVENT_BYTES} bytes")
    ctx = event.get("context")
    if ctx is not None:
        ctx_bytes = json.dumps(ctx, sort_keys=True).encode("utf-8")
        if len(ctx_bytes) > _MAX_CONTEXT_BYTES:
            raise TelemetryError(EVT_TOO_LARGE, f"context exceeds {_MAX_CONTEXT_BYTES} bytes")


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

class TelemetryWriter:
    """Append-only JSONL writer with OS-level locking and fail-soft semantics."""

    def __init__(self, path: Path | None = None, *, repo_root: Path | None = None) -> None:
        if path is None:
            if repo_root is None:
                raise ValueError("either path or repo_root is required")
            path = default_path(repo_root)
        self.path = Path(path)

    def write(self, event: dict[str, Any]) -> bool:
        """Append a single event. Returns True on success, False on fail-soft failure.

        Raises TelemetryError synchronously when the event itself is invalid
        (e.g., EVT_TOO_LARGE) — these are programmer errors, not I/O failures.
        """
        validate_event(event)
        line = json.dumps(event, sort_keys=True) + "\n"
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(str(self.path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
            try:
                with _exclusive_lock(fd):
                    os.write(fd, line.encode("utf-8"))
            finally:
                os.close(fd)
            return True
        except OSError as exc:
            print(f"[devspark] telemetry write failed (fail-soft): {exc}", file=sys.stderr)
            return False
