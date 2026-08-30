"""Contract tests for OKF knowledge documents and coverage validation."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "templates" / "schemas" / "okf-knowledge-document.schema.json"


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
