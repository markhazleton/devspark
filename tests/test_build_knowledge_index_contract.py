# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for the entity-ontology superset of the knowledge index builder.

Covers .knowledge/entities/<id>/_entity.yaml + layer docs, additive to the pre-existing flat
type-folder model exercised by test_knowledge_index_contract.py.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "scripts" / "build_knowledge_index.py"


def _entity(
    tmp_path: Path,
    entity_id: str = "widget",
    layers: tuple[str, ...] = ("architecture",),
    overrides: tuple[str, ...] = (),
    source_of_truth: tuple[str, ...] = ("README.md",),
    last_verified: str | None = "2099-01-01",
) -> None:
    entity_dir = tmp_path / ".knowledge" / "entities" / entity_id
    entity_dir.mkdir(parents=True, exist_ok=True)
    overrides_yaml = "\n".join(
        f"  - layer: {layer}\n    justification: not applicable" for layer in overrides
    )
    (entity_dir / "_entity.yaml").write_text(
        f"id: {entity_id}\ntype: subsystem\nowner: team-x\n"
        + (f"coverage_overrides:\n{overrides_yaml}\n" if overrides else ""),
        encoding="utf-8",
    )
    for layer in layers:
        sources_yaml = "\n".join(f"  - {path}" for path in source_of_truth)
        (entity_dir / f"{layer}.md").write_text(
            "\n".join(
                (
                    "---",
                    "type: entity-layer",
                    f"layer: {layer}",
                    f"title: {entity_id} {layer}",
                    "source_of_truth:",
                    sources_yaml,
                    *((f"last_verified: {last_verified}",) if last_verified else ()),
                    "---",
                    "",
                    f"# {entity_id} {layer}",
                    "",
                    "Current behavior.",
                    "",
                )
            ),
            encoding="utf-8",
        )
    (tmp_path / "README.md").write_text("placeholder\n", encoding="utf-8")


def _run(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ENGINE), "--repo-root", str(repo), "--stdout"],
        text=True,
        capture_output=True,
    )


def test_entity_with_all_layers_has_no_coverage_gap(tmp_path: Path) -> None:
    _entity(tmp_path, layers=("architecture", "business", "integration", "operations", "pattern", "plan"))
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr
    index = json.loads(result.stdout)
    entity = index["entities"][0]
    assert entity["missing_layers"] == []
    assert {node["layer"] for node in index["nodes"] if node.get("entity") == "widget"} == {
        "architecture",
        "business",
        "integration",
        "operations",
        "pattern",
        "plan",
    }


def test_missing_layer_without_override_is_a_gap(tmp_path: Path) -> None:
    _entity(tmp_path, layers=("architecture",))
    result = _run(tmp_path)
    index = json.loads(result.stdout)
    assert "business" in index["entities"][0]["missing_layers"]


def test_missing_layer_with_override_is_not_a_gap(tmp_path: Path) -> None:
    _entity(
        tmp_path,
        layers=("architecture",),
        overrides=("business", "integration", "operations", "pattern", "plan"),
    )
    result = _run(tmp_path)
    index = json.loads(result.stdout)
    assert index["entities"][0]["missing_layers"] == []


def test_nonexistent_source_of_truth_fails(tmp_path: Path) -> None:
    _entity(tmp_path, source_of_truth=("does/not/exist.py",))
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "does not exist" in result.stderr


def test_source_of_truth_pointing_into_devspark_work_fails(tmp_path: Path) -> None:
    work_file = tmp_path / ".devspark.work/specs/001-foo/plan.md"
    work_file.parent.mkdir(parents=True, exist_ok=True)
    work_file.write_text("plan\n", encoding="utf-8")
    _entity(tmp_path, source_of_truth=(".devspark.work/specs/001-foo/plan.md",))
    result = _run(tmp_path)
    assert result.returncode != 0
    assert ".devspark.work/ or .archive/" in result.stderr


def test_source_of_truth_pointing_into_archive_fails(tmp_path: Path) -> None:
    archived_file = tmp_path / ".archive/2026-01-01/specs/001-foo/plan.md"
    archived_file.parent.mkdir(parents=True, exist_ok=True)
    archived_file.write_text("plan\n", encoding="utf-8")
    _entity(tmp_path, source_of_truth=(".archive/2026-01-01/specs/001-foo/plan.md",))
    result = _run(tmp_path)
    assert result.returncode != 0
    assert ".devspark.work/ or .archive/" in result.stderr


