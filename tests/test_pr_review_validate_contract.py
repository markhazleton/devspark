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
STATE_ENGINE = ROOT / "scripts" / "pr-review-state.py"
MODERN_FIXTURE = ROOT / "tests" / "fixtures" / "pr-review-state" / "modern-valid.md"
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


def test_validator_checks_all_derived_views_for_modern_records(tmp_path):
    review = tmp_path / "pr-7.md"
    review.write_bytes(MODERN_FIXTURE.read_bytes())
    inspect = subprocess.run(
        [sys.executable, str(STATE_ENGINE), "inspect", str(review), "--json"],
        capture_output=True, text=True, timeout=30,
    )
    digest = json.loads(inspect.stdout)["digest"]
    rendered = subprocess.run(
        [sys.executable, str(STATE_ENGINE), "render", str(review), "--expected-digest", digest, "--json"],
        capture_output=True, text=True, timeout=30,
    )
    assert rendered.returncode == 0, rendered.stderr
    text = review.read_text(encoding="utf-8")
    assert validator.validate(text) == []

    changed = text.replace("unresolved_blockers: 1", "unresolved_blockers: 0", 1)
    assert "unresolved-blockers" in _codes(changed)

    inconsistent = text.replace("**Recommendation**: REQUEST CHANGES", "**Recommendation**: APPROVE")
    assert "derived-view-mismatch" in _codes(inconsistent)


def test_validator_keeps_risk_checks_for_modern_records(tmp_path):
    review = tmp_path / "pr-7.md"
    review.write_bytes(MODERN_FIXTURE.read_bytes())
    inspect = subprocess.run(
        [sys.executable, str(STATE_ENGINE), "inspect", str(review), "--json"],
        capture_output=True, text=True, timeout=30,
    )
    digest = json.loads(inspect.stdout)["digest"]
    subprocess.run(
        [sys.executable, str(STATE_ENGINE), "render", str(review), "--expected-digest", digest, "--json"],
        check=True, capture_output=True, text=True, timeout=30,
    )
    text = review.read_text(encoding="utf-8").replace("risk_rating: medium", "risk_rating: low")
    risk_digest = {"rating": "high", "report_form": "full", "tables": {"changed_files": "| File | Tier |"}}
    assert "risk-lowered" in _codes(text, risk_digest)


def test_validator_uses_the_shared_model_after_revision_one(tmp_path):
    review = tmp_path / "pr-7.md"
    review.write_bytes(MODERN_FIXTURE.read_bytes())
    inspect = subprocess.run(
        [sys.executable, str(STATE_ENGINE), "inspect", str(review), "--json"],
        capture_output=True, text=True, timeout=30,
    )
    digest = json.loads(inspect.stdout)["digest"]
    rendered = subprocess.run(
        [sys.executable, str(STATE_ENGINE), "render", str(review), "--expected-digest", digest, "--json"],
        capture_output=True, text=True, timeout=30,
    )
    assert rendered.returncode == 0, rendered.stderr

    text = review.read_text(encoding="utf-8").replace("revision: 2", "revision: 4", 1)

    assert validator.validate(text) == []


def test_validator_does_not_treat_nonblocking_prd_category_as_a_blocker(tmp_path):
    review = tmp_path / "pr-7.md"
    review.write_bytes(MODERN_FIXTURE.read_bytes())
    review.write_text(
        review.read_text(encoding="utf-8").replace("blocking: true", "blocking: false", 1),
        encoding="utf-8",
    )
    inspect = subprocess.run(
        [sys.executable, str(STATE_ENGINE), "inspect", str(review), "--json"],
        capture_output=True, text=True, timeout=30,
    )
    digest = json.loads(inspect.stdout)["digest"]
    rendered = subprocess.run(
        [sys.executable, str(STATE_ENGINE), "render", str(review), "--expected-digest", digest, "--json"],
        capture_output=True, text=True, timeout=30,
    )

    assert rendered.returncode == 0, rendered.stderr
    output = json.loads(rendered.stdout)
    assert output["historical_count"] == 1
    assert output["unresolved_blockers"] == 0
    assert output["recommendation"] == "approve"
    assert validator.validate(review.read_text(encoding="utf-8")) == []


def test_validator_preserves_explicit_legacy_closure_provenance(tmp_path):
    review = tmp_path / "pr-7.md"
    text = MODERN_FIXTURE.read_text(encoding="utf-8")
    text = text.replace("      status: open", "      status: resolved", 1)
    text = text.replace('      outcome: ""', '      outcome: Legacy resolved', 1)
    text = text.replace("      provenance: native", "      provenance: {kind: legacy}", 1)
    review.write_text(text, encoding="utf-8")
    inspect = subprocess.run(
        [sys.executable, str(STATE_ENGINE), "inspect", str(review), "--json"],
        capture_output=True, text=True, timeout=30,
    )
    digest = json.loads(inspect.stdout)["digest"]
    rendered = subprocess.run(
        [sys.executable, str(STATE_ENGINE), "render", str(review), "--expected-digest", digest, "--json"],
        capture_output=True, text=True, timeout=30,
    )

    assert rendered.returncode == 0, rendered.stderr
    finding = json.loads(rendered.stdout)["findings"][0]
    assert finding["status"] == "resolved"
    assert finding["verification"] is None
    assert finding["provenance"]["kind"] == "legacy"
    assert validator.validate(review.read_text(encoding="utf-8")) == []
