from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

from tests.knowledge_drift_test_helpers import parse_json_report, run_bounded

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "scripts" / "build_knowledge_index.py"
SELF_TEST = ROOT / "templates" / "knowledge-drift" / "self-test"
CORRUPTIONS = ROOT / "tests" / "fixtures" / "knowledge-drift" / "corruptions"


def _load_engine():
    spec = importlib.util.spec_from_file_location("build_knowledge_index", ENGINE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prepared_root(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "templates" / "knowledge-drift").mkdir(parents=True)
    shutil.copytree(SELF_TEST, repo / "templates" / "knowledge-drift" / "self-test")
    (repo / ".knowledge").mkdir()
    return repo


def _run(repo: Path, report: Path) -> tuple[int, dict]:
    result = run_bounded(
        [
            sys.executable,
            str(ENGINE),
            "--repo-root",
            str(repo),
            "--detect-drift",
            "--full-inventory",
            "--report-output",
            str(report),
        ],
        cwd=ROOT,
    )
    return result.returncode, parse_json_report(report)


def test_corrupted_known_changed_control_fails_closed(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    shutil.copy2(CORRUPTIONS / "known-changed.py", repo / "templates/knowledge-drift/self-test/sources/known-changed.py")
    code, report = _run(repo, tmp_path / "changed.json")
    assert code == 2
    assert report["status"] == "error"
    assert report["findings"] == []
    assert "known-changed" in str(report["errors"])


def test_corrupted_known_unchanged_control_fails_closed(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    shutil.copy2(CORRUPTIONS / "known-unchanged.py", repo / "templates/knowledge-drift/self-test/sources/known-unchanged.py")
    code, report = _run(repo, tmp_path / "unchanged.json")
    assert code == 2
    assert report["status"] == "error"
    assert report["findings"] == []
    assert "known-unchanged" in str(report["errors"])


def test_invalid_canonicalization_control_fails_closed(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    claims = repo / "templates/knowledge-drift/self-test/claims.yaml"
    claims.write_text(claims.read_text(encoding="utf-8").replace("unsupported-profile-v1", "exact-text-v1"), encoding="utf-8")
    code, report = _run(repo, tmp_path / "invalid.json")
    assert code == 2
    assert report["status"] == "error"
    assert report["findings"] == []
    assert "canonical" in str(report["errors"]).lower()


def test_missing_runtime_source_fails_closed(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    (repo / "templates/knowledge-drift/self-test/sources/known-unchanged.py").unlink()
    code, report = _run(repo, tmp_path / "missing.json")
    assert code == 2
    assert report["status"] == "error"
    assert report["findings"] == []
    assert "known-unchanged" in str(report["errors"])


def test_failed_run_replaces_stale_report_with_no_findings(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    report_path = tmp_path / "stale.json"
    report_path.write_text(
        '{"status":"findings","findings":[{"source":"secret-value"}]}\n',
        encoding="utf-8",
    )
    shutil.copy2(
        CORRUPTIONS / "known-unchanged.py",
        repo / "templates/knowledge-drift/self-test/sources/known-unchanged.py",
    )
    code, report = _run(repo, report_path)
    assert code == 2
    assert report["status"] == "error"
    assert report["findings"] == []
    assert "secret-value" not in report_path.read_text(encoding="utf-8")


def test_report_write_failure_is_actionable(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    report_directory = tmp_path / "report-directory"
    report_directory.mkdir()
    result = run_bounded(
        [
            sys.executable,
            str(ENGINE),
            "--repo-root",
            str(repo),
            "--detect-drift",
            "--full-inventory",
            "--report-output",
            str(report_directory),
        ],
        cwd=ROOT,
    )
    assert result.returncode == 2
    assert "report write failed" in result.stderr


def test_tooling_timeout_is_actionable_and_fail_closed(tmp_path: Path, monkeypatch) -> None:
    engine = _load_engine()

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="canonicalizer", timeout=5)

    monkeypatch.setattr(engine, "canonicalize_source", timeout)
    errors = engine.run_self_test(_prepared_root(tmp_path))

    assert errors
    assert any("timed out" in error.lower() for error in errors)
    assert all("retry" in error.lower() or "restore" in error.lower() for error in errors)


def _write_pinned_doc(repo: Path, *, verified: bool, source_content: str = "value = 1\n") -> tuple[Path, str]:
    engine = _load_engine()
    source_path = repo / "src" / "widget.py"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(source_content, encoding="utf-8")
    canonical, _ = engine.canonicalize_source(source_path, "python-token-v1")
    digest = engine.compute_digest(canonical)
    baseline = engine.baseline_address(digest)
    (repo / baseline).parent.mkdir(parents=True, exist_ok=True)
    (repo / baseline).write_bytes(canonical)
    verification = "verification:\n  state: verified\n  confirmed_on: 2026-01-01\n" if verified else ""
    doc = repo / ".knowledge" / "governance" / "widget.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(
        "---\n"
        "id: widget\n"
        "type: governance\n"
        "title: Widget\n"
        "source_of_truth:\n"
        "  - path: src/widget.py\n"
        f"    digest: {digest}\n"
        f"    baseline: {baseline}\n"
        "    profile: python-token-v1\n"
        f"{verification}"
        "---\n\n# Widget\n\nCurrent text.\n",
        encoding="utf-8",
    )
    return source_path, digest


def test_verified_document_with_changed_source_is_a_blocking_finding(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    source_path, _ = _write_pinned_doc(repo, verified=True)
    source_path.write_text("value = 2\n", encoding="utf-8")

    code, report = _run(repo, tmp_path / "report.json")

    assert code == 1
    assert report["status"] == "findings"
    assert len(report["findings"]) == 1
    assert report["findings"][0]["document"] == ".knowledge/governance/widget.md"


def test_unverified_document_with_changed_source_is_advisory_not_blocking(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    source_path, _ = _write_pinned_doc(repo, verified=False)
    source_path.write_text("value = 2\n", encoding="utf-8")

    code, report = _run(repo, tmp_path / "report.json")

    assert code == 0
    assert report["findings"] == []
    assert any(a["type"] == "pinned-unverified" for a in report["advisories"])
    assert report["summary"]["pinned-unverified"] == 1


def test_unchanged_verified_document_is_verified_current(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    _write_pinned_doc(repo, verified=True)

    code, report = _run(repo, tmp_path / "report.json")

    assert code == 0
    assert report["findings"] == []
    assert report["summary"]["verified-current"] == 1


def test_missing_claimed_source_is_uncheckable_run_error(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    source_path, _ = _write_pinned_doc(repo, verified=True)
    source_path.unlink()

    code, report = _run(repo, tmp_path / "report.json")

    assert code == 2
    assert report["status"] == "error"
    assert report["findings"] == []


def test_directory_claim_is_an_authoring_error(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    source_directory = repo / "src" / "widget"
    source_directory.mkdir(parents=True)
    engine = _load_engine()
    digest = engine.compute_digest(b"directory claim")
    baseline = engine.baseline_address(digest)
    (repo / baseline).parent.mkdir(parents=True, exist_ok=True)
    (repo / baseline).write_bytes(b"directory claim")
    (repo / ".knowledge" / "governance" / "widget.md").parent.mkdir(parents=True, exist_ok=True)
    (repo / ".knowledge" / "governance" / "widget.md").write_text(
        "---\n"
        "id: widget\n"
        "type: governance\n"
        "title: Widget\n"
        "source_of_truth:\n"
        "  - path: src/widget\n"
        f"    digest: {digest}\n"
        f"    baseline: {baseline}\n"
        "    profile: exact-text-v1\n"
        "verification:\n"
        "  state: verified\n"
        "  confirmed_on: 2026-01-01\n"
        "---\n\n# Widget\n",
        encoding="utf-8",
    )

    code, report = _run(repo, tmp_path / "directory.json")

    assert code == 2
    assert report["findings"] == []
    assert "regular file" in str(report["errors"]).lower() or "exists" in str(report["errors"]).lower()


def test_duplicate_claim_tuple_is_an_authoring_error_for_flat_documents(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    source_path, digest = _write_pinned_doc(repo, verified=True)
    baseline = _load_engine().baseline_address(digest)
    doc_path = repo / ".knowledge" / "governance" / "widget.md"
    text = doc_path.read_text(encoding="utf-8")
    text = text.replace(
        "    profile: python-token-v1\n",
        "    profile: python-token-v1\n"
        f"  - path: {source_path.relative_to(repo).as_posix()}\n"
        f"    digest: {digest}\n"
        f"    baseline: {baseline}\n"
        "    profile: python-token-v1\n",
        1,
    )
    doc_path.write_text(text, encoding="utf-8")

    code, report = _run(repo, tmp_path / "duplicate.json")

    assert code == 2
    assert report["findings"] == []
    assert "duplicate source claim" in str(report["errors"]).lower()


def test_malformed_enforcement_value_is_a_hard_configuration_error(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    config_path = repo / ".devspark.work"
    config_path.mkdir(parents=True, exist_ok=True)
    (config_path / "devspark.json").write_text(
        json.dumps({"knowledge_drift": {"enforcement": "typo-value"}}), encoding="utf-8"
    )

    code, report = _run(repo, tmp_path / "report.json")

    assert code == 2
    assert report["status"] == "error"
    assert "pinned-claims" in str(report["errors"])


def test_absent_enforcement_key_keeps_legacy_behavior(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    config_path = repo / ".devspark.work"
    config_path.mkdir(parents=True, exist_ok=True)
    (config_path / "devspark.json").write_text(json.dumps({"platform": "github"}), encoding="utf-8")

    code, report = _run(repo, tmp_path / "report.json")

    assert code == 0
    assert report["status"] == "ok"


def test_currency_report_is_advisory_and_separate_from_drift_exit_code(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    source_path, _ = _write_pinned_doc(repo, verified=True)
    source_path.write_text("value = 2\n", encoding="utf-8")

    drift_code, drift_report = _run(repo, tmp_path / "drift.json")
    currency_result = run_bounded(
        [
            sys.executable,
            str(ENGINE),
            "--repo-root",
            str(repo),
            "--currency-report",
            "--currency-days",
            "90",
            "--report-output",
            str(tmp_path / "currency.json"),
        ],
        cwd=ROOT,
    )
    currency_report = parse_json_report(tmp_path / "currency.json")

    assert drift_code == 1
    assert drift_report["findings"]
    assert currency_result.returncode == 0
    assert currency_report["schema_version"] == "1"
    assert currency_report["currency_days"] == 90
    assert currency_report["stale"]


def test_breadth_guidance_emits_advisory_above_threshold(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    engine = _load_engine()
    doc, digest = _write_pinned_doc(repo, verified=True)
    second_source = repo / "src" / "widget2.py"
    second_source.write_text("value2 = 2\n", encoding="utf-8")
    canonical, _ = engine.canonicalize_source(second_source, "python-token-v1")
    second_digest = engine.compute_digest(canonical)
    second_baseline = engine.baseline_address(second_digest)
    (repo / second_baseline).parent.mkdir(parents=True, exist_ok=True)
    (repo / second_baseline).write_bytes(canonical)
    doc_path = repo / ".knowledge" / "governance" / "widget.md"
    text = doc_path.read_text(encoding="utf-8")
    text = text.replace(
        "    profile: python-token-v1\n",
        "    profile: python-token-v1\n"
        "  - path: src/widget2.py\n"
        f"    digest: {second_digest}\n"
        f"    baseline: {second_baseline}\n"
        "    profile: python-token-v1\n",
        1,
    )
    doc_path.write_text(text, encoding="utf-8")

    result = run_bounded(
        [
            sys.executable,
            str(ENGINE),
            "--repo-root",
            str(repo),
            "--detect-drift",
            "--full-inventory",
            "--breadth-guidance",
            "1",
            "--report-output",
            str(tmp_path / "report.json"),
        ],
        cwd=ROOT,
    )
    report = parse_json_report(tmp_path / "report.json")

    assert result.returncode == 0, report
    assert any(a["type"] == "breadth" for a in report["advisories"])


def test_duplicate_baseline_across_documents_reported_independently(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    engine = _load_engine()
    source_a = repo / "src" / "a.py"
    source_b = repo / "src" / "b.py"
    source_a.parent.mkdir(parents=True, exist_ok=True)
    identical_content = "value = 1\n"
    source_a.write_text(identical_content, encoding="utf-8")
    source_b.write_text(identical_content, encoding="utf-8")
    canonical, _ = engine.canonicalize_source(source_a, "python-token-v1")
    digest = engine.compute_digest(canonical)
    baseline = engine.baseline_address(digest)
    (repo / baseline).parent.mkdir(parents=True, exist_ok=True)
    (repo / baseline).write_bytes(canonical)

    def _doc(name: str, source_relative: str) -> None:
        doc = repo / ".knowledge" / "governance" / name
        doc.parent.mkdir(parents=True, exist_ok=True)
        doc.write_text(
            "---\n"
            f"id: {name}\n"
            "type: governance\n"
            "title: Widget\n"
            "source_of_truth:\n"
            f"  - path: {source_relative}\n"
            f"    digest: {digest}\n"
            f"    baseline: {baseline}\n"
            "    profile: python-token-v1\n"
            "verification:\n"
            "  state: verified\n"
            "  confirmed_on: 2026-01-01\n"
            "---\n\n# Widget\n\nCurrent text.\n",
            encoding="utf-8",
        )

    _doc("widget-a.md", "src/a.py")
    _doc("widget-b.md", "src/b.py")

    source_a.write_text("value = 2\n", encoding="utf-8")
    source_b.write_text("value = 2\n", encoding="utf-8")

    code, report = _run(repo, tmp_path / "report.json")

    assert code == 1
    assert report["status"] == "findings"
    documents = {finding["document"] for finding in report["findings"]}
    assert documents == {".knowledge/governance/widget-a.md", ".knowledge/governance/widget-b.md"}
    assert len(report["findings"]) == 2


def test_drift_finding_never_includes_raw_source_or_baseline_content(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    secret_marker = "SYNTHETIC-SOURCE-BODY-MARKER"
    source_path, _ = _write_pinned_doc(repo, verified=True, source_content=f"value = 1  # {secret_marker}\n")
    source_path.write_text(f"value = 2  # {secret_marker}-changed\n", encoding="utf-8")

    code, report = _run(repo, tmp_path / "report.json")

    assert code == 1
    assert report["status"] == "findings"
    report_text = (tmp_path / "report.json").read_text(encoding="utf-8")
    assert secret_marker not in report_text
    for finding in report["findings"]:
        for claim in finding["source_claims"]:
            assert set(claim.keys()) == {"path", "profile", "region", "digest_before", "digest_after"}


def _write_region_pinned_doc(
    repo: Path, *, region: str | None, source_content: str, verified: bool = True
) -> Path:
    engine = _load_engine()
    source_path = repo / "src" / "regioned.py"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(source_content, encoding="utf-8")
    canonical, _ = engine.canonicalize_source(source_path, "python-token-v1", region)
    digest = engine.compute_digest(canonical)
    baseline = engine.baseline_address(digest)
    (repo / baseline).parent.mkdir(parents=True, exist_ok=True)
    (repo / baseline).write_bytes(canonical)
    region_line = f"    region: {region}\n" if region else ""
    verification = "verification:\n  state: verified\n  confirmed_on: 2026-01-01\n" if verified else ""
    doc = repo / ".knowledge" / "governance" / "regioned.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(
        "---\n"
        "id: regioned\n"
        "type: governance\n"
        "title: Regioned\n"
        "source_of_truth:\n"
        "  - path: src/regioned.py\n"
        f"    digest: {digest}\n"
        f"    baseline: {baseline}\n"
        "    profile: python-token-v1\n"
        f"{region_line}"
        f"{verification}"
        "---\n\n# Regioned\n\nCurrent text.\n",
        encoding="utf-8",
    )
    return source_path


_REGIONED_SOURCE = "def target():\n    return 1\n\n\ndef other():\n    return 2\n"


def test_symbolic_region_resolution_ignores_changes_outside_the_named_region(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    source_path = _write_region_pinned_doc(repo, region="target", source_content=_REGIONED_SOURCE)
    # Change only the unrelated `other` function; the pinned `target` region is untouched.
    source_path.write_text(_REGIONED_SOURCE.replace("return 2", "return 99"), encoding="utf-8")

    code, report = _run(repo, tmp_path / "report.json")

    assert code == 0
    assert report["findings"] == []
    assert not any(
        a["type"] == "region-widened" and a["document"] == ".knowledge/governance/regioned.md"
        for a in report["advisories"]
    )


def test_missing_region_widens_to_whole_source_with_advisory(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    _write_region_pinned_doc(repo, region="does-not-exist", source_content=_REGIONED_SOURCE)

    code, report = _run(repo, tmp_path / "report.json")

    # Widening is visible even when the (widened) content is still verified-current.
    assert code == 0
    assert report["findings"] == []
    assert any(
        a["type"] == "region-widened" and a["document"] == ".knowledge/governance/regioned.md"
        for a in report["advisories"]
    )


def test_region_widening_advisory_accompanies_a_blocking_finding_when_widened_content_changes(
    tmp_path: Path,
) -> None:
    repo = _prepared_root(tmp_path)
    source_path = _write_region_pinned_doc(repo, region="does-not-exist", source_content=_REGIONED_SOURCE)
    source_path.write_text(_REGIONED_SOURCE.replace("return 1", "return 100"), encoding="utf-8")

    code, report = _run(repo, tmp_path / "report.json")

    assert code == 1
    assert len(report["findings"]) == 1
    assert report["findings"][0]["document"] == ".knowledge/governance/regioned.md"
    assert any(
        a["type"] == "region-widened" and a["document"] == ".knowledge/governance/regioned.md"
        for a in report["advisories"]
    )


def test_manifest_error_redacts_control_body_from_report(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    claims = repo / "templates/knowledge-drift/self-test/claims.yaml"
    secret_marker = "SYNTHETIC-CONTROL-BODY"
    claims.write_text(f"controls: [\"{secret_marker}\"\n", encoding="utf-8")

    code, report = _run(repo, tmp_path / "redacted.json")

    assert code == 2
    assert report["findings"] == []
    assert secret_marker not in (tmp_path / "redacted.json").read_text(encoding="utf-8")
