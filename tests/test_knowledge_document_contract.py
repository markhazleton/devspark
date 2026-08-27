"""Contract tests for OKF knowledge documents and coverage validation."""

from __future__ import annotations

import json
import importlib.util
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
SCHEMA_PATH = ROOT / "templates" / "schemas" / "okf-knowledge-document.schema.json"

knowledge_spec = importlib.util.spec_from_file_location(
    "devspark_cli_knowledge",
    str(SRC / "devspark_cli" / "_knowledge.py"),
)
knowledge_module = importlib.util.module_from_spec(knowledge_spec)
sys.modules["devspark_cli_knowledge"] = knowledge_module
assert knowledge_spec.loader is not None
knowledge_spec.loader.exec_module(knowledge_module)

extract_frontmatter = knowledge_module.extract_frontmatter
validate_knowledge_coverage = knowledge_module.validate_knowledge_coverage


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _write_feature(root: Path, *, with_knowledge: bool = True, complete: bool = True) -> Path:
    feature = root / ".documentation" / "specs" / "001-fixture"
    (feature / "gates").mkdir(parents=True)
    (feature / "knowledge").mkdir(parents=True, exist_ok=True)
    (feature / "spec.md").write_text(
        "# Spec\n\n## Functional Requirements\n\n- **FR-001**: The system MUST do the thing.\n",
        encoding="utf-8",
    )
    (feature / "tasks.md").write_text(
        "# Tasks\n\n- [ ] T001 [US1] Implement FR-001 behavior.\n",
        encoding="utf-8",
    )
    (feature / "gates" / "analyze.md").write_text("gate: analyze\nstatus: pass\n", encoding="utf-8")
    if not with_knowledge:
        shutil.rmtree(feature / "knowledge")
        return feature

    evidence = "\n  - analyze-pass-001" if complete else "\n  []"
    (feature / "knowledge" / "fr-001.md").write_text(
        f"""---
okf_schema_version: "1.0"
document_id: fr-001
document_type: requirement
feature_id: "001-fixture"
title: Fixture requirement
status: active
requirement_ids:
  - FR-001
task_ids:
  - T001
gate_evidence_ids:{evidence}
source_artifacts:
  - spec.md
  - tasks.md
updated_at: "2026-08-27"
---

Fixture traceability.
""",
        encoding="utf-8",
    )
    return feature


def _bash_path(path: Path) -> str:
    if sys.platform == "win32":
        resolved = path.resolve()
        drive = resolved.drive.rstrip(":").lower()
        rest = resolved.as_posix().split(":", 1)[1]
        return f"/mnt/{drive}{rest}"
    return str(path)


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


def test_extract_frontmatter_accepts_crlf(tmp_path: Path) -> None:
    path = tmp_path / "doc.md"
    path.write_text(
        "---\r\nokf_schema_version: \"1.0\"\r\ndocument_id: doc\r\ndocument_type: decision\r\n"
        "feature_id: \"001-fixture\"\r\ntitle: Doc\r\nstatus: active\r\nupdated_at: \"2026-08-27\"\r\n---\r\nBody\r\n",
        encoding="utf-8",
    )
    assert extract_frontmatter(path)["document_id"] == "doc"


def test_coverage_core_skips_when_knowledge_absent(tmp_path: Path) -> None:
    feature = _write_feature(tmp_path, with_knowledge=False)
    report = validate_knowledge_coverage(feature)
    assert report["status"] == "skipped"
    assert "coverage validation skipped" in report["messages"][0]


def test_coverage_core_reports_complete_fixture(tmp_path: Path) -> None:
    feature = _write_feature(tmp_path, complete=True)
    report = validate_knowledge_coverage(feature)
    assert report["status"] == "ok"
    assert report["requirements_total"] == 1
    assert report["tasks_total"] == 1
    assert report["gate_evidence_total"] == 1
    assert report["requirements_covered"] == 1
    assert report["requirements_uncovered"] == []


def test_coverage_core_warns_for_uncovered_fixture(tmp_path: Path) -> None:
    feature = _write_feature(tmp_path, complete=False)
    report = validate_knowledge_coverage(feature)
    assert report["status"] == "warn"
    assert report["requirements_uncovered"] == ["FR-001"]
    assert any("no gate evidence" in message for message in report["messages"])


def test_bash_wrapper_outputs_json_when_available(tmp_path: Path) -> None:
    if shutil.which("bash") is None:
        pytest.skip("bash is not available")
    feature = _write_feature(tmp_path, complete=True)
    result = subprocess.run(
        [
            "bash",
            _bash_path(ROOT / "scripts" / "bash" / "validate-knowledge-coverage.sh"),
            "--feature-dir",
            _bash_path(feature),
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert json.loads(result.stdout)["status"] == "ok"


def test_powershell_wrapper_outputs_json_when_available(tmp_path: Path) -> None:
    if shutil.which("pwsh") is None:
        pytest.skip("pwsh is not available")
    feature = _write_feature(tmp_path, complete=True)
    result = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(ROOT / "scripts" / "powershell" / "validate-knowledge-coverage.ps1"),
            "-FeatureDir",
            str(feature),
            "-Json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert json.loads(result.stdout)["status"] == "ok"


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


def test_analyze_and_critic_run_fail_soft_coverage_validator() -> None:
    for rel_path in ("templates/commands/analyze.md", "templates/commands/critic.md"):
        text = _read(rel_path)
        assert "validate-knowledge-coverage" in text
        assert "fail-soft" in text
        assert "knowledge/" in text
        assert "clean skip" in text


def test_release_and_upgrade_surfaces_include_knowledge_files() -> None:
    bash_packager = _read(".github/workflows/scripts/create-release-packages.sh")
    ps_packager = _read(".github/workflows/scripts/create-release-packages.ps1")
    upgrade = _read("templates/commands/upgrade.md")

    for text in (bash_packager, ps_packager):
        assert "templates" in text
        assert "templates[/\\\\]commands" in text or "templates/commands/*" in text
        assert "templates[/\\\\]schemas" not in text and "templates/schemas" not in text

    for token in (
        "okf-knowledge-document.schema.json",
        "validate-knowledge-coverage.sh",
        "validate-knowledge-coverage.ps1",
        "command-preamble-contract.md",
        "devspark.verify.md",
        "templates/prompts/atomic/verify.md",
    ):
        assert token in upgrade
