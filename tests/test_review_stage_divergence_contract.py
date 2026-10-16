# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Review-stage divergence contract test.

Each review stage prompt MAY contain ``<!-- DIVERGENT: <id> -->`` markers.
Every such marker MUST also appear in
``.knowledge/architecture/review-stage-divergence.md`` so divergences are
documented in one place.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DIVERGENCE_DOC = REPO_ROOT / ".knowledge" / "architecture" / "review-stage-divergence.md"
REVIEW_FILES = [
    REPO_ROOT / "templates" / "commands" / n
    for n in ("clarify.md", "analyze.md", "critic.md", "pr-review.md", "address-pr-review.md")
]
MARKER = re.compile(r"<!--\s*DIVERGENT:\s*([^\s>]+)\s*-->")


def test_divergence_doc_exists() -> None:
    assert DIVERGENCE_DOC.is_file(), f"missing {DIVERGENCE_DOC}"


def test_every_divergent_marker_is_documented() -> None:
    doc_text = DIVERGENCE_DOC.read_text(encoding="utf-8") if DIVERGENCE_DOC.is_file() else ""
    missing: list[str] = []
    for f in REVIEW_FILES:
        text = f.read_text(encoding="utf-8")
        for marker in MARKER.findall(text):
            if marker not in doc_text:
                missing.append(f"{f.name}::{marker}")
    assert not missing, f"undocumented divergence markers: {missing}"


def test_pr_state_ownership_metadata_cites_implementation_and_test_evidence() -> None:
    text = DIVERGENCE_DOC.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    metadata = yaml.safe_load(parts[1])

    assert metadata["type"] == "architecture"
    assert "scripts/pr-review-state.py" in metadata["appliesTo"]
    assert "scripts/pr-review-state.py" in metadata["source_of_truth"]
    assert "templates/pr-review-state-contract.md" in metadata["source_of_truth"]
    assert "tests/test_pr_review_state_contract.py" in metadata["source_of_truth"]
    assert "tests/test_address_pr_review_contract.py" in metadata["source_of_truth"]
