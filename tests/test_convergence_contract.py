# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for the convergence/closeout lifecycle phase.

Guards two failure modes at once:

1. *Non-convergence* -- verification discovers an observation, the observation
   becomes work, the work is verified, which discovers another observation.
   The spec silently expands and never finishes.
2. *Orchestration creep* -- solving (1) by making the developer type another
   mandatory command, trading a lifecycle defect for an adoption defect.

Run with: python tests/test_convergence_contract.py
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

CONTRACT = "templates/closeout-contract.md"
VERIFY = "templates/commands/verify.md"
CLOSEOUT = "templates/commands/closeout.md"
PR_REVIEW = "templates/commands/pr-review.md"
NEXT = "templates/commands/next.md"
PREAMBLE = "templates/command-preamble-contract.md"
CONVERGENCE_MODULE = "templates/preamble/convergence.md"
ORCHESTRATION_MODULE = "templates/preamble/orchestration.md"
VERIFICATION_CONTRACT = "templates/verification-contract.md"
MAPPING = ".knowledge/governance/devspark-prompt-mapping.md"

CLASSIFICATIONS = ("blocking-defect", "accepted-limitation", "deferred-work", "learning")
CRITERION_KINDS = ("requirement", "invariant", "hypothesis", "target")


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


# --- 1/2. Verify owns both phases -------------------------------------------


def test_verify_classifies_findings_itself() -> None:
    """Verify must run the classification phase, not hand it off."""
    verify = _read(VERIFY)

    assert "### Closeout Phase" in verify, "verify.md must contain the closeout phase inline"
    assert "closeout-contract.md" in verify, "verify.md must load the closeout contract"
    for classification in CLASSIFICATIONS:
        assert classification in verify, f"verify.md must name the {classification} classification"
    for kind in CRITERION_KINDS:
        assert f"`{kind}`" in verify, f"verify.md must evaluate criteria of kind {kind}"


def test_verify_produces_a_closeout_decision() -> None:
    verify = _read(VERIFY)

    assert "gates/closeout.md" in verify, "verify.md must write the closeout gate artifact"
    assert "produced_by: verify" in verify, (
        "verify.md must stamp the artifact it produces so a decision made without a fresh "
        "evidence phase stays distinguishable from one made with it"
    )
    assert "decision: complete" in verify and "decision: not-complete" in verify, (
        "verify.md must emit an explicit completion decision"
    )
    assert "not-complete` is a successful run" in verify or "not-complete`" in verify, (
        "verify.md must treat not-complete as a valid answer"
    )


# --- 3/4. Only blocking findings create current-spec work -------------------


def test_non_blocking_finding_does_not_create_mandatory_work() -> None:
    contract = _read(CONTRACT)
    verify = _read(VERIFY)

    assert "discovery alone does not expand the current specification" in contract
    assert "expansion trigger" in contract, "contract must define the expansion triggers"
    assert "Blocking Defect is the only classification that creates mandatory work" in contract

    # The loop guard: a non-blocking finding may not silently re-enter implement.
    assert "MUST NOT trigger implementation followed by another mandatory verification cycle" in contract
    assert "MUST NOT be turned into implementation work followed by another verification cycle" in verify


def test_blocking_defect_does_create_mandatory_work() -> None:
    contract = _read(CONTRACT)
    verify = _read(VERIFY)

    assert "goes back to `/devspark-implement` for the blocking defects only" in contract
    assert "for the blocking defects only" in verify, (
        "verify.md must route a not-complete decision back to implement for blocking defects only"
    )
    assert "`decision: complete` requires" in contract or "unresolved blocking defects = 0" in contract


# --- 5/6. Criterion kinds: learning is a result, not a loophole -------------


def test_disproven_hypothesis_can_close_as_learning() -> None:
    contract = _read(CONTRACT)

    assert "A disproven hypothesis is a valid outcome" in contract
    assert "resolved-through-learning" in contract
    assert "original_expectation" in contract and "revised_understanding" in contract, (
        "a learning finding must retain the original expectation alongside the revised understanding"
    )


def test_failed_requirement_cannot_be_laundered_into_learning() -> None:
    contract = _read(CONTRACT)
    verify = _read(VERIFY)
    closeout = _read(CLOSEOUT)

    assert "anti-laundering rule" in contract.lower(), "contract must forbid re-labeling a failed requirement"
    assert "MUST NOT be reclassified as a `hypothesis` or a `target`" in contract
    assert "undeclared criterion is read as a `requirement`" in contract.replace("**", ""), (
        "an unlabeled criterion must read as the strictest kind"
    )
    for body, label in ((verify, VERIFY), (closeout, CLOSEOUT)):
        assert "Blocking Defect by definition" in body, (
            f"{label} must state that a failed requirement/invariant is a Blocking Defect by definition"
        )


# --- 7. Deferred work converges, and only a human can pull it back in -------


def test_deferred_work_does_not_reopen_the_current_spec() -> None:
    contract = _read(CONTRACT)

    assert "captured_as" in contract, "deferred work must name where it was actually captured"
    assert "Deferral must be real" in contract
    assert "promoted_by" in contract, "promotion into current scope must be recorded"
    assert "Promotion is an explicit act" in contract
    assert "MUST NOT promote on its own authority" in contract, (
        "an agent must not expand scope without explicit developer intent"
    )


# --- 8. Unclassified findings block ------------------------------------------


def test_unclassified_findings_block_closeout() -> None:
    contract = _read(CONTRACT)

    assert "unclassified findings = 0" in contract, "the stop condition must require zero unclassified findings"
    assert "An unclassified finding is itself blocking" in contract
    # ...and the stop condition must NOT demand zero of everything else.
    assert "It does **not** require zero accepted limitations" in contract, (
        "the stop condition must stay reachable: classified findings do not block"
    )


