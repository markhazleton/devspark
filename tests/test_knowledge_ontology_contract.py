# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for the DevSpark 7.8-A Knowledge ontology and ownership contract.

These pin the answer to "what exactly is a bootstrap allowed to write?": which structural forms
exist, which semantic roles each form may carry, which entity types are legal, and which of the
two path-claim kinds may be treated as ownership. Every vocabulary is asserted against the single
machine-readable contract so the builder, the published schemas, and the documented ontology
cannot drift apart silently.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_knowledge_index as bki  # noqa: E402


def _load_hyphenated(name: str):
    """`discover-knowledge.py` is a CLI filename, not an importable module name."""
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


discovery = _load_hyphenated("discover-knowledge")

ONTOLOGY_PATH = ROOT / "templates" / "schemas" / "knowledge-ontology.json"
ENTITY_SCHEMA_PATH = ROOT / "templates" / "schemas" / "entity-node.schema.json"
TAXONOMY_SCHEMA_PATH = ROOT / "templates" / "schemas" / "taxonomy-registry.schema.json"
SCAFFOLD_SCRIPT = ROOT / "scripts" / "scaffold-entity.py"
MIGRATE_SCRIPT = ROOT / "scripts" / "migrate-knowledge-to-entities.py"


@pytest.fixture(scope="module")
def ontology() -> dict:
    return json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))


# --- Ontology: forms and roles are distinct axes -----------------------------------------------


def test_form_and_role_are_separate_axes(ontology: dict) -> None:
    """The 7.8-A premise. A single `type` field could not express both an entity layer's
    structural form and the kind of truth it carries, which made valid documents permanently
    unclassifiable. Forms and roles must stay separately enumerated."""
    assert set(ontology["forms"]["values"]) == bki.FORMS
    assert ontology["roles"]["byForm"].keys() == bki.FORM_ROLES.keys()
    for form, roles in ontology["roles"]["byForm"].items():
        assert set(roles) == bki.FORM_ROLES[form], f"role vocabulary drift for form '{form}'"


def test_only_flat_documents_draw_their_role_from_the_taxonomy(ontology: dict) -> None:
    """A structural form is a fact about where a document lives, so the registry must not be able
    to assign one. This is what stops a valid entity layer from being reported as mismatched."""
    assert ontology["roles"]["assignableByTaxonomy"] == bki.FORM_FLAT
    registry_assignable = set(
        json.loads(TAXONOMY_SCHEMA_PATH.read_text(encoding="utf-8"))["definitions"]["mapping"][
            "properties"
        ]["nodeType"]["enum"]
    )
    assert registry_assignable == bki.FLAT_ROLES
    assert not registry_assignable & (bki.FORMS - {bki.FORM_FLAT})


def test_every_form_resolves_to_a_role(ontology: dict) -> None:
    """No form may exist without a defined role domain, or classification would have a hole that
    an author could only fill by guessing."""
    for form in bki.FORMS:
        assert bki.FORM_ROLES.get(form), f"form '{form}' has no role vocabulary"


def test_compat_type_preserves_historical_values() -> None:
    """7.7.x consumers read a single `type`. Adding the form/role axes must not renumber the
    world beneath them."""
    assert bki.compat_type(bki.FORM_FLAT, "architecture") == "architecture"
    assert bki.compat_type(bki.FORM_ENTITY_LAYER, "business") == bki.FORM_ENTITY_LAYER
    assert bki.compat_type(bki.FORM_GOVERNANCE_DECISION, "governance") == bki.FORM_GOVERNANCE_DECISION


def test_form_is_inferred_from_location() -> None:
    assert bki.infer_form(".knowledge/entities/widget/architecture.md") == bki.FORM_ENTITY_LAYER
    assert bki.infer_form(".knowledge/governance/decisions/x.md") == bki.FORM_GOVERNANCE_DECISION
    assert bki.infer_form(".knowledge/guides/x.md") == bki.FORM_FLAT


