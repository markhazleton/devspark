"""DevSpark workflow runner — executor with pause/resume support.

Implements ordered step execution, `pause_after`, `when` evaluation, and a
deterministic `mode="stub"` that records step ids without invoking atomic
prompts. Pause-state persistence is atomic (`.tmp` + fsync + `os.replace`)
with a SHA-256 context checksum for integrity.

See contracts:
- contracts/workflow-schema.md
- contracts/exit-codes.md
- contracts/telemetry-event.md
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .loader import (
    Workflow,
    WorkflowStep,
    evaluate_when_expression,
)


# Exit codes (mirror contracts/exit-codes.md)
EXIT_OK = 0
EXIT_GENERIC = 1
EXIT_AUTONOMY_REQUIRED = 20
EXIT_GUARDRAIL_BLOCKED = 21
EXIT_RESUME_FAILED = 25


# Pause-state schema version
PAUSE_STATE_SCHEMA_VERSION = 1


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _checksum_context(context: dict[str, Any]) -> str:
    serialized = json.dumps(context, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _atomic_write(path: Path, content: bytes) -> None:
    """Atomically write bytes to path: .tmp + fsync + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        os.write(fd, content)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(str(tmp), str(path))


# ---------------------------------------------------------------------------
# Run state
# ---------------------------------------------------------------------------

@dataclass
class StepResult:
    step_id: str
    prompt: str
    status: str            # "success" | "skipped" | "paused" | "failed"
    duration_ms: int = 0
    error: str | None = None
    error_class: str | None = None


@dataclass
class WorkflowRun:
    workflow_id: str
    workflow_run_id: str
    autonomy_level: str
    context: dict[str, Any] = field(default_factory=dict)
    results: list[StepResult] = field(default_factory=list)
    paused: bool = False
    paused_after_step: str | None = None
    next_step_id: str | None = None
    exit_code: int = EXIT_OK


# ---------------------------------------------------------------------------
# Pause-state persistence
# ---------------------------------------------------------------------------

def runs_dir(repo_root: Path) -> Path:
    """Resolve the directory used to persist pause state.

    Honors the DEVSPARK_RUNS_PATH override.
    """
    override = os.environ.get("DEVSPARK_RUNS_PATH")
    if override:
        return Path(override)
    return repo_root / ".documentation" / "telemetry" / "runs"


def write_pause_state(
    repo_root: Path,
    run: WorkflowRun,
    *,
    last_completed_step_id: str | None,
    next_step_id: str | None,
) -> Path:
    payload = {
        "schema_version": PAUSE_STATE_SCHEMA_VERSION,
        "workflow_id": run.workflow_id,
        "workflow_run_id": run.workflow_run_id,
        "last_completed_step_id": last_completed_step_id,
        "next_step_id": next_step_id,
        "context": run.context,
        "autonomy_level": run.autonomy_level,
        "paused_at": _utcnow_iso(),
        "context_checksum": _checksum_context(run.context),
    }
    target = runs_dir(repo_root) / f"{run.workflow_run_id}.json"
    _atomic_write(target, json.dumps(payload, sort_keys=True).encode("utf-8"))
    return target