# --- 9. PR review consumes, rather than restarts, the decision ---------------


def test_pr_review_respects_classified_non_blocking_findings() -> None:
    pr_review = _read(PR_REVIEW)

    assert "### 6d. Closeout Consumption" in pr_review
    assert "PRD6" in pr_review, "pr-review needs a stable finding code for an indefensible closeout"
    assert "do not reopen" in pr_review.lower()
    assert "An improvement you noticed is not a reason to reopen the spec" in pr_review
    assert "A genuine defect still reopens the work" in pr_review, (
        "consuming the closeout decision must not disarm the review"
    )
    assert "non-blocking note, not a finding" in pr_review, (
        "a route with no closeout artifact must not be forced to go produce one"
    )


def test_pr_review_closeout_does_not_add_a_reconciliation_command() -> None:
    pr_review = _read(PR_REVIEW)
    address = _read("templates/commands/address-pr-review.md")

    assert "do not require an additional reconciliation command" in pr_review.lower()
    assert "does not start another address/review reconciliation cycle" in address
    assert "/devspark-pr-review UPDATE" in address


# --- 10. One contract, two entry points --------------------------------------


def test_standalone_closeout_shares_the_verify_contract() -> None:
    closeout = _read(CLOSEOUT)
    contract = _read(CONTRACT)

    assert "One Contract, Not Two Implementations" in closeout
    assert "closeout-contract.md" in closeout, "the standalone command must defer to the shared contract"
    assert "produced_by: closeout" in closeout
    assert "produced_by: verify | closeout" in contract, (
        "the artifact must record which entry point produced it"
    )
    # The standalone entry point must be honest about the evidence it reused.
    assert "did not refresh" in closeout


def test_closeout_command_skills_resolve_to_the_template() -> None:
    skill = _read(".github/skills/devspark-closeout/SKILL.md")
    consumer = _read("templates/consumer-skills/devspark-closeout/SKILL.md")

    assert "templates/commands/closeout.md" in skill
    assert "devspark.closeout.md" in consumer


def test_closeout_template_carries_constitution_authority() -> None:
    """prompt-conformance-manifest.md Element 1: constitution.md + non-negotiable within 15 lines."""
    lines = _read(CLOSEOUT).splitlines()
    hits = [i for i, line in enumerate(lines) if "constitution.md" in line]
    assert hits, "closeout.md must reference constitution.md"
    assert any(
        any("non-negotiable" in lines[j].lower() for j in range(max(0, i - 15), min(len(lines), i + 16)))
        for i in hits
    ), "closeout.md must assert constitution.md as non-negotiable within 15 lines of the reference"


# --- 11. The happy path did not get longer -----------------------------------


def test_closeout_is_never_a_routine_next_step() -> None:
    """The convergence change must not add a command to the minimal happy path."""
    verify = _read(VERIFY)
    closeout = _read(CLOSEOUT)
    next_cmd = _read(NEXT)
    preamble = _read(CONVERGENCE_MODULE)

    assert "Never end by telling the user to run `/devspark-closeout`" in verify
    assert "Optional / Advanced — Not a Step on the Normal Path" in closeout
    assert "never needs to type this command" in closeout
    assert "**Never recommend `/devspark-closeout`.**" in next_cmd
    assert "Closeout is a phase, not a command" in preamble

    # Verify's handoffs route forward to the PR, never sideways to closeout.
    frontmatter = verify.split("---")[1]
    assert "devspark-closeout" not in frontmatter, (
        "verify.md must not offer closeout as a handoff -- it already ran that phase"
    )
    assert "devspark-create-pr" in frontmatter


def test_orchestration_principle_has_a_durable_home() -> None:
    # The principle is canonical in the orchestration preamble module (the philosophy page is a
    # vision and manifesto and no longer restates it); compare against unwrapped text.
    preamble = " ".join(_read(ORCHESTRATION_MODULE).replace(">", " ").split())
    mapping = _read(MAPPING)

    assert "Minimize required developer orchestration" in preamble
    assert "does not automatically justify a new mandatory command" in preamble
    assert "automate mechanical transitions; expose consequential decisions" in preamble
    assert "## 11. Orchestration Discipline" in preamble
    assert "## Developer-experience classification" in mapping
    for cls in ("CORE HAPPY-PATH", "OPTIONAL ADVANCED", "INTERNAL CAPABILITY", "DIAGNOSTIC / MAINTENANCE"):
        assert cls in mapping, f"command classification table missing the {cls} class"
    assert "zero** commands" in mapping, "the inventory must record the happy-path command count impact"


# --- Verification stays curious ----------------------------------------------


def test_verification_is_not_incentivised_to_find_less() -> None:
    verify = _read(VERIFY)
    verification_contract = _read(VERIFICATION_CONTRACT)

    assert "Find freely in steps 1–5; classify deliberately in step 6" in verify
    assert "discovered:" in verify and "discovered:" in verification_contract
    assert "never affects any mode's `status`" in verification_contract
    assert "optimizes for finding things" in verification_contract, (
        "the contract must say why the two phases stay distinct"
    )


def test_next_context_scripts_expose_the_decision_in_both_languages() -> None:
    """Constitution VI: bash and PowerShell stay functionally equivalent."""
    bash = _read("scripts/bash/next-context.sh")
    ps = _read("scripts/powershell/next-context.ps1")
    next_cmd = _read(NEXT)

    assert "CLOSEOUT_DECISION" in bash
    assert "CLOSEOUT_DECISION" in ps
    assert "gates/closeout.md" in bash and "gates/closeout.md" in ps
    assert "CLOSEOUT_DECISION" in next_cmd, "next.md must document the field its script emits"


def main() -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("Convergence contract validated.")


if __name__ == "__main__":
    main()
