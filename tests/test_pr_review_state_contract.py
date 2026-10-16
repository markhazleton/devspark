# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for PR-specific finding identity and review-state handling."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import shutil
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "scripts" / "pr-review-state.py"
FIXTURES = ROOT / "tests" / "fixtures" / "pr-review-state"


def _inspect(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ENGINE), "inspect", str(path), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        stdin=subprocess.DEVNULL,
    )


def _error(result: subprocess.CompletedProcess[str]) -> dict:
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"expected structured JSON diagnostics, got stdout={result.stdout!r} stderr={result.stderr!r}")


def _legacy_report(tmp_path: Path, body: str) -> Path:
    report = tmp_path / "review.md"
    report.write_text(body, encoding="utf-8")
    return report


def _state_repo(
    tmp_path: Path, fixture: Path = FIXTURES / "modern-valid.md"
) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    review = repo / ".devspark.work" / "pr-review" / "pr-7.md"
    review.parent.mkdir(parents=True)
    shutil.copyfile(fixture, review)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=15, stdin=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, timeout=15, stdin=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True, timeout=15, stdin=subprocess.DEVNULL)
    subprocess.run(["git", "add", ".devspark.work/pr-review/pr-7.md"], cwd=repo, check=True, timeout=15, stdin=subprocess.DEVNULL)
    subprocess.run(["git", "commit", "-qm", "Add synthetic review"], cwd=repo, check=True, timeout=15, stdin=subprocess.DEVNULL)
    return repo, review


def _apply_event(
    repo: Path, review: Path, tmp_path: Path, event: dict, digest: str | None = None,
    operations: list[str] | None = None,
):
    digest = digest or json.loads(_inspect(review).stdout)["digest"]
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(event), encoding="utf-8")
    if operations is not None:
        operations.append(event["operation"])
    return subprocess.run(
        [sys.executable, str(ENGINE), "apply", str(review), "--event", str(event_path),
         "--expected-digest", digest, "--repo-root", str(repo), "--json"],
        cwd=repo, capture_output=True, text=True, encoding="utf-8", timeout=30, stdin=subprocess.DEVNULL,
    )


def _pending_review(repo: Path, review: Path, tmp_path: Path) -> tuple[str, str]:
    (repo / "src").mkdir()
    (repo / "src" / "change.py").write_text("def forwards_upper_bound():\n    return True\n", encoding="utf-8")
    subprocess.run(["git", "add", "src/change.py"], cwd=repo, check=True, timeout=15, stdin=subprocess.DEVNULL)
    subprocess.run(["git", "commit", "-qm", "Add synthetic correction"], cwd=repo, check=True, timeout=15, stdin=subprocess.DEVNULL)
    correction = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True,
        timeout=15, stdin=subprocess.DEVNULL,
    ).stdout.strip()
    event = {
        "operation": "remediate-and-submit", "finding_id": "H-01", "actor_role": "author",
        "remediation": {
            "correction_commit": correction, "author_context": "synthetic-author",
            "explanation": "Added the missing upper-bound assertion.",
            "author_validation": "Synthetic focused test passed.",
            "proof_obligation": "Evaluate the forwarded exclusive upper bound.",
        },
    }
    result = _apply_event(repo, review, tmp_path, event)
    assert result.returncode == 0, result.stderr
    subprocess.run(["git", "add", ".devspark.work/pr-review/pr-7.md"], cwd=repo, check=True, timeout=15, stdin=subprocess.DEVNULL)
    subprocess.run(["git", "commit", "-qm", "Record synthetic remediation"], cwd=repo, check=True, timeout=15, stdin=subprocess.DEVNULL)
    evaluated = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True,
        timeout=15, stdin=subprocess.DEVNULL,
    ).stdout.strip()
    return correction, evaluated


def test_inspect_reads_modern_record_without_rewriting_it():
    source = FIXTURES / "modern-valid.md"
    original = source.read_bytes()

    result = _inspect(source)

    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert output["record"]["format_version"] == 1
    assert output["record"]["findings"][0]["finding_id"] == "H-01"
    assert output["digest"] == hashlib.sha256(original).hexdigest()
    assert source.read_bytes() == original


def test_inspect_rejects_unsupported_modern_version_without_legacy_fallback():
    result = _inspect(FIXTURES / "modern-unsupported.md")

    assert result.returncode != 0
    output = _error(result)
    assert output["ok"] is False
    assert output["issues"][0]["code"] == "unsupported-version"
    assert output["issues"][0]["location"]


def test_inspect_rejects_malformed_modern_yaml_without_legacy_fallback():
    result = _inspect(FIXTURES / "modern-malformed.md")

    assert result.returncode != 0
    output = _error(result)
    assert output["ok"] is False
    assert output["issues"][0]["code"] == "malformed-record"
    assert output["issues"][0]["location"]


