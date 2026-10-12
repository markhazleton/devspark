# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for `/devspark.context-projection` (DevSpark 7.7 Context Projection v1).

Covers:
1. Command wiring: command template, agent/prompt shims, atomic backward-compat shim, and
   dual-language wrapper scripts all resolve to `scripts/context-projection.py`.
2. Traversal behavior/schema per the Section 18 fixture matrix: simple entity relation,
   governance constraint (both directions), two-hop projection (hop-bounded), cycle safety,
   multi-path provenance, negative isolation, discovery-candidate isolation (advisory
   `discover-knowledge` findings are never traversable), candidate-limit truncation, and
   determinism.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "context-projection.py"
COMMAND_DOC = ROOT / "templates" / "commands" / "context-projection.md"
SKILL = ROOT / ".github" / "skills" / "devspark-context-projection" / "SKILL.md"
CONSUMER_SKILL = ROOT / "templates" / "consumer-skills" / "devspark-context-projection" / "SKILL.md"
BASH_WRAPPER = ROOT / "scripts" / "bash" / "context-projection.sh"
PS1_WRAPPER = ROOT / "scripts" / "powershell" / "context-projection.ps1"


# --- Command wiring ---------------------------------------------------------------------


def test_command_template_exists_and_declares_wrapper_scripts() -> None:
    text = COMMAND_DOC.read_text(encoding="utf-8")
    assert "sh: .devspark/scripts/bash/context-projection.sh $ARGUMENTS --json" in text
    assert "ps: .devspark/scripts/powershell/context-projection.ps1 $ARGUMENTS -Json" in text


def test_skill_resolves_to_command_template() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "name: devspark-context-projection" in text
    assert "templates/commands/context-projection.md" in text


def test_consumer_skill_resolves_through_the_customization_chain() -> None:
    text = CONSUMER_SKILL.read_text(encoding="utf-8")
    assert "name: devspark-context-projection" in text
    assert ".devspark/defaults/commands/devspark.context-projection.md" in text


def test_wrapper_scripts_exist_and_are_thin() -> None:
    assert BASH_WRAPPER.is_file()
    assert PS1_WRAPPER.is_file()
    assert "context-projection.py" in BASH_WRAPPER.read_text(encoding="utf-8")
    assert "context-projection.py" in PS1_WRAPPER.read_text(encoding="utf-8")


# --- Fixture helpers ---------------------------------------------------------------------


def _init_git_repo(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True, timeout=30)


def _write_entity(
    repo: Path,
    entity_id: str,
    *,
    relations: list[dict] | None = None,
    constrained_by: list[str] | None = None,
    source_of_truth: list[str] | None = None,
) -> None:
    entity_dir = repo / ".knowledge" / "entities" / entity_id
    entity_dir.mkdir(parents=True)
    data: dict = {"id": entity_id, "type": "subsystem", "owner": "team-x"}
    if relations:
        data["relations"] = relations
    if constrained_by:
        data["constrained_by"] = constrained_by
    (entity_dir / "_entity.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    source_of_truth = source_of_truth or [f"src/{entity_id}.py"]
    for source in source_of_truth:
        source_path = repo / source
        source_path.parent.mkdir(parents=True, exist_ok=True)
        if not source_path.exists():
            source_path.write_text("def run():\n    pass\n", encoding="utf-8")
    metadata = {
        "id": f"{entity_id}-architecture",
        "entity": entity_id,
        "layer": "architecture",
        "title": entity_id,
        "source_of_truth": source_of_truth,
        "last_verified": "2026-01-01",
    }
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
    (entity_dir / "architecture.md").write_text(f"---\n{frontmatter}---\n\nBody.\n", encoding="utf-8")


def _write_governance_decision(
    repo: Path, decision_id: str, *, constrains: list[str], applies_to: list[str] | None = None
) -> None:
    decision_dir = repo / ".knowledge" / "governance" / "decisions"
    decision_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "id": decision_id,
        "type": "governance-decision",
        "title": decision_id,
        "constrains": constrains,
    }
    if applies_to:
        metadata["appliesTo"] = applies_to
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
    (decision_dir / f"{decision_id}.md").write_text(f"---\n{frontmatter}---\n\nDecision body.\n", encoding="utf-8")


def _stamp_constrained_by(repo: Path, entity_id: str, decision_ids: list[str]) -> None:
    entity_yaml = repo / ".knowledge/entities" / entity_id / "_entity.yaml"
    data = yaml.safe_load(entity_yaml.read_text(encoding="utf-8"))
    data["constrained_by"] = decision_ids
    entity_yaml.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _run(repo: Path, *extra_args: str) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(repo), "--json", *extra_args],
        text=True, capture_output=True, timeout=60,
    )
    return result.returncode, json.loads(result.stdout)