def test_a_directory_index_is_navigation_not_a_member_of_it() -> None:
    """A README beside the decisions describes the folder; it does not make a decision. Deciding
    that by filename is what keeps form structural -- the alternative is letting frontmatter
    exempt a file from what it structurally is."""
    assert bki.infer_form(".knowledge/governance/decisions/README.md") == bki.FORM_FLAT
    assert bki.infer_form(".knowledge/governance/decisions/index.md") == bki.FORM_FLAT
    assert bki.infer_form(".knowledge/governance/decisions/retention.md") == (
        bki.FORM_GOVERNANCE_DECISION
    )


def test_ontology_declares_form_derived_rather_than_authored(ontology: dict) -> None:
    determination = ontology["forms"]["determination"]
    assert determination["authored"] is False
    assert determination["persisted"] == "derived"
    assert set(determination["navigationFilenames"]) == bki.NAVIGATION_FILENAMES


def test_canonical_fields_name_form_and_role_not_type(ontology: dict) -> None:
    """A 7.8-B consumer must never have to work out which meaning of `type` was intended."""
    fields = ontology["canonicalFields"]
    assert fields["form"]["canonical"] == "node.form"
    assert fields["role"]["canonical"] == "node.role"
    assert "type" in fields["form"]["compatibility"]
    assert "type" in fields["role"]["compatibility"]


def test_role_authoring_matrix_matches_the_implementation(ontology: dict) -> None:
    """Only a flat document's author owns the role axis. A layer's role is its layer and a
    decision's is governance, so neither is overridable."""
    by_source = ontology["roles"]["bySource"]
    assert by_source.keys() == bki.FORM_ROLES.keys()
    assert by_source[bki.FORM_FLAT]["authorMayOverride"] is True
    assert by_source[bki.FORM_ENTITY_LAYER]["authorMayOverride"] is False
    assert by_source[bki.FORM_GOVERNANCE_DECISION]["authorMayOverride"] is False


def test_resolve_role_reports_the_pattern_that_decided(ontology: dict) -> None:
    """Callers need to know how firmly the taxonomy spoke: a glob is a directory default, an
    exact path is a statement about one file."""
    glob_mapping = {"pathPattern": ".knowledge/guides/**", "nodeType": "reference-data"}
    role, pattern = bki.resolve_role(".knowledge/guides/x.md", [glob_mapping])
    assert (role, pattern) == ("reference-data", ".knowledge/guides/**")
    role, pattern = bki.resolve_role(".knowledge/nowhere/x.md", [])
    assert (role, pattern) == (bki.DEFAULT_ROLE, None)


# --- Taxonomy resolution: specificity, not declaration order -----------------------------------


def test_specific_mapping_beats_broader_one_regardless_of_order() -> None:
    """Resolution must not depend on which list happened to be scanned first. The same two
    mappings in either order must produce the same role."""
    broad = {"pathPattern": ".knowledge/governance/**", "nodeType": "governance"}
    narrow = {"pathPattern": ".knowledge/governance/runbooks/**", "nodeType": "operations-runbook"}
    target = ".knowledge/governance/runbooks/failover.md"
    assert bki.infer_role(target, [broad, narrow]) == "operations-runbook"
    assert bki.infer_role(target, [narrow, broad]) == "operations-runbook"


def test_registry_override_beats_builtin_default_at_equal_specificity() -> None:
    """A repository must still be able to override a built-in default; the specificity rule may
    not quietly take that away."""
    override = {"pathPattern": ".knowledge/guides/**", "nodeType": "operations-runbook"}
    assert bki.infer_role(".knowledge/guides/x.md", [override]) == "operations-runbook"
    assert bki.infer_role(".knowledge/guides/x.md", []) == "authoritative-reference"


def test_equally_specific_conflicting_mappings_fail_loudly() -> None:
    """Two same-origin mappings of identical specificity that disagree are genuinely ambiguous.
    Resolving by list position would silently pick a winner and call it truth."""
    with pytest.raises(ValueError, match="ambiguous"):
        bki.infer_role(
            ".knowledge/guides/x.md",
            [
                {"pathPattern": ".knowledge/guides/**", "nodeType": "operations-runbook"},
                {"pathPattern": ".knowledge/guides/**", "nodeType": "reference-data"},
            ],
        )