def test_inspect_normalizes_explicit_legacy_alias_to_one_blocker():
    result = _inspect(FIXTURES / "legacy-aliased.md")

    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    observed = {
        "findings": [
            {
                key: output["findings"][0][key]
                for key in ("finding_id", "aliases", "severity", "category", "blocking", "status")
            }
        ],
        "historical_count": output["historical_count"],
        "unresolved_blockers": output["unresolved_blockers"],
    }
    rendered = json.dumps(observed, indent=2) + "\n"
    expected = (FIXTURES / "expected-intake.json").read_text(encoding="utf-8").replace("\r\n", "\n")
    assert rendered == expected
    assert output["historical_count"] == 1
    assert output["unresolved_blockers"] == 1
    assert output["findings"][0]["finding_id"] == "H-01"
    assert output["findings"][0]["aliases"] == ["PRD3-01"]
    assert output["findings"][0]["status"] == "open"
    compatibility = output["open_findings"][0]
    assert compatibility["id"] == "H-01"
    assert compatibility["severity"] == "H"
    assert compatibility["severity_level"] == "high"
    assert compatibility["aliases"] == ["PRD3-01"]
    assert compatibility["auto_eligible"] is True


def test_inspect_keeps_similar_legacy_descriptions_as_distinct_findings(tmp_path: Path):
    report = _legacy_report(
        tmp_path,
        """# High Priority Issues (Non-blocking)

- [ ] **H-01** First boundary check is missing.
- [ ] **H-02** First boundary check is missing.
""",
    )

    result = _inspect(report)

    assert result.returncode == 0, result.stderr
    findings = json.loads(result.stdout)["findings"]
    assert [finding["finding_id"] for finding in findings] == ["H-01", "H-02"]


@pytest.mark.parametrize(
    ("body", "expected_id"),
    [
        ("# Findings (Non-blocking)\n\n| ID | Issue |\n| --- | --- |\n| M-03 | Table-only concern. |\n", "M-03"),
        ("# Findings (Non-blocking)\n\n- [ ] **L-04** Action-only concern.\n", "L-04"),
    ],
)
def test_inspect_reads_table_only_and_action_only_legacy_findings(
    tmp_path: Path, body: str, expected_id: str
):
    result = _inspect(_legacy_report(tmp_path, body))

    assert result.returncode == 0, result.stderr
    assert [finding["finding_id"] for finding in json.loads(result.stdout)["findings"]] == [expected_id]


def test_inspect_does_not_infer_legacy_blocking_from_high_severity(tmp_path: Path):
    report = _legacy_report(tmp_path, "# High Priority Issues\n\n- [ ] **H-07** Unclassified concern.\n")

    result = _inspect(report)

    assert result.returncode != 0
    issue = _error(result)["issues"][0]
    assert issue["code"] == "ambiguous-legacy-blocking"
    assert "authorized reviewer" in issue["recovery"]


def test_high_severity_without_a_blocking_obligation_remains_nonblocking(tmp_path: Path):
    review = _legacy_report(
        tmp_path,
        (FIXTURES / "modern-valid.md").read_text(encoding="utf-8").replace(
            "blocking: true", "blocking: false", 1
        ),
    )

    result = _inspect(review)

    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["findings"][0]["severity"] == "high"
    assert output["findings"][0]["blocking"] is False
    assert output["unresolved_blockers"] == 0
    assert output["recommendation"] == "approve"


def test_binding_obligation_remains_blocking_when_severity_is_low(tmp_path: Path):
    text = (FIXTURES / "modern-valid.md").read_text(encoding="utf-8")
    for old, new in (
        ("  high: 1", "  high: 0"),
        ("  low: 0", "  low: 1"),
        ("  con: 0", "  con: 1"),
        ("max_severity: high", "max_severity: low"),
        ("H-01", "L-01"),
        ("      severity: high", "      severity: low"),
        ("category: PRD3", "category: constitution"),
    ):
        text = text.replace(old, new, 1)
    review = _legacy_report(tmp_path, text)

    result = _inspect(review)

    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["findings"][0]["severity"] == "low"
    assert output["findings"][0]["blocking"] is True
    assert output["unresolved_blockers"] == 1
    assert output["recommendation"] == "request-changes"


def test_inspect_ignores_finding_examples_inside_code_fences(tmp_path: Path):
    report = _legacy_report(
        tmp_path,
        """# Findings

```markdown
- [ ] **H-99** Example only.
| ID | Status | Issue |
| --- | --- | --- |
| H-98 | Open | Example only. |
```
""",
    )

    result = _inspect(report)

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["findings"] == []


def test_inspect_accepts_a_genuinely_empty_legacy_report(tmp_path: Path):
    result = _inspect(_legacy_report(tmp_path, "# Pull Request Review\n\nNo findings.\n"))

    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["findings"] == []
    assert output["historical_count"] == 0
    assert output["unresolved_blockers"] == 0


