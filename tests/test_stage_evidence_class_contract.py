# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for the `stage` and `evidence_class` vocabulary in verification and closeout.

Text assertions over the contract templates and the commands that consume them. The vocabulary
adds no gate, state or script: the existing readers keep their behavior.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
COMMANDS = TEMPLATES / "commands"

STAGES = ("pre-merge", "post-deploy")
EVIDENCE_CLASSES = ("automated", "local-integration", "deployed", "rollout")
CONTRACTS = ("verification-contract.md", "closeout-contract.md")
CONSUMERS = ("verify", "closeout", "implement", "create-pr", "specify", "plan", "tasks", "critic")


def _read(path: Path) -> str:
    assert path.is_file(), f"{path.name} is missing"
    return path.read_text(encoding="utf-8")


def _contract(name: str) -> str:
    return _read(TEMPLATES / name)


def _command(name: str) -> str:
    return _read(COMMANDS / f"{name}.md")


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


@pytest.mark.parametrize("name", CONTRACTS)
def test_contracts_define_both_stages_and_all_evidence_classes(name: str) -> None:
    text = _contract(name)
    assert "stage" in text and "evidence_class" in text
    for value in STAGES + EVIDENCE_CLASSES:
        assert f"`{value}`" in text, value
    assert re.search(r"pre-merge[^.\n]*default|default[^.\n]*pre-merge", text, re.IGNORECASE)


def test_post_deploy_requires_deployed_or_rollout_evidence() -> None:
    text = _flat(_contract("verification-contract.md"))
    assert re.search(r"post-deploy[^.]*(deployed[^.]*rollout|rollout[^.]*deployed)", text)
    assert re.search(r"cannot be (provided|satisfied|proven)[^.]*pre-merge", text, re.IGNORECASE)


def test_closeout_records_a_post_deploy_requirement_as_a_deferral_with_a_real_record() -> None:
    text = _flat(_contract("closeout-contract.md"))
    assert "outcome: deferred" in text and "captured_as" in text and "accepted_by" in text
    assert re.search(r"real[^.]*(persistent|durable)[^.]*record|persistent[^.]*record", text, re.IGNORECASE)
    assert re.search(r"(hypothetical|missing|in-session)[^.]*(unclassified|not-complete)", text, re.IGNORECASE)
    assert re.search(r"owner[^.]*deployed[^.]*evidence[^.]*open|owner[^.]*open", text, re.IGNORECASE)


def test_a_failed_mandatory_pre_merge_requirement_is_never_deferred() -> None:
    text = _flat(_contract("closeout-contract.md"))
    assert re.search(r"mandatory[^.]*pre-merge[^.]*never[^.]*deferred", text, re.IGNORECASE)


def test_a_pre_merge_mode_that_needs_deployment_is_a_spec_authoring_defect() -> None:
    for name in ("specify", "verify"):
        text = _flat(_command(name))
        assert re.search(r"authoring defect", text, re.IGNORECASE), name
        assert re.search(r"(back|return)[^.]*spec", text, re.IGNORECASE), name


def test_deferred_post_deploy_items_do_not_block_merge_and_the_pr_says_so() -> None:
    text = _flat(_command("create-pr"))
    assert "ready to deploy, not deployed" in text
    assert re.search(r"deferred[^.]*(list|carr)", text, re.IGNORECASE)
    assert re.search(r"not block|does not block|do not block", _flat(_contract("closeout-contract.md")), re.IGNORECASE)


def test_the_post_merge_capture_rule_covers_every_tasks_derivation() -> None:
    for text in (_flat(_command("tasks")), _flat(_read(TEMPLATES / "tasks-template.md"))):
        assert re.search(r"post-merge capture", text, re.IGNORECASE)
        assert re.search(r"every\s+(tasks\s+)?derivation|all\s+(tasks\s+)?derivations", text, re.IGNORECASE)


@pytest.mark.parametrize("name", CONSUMERS)
def test_every_consuming_command_names_the_vocabulary(name: str) -> None:
    text = _command(name)
    assert re.search(r"post-deploy\b|evidence_class|`stage`", text), name


def test_the_deployment_rollback_critic_concern_remains_critical() -> None:
    text = _command("critic")
    assert re.search(r"\|\s*`deployment_rollback`[^\n]*\|\s*CRITICAL\s*\|", text)


def test_no_new_gate_artifact_or_script_is_introduced_for_the_vocabulary() -> None:
    forbidden = re.compile(r"stage[-_]?gate|evidence[-_]?class[-_]?(gate|script)", re.IGNORECASE)
    for path in list(TEMPLATES.glob("*-contract.md")) + [COMMANDS / f"{n}.md" for n in CONSUMERS]:
        assert not forbidden.search(path.read_text(encoding="utf-8")), path.name
    assert not list((ROOT / "scripts").rglob("*stage*evidence*"))
    assert not list((ROOT / "scripts").rglob("*evidence*class*"))
