# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for the PR risk calibration harness."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "scripts" / "pr-risk-calibrate.py"

_spec = importlib.util.spec_from_file_location("pr_risk_calibrate", ENGINE)
calibrate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(calibrate)


def _review(version: str, sev: str, rating: str) -> str:
    counts = {k: 0 for k in ("critical", "high", "medium", "low", "con")}
    if sev != "none":
        counts[sev] = 1
    body = "\n".join(f"  {k}: {v}" for k, v in counts.items())
    return (
        f'---\npr: 1\ndevspark_version: "{version}"\nfindings:\n{body}\n'
        f"max_severity: {sev}\nrisk_rating: {rating}\n---\n\n# Review\n"
    )


def _write(tmp_path: Path, name: str, text: str) -> None:
    reviews = tmp_path / ".devspark.work" / "pr-review"
    reviews.mkdir(parents=True, exist_ok=True)
    (reviews / name).write_text(text, encoding="utf-8")


def test_groups_by_version_and_computes_recall_and_over_rating(tmp_path):
    _write(tmp_path, "pr-1.md", _review("8.3.0", "high", "high"))
    _write(tmp_path, "pr-2.md", _review("8.3.0", "critical", "low"))
    _write(tmp_path, "pr-3.md", _review("8.3.0", "none", "high"))
    _write(tmp_path, "pr-4.md", _review("8.4.0", "high", "medium"))

    summary = calibrate.summarize(
        calibrate.collect(tmp_path, tmp_path / ".devspark.work" / "pr-review", "origin/main", None)
    )
    old, new = summary["per_version"]["8.3.0"], summary["per_version"]["8.4.0"]
    assert old["recall"] == 0.5 and old["missed"] == ["2"] and old["over_rating"] == 1.0
    assert new["recall"] == 1.0


def test_legacy_review_without_frontmatter_reads_revision_log():
    text = (
        "| Rev | Commit | Date | Critical | High | Medium | Low | CON |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| 1 | abc1234 | d | 0 | 2 | 1 | 0 | 0 |\n"
    )
    counts = calibrate.legacy_counts(text)
    assert counts["high"] == 2 and calibrate.max_severity(counts) == "high"


def test_legacy_commit_tolerates_backticks_and_newline():
    assert calibrate.legacy_commit("**Reviewed commit**: \n`74a4478babecfd50`") == "74a4478babecfd50"


def test_unreadable_reviews_are_skipped_not_miscounted(tmp_path):
    _write(tmp_path, "pr-9.md", "# no severity data\n")
    rows = calibrate.collect(tmp_path, tmp_path / ".devspark.work" / "pr-review", "origin/main", None)
    assert calibrate.summarize(rows)["skipped"] == {"no-severity": 1}


def test_cli_min_recall_gate(tmp_path):
    _write(tmp_path, "pr-2.md", _review("8.3.0", "critical", "low"))
    run = lambda *extra: subprocess.run(  # noqa: E731
        [sys.executable, str(ENGINE), "--repo-root", str(tmp_path), "--json", *extra],
        capture_output=True, text=True, timeout=30,
    )
    assert run().returncode == 0
    failing = run("--min-recall", "0.9")
    assert failing.returncode == 1
    assert json.loads(failing.stdout)["per_version"]["8.3.0"]["recall"] == 0.0