def test_inspect_preserves_unambiguous_legacy_closure_without_modern_verification(tmp_path: Path):
    report = _legacy_report(
        tmp_path,
        """# Immediate Actions (Blocking)

- [x] **H-05** Previously closed concern.

| ID | Status | Issue |
| --- | --- | --- |
| H-05 | Resolved | Previously closed concern. |
""",
    )

    result = _inspect(report)

    assert result.returncode == 0, result.stderr
    finding = json.loads(result.stdout)["findings"][0]
    assert finding["status"] == "resolved"
    assert finding["outcome"] == "Legacy resolved"
    assert finding["provenance"]["kind"] == "legacy"
    assert finding["verification"] is None


def test_inspect_diagnoses_conflicting_legacy_closure_evidence(tmp_path: Path):
    report = _legacy_report(
        tmp_path,
        """# Immediate Actions (Blocking)

- [x] **H-06** Conflicting closure evidence.

| ID | Status | Issue |
| --- | --- | --- |
| H-06 | Open | Conflicting closure evidence. |
""",
    )

    result = _inspect(report)

    assert result.returncode != 0
    issue = _error(result)["issues"][0]
    assert issue["code"] == "contradictory-legacy-status"
    assert issue["location"]


def test_apply_recovers_a_contradictory_legacy_status_with_an_explicit_choice(tmp_path: Path):
    report = _legacy_report(
        tmp_path,
        """# Immediate Actions (Blocking)

- [x] **H-06** Conflicting closure evidence.

| ID | Status | Issue |
| --- | --- | --- |
| H-06 | Open | Conflicting closure evidence. |
""",
    )
    event = {
        "operation": "recover-legacy",
        "finding_id": "H-06",
        "recovery": {
            "reason": "The detail row is current; the checkbox was stale.",
            "authorized_by": "review-owner",
            "evidence": ["Review owner confirmed the row is authoritative."],
            "chosen_interpretation": {
                "finding_id": "H-06", "aliases": [], "severity": "high", "category": None,
                "blocking": True, "description": "Conflicting closure evidence.",
                "expected_outcome": "", "evidence": ["Review owner decision."],
                "recommended_action": "", "execution_mode": "manual", "status": "open",
                "outcome": "", "remediation": None, "verification": None, "disposition": None,
                "reopen_reason": None,
            },
        },
    }
    event_path = tmp_path / "recovery.json"
    event_path.write_text(json.dumps(event), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(ENGINE), "apply", str(report), "--event", str(event_path),
         "--expected-digest", hashlib.sha256(report.read_bytes()).hexdigest(),
         "--repo-root", str(tmp_path), "--json"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=30,
        stdin=subprocess.DEVNULL,
    )

    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["changed"] is True
    recovered = json.loads(_inspect(report).stdout)["record"]["findings"][0]
    assert recovered["status"] == "open"
    assert recovered["provenance"]["recovery"]["authorized_by"] == "review-owner"


def test_legacy_reclassification_requires_a_named_authorized_reviewer(tmp_path: Path):
    report = _legacy_report(
        tmp_path, "# High Priority Issues\n\n- [ ] **H-07** Unclassified concern.\n"
    )
    event = {
        "operation": "recover-legacy",
        "finding_id": "H-07",
        "recovery": {
            "reason": "The evidence shows this is advisory.",
            "evidence": ["The cited requirement is nonbinding."],
            "chosen_interpretation": {
                "finding_id": "H-07", "aliases": [], "severity": "high", "category": None,
                "blocking": False, "description": "Unclassified concern.",
                "expected_outcome": "", "evidence": ["The cited requirement is nonbinding."],
                "recommended_action": "", "execution_mode": "manual", "status": "open",
                "outcome": "", "remediation": None, "verification": None, "disposition": None,
                "reopen_reason": None,
            },
        },
    }
    original = report.read_bytes()
    event_path = tmp_path / "recovery.json"
    event_path.write_text(json.dumps(event), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ENGINE), "apply", str(report), "--event", str(event_path),
         "--expected-digest", hashlib.sha256(original).hexdigest(),
         "--repo-root", str(tmp_path), "--json"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=30,
        stdin=subprocess.DEVNULL,
    )

    assert result.returncode != 0
    assert _error(result)["issues"][0]["code"] == "missing-classification"
    assert report.read_bytes() == original


def test_inspect_diagnoses_legacy_alias_owned_by_two_findings(tmp_path: Path):
    report = _legacy_report(
        tmp_path,
        """# Immediate Actions (Blocking)

- [ ] **H-01 / PRD3-01** First concern.
- [ ] **H-02 / PRD3-01** Second concern.
""",
    )

    result = _inspect(report)

    assert result.returncode != 0
    issue = _error(result)["issues"][0]
    assert issue["code"] == "alias-conflict"
    assert issue["location"]
    assert issue["recovery"]


