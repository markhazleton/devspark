"""Result aggregation, artifact writing, context resolution, and replay for the DevSpark harness runtime."""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path

import yaml

from ..registry import get_app, load_registry
from ..scope import resolve_doc_root, resolve_scope
from .adapters import get_registered_adapters, probe_adapter
from .config import load_adapter_default
from .spec_loader import HarnessSpecError, load_harness_spec
from .spec_models import (
    ExecutionMode,
    HarnessSpec,
    Run,
    RunContext,
    RunMetrics,
    ScopeDeclaration,
    ValidationFinding,
)
from .telemetry import TelemetrySink, utc_now_iso
from .validation import ValidationEngine


def generate_run_id() -> str:
    """Generate a unique, time-stamped run identifier."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run_{stamp}_{secrets.token_hex(3)}"


def resolve_context(
    spec: HarnessSpec,
    repo_root: Path,
    spec_path: Path,
    adapter_override: str | None,
    use_adapter_default: bool,
    dry_run: bool,
    execution_mode: ExecutionMode,
    hands_off: bool,
) -> RunContext:
    """Resolve the run context from spec and runner configuration."""
    registry = None
    try:
        registry = load_registry(repo_root)
    except ValueError as exc:
        if "No multi-app registry found at" in str(exc):
            registry = None
        else:
            raise HarnessSpecError(str(exc)) from exc

    repo_scope = spec.scope.type == "repo"
    scope_ctx = resolve_scope(registry, spec.scope.app, repo_scope, repo_root)
    if scope_ctx.errors:
        raise HarnessSpecError("; ".join(scope_ctx.errors))

    app = None
    if registry is not None and spec.scope.type == "app" and spec.scope.app:
        app = get_app(registry, spec.scope.app)
    doc_root = resolve_doc_root(app, repo_root)

    stored_default = load_adapter_default() if use_adapter_default or adapter_override is None else None
    adapter_name = adapter_override or stored_default or spec.defaults.adapter or "noop"

    return RunContext(
        run_id=generate_run_id(),
        repo_root=str(repo_root),
        spec_path=str(spec_path),
        doc_root=str(doc_root.resolve()),
        adapter=adapter_name,
        dry_run=dry_run,
        execution_mode=execution_mode,
        hands_off=hands_off,
    )


def prepare_run(spec: HarnessSpec, context: RunContext) -> tuple[Run, Path, TelemetrySink]:
    """Create run directory structure, telemetry sink, and Run object; write initial artifacts."""
    run_dir_root = Path(spec.telemetry.run_dir)
    run_dir_root.mkdir(parents=True, exist_ok=True)
    run_dir = run_dir_root / context.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "steps").mkdir(parents=True, exist_ok=True)
    telemetry = TelemetrySink(run_dir / "events.jsonl", enabled=spec.telemetry.emit_jsonl)
    run = Run(
        run_id=context.run_id,
        status="running",
        harness_name=spec.name,
        api_version=spec.apiVersion,
        scope=ScopeDeclaration.model_validate(spec.scope.model_dump()),
        started_at=utc_now_iso(),
        context=context,
        metrics=RunMetrics(steps_total=len(spec.steps)),
    )
    write_supporting_artifacts(run_dir, spec, context)
    telemetry.emit(
        "harness.run.started",
        run.run_id,
        harness_name=run.harness_name,
        api_version=run.api_version,
        scope=run.scope.model_dump(exclude_none=True),
        adapter=context.adapter,
        dry_run=context.dry_run,
        hands_off=context.hands_off,
    )
    write_adapter_doctor_artifact(run_dir, context)
    return run, run_dir, telemetry


def write_supporting_artifacts(run_dir: Path, spec: HarnessSpec, context: RunContext) -> None:
    """Write spec.resolved.yaml and context.json into the run directory."""
    (run_dir / "spec.resolved.yaml").write_text(
        yaml.safe_dump(spec.model_dump(mode="json", exclude_none=True), sort_keys=False),
        encoding="utf-8",
    )
    (run_dir / "context.json").write_text(
        json.dumps(context.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )


def write_adapter_doctor_artifact(run_dir: Path, context: RunContext) -> None:
    """Write adapter-doctor.json into the run directory."""
    profiles = [
        probe_adapter(adapter_name).model_dump(mode="json")
        for adapter_name in get_registered_adapters().keys()
    ]
    payload = {
        "selected_adapter": context.adapter,
        "profiles": profiles,
        "generated_at": utc_now_iso(),
    }
    (run_dir / "adapter-doctor.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def write_result(run_dir: Path | None, run: Run) -> None:
    """Serialize the Run object to result.json in the run directory."""
    if run_dir is None:
        return
    (run_dir / "result.json").write_text(
        json.dumps(run.model_dump(mode="json", exclude_none=True), indent=2) + "\n",
        encoding="utf-8",
    )


def write_lifecycle_artifacts(run_dir: Path | None, run: Run) -> None:
    """Write findings and stage iteration records into lifecycle/ sub-directory."""
    if run_dir is None:
        return
    if run.stage_iterations:
        iterations_path = run_dir / "lifecycle" / "stage-iterations.json"
        iterations_path.parent.mkdir(parents=True, exist_ok=True)
        iterations_path.write_text(
            json.dumps(
                [rec.model_dump(mode="json") for rec in run.stage_iterations],
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
    if run.findings:
        findings_path = run_dir / "lifecycle" / "findings.json"
        findings_path.parent.mkdir(parents=True, exist_ok=True)
        findings_path.write_text(
            json.dumps(
                [f.model_dump(mode="json") for f in run.findings],
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )


def write_final_decision_packet(run_dir: Path | None, run: Run) -> None:
    """Write decision-packet.json summarising workflow/delivery status."""
    if run_dir is None:
        return
    payload = {
        "run_id": run.run_id,
        "workflow_status": run.workflow_status,
        "delivery_status": run.delivery_status,
        "create_pr_ready": run.create_pr_ready,
        "failure_reason_code": run.failure_reason_code,
        "generated_at": utc_now_iso(),
    }
    (run_dir / "decision-packet.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def replay(run_dir: Path) -> dict:
    """Re-evaluate validation rules for a completed run against the current filesystem state."""
    spec_path = run_dir / "spec.resolved.yaml"
    context_path = run_dir / "context.json"

    if not spec_path.is_file():
        raise HarnessSpecError(f"spec.resolved.yaml not found in run dir: {run_dir}")
    if not context_path.is_file():
        raise HarnessSpecError(f"context.json not found in run dir: {run_dir}")

    context_data = json.loads(context_path.read_text(encoding="utf-8"))
    repo_root = Path(context_data["repo_root"])

    spec = load_harness_spec(spec_path, repo_root)
    context = RunContext.model_validate(context_data)

    result_path = run_dir / "result.json"
    original_result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.is_file() else {}
    original_step_statuses = {s["step_id"]: s["status"] for s in original_result.get("steps", [])}

    engine = ValidationEngine()
    replay_steps = []
    replayed_at = utc_now_iso()
    replay_run_id = f"replay_{run_dir.name}"

    replay_events_path = run_dir / "replay_events.jsonl"
    telemetry = TelemetrySink(replay_events_path, enabled=True)
    telemetry.emit(
        "harness.run.replayed",
        replay_run_id,
        original_run_id=context_data.get("run_id", ""),
        replayed_at=replayed_at,
    )

    for step in spec.steps:
        step_dir = run_dir / "steps" / step.id
        step_dir.mkdir(parents=True, exist_ok=True)

        deterministic_rules = [r for r in step.validation if r.type != "llm.rubric"]
        rubric_rules = [r for r in step.validation if r.type == "llm.rubric"]

        findings = []
        for rule in deterministic_rules:
            finding = engine.evaluate(rule, context, step_dir)
            findings.append(finding)

        has_det_errors = any(f.status == "failed" and f.severity == "error" for f in findings)

        for rule in rubric_rules:
            if has_det_errors:
                finding = ValidationFinding(
                    rule_id=rule.id,
                    type=rule.type,
                    status="skipped",
                    severity=rule.severity,
                    message="Skipped: deterministic error-severity rule failed",
                )
            else:
                finding = engine.evaluate(rule, context, step_dir)
            findings.append(finding)

        failed_errors = [f for f in findings if f.status == "failed" and f.severity == "error"]
        replayed_status = "passed" if not failed_errors else "failed"
        original_status = original_step_statuses.get(step.id, "unknown")

        replay_steps.append(
            {
                "step_id": step.id,
                "original_status": original_status,
                "replayed_status": replayed_status,
                "validation_findings": [f.model_dump() for f in findings],
            }
        )

    replay_result = {
        "replayed_at": replayed_at,
        "original_run_id": context_data.get("run_id", ""),
        "run_dir": str(run_dir),
        "steps": replay_steps,
    }
    (run_dir / "replay_result.json").write_text(
        json.dumps(replay_result, indent=2) + "\n", encoding="utf-8"
    )
    return replay_result


def prune_old_runs(run_dir_root: Path, keep: int) -> None:
    """Remove oldest run directories beyond the keep limit."""
    if keep < 1 or not run_dir_root.is_dir():
        return
    dirs = sorted(
        (p for p in run_dir_root.iterdir() if p.is_dir()),
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )
    for stale in dirs[keep:]:
        for child in sorted(stale.rglob("*"), reverse=True):
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
        stale.rmdir()


def finalize_run_artifacts(
    run: Run,
    spec: HarnessSpec,
    run_dir: Path | None,
    telemetry: TelemetrySink,
    started: float,
    retention_limit: int,
) -> None:
    """Set completion timestamps, emit telemetry, write artifacts, and prune old runs."""
    import time

    run.finished_at = utc_now_iso()
    run.metrics.duration_ms = int((time.perf_counter() - started) * 1000)
    for check in run.delivery_checks:
        telemetry.emit(
            "harness.delivery.check", run.run_id,
            check_id=check.check_id, check_type=check.check_type,
            required=check.required, status=check.status, details=check.details,
        )
    telemetry.emit(
        "harness.run.finished", run.run_id,
        status=run.status, workflow_status=run.workflow_status,
        delivery_status=run.delivery_status, create_pr_ready=run.create_pr_ready,
        duration_ms=run.metrics.duration_ms, steps_total=run.metrics.steps_total,
        validation_failures=run.metrics.validation_failures,
    )
    write_result(run_dir, run)
    write_lifecycle_artifacts(run_dir, run)
    write_final_decision_packet(run_dir, run)
    prune_old_runs(Path(spec.telemetry.run_dir), retention_limit)
