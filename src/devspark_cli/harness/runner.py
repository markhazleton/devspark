"""Harness runtime execution and validation."""

from __future__ import annotations

import json
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

from ..registry import get_app, load_registry
from ..scope import resolve_doc_root, resolve_scope
from .adapters.base import AgentAdapter
from .adapters.manual import ManualAdapter
from .adapters.noop import NoopAdapter
from .config import load_adapter_default, load_run_retention_limit
from .spec_loader import HarnessSpecError, default_retry_policy, discover_repo_root, load_harness_spec
from .spec_models import (
    ArtifactDelta,
    HarnessSpec,
    Run,
    RunContext,
    RunMetrics,
    ScopeDeclaration,
    StepResult,
    StepSpec,
    ValidationFinding,
)
from .telemetry import TelemetrySink, utc_now_iso
from .validation import ValidationEngine


DEFAULT_RETENTION = 20


def generate_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run_{stamp}_{secrets.token_hex(3)}"


class HarnessRunner:
    """Load and execute a harness spec."""

    def __init__(
        self,
        spec_file: str | Path,
        *,
        adapter_override: str | None = None,
        use_adapter_default: bool = False,
        dry_run: bool = False,
        repo_root: str | Path | None = None,
    ) -> None:
        self.spec_path = Path(spec_file).resolve()
        self.repo_root = Path(repo_root).resolve() if repo_root is not None else discover_repo_root(self.spec_path, Path.cwd())
        self.adapter_override = adapter_override
        self.use_adapter_default = use_adapter_default
        self.dry_run = dry_run
        self.spec: HarnessSpec | None = None
        self.context: RunContext | None = None
        self.run: Run | None = None
        self.run_dir: Path | None = None
        self.telemetry: TelemetrySink | None = None
        self._step_lookup: dict[str, int] = {}
        self.validation_engine = ValidationEngine()

    def load_spec(self) -> HarnessSpec:
        self.spec = load_harness_spec(self.spec_path, self.repo_root)
        self._step_lookup = {step.id: index for index, step in enumerate(self.spec.steps)}
        return self.spec

    def resolve_context(self) -> RunContext:
        spec = self.spec or self.load_spec()
        registry = None
        try:
            registry = load_registry(self.repo_root)
        except ValueError:
            registry = None

        repo_scope = spec.scope.type == "repo"
        scope_ctx = resolve_scope(registry, spec.scope.app, repo_scope, self.repo_root)
        if scope_ctx.errors:
            raise HarnessSpecError("; ".join(scope_ctx.errors))

        app = None
        if registry is not None and spec.scope.type == "app" and spec.scope.app:
            app = get_app(registry, spec.scope.app)
        doc_root = resolve_doc_root(app, self.repo_root)

        adapter_name = self.resolve_run_adapter(spec)
        self.context = RunContext(
            run_id=generate_run_id(),
            repo_root=str(self.repo_root),
            spec_path=str(self.spec_path),
            doc_root=str(doc_root.resolve()),
            adapter=adapter_name,
            dry_run=self.dry_run,
        )
        return self.context

    def resolve_run_adapter(self, spec: HarnessSpec | None = None) -> str:
        spec = spec or self.spec or self.load_spec()
        stored_default = load_adapter_default() if self.use_adapter_default or self.adapter_override is None else None
        return self.adapter_override or stored_default or spec.defaults.adapter or "noop"

    def resolve_step_adapter(self, step: StepSpec, spec: HarnessSpec) -> str:
        if step.type == "validation":
            return "validation"
        stored_default = load_adapter_default() if self.use_adapter_default or self.adapter_override is None else None
        return self.adapter_override or step.adapter or stored_default or spec.defaults.adapter or "noop"

    def get_adapter(self, name: str) -> AgentAdapter:
        adapters: dict[str, AgentAdapter] = {
            "noop": NoopAdapter(),
            "manual": ManualAdapter(),
        }
        if name not in adapters:
            raise HarnessSpecError(f"Unknown adapter: {name}")
        return adapters[name]

    def prepare_run(self) -> tuple[Run, Path]:
        spec = self.spec or self.load_spec()
        context = self.context or self.resolve_context()
        run_dir_root = Path(spec.telemetry.run_dir)
        run_dir_root.mkdir(parents=True, exist_ok=True)
        run_dir = run_dir_root / context.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "steps").mkdir(parents=True, exist_ok=True)
        self.run_dir = run_dir
        self.telemetry = TelemetrySink(run_dir / "events.jsonl", enabled=spec.telemetry.emit_jsonl)
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
        self.run = run
        self.write_supporting_artifacts()
        self.telemetry.emit(
            "harness.run.started",
            run.run_id,
            harness_name=run.harness_name,
            api_version=run.api_version,
            scope=run.scope.model_dump(exclude_none=True),
            adapter=context.adapter,
            dry_run=context.dry_run,
        )
        return run, run_dir

    def write_supporting_artifacts(self) -> None:
        if self.run_dir is None or self.spec is None or self.context is None:
            return
        (self.run_dir / "spec.resolved.yaml").write_text(
            yaml.safe_dump(self.spec.model_dump(mode="json", exclude_none=True), sort_keys=False),
            encoding="utf-8",
        )
        (self.run_dir / "context.json").write_text(
            json.dumps(self.context.model_dump(mode="json"), indent=2) + "\n",
            encoding="utf-8",
        )

    def write_result(self) -> None:
        if self.run_dir is None or self.run is None:
            return
        (self.run_dir / "result.json").write_text(
            json.dumps(self.run.model_dump(mode="json", exclude_none=True), indent=2) + "\n",
            encoding="utf-8",
        )

    def execute(self) -> Run:
        spec = self.spec or self.load_spec()
        run, _ = self.prepare_run()
        started = time.perf_counter()
        current_index = 0
        try:
            while current_index < len(spec.steps):
                step = spec.steps[current_index]
                result, next_step = self.execute_step(step)
                run.steps.append(result)
                if result.status == "passed":
                    run.metrics.steps_passed += 1
                elif result.status == "failed":
                    run.metrics.steps_failed += 1
                run.metrics.validation_failures += sum(
                    1 for finding in result.validation_findings if finding.status == "failed" and finding.severity == "error"
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

        run.finished_at = utc_now_iso()
        run.metrics.duration_ms = int((time.perf_counter() - started) * 1000)
        assert self.telemetry is not None
        self.telemetry.emit(
            "harness.run.finished",
            run.run_id,
            status=run.status,
            duration_ms=run.metrics.duration_ms,
            steps_total=run.metrics.steps_total,
            validation_failures=run.metrics.validation_failures,
        )
        self.write_result()
        self.prune_old_runs(Path(spec.telemetry.run_dir), keep=load_run_retention_limit())
        return run

    def execute_step(self, step: StepSpec) -> tuple[StepResult, int | None]:
        assert self.spec is not None
        assert self.context is not None
        assert self.run_dir is not None
        assert self.telemetry is not None

        step_dir = self.run_dir / "steps" / step.id
        step_dir.mkdir(parents=True, exist_ok=True)

        retry = step.retry or self.spec.defaults.retry or default_retry_policy()
        adapter_name = self.resolve_step_adapter(step, self.spec)

        if self.dry_run:
            self.telemetry.emit("harness.step.started", self.context.run_id, step_id=step.id, attempt=0, adapter=adapter_name)
            self.telemetry.emit(
                "harness.step.finished",
                self.context.run_id,
                step_id=step.id,
                attempt=0,
                status="skipped_dry_run",
                duration_ms=0,
            )
            result = StepResult(step_id=step.id, status="skipped_dry_run", attempts=0, adapter=adapter_name)
            return result, self.next_step_index(step, success=True)

        last_findings: list[ValidationFinding] = []
        total_duration = 0
        attempts = 0
        prompt_override: str | None = None
        for attempt in range(1, retry.maxAttempts + 1):
            attempts = attempt
            attempt_started = time.perf_counter()
            self.telemetry.emit("harness.step.started", self.context.run_id, step_id=step.id, attempt=attempt, adapter=adapter_name)
            try:
                if step.type != "validation":
                    adapter = self.get_adapter(adapter_name)
                    available, reason = adapter.is_available()
                    if not available:
                        message = reason or f"adapter {adapter_name} not available"
                        self.telemetry.emit("harness.policy.blocked", self.context.run_id, step_id=step.id, reason=message)
                        raise RuntimeError(message)
                    response = adapter.execute(step, self.context, self.telemetry, prompt_text=prompt_override)
                    if response.prompt_text:
                        (step_dir / "prompt.md").write_text(response.prompt_text, encoding="utf-8")
                    if response.output_text:
                        (step_dir / "output.txt").write_text(response.output_text, encoding="utf-8")
                last_findings = self.evaluate_step_validations(step, step_dir)
                failed_errors = [finding for finding in last_findings if finding.status == "failed" and finding.severity == "error"]
                duration_ms = int((time.perf_counter() - attempt_started) * 1000)
                total_duration += duration_ms
                status = "passed" if not failed_errors else "failed"
                self.telemetry.emit(
                    "harness.step.finished",
                    self.context.run_id,
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
                        artifacts=ArtifactDelta(),
                    )
                    return result, self.next_step_index(step, success=True)
                if attempt < retry.maxAttempts and "validation_fail" in retry.retryOn:
                    prompt_override = self.build_retry_prompt(step, failed_errors, retry)
                    if retry.requireHumanAfter is not None and attempt >= retry.requireHumanAfter:
                        self.pause_for_human_review(step, prompt_override or "", step_dir)
                    continue
                result = StepResult(
                    step_id=step.id,
                    status="failed",
                    attempts=attempt,
                    adapter=adapter_name,
                    duration_ms=total_duration,
                    validation_findings=last_findings,
                    artifacts=ArtifactDelta(),
                )
                return result, self.next_step_index(step, success=False)
            except KeyboardInterrupt:
                duration_ms = int((time.perf_counter() - attempt_started) * 1000)
                total_duration += duration_ms
                self.telemetry.emit(
                    "harness.step.finished",
                    self.context.run_id,
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
                    artifacts=ArtifactDelta(),
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
                self.telemetry.emit(
                    "harness.step.finished",
                    self.context.run_id,
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
                    artifacts=ArtifactDelta(),
                )
                return result, self.next_step_index(step, success=False)

        result = StepResult(
            step_id=step.id,
            status="failed",
            attempts=attempts,
            adapter=adapter_name,
            duration_ms=total_duration,
            validation_findings=last_findings,
            artifacts=ArtifactDelta(),
        )
        return result, self.next_step_index(step, success=False)

    def next_step_index(self, step: StepSpec, success: bool) -> int | None:
        target = step.on_success if success else step.on_failure
        if target:
            return self._step_lookup[target]
        if success:
            return None
        return None

    def evaluate_step_validations(self, step: StepSpec, step_dir: Path) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        for rule in step.validation:
            finding = self.validation_engine.evaluate(rule, self.context, step_dir)
            findings.append(finding)
            assert self.telemetry is not None
            assert self.context is not None
            self.telemetry.emit(
                "harness.step.validation",
                self.context.run_id,
                step_id=step.id,
                rule_id=rule.id,
                rule_type=rule.type,
                status=finding.status,
                severity=finding.severity,
                message=finding.message,
            )
        return findings

    def build_retry_prompt(self, step: StepSpec, failed_errors: list[ValidationFinding], retry) -> str | None:
        parts: list[str] = []
        if step.prompt_file:
            parts.append(Path(step.prompt_file).read_text(encoding="utf-8"))
        if retry.repairPrompt:
            parts.append(Path(retry.repairPrompt).read_text(encoding="utf-8"))
        lines = ["## Validation Errors"]
        lines.extend(f"- {finding.rule_id}: {finding.message}" for finding in failed_errors)
        parts.append("\n".join(lines))
        return "\n\n".join(part for part in parts if part)

    def pause_for_human_review(self, step: StepSpec, prompt_text: str, step_dir: Path) -> None:
        assert self.context is not None
        assert self.telemetry is not None
        manual_step = StepSpec.model_validate(
            {
                "id": f"{step.id}-human-review",
                "name": f"Human Review for {step.name or step.id}",
                "type": "human_gate",
                "mode": "manual",
                "adapter": "manual",
                "prompt_file": step.prompt_file or self.context.spec_path,
            }
        )
        ManualAdapter().execute(manual_step, self.context, self.telemetry, prompt_text=prompt_text)
        (step_dir / "prompt.md").write_text(prompt_text, encoding="utf-8")

    def prune_old_runs(self, run_dir_root: Path, keep: int = DEFAULT_RETENTION) -> None:
        if keep < 1 or not run_dir_root.is_dir():
            return
        run_dirs = sorted((path for path in run_dir_root.iterdir() if path.is_dir()), key=lambda item: item.stat().st_mtime, reverse=True)
        for stale in run_dirs[keep:]:
            for child in sorted(stale.rglob("*"), reverse=True):
                if child.is_file():
                    child.unlink()
                elif child.is_dir():
                    child.rmdir()
            stale.rmdir()


def run_status_to_exit_code(status: str) -> int:
    if status == "complete":
        return 0
    if status == "aborted":
        return 2
    return 1