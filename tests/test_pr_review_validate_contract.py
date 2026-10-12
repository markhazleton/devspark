# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for the deterministic PR review validator."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "scripts" / "pr-review-validate.py"
_spec = importlib.util.spec_from_file_location("pr_review_validate", ENGINE)
validator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validator)


def _review(*, high=1, rec="REQUEST CHANGES", status="🔴 Open", max_sev="high", rating="medium",
            escalated="false", immediate="- [ ] **H-01** `a.py:1` — x") -> str:
    rows = f"| H-01 | {status} | P | a.py:1 | x | y |\n" if high else ""
    return f"""---
pr: 7
devspark_version: "8.2.0"
reviewed_commit: abc1234
revision: 1
findings:
  critical: 0
  high: {high}
  medium: 0
  low: 0
  con: 0
max_severity: {max_sev}
risk_rating: {rating}
risk_score: 4
risk_escalated: {escalated}
---

# Pull Request Review: T

## Action Items

### Immediate Actions (Blocking — must resolve before merge)

{immediate}

### Recommended Improvements

## Findings Detail

### High Priority Issues

| ID | Status | Principle | File:Line | Issue | Fix |
|----|--------|-----------|-----------|-------|-----|
{rows}
## Approval Decision

**Recommendation**: {rec} — reason
"""


def _codes(text: str, digest: dict | None = None) -> set[str]:
    return {i["code"] for i in validator.validate(text, digest)}


def test_consistent_review_has_no_issues():
    assert _codes(_review()) == set()


def test_missing_frontmatter_keys_are_reported():
    assert _codes("# no frontmatter") == {"frontmatter-missing"}


def test_frontmatter_counts_must_match_body_on_first_revision():
    assert "findings-count" in _codes(_review().replace("high: 1", "high: 3"))


def test_max_severity_must_follow_counts():
    assert "max-severity" in _codes(_review(max_sev="critical"))


def test_request_changes_needs_an_open_blocker():
    assert "rec-without-blocker" in _codes(_review(status="✅ Resolved", immediate="None found."))


def test_approve_with_open_blocker_is_rejected():
    assert "approve-with-blocker" in _codes(_review(rec="APPROVE"))


def test_immediate_actions_must_agree_with_open_blockers():
    assert "immediate-actions" in _codes(_review(immediate="None found."))


def test_risk_rating_cannot_be_lowered_below_the_computed_floor():
    digest = {"rating": "high", "report_form": "full", "tables": {"changed_files": "| File | Tier |"}}
    codes = _codes(_review(rating="medium") + "\n| File | Tier |\n", digest)
    assert "risk-lowered" in codes


def test_escalation_flag_must_match_rating_difference():
    digest = {"rating": "low", "report_form": "short", "tables": {"changed_files": "| File |"}}
    assert "risk-escalation-flag" in _codes(_review(rating="medium"), digest)
    assert "risk-escalation-flag" not in _codes(_review(rating="medium", escalated="true"), digest)


def test_short_form_rejects_changed_files_section_and_full_form_requires_the_table():
    short = {"rating": "low", "report_form": "short", "tables": {"changed_files": "| File |"}}
    assert "form-bloat" in _codes(_review(rating="low") + "\n## Changed Files\n", short)
    standard = {"rating": "medium", "report_form": "standard", "tables": {"changed_files": "| File | Tier |"}}
    assert "table-not-pasted" in _codes(_review(), standard)


def test_cli_exit_code_and_json(tmp_path):
    bad = tmp_path / "pr-7.md"
    bad.write_text(_review(rec="APPROVE"), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ENGINE), str(bad)], capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 1
    assert json.loads(result.stdout)["ok"] is False
    good = tmp_path / "pr-8.md"
    good.write_text(_review(), encoding="utf-8")
    ok = subprocess.run([sys.executable, str(ENGINE), str(good)], capture_output=True, text=True, timeout=30)
    assert ok.returncode == 0


def test_review_template_runs_the_validator_after_writing():
    text = (ROOT / "templates/commands/pr-review.md").read_text(encoding="utf-8")
    assert "pr-review-validate.py" in text
