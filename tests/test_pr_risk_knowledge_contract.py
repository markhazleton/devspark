# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for knowledge-derived criticality in the PR risk digest."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
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
    (tmp_path / ".knowledge" / "index.json").write_text("[]", encoding="utf-8")
    assert pr_risk.load_knowledge(tmp_path) is None


def _write_knowledge_doc(repo: Path, claimed: str = "src/known/**") -> None:
    doc = repo / ".knowledge" / "architecture" / "overview.md"
    doc.parent.mkdir(parents=True)
    doc.write_text(f"---\nappliesTo:\n  - {claimed}\n---\n# Overview\n", encoding="utf-8")


def _write_index(repo: Path, claimed: str = "src/known/**", at: str = "2026-01-01T00:00:00Z") -> None:
    index = {"generated": {"at": at}, "nodes": [{"id": "a", "appliesTo": [claimed]}], "entities": []}
    (repo / ".knowledge").mkdir(exist_ok=True)
    (repo / ".knowledge" / "index.json").write_text(json.dumps(index), encoding="utf-8")


def _unreachable_engine(_repo_root):
    raise ValueError("boom")


def test_digest_says_whether_and_where_knowledge_was_applied():
    none = pr_risk.build_digest(["src/a.py"])
    assert none["knowledge"] == {"status": "absent", "source": "none", "claim_count": 0}
    provided = pr_risk.build_digest(["src/a.py"], knowledge=KNOWLEDGE)
    assert provided["knowledge"] == {"status": "applied", "source": "provided", "claim_count": 3}
    prebuilt = pr_risk.build_digest(
        ["src/a.py"], knowledge={**KNOWLEDGE, "source": "index", "generated_at": "2026-01-01T00:00:00Z"}
    )
    assert prebuilt["knowledge"] == {
        "status": "applied",
        "source": "index",
        "claim_count": 3,
        "generated_at": "2026-01-01T00:00:00Z",
    }
    unreadable = pr_risk.build_digest(["src/a.py"], knowledge={"claims": [], "status": "unreadable", "detail": "why"})
    assert unreadable["knowledge"]["status"] == "unreadable"
    assert unreadable["knowledge"]["detail"] == "why"


def test_knowledge_without_claims_applies_nothing_instead_of_flagging_every_file():
    digest = pr_risk.build_digest(["src/other/x.py", "tests/test_x.py"], knowledge={"claims": [], "entity_types": {}})
    assert digest["flags"]["unmapped_production"] is False
    assert digest["knowledge"]["status"] == "absent"


def test_resolve_knowledge_builds_live_claims_and_writes_nothing(tmp_path):
    _write_knowledge_doc(tmp_path)
    before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    resolved = pr_risk.resolve_knowledge(tmp_path)
    assert resolved["source"] == "live"
    assert ("src/known/**", None) in resolved["claims"]
    assert sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*")) == before


def test_live_claims_win_over_a_stale_prebuilt_index(tmp_path):
    _write_knowledge_doc(tmp_path, "src/known/**")
    _write_index(tmp_path, "src/old/**")
    resolved = pr_risk.resolve_knowledge(tmp_path)
    assert resolved["source"] == "live"
    assert [pattern for pattern, _ in resolved["claims"]] == ["src/known/**"]


def test_failed_live_build_falls_back_to_the_prebuilt_index_and_says_so(tmp_path, monkeypatch):
    _write_index(tmp_path)
    monkeypatch.setattr(pr_risk, "_live_index", _unreachable_engine)
    resolved = pr_risk.resolve_knowledge(tmp_path)
    assert resolved["source"] == "index"
    assert resolved["generated_at"] == "2026-01-01T00:00:00Z"
    assert "live build failed (ValueError)" in resolved["detail"]
    digest = pr_risk.build_digest(["src/a.py"], knowledge=resolved)
    assert digest["knowledge"]["status"] == "applied"
    assert "boom" not in json.dumps(digest["knowledge"])


def test_knowledge_that_cannot_be_read_is_reported_not_silently_dropped(tmp_path, monkeypatch):
    (tmp_path / ".knowledge").mkdir()
    monkeypatch.setattr(pr_risk, "_live_index", _unreachable_engine)
    digest = pr_risk.build_digest(["src/other/x.py"], knowledge=pr_risk.resolve_knowledge(tmp_path))
    assert digest["knowledge"]["status"] == "unreadable"
    assert digest["knowledge"]["source"] == "none"
    assert digest["flags"]["unmapped_production"] is False


def test_repo_without_knowledge_or_claims_is_absent(tmp_path):
    assert pr_risk.build_digest(["src/a.py"], knowledge=pr_risk.resolve_knowledge(tmp_path))["knowledge"]["status"] == "absent"
    (tmp_path / ".knowledge").mkdir()
    resolved = pr_risk.resolve_knowledge(tmp_path)
    assert resolved["source"] == "live"
    assert pr_risk.build_digest(["src/a.py"], knowledge=resolved)["knowledge"]["status"] == "absent"


def test_cli_applies_live_knowledge_without_a_prebuilt_index(tmp_path):
    _write_knowledge_doc(tmp_path)
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "pr-risk.py"), "--repo-root", str(tmp_path), "src/known/a.py", "src/other/b.py"],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    digest = json.loads(result.stdout)
    assert digest["knowledge"] == {"status": "applied", "source": "live", "claim_count": 1}
    assert digest["flags"]["unmapped_production"] is True
    assert not (tmp_path / ".knowledge" / "index.json").exists()