def test_apply_recovers_legacy_alias_ownership_and_retains_both_findings(tmp_path: Path):
    report = _legacy_report(
        tmp_path,
        """# Immediate Actions (Blocking)

- [ ] **H-01 / PRD3-01** First concern.
- [ ] **H-02 / PRD3-01** Second concern.
""",
    )
    event = {
        "operation": "recover-legacy",
        "finding_id": "H-01",
        "recovery": {
            "reason": "The explicit alias belongs to the first concern.",
            "authorized_by": "review-owner",
            "evidence": ["Source context identifies the first concern."],
            "chosen_interpretation": {
                "finding_id": "H-01", "aliases": ["PRD3-01"], "severity": "high",
                "category": "PRD3", "blocking": True, "description": "First concern.",
                "expected_outcome": "", "evidence": [], "recommended_action": "",
                "execution_mode": "manual", "status": "open", "outcome": "",
                "remediation": None, "verification": None, "disposition": None,
                "reopen_reason": None,
            },
        },
    }
    event_path = tmp_path / "recovery.json"
    event_path.write_text(json.dumps(event), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(ENGINE), "apply", str(report), "--event", str(event_path),
         "--expected-digest", hashlib.sha256(report.read_bytes()).hexdigest(),
         "--repo-root", str(tmp_path), "--json"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=30,
        stdin=subprocess.DEVNULL,
    )

    assert result.returncode == 0, result.stderr
    findings = json.loads(_inspect(report).stdout)["record"]["findings"]
    assert [finding["finding_id"] for finding in findings] == ["H-01", "H-02"]
    assert findings[0]["aliases"] == ["PRD3-01"]
    assert findings[1]["aliases"] == []


def test_inspect_diagnoses_malformed_finding_like_action(tmp_path: Path):
    report = _legacy_report(tmp_path, "# Findings\n\n- [ ] **Q-01** Unsupported identifier.\n")

    result = _inspect(report)

    assert result.returncode != 0
    issue = _error(result)["issues"][0]
    assert issue["code"] == "malformed-finding"
    assert issue["location"]
    assert issue["recovery"]


def test_apply_remediate_and_independently_verify_is_idempotent(tmp_path: Path):
    repo, review = _state_repo(tmp_path)
    (repo / "src").mkdir()
    (repo / "src" / "change.py").write_text("def forwards_upper_bound():\n    return True\n", encoding="utf-8")
    subprocess.run(["git", "add", "src/change.py"], cwd=repo, check=True, timeout=15, stdin=subprocess.DEVNULL)
    subprocess.run(["git", "commit", "-qm", "Add synthetic correction"], cwd=repo, check=True, timeout=15, stdin=subprocess.DEVNULL)
    correction = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True,
        timeout=15, stdin=subprocess.DEVNULL,
    ).stdout.strip()

    remediation = {
        "operation": "remediate-and-submit",
        "finding_id": "PRD3-01",
        "actor_role": "author",
        "actor_context": "synthetic-author",
        "remediation": {
            "correction_commit": correction,
            "author_context": "synthetic-author",
            "explanation": "Added the missing upper-bound assertion.",
            "author_validation": "Synthetic focused test passed.",
            "proof_obligation": "Evaluate the forwarded exclusive upper bound.",
        },
    }
    result = _apply_event(repo, review, tmp_path, remediation)
    assert result.returncode == 0, result.stderr
    pending = json.loads(result.stdout)
    assert pending["pending_verification_count"] == 1
    assert pending["unresolved_blockers"] == 1
    assert pending["recommendation"] == "request-changes"

    subprocess.run(["git", "add", ".devspark.work/pr-review/pr-7.md"], cwd=repo, check=True, timeout=15, stdin=subprocess.DEVNULL)
    subprocess.run(["git", "commit", "-qm", "Record synthetic remediation"], cwd=repo, check=True, timeout=15, stdin=subprocess.DEVNULL)
    evaluated = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True,
        timeout=15, stdin=subprocess.DEVNULL,
    ).stdout.strip()
    verification = {
        "operation": "verify",
        "finding_id": "H-01",
        "actor_role": "reviewer",
        "actor_context": "synthetic-reviewer",
        "verification": {
            "reviewer_context": "synthetic-reviewer",
            "reviewer_role": "reviewer",
            "conclusion": "confirmed",
            "proof": "Ran the focused upper-bound test and inspected the changed assertion.",
            "rationale": "The original expectation is satisfied in the committed correction.",
            "correction_commit": correction,
            "evaluated_commit": evaluated,
        },
    }
    result = _apply_event(repo, review, tmp_path, verification)
    assert result.returncode == 0, result.stderr
    closed = json.loads(result.stdout)
    assert closed["changed"] is True
    assert closed["unresolved_blockers"] == 0
    assert closed["recommendation"] == "approve"
    assert closed["findings"][0]["status"] == "resolved"
    assert "Pending independent verification: 0" in review.read_text(encoding="utf-8")

    repeated = _apply_event(repo, review, tmp_path, verification, closed["record_digest"])
    assert repeated.returncode == 0, repeated.stderr
    assert json.loads(repeated.stdout)["changed"] is False


