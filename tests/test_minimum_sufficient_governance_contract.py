# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Regressions for proportional scope authority and bounded correction continuation."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _read(path: str) -> str:
    return " ".join((ROOT / path).read_text(encoding="utf-8").split())


def test_existing_authority_does_not_require_a_second_approval() -> None:
    convergence = _read("templates/preamble/convergence.md")
    implement = _read("templates/commands/implement.md")

    assert "**Already authorized**" in convergence
    assert "do not ask for approval that the existing decision already grants" in convergence
    assert "After explicit authorization for a bounded correction" in implement


def test_human_authorized_bounded_correction_continues_in_the_existing_feature() -> None:
    convergence = _read("templates/preamble/convergence.md")
    preamble = _read("templates/command-preamble-contract.md")
    implement = _read("templates/commands/implement.md")
    judge = _read("templates/judge-contract.md")
    closeout = _read("templates/closeout-contract.md")

    assert "applies to governance as well as implementation" in preamble
    assert "follow convergence §10" in preamble
    for text in (convergence, implement, judge):
        assert "new spec" in text
        assert "branch" in text
    assert "existing feature artifacts" in convergence
    assert "current objective" in implement
    assert "record who authorized it" in implement
    assert "update only the affected change-surface and task/linkage entries" in implement
    assert "fresh Planning Review solely because the file surface grew" in convergence
    assert "does not prevent a human from" in closeout


def test_unauthorized_adjacent_discovery_is_deferred_not_implemented() -> None:
    convergence = _read("templates/preamble/convergence.md")
    implement = _read("templates/commands/implement.md")

    assert "Adjacent discovery" in convergence
    assert "Do not implement it without" in convergence
    assert "defer it and do not implement it without explicit human authorization" in implement


def test_material_changes_still_stop_for_existing_authoring_or_review_decisions() -> None:
    convergence = _read("templates/preamble/convergence.md")
    implement = _read("templates/commands/implement.md")
    judge = _read("templates/judge-contract.md")

    for text in (convergence, implement, judge):
        assert "objective" in text
        assert "security" in text
        assert "safety" in text or "invariant" in text
    assert "remains a STOP" in implement
    assert "existing authoring or review decision" in convergence


def test_human_authorization_never_bypasses_a_failing_gate() -> None:
    convergence = _read("templates/preamble/convergence.md")
    implement = _read("templates/commands/implement.md")
    verify = _read("templates/commands/verify.md")
    closeout = _read("templates/closeout-contract.md")

    assert "does not satisfy a failed requirement" in convergence
    assert "does not turn a failed requirement or verification into a pass" in implement
    assert "does not reclassify a failed requirement" in closeout
    assert "never a fabricated pass" in verify
    assert "status: fail" in verify


def test_bounded_correction_uses_targeted_reconciliation_and_actual_freshness_rules() -> None:
    convergence = _read("templates/preamble/convergence.md")
    implement = _read("templates/commands/implement.md")
    judge = _read("templates/judge-contract.md")

    assert "without regenerating unaffected planning artifacts" in convergence
    assert "perform only the required focused recheck or rerun" in implement
    assert "use the existing freshness result" in judge
    assert "changed implementation file list" in convergence
    assert "freshness evidence" in convergence
