"""Contract: deterministic token semantics and structural entity/layer projection.

Retrieval must match whole words, fold only number inflection, and let a correctly seeded entity
reach its own layer documents through the graph.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


explain = _load("explain_context_tokens", "explain-context.py")
projection = _load("context_projection_tokens", "context-projection.py")
builder = _load("build_knowledge_index_tokens", "build_knowledge_index.py")


# --------------------------------------------------------------------------- tokenization

@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("scripts/build_knowledge_index.py", {"script", "build", "knowledge", "index", "py"}),
        ("buildKnowledgeIndex", {"build", "knowledge", "index"}),
        ("HTTPServerError", {"http", "server", "error"}),
        ("context-projection.py", {"context", "projection", "py"}),
        ("Knowledge Engine: architecture", {"knowledge", "engine", "architecture"}),
    ],
)
def test_tokenization_splits_punctuation_case_and_identifiers(text, expected):
    assert expected <= set(explain.tokenize_text(text))


def test_tokenization_is_case_insensitive():
    assert explain.tokenize_text("Drift Check") == explain.tokenize_text("drift check")


@pytest.mark.parametrize(
    ("plural", "singular"),
    [
        ("findings", "finding"),
        ("systems", "system"),
        ("layers", "layer"),
        ("queries", "query"),
        ("entities", "entity"),
        ("matches", "match"),
        ("aliases", "alias"),
        ("artifacts", "artifact"),
    ],
)
def test_number_inflection_folds_to_singular(plural, singular):
    assert explain.normalize_token(plural) == singular


@pytest.mark.parametrize("word", ["status", "analysis", "process", "class", "alias", "series"])
def test_singular_nouns_ending_in_s_are_left_alone(word):
    assert explain.normalize_token(word) == word


# --------------------------------------------------------------------- matching decisions

MATCHING_DECISIONS = [
    # A query term and a candidate word that merely contains it are different words.
    ("system", "subsystem", False),
    ("plan", "planner", False),
    ("config", "configuration", False),
    ("run", "runtime", False),
    ("find", "finding", False),
    ("index", "indexer", False),
    # Number inflection is the same word.
    ("finding", "findings", True),
    ("findings", "finding", True),
    ("layer", "layers", True),
    ("entity", "entities", True),
    ("alias", "aliases", True),
]


@pytest.mark.parametrize(("keyword", "haystack", "should_match"), MATCHING_DECISIONS)
def test_matching_is_token_aware_not_substring(keyword, haystack, should_match):
    assert bool(explain.keyword_hits(haystack, [keyword])) is should_match


def test_substring_containment_no_longer_drives_relevance():
    """The historical false positive: 'system' scored against a document saying 'subsystem'."""
    assert "system" in "subsystem"
    assert explain.keyword_hits("subsystem architecture", ["system"]) == []


# ------------------------------------------------------------------------------ stopwords

@pytest.mark.parametrize(
    "word", ["not", "their", "should", "than", "from", "about", "because", "has", "let", "out", "which"]
)
def test_function_words_are_removed_from_queries(word):
    assert word not in explain.tokenize(f"{word} knowledge drift detection")


@pytest.mark.parametrize("word", ["system", "work", "check", "order", "claim", "source", "code", "plan"])
def test_open_class_words_are_retained(word):
    """Generic-sounding nouns still name real things in a repository and must keep scoring."""
    assert word in explain.tokenize(f"the {word} of a thing")


def test_inflected_stopwords_are_removed_after_normalization():
    assert "doe" not in explain.tokenize("what does the drift check do")


def test_query_of_only_stopwords_still_yields_terms():
    assert explain.tokenize("what is the") != []


# --------------------------------------------------------------- structural graph edges

def _index() -> dict:
    return json.loads((REPO / ".knowledge" / "index.json").read_text(encoding="utf-8"))


def test_builder_materializes_entity_to_layer_edges():
    index = _index()
    structural = [e for e in index["edges"] if e["rel"] == "has-layer"]
    assert structural, "entity composition must be materialized by the canonical builder"
    for entity in index["entities"]:
        layers = [n["id"] for n in index["nodes"] if n.get("entity") == entity["id"]]
        emitted = {e["to"] for e in structural if e["from"] == entity["id"]}
        assert emitted == set(layers)


def test_structural_edges_are_not_authored_relations():
    """Composition is inherent in the entity model; authors never restate it in relations[]."""
    index = _index()
    for entity in index["entities"]:
        targets = {
            str(r.get("object") or r.get("to") or "") for r in (entity.get("relations") or [])
        }
        layers = {n["id"] for n in index["nodes"] if n.get("entity") == entity["id"]}
        assert not (targets & layers)


def test_entity_seed_projects_to_its_own_layers():
    index = _index()
    for entity in index["entities"]:
        result = projection.project_context(index, [entity["id"]])
        reached = {c["id"] for c in result["CANDIDATES"]}
        layers = {n["id"] for n in index["nodes"] if n.get("entity") == entity["id"]}
        assert layers <= reached, f"{entity['id']} cannot reach its own layers"


def test_layer_seed_projects_back_to_its_entity():
    index = _index()
    layer = next(n for n in index["nodes"] if n.get("entity"))
    result = projection.project_context(index, [layer["id"]])
    assert layer["entity"] in {c["id"] for c in result["CANDIDATES"]}


def test_structural_provenance_is_distinguishable():
    index = _index()
    entity = index["entities"][0]
    result = projection.project_context(index, [entity["id"]])
    layers = {n["id"] for n in index["nodes"] if n.get("entity") == entity["id"]}
    for candidate in result["CANDIDATES"]:
        if candidate["id"] not in layers:
            continue
        kinds = {r["type"] for r in candidate["reasons"]}
        assert "structural_composition" in kinds
        assert "graph_relation" not in kinds


def test_reason_types_separate_structural_architectural_and_governance():
    index = _index()
    # One entity that has layers, an authored dependency, and a governing decision.
    result = projection.project_context(index, ["context-resolution"])
    kinds = {r["type"] for c in result["CANDIDATES"] for r in c["reasons"]}
    assert {"structural_composition", "graph_relation", "governance_constraint"} <= kinds


def test_layer_expansion_costs_a_hop_and_stays_bounded():
    index = _index()
    entity = next(e for e in index["entities"] if e["id"] == "knowledge-engine")
    layers = {n["id"] for n in index["nodes"] if n.get("entity") == entity["id"]}
    result = projection.project_context(index, [entity["id"]], max_hops=1)
    reached = {c["id"]: c["distance"] for c in result["CANDIDATES"]}
    assert layers <= set(reached)
    assert all(reached[layer] == 1 for layer in layers), "layers are one hop, never free"


def test_projection_remains_cycle_safe_and_within_candidate_limits():
    index = _index()
    seeds = [e["id"] for e in index["entities"]] + [n["id"] for n in index["nodes"]]
    result = projection.project_context(index, seeds)
    ids = [c["id"] for c in result["CANDIDATES"]]
    assert len(ids) == len(set(ids))
    assert result["GUARDRAILS"]["truncated"] is False


def test_projection_is_deterministic():
    index = _index()
    runs = [
        json.dumps(projection.project_context(index, ["knowledge-engine", "context-resolution"]))
        for _ in range(3)
    ]
    assert len(set(runs)) == 1


# ------------------------------------------------------ RD-4 historical recovery cases

@pytest.mark.parametrize(
    ("owned_file", "entity_id"),
    [
        ("scripts/explain-context.py", "context-resolution"),
        ("scripts/build_knowledge_index.py", "knowledge-engine"),
    ],
)
def test_entity_seed_recovers_the_layer_that_owns_a_file(owned_file, entity_id):
    """A lexical miss on the layer is recoverable whenever the parent entity is found."""
    index = _index()
    owners = {
        n["id"]
        for n in index["nodes"]
        if owned_file in {
            (c if isinstance(c, str) else c.get("path")) for c in (n.get("source_of_truth") or [])
        }
    }
    assert owners, f"no knowledge node owns {owned_file}"
    reached = {c["id"] for c in projection.project_context(index, [entity_id])["CANDIDATES"]}
    assert owners <= reached


# ------------------------------------------------------------------- plan contract shape

def _synthetic_index() -> dict:
    """One seed that reaches exactly one relevant neighbor and two plausible-but-irrelevant ones."""
    return {
        "nodes": [
            {"id": "billing-architecture", "entity": "billing", "type": "architecture", "title": "Billing architecture"},
            {"id": "billing-business", "entity": "billing", "type": "business", "title": "Billing business"},
            {"id": "billing-operations", "entity": "billing", "type": "operations", "title": "Billing operations"},
            {"id": "data-retention", "type": "governance-decision", "title": "Data retention"},
            {"id": "ledger-architecture", "entity": "ledger", "type": "architecture", "title": "Ledger architecture"},
        ],
        "entities": [{"id": "billing"}, {"id": "ledger"}],
        "edges": [
            {"from": "billing", "to": "billing-architecture", "rel": "has-layer"},
            {"from": "billing", "to": "billing-business", "rel": "has-layer"},
            {"from": "billing", "to": "billing-operations", "rel": "has-layer"},
            {"from": "billing", "to": "ledger", "rel": "depends-on"},
            {"from": "data-retention", "to": "billing", "rel": "constrains"},
            {"from": "ledger", "to": "ledger-architecture", "rel": "has-layer"},
        ],
    }


def test_projection_is_generous_so_selection_has_something_to_prune():
    result = projection.project_context(_synthetic_index(), ["billing"], max_hops=1)
    reached = {c["id"] for c in result["CANDIDATES"] if c["distance"] > 0}
    assert reached == {"billing-architecture", "billing-business", "billing-operations",
                       "ledger", "data-retention"}


def test_provenance_lets_a_consumer_select_only_the_relevant_neighbor():
    """Selecting requires telling composition and governance apart from a real dependency."""
    result = projection.project_context(_synthetic_index(), ["billing"], max_hops=1)
    by_kind: dict[str, set[str]] = {}
    for candidate in result["CANDIDATES"]:
        for reason in candidate["reasons"]:
            by_kind.setdefault(reason["type"], set()).add(candidate["id"])
    assert by_kind["graph_relation"] == {"ledger"}
    assert by_kind["governance_constraint"] == {"data-retention"}
    assert by_kind["structural_composition"] == {
        "billing-architecture", "billing-business", "billing-operations"
    }


def test_sibling_layers_are_reachable_but_individually_identifiable():
    """Plan must be able to drop sibling layers it does not need without losing the entity."""
    result = projection.project_context(_synthetic_index(), ["billing"], max_hops=1)
    siblings = [c for c in result["CANDIDATES"]
                if any(r["type"] == "structural_composition" for r in c["reasons"])]
    assert len(siblings) == 3
    assert all(c["distance"] == 1 for c in siblings)
    assert len({c["id"] for c in siblings}) == 3


PLAN_SURFACES = [REPO / "templates" / "commands" / "plan.md", REPO / "templates" / "plan-template.md"]


def test_plan_surfaces_separate_candidate_context_from_resolved_context():
    for surface in PLAN_SURFACES:
        text = surface.read_text(encoding="utf-8").lower()
        assert "context_resolved" in text
        assert "candidate" in text, f"{surface.name} must name the candidate stage it prunes"


def test_plan_does_not_promise_to_resolve_every_candidate():
    text = (REPO / "templates" / "commands" / "plan.md").read_text(encoding="utf-8").lower()
    # The obligation is a narrowing one, and it has to be stated as such.
    assert "smallest" in text
    assert "candidate context is not resolved context" in text
    assert "not required to include every candidate" in text


def test_projection_command_declares_candidates_are_not_resolved_context():
    text = (REPO / "templates" / "commands" / "context-projection.md").read_text(encoding="utf-8")
    lowered = text.lower()
    assert "candidate" in lowered
    assert "context_resolved" in lowered


# --------------------------------------------------------------- cross-language parity

def test_index_build_is_reproducible():
    """Structural edges must not make the generated artifact drift against itself."""
    result = subprocess.run(
        [sys.executable, "scripts/build_knowledge_index.py", "--repo-root", ".", "--check"],
        cwd=REPO, capture_output=True, text=True, timeout=300,
    )
    assert result.returncode == 0, result.stdout + result.stderr
