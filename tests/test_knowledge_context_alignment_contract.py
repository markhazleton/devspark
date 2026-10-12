# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""
Contract tests for task-specific Knowledge context correctness.

Three invariants from the Knowledge Framework Contract are guarded here, because each one
regressed silently before it was tested:

* Retrieval (section 15) ranks entities on *meaning*, never on where they are stored or who owns
  them. Every entity lives under `.knowledge/entities/` and a corpus commonly shares one owner, so
  scoring those fields lets a single generic word ("knowledge") retrieve the entire entity set and
  hand an agent a working set full of unrelated concepts.
* `context_resolved` (section 17) is kind-agnostic. A flat Knowledge document is first-class
  resolved context, so no template, gate, or consuming command may model resolved context as
  entity-or-decision only.
* The hop policy (section 16) is stated once: planning projects at most 2 hops, implementation
  consumes the resolved set and may take at most 1 additional logged hop. A second, more generous
  budget anywhere in the framework is a contract violation, not a wording preference.

These are semantic assertions on purpose. They do not pin prose, so ordinary rewording stays free.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMANDS_DIR = REPO_ROOT / "templates" / "commands"
PLAN_TEMPLATE = REPO_ROOT / "templates" / "plan-template.md"

OWNER = "DevSpark Maintainers"


