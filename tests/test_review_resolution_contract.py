"""Review-resolution contract test (T050)."""

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