def load_pause_state(repo_root: Path, workflow_run_id: str) -> dict[str, Any]:
    """Load and integrity-verify a persisted pause state.

    Raises ValueError on any check failure (caller should map to EXIT_RESUME_FAILED).
    """
    path = runs_dir(repo_root) / f"{workflow_run_id}.json"
    if not path.is_file():
        raise ValueError(f"pause-state file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"pause-state file is not valid JSON: {exc}") from exc

    if data.get("schema_version") != PAUSE_STATE_SCHEMA_VERSION:
        raise ValueError(
            f"pause-state schema_version mismatch: {data.get('schema_version')!r} "
            f"!= {PAUSE_STATE_SCHEMA_VERSION}"
        )

    expected = _checksum_context(data.get("context", {}))
    actual = data.get("context_checksum")
    if expected != actual:
        raise ValueError(
            f"pause-state context_checksum mismatch (expected={expected!r}, found={actual!r})"
        )

    return data


# ---------------------------------------------------------------------------
# Workflow runner
# ---------------------------------------------------------------------------

PromptInvoker = Callable[[str, WorkflowStep, dict[str, Any]], dict[str, Any]]
"""Signature for the function that actually executes an atomic prompt.

Returns a dict of context updates merged into the run context.
"""


class WorkflowRunner:
    """Execute a workflow with optional pause/resume.

    Two modes:
      - mode="stub":  do not invoke the prompt; record the step as success.
                      Used by deterministic CI tests (T019, T020, T034).
      - mode="live":  call the supplied invoker for every step.
    """

    def __init__(
        self,
        workflow: Workflow,
        *,
        mode: str = "live",
        invoker: PromptInvoker | None = None,
        repo_root: Path | None = None,
        telemetry=None,
        autonomy_enforcer=None,
    ) -> None:
        if mode not in ("live", "stub"):
            raise ValueError(f"unknown runner mode: {mode!r}")
        if mode == "live" and invoker is None:
            raise ValueError("live mode requires an invoker")
        self.workflow = workflow
        self.mode = mode
        self.invoker = invoker
        self.repo_root = repo_root or Path.cwd()
        self.telemetry = telemetry
        self.autonomy_enforcer = autonomy_enforcer

    # ------------------------------------------------------------------ run
    def run(
        self,
        context: dict[str, Any] | None = None,
        *,
        autonomy_level: str | None = None,
        workflow_run_id: str | None = None,
        start_at_step_id: str | None = None,
    ) -> WorkflowRun:
        run = WorkflowRun(
            workflow_id=self.workflow.id,
            workflow_run_id=workflow_run_id or str(uuid.uuid4()),
            autonomy_level=autonomy_level or self.workflow.autonomy_level,
            context=dict(context or {}),
        )

        skip = start_at_step_id is not None
        for idx, step in enumerate(self.workflow.steps):
            if skip:
                if step.id == start_at_step_id:
                    skip = False
                else:
                    continue

            # `when` gating
            if step.when is not None:
                try:
                    enabled = evaluate_when_expression(step.when, run.context)
                except Exception as exc:
                    self._emit(run, step, "failed", error=f"when-eval failed: {exc}", error_class="WhenEvalError")
                    run.results.append(StepResult(step.id, step.prompt, "failed", error=str(exc), error_class="WhenEvalError"))
                    run.exit_code = EXIT_GENERIC
                    return run
                if not enabled:
                    run.results.append(StepResult(step.id, step.prompt, "skipped"))
                    self._emit(run, step, "completed", status="success")
                    continue

            # Pre-step autonomy hook (baseline capture)
            if self.autonomy_enforcer is not None:
                try:
                    self.autonomy_enforcer.before_step(run, step)
                except Exception as exc:
                    self._emit(run, step, "failed", error=str(exc), error_class="AutonomyPreError")
                    run.results.append(StepResult(step.id, step.prompt, "failed", error=str(exc), error_class="AutonomyPreError"))
                    run.exit_code = EXIT_GUARDRAIL_BLOCKED
                    return run

            # Execute
            self._emit(run, step, "started", status="pending", duration_ms=0)
            try:
                if self.mode == "stub":
                    updates: dict[str, Any] = {}
                else:
                    updates = self.invoker(step.prompt, step, dict(run.context)) or {}
                run.context.update(updates)
                run.results.append(StepResult(step.id, step.prompt, "success"))
                self._emit(run, step, "completed", status="success")
            except Exception as exc:
                run.results.append(
                    StepResult(step.id, step.prompt, "failed", error=str(exc), error_class=type(exc).__name__)
                )
                self._emit(run, step, "failed", error=str(exc), error_class=type(exc).__name__)
                if step.on_failure == "continue":
                    continue
                if step.on_failure == "pause":
                    self._pause(run, step)
                    return run
                run.exit_code = EXIT_GENERIC
                return run

            # Post-step autonomy hook (diff evaluation)
            if self.autonomy_enforcer is not None:
                try:
                    decision = self.autonomy_enforcer.after_step(run, step)
                except Exception as exc:
                    self._emit(run, step, "failed", error=str(exc), error_class="AutonomyPostError")
                    run.results.append(StepResult(step.id, step.prompt, "failed", error=str(exc), error_class="AutonomyPostError"))
                    run.exit_code = EXIT_GUARDRAIL_BLOCKED
                    return run
                if decision and decision.get("action") == "pause":
                    self._emit(run, step, "guardrail_triggered", status="pending",
                               guardrail_rule=decision.get("rule"))
                    self._pause(run, step, downgraded=True, guardrail=decision.get("rule"))
                    return run
                if decision and decision.get("action") == "block":
                    self._emit(run, step, "guardrail_triggered", status="failure",
                               guardrail_rule=decision.get("rule"))
                    run.exit_code = EXIT_GUARDRAIL_BLOCKED
                    return run

            # Pause-after gating
            if step.pause_after or step.id in self.workflow.review_after:
                self._pause(run, step)
                return run

        run.exit_code = EXIT_OK
        return run

    def run_full_lifecycle(
        self,
        context: dict[str, Any] | None = None,
        *,
        autonomy_level: str | None = None,
        workflow_run_id: str | None = None,
    ) -> WorkflowRun:
        """Execute a full lifecycle workflow in one pass.

        The concrete stage order is defined by the workflow file and is expected to
        include plan -> tasks -> analyze -> critic -> implement -> create-pr -> pr-review.
        """
        return self.run(
            context=context,
            autonomy_level=autonomy_level,
            workflow_run_id=workflow_run_id,
            start_at_step_id=None,
        )

    # ------------------------------------------------------------------ pause
    def _pause(
        self,
        run: WorkflowRun,
        completed_step: WorkflowStep,
        *,
        downgraded: bool = False,
        guardrail: str | None = None,
    ) -> None:
        next_step_id = self._next_step_id(completed_step.id)
        run.paused = True
        run.paused_after_step = completed_step.id
        run.next_step_id = next_step_id

        try:
            target = write_pause_state(
                self.repo_root,
                run,
                last_completed_step_id=completed_step.id,
                next_step_id=next_step_id,
            )
        except OSError as exc:
            print(f"[devspark] WARNING: failed to persist pause state: {exc}", file=sys.stderr)
            target = None

        # Resume hint to stderr (FR-007c)
        print(
            f"Paused. Resume with: devspark resume {run.workflow_run_id}",
            file=sys.stderr,
        )
        if target is not None:
            print(f"  pause-state: {target}", file=sys.stderr)
        if downgraded and guardrail:
            print(f"  reason: guardrail downgrade ({guardrail})", file=sys.stderr)

        self._emit(run, completed_step, "paused", status="pending")

    def _next_step_id(self, after_step_id: str) -> str | None:
        ids = [s.id for s in self.workflow.steps]
        try:
            i = ids.index(after_step_id)
        except ValueError:
            return None
        return ids[i + 1] if i + 1 < len(ids) else None

    # ----------------------------------------------------------------- emit
    def _emit(
        self,
        run: WorkflowRun,
        step: WorkflowStep,
        phase: str,
        *,
        status: str = "success",
        duration_ms: int = 0,
        error: str | None = None,
        error_class: str | None = None,
        guardrail_rule: str | None = None,
    ) -> None:
        if self.telemetry is None:
            return
        event = {
            "schema_version": "1",
            "event_id": str(uuid.uuid4()),
            "timestamp": _utcnow_iso(),
            "workflow_id": run.workflow_id,
            "workflow_run_id": run.workflow_run_id,
            "step_id": step.id,
            "phase": phase,
            "status": status,
            "duration_ms": int(duration_ms),
            "success": status == "success",
            "autonomy_level": run.autonomy_level,
            "guardrail_rule": guardrail_rule,
            "error": error,
        }
        if error_class is not None:
            event["error_class"] = error_class
        try:
            self.telemetry.write(event)
        except Exception as exc:  # fail-soft
            print(f"[devspark] telemetry write failed: {exc}", file=sys.stderr)