def test_legacy_alias_replay_closes_without_reconciliation_or_host_writes(tmp_path: Path):
    baseline = (FIXTURES / "baseline-observations.json").read_bytes()
    repo, review = _state_repo(tmp_path, FIXTURES / "legacy-aliased.md")
    (repo / "handler.py").write_text(
        "return adapter.search(created_after=lower)\n", encoding="utf-8"
    )
    test_file = repo / "tests" / "test_window.py"
    test_file.parent.mkdir()
    test_file.write_text(
        "def test_window_forwards_bounds(adapter):\n"
        "    search_window(adapter, lower=LOWER, upper=UPPER)\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "handler.py", "tests/test_window.py"], cwd=repo, check=True,
        timeout=15, stdin=subprocess.DEVNULL,
    )
    subprocess.run(
        ["git", "commit", "-qm", "Add synthetic baseline code"], cwd=repo, check=True,
        timeout=15, stdin=subprocess.DEVNULL,
    )
    intake = _inspect(review)
    assert intake.returncode == 0, intake.stderr
    assert json.loads(intake.stdout)["unresolved_blockers"] == 1

    subprocess.run(
        ["git", "apply", str(FIXTURES / "correction.diff")], cwd=repo, check=True,
        timeout=15, stdin=subprocess.DEVNULL,
    )
    subprocess.run(
        ["git", "add", "handler.py", "tests/test_window.py"], cwd=repo, check=True,
        timeout=15, stdin=subprocess.DEVNULL,
    )
    subprocess.run(
        ["git", "commit", "-qm", "Apply synthetic boundary correction"], cwd=repo,
        check=True, timeout=15, stdin=subprocess.DEVNULL,
    )
    correction = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True,
        timeout=15, stdin=subprocess.DEVNULL,
    ).stdout.strip()
    correction_paths = subprocess.run(
        ["git", "show", "--format=", "--name-only", correction], cwd=repo, check=True,
        capture_output=True, text=True, timeout=15, stdin=subprocess.DEVNULL,
    ).stdout.splitlines()
    assert sorted(correction_paths) == ["handler.py", "tests/test_window.py"]
    assert "created_before=upper" in (repo / "handler.py").read_text(encoding="utf-8")
    assert 'created_before"]' in test_file.read_text(encoding="utf-8")

    operations: list[str] = []
    author_result = _apply_event(repo, review, tmp_path, {
        "operation": "remediate-and-submit", "finding_id": "PRD3-01",
        "actor_role": "author", "actor_context": "synthetic-author",
        "remediation": {
            "correction_commit": correction, "author_context": "synthetic-author",
            "explanation": "Forward the upper bound and assert it at the request boundary.",
            "author_validation_absent_reason": "No application test suite was invoked in this replay.",
            "proof_obligation": "Independently evaluate the committed boundary assertion.",
        },
    }, operations=operations)
    assert author_result.returncode == 0, author_result.stdout or author_result.stderr
    assert json.loads(author_result.stdout)["unresolved_blockers"] == 1
    subprocess.run(
        ["git", "add", ".devspark.work/pr-review/pr-7.md"], cwd=repo, check=True,
        timeout=15, stdin=subprocess.DEVNULL,
    )
    subprocess.run(
        ["git", "commit", "-qm", "Record synthetic author remediation"], cwd=repo,
        check=True, timeout=15, stdin=subprocess.DEVNULL,
    )
    evaluated = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True,
        timeout=15, stdin=subprocess.DEVNULL,
    ).stdout.strip()
    review_paths = subprocess.run(
        ["git", "show", "--format=", "--name-only", evaluated], cwd=repo, check=True,
        capture_output=True, text=True, timeout=15, stdin=subprocess.DEVNULL,
    ).stdout.splitlines()
    assert review_paths == [".devspark.work/pr-review/pr-7.md"]

    reviewer_result = _apply_event(repo, review, tmp_path, {
        "operation": "verify", "finding_id": "H-01",
        "actor_role": "reviewer", "actor_context": "synthetic-reviewer",
        "verification": {
            "reviewer_context": "synthetic-reviewer", "reviewer_role": "independent reviewer",
            "conclusion": "confirmed",
            "proof": "Inspected the committed argument and checked the boundary assertion.",
            "rationale": "The correction forwards and asserts the exclusive upper bound.",
            "correction_commit": correction, "evaluated_commit": evaluated,
        },
    }, operations=operations)
    assert reviewer_result.returncode == 0, reviewer_result.stdout or reviewer_result.stderr
    output = json.loads(reviewer_result.stdout)
    finding = output["findings"][0]
    observed = {
        "finding_id": finding["finding_id"],
        "aliases": finding["aliases"],
        "status": finding["status"],
        **{key: output[key] for key in (
            "historical_count", "current_counts", "current_state_counts", "unresolved_blockers",
            "pending_verification_count", "gate_status", "recommendation",
        )},
        "workflow_counts": {
            "initial_intakes": 1,
            "author_submissions": operations.count("remediate-and-submit"),
            "independent_evaluations": operations.count("verify"),
            "reconciliation_only_operations": 0,
            "host_writes": 0,
            "application_test_runs": 0,
        },
    }
    rendered = json.dumps(observed, indent=2) + "\n"
    expected = (FIXTURES / "expected-closeout.json").read_text(encoding="utf-8").replace("\r\n", "\n")
    assert rendered == expected
    assert (FIXTURES / "baseline-observations.json").read_bytes() == baseline


