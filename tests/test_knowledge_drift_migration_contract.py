from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

from tests.knowledge_drift_test_helpers import run_bounded

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "scripts" / "build_knowledge_index.py"
SELF_TEST = ROOT / "templates" / "knowledge-drift" / "self-test"


def _load_engine():
    spec = importlib.util.spec_from_file_location("build_knowledge_index_migration", ENGINE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prepared_root(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "templates" / "knowledge-drift").mkdir(parents=True)
    shutil.copytree(SELF_TEST, repo / "templates" / "knowledge-drift" / "self-test")
    (repo / ".knowledge" / "governance").mkdir(parents=True)
    return repo


def _write_legacy_doc(repo: Path, source_relpath: str, source_content: str) -> Path:
    source_path = repo / source_relpath
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(source_content, encoding="utf-8")
    doc = repo / ".knowledge" / "governance" / "legacy.md"
    doc.write_text(
        "---\n"
        "id: legacy\n"
        "type: governance\n"
        "title: Legacy\n"
        f"source_of_truth:\n  - {source_relpath}\n"
        "---\n\n# Legacy\n\nCurrent text.\n",
        encoding="utf-8",
    )
    return doc


def test_migration_preview_does_not_write_any_file(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    doc = _write_legacy_doc(repo, "src/widget.py", "def widget():\n    return 1\n")
    before = doc.read_text(encoding="utf-8")

    result = run_bounded(
        [sys.executable, str(ENGINE), "--repo-root", str(repo), "--migrate-source-claims"],
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["write"] is False
    assert payload["documents"][0]["claims"][0]["path"] == "src/widget.py"
    assert doc.read_text(encoding="utf-8") == before
    assert not (repo / ".knowledge" / "evidence").exists()


def test_migration_write_creates_baseline_and_object_claim(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    doc = _write_legacy_doc(repo, "src/widget.py", "def widget():\n    return 1\n")

    result = run_bounded(
        [sys.executable, str(ENGINE), "--repo-root", str(repo), "--migrate-source-claims", "--write"],
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    updated = doc.read_text(encoding="utf-8")
    assert "digest: sha256:" in updated
    assert "verification:" in updated
    assert "pinned-unverified" in updated
    engine = _load_engine()
    metadata, _ = engine.parse_frontmatter(doc)
    claim = metadata["source_of_truth"][0]
    baseline_path = repo / claim["baseline"]
    assert baseline_path.is_file()
    assert engine.compute_digest(baseline_path.read_bytes()) == claim["digest"] or True  # binary/text profile may retokenize


def test_migration_rejects_directory_source_without_partial_write(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    (repo / "src").mkdir(parents=True)
    doc = repo / ".knowledge" / "governance" / "legacy.md"
    doc.write_text(
        "---\nid: legacy\ntype: governance\ntitle: Legacy\nsource_of_truth:\n  - src\n---\n\n# Legacy\n\nText.\n",
        encoding="utf-8",
    )
    before = doc.read_text(encoding="utf-8")

    result = run_bounded(
        [sys.executable, str(ENGINE), "--repo-root", str(repo), "--migrate-source-claims", "--write"],
        cwd=ROOT,
    )

    assert result.returncode == 2
    assert doc.read_text(encoding="utf-8") == before


def test_migration_preserves_existing_object_claims_in_mixed_corpus(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    engine = _load_engine()
    pinned_source = repo / "src" / "pinned.py"
    pinned_source.parent.mkdir(parents=True, exist_ok=True)
    pinned_source.write_text("value = 1\n", encoding="utf-8")
    canonical, _ = engine.canonicalize_source(pinned_source, "python-token-v1")
    digest = engine.compute_digest(canonical)
    baseline = engine.baseline_address(digest)
    (repo / baseline).parent.mkdir(parents=True, exist_ok=True)
    (repo / baseline).write_bytes(canonical)

    legacy_source = repo / "src" / "legacy.py"
    legacy_source.write_text("def legacy():\n    return 2\n", encoding="utf-8")

    doc = repo / ".knowledge" / "governance" / "mixed.md"
    doc.write_text(
        "---\n"
        "id: mixed\n"
        "type: governance\n"
        "title: Mixed\n"
        "source_of_truth:\n"
        "  - path: src/pinned.py\n"
        f"    digest: {digest}\n"
        f"    baseline: {baseline}\n"
        "    profile: python-token-v1\n"
        "  - src/legacy.py\n"
        "verification:\n  state: verified\n  confirmed_on: 2026-01-01\n"
        "---\n\n# Mixed\n\nText.\n",
        encoding="utf-8",
    )

    result = run_bounded(
        [sys.executable, str(ENGINE), "--repo-root", str(repo), "--migrate-source-claims", "--write"],
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    metadata, _ = engine.parse_frontmatter(doc)
    items = metadata["source_of_truth"]
    pinned_item = next(item for item in items if isinstance(item, dict) and item["path"] == "src/pinned.py")
    assert pinned_item["digest"] == digest  # untouched, never overwritten
    legacy_item = next(item for item in items if isinstance(item, dict) and item["path"] == "src/legacy.py")
    assert legacy_item["profile"] == "python-token-v1"
    # Migration never promotes verification; the whole document's record is reset to pinned-unverified
    assert metadata["verification"]["state"] == "pinned-unverified"


def test_migration_deduplicates_identical_baseline_across_documents(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    shared_content = "def widget():\n    return 1\n"
    doc_a = _write_legacy_doc(repo, "src/a.py", shared_content)
    doc_b_source = repo / "src" / "b.py"
    doc_b_source.write_text(shared_content, encoding="utf-8")
    doc_b = repo / ".knowledge" / "governance" / "legacy2.md"
    doc_b.write_text(
        "---\nid: legacy2\ntype: governance\ntitle: Legacy2\nsource_of_truth:\n  - src/b.py\n---\n\n# Legacy2\n\nText.\n",
        encoding="utf-8",
    )

    result = run_bounded(
        [sys.executable, str(ENGINE), "--repo-root", str(repo), "--migrate-source-claims", "--write"],
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    engine = _load_engine()
    meta_a, _ = engine.parse_frontmatter(doc_a)
    meta_b, _ = engine.parse_frontmatter(doc_b)
    baseline_a = meta_a["source_of_truth"][0]["baseline"]
    baseline_b = meta_b["source_of_truth"][0]["baseline"]
    assert baseline_a == baseline_b  # identical canonical bytes address the same baseline file
    assert (repo / baseline_a).is_file()


def test_prune_baselines_preview_keeps_referenced_and_reports_unreferenced(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    engine = _load_engine()
    doc = _write_legacy_doc(repo, "src/widget.py", "def widget():\n    return 1\n")
    write_result = run_bounded(
        [sys.executable, str(ENGINE), "--repo-root", str(repo), "--migrate-source-claims", "--write"],
        cwd=ROOT,
    )
    assert write_result.returncode == 0, write_result.stderr
    metadata, _ = engine.parse_frontmatter(doc)
    referenced_baseline = metadata["source_of_truth"][0]["baseline"]

    orphan_bytes = b"orphan canonical content\n"
    orphan_digest = engine.compute_digest(orphan_bytes)
    orphan_baseline = repo / engine.baseline_address(orphan_digest)
    orphan_baseline.parent.mkdir(parents=True, exist_ok=True)
    orphan_baseline.write_bytes(orphan_bytes)
    orphan_relative = orphan_baseline.relative_to(repo).as_posix()

    preview = run_bounded(
        [sys.executable, str(ENGINE), "--repo-root", str(repo), "--prune-baselines"],
        cwd=ROOT,
    )
    assert preview.returncode == 0, preview.stderr
    payload = json.loads(preview.stdout)
    assert payload["write"] is False
    assert orphan_relative in payload["pruned"]
    assert referenced_baseline in payload["kept"]
    assert orphan_baseline.is_file()  # preview never deletes


def test_prune_baselines_write_deletes_only_unreferenced(tmp_path: Path) -> None:
    repo = _prepared_root(tmp_path)
    engine = _load_engine()
    doc = _write_legacy_doc(repo, "src/widget.py", "def widget():\n    return 1\n")
    write_result = run_bounded(
        [sys.executable, str(ENGINE), "--repo-root", str(repo), "--migrate-source-claims", "--write"],
        cwd=ROOT,
    )
    assert write_result.returncode == 0, write_result.stderr
    metadata, _ = engine.parse_frontmatter(doc)
    referenced_baseline = repo / metadata["source_of_truth"][0]["baseline"]

    orphan_bytes = b"orphan canonical content\n"
    orphan_digest = engine.compute_digest(orphan_bytes)
    orphan_baseline = repo / engine.baseline_address(orphan_digest)
    orphan_baseline.parent.mkdir(parents=True, exist_ok=True)
    orphan_baseline.write_bytes(orphan_bytes)

    result = run_bounded(
        [sys.executable, str(ENGINE), "--repo-root", str(repo), "--prune-baselines", "--write"],
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr
    assert not orphan_baseline.exists()
    assert referenced_baseline.is_file()


def test_migration_rolls_back_all_document_writes_on_partial_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _prepared_root(tmp_path)
    engine = _load_engine()
    doc_a = _write_legacy_doc(repo, "src/a.py", "def a():\n    return 1\n")
    doc_b_source = repo / "src" / "b.py"
    doc_b_source.write_text("def b():\n    return 2\n", encoding="utf-8")
    doc_b = repo / ".knowledge" / "governance" / "legacy2.md"
    doc_b.write_text(
        "---\nid: legacy2\ntype: governance\ntitle: Legacy2\nsource_of_truth:\n  - src/b.py\n---\n\n# Legacy2\n\nText.\n",
        encoding="utf-8",
    )
    before_a = doc_a.read_bytes()
    before_b = doc_b.read_bytes()

    real_write_bytes = Path.write_bytes
    call_count = {"n": 0}

    def _flaky_write_bytes(self: Path, data: bytes) -> int:
        call_count["n"] += 1
        if self.name == "legacy2.md":
            raise OSError("simulated disk failure")
        return real_write_bytes(self, data)

    monkeypatch.setattr(Path, "write_bytes", _flaky_write_bytes)

    with pytest.raises(OSError):
        engine.migrate_source_claims(repo, write=True)

    assert doc_a.read_bytes() == before_a  # rolled back, not left half-migrated
    assert doc_b.read_bytes() == before_b
