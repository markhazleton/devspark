# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for `scripts/knowledge-integrity.py` (DevSpark 7.6 Knowledge Integrity).

Each test pins one integrity check against a synthetic repository, plus the shared finding
schema's determinism guarantee: repeated scans of an unchanged problem must produce the same
`finding_id`, never a new arbitrary one.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
INTEGRITY_SCRIPT = ROOT / "scripts" / "knowledge-integrity.py"

from knowledge_findings import validate_finding  # noqa: E402


def _write_doc(repo: Path, relpath: str, *, node_type: str = "architecture", extra: dict | None = None, body: str = "Body text.\n") -> Path:
    doc = repo / relpath
    doc.parent.mkdir(parents=True, exist_ok=True)
    metadata: dict = {"id": doc.stem, "type": node_type, "title": doc.stem}
    if extra:
        metadata.update(extra)
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
    doc.write_text(f"---\n{frontmatter}---\n\n{body}", encoding="utf-8")
    return doc


def _run(repo: Path) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, str(INTEGRITY_SCRIPT), "--repo-root", str(repo)],
        text=True,
        capture_output=True,
        timeout=60,
    )
    return result.returncode, json.loads(result.stdout)


def _findings_by_category(payload: dict, category: str) -> list[dict]:
    return [f for f in payload["FINDINGS"] if f["category"] == category]


def test_engine_agreement_no_divergence_when_identical(tmp_path: Path) -> None:
    _write_doc(tmp_path, ".knowledge/architecture/one.md")
    secondary = tmp_path / ".devspark/scripts/build_knowledge_index.py"
    secondary.parent.mkdir(parents=True)
    # Byte-identical to the canonical engine: same implementation installed twice, not a divergence.
    secondary.write_bytes((ROOT / "scripts" / "build_knowledge_index.py").read_bytes())

    _code, payload = _run(tmp_path)
    assert _findings_by_category(payload, "engine-divergence") == []


def test_engine_divergence_detected(tmp_path: Path) -> None:
    _write_doc(tmp_path, ".knowledge/architecture/one.md")
    secondary = tmp_path / ".devspark/scripts/build_knowledge_index.py"
    secondary.parent.mkdir(parents=True)
    secondary.write_text(
        "def build_index(root):\n"
        "    return {'generated': {'by': 'fake'}, 'nodes': [], 'edges': [], 'entities': [],"
        " 'dangling_references': [], 'roots': [], 'stale_entities': []}\n",
        encoding="utf-8",
    )

    code, payload = _run(tmp_path)
    divergence = _findings_by_category(payload, "engine-divergence")
    assert len(divergence) == 1
    assert divergence[0]["severity"] == "high"
    assert code == 1  # engine-divergence is a hard structural failure


def test_stale_legacy_repo_root_engine_detected_when_running_from_installed_location(tmp_path: Path) -> None:
    # Reproduces the production failure mode: a repo carries a pre-`.devspark/` legacy copy of
    # the engine at its repository root, and the validator runs from its INSTALLED location
    # (`.devspark/scripts/`), which must still detect the stale root copy as a divergence.
    _write_doc(tmp_path, ".knowledge/architecture/one.md")
    installed_dir = tmp_path / ".devspark/scripts"
    installed_dir.mkdir(parents=True)
    for name in ("knowledge-integrity.py", "knowledge_findings.py", "build_knowledge_index.py"):
        (installed_dir / name).write_bytes((ROOT / "scripts" / name).read_bytes())

    legacy_root_copy = tmp_path / "scripts" / "build_knowledge_index.py"
    legacy_root_copy.parent.mkdir(parents=True)
    legacy_root_copy.write_text(
        "def build_index(root):\n"
        "    return {'generated': {'by': 'stale-legacy-copy'}, 'nodes': [], 'edges': [], 'entities': [],"
        " 'dangling_references': [], 'roots': [], 'stale_entities': []}\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(installed_dir / "knowledge-integrity.py"), "--repo-root", str(tmp_path)],
        text=True, capture_output=True, timeout=60,
    )
    payload = json.loads(result.stdout)
    divergence = _findings_by_category(payload, "engine-divergence")
    assert len(divergence) == 1
    assert divergence[0]["subject"] == "scripts/build_knowledge_index.py"
    assert result.returncode == 1


def _write_entity(tmp_path: Path, entity_id: str, *, source_of_truth: list[str]) -> None:
    entity_dir = tmp_path / ".knowledge/entities" / entity_id
    entity_dir.mkdir(parents=True)
    (entity_dir / "_entity.yaml").write_text(
        yaml.safe_dump({"id": entity_id, "type": "subsystem", "owner": "team-x"}, sort_keys=False),
        encoding="utf-8",
    )
    metadata = {
        "id": f"{entity_id}-architecture",
        "layer": "architecture",
        "title": entity_id,
        "source_of_truth": source_of_truth,
        "last_verified": "2026-01-01",
    }
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
    (entity_dir / "architecture.md").write_text(f"---\n{frontmatter}---\n\nBody.\n", encoding="utf-8")


