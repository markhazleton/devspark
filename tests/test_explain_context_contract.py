# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for the `/devspark.explain` context resolver.

Covers how a knowledge node's declared sources are reported back to the command, since a
wrong `exists` verdict there reads as stale knowledge rather than as a resolver bug. Also covers
the retained-baseline explain-and-confirm workflow (writer-enumeration, deterministic text/binary
diff, atomic rotation, interruption, shared-reference, and unreferenced-pruning), since a bug in
that workflow would silently confirm the wrong claim or corrupt a knowledge document.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "explain_context", ROOT / "scripts" / "explain-context.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def explain_context():
    return _load_module()


@pytest.fixture(scope="module")
def engine(explain_context):
    # `explain-context.py` already imports `build_knowledge_index` by absolute path; reuse the
    # exact same module object rather than loading a second copy under a different name.
    import sys

    return sys.modules["build_knowledge_index"]


def _write_claim_doc(
    repo: Path,
    doc_relpath: str,
    claims: list[dict[str, object]],
    *,
    verification: dict[str, object] | None = None,
) -> Path:
    doc = repo / doc_relpath
    doc.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "id": doc.stem,
        "type": "governance",
        "title": doc.stem,
        "source_of_truth": claims,
    }
    if verification is not None:
        metadata["verification"] = verification
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
    doc.write_text(f"---\n{frontmatter}---\n\n# {doc.stem}\n\nBody.\n", encoding="utf-8")
    return doc


def _pin_claim(engine, repo: Path, source_relpath: str, profile: str) -> dict[str, str]:
    """Write source + a matching baseline and return the resulting object claim dict."""
    source_path = repo / source_relpath
    canonical, _ = engine.canonicalize_source(source_path, profile)
    digest = engine.compute_digest(canonical)
    baseline = engine.baseline_address(digest)
    baseline_path = repo / baseline
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_bytes(canonical)
    return {"path": source_relpath, "digest": digest, "baseline": baseline, "profile": profile}


def _write_source(repo: Path, relpath: str, content: str) -> Path:
    path = repo / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_binary_source(repo: Path, relpath: str, content: bytes) -> Path:
    path = repo / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _repo_with_source(tmp_path: Path) -> Path:
    (tmp_path / "src" / "widget").mkdir(parents=True)
    (tmp_path / "src" / "widget" / "service.py").write_text("code\n", encoding="utf-8")
    return tmp_path


def test_glob_applies_to_resolves_when_files_match(explain_context, tmp_path: Path) -> None:
    repo = _repo_with_source(tmp_path)
    node = {"id": "widget", "path": ".knowledge/architecture/widget.md", "appliesTo": ["src/**/*.py"]}
    entry = explain_context.enrich_node(repo, node, {})
    assert [status["exists"] for status in entry["source_status"]] == [True]


def test_glob_applies_to_matching_nothing_is_reported_missing(explain_context, tmp_path: Path) -> None:
    repo = _repo_with_source(tmp_path)
    node = {"id": "widget", "path": ".knowledge/architecture/widget.md", "appliesTo": ["src/**/*.ts"]}
    entry = explain_context.enrich_node(repo, node, {})
    assert [status["exists"] for status in entry["source_status"]] == [False]


def test_literal_source_of_truth_still_resolves(explain_context, tmp_path: Path) -> None:
    repo = _repo_with_source(tmp_path)
    node = {
        "id": "widget",
        "path": ".knowledge/entities/widget/architecture.md",
        "source_of_truth": ["src/widget/service.py", "src/widget/missing.py"],
    }
    entry = explain_context.enrich_node(repo, node, {})
    assert [status["exists"] for status in entry["source_status"]] == [True, False]


# --- Retained-baseline explain-and-confirm workflow (writer-enumeration, diff, rotation) -------


def test_enrich_node_enumerates_every_claim_in_the_document(explain_context, engine, tmp_path: Path) -> None:
    repo = tmp_path
    _write_source(repo, "src/unchanged.py", "value = 1\n")
    _write_source(repo, "src/changed.py", "value = 2\n")
    unchanged_claim = _pin_claim(engine, repo, "src/unchanged.py", "python-token-v1")
    drifted_claim = _pin_claim(engine, repo, "src/changed.py", "python-token-v1")
    doc = _write_claim_doc(
        repo,
        ".knowledge/governance/widget.md",
        [unchanged_claim, drifted_claim],
        verification={"state": "verified", "confirmed_on": "2026-01-01"},
    )
    _write_source(repo, "src/changed.py", "value = 999\n")  # drift after pinning
    engine.reset_canonicalization_cache()

    node = {"id": "widget", "path": doc.relative_to(repo).as_posix()}
    entry = explain_context.enrich_node(repo, node, {})

    assert len(entry["claim_states"]) == 2
    statuses = {state["path"]: state["status"] for state in entry["claim_states"]}
    assert statuses["src/unchanged.py"] == "verified-current"
    assert statuses["src/changed.py"] == "drifted"
    assert entry["claim_states"][0]["diff"] is None
    assert entry["claim_states"][1]["diff"]["kind"] == "text"


