# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""
Contract tests for the Genuine Fix Discipline (anti-gaming) guidance.

command-preamble-contract.md section 9 (+ 9.1 intent-cue table) is the single
source of truth for anti-gaming remediation, and a fixed set of commands must
reference it: the fix/review commands that *act on* findings and the gate
commands that *generate* them. A future edit that drops the section, the table,
or a required reference would silently re-open the gaming gap these tests guard.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PREAMBLE = REPO_ROOT / "templates" / "preamble" / "finding-fix.md"
COMMANDS_DIR = REPO_ROOT / "templates" / "commands"

# Commands that must point back at the shared section 9 guidance.
REQUIRED_REFERENCERS = (
    "implement",
    "quickfix",
    "pr-review",
    "address-pr-review",
    "critic",
    "analyze",
    "verify",
    "site-audit",
)


def test_preamble_defines_genuine_fix_discipline_section() -> None:
    if not PREAMBLE.is_file():
        pytest.skip("finding-fix preamble module missing")
    text = PREAMBLE.read_text(encoding="utf-8")
    assert "## 9. Genuine Fix Discipline" in text, "section 9 heading missing"
    assert "### 9.1 Intent Cues for Common Structural Smells" in text, "9.1 intent-cue table heading missing"
    # The table must retain its column contract (starting-sentence intent cues).
    assert "Intent cue (say this first)" in text, "9.1 intent-cue table header missing"
    assert "Gamed fix looks like" in text, "9.1 gamed-fix column missing"


@pytest.mark.parametrize("command", REQUIRED_REFERENCERS)
def test_command_references_genuine_fix_discipline(command: str) -> None:
    path = COMMANDS_DIR / f"{command}.md"
    if not path.is_file():
        pytest.skip(f"{command}.md missing")
    text = path.read_text(encoding="utf-8")
    assert "command-preamble-contract.md" in text and "\u00a79" in text, (
        f"{command}.md must reference command-preamble-contract.md \u00a79 (Genuine Fix Discipline)"
    )
