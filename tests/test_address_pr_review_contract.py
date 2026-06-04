"""Contract checks for /devspark.address-pr-review artifacts.

Run with: python tests/test_address_pr_review_contract.py
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def main() -> None:
    command = _read("templates/commands/address-pr-review.md")
    script = _read("scripts/powershell/address-pr-review.ps1")
    bash_script = _read("scripts/bash/address-pr-review.sh")
    hook = _read(".devspark/hooks/pre-commit-review-isolation.ps1")
    hook_readme = _read(".devspark/hooks/README.md")
    pr_review = _read("templates/commands/pr-review.md")
    claude_shim = _read(".claude/commands/devspark.address-pr-review.md")
    copilot_shim = _read(".github/prompts/devspark.address-pr-review.prompt.md")
    constitution = _read(".documentation/memory/constitution.md")

    for phase in range(0, 8):
        assert f"Phase {phase}" in command

    assert "-Gate code-only" in command
    assert "-Gate review-only" in command
    assert "--pr-id {PR_ID} --json" in command
    assert "--gate code-only" in command
    assert "--gate review-only" in command
    assert "sh: .devspark/scripts/bash/address-pr-review.sh --pr-id $ARGUMENTS --json" in command
    assert "git log HEAD~2..HEAD --name-only" in command
    assert "Nothing to address." in command
    assert "/devspark.pr-review UPDATE" in command

    assert "[string]$PrId" in script
    assert "[ValidateSet('code-only', 'review-only')]" in script
    assert "Code commit gate failed" in script
    assert "Review commit gate failed" in script
    assert "^\\s*-\\s*\\[\\s\\]\\s+\\*\\*((C|H|M|L|CON)-\\d{2})\\*\\*" in script
    assert "--pr-id" in bash_script
    assert "--gate" in bash_script
    assert "Code commit gate failed" in bash_script
    assert "Review commit gate failed" in bash_script

    assert "PR review files must be committed in isolation" in hook
    assert ".git/hooks/pre-commit" in hook_readme

    assert "/devspark.address-pr-review {PR_ID}" in pr_review
    assert "templates/commands/address-pr-review.md" in claude_shim
    assert "agent: devspark.address-pr-review" in copilot_shim
    assert "PR Review Artifact Commit Discipline (MUST)" in constitution

    print("Address PR review contract validated.")


if __name__ == "__main__":
    main()
