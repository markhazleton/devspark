"""Convergence loop, retry policy, and finding management for the DevSpark harness runtime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from .spec_models import Finding, Run, StageIterationRecord
from .telemetry import TelemetrySink, utc_now_iso


def write_convergence_state(
    run_dir: Path | None,
    pass_number: int,
    max_passes: int,
    converged: bool,
    reason: str | None = None,
) -> None:
    """Record convergence loop state for hands-off lifecycle re-validation."""
    if run_dir is None:
        return
    convergence_path = run_dir / "lifecycle" / "convergence-state.json"
    convergence_path.parent.mkdir(parents=True, exist_ok=True)
    state: dict = {
        "pass_number": pass_number,
        "max_passes": max_passes,
        "converged": converged,
        "timestamp": utc_now_iso(),
    }
    if reason:
        state["reason"] = reason
    convergence_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def write_max_pass_failure_report(run_dir: Path | None, open_findings_count: int) -> None:
    """Write a markdown report when the convergence loop exceeds max passes."""
    if run_dir is None:
        return
    lines = [
        "# Convergence Max-Pass Failure",
        "",
        f"- Passes attempted: {open_findings_count}",
        f"- Remaining open findings: {open_findings_count}",
        "",
        "## Next Actions",
        "- Resolve unresolved findings and rerun analyze/critic.",
        "- Use interactive mode if write approvals are needed.",
    ]
    (run_dir / "max-pass-failure-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def add_finding(
    run: Run | None,
    finding_id: str,
    severity: str,
    description: str,
    recommended_action: str,
    execution_mode: str = "manual",
) -> None:
    """Add a new finding to the current run."""
    if run is None:
        return
    if run.findings is None:
        run.findings = []
    finding = Finding(
        finding_id=finding_id,
        severity=severity,
        description=description,
        recommended_action=recommended_action,
        execution_mode=execution_mode,
        status="open",
    )
    run.findings.append(finding)


def resolve_finding(run: Run | None, finding_id: str) -> bool:
    """Mark a finding as resolved. Returns True if the transition was applied."""
    if run is None or run.findings is None:
        return False
    for finding in run.findings:
        if finding.finding_id == finding_id and finding.status == "open":
            finding.status = "resolved"
            return True
    return False


def defer_finding(run: Run | None, finding_id: str, reason: str | None = None) -> bool:
    """Mark a finding as deferred. Returns True if the transition was applied."""
    if run is None or run.findings is None:
        return False
    for finding in run.findings:
        if finding.finding_id == finding_id and finding.status == "open":
            finding.status = "deferred"
            if reason:
                finding.description = f"{finding.description} (deferred: {reason})"
            return True
    return False


def get_open_findings(run: Run | None) -> list:
    """Return all currently-open findings for re-evaluation."""
    if run is None or run.findings is None:
        return []
    return [f for f in run.findings if f.status == "open"]


def record_stage_failure(
    telemetry: TelemetrySink | None,
    context: object | None,
    stage_name: str,
    reason_code: str,
    details: str | None = None,
) -> None:
    """Emit a stage-level failure telemetry event with reason code."""
    if telemetry is None or context is None:
        return
    event_data: dict = {"stage": stage_name, "reason_code": reason_code}
    if details:
        event_data["details"] = details
    telemetry.emit("harness.stage.failure", context.run_id, **event_data)  # type: ignore[union-attr]


def run_stage_revalidation_loop(
    run: Run | None,
    telemetry: TelemetrySink | None,
    context: object | None,
    run_dir: Path | None,
    get_open_findings_fn: Callable[[], list],
    max_passes: int = 3,
) -> tuple[bool, int]:
    """Run a re-validation-only loop for analyze/critic findings."""
    open_findings = get_open_findings_fn()
    if not open_findings:
        write_convergence_state(run_dir, pass_number=1, max_passes=max_passes, converged=True)
        return True, 1

    for pass_index in range(1, max_passes + 1):
        current_open = get_open_findings_fn()
        if not current_open:
            write_convergence_state(run_dir, pass_number=pass_index, max_passes=max_passes, converged=True)
            return True, pass_index

        for stage_name in ("analyze", "critic"):
            if run is not None:
                run.stage_iterations.append(
                    StageIterationRecord(
                        stage=stage_name,
                        pass_index=pass_index,
                        finding_deltas={"open": len(current_open)},
                        actions_attempted=["revalidate"],
                        revalidation_status="continue",
                    )
                )
            if telemetry is not None and context is not None:
                telemetry.emit(
                    "harness.stage.iteration",
                    context.run_id,  # type: ignore[union-attr]
                    stage=stage_name,
                    pass_index=pass_index,
                    open_findings=len(current_open),
                )

        if pass_index == max_passes:
            write_convergence_state(
                run_dir,
                pass_number=pass_index,
                max_passes=max_passes,
                converged=False,
                reason="max-pass-failed",
            )
            return False, pass_index

    return False, max_passes