def test_entity_id_must_match_folder_name(tmp_path: Path) -> None:
    _entity(tmp_path, entity_id="widget")
    entity_yaml = tmp_path / ".knowledge/entities/widget/_entity.yaml"
    entity_yaml.write_text("id: other\ntype: subsystem\nowner: team-x\n", encoding="utf-8")
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "must match folder name" in result.stderr


def test_missing_entity_yaml_fails(tmp_path: Path) -> None:
    _entity(tmp_path)
    (tmp_path / ".knowledge/entities/widget/_entity.yaml").unlink()
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "missing required _entity.yaml" in result.stderr


def _write_flat_doc_with_applies_to(tmp_path: Path, applies_to: str) -> None:
    doc = tmp_path / ".knowledge/architecture/widget.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(
        "\n".join(
            (
                "---",
                "id: widget",
                "type: architecture",
                "title: Widget",
                "appliesTo:",
                f"  - {applies_to}",
                "---",
                "",
                "# Widget",
                "",
                "Current behavior.",
                "",
            )
        ),
        encoding="utf-8",
    )


def test_unmapped_files_reports_only_files_matching_no_pattern(tmp_path: Path) -> None:
    _write_flat_doc_with_applies_to(tmp_path, "src/widget/**")
    (tmp_path / "README.md").write_text("placeholder\n", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ENGINE),
            "--repo-root",
            str(tmp_path),
            "--unmapped-files",
            "src/widget/service.py",
            "src/other/module.py",
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == ["src/other/module.py"]


def test_unmapped_files_never_writes_index(tmp_path: Path) -> None:
    _write_flat_doc_with_applies_to(tmp_path, "src/widget/**")
    result = subprocess.run(
        [
            sys.executable,
            str(ENGINE),
            "--repo-root",
            str(tmp_path),
            "--unmapped-files",
            "src/other/module.py",
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / ".knowledge/index.json").exists()


def test_flat_and_entity_docs_coexist(tmp_path: Path) -> None:
    _entity(tmp_path)
    flat = tmp_path / ".knowledge/architecture/legacy.md"
    flat.parent.mkdir(parents=True)
    flat.write_text(
        "---\nid: legacy\ntype: architecture\ntitle: Legacy\n---\n\n# Legacy\n\nCurrent text.\n",
        encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr
    index = json.loads(result.stdout)
    ids = {node["id"] for node in index["nodes"]}
    assert "legacy" in ids
    assert "widget-architecture" in ids


def test_coverage_report_written_alongside_index(tmp_path: Path) -> None:
    _entity(tmp_path, layers=("architecture",))
    result = subprocess.run(
        [sys.executable, str(ENGINE), "--repo-root", str(tmp_path)],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    coverage = json.loads((tmp_path / ".knowledge/ontology/coverage.json").read_text(encoding="utf-8"))
    assert coverage["entity_count"] == 1
    assert coverage["fully_covered"] == 0
    assert coverage["gaps"][0]["entity"] == "widget"
    assert "business" in coverage["gaps"][0]["missing_layers"]


def _generate(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ENGINE), "--repo-root", str(repo)],
        text=True,
        capture_output=True,
        timeout=60,
    )


def _check(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ENGINE), "--repo-root", str(repo), "--check"],
        text=True,
        capture_output=True,
        timeout=60,
    )


def _coverage(repo: Path) -> dict:
    return json.loads((repo / ".knowledge/ontology/coverage.json").read_text(encoding="utf-8"))


def test_check_passes_for_freshly_generated_entity_coverage(tmp_path: Path) -> None:
    _entity(tmp_path, layers=("architecture",))
    assert _generate(tmp_path).returncode == 0
    result = _check(tmp_path)
    assert result.returncode == 0, result.stderr


def test_removing_final_entity_regenerates_zero_state_coverage(tmp_path: Path) -> None:
    _entity(tmp_path, layers=("architecture",))
    assert _generate(tmp_path).returncode == 0
    assert _coverage(tmp_path)["entity_count"] == 1

    shutil.rmtree(tmp_path / ".knowledge/entities/widget")
    result = _generate(tmp_path)
    assert result.returncode == 0, result.stderr
    coverage = _coverage(tmp_path)
    assert coverage["entity_count"] == 0
    assert coverage["fully_covered"] == 0
    assert coverage["gaps"] == []