def test_enumerate_claim_states_text_diff_is_a_deterministic_unified_diff(engine, tmp_path: Path) -> None:
    repo = tmp_path
    _write_source(repo, "src/widget.py", "def widget():\n    return 1\n")
    claim = _pin_claim(engine, repo, "src/widget.py", "exact-text-v1")
    doc = _write_claim_doc(repo, ".knowledge/governance/widget.md", [claim])
    _write_source(repo, "src/widget.py", "def widget():\n    return 2\n")
    engine.reset_canonicalization_cache()

    metadata, _ = engine.parse_frontmatter(doc)
    first = engine.enumerate_claim_states(repo, doc, metadata)
    second = engine.enumerate_claim_states(repo, doc, metadata)

    assert first == second
    assert first[0]["diff"]["kind"] == "text"
    assert any("return 2" in line for line in first[0]["diff"]["unified_diff"])


def test_enumerate_claim_states_binary_diff_reports_offset_ranges(engine, tmp_path: Path) -> None:
    repo = tmp_path
    _write_binary_source(repo, "assets/icon.bin", b"\x00\x01\x02\x03")
    claim = _pin_claim(engine, repo, "assets/icon.bin", "binary-v1")
    doc = _write_claim_doc(repo, ".knowledge/governance/icon.md", [claim])
    _write_binary_source(repo, "assets/icon.bin", b"\x00\xff\x02\x03")
    engine.reset_canonicalization_cache()

    metadata, _ = engine.parse_frontmatter(doc)
    states = engine.enumerate_claim_states(repo, doc, metadata)

    assert states[0]["diff"]["kind"] == "binary"
    assert states[0]["diff"]["ranges"]
    assert all({"op", "before_offset", "before_length", "after_offset", "after_length"} <= r.keys() for r in states[0]["diff"]["ranges"])


def test_rotate_claim_atomically_confirms_and_updates_digest(engine, tmp_path: Path) -> None:
    repo = tmp_path
    _write_source(repo, "src/widget.py", "def widget():\n    return 1\n")
    claim = _pin_claim(engine, repo, "src/widget.py", "exact-text-v1")
    doc = _write_claim_doc(
        repo, ".knowledge/governance/widget.md", [claim], verification={"state": "pinned-unverified"}
    )
    _write_source(repo, "src/widget.py", "def widget():\n    return 2\n")
    engine.reset_canonicalization_cache()

    result = engine.rotate_claim(repo, doc, "src/widget.py", "exact-text-v1")

    metadata, _ = engine.parse_frontmatter(doc)
    updated_claim = metadata["source_of_truth"][0]
    assert updated_claim["digest"] == result["digest_after"]
    assert updated_claim["digest"] != claim["digest"]
    assert metadata["verification"]["state"] == "verified"
    assert metadata["verification"]["confirmed_on"]
    assert (repo / updated_claim["baseline"]).is_file()


