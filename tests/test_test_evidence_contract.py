# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for the shared test-evidence record and evidence-first PR Review."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _flat(rel: str) -> str:
    return re.sub(r"\s+", " ", (ROOT / rel).read_text(encoding="utf-8"))


def test_contract_defines_a_reusable_record_with_validity_rules() -> None:
    contract = _flat("templates/verification-contract.md").split("## 4.1 Test Evidence Record", 1)[1]
    contract = contract.split("## 5. Non-Negotiables", 1)[0]
    for field in ("commit:", "tree:", "command:", "result:", "run_at:", "run_by:"):
        assert field in contract, field
    for rule in ("`exit 0` and `tree: clean`", "recorded commit still exists", "invalidates it"):
        assert rule in contract, rule
    assert "policy wins" in contract


def test_pr_review_inspects_evidence_before_running_and_never_fakes_a_pass() -> None:
    review = _flat("templates/commands/pr-review.md")
    section = review.split("#### Testing Validation", 1)[1].split("#### Documentation Review", 1)[0]
    assert section.index("Find existing evidence") < section.index("Run the scoped tests yourself")
    for trigger in (
        "no valid record covers the changed tests",
        "high-risk",
        "repository policy requires the reviewer's own run",
        "did not exercise",
    ):
        assert trigger in section, trigger
    assert "Failing tests are an automatic HIGH finding" not in section
    for attribution in ("product regression", "environment failure", "unrelated baseline debt", "unattributed failure"):
        assert attribution in section
    assert "required gate still remains unmet" in section
    assert "retry policy permits it" in section
    assert "never approve on evidence you could not validate" in section


def test_evidence_reuse_handles_intervening_changes_without_duplicate_runs() -> None:
    contract = _flat("templates/verification-contract.md")
    for safeguard in (
        "same rule to direct edits, merges and rebases",
        "staged and unstaged changes and relevant untracked inputs",
        "When impact cannot be bounded, rerun the recorded scope",
        "A role label alone does not establish independent execution",
        "skipped required coverage does not satisfy it",
        "broader run satisfies narrower checks",
    ):
        assert safeguard in contract
    review = _flat("templates/commands/pr-review.md")
    assert "the first command is not a permanent minimum scope" in review
    assert "the full suite only when a scoped run is not possible" not in review
    assert "Keep the same test command" not in review
    assert "Test suite failures on changed test files | HIGH" not in review
    assert "| Test failure attributed to this PR's changed behavior | By demonstrated impact |" in review
    assert "never search for or reconstruct a bundle" in review
    remediation = _flat("templates/commands/address-pr-review.md")
    assert "validate the batch once" in remediation
    assert "Replacing test scope does not silently drop a required validator" in remediation
    assert "do not expand remediation or retry silently" in remediation


def test_implement_and_verify_record_runs_for_reuse() -> None:
    for rel in ("templates/commands/implement.md", "templates/commands/verify.md"):
        assert "gates/test-evidence.md" in _flat(rel), rel
