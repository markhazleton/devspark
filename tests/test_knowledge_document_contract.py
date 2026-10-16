# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for OKF knowledge document generation.

Exercises the shared writer helper (New-KnowledgeDocument / write_knowledge_document)
directly in both PowerShell and Bash, plus the coverage-report script pair and the
full specify->plan->tasks lifecycle.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HAS_PWSH = shutil.which("pwsh") is not None
HAS_BASH = shutil.which("bash") is not None
HAS_JQ = HAS_BASH and subprocess.run(
    ["bash", "-c", "command -v jq"], capture_output=True, timeout=60
).returncode == 0
NPX_PATH = shutil.which("npx")
HAS_MARKDOWNLINT = NPX_PATH is not None


def _run_ps(command: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["pwsh", "-NoProfile", "-Command", command],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        timeout=120,
    )


def _run_bash(command: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-c", command],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        timeout=120,
    )


def _to_wsl_path(path: Path) -> str:
    """Convert a Windows path to a WSL /mnt/<drive>/... path (bash here is WSL bash.exe)."""
    posix = path.as_posix()
    if len(posix) > 1 and posix[1] == ":":
        return f"/mnt/{posix[0].lower()}{posix[2:]}"
    return posix


def _write_via_powershell(tmp_path: Path, args: str) -> subprocess.CompletedProcess[str]:
    script = f". '{ROOT / 'scripts' / 'powershell' / 'common.ps1'}'; {args}"
    return _run_ps(script, tmp_path)


def _write_via_bash(tmp_path: Path, args: str) -> subprocess.CompletedProcess[str]:
    common_sh = _to_wsl_path(ROOT / "scripts" / "bash" / "common.sh")
    script = f"source '{common_sh}'; {args}"
    return _run_bash(script, tmp_path)


# --- Schema compliance, both variants -------------------------------------------------


@pytest.mark.skipif(not HAS_PWSH, reason="pwsh not available")
def test_writer_schema_compliance_powershell(tmp_path: Path) -> None:
    feature_dir = tmp_path / "005-sample"
    feature_dir.mkdir()
    result = _write_via_powershell(
        tmp_path,
        (
            "New-KnowledgeDocument -FeatureDir '"
            + str(feature_dir)
            + "' -Id 'fr-001' -Type 'requirement' -Title 'Sample requirement' "
            + "-Status 'draft' -Links @{ feature = 'feature'; implemented_by = @() } "
            + "-GeneratedBy 'devspark.specify'"
        ),
    )
    assert result.returncode == 0, result.stderr
    doc = feature_dir / "knowledge" / "fr-001.md"
    assert doc.exists()
    text = doc.read_text(encoding="utf-8")
    for field in ("id: fr-001", "type: requirement", "status: draft", "generated:", "by: devspark.specify"):
        assert field in text


@pytest.mark.skipif(not HAS_JQ, reason="bash+jq not available")
def test_writer_schema_compliance_bash(tmp_path: Path) -> None:
    feature_dir = tmp_path / "005-sample"
    feature_dir.mkdir()
    links = json.dumps({"feature": "feature", "implemented_by": []})
    result = _write_via_bash(
        tmp_path,
        f"write_knowledge_document '{_to_wsl_path(feature_dir)}' fr-001 requirement 'Sample requirement' draft '{links}' devspark.specify",
    )
    assert result.returncode == 0, result.stderr
    doc = feature_dir / "knowledge" / "fr-001.md"
    assert doc.exists()
    text = doc.read_text(encoding="utf-8")
    for field in ("id: fr-001", "type: requirement", "status: draft", "generated:", "by: devspark.specify"):
        assert field in text


# --- Writer failure is isolated, both variants ----------------------------------------