def test_rotate_claim_interruption_leaves_document_unchanged(engine, tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path
    _write_source(repo, "src/widget.py", "def widget():\n    return 1\n")
    claim = _pin_claim(engine, repo, "src/widget.py", "exact-text-v1")
    doc = _write_claim_doc(
        repo, ".knowledge/governance/widget.md", [claim], verification={"state": "pinned-unverified"}
    )
    _write_source(repo, "src/widget.py", "def widget():\n    return 2\n")
    engine.reset_canonicalization_cache()
    before_bytes = doc.read_bytes()

    original_write_bytes = Path.write_bytes
    call_count = {"n": 0}

    def flaky_write_bytes(self: Path, data: bytes):
        if self == doc:
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise OSError("simulated interruption")
        return original_write_bytes(self, data)

    monkeypatch.setattr(Path, "write_bytes", flaky_write_bytes)

    with pytest.raises(OSError):
        engine.rotate_claim(repo, doc, "src/widget.py", "exact-text-v1")

    assert doc.read_bytes() == before_bytes
    # The new baseline may already exist on disk (created before the failed document write) --
    # that is safe per the rotation-transaction contract, since it is unreferenced and prunable.


def test_rotate_claim_keeps_baseline_still_referenced_by_another_document(engine, tmp_path: Path) -> None:
    repo = tmp_path
    _write_source(repo, "src/shared.py", "value = 1\n")
    shared_claim = _pin_claim(engine, repo, "src/shared.py", "exact-text-v1")
    doc_a = _write_claim_doc(
        repo, ".knowledge/governance/a.md", [dict(shared_claim)], verification={"state": "verified", "confirmed_on": "2026-01-01"}
    )
    _write_source(repo, "src/other.py", "value = 1\n")
    other_claim = dict(shared_claim)
    other_claim["path"] = "src/other.py"  # deliberately shares the same digest/baseline address
    doc_b = _write_claim_doc(
        repo, ".knowledge/governance/b.md", [other_claim], verification={"state": "verified", "confirmed_on": "2026-01-01"}
    )
    _write_source(repo, "src/shared.py", "value = 2\n")  # only doc_a's claim now drifts
    engine.reset_canonicalization_cache()

    result = engine.rotate_claim(repo, doc_a, "src/shared.py", "exact-text-v1")

    old_baseline = repo / shared_claim["baseline"]
    assert old_baseline.is_file()  # still referenced by doc_b's unchanged claim
    assert shared_claim["baseline"] not in result["pruned"]
    metadata_b, _ = engine.parse_frontmatter(doc_b)
    assert metadata_b["source_of_truth"][0]["baseline"] == shared_claim["baseline"]


def test_rotate_claim_prunes_baseline_left_unreferenced_after_rotation(engine, tmp_path: Path) -> None:
    repo = tmp_path
    _write_source(repo, "src/widget.py", "def widget():\n    return 1\n")
    claim = _pin_claim(engine, repo, "src/widget.py", "exact-text-v1")
    doc = _write_claim_doc(
        repo, ".knowledge/governance/widget.md", [claim], verification={"state": "verified", "confirmed_on": "2026-01-01"}
    )
    old_baseline = repo / claim["baseline"]
    _write_source(repo, "src/widget.py", "def widget():\n    return 2\n")
    engine.reset_canonicalization_cache()

    result = engine.rotate_claim(repo, doc, "src/widget.py", "exact-text-v1")

    assert claim["baseline"] in result["pruned"]
    assert not old_baseline.exists()



def _owner_index():
    return {
        "nodes": [
            {"id": "governance", "path": ".knowledge/g.md", "form": "flat-document",
             "appliesTo": ["templates/commands/**"]},
            {"id": "engine-arch", "path": ".knowledge/entities/engine/arch.md", "form": "entity-layer",
             "entity": "engine", "source_of_truth": ["scripts/engine/", {"path": "scripts/a.py", "digest": "x"}]},
            {"id": "plan-note", "path": ".knowledge/p.md", "form": "flat-document",
             "source_of_truth": ["templates/commands/plan.md"]},
        ]
    }


def _owners(engine, path):
    located = engine.match_file_owners(_owner_index(), [path])
    return [(o["id"], o["relationship"]) for o in located["files"][0]["owners"]]


def test_files_mode_matches_glob_directory_object_claim_and_exact_path(engine) -> None:
    assert _owners(engine, "templates/commands/tasks.md") == [("governance", "appliesTo")]
    assert _owners(engine, "scripts/engine/core.py") == [("engine-arch", "source_of_truth")]
    assert _owners(engine, "scripts/a.py") == [("engine-arch", "source_of_truth")]


def test_files_mode_reports_overlapping_matches_with_their_relationships(engine) -> None:
    assert _owners(engine, "templates/commands/plan.md") == [
        ("governance", "appliesTo"),
        ("plan-note", "source_of_truth"),
    ]


def test_files_mode_reports_unmapped_files_and_entity_context(engine) -> None:
    located = engine.match_file_owners(_owner_index(), ["scripts/engine/core.py", "docs/other.md"])

    assert located["unmapped_files"] == ["docs/other.md"]
    assert located["files"][0]["owners"][0]["entity"] == "engine"
    assert located["files"][1]["owners"] == []


def test_explain_files_mode_cli_returns_owners_and_unmapped_files() -> None:
    import json
    import subprocess
    import sys

    done = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "explain-context.py"), "--files",
         "templates/commands/plan.md", "no/such/file.txt"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=120, stdin=subprocess.DEVNULL,
    )

    assert done.returncode == 0, done.stderr
    payload = json.loads(done.stdout)
    by_path = {item["path"]: item["owners"] for item in payload["FILES"]}
    assert by_path["templates/commands/plan.md"]
    assert payload["UNMAPPED_FILES"] == ["no/such/file.txt"]
    assert payload["SUMMARY"]["file_count"] == 2