def test_check_ignores_stale_derived_coverage(tmp_path: Path) -> None:
    _entity(tmp_path, layers=("architecture",))
    assert _generate(tmp_path).returncode == 0
    stale = _coverage(tmp_path)

    shutil.rmtree(tmp_path / ".knowledge/entities/widget")
    assert _generate(tmp_path).returncode == 0
    (tmp_path / ".knowledge/ontology/coverage.json").write_text(
        json.dumps(stale, indent=2) + "\n", encoding="utf-8"
    )

    result = _check(tmp_path)
    assert result.returncode == 0, result.stderr


def test_check_passes_without_any_derived_files_and_writes_none(tmp_path: Path) -> None:
    _write_flat_doc_with_applies_to(tmp_path, "src/widget/**")
    result = _check(tmp_path)
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / ".knowledge/index.json").exists()
    assert not (tmp_path / ".knowledge/ontology/coverage.json").exists()


def test_check_still_fails_when_knowledge_cannot_be_built(tmp_path: Path) -> None:
    _entity(tmp_path, layers=("architecture",))
    (tmp_path / ".knowledge/entities/widget/_entity.yaml").unlink()
    result = _check(tmp_path)
    assert result.returncode == 1


def test_legacy_shim_still_works(tmp_path: Path) -> None:
    legacy_engine = ROOT / "scripts" / "generate-knowledge-index.py"
    _entity(tmp_path, layers=("architecture",))
    result = subprocess.run(
        [sys.executable, str(legacy_engine), "--repo-root", str(tmp_path), "--stdout"],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["entities"][0]["id"] == "widget"


@pytest.mark.skipif(
    not (ROOT / ".git").exists(), reason="git-based staleness check requires a git repo"
)
def test_stale_last_verified_fails_in_real_repo() -> None:
    result = subprocess.run(
        [sys.executable, str(ENGINE), "--repo-root", str(ROOT), "--stdout"],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr


def _init_git_repo_with_commit(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True)


def test_stale_last_verified_is_reported_but_does_not_fail_by_default(tmp_path: Path) -> None:
    _entity(tmp_path, last_verified="2000-01-01")
    _init_git_repo_with_commit(tmp_path)
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr
    index = json.loads(result.stdout)
    assert index["stale_entities"], "expected the stale doc to be reported, not silently dropped"
    assert index["stale_entities"][0]["path"].endswith("architecture.md")
    assert "STALE:" in result.stderr


def test_current_last_verified_reports_no_staleness(tmp_path: Path) -> None:
    _entity(tmp_path, last_verified="2099-01-01")
    _init_git_repo_with_commit(tmp_path)
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["stale_entities"] == []
    assert "STALE:" not in result.stderr


def test_missing_last_verified_builds_and_is_never_stale(tmp_path: Path) -> None:
    _entity(tmp_path, last_verified=None)
    _init_git_repo_with_commit(tmp_path)
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr
    index = json.loads(result.stdout)
    assert index["stale_entities"] == []
    assert _check(tmp_path).returncode == 0


def test_invalid_last_verified_still_fails_when_present(tmp_path: Path) -> None:
    _entity(tmp_path, last_verified="not-a-date")
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "ISO date" in result.stderr


def test_fail_on_stale_flag_makes_staleness_blocking(tmp_path: Path) -> None:
    _entity(tmp_path, last_verified="2000-01-01")
    _init_git_repo_with_commit(tmp_path)
    result = subprocess.run(
        [sys.executable, str(ENGINE), "--repo-root", str(tmp_path), "--stdout", "--fail-on-stale"],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 1
    assert "last_verified" in result.stderr


def _write_entity_yaml(tmp_path: Path, entity_id: str, body: str) -> None:
    path = tmp_path / ".knowledge" / "entities" / entity_id / "_entity.yaml"
    path.write_text(body, encoding="utf-8")


def test_relation_to_unknown_entity_fails_the_build(tmp_path: Path) -> None:
    _entity(tmp_path, entity_id="widget")
    _write_entity_yaml(
        tmp_path,
        "widget",
        "id: widget\ntype: subsystem\nowner: team-x\nrelations:\n  - to: ghost\n    rel: depends-on\n",
    )
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "unknown entity 'ghost'" in result.stderr


def test_relation_without_a_target_fails_the_build(tmp_path: Path) -> None:
    _entity(tmp_path, entity_id="widget")
    _write_entity_yaml(
        tmp_path,
        "widget",
        "id: widget\ntype: subsystem\nowner: team-x\nrelations:\n  - rel: depends-on\n",
    )
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "requires an 'object' (or 'to') entity id" in result.stderr


def test_relation_to_known_entity_builds(tmp_path: Path) -> None:
    _entity(tmp_path, entity_id="widget")
    _entity(tmp_path, entity_id="gadget")
    _write_entity_yaml(
        tmp_path,
        "widget",
        "id: widget\ntype: subsystem\nowner: team-x\nrelations:\n  - to: gadget\n    rel: depends-on\n",
    )
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr
    index = json.loads(result.stdout)
    widget = next(entity for entity in index["entities"] if entity["id"] == "widget")
    assert widget["relations"] == [{"to": "gadget", "rel": "depends-on"}]


def test_predicate_object_relations_are_accepted(tmp_path: Path) -> None:
    """Both authored spellings build -- rejecting one strands an existing corpus on an old engine."""
    _entity(tmp_path, entity_id="widget")
    _entity(tmp_path, entity_id="gadget")
    _write_entity_yaml(
        tmp_path,
        "widget",
        "id: widget\ntype: subsystem\nowner: team-x\n"
        "relations:\n  - { predicate: routes-to, object: gadget }\n",
    )
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr
    assert {"from": "widget", "to": "gadget", "rel": "routes-to"} in json.loads(result.stdout)[
        "edges"
    ]


def test_relations_are_materialized_as_edges(tmp_path: Path) -> None:
    """A declared relation that produces no edge is a graph nothing can traverse."""
    _entity(tmp_path, entity_id="widget")
    _entity(tmp_path, entity_id="gadget")
    _write_entity_yaml(
        tmp_path,
        "widget",
        "id: widget\ntype: subsystem\nowner: team-x\nrelations:\n  - to: gadget\n    rel: depends-on\n",
    )
    index = json.loads(_run(tmp_path).stdout)
    assert {"from": "widget", "to": "gadget", "rel": "depends-on"} in index["edges"]
    assert index["dangling_references"] == []


def test_auxiliary_layers_do_not_count_as_coverage_gaps(tmp_path: Path) -> None:
    """`fully_covered` has to be reachable, or it reports nothing."""
    _entity(
        tmp_path,
        entity_id="widget",
        layers=("architecture", "business", "integration", "operations"),
    )
    index = json.loads(_run(tmp_path).stdout)
    widget = next(entity for entity in index["entities"] if entity["id"] == "widget")
    assert widget["missing_layers"] == []


def test_unresolved_reference_is_reported_without_failing(tmp_path: Path) -> None:
    node = tmp_path / ".knowledge" / "architecture" / "authentication.md"
    node.parent.mkdir(parents=True)
    node.write_text(
        "---\nid: authentication\ntype: architecture\ntitle: Authentication\n"
        "links:\n  references:\n    - identity-provider\n---\n\n"
        "# Authentication\n\nCurrent behavior.\n",
        encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr
    index = json.loads(result.stdout)
    assert index["dangling_references"] == [
        {
            "from": "authentication",
            "to": "identity-provider",
            "path": ".knowledge/architecture/authentication.md",
        }
    ]


def test_resolved_reference_is_not_reported_as_dangling(tmp_path: Path) -> None:
    for node_id in ("authentication", "identity-provider"):
        node = tmp_path / ".knowledge" / "architecture" / f"{node_id}.md"
        node.parent.mkdir(parents=True, exist_ok=True)
        references = "links:\n  references:\n    - identity-provider\n" if node_id == "authentication" else ""
        node.write_text(
            f"---\nid: {node_id}\ntype: architecture\ntitle: {node_id}\n{references}---\n\n"
            f"# {node_id}\n\nCurrent behavior.\n",
            encoding="utf-8",
        )
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["dangling_references"] == []


def _unmapped(repo: Path, *changed_files: str) -> list[str]:
    result = subprocess.run(
        [sys.executable, str(ENGINE), "--repo-root", str(repo), "--unmapped-files", *changed_files],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_entity_source_of_truth_claims_a_changed_file(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src/widget.py").write_text("code\n", encoding="utf-8")
    _entity(tmp_path, source_of_truth=("src/widget.py",))
    assert _unmapped(tmp_path, "src/widget.py", "src/other.py") == ["src/other.py"]


def test_directory_source_of_truth_claims_files_beneath_it(tmp_path: Path) -> None:
    (tmp_path / "src/widget").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src/widget/service.py").write_text("code\n", encoding="utf-8")
    _entity(tmp_path, source_of_truth=("src/widget",))
    assert _unmapped(tmp_path, "src/widget/service.py", "src/other/module.py") == [
        "src/other/module.py"
    ]


# --- Knowledge drift detection: canonicalization, digests, object-claim validation -----------


def _load_engine():
    import importlib.util

    spec = importlib.util.spec_from_file_location("build_knowledge_index_engine", ENGINE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def engine():
    module = _load_engine()
    module.reset_canonicalization_cache()
    yield module
    module.reset_canonicalization_cache()


def test_compute_digest_is_sha256_content_address(engine) -> None:
    digest = engine.compute_digest(b"hello")
    assert digest == "sha256:" + __import__("hashlib").sha256(b"hello").hexdigest()


def test_baseline_address_is_derived_from_digest(engine) -> None:
    digest = "sha256:" + "ab" * 32
    assert engine.baseline_address(digest) == f".knowledge/evidence/source-baselines/sha256/ab/{'ab' * 32}.baseline"


def test_baseline_address_rejects_malformed_digest(engine) -> None:
    with pytest.raises(engine.CanonicalizationError):
        engine.baseline_address("not-a-digest")


def test_exact_text_v1_canonicalizes_crlf_and_lf_identically(tmp_path: Path, engine) -> None:
    crlf = tmp_path / "crlf.txt"
    crlf.write_bytes(b"line one\r\nline two\r\n")
    lf = tmp_path / "lf.txt"
    lf.write_bytes(b"line one\nline two\n")
    crlf_bytes, crlf_widened = engine.canonicalize_source(crlf, "exact-text-v1")
    lf_bytes, lf_widened = engine.canonicalize_source(lf, "exact-text-v1")
    assert crlf_bytes == lf_bytes
    assert crlf_widened is False
    assert lf_widened is False


def test_binary_v1_is_byte_exact(tmp_path: Path, engine) -> None:
    payload = tmp_path / "payload.bin"
    payload.write_bytes(b"\x00\x01\x02\xff")
    canonical, widened = engine.canonicalize_source(payload, "binary-v1")
    assert canonical == b"\x00\x01\x02\xff"
    assert widened is False


def test_python_token_v1_ignores_comment_only_change(tmp_path: Path, engine) -> None:
    before = tmp_path / "before.py"
    before.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    after = tmp_path / "after.py"
    after.write_text("def add(a, b):\n    # explain the addition\n    return a + b\n", encoding="utf-8")
    before_bytes, _ = engine.canonicalize_source(before, "python-token-v1")
    after_bytes, _ = engine.canonicalize_source(after, "python-token-v1")
    assert before_bytes == after_bytes


def test_python_token_v1_detects_behavioral_change(tmp_path: Path, engine) -> None:
    before = tmp_path / "before.py"
    before.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    after = tmp_path / "after.py"
    after.write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    before_bytes, _ = engine.canonicalize_source(before, "python-token-v1")
    after_bytes, _ = engine.canonicalize_source(after, "python-token-v1")
    assert before_bytes != after_bytes


def test_python_token_v1_limits_comparison_to_named_region(tmp_path: Path, engine) -> None:
    before = tmp_path / "before.py"
    before.write_text(
        "def target():\n    return 1\n\n\ndef other():\n    return 1\n",
        encoding="utf-8",
    )
    after = tmp_path / "after.py"
    after.write_text(
        "def target():\n    return 1\n\n\ndef other():\n    return 2\n",
        encoding="utf-8",
    )
    before_bytes, widened_before = engine.canonicalize_source(before, "python-token-v1", "target")
    after_bytes, widened_after = engine.canonicalize_source(after, "python-token-v1", "target")
    assert before_bytes == after_bytes
    assert widened_before is False
    assert widened_after is False


def test_python_token_v1_widens_when_named_region_disappears(tmp_path: Path, engine) -> None:
    source = tmp_path / "source.py"
    source.write_text("def replacement():\n    return 1\n", encoding="utf-8")

    canonical, widened = engine.canonicalize_source(source, "python-token-v1", "missing")

    whole_file, whole_file_widened = engine.canonicalize_source(source, "python-token-v1")
    assert canonical == whole_file
    assert widened is True
    assert whole_file_widened is False


def test_python_token_v1_falls_back_to_exact_for_non_python_file(tmp_path: Path, engine) -> None:
    text_file = tmp_path / "notes.txt"
    text_file.write_text("hello\r\nworld\r\n", encoding="utf-8")
    canonical, widened = engine.canonicalize_source(text_file, "python-token-v1")
    exact, _ = engine.canonicalize_source(text_file, "exact-text-v1")
    assert canonical == exact
    assert widened is False


def test_python_token_v1_falls_back_to_exact_on_unparseable_source(tmp_path: Path, engine) -> None:
    broken = tmp_path / "broken.py"
    # Unterminated triple-quote: fails tokenize, must not raise out of canonicalize_source.
    broken.write_bytes(b'"""unterminated')
    canonical, widened = engine.canonicalize_source(broken, "python-token-v1")
    exact, _ = engine.canonicalize_source(broken, "exact-text-v1")
    assert canonical == exact
    assert widened is False


def test_canonicalize_source_rejects_unknown_profile(tmp_path: Path, engine) -> None:
    target = tmp_path / "file.txt"
    target.write_text("content\n", encoding="utf-8")
    with pytest.raises(engine.CanonicalizationError):
        engine.canonicalize_source(target, "nonexistent-profile-v1")


def test_canonicalize_source_is_cached_per_run(tmp_path: Path, engine) -> None:
    target = tmp_path / "cached.txt"
    target.write_text("content\n", encoding="utf-8")
    first, _ = engine.canonicalize_source(target, "exact-text-v1")
    target.write_text("changed on disk but cache is not re-read\n", encoding="utf-8")
    second, _ = engine.canonicalize_source(target, "exact-text-v1")
    assert first == second
    engine.reset_canonicalization_cache()
    third, _ = engine.canonicalize_source(target, "exact-text-v1")
    assert third != first


def _digest_and_baseline(engine, content: bytes) -> tuple[str, str]:
    digest = engine.compute_digest(content)
    return digest, engine.baseline_address(digest)


def test_validate_source_claims_accepts_well_formed_object_claim(tmp_path: Path, engine) -> None:
    digest, baseline = _digest_and_baseline(engine, b"anything")
    metadata = {
        "source_of_truth": [
            {"path": "scripts/build_knowledge_index.py", "digest": digest, "baseline": baseline, "profile": "exact-text-v1"}
        ]
    }
    engine.validate_source_claims(Path("doc.md"), metadata)  # must not raise


def test_validate_source_claims_rejects_baseline_digest_mismatch(tmp_path: Path, engine) -> None:
    digest, _ = _digest_and_baseline(engine, b"anything")
    wrong_baseline = engine.baseline_address(engine.compute_digest(b"something-else"))
    metadata = {
        "source_of_truth": [
            {"path": "scripts/build_knowledge_index.py", "digest": digest, "baseline": wrong_baseline, "profile": "exact-text-v1"}
        ]
    }
    with pytest.raises(engine.ObjectClaimError):
        engine.validate_source_claims(Path("doc.md"), metadata)


def test_validate_source_claims_rejects_duplicate_tuple(tmp_path: Path, engine) -> None:
    digest, baseline = _digest_and_baseline(engine, b"anything")
    claim = {"path": "scripts/build_knowledge_index.py", "digest": digest, "baseline": baseline, "profile": "exact-text-v1"}
    metadata = {"source_of_truth": [dict(claim), dict(claim)]}
    with pytest.raises(engine.ObjectClaimError):
        engine.validate_source_claims(Path("doc.md"), metadata)


def test_validate_source_claims_rejects_planning_path(tmp_path: Path, engine) -> None:
    digest, baseline = _digest_and_baseline(engine, b"anything")
    metadata = {
        "source_of_truth": [
            {
                "path": ".devspark.work/specs/002-example/tasks.md",
                "digest": digest,
                "baseline": baseline,
                "profile": "exact-text-v1",
            }
        ]
    }
    with pytest.raises(engine.ObjectClaimError):
        engine.validate_source_claims(Path("doc.md"), metadata)


def test_validate_source_claims_leaves_legacy_strings_untouched(engine) -> None:
    metadata = {"source_of_truth": ["scripts/build_knowledge_index.py", "README.md"]}
    engine.validate_source_claims(Path("doc.md"), metadata)  # must not raise


def test_validate_source_claims_verified_requires_confirmed_on(engine) -> None:
    metadata = {"source_of_truth": ["README.md"], "verification": {"state": "verified"}}
    with pytest.raises(engine.ObjectClaimError):
        engine.validate_source_claims(Path("doc.md"), metadata)
