# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract checks for /devspark-address-pr-review artifacts.

Run with: python tests/test_address_pr_review_contract.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
GIT_BASH = Path(r"C:\Program Files\Git\bin\bash.exe")
PWSH = shutil.which("pwsh")

REVIEW = """# Pull Request Review: Fixture

## Action Items

### Immediate Actions (Blocking — must resolve before merge)

- [ ] **C-01** `a.py:1` — crash on empty input
- [ ] **H-01** `a.py:2` — unchecked path
- [ ] **PRD1-01** `a.py:3` — code contradicts the knowledge node
- [ ] **H-02** `a.py:4` — risk accepted by the owner
- [ ] **H-03** `a.py:5` — already fixed upstream
- [x] **C-02** `a.py:6` — fixed in abc1234

### Recommended Improvements

- [ ] **M-01** `a.py:7` — rename helper
- [ ] **L-01** `a.py:8` — tidy comment
- [ ] **PRD5-01** `a.py:9` — optional knowledge note

### Constitution Improvements (Non-blocking — feed into `/devspark-evolve-constitution`)

- [ ] **CON-01** — clarify a principle

## Findings Detail

| ID | Status | Principle | File:Line | Issue | Fix |
|----|--------|-----------|-----------|-------|-----|
| H-03 | ✅ Resolved | Name | a.py:5 | already fixed | none |
"""

EXPECTED = {
    "C-01": ("auto", True),
    "H-01": ("auto", True),
    "PRD1-01": ("auto", True),
    "H-02": ("report", False),
    "H-03": ("report", False),
    "M-01": ("report", False),
    "L-01": ("report", False),
    "PRD5-01": ("report", False),
    "CON-01": ("evolve-constitution", False),
}


def _bash() -> str | None:
    if GIT_BASH.exists():
        return str(GIT_BASH)
    return shutil.which("bash")


def _review_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / ".devspark.work" / "pr-review").mkdir(parents=True)
    (repo / ".devspark.work" / "pr-review" / "pr-7.md").write_text(REVIEW, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30, stdin=subprocess.DEVNULL)
    return repo


def _parse(shell: str, repo: Path) -> dict:
    if shell == "pwsh":
        cmd = [PWSH, "-NoProfile", "-File", str(ROOT / "scripts/powershell/address-pr-review.ps1"), "-PrId", "7", "-Json"]
    else:
        cmd = [_bash(), str(ROOT / "scripts/bash/address-pr-review.sh"), "--pr-id", "7", "--json"]
    done = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, encoding="utf-8", timeout=60, stdin=subprocess.DEVNULL)
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


SHELLS = [
    pytest.param("pwsh", marks=pytest.mark.skipif(PWSH is None, reason="pwsh not available")),
    pytest.param("bash", marks=pytest.mark.skipif(_bash() is None, reason="bash not available")),
]


@pytest.mark.parametrize("shell", SHELLS)
def test_only_open_blocking_findings_are_auto_eligible(tmp_path, shell):
    result = _parse(shell, _review_repo(tmp_path))

    got = {f["id"]: (f["route"], f["auto_eligible"]) for f in result["open_findings"]}
    assert got == EXPECTED
    assert result["open_count"] == len(EXPECTED)
    assert result["auto_eligible_count"] == 3
    assert all(f["reason"] for f in result["open_findings"])


def test_both_shells_agree_on_eligibility(tmp_path):
    if PWSH is None or _bash() is None:
        pytest.skip("both shells are required")
    repo = _review_repo(tmp_path)
    keys = ("id", "severity", "status", "blocking", "auto_eligible", "route")
    ps = [{k: f[k] for k in keys} for f in _parse("pwsh", repo)["open_findings"]]
    sh = [{k: f[k] for k in keys} for f in _parse("bash", repo)["open_findings"]]
    assert ps == sh


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_command_and_script_contract() -> None:
    main()


def main() -> None:
    command = _read("templates/commands/address-pr-review.md")
    script = _read("scripts/powershell/address-pr-review.ps1")
    bash_script = _read("scripts/bash/address-pr-review.sh")
    hook = _read(".devspark/hooks/pre-commit-review-isolation.ps1")
    hook_readme = _read(".devspark/hooks/README.md")
    pr_review = _read("templates/commands/pr-review.md")
    constitution = _read(".knowledge/governance/constitution.md")

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
    assert "/devspark-pr-review UPDATE" in command

    assert "[string]$PrId" in script
    assert "[ValidateSet('code-only', 'review-only')]" in script
    assert "Code commit gate failed" in script
    assert "Review commit gate failed" in script
    assert "^\\s*-\\s*\\[\\s\\]\\s+\\*\\*((C|H|M|L|CON|PRD\\d+)-\\d{2,})\\*\\*" in script
    assert "--pr-id" in bash_script
    assert "--gate" in bash_script
    assert "Code commit gate failed" in bash_script
    assert "Review commit gate failed" in bash_script

    assert "PR review files must be committed in isolation" in hook
    assert ".git/hooks/pre-commit" in hook_readme

    assert "/devspark-address-pr-review {PR_ID}" in pr_review
    assert "PR Review Artifact Commit Discipline (MUST)" in constitution

    # The source repository bypasses DevSpark command overrides: its skill routes straight to templates/commands/.
    assert "templates/commands/address-pr-review.md" in (
        ROOT / ".github/skills/devspark-address-pr-review/SKILL.md"
    ).read_text(encoding="utf-8")

    print("Address PR review contract validated.")


if __name__ == "__main__":
    main()