def test_broken_mapping_reported_as_finding(tmp_path: Path) -> None:
    _write_entity(tmp_path, "widget", source_of_truth=["src/does_not_exist.py"])

    code, payload = _run(tmp_path)
    assert payload["index_build_ok"] is False
    missing = _findings_by_category(payload, "missing-mapping")
    assert len(missing) == 1
    assert missing[0]["evidence"][0]["type"] == "build-error"
    assert code == 1


def test_overriding_a_directory_default_is_not_a_finding(tmp_path: Path) -> None:
    """`governance/**` is a glob, so it states a default for the directory. A document declaring
    a different role is exercising the precedence the contract grants it. Reporting that forever
    would be a finding nobody can act on."""
    _write_doc(tmp_path, ".knowledge/governance/one.md", node_type="architecture")

    _code, payload = _run(tmp_path)
    assert _findings_by_category(payload, "taxonomy-mismatch") == []


def test_taxonomy_mismatch_detected(tmp_path: Path) -> None:
    """An exact-path mapping is a deliberate statement about one file. A document contradicting
    it means two deliberate statements disagree, which is a real conflict someone must settle."""
    _write_doc(tmp_path, ".knowledge/governance/one.md", node_type="architecture")
    (tmp_path / ".knowledge" / "taxonomy-registry.json").write_text(
        json.dumps({"mappings": [{"pathPattern": ".knowledge/governance/one.md", "nodeType": "governance"}]}),
        encoding="utf-8",
    )

    _code, payload = _run(tmp_path)
    mismatch = _findings_by_category(payload, "taxonomy-mismatch")
    assert len(mismatch) == 1
    assert mismatch[0]["evidence"][1]["value"] == "architecture"
    assert mismatch[0]["evidence"][2]["value"] == "governance"


def test_unreachable_knowledge_root_detected(tmp_path: Path) -> None:
    _write_doc(tmp_path, ".knowledge/architecture/one.md")
    nested = tmp_path / "app-a" / ".knowledge"
    nested.mkdir(parents=True)
    (nested / "placeholder.md").write_text("not indexed by the top-level root\n", encoding="utf-8")

    _code, payload = _run(tmp_path)
    unreachable = _findings_by_category(payload, "unreachable-knowledge-root")
    assert any(f["subject"] == "app-a/.knowledge" for f in unreachable)


def test_example_project_knowledge_root_is_not_unreachable(tmp_path: Path) -> None:
    _write_doc(tmp_path, ".knowledge/architecture/one.md")
    example = tmp_path / "examples" / "sample-app" / ".knowledge" / "governance"
    example.mkdir(parents=True)
    (example / "constitution.md").write_text("# Sample constitution\n", encoding="utf-8")

    _code, payload = _run(tmp_path)
    assert not _findings_by_category(payload, "unreachable-knowledge-root")


def test_generated_site_knowledge_root_is_not_unreachable(tmp_path: Path) -> None:
    _write_doc(tmp_path, ".knowledge/architecture/one.md")
    generated = tmp_path / "site" / "_site" / "raw" / ".knowledge" / "governance"
    generated.mkdir(parents=True)
    (generated / "constitution.md").write_text("# Generated copy\n", encoding="utf-8")

    _code, payload = _run(tmp_path)
    assert not _findings_by_category(payload, "unreachable-knowledge-root")


def test_schema_tooling_contradiction_detected(tmp_path: Path) -> None:
    _write_doc(tmp_path, ".knowledge/architecture/one.md")
    registry = tmp_path / ".knowledge/taxonomy-registry.json"
    registry.write_text(
        json.dumps({"mappings": [{"pathPattern": ".knowledge/legacy/**", "nodeType": "historical-record"}]}),
        encoding="utf-8",
    )

    _code, payload = _run(tmp_path)
    contradictions = _findings_by_category(payload, "schema-tooling-contradiction")
    assert len(contradictions) == 1
    assert contradictions[0]["severity"] == "medium"


def test_stable_finding_identity_across_repeated_scans(tmp_path: Path) -> None:
    _write_doc(tmp_path, ".knowledge/architecture/one.md", extra={"type": "not-a-real-type"})

    _code1, payload1 = _run(tmp_path)
    _code2, payload2 = _run(tmp_path)

    ids1 = sorted(f["finding_id"] for f in payload1["FINDINGS"])
    ids2 = sorted(f["finding_id"] for f in payload2["FINDINGS"])
    assert ids1 == ids2
    assert ids1  # sanity: the fixture actually produced findings to compare


def test_missing_derived_index_is_not_a_finding(tmp_path: Path) -> None:
    _write_doc(tmp_path, ".knowledge/architecture/one.md")

    code, payload = _run(tmp_path)
    assert _findings_by_category(payload, "generated-artifact-drift") == []
    assert code == 0


def test_every_emitted_finding_validates_against_shared_schema(tmp_path: Path) -> None:
    # Combine several trigger conditions so the check exercises more than one category at once.
    _write_doc(tmp_path, ".knowledge/architecture/one.md", extra={"type": "not-a-real-type"})
    (tmp_path / "examples").mkdir()
    (tmp_path / "examples" / ".knowledge").mkdir()

    _, payload = _run(tmp_path)
    findings = payload["FINDINGS"]
    assert findings, "expected at least one finding to validate against the schema"
    for finding in findings:
        errors = validate_finding(finding)
        assert errors == [], f"{finding.get('finding_id')}: {errors}"

