from __future__ import annotations

from devspark_cli.harness.spec_models import Finding, StageIterationRecord


def test_finding_statuses_support_open_resolved_deferred() -> None:
    finding = Finding(
        finding_id="critic-001",
        severity="high",
        description="Example issue",
        recommended_action="Fix issue",
        status="open",
    )
    assert finding.status == "open"

    finding.status = "resolved"
    assert finding.status == "resolved"

    finding.status = "deferred"
    assert finding.status == "deferred"


def test_stage_iteration_record_supports_convergence_states() -> None:
    record = StageIterationRecord(
        stage="critic",
        pass_index=1,
        finding_deltas={"open": 2, "resolved": 1},
        actions_attempted=["re-run validation"],
        revalidation_status="continue",
    )
    assert record.revalidation_status == "continue"

    record.revalidation_status = "converged"
    assert record.revalidation_status == "converged"

    record.revalidation_status = "max-pass-failed"
    assert record.revalidation_status == "max-pass-failed"
