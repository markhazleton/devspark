# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Review-resolution contract test."""

from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
REVIEW_FILES = [
    REPO_ROOT / "templates" / "commands" / name
    for name in (
        "clarify.md",
        "analyze.md",
        "critic.md",
        "pr-review.md",
        "address-pr-review.md",
    )
]


REQUIRED_FIELDS = (
    "finding_id",
    "severity",
    "description",
    "recommended_action",
    "execution_mode",
    "status",
    "outcome",
)


@pytest.mark.parametrize("file", REVIEW_FILES, ids=lambda p: p.name)
def test_review_command_emits_shared_contract(file: Path) -> None:
    text = file.read_text(encoding="utf-8")
    assert "Shared Review Resolution Contract" in text, (
        f"{file.name} missing shared contract section"
    )
    for field in REQUIRED_FIELDS:
        assert field in text, f"{file.name} missing required field {field!r}"


def test_execution_mode_enum_advertised_consistently() -> None:
    """All five files must mention all three execution_mode values."""
    for file in REVIEW_FILES:
        text = file.read_text(encoding="utf-8")
        for mode in ("auto", "selective", "manual"):
            assert mode in text, f"{file.name} missing execution_mode value {mode!r}"


def test_finding_id_naming_convention_documented() -> None:
    """All five files reference stable finding_id naming."""
    pattern = re.compile(r"finding_id", re.IGNORECASE)
    for file in REVIEW_FILES:
        assert pattern.search(file.read_text(encoding="utf-8")), file.name


def test_pr_lifecycle_extension_does_not_change_other_review_stages() -> None:
    for file in REVIEW_FILES[:3]:
        assert "DIVERGENT: pr-review-state" not in file.read_text(encoding="utf-8")

    pr_review = REVIEW_FILES[3].read_text(encoding="utf-8")
    address = REVIEW_FILES[4].read_text(encoding="utf-8")
    assert "pr-review-state" in pr_review
    assert "do not export PR-only" in pr_review
    assert "select it without a redundant selection question" in address
    assert "does not start another address/review reconciliation cycle" in address


def test_pr_update_finishes_evaluation_and_derived_state_in_one_operation() -> None:
    text = REVIEW_FILES[3].read_text(encoding="utf-8")
    assert "bounded independent evaluation" in text
    assert "do not require an additional reconciliation command" in text
    assert "run `scripts/pr-review-validate.py` against the resulting file" in text
