"""Review-stage divergence contract test (T055a).

Each review stage prompt MAY contain ``<!-- DIVERGENT: <id> -->`` markers.
Every such marker MUST also appear in
``.knowledge/entities/command-templates/review-stage-divergence.md`` so divergences are
documented in one place (FR-036).
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DIVERGENCE_DOC = (
    REPO_ROOT
    / ".knowledge"
    / "entities"
    / "command-templates"
    / "review-stage-divergence.md"
)
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
