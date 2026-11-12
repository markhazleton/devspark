# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Static contract checks for acceptance planning and the durable Tests pillar."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT = "qa-acceptance.md"


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _flat(rel_path: str) -> str:
    return " ".join(_read(rel_path).split())


# -- Unchanged surface -------------------------------------------------------


def test_no_qa_command_prompt_agent_or_template_exists() -> None:
    roots = [
        "templates/commands",
        "templates/prompts",
        ".github/agents",
        ".github/prompts",
        "templates",
    ]
    for root in roots:
        base = REPO_ROOT / root
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.is_file():
                lowered = path.name.lower()
                assert "qa-" not in lowered, path
                assert not lowered.startswith("qa"), path
                assert "acceptance" not in lowered, path


def test_unrelated_sources_do_not_mention_the_artifact() -> None:
    for rel in (
        "templates/judge-contract.md",
        "templates/closeout-contract.md",
        "templates/commands/closeout.md",
        "templates/commands/specify.md",
        "templates/commands/create-pr.md",
        "templates/commands/quickfix.md",
        "templates/quick-spec-template.md",
    ):
        assert ARTIFACT not in _read(rel), rel


# -- Acceptance planning (Plan, Analyze, Critic) -----------------------------


def test_plan_creates_artifact_conditionally_with_compact_contract() -> None:
    plan = _flat("templates/commands/plan.md")
    assert ARTIFACT in plan
    assert "Never create it empty" in plan
    assert "At most one per spec" in plan
    assert "ID | Trace | Surface | Scenario | Runner | Regression" in plan
    assert "free text" in plan
    assert "never a DevSpark enumeration" in plan
    assert "`automated`, `manual` or `hybrid`" in plan
    assert "naming no tool or vendor" in plan
    assert "No execution-tracking fields" in plan
    for disposition in ("`add`", "`update <ref>`", "`retire <ref>`", "`none (<reason>)`"):
        assert disposition in plan
    assert "`retire` plus `add`" in plan
    assert "a scenario never creates a requirement" in plan
    assert "regression is curation, not accumulation" in plan


def test_plan_template_lists_artifact_as_conditional() -> None:
    template = _read("templates/plan-template.md")
    assert ARTIFACT in template
    line = next(x for x in template.splitlines() if ARTIFACT in x)
    assert line.split("#", 1)[1].strip().startswith("Only if")


def test_analyze_and_critic_carry_lane_checks() -> None:
    analyze = _flat("templates/commands/analyze.md")
    critic = _flat("templates/commands/critic.md")
    assert "untraced scenario" in analyze
    assert "outside the approved scope" in analyze
    assert "externally important success criterion" in analyze
    assert "internals rather than observable behavior" in critic
    assert "append-only regression disposition" in critic
    assert "would not actually prove the requirement" in critic


def test_assurance_contract_keeps_checks_in_existing_lanes() -> None:
    contract = _flat("templates/assurance-contract.md")
    assert contract.count(ARTIFACT) >= 2
    assert "scenario trace validity" in contract
    assert "internals-based scenarios" in contract
    assert "Planning-review adjudication is unchanged" in contract


# -- Tests pillar (Tasks, Implement, Knowledge) ------------------------------


def test_tests_are_no_longer_optional() -> None:
    for rel in ("templates/commands/tasks.md", "templates/tasks-template.md"):
        text = _read(rel)
        assert "Tests are OPTIONAL" not in text, rel
        assert "OPTIONAL - only if tests requested" not in text, rel
        assert "Tests impact" in text, rel
        assert "never assume every change adds tests" in text, rel
    assert ARTIFACT in _read("templates/commands/tasks.md")


def test_no_guidance_requires_every_change_to_add_tests() -> None:
    for rel in ("templates/commands/tasks.md", "templates/tasks-template.md"):
        assert "every change adds tests" not in _read(rel).replace(
            "never assume every change adds tests", ""
        ), rel


def test_implement_applies_planned_tests_delta() -> None:
    implement = _flat("templates/commands/implement.md")
    assert ARTIFACT in implement
    assert "planned durable Tests delta" in implement
    assert "durable manual-regression reference" in implement
    assert "carry no spec, task or scenario identifiers" in implement


def test_knowledge_states_the_tests_pillar() -> None:
    contract = _flat(".knowledge/governance/knowledge-framework-contract.md")
    assert "Tests are a durable pillar" in contract
    assert "Knowledge is the claim, Tests are the evidence, Code is the subject" in contract
    assert "Regression is not Knowledge" in contract
    assert "conceptual ownership, not a directory taxonomy" in contract


# -- Spec closes at PR -------------------------------------------------------


def test_tasks_guidance_forbids_post_merge_qa_work() -> None:
    for rel in ("templates/commands/tasks.md", "templates/tasks-template.md"):
        text = _flat(rel)
        assert "waits for deployment" in text, rel
        assert "post-deployment sign-off" in text, rel
        assert "later sprint" in text, rel
        assert "defects not yet" in text, rel
    tasks = _flat("templates/commands/tasks.md")
    assert "automated acceptance coverage" in tasks
    assert "source-controlled QA material" in tasks


def test_ownership_split_is_stated_once_in_knowledge() -> None:
    mapping = _flat(".knowledge/governance/devspark-prompt-mapping.md")
    assert "the spec owns defining and preparing acceptance" in mapping
    assert "QA operations own post-deployment execution" in mapping
    assert "not required to complete, close out or make the spec archive-ready" in mapping
    assert "creates new work and does not reopen the spec" in mapping
    assert mapping.count("QA operations own post-deployment execution") == 1


def test_closeout_and_verification_regression_gates_are_unchanged() -> None:
    closeout = _read("templates/commands/closeout.md")
    contract = _read("templates/closeout-contract.md")
    verification = _read("templates/verification-contract.md")
    assert "name the regression gate that keeps each claimed outcome true" in closeout
    assert "required regression gates satisfied or explicitly governed" in contract
    assert "regression-pinned" in verification


# -- PR review ---------------------------------------------------------------


def test_pr_review_judges_the_tests_delta_from_the_durable_diff_not_the_plan() -> None:
    review = _flat("templates/commands/pr-review.md")
    assert ARTIFACT not in review
    assert "Planned Tests delta" not in review
    assert "Unjustified test removal" in review
    assert "`PRD3` — Insufficient test depth" in review
