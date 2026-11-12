# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Regressions for proportional scope authority and bounded correction continuation."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _read(path: str) -> str:
    return " ".join((ROOT / path).read_text(encoding="utf-8").split())


def test_operating_limits_are_explicit_preserved_and_not_universal_defaults() -> None:
    preamble = _read("templates/command-preamble-contract.md")
    operating = preamble.split("**Operating assumptions.**", 1)[1].split("**Approval authority.**", 1)[0]
    assert "single-environment, single-user" in operating
    assert "Do not assume these limits when they were not stated" in operating
    assert "Single user does not imply single execution" in operating
    assert "If evidence contradicts an assumption" in operating
    for command in ("specify", "implement", "create-pr"):
        text = _read(f"templates/commands/{command}.md")
        assert "explicit operating assumptions" in text, command
        for boundary in ("target environment", "supported users", "configuration", "decision owner"):
            assert boundary in text, (command, boundary)


def test_approval_requires_actual_authority_not_invented_stakeholders() -> None:
    preamble = _read("templates/command-preamble-contract.md")
    authority = preamble.split("**Approval authority.**", 1)[1].split("## 14.", 1)[0]
    for rule in (
        "Do not invent external approvers",
        "must cite an existing applicable policy, contract or explicit instruction",
        "Repository access alone neither establishes nor removes that authority",
        "A recommendation is not a required sign-off",
        "Existing applicable mandatory controls remain binding",
        "authorization already given is not requested again",
    ):
        assert rule in authority


def test_existing_authority_does_not_require_a_second_approval() -> None:
    convergence = _read("templates/preamble/convergence.md")
    implement = _read("templates/commands/implement.md")

    assert "**Already authorized**" in convergence
    assert "do not ask for approval that the existing decision already grants" in convergence
    assert "After explicit authorization for a bounded correction" in implement


def test_investigation_stops_at_the_question_and_command_completion() -> None:
    convergence = _read("templates/preamble/convergence.md")
    for rule in (
        "Before an additional search, read, probe or test run",
        "what evidence would settle it",
        "Stop tracing when the question is answered",
        "Reading a dependency does not authorize an audit of that dependency",
        "no investigation ledger or extra artifact is required",
        "Do not add a final discovery sweep",
        "coverage limit instead of claiming completion",
    ):
        assert rule in convergence
    implement = _read("templates/commands/implement.md")
    assert "do not add a cleanup pass or search for adjacent improvements" in implement


def test_reopening_requires_invalidating_evidence_and_optional_advice_stays_optional() -> None:
    convergence = _read("templates/preamble/convergence.md")
    for rule in (
        "name its original basis",
        "new evidence or authorized scope change that invalidates it",
        "a changed path without a relevant semantic change is not sufficient",
        "without automatically creating a ticket, plan or approval cycle",
        "must never hide an unresolved blocker",
    ):
        assert rule in convergence
    review = _read("templates/commands/pr-review.md")
    assert "a different reviewer or preference is not new evidence" in review
    assert "smallest necessary correction" in review


def test_remediation_all_does_not_grow_with_adjacent_discoveries() -> None:
    remediation = _read("templates/commands/address-pr-review.md")
    for rule in (
        "Freeze those finding IDs and their required outcomes for this invocation",
        "`all` means the actionable findings selected now",
        "regressions caused by the selected corrections",
        "the file list is not a hard limit",
        "Do not add adjacent refactors or newly discovered unrelated findings to the batch",
        "obtain explicit authorization before adding separate work",
    ):
        assert rule in remediation


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