def test_unmapped_path_resolves_to_a_declared_default() -> None:
    assert bki.infer_role(".knowledge/unmapped/thing.md", []) == bki.DEFAULT_ROLE
    assert bki.DEFAULT_ROLE in bki.FLAT_ROLES


# --- Entity type: controlled vocabulary, advisory only -----------------------------------------


def test_entity_types_are_a_closed_vocabulary_with_meanings(ontology: dict) -> None:
    """An uncontrolled free-text type is indistinguishable from a guess. Each value must also
    carry a definition, so an author can choose without inventing a convention."""
    assert set(ontology["entityTypes"]["values"]) == set(bki.ENTITY_TYPES)
    for name, description in bki.ENTITY_TYPES.items():
        assert description.strip(), f"entity type '{name}' has no definition"


def test_entity_schema_pins_the_same_entity_vocabulary() -> None:
    schema = json.loads(ENTITY_SCHEMA_PATH.read_text(encoding="utf-8"))
    assert set(schema["properties"]["type"]["enum"]) == set(bki.ENTITY_TYPES)


def test_entity_type_does_not_mandate_layers(tmp_path: Path) -> None:
    """Entity type is a semantic label, not a coverage requirement. Four entities that differ only
    by type, with identical layer coverage, must produce identical coverage results -- otherwise
    choosing a type would silently obligate an author to write documents they have no evidence
    for. (Note `integration` is deliberately both an entity type and a layer name: an entity can
    *be* a boundary, or merely *have* an integration facet. The names coincide; the axes do not.)
    """
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "widget.py").write_text("x = 1\n", encoding="utf-8")
    for entity_type in sorted(bki.ENTITY_TYPES):
        entity_dir = repo / ".knowledge" / "entities" / f"e-{entity_type}"
        entity_dir.mkdir(parents=True)
        (entity_dir / "_entity.yaml").write_text(
            f"id: e-{entity_type}\ntype: {entity_type}\nowner: team-x\n", encoding="utf-8"
        )
        layer_meta = {
            "type": "entity-layer",
            "layer": "architecture",
            "title": f"{entity_type} architecture",
            "source_of_truth": ["src/widget.py"],
            "last_verified": "2099-01-01",
        }
        (entity_dir / "architecture.md").write_text(
            f"---\n{yaml.safe_dump(layer_meta, sort_keys=False)}---\n\n# Arch\n\nBody.\n",
            encoding="utf-8",
        )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_knowledge_index.py"), "--repo-root", str(repo)],
        check=True, capture_output=True, text=True, timeout=120,
    )
    index = json.loads((repo / ".knowledge" / "index.json").read_text(encoding="utf-8"))
    coverage = {
        entity["type"]: (tuple(sorted(entity["layers"])), tuple(sorted(entity["missing_layers"])))
        for entity in index["entities"]
    }
    assert len(coverage) == len(bki.ENTITY_TYPES)
    assert len(set(coverage.values())) == 1, (
        f"entity type changed required layer coverage: {coverage}"
    )


def test_entity_schema_keeps_coverage_evidence_driven() -> None:
    schema = json.loads(ENTITY_SCHEMA_PATH.read_text(encoding="utf-8"))
    assert "if" not in schema and "allOf" not in schema, (
        "the entity schema must not make layer presence conditional on entity type"
    )
    assert "coverage_overrides" in schema["properties"], (
        "layer coverage is declared per entity by evidence, not implied by its type"
    )


def test_unknown_entity_type_is_rejected(tmp_path: Path) -> None:
    entity_dir = tmp_path / ".knowledge" / "entities" / "widget"
    entity_dir.mkdir(parents=True)
    entity_yaml = entity_dir / "_entity.yaml"
    entity_yaml.write_text("id: widget\ntype: service\nowner: team-x\n", encoding="utf-8")
    with pytest.raises(ValueError, match="not a known entity type"):
        bki.load_entity_node(entity_yaml)