def _project_repo(tmp_path: Path) -> Path:
    """A small repository: one flat document plus an entity whose two layers cite one source."""
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "engine.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    (repo / ".knowledge" / "governance").mkdir(parents=True)
    (repo / ".knowledge" / "governance" / "widgets.md").write_text(
        "---\nid: widgets\ntype: governance\ntitle: Widgets\n---\n\n# Widgets\n\nHow widgets are made.\n",
        encoding="utf-8",
    )
    entity = repo / ".knowledge" / "entities" / "engine"
    entity.mkdir(parents=True)
    (entity / "_entity.yaml").write_text("id: engine\ntype: subsystem\nowner: Team\n", encoding="utf-8")
    for layer in ("architecture", "business"):
        (entity / f"{layer}.md").write_text(
            f"---\nid: engine-{layer}\nlayer: {layer}\ntitle: Engine {layer}\n"
            "source_of_truth:\n  - src/engine.py\nlast_verified: 2099-01-01\n---\n\n"
            f"# Engine {layer}\n\nWidgets engine.\n",
            encoding="utf-8",
        )
    return repo


def _run_project(explain_context, monkeypatch, capsys, repo: Path, during_build=None):
    real_build = explain_context.build_index
    calls = {"builds": 0}

    def build(root, *args, **kwargs):
        calls["builds"] += 1
        index = real_build(root, *args, **kwargs)
        if during_build is not None:
            during_build(root)
        return index

    monkeypatch.setattr(explain_context, "repository_root", lambda: repo)
    monkeypatch.setattr(explain_context, "build_index", build)
    monkeypatch.setattr("sys.argv", ["explain-context.py", "--project", "widgets"])
    code = explain_context.main()
    return code, json.loads(capsys.readouterr().out), calls["builds"]


def test_project_builds_once_and_returns_a_projection_without_persisting_anything(
    explain_context, monkeypatch, capsys, tmp_path: Path
) -> None:
    repo = _project_repo(tmp_path)
    before = sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*"))

    code, payload, builds = _run_project(explain_context, monkeypatch, capsys, repo)

    assert code == 0 and builds == 1 and payload["INDEX_BUILDS"] == 1
    assert "widgets" in payload["PROJECTION"]["SEEDS"]
    assert "engine" in {item["id"] for item in payload["PROJECTION"]["CANDIDATES"]}  # reached through its layer
    assert "RETRY_REQUIRED" not in payload
    assert sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*")) == before


def _edit_keeping_mtime(path: Path, text: str) -> None:
    stat = path.stat()
    path.write_text(text, encoding="utf-8")
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))


@pytest.mark.parametrize("mutation", ["edit", "equal-mtime-edit", "add", "delete", "source-edit"])
def test_project_discards_output_when_an_input_changes_during_the_run(
    explain_context, monkeypatch, capsys, tmp_path: Path, mutation: str
) -> None:
    repo = _project_repo(tmp_path)
    doc = repo / ".knowledge" / "governance" / "widgets.md"

    def mutate(_root: Path) -> None:
        if mutation == "edit":
            doc.write_text(doc.read_text(encoding="utf-8") + "\nMore.\n", encoding="utf-8")
        elif mutation == "equal-mtime-edit":
            _edit_keeping_mtime(doc, doc.read_text(encoding="utf-8").replace("made", "built"))
        elif mutation == "add":
            (doc.parent / "extra.md").write_text("---\nid: extra\ntype: governance\ntitle: Extra\n---\n\n# Extra\n", encoding="utf-8")
        elif mutation == "delete":
            doc.unlink()
        else:
            _edit_keeping_mtime(repo / "src" / "engine.py", "def run():\n    return 2\n")

    code, payload, _ = _run_project(explain_context, monkeypatch, capsys, repo, during_build=mutate)

    assert code == 3 and payload["RETRY_REQUIRED"] is True and payload["CHANGED_INPUTS"]
    assert "PROJECTION" not in payload and "MATCHED_KNOWLEDGE" not in payload


def test_project_treats_unverifiable_inputs_as_changed(explain_context, monkeypatch, capsys, tmp_path: Path) -> None:
    repo = _project_repo(tmp_path)
    real = explain_context.knowledge_base_inventory
    calls = {"count": 0}

    def flaky(root):
        calls["count"] += 1
        if calls["count"] == 2:
            raise explain_context.InputsUncertain("history unavailable")
        return real(root)

    monkeypatch.setattr(explain_context, "knowledge_base_inventory", flaky)
    code, payload, _ = _run_project(explain_context, monkeypatch, capsys, repo)

    assert code == 3 and payload["CHANGED_INPUTS"] == ["uncertain: history unavailable"]


def test_one_build_queries_each_cited_source_history_once(engine, monkeypatch, tmp_path: Path) -> None:
    repo = _project_repo(tmp_path)
    queried: list[str] = []

    def record(root, relative_path):
        queried.append(relative_path)
        return None

    monkeypatch.setattr(engine, "_git_last_commit_date", record)
    engine.build_index(repo)
    assert queried == ["src/engine.py"]

    queried.clear()
    engine.build_index(repo)
    assert queried == ["src/engine.py"]  # a second build starts from nothing: no cross-build retention