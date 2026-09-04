"""Contracts for the ad-hoc, current-truth-grounded explain command."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_explain_prompt_has_scope_output_and_write_safety_contracts() -> None:
    command = _read("templates/commands/explain.md")

    assert "explain-context.sh $ARGUMENTS --json" in command
    assert "explain-context.ps1 $ARGUMENTS -Json" in command
    assert "not part of the `specify -> plan -> tasks -> implement` gate chain" in command
    assert "never changes application code or tests" in command
    assert "Do not modify any file until the user explicitly confirms" in command
    assert "With `--dry-run`, make no writes" in command
    assert '"handoff": "/devspark.specify"' in command
    assert "No DELTA/KNOW findings for this topic." in command

    answer = command.index("### `## Answer`")
    findings = command.index("### `## Findings`")
    summary = command.index("### `## Agent Summary`")
    assert answer < findings < summary

    for code in ("DELTA1", "DELTA2", "DELTA3", "DELTA4", "KNOW1", "KNOW2", "KNOW3", "KNOW4"):
        assert code in command
        assert code in _read("templates/commands/site-audit.md")


def test_explain_shims_and_documentation_are_present() -> None:
    expected = {
        ".claude/commands/devspark.explain.md": "templates/commands/explain.md",
        ".github/agents/devspark.explain.agent.md": "templates/commands/explain.md",
        ".github/prompts/devspark.explain.prompt.md": "devspark.explain",
        "templates/prompts/atomic/explain.md": "templates/commands/explain.md",
        ".knowledge/entities/product-documentation/site/explain-usage.md": "/devspark.explain",
    }
    for relative, token in expected.items():
        assert (ROOT / relative).is_file(), relative
        assert token in _read(relative)


@pytest.mark.skipif(
    shutil.which("rg") is None or shutil.which("jq") is None or shutil.which("git") is None,
    reason="explain-context smoke test requires git, rg, and jq",
)
def test_bash_explain_context_is_bounded_read_only_and_honors_dry_run(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".knowledge/entities/auth").mkdir(parents=True)
    (tmp_path / ".knowledge/entities/auth/architecture.md").write_text(
        "Authentication uses TokenService.\n", encoding="utf-8"
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src/auth.py").write_text(
        "class TokenService:\n    pass\n", encoding="utf-8"
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_auth.py").write_text(
        "def test_authentication():\n    assert True\n", encoding="utf-8"
    )
    (tmp_path / ".archive/old").mkdir(parents=True)
    (tmp_path / ".archive/old/auth.py").write_text("authentication", encoding="utf-8")
    (tmp_path / ".devspark.work/specs/001-auth").mkdir(parents=True)
    (tmp_path / ".devspark.work/specs/001-auth/spec.md").write_text(
        "authentication", encoding="utf-8"
    )

    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file())
    completed = subprocess.run(
        [
            "bash",
            str(ROOT / "scripts/bash/explain-context.sh"),
            "how is authentication done",
            "--dry-run",
            "--json",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file())

    assert payload["topic"] == "how is authentication done"
    assert payload["dry_run"] is True
    assert ".knowledge/entities/auth/architecture.md" in payload["knowledge_matches"]
    assert "src/auth.py" in payload["code_matches"]
    assert "tests/test_auth.py" in payload["test_matches"]
    assert all(not path.startswith(".archive/") for path in payload["code_matches"])
    assert all(not path.startswith(".devspark.work/") for path in payload["code_matches"])
    assert payload["constraints"]["read_only"] is True
    assert before == after


def test_powershell_context_declares_equivalent_contract() -> None:
    bash = _read("scripts/bash/explain-context.sh")
    powershell = _read("scripts/powershell/explain-context.ps1")
    for token in ("topic", "terms", "dry_run", "knowledge_matches", "code_matches", "test_matches"):
        assert token in bash
        assert token in powershell
    for excluded in (".archive", ".devspark.work", ".documentation"):
        assert excluded in bash
        assert excluded in powershell