def test_known_entity_type_is_accepted(tmp_path: Path) -> None:
    entity_dir = tmp_path / ".knowledge" / "entities" / "widget"
    entity_dir.mkdir(parents=True)
    entity_yaml = entity_dir / "_entity.yaml"
    entity_yaml.write_text("id: widget\ntype: subsystem\nowner: team-x\n", encoding="utf-8")
    assert bki.load_entity_node(entity_yaml)["type"] == "subsystem"


# --- Ownership vs applicability ----------------------------------------------------------------


def test_claim_kinds_are_documented_and_distinct(ontology: dict) -> None:
    kinds = ontology["claimKinds"]["values"]
    assert set(kinds) == {"source_of_truth", "appliesTo"}
    assert kinds["source_of_truth"] != kinds["appliesTo"]
    # The consumer that actually separates the two kinds must name the same fields, or the
    # published contract could describe a distinction the code had stopped making.
    assert discovery.CLAIM_OWNERSHIP == "source_of_truth"
    assert discovery.CLAIM_APPLICABILITY == "appliesTo"
    assert {discovery.CLAIM_OWNERSHIP, discovery.CLAIM_APPLICABILITY} == set(kinds)


def test_entity_layer_may_not_declare_links(tmp_path: Path) -> None:
    """Relationships belong to the entity; a layer describes one facet. Accepting `links` here
    produced a field that looked authored but never reached the graph."""
    doc = tmp_path / "architecture.md"
    doc.write_text("# x\n", encoding="utf-8")
    metadata = {
        "layer": "architecture",
        "source_of_truth": ["scripts/x.py"],
        "last_verified": "2026-01-01",
        "links": {"references": ["other"]},
    }
    with pytest.raises(ValueError, match="cannot declare 'links'"):
        bki.validate_entity_layer_doc(tmp_path, doc, metadata, [])


def _ownership_repo(tmp_path: Path) -> Path:
    """A repository where one entity OWNS a file and a separate governance document APPLIES to
    the same file. That is normal and must never be reported as an ownership conflict."""
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "widget.py").write_text("x = 1\n", encoding="utf-8")

    entity_dir = repo / ".knowledge" / "entities" / "widget"
    entity_dir.mkdir(parents=True)
    (entity_dir / "_entity.yaml").write_text(
        "id: widget\ntype: subsystem\nowner: team-x\n", encoding="utf-8"
    )
    layer_meta = {
        "type": "entity-layer",
        "layer": "architecture",
        "title": "Widget architecture",
        "source_of_truth": ["src/widget.py"],
        "last_verified": "2099-01-01",
    }
    (entity_dir / "architecture.md").write_text(
        f"---\n{yaml.safe_dump(layer_meta, sort_keys=False)}---\n\n# Widget architecture\n\nBody.\n",
        encoding="utf-8",
    )

    governance = repo / ".knowledge" / "governance"
    governance.mkdir(parents=True)
    gov_meta = {
        "id": "coding-standard",
        "type": "governance",
        "title": "Coding standard",
        "appliesTo": ["src/widget.py"],
    }
    (governance / "coding-standard.md").write_text(
        f"---\n{yaml.safe_dump(gov_meta, sort_keys=False)}---\n\n# Coding standard\n\nBody.\n",
        encoding="utf-8",
    )
    return repo


def test_applicability_does_not_create_an_ownership_conflict(tmp_path: Path) -> None:
    repo = _ownership_repo(tmp_path)
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_knowledge_index.py"), "--repo-root", str(repo)],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "discover-knowledge.py"), "--repo-root", str(repo), "--json"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    payload = json.loads(result.stdout)
    overlaps = [f for f in payload["FINDINGS"] if f["category"] == "overlapping-ownership"]
    assert overlaps == [], (
        "a governance document applying to a file an entity owns is normal co-existence, "
        f"not competing ownership; got {overlaps}"
    )


