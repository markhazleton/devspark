# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for the deterministic PR risk digest."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "scripts" / "pr-risk.py"

_spec = importlib.util.spec_from_file_location("pr_risk", ENGINE)
pr_risk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pr_risk)


def _tiers(digest: dict) -> dict[str, str]:
    return {f["path"]: f["tier"] for f in digest["files"]}


def test_tiers_follow_path_patterns():
    digest = pr_risk.build_digest(
        [
            "src/Auth/TokenService.cs",
            "src/orders/OrderCalculator.cs",
            "tests/test_orders.py",
            "docs/guide.md",
            "db/migrations/001_init.sql",
        ]
    )
    assert _tiers(digest) == {
        "src/Auth/TokenService.cs": "P0",
        "src/orders/OrderCalculator.cs": "P1",
        "tests/test_orders.py": "P2",
        "docs/guide.md": "P3",
        "db/migrations/001_init.sql": "P0",
    }


def test_flags_and_rating_are_auditable():
    digest = pr_risk.build_digest(["src/Auth/TokenService.cs", "db/migrations/001_init.sql"])
    assert digest["flags"]["auth_or_security_path"] is True
    assert digest["flags"]["schema_or_migration"] is True
    assert digest["flags"]["production_without_tests"] is True
    assert digest["rating"] == "high"
    assert digest["risk_score"] == sum(f["points"] for f in digest["factors"])


def test_docs_only_change_is_low_risk():
    digest = pr_risk.build_digest(["README.md", "docs/a.md"])
    assert digest["rating"] == "low"
    assert digest["flags"]["production_without_tests"] is False


def test_production_change_with_tests_clears_flag():
    digest = pr_risk.build_digest(["src/orders/OrderCalculator.cs", "tests/test_orders.py"])
    assert digest["flags"]["production_without_tests"] is False


def test_large_diff_flag_uses_line_totals():
    digest = pr_risk.build_digest(["src/a.py"], lines_added=1700, lines_deleted=400)
    assert digest["flags"]["large_diff"] is True


def test_many_non_doc_files_is_large_but_docs_are_not():
    code = [f"src/m{i}.py" for i in range(25)]
    docs = [f"docs/d{i}.md" for i in range(60)]
    assert pr_risk.build_digest(code)["flags"]["large_diff"] is True
    assert pr_risk.build_digest(docs)["flags"]["large_diff"] is False


def test_repo_override_takes_precedence(tmp_path):
    work = tmp_path / ".devspark.work"
    work.mkdir()
    (work / "devspark.json").write_text(
        json.dumps({"pr_risk": {"tier_patterns": {"P0": ["^src/utils/legacy_auth"]}}}),
        encoding="utf-8",
    )
    overrides = pr_risk._load_overrides(tmp_path)
    digest = pr_risk.build_digest(["src/utils/legacy_auth.py"], overrides)
    assert digest["files"][0]["tier"] == "P0"


def test_invalid_override_pattern_is_ignored(tmp_path):
    work = tmp_path / ".devspark.work"
    work.mkdir()
    (work / "devspark.json").write_text(
        json.dumps({"pr_risk": {"tier_patterns": {"P0": ["(unclosed"]}}}), encoding="utf-8"
    )
    assert pr_risk._load_overrides(tmp_path) == []


def test_cli_emits_json():
    result = subprocess.run(
        [sys.executable, str(ENGINE), "--repo-root", str(ROOT), "src/Auth/x.cs"],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    assert json.loads(result.stdout)["tier_counts"]["P0"] == 1


def test_both_context_twins_emit_risk_from_shared_helper():
    ps = (ROOT / "scripts/powershell/get-pr-context.ps1").read_text(encoding="utf-8")
    sh = (ROOT / "scripts/bash/get-pr-context.sh").read_text(encoding="utf-8")
    assert "pr-risk.py" in ps and "pr-risk.py" in sh
    assert "risk = $riskDigest" in ps
    assert '"risk": $risk_json' in sh


def test_review_template_declares_machine_readable_frontmatter():
    text = (ROOT / "templates/commands/pr-review.md").read_text(encoding="utf-8")
    block = text.split("#### Report Structure", 1)[1].split("# Pull Request Review:", 1)[0]
    for key in ("pr:", "devspark_version:", "reviewed_commit:", "revision:", "findings:", "max_severity:", "risk_rating:", "risk_score:", "risk_escalated:"):
        assert key in block, key


def test_both_context_twins_emit_devspark_version():
    ps = (ROOT / "scripts/powershell/get-pr-context.ps1").read_text(encoding="utf-8")
    sh = (ROOT / "scripts/bash/get-pr-context.sh").read_text(encoding="utf-8")
    assert "DEVSPARK_VERSION = (Get-DevSparkVersion" in ps
    assert '"DEVSPARK_VERSION": $(get_devspark_version' in sh


def test_report_form_follows_rating():
    assert pr_risk.build_digest(["README.md"])["report_form"] == "short"
    assert pr_risk.build_digest(["src/Auth/x.cs", "db/migrations/1.sql"])["report_form"] == "full"


def test_tables_render_stats_and_cap_rows():
    stats = {"src/a.py": {"added": 3, "deleted": 1, "change": "Added"}}
    digest = pr_risk.build_digest(["src/a.py", "tests/test_a.py"], stats=stats)
    assert "| src/a.py | P1 | +3 -1 | Added |" in digest["tables"]["changed_files"]
    assert "tests/test_a.py" in digest["tables"]["test_files"]
    many = pr_risk.build_digest([f"docs/d{i}.md" for i in range(60)])
    assert "20 more P2/P3 files not listed" in many["tables"]["changed_files"]
    assert pr_risk.build_digest(["src/a.py"])["tables"]["test_files"] == "No test files changed in this PR."


def test_git_stats_reads_numstat_and_change_type(tmp_path):
    def git(*args):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, timeout=30)

    git("init", "-q")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "Test User")
    (tmp_path / "old.py").write_text("a\nb\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-qm", "base")
    base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path, capture_output=True, text=True, timeout=30).stdout.strip()
    (tmp_path / "old.py").write_text("a\n", encoding="utf-8")
    (tmp_path / "new.py").write_text("x\ny\nz\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-qm", "change")
    stats = pr_risk.git_stats(tmp_path, f"{base}...HEAD")
    assert stats["new.py"] == {"added": 3, "deleted": 0, "change": "Added"}
    assert stats["old.py"] == {"added": 0, "deleted": 1, "change": "Modified"}
    assert pr_risk.git_stats(tmp_path, "nope...HEAD") == {}


def test_both_context_twins_pass_the_git_range_and_full_file_list():
    ps = (ROOT / "scripts/powershell/get-pr-context.ps1").read_text(encoding="utf-8")
    sh = (ROOT / "scripts/bash/get-pr-context.sh").read_text(encoding="utf-8")
    assert "'--range'" in ps and "@allFilesChanged" in ps
    assert "--range" in sh and "all_files_json" in sh