@pytest.mark.parametrize(
    ("evaluation_update", "expected_code"),
    [
        ({"proof": ""}, "missing-classification"),
        ({"reviewer_context": "synthetic-author"}, "author-self-verification"),
        ({"correction_commit": "3333333333333333333333333333333333333333"}, "wrong-correction-context"),
    ],
)
def test_apply_rejects_incomplete_or_nonindependent_evaluation_without_write(
    tmp_path: Path, evaluation_update: dict, expected_code: str
):
    repo, review = _state_repo(tmp_path)
    correction, evaluated = _pending_review(repo, review, tmp_path)
    event = {
        "operation": "verify", "finding_id": "H-01",
        "verification": {
            "reviewer_context": "synthetic-reviewer", "reviewer_role": "reviewer",
            "conclusion": "confirmed", "proof": "Focused proof passed.",
            "rationale": "The original expectation is satisfied.",
            "correction_commit": correction, "evaluated_commit": evaluated,
        },
    }
    event["verification"].update(evaluation_update)
    original = review.read_bytes()

    result = _apply_event(repo, review, tmp_path, event)

    assert result.returncode != 0
    assert _error(result)["issues"][0]["code"] == expected_code
    assert review.read_bytes() == original


@pytest.mark.parametrize("operation", ["submit", "verify", "reopen"])
def test_apply_rejects_transitions_that_do_not_match_the_current_state(tmp_path: Path, operation: str):
    repo, review = _state_repo(tmp_path)
    event = {"operation": operation, "finding_id": "H-01"}
    result = _apply_event(repo, review, tmp_path, event)

    assert result.returncode != 0
    assert _error(result)["issues"][0]["code"] == "unauthorized-transition"


def test_apply_rejects_evaluation_when_repository_has_unrelated_worktree_changes(tmp_path: Path):
    repo, review = _state_repo(tmp_path)
    correction, evaluated = _pending_review(repo, review, tmp_path)
    dirty_file = repo / "src" / "unrelated.py"
    dirty_file.write_text("synthetic unrelated change\n", encoding="utf-8")
    event = {
        "operation": "verify", "finding_id": "H-01",
        "verification": {
            "reviewer_context": "synthetic-reviewer", "reviewer_role": "reviewer",
            "conclusion": "confirmed", "proof": "Focused proof passed.",
            "rationale": "The original expectation is satisfied.",
            "correction_commit": correction, "evaluated_commit": evaluated,
        },
    }

    result = _apply_event(repo, review, tmp_path, event)

    assert result.returncode != 0
    assert _error(result)["issues"][0]["code"] == "wrong-correction-context"
    assert review.read_text(encoding="utf-8").find("Pending independent verification") >= 0
    dirty_file.unlink()


def test_apply_rejects_evaluation_commit_that_does_not_contain_the_correction(tmp_path: Path):
    repo, review = _state_repo(tmp_path)
    correction, _evaluated = _pending_review(repo, review, tmp_path)
    pending_report = review.read_bytes()
    base = subprocess.run(
        ["git", "rev-parse", f"{correction}^"], cwd=repo, check=True, capture_output=True,
        text=True, timeout=15, stdin=subprocess.DEVNULL,
    ).stdout.strip()
    subprocess.run(
        ["git", "checkout", "-q", "--detach", base], cwd=repo, check=True, timeout=15,
        stdin=subprocess.DEVNULL,
    )
    review.write_bytes(pending_report)
    unrelated = repo / "src" / "unrelated.py"
    unrelated.parent.mkdir(exist_ok=True)
    unrelated.write_text("synthetic independent branch\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "src/unrelated.py"], cwd=repo, check=True, timeout=15,
        stdin=subprocess.DEVNULL,
    )
    subprocess.run(
        ["git", "commit", "-qm", "Create unrelated evaluated context"], cwd=repo,
        check=True, timeout=15, stdin=subprocess.DEVNULL,
    )
    evaluated = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True,
        timeout=15, stdin=subprocess.DEVNULL,
    ).stdout.strip()
    event = {
        "operation": "verify", "finding_id": "H-01",
        "verification": {
            "reviewer_context": "synthetic-reviewer", "reviewer_role": "reviewer",
            "conclusion": "confirmed", "proof": "Focused proof passed.",
            "rationale": "The original expectation is satisfied.",
            "correction_commit": correction, "evaluated_commit": evaluated,
        },
    }

    result = _apply_event(repo, review, tmp_path, event)

    assert result.returncode != 0
    assert _error(result)["issues"][0]["code"] == "wrong-correction-context"
    assert review.read_bytes() == pending_report


