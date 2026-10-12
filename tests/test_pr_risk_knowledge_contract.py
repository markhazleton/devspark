# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for knowledge-derived criticality in the PR risk digest."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("pr_risk", ROOT / "scripts" / "pr-risk.py")
pr_risk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pr_risk)

KNOWLEDGE = {
    "claims": [("src/rules/**", "pricing"), ("src/cli/**", "tooling-entity"), ("src/gateway/", "billing-api")],
    "entity_types": {"pricing": "domain", "tooling-entity": "tooling", "billing-api": "integration"},
}


def _tier(digest: dict, path: str) -> dict:
    return next(f for f in digest["files"] if f["path"] == path)


def test_domain_and_integration_ownership_promotes_default_tier_to_p0():
    digest = pr_risk.build_digest(
        ["src/rules/discount.py", "src/gateway/client.py", "src/cli/run.py"], knowledge=KNOWLEDGE
    )
    assert _tier(digest, "src/rules/discount.py")["tier"] == "P0"
    assert _tier(digest, "src/rules/discount.py")["promoted_by"] == "pricing"
    assert _tier(digest, "src/gateway/client.py")["tier"] == "P0"
    assert _tier(digest, "src/cli/run.py")["tier"] == "P1"
    p0 = next(f for f in digest["factors"] if f["factor"] == "p0_files")
    assert p0["from_knowledge"] == 2


def test_promotion_never_touches_tests_docs_or_explicit_overrides():
    digest = pr_risk.build_digest(
        ["src/rules/test_discount.py", "src/rules/README.md", "src/rules/legacy.py"],
        overrides=[("P2", r"legacy")],
        knowledge=KNOWLEDGE,
    )
    assert {f["path"]: f["tier"] for f in digest["files"]} == {
        "src/rules/test_discount.py": "P2",
        "src/rules/README.md": "P3",
        "src/rules/legacy.py": "P2",
    }


def test_unclaimed_production_file_adds_a_factor_only_when_knowledge_exists():
    with_index = pr_risk.build_digest(["src/other/x.py", "tests/test_x.py"], knowledge=KNOWLEDGE)
    assert with_index["flags"]["unmapped_production"] is True
    assert any(f["factor"] == "unmapped_production" for f in with_index["factors"])
    without_index = pr_risk.build_digest(["src/other/x.py", "tests/test_x.py"])
    assert without_index["flags"]["unmapped_production"] is False


def test_load_knowledge_reads_claims_and_entity_types(tmp_path):
    (tmp_path / ".knowledge").mkdir()
    index = {
        "nodes": [
            {"id": "a", "entity": "pricing", "source_of_truth": ["src/rules/**", {"path": "src/x.py"}]},
            {"id": "b", "appliesTo": ["docs/**"]},
        ],
        "entities": [{"id": "pricing", "type": "domain"}],
    }
    (tmp_path / ".knowledge" / "index.json").write_text(json.dumps(index), encoding="utf-8")
    loaded = pr_risk.load_knowledge(tmp_path)
    assert ("src/rules/**", "pricing") in loaded["claims"]
    assert ("src/x.py", "pricing") in loaded["claims"]
    assert ("docs/**", None) in loaded["claims"]
    assert loaded["entity_types"] == {"pricing": "domain"}


def test_load_knowledge_is_none_without_a_readable_index(tmp_path):
    assert pr_risk.load_knowledge(tmp_path) is None
    (tmp_path / ".knowledge").mkdir()
    (tmp_path / ".knowledge" / "index.json").write_text("{ bad", encoding="utf-8")
    assert pr_risk.load_knowledge(tmp_path) is None