def test_two_entities_owning_the_same_file_is_still_reported(tmp_path: Path) -> None:
    """The regression guard's mirror image: suppressing the false positive must not also
    suppress the true one."""
    repo = _ownership_repo(tmp_path)
    other = repo / ".knowledge" / "entities" / "gadget"
    other.mkdir(parents=True)
    (other / "_entity.yaml").write_text(
        "id: gadget\ntype: subsystem\nowner: team-y\n", encoding="utf-8"
    )
    layer_meta = {
        "type": "entity-layer",
        "layer": "architecture",
        "title": "Gadget architecture",
        "source_of_truth": ["src/widget.py"],
        "last_verified": "2099-01-01",
    }
    (other / "architecture.md").write_text(
        f"---\n{yaml.safe_dump(layer_meta, sort_keys=False)}---\n\n# Gadget architecture\n\nBody.\n",
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_knowledge_index.py"), "--repo-root", str(repo)],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "discover-knowledge.py"), "--repo-root", str(repo), "--json"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    payload = json.loads(result.stdout)
    overlaps = [f for f in payload["FINDINGS"] if f["category"] == "overlapping-ownership"]
    assert len(overlaps) == 1, f"two entities owning one file must still be reported; got {overlaps}"
    kinds = [e for e in overlaps[0]["evidence"] if e.get("type") == "claim-kind"]
    assert kinds and kinds[0]["value"] == "source_of_truth", (
        "the finding must state which claim kind it is about, so a reader can tell ownership "
        "from applicability without re-deriving it"
    )


# --- Authoring tools may not fabricate authoritative metadata ----------------------------------


def test_scaffold_rejects_an_unknown_entity_type(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable, str(SCAFFOLD_SCRIPT), "--repo-root", str(tmp_path),
            "--entity-id", "widget", "--type", "service", "--owner", "team-x",
            "--source", "x.py", "--layer", "architecture", "--json",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode != 0
    assert "invalid choice" in result.stderr


def test_migration_refuses_to_invent_owner_or_type(tmp_path: Path) -> None:
    """A placeholder owner is indistinguishable from a real one once written. The migration must
    refuse rather than manufacture metadata that looks authoritative and is not."""
    repo = tmp_path / "repo"
    docs = repo / ".knowledge" / "architecture"
    docs.mkdir(parents=True)
    meta = {"id": "widget", "type": "architecture", "title": "Widget"}
    (docs / "widget.md").write_text(
        f"---\n{yaml.safe_dump(meta, sort_keys=False)}---\n\n# Widget\n\nBody.\n", encoding="utf-8"
    )
    result = subprocess.run(
        [sys.executable, str(MIGRATE_SCRIPT), "--repo-root", str(repo), "--yes"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode != 0
    assert "--owner" in result.stderr and "--entity-type" in result.stderr
    assert not list(repo.glob(".knowledge/entities/**/_entity.yaml")), (
        "a refused migration must leave no partially-authored entity behind"
    )


# --- Structure outranks declaration ------------------------------------------------------------


def _write_doc(path: Path, metadata: dict, body: str = "Body.") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\n{yaml.safe_dump(metadata, sort_keys=False)}---\n\n# {metadata.get('title', 'Doc')}"
        f"\n\n{body}\n",
        encoding="utf-8",
    )


def test_frontmatter_may_not_declare_a_structural_form(tmp_path: Path) -> None:
    """Authored metadata outranks inference on an axis the author owns, but a form is a fact
    about where the file lives. Without this a stray document could call itself an entity layer
    while belonging to no entity."""
    repo = tmp_path / "repo"
    _write_doc(
        repo / ".knowledge" / "guides" / "stray.md",
        {"id": "stray", "type": "entity-layer", "title": "Stray"},
    )
    with pytest.raises(ValueError, match="form is structural"):
        bki.build_index(repo)


def test_navigational_readme_beside_decisions_builds_as_a_flat_document(tmp_path: Path) -> None:
    """The case that forced the rule: a decisions README has no `constrains` list and is not a
    decision, and it must classify correctly without declaring its own structure."""
    repo = tmp_path / "repo"
    _write_doc(
        repo / ".knowledge" / "governance" / "decisions" / "README.md",
        {"id": "decisions-readme", "type": "governance", "title": "Decisions"},
    )
    index = bki.build_index(repo)
    node = next(n for n in index["nodes"] if n["id"] == "decisions-readme")
    assert node["form"] == bki.FORM_FLAT
    assert node["role"] == "governance"
    assert node["type"] == "governance"


def test_an_entity_layers_role_is_the_facet_it_describes(tmp_path: Path) -> None:
    """A layer's role is not authored and not taxonomy-assigned: the facet it covers IS the kind
    of truth it carries, which is why the registry must never be able to reclassify one."""
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "x.py").write_text("x = 1\n", encoding="utf-8")
    entity_dir = repo / ".knowledge" / "entities" / "widget"
    entity_dir.mkdir(parents=True)
    (entity_dir / "_entity.yaml").write_text(
        "id: widget\ntype: subsystem\nowner: team-x\n", encoding="utf-8"
    )
    _write_doc(
        entity_dir / "operations.md",
        {
            "type": "entity-layer",
            "layer": "operations",
            "title": "Widget operations",
            "source_of_truth": ["src/x.py"],
            "last_verified": "2099-01-01",
        },
    )
    index = bki.build_index(repo)
    node = next(n for n in index["nodes"] if n["id"] == "widget-operations")
    assert node["form"] == bki.FORM_ENTITY_LAYER
    assert node["role"] == "operations"
    assert node["type"] == bki.FORM_ENTITY_LAYER


def test_mentioning_a_file_is_not_claiming_it(tmp_path: Path) -> None:
    """Ownership is an explicit claim. If prose counted, every document naming a path would
    compete for it and the overlap signal would drown in coincidence."""
    repo = _ownership_repo(tmp_path)
    _write_doc(
        repo / ".knowledge" / "architecture" / "overview.md",
        {"id": "overview", "type": "architecture", "title": "Overview"},
        body="The scheduler calls into src/widget.py during dispatch.",
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_knowledge_index.py"), "--repo-root", str(repo)],
        check=True, capture_output=True, text=True, timeout=120,
    )
    index = json.loads((repo / ".knowledge" / "index.json").read_text(encoding="utf-8"))
    overview = next(n for n in index["nodes"] if n["id"] == "overview")
    assert not overview.get("source_of_truth")

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "discover-knowledge.py"), "--repo-root", str(repo), "--json"],
        capture_output=True, text=True, timeout=120,
    )
    payload = json.loads(result.stdout)
    overlaps = [f for f in payload["FINDINGS"] if f["category"] == "overlapping-ownership"]
    assert overlaps == [], f"a prose mention must not compete for ownership; got {overlaps}"


