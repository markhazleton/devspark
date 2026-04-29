"""Harness runtime execution and validation."""

from __future__ import annotations

import json
import secrets
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

from ..registry import get_app, load_registry
from ..scope import resolve_doc_root, resolve_scope
from .adapters import get_registered_adapters
from .adapters.base import AgentAdapter
from .adapters.manual import ManualAdapter
from .config import load_adapter_default, load_run_retention_limit
from .spec_loader import HarnessSpecError, default_retry_policy, discover_repo_root, load_harness_spec
from .spec_models import (
    ArtifactDelta,
    DeliveryCheckResult,
    DeliveryStatus,
    ExecutionMode,
    HarnessSpec,
    REASON_CODE_CREATE_PR_BLOCKED,
    REASON_CODE_DECODE_REPLACEMENT,
    REASON_CODE_DELIVERY_UNMET,
    REASON_CODE_STEP_TIMEOUT,
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


def _snapshot_outputs(paths: list[str]) -> dict[str, tuple[float, int] | None]:
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


def _diff_snapshots(
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
        execution_mode: ExecutionMode = "act",
    ) -> None:
        self.spec_path = Path(spec_file).resolve()
        self.repo_root = Path(repo_root).resolve() if repo_root is not None else discover_repo_root(self.spec_path)
        self.adapter_override = adapter_override
        self.use_adapter_default = use_adapter_default
        self.dry_run = dry_run
        self.execution_mode = execution_mode
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
        except ValueError as exc:
            if "No multi-app registry found at" in str(exc):
                registry = None
            else:
                raise HarnessSpecError(str(exc)) from exc

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
            execution_mode=self.execution_mode,
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
        adapters = get_registered_adapters()
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

    def write_lifecycle_artifacts(self) -> None:
        """Write lifecycle-related artifacts (findings, stage iterations, convergence state).
        
        Scaffolding for Phase 2 convergence loop support. Called at end of run execution
        to persist finding state transitions and iteration records for hands-off re-validation.
        """
        if self.run_dir is None or self.run is None:
            return
        
        # Write stage iteration records if present
        if self.run.stage_iterations:
            iterations_path = self.run_dir / "lifecycle" / "stage-iterations.json"
            iterations_path.parent.mkdir(parents=True, exist_ok=True)
            iterations_path.write_text(
                json.dumps(
                    [iter_record.model_dump(mode="json") for iter_record in self.run.stage_iterations],
                    indent=2
                ) + "\n",
                encoding="utf-8",
            )
        
        # Write findings records if present
        if self.run.findings:
            findings_path = self.run_dir / "lifecycle" / "findings.json"
            findings_path.parent.mkdir(parents=True, exist_ok=True)
            findings_path.write_text(
                json.dumps(
                    [finding.model_dump(mode="json") for finding in self.run.findings],
                    indent=2
                ) + "\n",
                encoding="utf-8",
            )
    
    def write_convergence_state(self, pass_number: int, max_passes: int, converged: bool, reason: str | None = None) -> None:
        """Record convergence loop state for hands-off lifecycle re-validation.
        
        Scaffolding for Phase 5 convergence loop implementation. Records whether analyze/critic
        passes are converging toward resolution or hitting max-pass limit.
        
        Args:
            pass_number: Current pass number (1-indexed)
            max_passes: Maximum allowed passes
            converged: Whether convergence criteria met
            reason: Optional explanation if not converged
        """
        if self.run_dir is None:
            return
        
        convergence_path = self.run_dir / "lifecycle" / "convergence-state.json"
        convergence_path.parent.mkdir(parents=True, exist_ok=True)
        
        state = {
            "pass_number": pass_number,
            "max_passes": max_passes,
            "converged": converged,
            "timestamp": utc_now_iso(),
        }
        if reason:
            state["reason"] = reason
        
        convergence_path.write_text(
            json.dumps(state, indent=2) + "\n",
            encoding="utf-8",
        )

    def add_finding(
        self,
        finding_id: str,
        severity: str,
        description: str,
        recommended_action: str,
        execution_mode: str = "manual",
    ) -> None:
        """Add a new finding to the current run.
        
        Part of Phase 2 convergence loop scaffolding. Findings track analyze/critic
        issues that need resolution in subsequent passes.
        
        Args:
            finding_id: Unique identifier for the finding
            severity: "error", "warning", or "info"
            description: Human-readable description
            recommended_action: Suggested remediation action
            execution_mode: "auto" (attempted), "selective" (conditional), "manual" (user-triggered)
        """
        if self.run is None:
            return
        
        if self.run.findings is None:
            self.run.findings = []
        
        from .spec_models import Finding
        finding = Finding(
            finding_id=finding_id,
            severity=severity,
            description=description,
            recommended_action=recommended_action,
            execution_mode=execution_mode,
            status="open",
        )
        self.run.findings.append(finding)

    def resolve_finding(self, finding_id: str) -> bool:
        """Mark a finding as resolved.
        
        Called when re-validation confirms that a previously-identified issue
        has been fixed in the latest stage output.
        
        Returns:
            True if finding was found and transitioned; False otherwise.
        """
        if self.run is None or self.run.findings is None:
            return False
        
        for finding in self.run.findings:
            if finding.finding_id == finding_id and finding.status == "open":
                finding.status = "resolved"
                return True
        return False

    def defer_finding(self, finding_id: str, reason: str | None = None) -> bool:
        """Mark a finding as deferred (post-MVP work).
        
        Called when an issue is identified but cannot be resolved in the current
        run context and should be addressed in a future iteration.
        
        Returns:
            True if finding was found and transitioned; False otherwise.
        """
        if self.run is None or self.run.findings is None:
            return False
        
        for finding in self.run.findings:
            if finding.finding_id == finding_id and finding.status == "open":
                finding.status = "deferred"
                if reason:
                    finding.description = f"{finding.description} (deferred: {reason})"
                return True
        return False

    def get_open_findings(self) -> list:
        """Return all currently-open findings for re-evaluation."""
        if self.run is None or self.run.findings is None:
            return []
        return [f for f in self.run.findings if f.status == "open"]

    def record_stage_failure(self, stage_name: str, reason_code: str, details: str | None = None) -> None:
        """Record a stage-level failure with reason code for audit trail.
        
        Part of Phase 2 explicit failure tracking. Maps stage failures to structured
        reason codes for reporting, gating decisions, and hands-off orchestration.
        
        Args:
            stage_name: Name of the stage (e.g., "analyze", "critic", "implement")
            reason_code: Canonical reason code (e.g., REASON_CODE_CREATE_PR_BLOCKED)
            details: Optional additional context
        """
        if self.telemetry is None or self.context is None:
            return
        
        # Emit telemetry event for stage failure with reason code
        event_data = {
            "stage": stage_name,
            "reason_code": reason_code,
        }
        if details:
            event_data["details"] = details
        
        self.telemetry.emit("harness.stage.failure", self.context.run_id, **event_data)

    def get_stage_reason_code(self) -> str | None:
        """Return the failure reason code if this run failed at a stage boundary."""
        if self.run is None:
            return None
        return self.run.failure_reason_code

    def _collect_delivery_checks(self) -> list[DeliveryCheckResult]:
        if self.context is None:
            return []
        repo_root = Path(self.context.repo_root)
        changed: set[str] = set()
        try:
            commands = [
                ["git", "diff", "origin/main...HEAD", "--name-only", "--", "src/", "test/"],
                ["git", "diff", "--cached", "--name-only", "--", "src/", "test/"],
                ["git", "diff", "--name-only", "--", "src/", "test/"],
            ]
            for command in commands:
                completed = subprocess.run(
                    command,
                    cwd=repo_root,
                    text=True,
                    errors="replace",
                    capture_output=True,
                    check=False,
                    timeout=30,
                )
                if completed.returncode == 0:
                    for line in (completed.stdout or "").splitlines():
                        value = line.strip()
                        if value:
                            changed.add(value.replace("\\", "/"))

            status_completed = subprocess.run(
                ["git", "status", "--porcelain", "--", "src/", "test/"],
                cwd=repo_root,
                text=True,
                errors="replace",
                capture_output=True,
                check=False,
                timeout=30,
            )
            if status_completed.returncode == 0:
                for line in (status_completed.stdout or "").splitlines():
                    candidate = line[3:].strip() if len(line) > 3 else ""
                    if candidate:
                        changed.add(candidate.replace("\\", "/"))
        except Exception:
            changed = set()

        checks: list[DeliveryCheckResult] = []
        checks.append(
            DeliveryCheckResult(
                check_id="default-src-test-changed-count",
                check_type="git.changed_count",
                required=True,
                status="pass" if len(changed) >= 1 else "fail",
                details={"base_ref": "origin/main", "count": len(changed)},
            )
        )
        checks.append(
            DeliveryCheckResult(
                check_id="default-src-test-path-match",
                check_type="git.changed_path_match",
                required=True,
                status="pass" if any(path.startswith("src/") or path.startswith("test/") for path in changed) else "fail",
                details={"base_ref": "origin/main", "matched_paths": sorted(changed)[:20]},
            )
        )
        return checks

    def _write_no_change_explainer(self, checks: list[DeliveryCheckResult]) -> None:
        if self.run_dir is None:
            return
        failed = [check for check in checks if check.required and check.status == "fail"]
        if not failed:
            return
        lines = [
            "# Delivery Status Unmet",
            "",
            "Workflow execution completed but delivery evidence requirements were not met.",
            "",
            "## Failed Checks",
        ]
        for check in failed:
            lines.append(f"- {check.check_id}: {check.details}")
        lines.append("")
        lines.append("## Next Actions")
        lines.append("- Ensure at least one file changes under src/ or test/.")
        lines.append("- Re-run harness after implementation changes are present.")
        (self.run_dir / "no-change-explainer.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

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

        run.workflow_status = "complete" if run.status == "complete" else "failed"
        run.delivery_checks = self._collect_delivery_checks()
        required_failed = [check for check in run.delivery_checks if check.required and check.status == "fail"]
        run.delivery_status = "met" if not required_failed else "unmet"
        run.create_pr_ready = run.workflow_status == "complete" and run.delivery_status == "met"
        if run.delivery_status == "unmet":
            run.failure_reason_code = REASON_CODE_DELIVERY_UNMET
            self._write_no_change_explainer(run.delivery_checks)
        elif not run.create_pr_ready:
            run.failure_reason_code = REASON_CODE_CREATE_PR_BLOCKED

        run.finished_at = utc_now_iso()
        run.metrics.duration_ms = int((time.perf_counter() - started) * 1000)
        assert self.telemetry is not None
        for check in run.delivery_checks:
            self.telemetry.emit(
                "harness.delivery.check",
                run.run_id,
                check_id=check.check_id,
                check_type=check.check_type,
                required=check.required,
                status=check.status,
                details=check.details,
            )
        self.telemetry.emit(
            "harness.run.finished",
            run.run_id,
            status=run.status,
            workflow_status=run.workflow_status,
            delivery_status=run.delivery_status,
            create_pr_ready=run.create_pr_ready,
            duration_ms=run.metrics.duration_ms,
            steps_total=run.metrics.steps_total,
            validation_failures=run.metrics.validation_failures,
        )
        self.write_result()
        self.write_lifecycle_artifacts()
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

        before_snapshot = _snapshot_outputs(step.outputs)
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
                        artifacts=self._compute_artifacts(step, before_snapshot),
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
                    artifacts=self._compute_artifacts(step, before_snapshot),
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
                    artifacts=self._compute_artifacts(step, before_snapshot),
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
                    artifacts=self._compute_artifacts(step, before_snapshot),
                )
                return result, self.next_step_index(step, success=False)

        result = StepResult(
            step_id=step.id,
            status="failed",
            attempts=attempts,
            adapter=adapter_name,
            duration_ms=total_duration,
            validation_findings=last_findings,
            artifacts=self._compute_artifacts(step, before_snapshot),
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
        assert self.context is not None
        assert self.telemetry is not None
        findings: list[ValidationFinding] = []

        # Phase 3: deterministic-first ordering — evaluate non-rubric rules before llm.rubric
        deterministic_rules = [r for r in step.validation if r.type != "llm.rubric"]
        rubric_rules = [r for r in step.validation if r.type == "llm.rubric"]

        for rule in deterministic_rules:
            finding = self.validation_engine.evaluate(rule, self.context, step_dir)
            findings.append(finding)
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
            if "timed out" in finding.message.lower():
                self.telemetry.emit(
                    "harness.step.incident",
                    self.context.run_id,
                    step_id=step.id,
                    reason_code=REASON_CODE_STEP_TIMEOUT,
                    rule_id=rule.id,
                    non_fatal=True,
                )
            if "decode replacements applied" in finding.message.lower():
                self.telemetry.emit(
                    "harness.step.incident",
                    self.context.run_id,
                    step_id=step.id,
                    reason_code=REASON_CODE_DECODE_REPLACEMENT,
                    rule_id=rule.id,
                    non_fatal=True,
                )

        # Skip rubric rules if any deterministic error-severity rule failed
        has_deterministic_errors = any(
            f.status == "failed" and f.severity == "error" for f in findings
        )

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
                finding = self.validation_engine.evaluate(rule, self.context, step_dir)
            findings.append(finding)
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
            if "timed out" in finding.message.lower():
                self.telemetry.emit(
                    "harness.step.incident",
                    self.context.run_id,
                    step_id=step.id,
                    reason_code=REASON_CODE_STEP_TIMEOUT,
                    rule_id=rule.id,
                    non_fatal=True,
                )
            if "decode replacements applied" in finding.message.lower():
                self.telemetry.emit(
                    "harness.step.incident",
                    self.context.run_id,
                    step_id=step.id,
                    reason_code=REASON_CODE_DECODE_REPLACEMENT,
                    rule_id=rule.id,
                    non_fatal=True,
                )

        return findings

    def _compute_artifacts(self, step: StepSpec, before_snapshot: dict) -> ArtifactDelta:
        """Compute artifact delta from declared outputs and emit telemetry."""
        delta = _diff_snapshots(before_snapshot, _snapshot_outputs(step.outputs))
        if self.telemetry is not None and self.context is not None:
            self.telemetry.emit(
                "harness.step.artifacts",
                self.context.run_id,
                step_id=step.id,
                created=delta.created,
                modified=delta.modified,
                deleted=delta.deleted,
            )
        return delta

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

    @classmethod
    def replay(cls, run_dir: Path) -> dict:
        """Re-evaluate validation rules for a completed run against the current filesystem state.

        Reads spec.resolved.yaml and context.json from run_dir, re-evaluates all validation
        rules, and writes replay_result.json alongside the original result.json.
        Returns the replay result dict.
        """
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

            # Deterministic-first, same ordering as live runs
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


def run_status_to_exit_code(status: str) -> int:
    if status == "complete":
        return 0
    if status == "aborted":
        return 2
    return 1