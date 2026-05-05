"""Harness runtime execution and validation."""

from __future__ import annotations

import time
from pathlib import Path

from .adapters import probe_adapter
from .config import load_adapter_default, load_run_retention_limit
from .spec_loader import discover_repo_root, load_harness_spec
from .spec_models import (
    AdapterCapabilityProfile, ExecutionMode, HarnessSpec,
    Run, RunContext, StepResult, StepSpec, ValidationFinding,
)
from .telemetry import TelemetrySink
from .validation import ValidationEngine
from . import _convergence as _conv
from . import _delivery_gate as _dg
from . import _probe_dispatch as _pd
from . import _result_fmt as _rf


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
        hands_off: bool = False,
    ) -> None:
        self.spec_path = Path(spec_file).resolve()
        self.repo_root = Path(repo_root).resolve() if repo_root is not None else discover_repo_root(self.spec_path)
        self.adapter_override = adapter_override
        self.use_adapter_default = use_adapter_default
        self.dry_run = dry_run
        self.execution_mode = execution_mode
        self.hands_off = hands_off
        self.spec: HarnessSpec | None = None
        self.context: RunContext | None = None
        self.run: Run | None = None
        self.run_dir: Path | None = None
        self.telemetry: TelemetrySink | None = None
        self._step_lookup: dict[str, int] = {}
        self.validation_engine = ValidationEngine()

    def load_spec(self) -> HarnessSpec:
        self.spec = load_harness_spec(self.spec_path, self.repo_root)
        self._step_lookup = {step.id: idx for idx, step in enumerate(self.spec.steps)}
        return self.spec

    def resolve_context(self) -> RunContext:
        self.context = _rf.resolve_context(
            self.spec or self.load_spec(), self.repo_root, self.spec_path,
            self.adapter_override, self.use_adapter_default,
            self.dry_run, self.execution_mode, self.hands_off,
        )
        return self.context

    def resolve_run_adapter(self, spec: HarnessSpec | None = None) -> str:
        spec = spec or self.spec or self.load_spec()
        stored = load_adapter_default() if self.use_adapter_default or self.adapter_override is None else None
        return self.adapter_override or stored or spec.defaults.adapter or "noop"

    def get_adapter_capability_profile(self, adapter_name: str) -> AdapterCapabilityProfile:
        return probe_adapter(adapter_name)

    def prepare_run(self) -> tuple[Run, Path]:
        spec = self.spec or self.load_spec()
        context = self.context or self.resolve_context()
        self.run, self.run_dir, self.telemetry = _rf.prepare_run(spec, context)
        return self.run, self.run_dir

    def run_stage_revalidation_loop(self, max_passes: int = 3) -> tuple[bool, int]:
        return _conv.run_stage_revalidation_loop(
            self.run, self.telemetry, self.context, self.run_dir, self.get_open_findings, max_passes
        )

    def write_convergence_state(self, pass_number: int, max_passes: int, converged: bool, reason: str | None = None) -> None:
        _conv.write_convergence_state(self.run_dir, pass_number, max_passes, converged, reason)

    def add_finding(self, finding_id: str, severity: str, description: str, recommended_action: str, execution_mode: str = "manual") -> None:
        _conv.add_finding(self.run, finding_id, severity, description, recommended_action, execution_mode)

    def resolve_finding(self, finding_id: str) -> bool:
        return _conv.resolve_finding(self.run, finding_id)

    def defer_finding(self, finding_id: str, reason: str | None = None) -> bool:
        return _conv.defer_finding(self.run, finding_id, reason)

    def get_open_findings(self) -> list:
        return _conv.get_open_findings(self.run)

    def record_stage_failure(self, stage_name: str, reason_code: str, details: str | None = None) -> None:
        _conv.record_stage_failure(self.telemetry, self.context, stage_name, reason_code, details)

    def get_stage_reason_code(self) -> str | None:
        return self.run.failure_reason_code if self.run else None

    def execute_step(self, step: StepSpec) -> tuple[StepResult, int | None]:
        assert self.spec and self.context and self.run_dir and self.telemetry
        return _pd.execute_step(
            step, self.spec, self.context, self.run_dir, self.telemetry,
            self._step_lookup, self.validation_engine, self.dry_run, self.hands_off,
            self.adapter_override, self.use_adapter_default,
        )

    def evaluate_step_validations(self, step: StepSpec, step_dir: Path) -> list[ValidationFinding]:
        assert self.context and self.telemetry
        return _pd.evaluate_step_validations(step, step_dir, self.context, self.telemetry, self.validation_engine)

    def next_step_index(self, step: StepSpec, success: bool) -> int | None:
        return _pd.next_step_index(step, self._step_lookup, success)

    def execute(self) -> Run:
        spec = self.spec or self.load_spec()
        run, _ = self.prepare_run()
        started = time.perf_counter()
        _pd.run_step_loop(run, spec, self.execute_step)
        run.workflow_status = "complete" if run.status == "complete" else "failed"
        _dg.evaluate_delivery_gate(run, self.run_dir, Path(self.context.repo_root))
        if self.hands_off:
            converged, _ = self.run_stage_revalidation_loop(max_passes=3)
            if not converged:
                run.failure_reason_code = "convergence_max_pass_failed"
                _conv.write_max_pass_failure_report(self.run_dir, len(self.get_open_findings()))
        assert self.telemetry is not None
        _rf.finalize_run_artifacts(run, spec, self.run_dir, self.telemetry, started, load_run_retention_limit())
        return run

    def prune_old_runs(self, run_dir_root: Path, keep: int = 20) -> None:
        _rf.prune_old_runs(run_dir_root, keep)

    @classmethod
    def replay(cls, run_dir: Path) -> dict:
        return _rf.replay(run_dir)


def run_status_to_exit_code(status: str) -> int:
    if status == "complete":
        return 0
    if status == "aborted":
        return 2
    return 1