def test_an_entity_type_and_a_layer_role_may_both_be_integration(tmp_path: Path) -> None:
    """The two vocabularies are independent axes that happen to share a word. An entity may BE a
    boundary or merely HAVE a boundary-facing facet, and neither implies the other."""
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "x.py").write_text("x = 1\n", encoding="utf-8")
    for entity_id, entity_type, layer in (
        ("boundary", "integration", "architecture"),
        ("engine", "subsystem", "integration"),
    ):
        entity_dir = repo / ".knowledge" / "entities" / entity_id
        entity_dir.mkdir(parents=True)
        (entity_dir / "_entity.yaml").write_text(
            f"id: {entity_id}\ntype: {entity_type}\nowner: team-x\n", encoding="utf-8"
        )
        _write_doc(
            entity_dir / f"{layer}.md",
            {
                "type": "entity-layer",
                "layer": layer,
                "title": f"{entity_id} {layer}",
                "source_of_truth": ["src/x.py"],
                "last_verified": "2099-01-01",
            },
        )
    index = bki.build_index(repo)
    by_id = {e["id"]: e for e in index["entities"]}
    assert by_id["boundary"]["type"] == "integration"
    assert by_id["boundary"]["layers"] == ["architecture"]
    assert by_id["engine"]["type"] == "subsystem"
    assert by_id["engine"]["layers"] == ["integration"]


