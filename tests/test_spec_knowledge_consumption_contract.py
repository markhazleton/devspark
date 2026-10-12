"""Contract tests for spec knowledge consumption.

Pins the ten-element consumption map in the spec validation contract, the per-command declarations in
the Clarify, Plan and Analyze prompts, and the wording that carries the semantic behavior. Seeded drift
fixtures prove the declaration checker fails closed and names the command and element.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "spec-knowledge-consumption"
CONTRACT = ROOT / "templates" / "spec-validation-contract.md"
COMMANDS = ROOT / "templates" / "commands"

DECLARING = ("clarify", "plan", "analyze")


def _yaml_block(text: str, key: str) -> dict:
    for match in re.finditer(r"```yaml\n(.*?)```", text, re.DOTALL):
        if match.group(1).lstrip().startswith(f"{key}:"):
            return yaml.safe_load(match.group(1))[key]
    raise AssertionError(f"no yaml block starting with {key}:")


def _purposes(value) -> set[str]:
    return set(value) if isinstance(value, list) else {value}


def _map() -> dict:
    return _yaml_block(CONTRACT.read_text(encoding="utf-8"), "spec_knowledge_map")


def check_declaration(kmap: dict, decl: dict) -> list[str]:
    """Return one violation string per problem, each naming the command and element."""
    command = decl.get("command", "<unknown>")
    problems: list[str] = []
    entry = kmap["commands"].get(command)
    if entry is None or not entry.get("declared"):
        problems.append(f"{command}: declaration present but command is not declared in the map")
        return problems
    elements = kmap["elements"]
    vocabulary = set(kmap["purposes"])
    reads = decl.get("reads", {})
    for element in elements:
        if element not in reads:
            problems.append(f"{command}: element {element} dropped from reads")
    for element, purpose in reads.items():
        if element not in elements:
            problems.append(f"{command}: element {element} is not in the map")
            continue
        if not _purposes(purpose) <= vocabulary:
            problems.append(f"{command}: element {element} uses a purpose outside the vocabulary")
        elif _purposes(purpose) != _purposes(elements[element]):
            problems.append(f"{command}: element {element} purpose differs from the map")
    for element in decl.get("writes", []):
        if element not in entry["writes"]:
            problems.append(f"{command}: element {element} is not writable per the map")
    return problems


def _shipped(command: str) -> dict:
    text = (COMMANDS / f"{command}.md").read_text(encoding="utf-8")
    return _yaml_block(text, "spec_knowledge_consumption")


def _fixture(name: str) -> dict:
    return _yaml_block((FIXTURES / "drift" / f"{name}.md").read_text(encoding="utf-8"), "spec_knowledge_consumption")


# ---------------------------------------------------------------- map and declarations


def test_map_has_ten_elements_with_semantic_purposes() -> None:
    kmap = _map()
    assert len(kmap["elements"]) == 10
    assert set(kmap["purposes"]) == {"PROJECT", "CONSTRAIN", "CONTEXT", "NOT_CONSUMED"}
    for element, purpose in kmap["elements"].items():
        assert _purposes(purpose) <= set(kmap["purposes"]), element


@pytest.mark.parametrize("command", DECLARING)
def test_shipped_declaration_matches_map(command: str) -> None:
    assert check_declaration(_map(), _shipped(command)) == []


def test_declared_commands_each_have_a_declaration_and_nothing_else_does() -> None:
    kmap = _map()
    declared = {c for c, e in kmap["commands"].items() if e["declared"]}
    assert declared == set(DECLARING)
    for path in COMMANDS.glob("*.md"):
        has_block = "spec_knowledge_consumption:" in path.read_text(encoding="utf-8")
        assert has_block == (path.stem in declared), path.name
    assert not declared & set(kmap["not_yet_declared"])


def test_plan_and_analyze_write_nothing_and_clarify_writes_spec_only() -> None:
    kmap = _map()
    assert kmap["commands"]["plan"]["writes"] == []
    assert kmap["commands"]["analyze"]["writes"] == []
    assert set(kmap["commands"]["clarify"]["writes"]) == set(kmap["elements"])


# ---------------------------------------------------------------- seeded drift


def test_valid_fixture_passes() -> None:
    assert check_declaration(_map(), _fixture("valid-plan")) == []


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("dropped-element", "plan: element success_criteria dropped"),
        ("disallowed-purpose", "plan: element non_goals purpose differs"),
        ("unwritable-element", "plan: element requirements is not writable"),
        ("undeclared-cell", "plan: element decision_ledger is not in the map"),
        ("command-not-in-map", "tasks: declaration present but command is not declared"),
    ],
)
def test_drift_fixture_fails_naming_command_and_element(name: str, expected: str) -> None:
    problems = check_declaration(_map(), _fixture(name))
    assert any(expected in p for p in problems), problems


def test_purpose_outside_vocabulary_is_reported() -> None:
    decl = _fixture("valid-plan")
    decl["reads"]["context"] = "AUTHORIZE"
    assert any("context uses a purpose outside the vocabulary" in p for p in check_declaration(_map(), decl))


def test_no_new_artifacts_commands_or_gates() -> None:
    forbidden = (
        "business-goals", "architecture-intent", "domain-model", "decision-ledger",
        "accepted-limitations", "manual-operations",
    )
    for path in (ROOT / "templates").rglob("*.md"):
        if path.parent.name in {"knowledge", "gates"} or "spec-knowledge" in path.name:
            continue
        assert not any(path.stem == name for name in forbidden), path
    assert not (COMMANDS / "spec-knowledge.md").exists()
    assert not (ROOT / "templates" / "prompts" / "atomic" / "spec-knowledge.md").exists()


# ---------------------------------------------------------------- prompt wording


def _text(command: str) -> str:
    return (COMMANDS / f"{command}.md").read_text(encoding="utf-8")


def test_plan_wording_pins() -> None:
    text = _text("plan")
    for phrase in (
        "Smallest sufficient projection",
        "Only `PROJECT` authorizes work",
        "Optimization is free only inside declared behavior",
        "reconsider the mechanism",
        "Revise authority depends on whether Judge has run",
        "bounded consistency correction",
        "fall back to the spec",
    ):
        assert phrase in text, phrase


def test_analyze_wording_pins() -> None:
    text = _text("analyze")
    section = text.split("## Spec Knowledge Consumption")[1].split("## Outline")[0]
    assert "writes: []" in section
    for phrase in ("Semantic fidelity", "Plan versus recorded spec decisions", "Overview references"):
        assert phrase in text, phrase
    for phrase in ("propose no redesign", "yields no finding", "unrelated blocker is not a fidelity finding", "advisory"):
        assert phrase in text, phrase


def test_clarify_and_specify_wording_pins() -> None:
    clarify = _text("clarify")
    assert "Domain invariant:" in clarify and "Architectural constraint:" in clarify
    assert "bounded consistency correction" in clarify
    assert "substantive" in clarify
    specify = _text("specify")
    assert "invariant" in specify.lower() and "none known" in specify


def test_plan_adds_no_auto_repair_or_lifecycle_routing() -> None:
    section = _text("plan").split("## Spec Knowledge Consumption")[1].split("## Outline")[0].lower()
    assert "auto-repair" not in section and "execution_mode" not in section
    assert "adds no automatic repair" in section


# ---------------------------------------------------------------- seeded Analyze and Clarify cases


def _cases() -> list[dict]:
    return yaml.safe_load((FIXTURES / "analyze" / "cases.yaml").read_text(encoding="utf-8"))["cases"]


def test_analyze_cases_are_well_formed_and_paired() -> None:
    cases = {c["id"]: c for c in _cases()}
    assert len(cases) >= 17
    for case in cases.values():
        assert case["expect"] in {"finding", "none", "unrelated-blocker"}
        assert case["spec"].strip() and case["plan"].strip()
        if case["expect"] == "finding":
            control = cases[case["pair"]]
            assert control["expect"] == "none"
            assert case["cites"] in case["spec"]


def test_clarify_case_is_well_formed() -> None:
    case = yaml.safe_load((FIXTURES / "clarify" / "case.yaml").read_text(encoding="utf-8"))
    assert case["expect"]["contradictory_criteria"] == 0
    assert case["expect"]["clarification_bullets"] == 1
    assert "Success Criteria" in case["spec_before"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
