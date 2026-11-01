"""Verify, Closeout and Create PR agree on delivery readiness for universal work branches.

Prompt-wording checks only: these assert what the command prompts instruct an agent to do. The
executable behavior (the Create PR preflight ``lifecycle`` field and its refusal of an unresolved
mandatory obligation, in both shells) is covered in ``test_create_pr_knowledge_readiness_contract.py``;
``/devspark-next`` routing on the same check is covered in ``test_next_context_resolution_contract.py``.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
COMMANDS = ROOT / "templates" / "commands"


def _read(name: str) -> str:
    return (COMMANDS / name).read_text(encoding="utf-8")


def _flat(name: str) -> str:
    return " ".join(_read(name).replace("**", "").split())


def _frontmatter(name: str) -> dict:
    return yaml.safe_load(_read(name).split("---", 2)[1])


def _work_branch_verification() -> str:
    text = _read("verify.md").split("## Work Branch Verification (no planning bundle)", 1)[1]
    return " ".join(text.replace("**", "").split())


def test_verify_routes_a_work_branch_to_proportional_proof_without_gate_documents() -> None:
    outline = _flat("verify.md")
    assert "Universal work branch (any `NNN-work-*` branch; a file named `spec.md` in its directory never makes it a legacy bundle): follow *Work Branch Verification*" in outline

    section = _work_branch_verification()
    assert "in proportion to the change's risk" in section
    assert "No declared mode is required." in section
    assert "Write no `gates/verify.md` or `gates/closeout.md`" in section
    assert "do not create `work.md`" in section
    for heading in ("observed", "assumed", "cannot be obtained"):
        assert heading in section
    for question in ("Delivered", "Verified", "Eligible"):
        assert question in section
    assert "judge.py lifecycle" in section


def test_verify_keeps_post_deploy_requirements_visible_but_never_a_pre_merge_failure() -> None:
    section = _work_branch_verification()
    assert "only be proven after deployment is named as deferred" in section
    assert "never fails this check before merge" in section
    assert "never reported as passed" in section
    assert "Keep it visible past this session" in section
    assert "`/devspark-create-pr` carries it into the PR's deployment status" in section

    create_pr = _flat("create-pr.md")
    assert (
        "On a work branch, do the same for each requirement that `work.md` or the verification report "
        "names as provable only after deployment"
    ) in create_pr


def test_verify_on_a_work_branch_never_chains_more_assurance() -> None:
    section = _work_branch_verification()
    assert "Never recommend `/devspark-closeout` here" in section
    assert "Analyze or Critic only for a specific, named concern" in section
    assert "Nothing in it is a mandatory step" in section


def test_closeout_reassesses_a_work_branch_without_a_document() -> None:
    text = _flat("closeout.md")
    assert "no `gates/closeout.md` to write" in text
    assert "delivered, verified, eligible" in text
    assert "never block merge" in text


def test_fixing_a_closeout_defect_routes_back_to_verification_not_closeout() -> None:
    prompts = [h["prompt"] for h in _frontmatter("closeout.md")["handoffs"]]
    assert not any("re-run closeout" in p for p in prompts)
    assert any("re-run verification" in p for p in prompts)


def test_create_pr_reads_the_preflight_lifecycle_and_names_the_head() -> None:
    """Prompt-wording check only: the refusal itself is exercised in test_create_pr_knowledge_readiness_contract."""
    text = _flat("create-pr.md")
    assert "Preflight already runs the lifecycle check and reports it as `lifecycle`" in text
    assert "do not run the check again" in text
    assert "`unavailable` means the check could not run, and is never a pass" in text
    assert "CREATE PR BLOCKED — LIFECYCLE CHECK UNAVAILABLE" in text
    assert "DevSpark has no override for this" in text
    assert "readiness is unconfirmed rather than calling it clean" in text
    assert "`remote.local_head`" in text and "`remote.remote_head`" in text


def test_create_pr_states_its_exit_code_contract() -> None:
    """Prompt-wording check only: the exit codes themselves are exercised in test_create_pr_knowledge_readiness_contract."""
    text = _flat("create-pr.md")
    assert "exit `0` only when they return `status: ok`" in text
    assert "exits `1` in both the PowerShell and Bash scripts" in text
    assert "Read the exit code, not the message text" in text


def test_create_pr_records_an_obligation_decision_in_work_md_not_by_proceeding() -> None:
    text = _flat("create-pr.md")
    assert "CREATE PR BLOCKED — REQUIRED OBLIGATION UNRESOLVED" in text
    assert "Proceeding past the check is never how that decision is recorded." in text
    assert "checking the `## Required Obligations` entry in `work.md` with a reference to it" in text
    assert "record that decision in the PR" not in text


def test_create_pr_treats_verification_and_gate_artifacts_as_optional_on_work_branches() -> None:
    text = _flat("create-pr.md")
    assert "It needs no Verify or Closeout document." in text
    assert "it needs no spec, no declared mode and no gate document, and skipping it is never a failure" in text
    assert "recommend `/devspark-analyze` or `/devspark-critic` before merge" not in text
    assert "only for a specific, named concern in this change" in text


def test_implement_offers_verification_without_requiring_it() -> None:
    handoffs = _frontmatter("implement.md")["handoffs"]
    verify = [h for h in handoffs if h["agent"] == "devspark-verify"]
    assert verify and "optional" in verify[0]["label"].lower()
    assert verify[0].get("send") is not True
