# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Explain reports and classifies discoveries; it never turns them into work on its own."""

from __future__ import annotations

from pathlib import Path

PROMPT = Path(__file__).resolve().parent.parent / "templates" / "commands" / "explain.md"


def _flat() -> str:
    return " ".join(PROMPT.read_text(encoding="utf-8").replace("**", "").replace("`", "").split())


def test_explain_does_not_require_a_knowledge_update_for_every_gap() -> None:
    text = _flat()
    assert "MUST result in a proposed update" not in text
    assert "absence of a Knowledge node is only an observation" in text


def test_explain_never_bundles_a_fix_with_a_trace_save() -> None:
    text = _flat()
    assert "Apply fix and save trace" not in text
    assert "Default recommendation is yes" not in text
    assert "never combine two actions, or an action and a trace save, into one yes/no" in text


def test_explain_forbids_self_promotion_of_findings() -> None:
    assert (
        "A finding discovered by Explain is reported and classified, but is not added to the "
        "current work unless the developer explicitly promotes it."
    ) in _flat()


def test_confirmed_code_defect_starts_work_rather_than_a_legacy_route() -> None:
    frontmatter = PROMPT.read_text(encoding="utf-8").split("---", 2)[1]
    assert "agent: devspark-quickfix" not in frontmatter
    assert "label: Start Work on a Gap or Defect\n    agent: devspark-specify" in frontmatter
    text = _flat()
    assert (
        "Explain reports confirmed code defects and offers the Start Work handoff "
        "(/devspark-specify). It does not modify application code itself."
    ) in text
    assert "Explain edits code only if" not in text