def test_unmet_required_condition_prevents_positive_final_recommendation(tmp_path: Path):
    repo, review = _state_repo(tmp_path)
    correction, evaluated = _pending_review(repo, review, tmp_path)
    result = _apply_event(repo, review, tmp_path, {
        "operation": "verify", "finding_id": "H-01",
        "verification": {
            "reviewer_context": "synthetic-reviewer", "reviewer_role": "reviewer",
            "conclusion": "confirmed", "proof": "Focused proof passed.",
            "rationale": "The original expectation is satisfied.",
            "correction_commit": correction, "evaluated_commit": evaluated,
        },
        "conditions": [{
            "condition_id": "required-review-check",
            "result": "fail",
            "required": True,
            "evidence": ["Synthetic required review check did not pass."],
            "reason": "A separate existing obligation remains unsatisfied.",
        }],
    })

    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["findings"][0]["status"] == "resolved"
    assert output["unresolved_blockers"] == 0
    assert output["gate_status"] == "fail"
    assert output["recommendation"] == "request-changes"


@pytest.mark.parametrize("kind", ["accepted", "deferred", "withdrawn"])
def test_apply_preserves_governed_disposition_authority(tmp_path: Path, kind: str):
    repo, review = _state_repo(tmp_path)
    result = _apply_event(repo, review, tmp_path, {
        "operation": "disposition", "finding_id": "H-01",
        "disposition": {
            "kind": kind,
            "reason": "Synthetic authorized disposition.",
            "authorized_by": "review-owner",
            "capture_reference": "synthetic-decision-1",
        },
    })

    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["findings"][0]["disposition"]["authorized_by"] == "review-owner"
    assert output["unresolved_blockers"] == 0
    assert output["recommendation"] == "approve"


def test_apply_rejects_disposition_without_a_named_authorized_human(tmp_path: Path):
    repo, review = _state_repo(tmp_path)
    original = review.read_bytes()
    result = _apply_event(repo, review, tmp_path, {
        "operation": "disposition", "finding_id": "H-01",
        "disposition": {
            "kind": "accepted",
            "reason": "Synthetic limitation.",
            "authorized_by": "",
            "capture_reference": "synthetic-decision-1",
        },
    })

    assert result.returncode != 0
    assert _error(result)["issues"][0]["code"] == "missing-classification"
    assert review.read_bytes() == original


def test_reopen_retains_prior_independent_resolution_and_requires_recurrence_evidence(tmp_path: Path):
    repo, review = _state_repo(tmp_path)
    correction, evaluated = _pending_review(repo, review, tmp_path)
    confirmed = _apply_event(repo, review, tmp_path, {
        "operation": "verify", "finding_id": "H-01",
        "verification": {
            "reviewer_context": "synthetic-reviewer", "reviewer_role": "reviewer",
            "conclusion": "confirmed", "proof": "Focused proof passed.",
            "rationale": "The original expectation is satisfied.",
            "correction_commit": correction, "evaluated_commit": evaluated,
        },
    })
    assert confirmed.returncode == 0, confirmed.stderr
    subprocess.run(
        ["git", "add", ".devspark.work/pr-review/pr-7.md"], cwd=repo, check=True,
        timeout=15, stdin=subprocess.DEVNULL,
    )
    subprocess.run(
        ["git", "commit", "-qm", "Record synthetic independent verification"], cwd=repo,
        check=True, timeout=15, stdin=subprocess.DEVNULL,
    )
    resolved = json.loads(_inspect(review).stdout)["record"]["findings"][0]
    reopened = _apply_event(repo, review, tmp_path, {
        "operation": "reopen", "finding_id": "H-01",
        "reopen_reason": "A focused recurrence was observed in the corrected boundary.",
        "verification": {
            "reviewer_context": "synthetic-followup-reviewer", "reviewer_role": "reviewer",
            "conclusion": "incomplete", "proof": "The recurrence is present in the current test.",
            "rationale": "The correction does not cover the reproduced recurrence.",
            "correction_commit": correction,
            "evaluated_commit": subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True,
                text=True, timeout=15, stdin=subprocess.DEVNULL,
            ).stdout.strip(),
        },
    })

    assert reopened.returncode == 0, reopened.stderr
    finding = json.loads(reopened.stdout)["findings"][0]
    assert finding["status"] == "reopened"
    assert finding["reopen_reason"].startswith("A focused recurrence")
    assert finding["prior_resolution"]["verification"] == resolved["verification"]