def _load_explain_context():
    spec = importlib.util.spec_from_file_location(
        "explain_context_alignment", REPO_ROOT / "scripts" / "explain-context.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def explain():
    return _load_explain_context()


def _entity(entity_id: str, **overrides: Any) -> dict[str, Any]:
    entity = {
        "id": entity_id,
        "type": "subsystem",
        "owner": OWNER,
        "path": f".knowledge/entities/{entity_id}",
        "relations": [],
        "layers": ["architecture"],
        "missing_layers": [],
        "coverage_overrides": [],
        "constrained_by": [],
    }
    entity.update(overrides)
    return entity


def _layer(entity_id: str, title: str, aliases: list[str], headings: list[str]) -> dict[str, Any]:
    return {
        "id": f"{entity_id}-architecture",
        "entity": entity_id,
        "layer": "architecture",
        "type": "entity-layer",
        "path": f".knowledge/entities/{entity_id}/architecture.md",
        "title": title,
        "aliases": aliases,
        "headings": headings,
    }


@pytest.fixture(scope="module")
def corpus() -> dict[str, Any]:
    """Two entities that share a storage root and an owner but mean entirely different things."""
    return {
        "entities": [
            _entity("knowledge-engine"),
            _entity(
                "billing-gateway",
                relations=[{"to": "knowledge-engine", "rel": "depends-on"}],
            ),
        ],
        "nodes": [
            _layer(
                "knowledge-engine",
                "Knowledge Engine - Architecture",
                ["index generation", "taxonomy"],
                ["The generated index", "Drift detection"],
            ),
            _layer(
                "billing-gateway",
                "Billing Gateway - Architecture",
                ["invoice dispatch", "payment capture"],
                ["Settlement windows", "Refund handling"],
            ),
        ],
    }


def _match(explain, corpus: dict[str, Any], topic: str) -> list[str]:
    return [e["id"] for e in explain.match_entities(corpus, explain.tokenize(topic), 25)]


# --- Retrieval: storage location and ownership are not meaning ---------------------------------


def test_shared_storage_root_does_not_make_every_entity_relevant(explain, corpus) -> None:
    """A word that appears in every entity's path must not retrieve every entity."""
    assert "entities" in corpus["entities"][0]["path"]
    assert _match(explain, corpus, "entities") == []


def test_generic_corpus_word_retrieves_only_entities_that_mean_it(explain, corpus) -> None:
    matched = _match(explain, corpus, "knowledge")
    assert "knowledge-engine" in matched
    assert "billing-gateway" not in matched, (
        "an unrelated entity was retrieved for a generic corpus word it does not mean"
    )


def test_shared_owner_does_not_make_every_entity_relevant(explain, corpus) -> None:
    """Owner is provenance, not subject matter."""
    assert all(e["owner"] == OWNER for e in corpus["entities"])
    assert _match(explain, corpus, OWNER) == []


def test_relation_target_does_not_confer_lexical_relevance(explain, corpus) -> None:
    """Adjacency is Context Projection's job; lexical retrieval must not borrow a neighbour's name."""
    matched = _match(explain, corpus, "knowledge engine")
    assert "billing-gateway" not in matched, (
        "an entity was retrieved because of what it points at, not what it is"
    )


def test_authored_meaning_still_retrieves_its_entity(explain, corpus) -> None:
    """The fix must not be achieved by matching less."""
    assert _match(explain, corpus, "billing gateway") == ["billing-gateway"]
    assert _match(explain, corpus, "invoice dispatch") == ["billing-gateway"]
    assert _match(explain, corpus, "drift detection") == ["knowledge-engine"]


def test_entity_ranking_is_deterministic_and_meaning_ordered(explain, corpus) -> None:
    keywords = explain.tokenize("knowledge engine index generation")
    first = explain.match_entities(corpus, keywords, 25)
    second = explain.match_entities(corpus, keywords, 25)
    assert [e["id"] for e in first] == [e["id"] for e in second]
    assert first[0]["id"] == "knowledge-engine"


# --- `context_resolved`: flat Knowledge is first-class ------------------------------------------

# Every surface that defines, produces, validates, or consumes `context_resolved`.
RESOLVED_CONTEXT_SURFACES = (
    PLAN_TEMPLATE,
    COMMANDS_DIR / "plan.md",
    COMMANDS_DIR / "analyze.md",
    COMMANDS_DIR / "critic.md",
    COMMANDS_DIR / "implement.md",
)

# Kinds `context_resolved` must support, per the contract's four-kind table.
RESOLVED_KINDS = ("knowledge", "entity", "entity-layer", "decision")


def _read(path: Path) -> str:
    if not path.is_file():
        pytest.skip(f"{path.name} missing")
    return path.read_text(encoding="utf-8")


def test_plan_template_declares_every_resolved_kind() -> None:
    text = _read(PLAN_TEMPLATE)
    assert "context_resolved:" in text
    kind_line = next(
        (line for line in text.splitlines() if line.strip().startswith("kind:")), ""
    )
    assert kind_line, "plan-template.md must record a `kind` for each resolved item"
    for kind in RESOLVED_KINDS:
        assert kind in kind_line, f"plan-template.md `kind` field omits `{kind}`"


def test_plan_template_preserves_provenance_per_item() -> None:
    text = _read(PLAN_TEMPLATE)
    for field in ("id:", "kind:", "via:", "hop:", "reason:"):
        assert field in text, f"plan-template.md resolved item is missing `{field}`"


@pytest.mark.parametrize(
    "path", RESOLVED_CONTEXT_SURFACES, ids=lambda p: p.name
)
def test_resolved_context_surface_treats_flat_knowledge_as_first_class(path: Path) -> None:
    """No surface may describe resolved context as entities-and-decisions only."""
    text = _read(path).lower()
    assert "flat document" in text or "flat knowledge" in text, (
        f"{path.name} never names flat Knowledge documents, so it still models resolved "
        "context as entity-or-decision only"
    )


@pytest.mark.parametrize(
    "path", RESOLVED_CONTEXT_SURFACES, ids=lambda p: p.name
)
def test_resolved_context_surface_does_not_pair_entity_with_decision_alone(path: Path) -> None:
    """Guard the specific shorthand that excluded flat documents: `entity/decision`."""
    text = _read(path)
    assert "entity/decision" not in text.lower(), (
        f"{path.name} uses the `entity/decision` shorthand, which excludes flat Knowledge"
    )


# --- One hop policy ------------------------------------------------------------------------------

# Every surface that states a projection or escalation budget.
HOP_POLICY_SURFACES = (
    PLAN_TEMPLATE,
    COMMANDS_DIR / "plan.md",
    COMMANDS_DIR / "implement.md",
    COMMANDS_DIR / "critic.md",
    COMMANDS_DIR / "quickfix.md",
    COMMANDS_DIR / "specify.md",
    REPO_ROOT / ".knowledge" / "governance" / "devspark-prompt-mapping.md",
    REPO_ROOT / ".knowledge" / "governance" / "devspark-philosophy.md",
    REPO_ROOT / "site" / "src" / "guides" / "prompt-lifecycle-mapping.md",
    REPO_ROOT / "site" / "src" / "why" / "philosophy.md",
)

# A range is not a budget. Matches "2-3 hops" with any dash, and "3 hops".
RANGE_BUDGET_RE = re.compile(r"\d\s*[-\u2010-\u2015]\s*\d\s*hops", re.IGNORECASE)
THREE_HOPS_RE = re.compile(r"\b3\s*hops\b", re.IGNORECASE)


@pytest.mark.parametrize("path", HOP_POLICY_SURFACES, ids=lambda p: p.name)
def test_no_surface_states_a_competing_hop_budget(path: Path) -> None:
    text = _read(path)
    assert not RANGE_BUDGET_RE.search(text), (
        f"{path.name} states a hop *range*; the canonical budget is a single number"
    )
    assert not THREE_HOPS_RE.search(text), (
        f"{path.name} states a 3-hop budget, which exceeds the canonical planning budget of 2"
    )


def test_plan_template_hop_field_stays_within_the_planning_budget() -> None:
    text = _read(PLAN_TEMPLATE)
    hop_line = next((line for line in text.splitlines() if line.strip().startswith("hop:")), "")
    assert hop_line, "plan-template.md must record a `hop` for each resolved item"
    assert "3" not in hop_line, (
        "plan-template.md offers hop 3, above planning's 2-hop projection budget"
    )
    for allowed in ("0", "1", "2"):
        assert allowed in hop_line, f"plan-template.md `hop` field omits {allowed}"


def test_plan_states_the_canonical_two_hop_projection_budget() -> None:
    text = _read(COMMANDS_DIR / "plan.md").lower()
    assert "2 hops" in text or "--max-hops 2" in text, (
        "plan.md must state the 2-hop projection budget"
    )


def test_implement_allows_exactly_one_logged_additional_hop() -> None:
    text = _read(COMMANDS_DIR / "implement.md").lower()
    assert "one additional hop" in text, (
        "implement.md must bound its own traversal to one additional hop"
    )
    assert "log it" in text or "logged" in text, (
        "implement.md must require the escalation hop to be logged"
    )


def test_context_projection_default_matches_the_planning_budget() -> None:
    spec = importlib.util.spec_from_file_location(
        "context_projection_alignment", REPO_ROOT / "scripts" / "context-projection.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert module.DEFAULT_MAX_HOPS == 2, (
        "Context Projection's default depth must equal the canonical planning budget"
    )
