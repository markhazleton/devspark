# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for `scripts/knowledge-benchmark.py`, DevSpark's canonical retrieval-evaluation
harness (DevSpark 7.6). These pin the same production-validation regression classes called out
in the 7.6 spec: narrow-vs-broad, governance visibility, body-only discovery, alias discovery,
generic shared headings, multi-concept recall, and run-to-run reproducibility.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
BENCHMARK_SCRIPT = ROOT / "scripts" / "knowledge-benchmark.py"


def _write_doc(
    repo: Path,
    relpath: str,
    *,
    title: str,
    body: str,
    node_type: str = "architecture",
    aliases: list[str] | None = None,
    extra: dict | None = None,
) -> None:
    doc = repo / relpath
    doc.parent.mkdir(parents=True, exist_ok=True)
    metadata: dict = {"id": doc.stem, "type": node_type, "title": title}
    if aliases is not None:
        metadata["aliases"] = aliases
    if extra:
        metadata.update(extra)
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
    doc.write_text(f"---\n{frontmatter}---\n\n{body}", encoding="utf-8")


def _run(repo: Path, fixture_path: Path, *, collapse: bool = False) -> dict:
    args = [sys.executable, str(BENCHMARK_SCRIPT), "--repo-root", str(repo), "--fixture", str(fixture_path)]
    if collapse:
        args.append("--collapse-entities")
    result = subprocess.run(args, text=True, capture_output=True, timeout=60)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _write_fixture(tmp_path: Path, cases: list[dict]) -> Path:
    fixture_path = tmp_path / "fixture.json"
    fixture_path.write_text(json.dumps({"cases": cases}), encoding="utf-8")
    return fixture_path


def test_narrow_document_beats_broad_document(tmp_path: Path) -> None:
    _write_doc(
        tmp_path, ".knowledge/architecture/chief-complaint.md",
        title="Chief Complaint Capture", body="How the patient chief complaint is captured and validated.\n",
    )
    _write_doc(
        tmp_path, ".knowledge/reference/glossary.md",
        title="Glossary", node_type="reference-data",
        body="chief complaint patient validated capture record note flag entry field value data item\n" * 3,
    )
    fixture = _write_fixture(tmp_path, [{"query": "how is the chief complaint captured", "expected": "chief-complaint"}])

    payload = _run(tmp_path, fixture)
    assert payload["cases"][0]["expected"][0]["rank"] == 1


def test_governance_node_remains_visible_even_when_outranked(tmp_path: Path) -> None:
    _write_doc(
        tmp_path, ".knowledge/architecture/scheduler.md",
        title="Scheduler", body="Scheduler behavior and retry policy for job dispatch.\n",
    )
    # A file under decisions/ IS a decision, so it must constrain something real. Sitting in that
    # directory is what makes it an ADR; frontmatter cannot opt a file out of where it lives.
    entity_dir = tmp_path / ".knowledge" / "entities" / "scheduler-service"
    entity_dir.mkdir(parents=True)
    (entity_dir / "_entity.yaml").write_text(
        "id: scheduler-service\ntype: subsystem\nowner: team-x\nconstrained_by: [scheduler-retry-policy]\n",
        encoding="utf-8",
    )
    _write_doc(
        tmp_path, ".knowledge/governance/decisions/scheduler-retry-policy.md",
        title="ADR: Scheduler Retry Policy", node_type="governance",
        body="Decision about scheduler retry policy and job dispatch.\n",
        extra={"constrains": ["scheduler-service"]},
    )
    fixture = _write_fixture(tmp_path, [{"query": "scheduler retry policy job dispatch", "expected": "scheduler"}])

    payload = _run(tmp_path, fixture)
    candidate_ids = {c["id"] for c in payload["cases"][0]["raw_top_candidates"]}
    assert "scheduler-retry-policy" in candidate_ids  # governance/ADR nodes are never silently excluded


