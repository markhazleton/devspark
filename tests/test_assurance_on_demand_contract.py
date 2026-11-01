"""Assurance on demand on universal work branches.

Prompt-wording checks only: these assert what the command prompts instruct an agent to do. The
executable behavior (``judge.py resolve`` on a work branch, ``judge.py lifecycle`` enforcing
required obligations) is covered in ``test_judge_contract.py``, and the declared Analyze/Critic
scripts running on a work branch in both shells in ``test_next_context_resolution_contract.py``.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
COMMANDS = ROOT / "templates" / "commands"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontmatter(name: str) -> dict:
    return yaml.safe_load(_read(COMMANDS / name).split("---", 2)[1])


def _on_demand_section() -> str:
    text = _read(ROOT / "templates" / "assurance-contract.md")
    return text.split("## 13. Assurance on Demand (work branches)", 1)[1]


def test_the_contract_defines_one_concern_one_capability_and_a_compact_result():
    section = _on_demand_section()

    for field in ("Concern:", "Capability:", "Evidence:", "Outcome:", "Disposition:"):
        assert field in section
    assert "No concern, no run." in section
    assert "Running one capability never runs another" in section
    assert "Write no `gates/*.md` file and no `tasks.md`" in section
    assert "No specification, task list, frontmatter, or semantic fingerprint is required." in section


def test_persisted_decisions_and_obligations_are_optional_and_bounded():
    section = _on_demand_section()

    assert "Persistence only for continuity" in section
    assert "`## Material Decisions`" in section and "Basis:" in section
    assert "Unrelated files, bookkeeping and checkbox edits never reopen it." in section
    assert "`## Required Obligations`" in section and "Authority:" in section
    assert "never an applicable mandatory obligation" in section
    assert "not mechanically enforced" in section


@pytest.mark.parametrize("name,skipped", [("analyze.md", "skip §10"), ("critic.md", "skip §11")])
def test_analyze_and_critic_run_on_a_work_branch_without_a_gate_or_a_chain(name, skipped):
    text = _read(COMMANDS / name)

    assert "| work branch (`NNN-work-*`, whatever its directory holds)" in text and "`WORK`" in text
    assert "AND the branch is not a `NNN-work-*` branch" in text
    assert "assurance-contract.md §13" in text
    assert f"Write no gate artifact ({skipped})" in text
    assert "Skip this step on a work branch (`WORK` scope)" in text
    assert "return to `/devspark-implement`" in text
    assert "Never run " in text and "as a follow-on" in text


def test_critic_never_auto_sends_and_can_return_to_implementation():
    handoffs = _frontmatter("critic.md")["handoffs"]

    assert all(h.get("send") is not True for h in handoffs)
    assert handoffs[0]["agent"] == "devspark-implement"


def test_judge_adjudicates_on_demand_without_planning_review_machinery():
    text = _read(COMMANDS / "planning-review.md")

    assert "If it reports `work-branch`, follow **Work Branch Adjudication**" in text
    assert "nothing writes `gates/judge.md`" in text
    assert "genuinely conflict" in text
    assert "Running Analyze or Critic never obliges a Judge run." in text


def test_implementation_invokes_one_capability_and_applies_its_disposition():
    text = _read(COMMANDS / "implement.md")
    work_route = text.split("## Work Route (no planning bundle)", 1)[1].split("## Quickfix Route", 1)[0]

    assert "run only the matching" in work_route and "capability on demand" in work_route
    for disposition in ("`continue`", "`pause affected work`", "`decision needed`"):
        assert disposition in work_route
    assert "Never chain a second activity automatically." in work_route
    assert "every `## Required Obligations` entry checked" in work_route


def test_delivery_never_lets_the_developer_waive_a_mandatory_obligation():
    text = _read(COMMANDS / "create-pr.md")

    assert "an unchecked `## Required Obligations` entry in `work.md`" in text
    assert "The exception is `required-obligation-unresolved`" in text
    assert "not the developer's to waive" in text