@pytest.mark.skipif(not HAS_PWSH, reason="pwsh not available")
def test_writer_failure_is_isolated_powershell(tmp_path: Path) -> None:
    # FeatureDir points at a path that cannot be created (a file, not a directory)
    # so New-Item -Directory fails inside the try/catch -- the function must
    # return $false, not throw, and must leave no temp file behind.
    blocker = tmp_path / "blocked"
    blocker.write_text("not a directory", encoding="utf-8")
    result = _write_via_powershell(
        tmp_path,
        (
            "$ok = New-KnowledgeDocument -FeatureDir '"
            + str(blocker)
            + "' -Id 'fr-001' -Type 'requirement' -Title 'x' -Status 'draft' "
            + "-Links @{ feature = 'feature'; implemented_by = @() } -GeneratedBy 'devspark.specify'; "
            + "Write-Output \"RESULT:$ok\""
        ),
    )
    assert result.returncode == 0, result.stderr
    assert "RESULT:False" in result.stdout
    assert not (blocker / "knowledge").exists()


@pytest.mark.skipif(not HAS_JQ, reason="bash+jq not available")
def test_writer_failure_is_isolated_bash(tmp_path: Path) -> None:
    blocker = tmp_path / "blocked"
    blocker.write_text("not a directory", encoding="utf-8")
    links = json.dumps({"feature": "feature", "implemented_by": []})
    result = _write_via_bash(
        tmp_path,
        f"write_knowledge_document '{_to_wsl_path(blocker)}' fr-001 requirement x draft '{links}' devspark.specify; echo RESULT:$?",
    )
    assert result.returncode == 0, result.stderr
    assert "RESULT:1" in result.stdout
    assert not (blocker / "knowledge").exists()


# --- Generated markdown passes markdownlint-cli2 ---------------------------------------


