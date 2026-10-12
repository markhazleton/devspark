# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for the shared `.knowledge` finding schema (`scripts/knowledge_findings.py`)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from knowledge_findings import make_finding, validate_finding  # noqa: E402


def _sample(**overrides):
    base = dict(
        category="knowledge-gap",
        severity="medium",
        confidence="high",
        subject="widgets/**",
        summary="No current knowledge covers widgets/**.",
        evidence=[{"type": "source-path", "path": "widgets/core.py"}],
        recommendation="Consider creating current knowledge for widgets.",
        changes_authoritative_truth=False,
        source="discover-knowledge",
    )
    base.update(overrides)
    return base


def test_make_finding_conforms_to_schema() -> None:
    finding = make_finding(**_sample())
    assert validate_finding(finding) == []


def test_finding_id_is_deterministic_for_same_identity() -> None:
    first = make_finding(**_sample())
    second = make_finding(**_sample())
    assert first["finding_id"] == second["finding_id"]


def test_finding_id_differs_for_different_subject() -> None:
    first = make_finding(**_sample())
    second = make_finding(**_sample(subject="other/**"))
    assert first["finding_id"] != second["finding_id"]


def test_invalid_category_rejected() -> None:
    try:
        make_finding(**_sample(category="not-a-real-category"))
    except ValueError:
        return
    raise AssertionError("expected ValueError for invalid category")


def test_validate_finding_flags_missing_keys() -> None:
    finding = make_finding(**_sample())
    del finding["recommendation"]
    errors = validate_finding(finding)
    assert any("missing keys" in e for e in errors)
