"""Contract tests for OKF knowledge documents and coverage validation."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "templates" / "schemas" / "okf-knowledge-document.schema.json"
KNOWLEDGE_NODE_SCHEMA_PATH = ROOT / "templates" / "schemas" / "knowledge-node.schema.json"
EVIDENCE_SCHEMA_PATH = ROOT / "templates" / "schemas" / "devspark-evidence.schema.json"
ENTITY_SCHEMA_PATH = ROOT / "templates" / "schemas" / "entity-node.schema.json"


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_schema_accepts_valid_frontmatter_and_rejects_invalid() -> None:
    validator = Draft202012Validator(_schema())
    valid = yaml.safe_load(
        textwrap.dedent(
            """\
            okf_schema_version: "1.0"
            document_id: gate-analyze-001
            document_type: gate-evidence
            feature_id: "001-fixture"
            title: Analyze evidence
            status: complete
            requirement_ids:
              - FR-001
            task_ids:
              - T001
            gate_evidence_ids:
              - analyze-pass-001
            source_artifacts:
              - gates/analyze.md
            updated_at: "2026-08-27"
            """
        )
    )
    assert not list(validator.iter_errors(valid))

    invalid = dict(valid)
    invalid["document_type"] = "metric"
    invalid["requirement_ids"] = ["REQ-1"]
    errors = [error.message for error in validator.iter_errors(invalid)]
    assert any("'metric' is not one of" in message for message in errors)
    assert any("'REQ-1' does not match" in message for message in errors)


def _knowledge_node_validator() -> Draft202012Validator:
    schema = json.loads(KNOWLEDGE_NODE_SCHEMA_PATH.read_text(encoding="utf-8"))
    schema["properties"]["evidence"]["items"] = json.loads(EVIDENCE_SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _frontmatter(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1])


def test_decision_frontmatter_uses_constrains_contract() -> None:
    validator = _knowledge_node_validator()
    valid = yaml.safe_load(
        textwrap.dedent(
            """\
            id: current-truth-test
            type: governance-decision
            title: Current Truth Test
            constrains:
              - command-templates
            last_verified: "2026-09-26"
            evidence:
              - type: test
                ref: tests/test_knowledge_document_contract.py
                verified_by: execution
            """
        )
    )
    assert not list(validator.iter_errors(valid))

    for banned in ("status", "supersedes", "governs", "layer"):
        invalid = dict(valid)
        invalid[banned] = "x"
        assert list(validator.iter_errors(invalid)), f"{banned} must be rejected on decisions"
    missing = dict(valid)
    missing.pop("constrains")
    assert any("'constrains' is a required property" in error.message for error in validator.iter_errors(missing))

    decision_files = sorted((ROOT / ".knowledge" / "governance" / "decisions").glob("*.md"))
    decision_files = [path for path in decision_files if path.name != "README.md"]
    assert decision_files
    for path in decision_files:
        data = _frontmatter(path)
        assert data["id"] == path.stem, f"{path.name} must be keyed by topic"
        assert not list(validator.iter_errors(data)), f"{path.name} decision frontmatter must match schema"


def test_entity_nodes_and_layer_documents_match_schemas() -> None:
    entity_schema = json.loads(ENTITY_SCHEMA_PATH.read_text(encoding="utf-8"))
    entity_schema["properties"]["evidence"]["items"] = json.loads(EVIDENCE_SCHEMA_PATH.read_text(encoding="utf-8"))
    entity_validator = Draft202012Validator(entity_schema)
    layer_validator = _knowledge_node_validator()

    entity_files = sorted((ROOT / ".knowledge" / "entities").glob("*/_entity.yaml"))
    assert entity_files
    for path in entity_files:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["id"] == path.parent.name
        assert not list(entity_validator.iter_errors(data)), f"{path} must match entity-node schema"
        assert not (path.parent / "_derived.yaml").exists(), "constrained_by is hand-authored in _entity.yaml"
        for layer in sorted(path.parent.glob("*.md")):
            assert not list(layer_validator.iter_errors(_frontmatter(layer))), f"{layer} must match knowledge-node schema"

    lifecycle_entity = {"id": "x", "name": "X", "kind": "knowledge-model", "summary": "x", "lifecycle": "current",
                        "evidence": [{"type": "test", "ref": "tests", "verified_by": "execution"}]}
    assert list(entity_validator.iter_errors(lifecycle_entity)), "lifecycle is banned on entity nodes"


def test_ontology_generator_outputs_are_current() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/build_knowledge_index.py", "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not list((ROOT / ".knowledge" / "ontology").glob("*.generated.md"))


def test_packaged_ontology_generator_uses_consumer_root_and_ignores_scaffold_readme(tmp_path: Path) -> None:
    """Exercise the layout produced by release packages, not only the source checkout."""
    consumer = tmp_path / "consumer"
    script = consumer / ".devspark" / "scripts" / "build_knowledge_index.py"
    script.parent.mkdir(parents=True)
    shutil.copy(ROOT / "scripts" / "build_knowledge_index.py", script)
    (consumer / ".knowledge" / "entities").mkdir(parents=True)
    decisions = consumer / ".knowledge" / "governance" / "decisions"
    decisions.mkdir(parents=True)
    (decisions / "README.md").write_text(
        "# Decisions\n\nThis file documents the decision directory.\n", encoding="utf-8"
    )
    (consumer / ".knowledge" / "ontology").mkdir(parents=True)

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=consumer,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 decisions" in result.stdout
    assert (consumer / ".knowledge" / "ontology" / "coverage.json").exists()
    assert (consumer / ".knowledge" / "ontology" / "index.json").exists()
    assert not (consumer / ".devspark" / ".knowledge").exists()


def test_lifecycle_json_contracts_remain_token_stable() -> None:
    bash_create = _read("scripts/bash/create-new-feature.sh")
    ps_create = _read("scripts/powershell/create-new-feature.ps1")
    bash_plan = _read("scripts/bash/setup-plan.sh")
    ps_plan = _read("scripts/powershell/setup-plan.ps1")

    assert 'printf \'{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_NUM":"%s"}\\n\'' in bash_create
    assert "BRANCH_NAME = $branchName" in ps_create
    assert "SPEC_FILE = $specFile" in ps_create
    assert "FEATURE_NUM = $featureNum" in ps_create
    assert "HAS_GIT = $hasGit" in ps_create

    assert 'printf \'{"FEATURE_SPEC":"%s","IMPL_PLAN":"%s","SPECS_DIR":"%s","BRANCH":"%s","HAS_GIT":"%s"}\\n\'' in bash_plan
    for token in ("FEATURE_SPEC", "IMPL_PLAN", "SPECS_DIR", "BRANCH", "HAS_GIT"):
        assert token in ps_plan


def test_lifecycle_scripts_dual_write_knowledge_without_json_mutation() -> None:
    bash_common = _read("scripts/bash/common.sh")
    ps_common = _read("scripts/powershell/common.ps1")
    bash_create = _read("scripts/bash/create-new-feature.sh")
    ps_create = _read("scripts/powershell/create-new-feature.ps1")
    bash_plan = _read("scripts/bash/setup-plan.sh")
    ps_plan = _read("scripts/powershell/setup-plan.ps1")

    assert 'updated_at: "$updated_at"' in bash_common
    assert 'updated_at: "$updatedAt"' in ps_common
    assert "write_okf_knowledge_document" in bash_create
    assert "Write-OkfKnowledgeDocument" in ps_create
    assert "write_okf_knowledge_document" in bash_plan
    assert "Write-OkfKnowledgeDocument" in ps_plan


def test_release_packagers_include_knowledge_files() -> None:
    bash_packager = _read(".github/workflows/scripts/create-release-packages.sh")
    ps_packager = _read(".github/workflows/scripts/create-release-packages.ps1")

    for text in (bash_packager, ps_packager):
        assert "templates" in text
        assert "templates[/\\\\]commands" in text or "templates/commands/*" in text
        assert "templates[/\\\\]schemas" not in text and "templates/schemas" not in text