def test_a_test_file_may_be_source_of_truth(tmp_path: Path) -> None:
    """Tests prove and constrain behavior, so they are first-class evidence ownership. Treating
    ownership as production-only would leave the behavior a test pins unowned."""
    repo = tmp_path / "repo"
    (repo / "tests").mkdir(parents=True)
    (repo / "tests" / "test_widget.py").write_text("def test_x():\n    pass\n", encoding="utf-8")
    entity_dir = repo / ".knowledge" / "entities" / "widget"
    entity_dir.mkdir(parents=True)
    (entity_dir / "_entity.yaml").write_text(
        "id: widget\ntype: subsystem\nowner: team-x\n", encoding="utf-8"
    )
    _write_doc(
        entity_dir / "business.md",
        {
            "type": "entity-layer",
            "layer": "business",
            "title": "Widget rules",
            "source_of_truth": ["tests/test_widget.py"],
            "last_verified": "2099-01-01",
        },
    )
    index = bki.build_index(repo)
    node = next(n for n in index["nodes"] if n["id"] == "widget-business")
    assert node["source_of_truth"] == ["tests/test_widget.py"]


def test_entity_type_and_entity_layer_vocabularies_stay_independent(ontology: dict) -> None:
    assert "integration" in bki.ENTITY_TYPES
    assert "integration" in bki.ALLOWED_LAYERS
    assert ontology["entityTypes"]["layerIndependence"]


def test_unknown_entity_type_blocks_materialization_without_a_fallback(ontology: dict) -> None:
    """A fallback type would let an uncertain classification become authoritative silently.
    Uncertainty blocks materialization; it does not block recognizing the concept."""
    unknown = ontology["entityTypes"]["unknownType"]
    assert unknown["behavior"] == "block-materialization"
    assert "no fallback type" in unknown["rule"].lower()


def test_entity_vocabulary_is_extensible_only_by_deliberate_change(ontology: dict) -> None:
    extensibility = ontology["entityTypes"]["extensibility"]
    assert extensibility["closedFor"] == "materialization"
    assert len(extensibility["requirementsToAdd"]) >= 4


# --- What an integrity finding means -----------------------------------------------------------


def _taxonomy_mismatches(tmp_path: Path, pattern: str) -> list[dict]:
    """Build a repo whose registry maps `pattern` to one role while the document declares
    another, then report what integrity makes of the disagreement."""
    repo = tmp_path / "repo"
    _write_doc(
        repo / ".knowledge" / "guides" / "runbook.md",
        {"id": "runbook", "type": "operations-runbook", "title": "Runbook"},
    )
    (repo / ".knowledge" / "taxonomy-registry.json").write_text(
        json.dumps({"mappings": [{"pathPattern": pattern, "nodeType": "authoritative-reference"}]}),
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_knowledge_index.py"), "--repo-root", str(repo)],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "knowledge-integrity.py"), "--repo-root", str(repo), "--json"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    payload = json.loads(result.stdout)
    return [f for f in payload["FINDINGS"] if f["category"] == "taxonomy-mismatch"]


def test_declaring_a_role_against_a_broad_glob_is_not_a_finding(tmp_path: Path) -> None:
    """A glob states a directory's default. A document inside it choosing a different role is the
    precedence rule working, and a report that keeps listing it trains readers to skim past."""
    assert _taxonomy_mismatches(tmp_path, ".knowledge/guides/**") == []


def test_contradicting_an_exact_path_mapping_is_a_finding(tmp_path: Path) -> None:
    """Its mirror image: an exact-path mapping is a statement about one file, so a document
    disagreeing means two deliberate statements conflict and someone has to settle it."""
    findings = _taxonomy_mismatches(tmp_path, ".knowledge/guides/runbook.md")
    assert len(findings) == 1
    assert findings[0]["subject"] == "runbook"