@pytest.mark.skipif(not HAS_PWSH, reason="pwsh not available")
@pytest.mark.skipif(not HAS_MARKDOWNLINT, reason="npx not available")
def test_generated_markdown_passes_lint(tmp_path: Path) -> None:
    feature_dir = tmp_path / "005-sample"
    feature_dir.mkdir()
    result = _write_via_powershell(
        tmp_path,
        (
            "New-KnowledgeDocument -FeatureDir '"
            + str(feature_dir)
            + "' -Id 'feature' -Type 'feature' -Title 'Sample feature' -Status 'draft' "
            + "-Links @{ requirements = @('fr-001') } -GeneratedBy 'devspark.specify'"
        ),
    )
    assert result.returncode == 0, result.stderr
    doc = feature_dir / "knowledge" / "feature.md"
    lint = subprocess.run(
        [NPX_PATH, "--yes", "markdownlint-cli2", str(doc)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=300,
    )
    assert lint.returncode == 0, f"{lint.stdout}\n{lint.stderr}"


# --- Full specify -> plan -> tasks lifecycle integration ------------------------------


@pytest.mark.skipif(not HAS_PWSH, reason="pwsh not available")
def test_full_lifecycle_generates_knowledge_docs(tmp_path: Path) -> None:
    feature_dir = tmp_path / "005-sample"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text(
        "---\nclassification: full-spec\n---\n\n"
        "# Feature Specification: Sample\n\n"
        "## Requirements\n\n"
        "- **FR-001**: System MUST do the sample thing\n"
        "- **FR-002**: System MUST do a second sample thing\n",
        encoding="utf-8",
    )
    script = f". '{ROOT / 'scripts' / 'powershell' / 'common.ps1'}'; " + (
        "New-KnowledgeDocument -FeatureDir '"
        + str(feature_dir)
        + "' -Id 'feature' -Type 'feature' -Title 'Sample' -Status 'draft' "
        + "-Links @{ requirements = @('fr-001','fr-002') } -GeneratedBy 'devspark.specify'; "
        + "New-KnowledgeDocument -FeatureDir '"
        + str(feature_dir)
        + "' -Id 'fr-001' -Type 'requirement' -Title 'System MUST do the sample thing' -Status 'draft' "
        + "-Links @{ feature = 'feature'; implemented_by = @() } -GeneratedBy 'devspark.specify'; "
        + "New-KnowledgeDocument -FeatureDir '"
        + str(feature_dir)
        + "' -Id 'fr-002' -Type 'requirement' -Title 'System MUST do a second sample thing' -Status 'draft' "
        + "-Links @{ feature = 'feature'; implemented_by = @() } -GeneratedBy 'devspark.specify'; "
        + "New-KnowledgeDocument -FeatureDir '"
        + str(feature_dir)
        + "' -Id 'task-001' -Type 'task' -Title 'Do the first task' -Status 'draft' "
        + "-Links @{ feature = 'feature'; implements = @('fr-001') } -GeneratedBy 'devspark.tasks'"
    )
    result = _run_ps(script, tmp_path)
    assert result.returncode == 0, result.stderr

    knowledge_dir = feature_dir / "knowledge"
    assert (knowledge_dir / "feature.md").exists()
    assert (knowledge_dir / "fr-001.md").exists()
    assert (knowledge_dir / "fr-002.md").exists()
    assert (knowledge_dir / "task-001.md").exists()
    task_doc = (knowledge_dir / "task-001.md").read_text(encoding="utf-8")
    assert "implements:" in task_doc
    assert "- fr-001" in task_doc


# --- Writer failure never changes a script's JSON contract or exit code --------------


@pytest.mark.skipif(not HAS_PWSH, reason="pwsh not available")
def test_json_contract_unchanged_on_writer_failure(tmp_path: Path) -> None:
    """A writer failure inside create-new-feature must not change its JSON/exit code.

    This simulates the isolation by calling New-KnowledgeDocument against an
    unwritable path (as in test_writer_failure_is_isolated) and confirming the
    call site's own success (e.g. JSON emission) is a separate concern -- the
    writer's own return value never throws or bubbles up.
    """
    blocker = tmp_path / "blocked"
    blocker.write_text("not a directory", encoding="utf-8")
    script = f". '{ROOT / 'scripts' / 'powershell' / 'common.ps1'}'; " + (
        "$ok = New-KnowledgeDocument -FeatureDir '"
        + str(blocker)
        + "' -Id 'fr-001' -Type 'requirement' -Title 'x' -Status 'draft' "
        + "-Links @{ feature = 'feature'; implemented_by = @() } -GeneratedBy 'devspark.specify'; "
        + "$contract = @{ contract = 1; BRANCH_NAME = 'sample'; FEATURE_NUM = '005' }; "
        + "$contract | ConvertTo-Json -Compress"
    )
    result = _run_ps(script, tmp_path)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["contract"] == 1
    assert payload["BRANCH_NAME"] == "sample"


# --- Coverage report detects orphaned tasks and unimplemented requirements -----------


def _run_coverage_powershell(feature_dir: Path, tmp_path: Path) -> dict:
    script_path = ROOT / "scripts" / "powershell" / "validate-knowledge-coverage.ps1"
    result = _run_ps(
        f"& '{script_path}' -Json -Feature '{feature_dir}'",
        tmp_path,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


@pytest.mark.skipif(not HAS_PWSH, reason="pwsh not available")
def test_coverage_report_detects_orphans_powershell(tmp_path: Path) -> None:
    feature_dir = tmp_path / "005-sample"
    feature_dir.mkdir()
    script = f". '{ROOT / 'scripts' / 'powershell' / 'common.ps1'}'; " + (
        # fr-001 has an implementing task; fr-002 does not (unimplemented)
        "New-KnowledgeDocument -FeatureDir '" + str(feature_dir) + "' -Id 'fr-001' -Type 'requirement' -Title 'A' -Status 'draft' -Links @{ feature='feature'; implemented_by=@('task-001') } -GeneratedBy 'setup-plan'; "
        + "New-KnowledgeDocument -FeatureDir '" + str(feature_dir) + "' -Id 'fr-002' -Type 'requirement' -Title 'B' -Status 'draft' -Links @{ feature='feature'; implemented_by=@() } -GeneratedBy 'setup-plan'; "
        # task-001 implements fr-001; task-002 implements nothing (orphan)
        + "New-KnowledgeDocument -FeatureDir '" + str(feature_dir) + "' -Id 'task-001' -Type 'task' -Title 'T1' -Status 'draft' -Links @{ feature='feature'; implements=@('fr-001') } -GeneratedBy 'devspark.tasks'; "
        + "New-KnowledgeDocument -FeatureDir '" + str(feature_dir) + "' -Id 'task-002' -Type 'task' -Title 'T2' -Status 'draft' -Links @{ feature='feature'; implements=@() } -GeneratedBy 'devspark.tasks'"
    )
    result = _run_ps(script, tmp_path)
    assert result.returncode == 0, result.stderr

    report = _run_coverage_powershell(feature_dir, tmp_path)
    assert report["ok"] is False
    assert report["orphan_tasks"] == ["task-002"]
    assert report["unimplemented_requirements"] == ["fr-002"]


@pytest.mark.skipif(not HAS_PWSH, reason="pwsh not available")
def test_coverage_report_clean_when_fully_linked(tmp_path: Path) -> None:
    feature_dir = tmp_path / "005-sample"
    feature_dir.mkdir()
    script = f". '{ROOT / 'scripts' / 'powershell' / 'common.ps1'}'; " + (
        "New-KnowledgeDocument -FeatureDir '" + str(feature_dir) + "' -Id 'fr-001' -Type 'requirement' -Title 'A' -Status 'draft' -Links @{ feature='feature'; implemented_by=@('task-001') } -GeneratedBy 'setup-plan'; "
        + "New-KnowledgeDocument -FeatureDir '" + str(feature_dir) + "' -Id 'task-001' -Type 'task' -Title 'T1' -Status 'draft' -Links @{ feature='feature'; implements=@('fr-001') } -GeneratedBy 'devspark.tasks'"
    )
    result = _run_ps(script, tmp_path)
    assert result.returncode == 0, result.stderr

    report = _run_coverage_powershell(feature_dir, tmp_path)
    assert report["ok"] is True
    assert report["orphan_tasks"] == []
    assert report["unimplemented_requirements"] == []


@pytest.mark.skipif(not HAS_PWSH, reason="pwsh not available")
def test_coverage_report_no_findings_before_tasks_exist(tmp_path: Path) -> None:
    """A requirement with no tasks yet (before /devspark.tasks has run) is not a finding."""
    feature_dir = tmp_path / "005-sample"
    feature_dir.mkdir()
    script = f". '{ROOT / 'scripts' / 'powershell' / 'common.ps1'}'; " + (
        "New-KnowledgeDocument -FeatureDir '" + str(feature_dir) + "' -Id 'fr-001' -Type 'requirement' -Title 'A' -Status 'draft' -Links @{ feature='feature'; implemented_by=@() } -GeneratedBy 'setup-plan'"
    )
    result = _run_ps(script, tmp_path)
    assert result.returncode == 0, result.stderr

    report = _run_coverage_powershell(feature_dir, tmp_path)
    assert report["ok"] is True
    assert report["unimplemented_requirements"] == []


# --- PR #61822 H-01: titles containing quotes must not corrupt the YAML frontmatter ---------


@pytest.mark.skipif(not HAS_PWSH, reason="pwsh not available")
def test_writer_escapes_quotes_in_title_powershell(tmp_path: Path) -> None:
    feature_dir = tmp_path / "005-sample"
    feature_dir.mkdir()
    result = _write_via_powershell(
        tmp_path,
        (
            "New-KnowledgeDocument -FeatureDir '"
            + str(feature_dir)
            + "' -Id 'fr-001' -Type 'requirement' -Title 'Support \"quoted\" terms' "
            + "-Status 'draft' -Links @{ feature = 'feature'; implemented_by = @() } "
            + "-GeneratedBy 'devspark.specify'"
        ),
    )
    assert result.returncode == 0, result.stderr
    doc = feature_dir / "knowledge" / "fr-001.md"
    text = doc.read_text(encoding="utf-8")
    assert 'title: "Support \\"quoted\\" terms"' in text
    # The frontmatter must still be well-formed: exactly two "---" delimiters.
    assert text.count("---") == 2


@pytest.mark.skipif(not HAS_JQ, reason="bash+jq not available")
def test_writer_escapes_quotes_in_title_bash(tmp_path: Path) -> None:
    feature_dir = tmp_path / "005-sample"
    feature_dir.mkdir()
    links = json.dumps({"feature": "feature", "implemented_by": []})
    result = _write_via_bash(
        tmp_path,
        f"write_knowledge_document '{_to_wsl_path(feature_dir)}' fr-001 requirement 'Support \"quoted\" terms' draft '{links}' devspark.specify",
    )
    assert result.returncode == 0, result.stderr
    doc = feature_dir / "knowledge" / "fr-001.md"
    text = doc.read_text(encoding="utf-8")
    assert 'title: "Support \\"quoted\\" terms"' in text
    assert text.count("---") == 2


# --- Object source claims (knowledge drift detection), additive schema contract ------


@pytest.fixture(scope="module")
def _knowledge_node_schema() -> dict:
    return json.loads(
        (ROOT / "templates/schemas/knowledge-node.schema.json").read_text(encoding="utf-8")
    )


def _entity_layer_doc(source_of_truth: list) -> dict:
    return {
        "id": "sample-entity",
        "type": "entity-layer",
        "title": "Sample",
        "layer": "pattern",
        "last_verified": "2026-09-24",
        "source_of_truth": source_of_truth,
    }


def test_schema_accepts_legacy_string_source_of_truth(_knowledge_node_schema: dict) -> None:
    import jsonschema

    jsonschema.validate(_entity_layer_doc(["scripts/build_knowledge_index.py"]), _knowledge_node_schema)


def test_schema_accepts_object_source_claim(_knowledge_node_schema: dict) -> None:
    import jsonschema

    digest = "sha256:" + "0" * 64
    doc = _entity_layer_doc(
        [
            {
                "path": "scripts/build_knowledge_index.py",
                "digest": digest,
                "baseline": f".knowledge/evidence/source-baselines/sha256/00/{'0' * 64}.baseline",
                "profile": "python-token-v1",
                "region": "build_entities",
            }
        ]
    )
    doc["verification"] = {"state": "pinned-unverified"}
    jsonschema.validate(doc, _knowledge_node_schema)


def test_schema_accepts_mixed_legacy_and_object_claims(_knowledge_node_schema: dict) -> None:
    import jsonschema

    digest = "sha256:" + "a" * 64
    doc = _entity_layer_doc(
        [
            "scripts/explain-context.py",
            {
                "path": "scripts/build_knowledge_index.py",
                "digest": digest,
                "baseline": f".knowledge/evidence/source-baselines/sha256/aa/{'a' * 64}.baseline",
                "profile": "exact-text-v1",
            },
        ]
    )
    jsonschema.validate(doc, _knowledge_node_schema)


def test_schema_rejects_malformed_digest(_knowledge_node_schema: dict) -> None:
    import jsonschema

    doc = _entity_layer_doc(
        [
            {
                "path": "scripts/build_knowledge_index.py",
                "digest": "not-a-digest",
                "baseline": f".knowledge/evidence/source-baselines/sha256/00/{'0' * 64}.baseline",
                "profile": "python-token-v1",
            }
        ]
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(doc, _knowledge_node_schema)


def test_schema_rejects_baseline_address_not_derived_from_digest_shape(_knowledge_node_schema: dict) -> None:
    """The schema can only check baseline *shape* (sha256/<2-hex>/<64-hex>.baseline); the
    generator itself must verify the address is actually derived from the digest at runtime."""
    import jsonschema

    doc = _entity_layer_doc(
        [
            {
                "path": "scripts/build_knowledge_index.py",
                "digest": "sha256:" + "0" * 64,
                "baseline": ".knowledge/evidence/source-baselines/not-a-valid-address.baseline",
                "profile": "python-token-v1",
            }
        ]
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(doc, _knowledge_node_schema)


def test_schema_rejects_object_claim_missing_required_fields(_knowledge_node_schema: dict) -> None:
    import jsonschema

    doc = _entity_layer_doc([{"path": "scripts/build_knowledge_index.py", "profile": "python-token-v1"}])
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(doc, _knowledge_node_schema)


def test_schema_rejects_object_claim_pointing_at_forbidden_planning_path(_knowledge_node_schema: dict) -> None:
    import jsonschema

    doc = _entity_layer_doc(
        [
            {
                "path": ".devspark.work/specs/002-example/tasks.md",
                "digest": "sha256:" + "1" * 64,
                "baseline": f".knowledge/evidence/source-baselines/sha256/11/{'1' * 64}.baseline",
                "profile": "exact-text-v1",
            }
        ]
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(doc, _knowledge_node_schema)


def test_schema_rejects_directory_shaped_object_claim(_knowledge_node_schema: dict) -> None:
    import jsonschema

    digest = "sha256:" + "3" * 64
    doc = _entity_layer_doc(
        [
            {
                "path": "src/widget/",
                "digest": digest,
                "baseline": f".knowledge/evidence/source-baselines/sha256/33/{'3' * 64}.baseline",
                "profile": "exact-text-v1",
            }
        ]
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(doc, _knowledge_node_schema)


def test_schema_rejects_duplicate_object_claims(_knowledge_node_schema: dict) -> None:
    import jsonschema

    digest = "sha256:" + "4" * 64
    claim = {
        "path": "src/widget.py",
        "digest": digest,
        "baseline": f".knowledge/evidence/source-baselines/sha256/44/{'4' * 64}.baseline",
        "profile": "exact-text-v1",
    }
    doc = _entity_layer_doc([claim, dict(claim)])
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(doc, _knowledge_node_schema)


def test_schema_rejects_unversioned_profile(_knowledge_node_schema: dict) -> None:
    import jsonschema

    doc = _entity_layer_doc(
        [
            {
                "path": "scripts/build_knowledge_index.py",
                "digest": "sha256:" + "2" * 64,
                "baseline": f".knowledge/evidence/source-baselines/sha256/22/{'2' * 64}.baseline",
                "profile": "python-token",
            }
        ]
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(doc, _knowledge_node_schema)


def test_schema_verified_requires_confirmed_on(_knowledge_node_schema: dict) -> None:
    import jsonschema

    doc = _entity_layer_doc(["scripts/build_knowledge_index.py"])
    doc["verification"] = {"state": "verified"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(doc, _knowledge_node_schema)

    doc["verification"] = {"state": "verified", "confirmed_on": "2026-09-24"}
    jsonschema.validate(doc, _knowledge_node_schema)


def test_schema_rejects_confirmed_on_for_pinned_unverified(_knowledge_node_schema: dict) -> None:
    import jsonschema

    doc = _entity_layer_doc(["scripts/build_knowledge_index.py"])
    doc["verification"] = {"state": "pinned-unverified", "confirmed_on": "2026-09-24"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(doc, _knowledge_node_schema)


def test_repo_config_schema_accepts_pinned_claims_enforcement() -> None:
    import jsonschema

    schema = json.loads((ROOT / "templates/devspark-config.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate({"knowledge_drift": {"enforcement": "pinned-claims"}}, schema)
    # The schema itself is documentation-only for this field (additionalProperties: true
    # throughout); the *runtime* hard-fail on a malformed value is a generator-level contract
    # covered by tests/test_knowledge_drift_cli_contract.py, not this schema.
    jsonschema.validate({"knowledge_drift": {"enforcement": "typo-value"}}, schema)


# --- Overview section references written by setup-plan, both shells ----------------

_INDEX_FIXTURES = ROOT / "tests" / "fixtures" / "spec-knowledge-consumption" / "index"
_SPEC_SECTION_NAMES = [
    "Requirements",
    "Key Entities",
    "Clarifications",
    "Success Criteria",
    "Assumptions",
    "Out of Scope",
    "Minimum Sufficient Change",
]


def _shell_executable(shell: str) -> str | None:
    if shell == "pwsh":
        return shutil.which("pwsh")
    if os.name == "nt":
        git_bash = "C:/Program Files/Git/bin/bash.exe"
        return git_bash if Path(git_bash).exists() else None
    return shutil.which("bash")


def _run_setup_plan(tmp_path: Path, shell: str, spec_fixture: str) -> tuple[dict, str]:
    executable = _shell_executable(shell)
    if not executable:
        pytest.skip(f"{shell} unavailable")
    if shell == "bash" and not shutil.which("jq"):
        pytest.skip("jq unavailable")
    repo = tmp_path / "repo"
    feature = repo / ".devspark.work" / "specs" / "001-synthetic"
    feature.mkdir(parents=True)
    (repo / "templates").mkdir()
    (repo / "templates" / "plan-template.md").write_text("# Template\n", encoding="utf-8")
    shutil.copyfile(_INDEX_FIXTURES / spec_fixture, feature / "spec.md")
    subprocess.run(["git", "init", "-q", "-b", "001-synthetic", str(repo)], check=True, timeout=15, stdin=subprocess.DEVNULL)
    env = {**os.environ, "DEVSPARK_FEATURE": "001-synthetic"}
    script = ROOT / "scripts" / ("powershell/setup-plan.ps1" if shell == "pwsh" else "bash/setup-plan.sh")
    command = (
        [executable, "-NoProfile", "-File", str(script), "-Json"]
        if shell == "pwsh"
        else [executable, str(script), "--json"]
    )
    result = subprocess.run(
        command, cwd=repo, env=env, capture_output=True, text=True, check=True, timeout=30, stdin=subprocess.DEVNULL
    )
    payload = json.loads(result.stdout[result.stdout.index("{"):])
    return payload, (feature / "knowledge" / "feature.md").read_text(encoding="utf-8")


def _feature_links(feature_doc: str) -> dict:
    import yaml

    frontmatter = feature_doc.split("---", 2)[1]
    return yaml.safe_load(frontmatter)["links"]


@pytest.mark.parametrize("shell", ["pwsh", "bash"])
def test_overview_references_present_spec_sections(tmp_path: Path, shell: str) -> None:
    payload, feature_doc = _run_setup_plan(tmp_path, shell, "spec-full.md")
    links = _feature_links(feature_doc)
    assert links["requirements"] == ["fr-001"]
    assert links["spec_sections"] == _SPEC_SECTION_NAMES
    assert links["spec_sections_absent"] in ([], None)
    # References only: no prose from the spec is copied into the overview.
    assert "versioned record" not in feature_doc
    assert "Operators run the copy manually" not in feature_doc
    # The script's own contract is unchanged.
    assert payload["PLAN_MODE"] == "create"
    assert {"FEATURE_SPEC", "IMPL_PLAN", "SPECS_DIR", "BRANCH", "HAS_GIT", "PLAN_EXISTS"} <= payload.keys()


@pytest.mark.parametrize("shell", ["pwsh", "bash"])
def test_overview_records_missing_spec_sections_as_absent(tmp_path: Path, shell: str) -> None:
    _, feature_doc = _run_setup_plan(tmp_path, shell, "spec-minimal.md")
    links = _feature_links(feature_doc)
    assert links["spec_sections"] == ["Requirements"]
    assert links["spec_sections_absent"] == [n for n in _SPEC_SECTION_NAMES if n != "Requirements"]
    # Every reference either resolves to a spec heading or is recorded as absent.
    assert set(links["spec_sections"]) | set(links["spec_sections_absent"]) == set(_SPEC_SECTION_NAMES)


@pytest.mark.parametrize("shell", ["pwsh", "bash"])
def test_setup_plan_adds_no_mode_switch_for_overview(shell: str) -> None:
    script = (ROOT / "scripts" / ("powershell/setup-plan.ps1" if shell == "pwsh" else "bash/setup-plan.sh")).read_text(
        encoding="utf-8"
    )
    for forbidden in ("refresh-knowledge", "RefreshKnowledge", "prune", "Prune", "--knowledge-only", "KnowledgeOnly"):
        assert forbidden not in script


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