def test_body_only_concept_is_discoverable(tmp_path: Path) -> None:
    _write_doc(
        tmp_path, ".knowledge/architecture/feature-flags.md",
        title="Feature Flags", body="Rollout uses a percentage-based gradual exposure strategy internally.\n",
    )
    fixture = _write_fixture(tmp_path, [{"query": "gradual exposure strategy", "expected": "feature-flags"}])

    payload = _run(tmp_path, fixture)
    assert payload["cases"][0]["expected"][0]["visible_within_limit"] is True


def test_alias_improves_retrieval(tmp_path: Path) -> None:
    _write_doc(
        tmp_path, ".knowledge/architecture/disconnect.md",
        title="Session Disconnect Handling", body="Handles abrupt termination.\n",
        aliases=["dropped call"],
    )
    fixture = _write_fixture(tmp_path, [{"query": "dropped call handling", "expected": "disconnect"}])

    payload = _run(tmp_path, fixture)
    assert payload["cases"][0]["expected"][0]["rank"] == 1
    assert any("alias" in m for m in payload["cases"][0]["expected"][0]["matched_on"])


def test_generic_shared_headings_stay_deterministic(tmp_path: Path) -> None:
    for name in ("alpha", "beta", "gamma"):
        _write_doc(
            tmp_path, f".knowledge/architecture/{name}.md",
            title=name.title(), body=f"## Overview\n## Decision\n## Notes\n{name} specific behavior detail.\n",
        )
    fixture = _write_fixture(tmp_path, [{"query": "beta specific behavior detail", "expected": "beta"}])

    first = _run(tmp_path, fixture)
    second = _run(tmp_path, fixture)
    assert first == second  # deterministic: identical corpus/query -> identical ranking
    assert first["cases"][0]["expected"][0]["rank"] == 1


def test_multi_concept_recall(tmp_path: Path) -> None:
    _write_doc(tmp_path, ".knowledge/architecture/patient-complaint.md", title="Patient Complaint", body="Captures patient complaint text.\n")
    _write_doc(tmp_path, ".knowledge/architecture/clarified-need.md", title="Clarified Need", body="Derives the clarified need from complaint text.\n")
    fixture = _write_fixture(
        tmp_path,
        [{"query": "patient complaint clarified need", "expected": ["patient-complaint", "clarified-need"]}],
    )

    payload = _run(tmp_path, fixture)
    recall = payload["cases"][0]["recall"]
    assert recall["relevant_expected"] == 2
    assert recall["relevant_returned"] == 2
    assert recall["recall_pct"] == 100.0
    assert payload["summary"]["multi_concept_mean_recall_pct"] == 100.0


def test_reproducibility_across_runs(tmp_path: Path) -> None:
    _write_doc(tmp_path, ".knowledge/architecture/configuration.md", title="Configuration", body="Runtime configuration source and precedence.\n")
    fixture = _write_fixture(tmp_path, [{"query": "runtime configuration precedence", "expected": "configuration"}])

    assert _run(tmp_path, fixture) == _run(tmp_path, fixture)


# --- 7.6.1 corrective regressions: consumer-visible vs. full-ranking semantics -----------------


def _write_entity(repo: Path, entity_id: str, *, body: str, title: str | None = None) -> None:
    entity_dir = repo / ".knowledge/entities" / entity_id
    entity_dir.mkdir(parents=True)
    (entity_dir / "_entity.yaml").write_text(
        yaml.safe_dump({"id": entity_id, "type": "subsystem", "owner": "team-x"}, sort_keys=False),
        encoding="utf-8",
    )
    src = repo / "src" / f"{entity_id}.py"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("def run():\n    pass\n", encoding="utf-8")
    metadata = {
        "id": f"{entity_id}-integration",
        "entity": entity_id,
        "layer": "architecture",
        "title": title or entity_id,
        "source_of_truth": [f"src/{entity_id}.py"],
        "last_verified": "2026-01-01",
    }
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
    (entity_dir / "architecture.md").write_text(f"---\n{frontmatter}---\n\n{body}\n", encoding="utf-8")


