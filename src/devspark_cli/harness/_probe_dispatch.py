"""Probe dispatch and result collection for the DevSpark harness runtime."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from .adapters import get_registered_adapters, probe_adapter
from .adapters.base import AgentAdapter
from .adapters.manual import ManualAdapter
from .config import load_adapter_default, load_manual_gate_policy
from .spec_loader import HarnessSpecError, default_retry_policy
from .spec_models import (
    ArtifactDelta,
    HarnessSpec,
    REASON_CODE_DECODE_REPLACEMENT,
    REASON_CODE_STEP_TIMEOUT,
    RetryPolicy,
    RunContext,
    StepResult,
    StepSpec,
    ValidationFinding,
)
from .telemetry import TelemetrySink
from .validation import ValidationEngine


def snapshot_outputs(paths: list[str]) -> dict[str, tuple[float, int] | None]:
    """Capture mtime+size for each declared output path, or None if missing."""
    result: dict[str, tuple[float, int] | None] = {}
    for p in paths:
        path = Path(p)
        if path.exists():
            stat = path.stat()
            result[p] = (stat.st_mtime, stat.st_size)
        else:
            result[p] = None
    return result


def diff_snapshots(
    before: dict[str, tuple[float, int] | None],
    after: dict[str, tuple[float, int] | None],
) -> ArtifactDelta:
    """Compare before/after snapshots and return populated ArtifactDelta."""
    created: list[str] = []
    modified: list[str] = []
    deleted: list[str] = []
    all_paths = sorted(set(before) | set(after))
    for p in all_paths:
        b, a = before.get(p), after.get(p)
        if b is None and a is not None:
            created.append(p)
        elif b is not None and a is None:
            deleted.append(p)
        elif b is not None and a is not None and b != a:
            modified.append(p)
    return ArtifactDelta(created=created, modified=modified, deleted=deleted)


def compute_artifacts(
    step: StepSpec,
    before_snapshot: dict,
    telemetry: TelemetrySink | None,
    context: RunContext | None,
) -> ArtifactDelta:
    """Compute artifact delta from declared outputs and emit telemetry."""
    delta = diff_snapshots(before_snapshot, snapshot_outputs(step.outputs))
    if telemetry is not None and context is not None:
        telemetry.emit(
            "harness.step.artifacts",
            context.run_id,
            step_id=step.id,
            created=delta.created,
            modified=delta.modified,
            deleted=delta.deleted,
        )
    return delta


def resolve_step_adapter(
    step: StepSpec,
    spec: HarnessSpec,
    adapter_override: str | None,
    use_adapter_default: bool,
) -> str:
    """Return the effective adapter name for a given step."""
    if step.type == "validation":
        return "validation"
    stored_default = load_adapter_default() if use_adapter_default or adapter_override is None else None
    return adapter_override or step.adapter or stored_default or spec.defaults.adapter or "noop"


def get_adapter(name: str) -> AgentAdapter:
    """Return the registered adapter for the given name."""
    adapters = get_registered_adapters()
    if name not in adapters:
        raise HarnessSpecError(f"Unknown adapter: {name}")
    return adapters[name]


def is_write_required_step(step: StepSpec) -> bool:
    """Return True if the step id indicates a write-required operation."""
    lowered = step.id.lower()
    return any(marker in lowered for marker in ("implement", "create-pr", "pr-review"))


def enforce_write_capability(step: StepSpec, adapter_name: str, hands_off: bool) -> None:
    """Raise RuntimeError if a write-required step uses an incompatible adapter."""
    if not hands_off or not is_write_required_step(step):
        return
    profile = probe_adapter(adapter_name)
    if profile.state in ("write_incompatible", "unavailable", "write_approval_required"):
        details = profile.remediation_guidance or "Select a write-capable non-interactive adapter."
        raise RuntimeError(
            f"write_incompatible_adapter: step={step.id} adapter={adapter_name} state={profile.state}. {details}"
        )


def next_step_index(step: StepSpec, step_lookup: dict[str, int], success: bool) -> int | None:
    """Return the next step index based on on_success/on_failure routing."""
    target = step.on_success if success else step.on_failure
    if target:
        return step_lookup[target]
    return None


def build_retry_prompt(step: StepSpec, failed_errors: list[ValidationFinding], retry: RetryPolicy) -> str | None:
    """Build a retry prompt by combining the step prompt, repair prompt, and validation errors."""
    parts: list[str] = []
    if step.prompt_file:
        parts.append(Path(step.prompt_file).read_text(encoding="utf-8"))
    if retry.repairPrompt:
        parts.append(Path(retry.repairPrompt).read_text(encoding="utf-8"))
    lines = ["## Validation Errors"]
    lines.extend(f"- {finding.rule_id}: {finding.message}" for finding in failed_errors)
    parts.append("\n".join(lines))
    return "\n\n".join(part for part in parts if part)


def pause_for_human_review(
    step: StepSpec,
    prompt_text: str,
    step_dir: Path,
    context: RunContext,
    telemetry: TelemetrySink,
) -> None:
    """Pause and prompt a human reviewer, or bypass in hands-off mode."""
    if context.hands_off:
        telemetry.emit(
            "harness.policy.blocked",
            context.run_id,
            step_id=step.id,
            reason="hands_off_manual_prompt_bypassed",
        )
        return

    policy = load_manual_gate_policy()
    if policy == "confirm-with-file-check" and not (step_dir / "output.txt").exists():
        raise RuntimeError(f"manual_gate_policy_blocked: {policy} requires output.txt for step {step.id}")
    if policy == "confirm-with-git-diff-check":
        status = subprocess.run(
            ["git", "diff", "--name-only", "--", "src/", "test/"],
            cwd=context.repo_root,
            text=True,
            errors="replace",
            capture_output=True,
            check=False,
        )
        if status.returncode != 0 or not (status.stdout or "").strip():
            raise RuntimeError(f"manual_gate_policy_blocked: {policy} requires changes under src/ or test/")

    manual_step = StepSpec.model_validate(
        {
            "id": f"{step.id}-human-review",
            "name": f"Human Review for {step.name or step.id}",
            "type": "human_gate",
            "mode": "manual",
            "adapter": "manual",
            "prompt_file": step.prompt_file or context.spec_path,
        }
    )
    ManualAdapter().execute(manual_step, context, telemetry, prompt_text=prompt_text)
    (step_dir / "prompt.md").write_text(prompt_text, encoding="utf-8")


def evaluate_step_validations(
    step: StepSpec,
    step_dir: Path,
    context: RunContext,
    telemetry: TelemetrySink,
    engine: ValidationEngine,
) -> list[ValidationFinding]:
    """Evaluate all validation rules for a step, deterministic-first."""
    findings: list[ValidationFinding] = []

    deterministic_rules = [r for r in step.validation if r.type != "llm.rubric"]
    rubric_rules = [r for r in step.validation if r.type == "llm.rubric"]

    for rule in deterministic_rules:
        finding = engine.evaluate(rule, context, step_dir)
        findings.append(finding)
        telemetry.emit(
            "harness.step.validation",
            context.run_id,
            step_id=step.id,
            rule_id=rule.id,
            rule_type=rule.type,
            status=finding.status,
            severity=finding.severity,
            message=finding.message,
        )
        if "timed out" in finding.message.lower():
            telemetry.emit(
                "harness.step.incident",
                context.run_id,
                step_id=step.id,
                reason_code=REASON_CODE_STEP_TIMEOUT,
                rule_id=rule.id,
                non_fatal=True,
            )
        if "decode replacements applied" in finding.message.lower():
            telemetry.emit(
                "harness.step.incident",
                context.run_id,
                step_id=step.id,
                reason_code=REASON_CODE_DECODE_REPLACEMENT,
                rule_id=rule.id,
                non_fatal=True,
            )

    has_deterministic_errors = any(f.status == "failed" and f.severity == "error" for f in findings)

    for rule in rubric_rules:
        if has_deterministic_errors:
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
        telemetry.emit(
            "harness.step.validation",
            context.run_id,
            step_id=step.id,
            rule_id=rule.id,
            rule_type=rule.type,
            status=finding.status,
            severity=finding.severity,
            message=finding.message,
        )
        if "timed out" in finding.message.lower():
            telemetry.emit(
                "harness.step.incident",
                context.run_id,
                step_id=step.id,
                reason_code=REASON_CODE_STEP_TIMEOUT,
                rule_id=rule.id,
                non_fatal=True,
            )
        if "decode replacements applied" in finding.message.lower():
            telemetry.emit(
                "harness.step.incident",
                context.run_id,
                step_id=step.id,
                reason_code=REASON_CODE_DECODE_REPLACEMENT,
                rule_id=rule.id,
                non_fatal=True,
            )

    return findings


def execute_step(
    step: StepSpec,
    spec: HarnessSpec,
    context: RunContext,
    run_dir: Path,
    telemetry: TelemetrySink,
    step_lookup: dict[str, int],
    validation_engine: ValidationEngine,
    dry_run: bool,
    hands_off: bool,
    adapter_override: str | None,
    use_adapter_default: bool,
) -> tuple[StepResult, int | None]:
    """Execute a single harness step with retry logic and validation."""
    step_dir = run_dir / "steps" / step.id
    step_dir.mkdir(parents=True, exist_ok=True)

    retry = step.retry or spec.defaults.retry or default_retry_policy()
    adapter_name = resolve_step_adapter(step, spec, adapter_override, use_adapter_default)

    if dry_run:
        telemetry.emit("harness.step.started", context.run_id, step_id=step.id, attempt=0, adapter=adapter_name)
        telemetry.emit(
            "harness.step.finished",
            context.run_id,
            step_id=step.id,
            attempt=0,
            status="skipped_dry_run",
            duration_ms=0,
        )
        result = StepResult(step_id=step.id, status="skipped_dry_run", attempts=0, adapter=adapter_name)
        return result, next_step_index(step, step_lookup, success=True)

    before_snapshot = snapshot_outputs(step.outputs)
    last_findings: list[ValidationFinding] = []
    total_duration = 0
    attempts = 0
    prompt_override: str | None = None
    for attempt in range(1, retry.maxAttempts + 1):
        attempts = attempt
        attempt_started = time.perf_counter()
        telemetry.emit("harness.step.started", context.run_id, step_id=step.id, attempt=attempt, adapter=adapter_name)
        try:
            if step.type != "validation":
                adapter = get_adapter(adapter_name)
                if hands_off and adapter_name == "manual":
                    profile = probe_adapter(adapter_name)
                    details = profile.remediation_guidance or "Select a non-interactive adapter for hands-off mode."
                    message = (
                        f"write_incompatible_adapter: step={step.id} adapter={adapter_name} "
                        f"state={profile.state}. {details}"
                    )
                    telemetry.emit(
                        "harness.policy.blocked",
                        context.run_id,
                        step_id=step.id,
                        reason=message,
                    )
                    raise RuntimeError(message)
                enforce_write_capability(step, adapter_name, hands_off)
                available, reason = adapter.is_available()
                if not available:
                    message = reason or f"adapter {adapter_name} not available"
                    telemetry.emit("harness.policy.blocked", context.run_id, step_id=step.id, reason=message)
                    raise RuntimeError(message)
                response = adapter.execute(step, context, telemetry, prompt_text=prompt_override)
                if response.prompt_text:
                    (step_dir / "prompt.md").write_text(response.prompt_text, encoding="utf-8")
                if response.output_text:
                    (step_dir / "output.txt").write_text(response.output_text, encoding="utf-8")
            last_findings = evaluate_step_validations(step, step_dir, context, telemetry, validation_engine)
            failed_errors = [f for f in last_findings if f.status == "failed" and f.severity == "error"]
            duration_ms = int((time.perf_counter() - attempt_started) * 1000)
            total_duration += duration_ms
            status = "passed" if not failed_errors else "failed"
            telemetry.emit(
                "harness.step.finished",
                context.run_id,
                step_id=step.id,
                attempt=attempt,
                status=status,
                duration_ms=duration_ms,
            )
            if not failed_errors:
                result = StepResult(
                    step_id=step.id,
                    status="passed",
                    attempts=attempt,
                    adapter=adapter_name,
                    duration_ms=total_duration,
                    validation_findings=last_findings,
                    artifacts=compute_artifacts(step, before_snapshot, telemetry, context),
                )
                return result, next_step_index(step, step_lookup, success=True)
            if attempt < retry.maxAttempts and "validation_fail" in retry.retryOn:
                prompt_override = build_retry_prompt(step, failed_errors, retry)
                if retry.requireHumanAfter is not None and attempt >= retry.requireHumanAfter:
                    pause_for_human_review(step, prompt_override or "", step_dir, context, telemetry)
                continue
            result = StepResult(
                step_id=step.id,
                status="failed",
                attempts=attempt,
                adapter=adapter_name,
                duration_ms=total_duration,
                validation_findings=last_findings,
                artifacts=compute_artifacts(step, before_snapshot, telemetry, context),
            )
            return result, next_step_index(step, step_lookup, success=False)
        except KeyboardInterrupt:
            duration_ms = int((time.perf_counter() - attempt_started) * 1000)
            total_duration += duration_ms
            telemetry.emit(
                "harness.step.finished",
                context.run_id,
                step_id=step.id,
                attempt=attempt,
                status="aborted",
                duration_ms=duration_ms,
            )
            result = StepResult(
                step_id=step.id,
                status="aborted",
                attempts=attempt,
                adapter=adapter_name,
                duration_ms=total_duration,
                validation_findings=last_findings,
                artifacts=compute_artifacts(step, before_snapshot, telemetry, context),
            )
            return result, None
        except Exception as exc:
            duration_ms = int((time.perf_counter() - attempt_started) * 1000)
            total_duration += duration_ms
            finding = ValidationFinding(
                rule_id="adapter.execution",
                type="tool_error",
                status="failed",
                severity="error",
                message=str(exc),
            )
            last_findings = [finding]
            telemetry.emit(
                "harness.step.finished",
                context.run_id,
                step_id=step.id,
                attempt=attempt,
                status="failed",
                duration_ms=duration_ms,
            )
            if attempt < retry.maxAttempts and "tool_error" in retry.retryOn:
                continue
            result = StepResult(
                step_id=step.id,
                status="failed",
                attempts=attempt,
                adapter=adapter_name,
                duration_ms=total_duration,
                validation_findings=last_findings,
                artifacts=compute_artifacts(step, before_snapshot, telemetry, context),
            )
            return result, next_step_index(step, step_lookup, success=False)

    result = StepResult(
        step_id=step.id,
        status="failed",
        attempts=attempts,
        adapter=adapter_name,
        duration_ms=total_duration,
        validation_findings=last_findings,
        artifacts=compute_artifacts(step, before_snapshot, telemetry, context),
    )
    return result, next_step_index(step, step_lookup, success=False)


def run_step_loop(run: object, spec: HarnessSpec, execute_step_fn: object) -> None:
    """Run the main step execution loop, updating run metrics and status in-place."""
    from typing import Callable
    from .spec_models import Run as _Run
    assert isinstance(run, _Run)
    _fn: Callable[[StepSpec], tuple[StepResult, int | None]] = execute_step_fn  # type: ignore[assignment]
    current_index = 0
    try:
        while current_index < len(spec.steps):
            step = spec.steps[current_index]
            result, next_step = _fn(step)
            run.steps.append(result)
            if result.status == "passed":
                run.metrics.steps_passed += 1
            elif result.status == "failed":
                run.metrics.steps_failed += 1
            run.metrics.validation_failures += sum(
                1 for f in result.validation_findings if f.status == "failed" and f.severity == "error"
            )
            if result.status == "failed" and next_step is None:
                run.status = "failed"
                break
            if result.status == "aborted":
                run.status = "aborted"
                break
            current_index = next_step if next_step is not None else current_index + 1
        else:
            if run.status == "running":
                run.status = "complete"
    except KeyboardInterrupt:
        run.status = "aborted"