def test_apply_rejects_stale_digest_and_busy_guard_without_replacing_review(tmp_path: Path):
    repo, review = _state_repo(tmp_path)
    original_digest = json.loads(_inspect(review).stdout)["digest"]
    review.write_text(review.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    stale_bytes = review.read_bytes()
    current_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True,
        timeout=15, stdin=subprocess.DEVNULL,
    ).stdout.strip()
    remediation = {
        "operation": "remediate", "finding_id": "H-01",
        "remediation": {
            "correction_commit": current_commit,
            "author_context": "synthetic-author", "explanation": "Synthetic correction.",
            "author_validation_absent_reason": "No applicable author test was run.",
        },
    }
    stale = _apply_event(repo, review, tmp_path, remediation, original_digest)
    assert stale.returncode != 0
    assert _error(stale)["issues"][0]["code"] == "stale-record"
    assert review.read_bytes() == stale_bytes

    current_digest = json.loads(_inspect(review).stdout)["digest"]
    guard = review.with_name(f".{review.name}.lock")
    guard.write_text("synthetic writer\n", encoding="ascii")
    busy = _apply_event(repo, review, tmp_path, remediation, current_digest)
    assert busy.returncode != 0
    assert _error(busy)["issues"][0]["code"] == "writer-busy"
    assert review.read_bytes() == stale_bytes


def test_interrupted_atomic_replacement_cleans_guard_and_temporary_file(tmp_path: Path, monkeypatch):
    repo, review = _state_repo(tmp_path)
    digest = json.loads(_inspect(review).stdout)["digest"]
    current_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True,
        timeout=15, stdin=subprocess.DEVNULL,
    ).stdout.strip()
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps({
        "operation": "remediate", "finding_id": "H-01",
        "remediation": {
            "correction_commit": current_commit,
            "author_context": "synthetic-author", "explanation": "Synthetic correction.",
            "author_validation_absent_reason": "No applicable author test was run.",
        },
    }), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("pr_review_state_under_test", ENGINE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original = review.read_bytes()
    monkeypatch.setattr(module.os, "replace", lambda *_args: (_ for _ in ()).throw(PermissionError("synthetic interruption")))

    with pytest.raises(PermissionError, match="synthetic interruption"):
        module.apply(review, event_path, digest, repo)

    assert review.read_bytes() == original
    assert not review.with_name(f".{review.name}.lock").exists()
    assert not list(review.parent.glob(f".{review.name}.*.tmp"))


def test_render_updates_derived_views_once_and_preserves_unmarked_narrative(tmp_path: Path):
    repo, review = _state_repo(tmp_path)
    original_text = review.read_text(encoding="utf-8")
    review.write_text(original_text.replace(
        "<!-- PR-REVIEW-DERIVED:ACTION:BEGIN -->",
        "## Scope Narrative\n\nSynthetic reviewer context preserved.\n\n<!-- PR-REVIEW-DERIVED:ACTION:BEGIN -->",
    ), encoding="utf-8")
    digest = json.loads(_inspect(review).stdout)["digest"]
    rendered = subprocess.run(
        [sys.executable, str(ENGINE), "render", str(review), "--expected-digest", digest, "--json"],
        cwd=repo, capture_output=True, text=True, encoding="utf-8", timeout=30, stdin=subprocess.DEVNULL,
    )

    assert rendered.returncode == 0, rendered.stderr
    result = json.loads(rendered.stdout)
    assert result["changed"] is True
    text = review.read_text(encoding="utf-8")
    assert text.count("Synthetic reviewer context preserved.") == 1
    assert "- Unresolved blockers: 1" in text
    assert "**Recommendation**: REQUEST CHANGES" in text
    assert "historical_findings:" in text

    repeated = subprocess.run(
        [sys.executable, str(ENGINE), "render", str(review), "--expected-digest", result["record_digest"], "--json"],
        cwd=repo, capture_output=True, text=True, encoding="utf-8", timeout=30, stdin=subprocess.DEVNULL,
    )
    assert repeated.returncode == 0, repeated.stderr
    assert json.loads(repeated.stdout)["changed"] is False


def test_installed_package_carries_the_state_engine_contract_and_both_helpers(package_build, tmp_path: Path):
    extracted = tmp_path / "installed"
    with zipfile.ZipFile(package_build.zips["copilot"]) as archive:
        archive.extractall(extracted)

    installed = extracted / ".devspark"
    for relative in (
        "scripts/pr-review-state.py",
        "scripts/pr-review-validate.py",
        "scripts/bash/address-pr-review.sh",
        "scripts/powershell/address-pr-review.ps1",
        "pr-review-state-contract.md",
    ):
        assert (installed / relative).is_file(), relative
    assert "../pr-review-state.py" in (installed / "scripts/bash/address-pr-review.sh").read_text(encoding="utf-8")
    assert "pr-review-state.py" in (installed / "scripts/powershell/address-pr-review.ps1").read_text(encoding="utf-8")

    bash_packager = (ROOT / "eng/release/create-release-packages.sh").read_text(encoding="utf-8")
    ps_packager = (ROOT / "eng/release/create-release-packages.ps1").read_text(encoding="utf-8")
    assert "find scripts -maxdepth 1 -type f" in bash_packager
    assert 'Get-ChildItem -Path "scripts" -File' in ps_packager