def _ids(payload: dict) -> set[str]:
    return {c["id"] for c in payload["CANDIDATES"]}


def _distance(payload: dict, node_id: str) -> int | None:
    for candidate in payload["CANDIDATES"]:
        if candidate["id"] == node_id:
            return candidate["distance"]
    return None


# --- Behavior: Section 18 fixture matrix --------------------------------------------------


def test_simple_entity_relation_projects_target(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write_entity(repo, "a")
    _write_entity(repo, "b")
    (repo / ".knowledge/entities/a/_entity.yaml").write_text(
        yaml.safe_dump(
            {"id": "a", "type": "subsystem", "owner": "team-x", "relations": [{"object": "b", "predicate": "relates-to"}]},
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    _init_git_repo(repo)

    code, payload = _run(repo, "--seed", "a")
    assert code == 0
    assert "b" in _ids(payload)
    assert _distance(payload, "b") == 1
    b_reason = next(c for c in payload["CANDIDATES"] if c["id"] == "b")["reasons"][0]
    assert b_reason == {"type": "graph_relation", "seed": "a", "via": "a", "relation": "relates-to", "distance": 1}


def test_governance_constraint_projects_decision(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write_entity(repo, "disconnect")
    _write_governance_decision(repo, "adr-runtime-config-hard-fail-startup", constrains=["disconnect"], applies_to=["src/disconnect.py"])
    _stamp_constrained_by(repo, "disconnect", ["adr-runtime-config-hard-fail-startup"])
    _init_git_repo(repo)

    code, payload = _run(repo, "--seed", "disconnect")
    assert code == 0
    assert "adr-runtime-config-hard-fail-startup" in _ids(payload)
    assert _distance(payload, "adr-runtime-config-hard-fail-startup") == 1
    reason = next(c for c in payload["CANDIDATES"] if c["id"] == "adr-runtime-config-hard-fail-startup")["reasons"][0]
    assert reason["type"] == "governance_constraint"
    assert reason["relation"] == "constrained_by"
    governance_ids = payload["CHANNELS"]["governance"]
    assert governance_ids == ["adr-runtime-config-hard-fail-startup"]


def test_reciprocal_governance_direction_projects_entity(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write_entity(repo, "disconnect")
    _write_governance_decision(repo, "adr-runtime-config-hard-fail-startup", constrains=["disconnect"], applies_to=["src/disconnect.py"])
    _stamp_constrained_by(repo, "disconnect", ["adr-runtime-config-hard-fail-startup"])
    _init_git_repo(repo)

    code, payload = _run(repo, "--seed", "adr-runtime-config-hard-fail-startup")
    assert code == 0
    assert "disconnect" in _ids(payload)
    reason = next(c for c in payload["CANDIDATES"] if c["id"] == "disconnect")["reasons"][0]
    assert reason["relation"] == "constrains"
    assert payload["CHANNELS"]["entity"] == ["disconnect"]


def test_two_hop_projection_respects_max_hops(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write_entity(repo, "a", relations=[{"object": "b", "predicate": "relates-to"}])
    _write_entity(repo, "b", relations=[{"object": "c", "predicate": "relates-to"}])
    _write_entity(repo, "c")
    _init_git_repo(repo)

    _, two_hop = _run(repo, "--seed", "a", "--max-hops", "2")
    assert _ids(two_hop) >= {"b", "c"}
    assert _distance(two_hop, "b") == 1
    assert _distance(two_hop, "c") == 2

    _, one_hop = _run(repo, "--seed", "a", "--max-hops", "1")
    assert "b" in _ids(one_hop)
    assert "c" not in _ids(one_hop)


def test_cycle_does_not_duplicate_or_infinite_loop(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write_entity(repo, "a", relations=[{"object": "b", "predicate": "relates-to"}])
    _write_entity(repo, "b", relations=[{"object": "a", "predicate": "relates-to"}])
    _init_git_repo(repo)

    code, payload = _run(repo, "--seed", "a", "--max-hops", "5")
    assert code == 0
    ids = [c["id"] for c in payload["CANDIDATES"]]
    assert ids.count("a") == 1
    assert ids.count("b") == 1
    assert _distance(payload, "a") == 0
    assert _distance(payload, "b") == 1


def test_multiple_paths_produce_single_node_with_both_provenances(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write_entity(repo, "a", relations=[{"object": "b", "predicate": "relates-to"}, {"object": "c", "predicate": "relates-to"}])
    _write_entity(repo, "b", relations=[{"object": "d", "predicate": "relates-to"}])
    _write_entity(repo, "c", relations=[{"object": "d", "predicate": "relates-to"}])
    _write_entity(repo, "d")
    _init_git_repo(repo)

    code, payload = _run(repo, "--seed", "a", "--max-hops", "2")
    assert code == 0
    d_matches = [c for c in payload["CANDIDATES"] if c["id"] == "d"]
    assert len(d_matches) == 1
    assert d_matches[0]["distance"] == 2
    vias = {reason["via"] for reason in d_matches[0]["reasons"]}
    assert vias == {"b", "c"}


def test_negative_isolation_unrelated_entity_not_present(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write_entity(repo, "a", relations=[{"object": "b", "predicate": "relates-to"}])
    _write_entity(repo, "b")
    _write_entity(repo, "x")  # unrelated, no edges to/from a or b
    _init_git_repo(repo)

    _, payload = _run(repo, "--seed", "a")
    assert "x" not in _ids(payload)


def test_unaccepted_discovery_governance_candidate_is_not_traversable(tmp_path: Path) -> None:
    """A `discover-knowledge` `governance-relationship-candidate` (shared source path, entity NOT
    listed in the decision's `constrains`) is advisory only -- Context Projection must never
    traverse it, since it never becomes an edge in the generated index (Section 4/19)."""
    repo = tmp_path / "repo"
    _write_entity(repo, "checkout")
    _write_governance_decision(repo, "payments-data-retention", constrains=["billing"], applies_to=["src/checkout.py"])
    _write_entity(repo, "billing")
    _stamp_constrained_by(repo, "billing", ["payments-data-retention"])
    _init_git_repo(repo)

    _, payload = _run(repo, "--seed", "checkout")
    assert "payments-data-retention" not in _ids(payload)


def test_candidate_limit_triggers_deterministic_truncation_reporting(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    relations = [{"object": f"leaf-{i}", "predicate": "relates-to"} for i in range(20)]
    _write_entity(repo, "hub", relations=relations)
    for i in range(20):
        _write_entity(repo, f"leaf-{i}")
    _init_git_repo(repo)

    code, payload = _run(repo, "--seed", "hub", "--max-candidates", "5")
    assert code == 0
    assert payload["GUARDRAILS"]["truncated"] is True
    assert payload["GUARDRAILS"]["max_candidates"] == 5
    # 20 related entities, plus the layer document each of the 21 entities is composed of.
    assert payload["GUARDRAILS"]["total_unique_candidates"] == 41
    assert payload["GUARDRAILS"]["truncation_reason"]
    non_seed_candidates = [c for c in payload["CANDIDATES"] if c["id"] != "hub"]
    assert len(non_seed_candidates) == 5


def test_determinism_across_repeated_runs(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write_entity(repo, "a", relations=[{"object": "b", "predicate": "relates-to"}, {"object": "c", "predicate": "relates-to"}])
    _write_entity(repo, "b", relations=[{"object": "d", "predicate": "relates-to"}])
    _write_entity(repo, "c", relations=[{"object": "d", "predicate": "relates-to"}])
    _write_entity(repo, "d")
    _init_git_repo(repo)

    _, first = _run(repo, "--seed", "a", "--max-hops", "2")
    _, second = _run(repo, "--seed", "a", "--max-hops", "2")
    assert first == second


def test_unresolved_seed_is_reported_not_silently_dropped(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write_entity(repo, "a")
    _init_git_repo(repo)

    code, payload = _run(repo, "--seed", "a", "--seed", "does-not-exist")
    assert code == 0
    assert payload["SEEDS"] == ["a"]
    assert payload["UNRESOLVED_SEEDS"] == ["does-not-exist"]


def test_fan_out_audit_reports_per_entity_and_summary(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write_entity(repo, "a", relations=[{"object": "b", "predicate": "relates-to"}])
    _write_entity(repo, "b")
    _init_git_repo(repo)

    code, payload = _run(repo, "--audit-fan-out")
    assert code == 0
    entities_audited = {item["entity"] for item in payload["FAN_OUT_AUDIT"]}
    assert entities_audited == {"a", "b"}
    a_audit = next(item for item in payload["FAN_OUT_AUDIT"] if item["entity"] == "a")
    # `b` via the authored relation, plus `a`'s own layer document via composition.
    assert a_audit["hop1_candidate_count"] == 2
    assert payload["SUMMARY"]["entity_count"] == 2


def test_bash_wrapper_reaches_context_projection_py(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write_entity(repo, "a", relations=[{"object": "b", "predicate": "relates-to"}])
    _write_entity(repo, "b")
    _init_git_repo(repo)

    git_bash = r"C:\Program Files\Git\bin\bash.exe"
    bash = git_bash if Path(git_bash).exists() else shutil.which("bash")
    if bash is None:
        pytest.skip("bash not available")
    result = subprocess.run(
        [bash, str(BASH_WRAPPER), "--repo-root", str(repo), "--seed", "a", "--json"],
        capture_output=True, text=True, timeout=60,
    )
    payload = json.loads(result.stdout)
    assert "b" in {c["id"] for c in payload["CANDIDATES"]}