def test_benchmark_visible_set_correctness_deep_full_rank_is_not_promoted(tmp_path: Path) -> None:
    """Fixture #14 acceptance case: an expected entity present only at full-ranking position 10
    (with `limit=8`) must report a miss for consumer visibility -- collapsing must never promote
    it into the consumer-visible Top-8."""
    query_terms = "alpha delta report widget module process record entry"
    for i in range(9):
        _write_entity(tmp_path, f"filler{i}", body=f"{query_terms} filler variant {i} detail.\n")
    _write_entity(tmp_path, "target", body=f"{query_terms} distinct trailing token zzz.\n")
    fixture = _write_fixture(tmp_path, [{"query": query_terms, "expected": "target", "limit": 8}])

    payload = _run(tmp_path, fixture)
    expected = payload["cases"][0]["expected"][0]
    assert expected["full_ranking"]["rank"] == 10
    assert expected["consumer"]["rank"] is None
    assert expected["consumer"]["visible"] is False
    assert expected["visible_within_limit"] is False  # back-compat field must not be silently promoted


def test_duplicate_entity_layers_bound_consumer_candidates_to_raw_limit(tmp_path: Path) -> None:
    """Fixture #14: four layer docs for one entity plus four other entities inside the raw top-8
    must yield raw consumer candidates == 8, a collapsed view of five distinct entities, and no
    candidate introduced beyond raw position 8."""
    entity_dir = tmp_path / ".knowledge/entities/hub"
    entity_dir.mkdir(parents=True)
    (entity_dir / "_entity.yaml").write_text(
        yaml.safe_dump({"id": "hub", "type": "subsystem", "owner": "team-x"}, sort_keys=False), encoding="utf-8"
    )
    query_terms = "shared token widget process record"
    for layer in ("architecture", "operations", "integration", "pattern"):
        src = tmp_path / "src" / f"hub_{layer}.py"
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_text("x = 1\n", encoding="utf-8")
        metadata = {
            "id": f"hub-{layer}",
            "entity": "hub",
            "layer": layer,
            "title": f"Hub {layer}",
            "source_of_truth": [f"src/hub_{layer}.py"],
            "last_verified": "2026-01-01",
        }
        frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
        (entity_dir / f"{layer}.md").write_text(f"---\n{frontmatter}---\n\n{query_terms}\n", encoding="utf-8")
    for i in range(4):
        _write_entity(tmp_path, f"other{i}", body=f"{query_terms} other variant {i}.\n")

    fixture = _write_fixture(tmp_path, [{"query": query_terms, "expected": "hub", "limit": 8}])
    payload = _run(tmp_path, fixture)
    consumer = payload["cases"][0]["consumer"]
    assert len(consumer["raw_candidates"]) == 8
    assert len(consumer["collapsed_entities"]) == 5
    raw_ids = {c["id"] for c in consumer["raw_candidates"]}
    full_raw_ids = {c["id"] for c in payload["cases"][0]["full_ranking"]["raw_candidates"][:8]}
    assert raw_ids == full_raw_ids  # collapsing never introduces a candidate beyond raw position 8


def test_raw_entity_identity_matching_recognizes_entity_attribute(tmp_path: Path) -> None:
    """Fix #2: an `expected` identity of `conversations` must match a raw node whose `id` is
    `conversations-integration` but whose `entity` attribute is `conversations`, without requiring
    every layer-document id to be enumerated in the fixture."""
    _write_entity(tmp_path, "conversations", body="Conversation integration handling detail.\n")
    fixture = _write_fixture(tmp_path, [{"query": "conversation integration handling", "expected": "conversations"}])

    payload = _run(tmp_path, fixture)
    expected = payload["cases"][0]["expected"][0]
    assert expected["matched_as"] == "entity_id"
    assert expected["raw_node_id"] == "conversations-integration"
    assert expected["entity_id"] == "conversations"
    assert expected["consumer"]["visible"] is True
