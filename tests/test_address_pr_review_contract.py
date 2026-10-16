# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract checks for /devspark-address-pr-review artifacts.

Run with: python tests/test_address_pr_review_contract.py
"""

from __future__ import annotations

import atexit
import functools
import json
import os
import shutil
import subprocess
import tempfile
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
| H-03 | Open | Name | a.py:5 | already fixed upstream | none |
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


def _review_repo(tmp_path: Path, review: str = REVIEW) -> Path:
    repo = tmp_path / "repo"
    (repo / ".devspark.work" / "pr-review").mkdir(parents=True)
    (repo / ".devspark.work" / "pr-review" / "pr-7.md").write_text(review, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30, stdin=subprocess.DEVNULL)
    return repo


def _parse(shell: str, repo: Path, env: dict[str, str] | None = None) -> dict:
    if shell == "pwsh":
        cmd = [PWSH, "-NoProfile", "-File", str(ROOT / "scripts/powershell/address-pr-review.ps1"), "-PrId", "7", "-Json"]
    else:
        cmd = [_bash(), str(ROOT / "scripts/bash/address-pr-review.sh"), "--pr-id", "7", "--json"]
    child_env = os.environ.copy()
    if env:
        child_env.update(env)
    done = subprocess.run(
        cmd, cwd=repo, env=child_env, capture_output=True, text=True, encoding="utf-8",
        timeout=60, stdin=subprocess.DEVNULL
    )
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


def _is_python_name(name: str) -> bool:
    return name.lower().removesuffix(".exe").startswith("python")


@functools.lru_cache(maxsize=1)
def _path_without_python() -> str:
    entries = os.environ.get("PATH", "").split(os.pathsep)
    python_names = {"python.exe", "python3.exe", "python", "python3"}
    holds_python = [entry for entry in entries if any((Path(entry) / name).is_file() for name in python_names)]
    if os.name == "nt":
        return os.pathsep.join(entry for entry in entries if entry not in holds_python)

    # On POSIX the interpreter shares /usr/bin with git, dirname and the shells, so dropping the
    # whole directory would strip those too. Shadow each such directory without the python names.
    shadow_root = Path(tempfile.mkdtemp(prefix="no-python-path-"))
    atexit.register(shutil.rmtree, shadow_root, ignore_errors=True)
    retained: list[str] = []
    for entry in entries:
        if entry not in holds_python:
            retained.append(entry)
            continue
        shadow = shadow_root / str(len(retained))
        shadow.mkdir()
        for tool in sorted(Path(entry).iterdir()):
            if not _is_python_name(tool.name) and tool.is_file():
                (shadow / tool.name).symlink_to(tool)
        retained.append(str(shadow))
    return os.pathsep.join(retained)


def _parse_failure(shell: str, repo: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    if shell == "pwsh":
        cmd = [PWSH, "-NoProfile", "-File", str(ROOT / "scripts/powershell/address-pr-review.ps1"), "-PrId", "7", "-Json"]
    else:
        cmd = [_bash(), str(ROOT / "scripts/bash/address-pr-review.sh"), "--pr-id", "7", "--json"]
    child_env = os.environ.copy()
    child_env.update(env)
    return subprocess.run(
        cmd, cwd=repo, env=child_env, capture_output=True, text=True, encoding="utf-8",
        timeout=60, stdin=subprocess.DEVNULL
    )


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


def test_both_shells_agree_on_native_legacy_interpretation(tmp_path):
    if PWSH is None or _bash() is None:
        pytest.skip("both shells are required")
    repo = _review_repo(tmp_path)
    env = {"PATH": _path_without_python()}
    ps_result = _parse("pwsh", repo, env)
    sh_result = _parse("bash", repo, env)
    keys = ("finding_id", "aliases", "severity", "category", "blocking", "status",
            "outcome", "description", "expected_outcome", "evidence")
    ps = [{key: finding[key] for key in keys} for finding in ps_result["findings"]]
    sh = [{key: finding[key] for key in keys} for finding in sh_result["findings"]]
    assert ps == sh
    projection_keys = ("id", "severity", "status", "blocking", "auto_eligible", "route")
    ps_open = [{key: finding[key] for key in projection_keys} for finding in ps_result["open_findings"]]
    sh_open = [{key: finding[key] for key in projection_keys} for finding in sh_result["open_findings"]]
    assert ps_open == sh_open


@pytest.mark.parametrize("shell", SHELLS)
def test_legacy_alias_projection_preserves_compatibility_keys(tmp_path, shell):
    review = (ROOT / "tests/fixtures/pr-review-state/legacy-aliased.md").read_text(encoding="utf-8")
    result = _parse(shell, _review_repo(tmp_path, review))

    assert {"pr_id", "review_file", "open_findings", "open_count", "auto_eligible_count"} <= result.keys()
    assert {"findings", "pending_verification", "pending_verification_count",
            "unresolved_blockers", "recommendation", "diagnostics"} <= result.keys()
    finding = result["open_findings"][0]
    assert finding["id"] == "H-01"
    assert finding["severity"] == "H"
    assert finding["aliases"] == ["PRD3-01"]
    assert finding["lifecycle_state"] == "open"
    assert result["open_count"] == 1
    assert result["unresolved_blockers"] == 1


@pytest.mark.parametrize("shell", SHELLS)
def test_pending_verification_is_visible_but_not_author_auto_eligible(tmp_path, shell):
    review = (ROOT / "tests/fixtures/pr-review-state/modern-valid.md").read_text(encoding="utf-8")
    review = review.replace("status: open", "status: awaiting-verification")
    review = review.replace(
        "      remediation: null",
        """      remediation:
        correction_commit: "2222222222222222222222222222222222222222"
        author_context: synthetic-author
        explanation: "The expected boundary assertion was added."
        author_validation: "Synthetic focused test passed."
        """,
    )
    result = _parse(shell, _review_repo(tmp_path, review))

    assert result["pending_verification_count"] == 1
    assert result["pending_verification"][0]["finding_id"] == "H-01"
    assert result["open_findings"][0]["lifecycle_state"] == "awaiting-verification"
    assert result["open_findings"][0]["auto_eligible"] is False
    assert result["unresolved_blockers"] == 1


@pytest.mark.parametrize("shell", SHELLS)
def test_legacy_alias_is_readable_without_python(tmp_path, shell):
    review = (ROOT / "tests/fixtures/pr-review-state/legacy-aliased.md").read_text(encoding="utf-8")
    result = _parse(shell, _review_repo(tmp_path, review), {"PATH": _path_without_python()})

    assert result["findings"][0]["finding_id"] == "H-01"
    assert result["findings"][0]["aliases"] == ["PRD3-01"]
    assert result["unresolved_blockers"] == 1


@pytest.mark.parametrize(
    ("review", "finding_id", "lifecycle"),
    [
        ("# Findings (Non-blocking)\n\n| ID | Status | Issue |\n| --- | --- | --- |\n| M-03 | Open | Table-only concern. |\n", "M-03", "open"),
        ("# Findings (Non-blocking)\n\n- [ ] **L-04** Action-only concern.\n", "L-04", "open"),
        (
            "# Immediate Actions (Blocking)\n\n- [x] **H-05** Closed concern.\n\n| ID | Status | Issue |\n| --- | --- | --- |\n| H-05 | Resolved | Closed concern. |\n",
            "H-05",
            "resolved",
        ),
        ("# Findings\n\n```markdown\n- [ ] **H-99** Example only.\n```\n", None, None),
    ],
)
@pytest.mark.parametrize("shell", SHELLS)
def test_native_legacy_grammar_is_preserved_without_python(tmp_path, shell, review, finding_id, lifecycle):
    result = _parse(shell, _review_repo(tmp_path, review), {"PATH": _path_without_python()})

    if finding_id is None:
        assert result["findings"] == []
        return
    assert [finding["finding_id"] for finding in result["findings"]] == [finding_id]
    assert result["findings"][0]["status"] == lifecycle
    if lifecycle == "resolved":
        assert result["findings"][0]["outcome"] == "Legacy resolved"
        assert result["findings"][0]["verification"] is None


@pytest.mark.parametrize("shell", SHELLS)
def test_ambiguous_legacy_finding_is_not_inferred_from_severity_without_python(tmp_path, shell):
    review = "# High Priority Issues\n\n- [ ] **H-07** Unclassified concern.\n"
    result = _parse_failure(shell, _review_repo(tmp_path, review), {"PATH": _path_without_python()})

    assert result.returncode != 0
    assert '"code":"ambiguous-legacy-blocking"' in result.stdout


@pytest.mark.parametrize("shell", SHELLS)
def test_structured_record_fails_explicitly_without_python(tmp_path, shell):
    review = (ROOT / "tests/fixtures/pr-review-state/modern-valid.md").read_text(encoding="utf-8")
    result = _parse_failure(shell, _review_repo(tmp_path, review), {"PATH": _path_without_python()})

    assert result.returncode != 0
    assert "python" in (result.stderr + result.stdout).lower()


@pytest.mark.parametrize("shell", SHELLS)
def test_unchecked_action_with_closed_detail_row_is_diagnosed_without_python(tmp_path, shell):
    review = """# Immediate Actions (Blocking)

- [ ] **H-05** Conflicting closure state.

| ID | Status | Issue |
| --- | --- | --- |
| H-05 | Resolved | Conflicting closure state. |
"""
    result = _parse_failure(shell, _review_repo(tmp_path, review), {"PATH": _path_without_python()})

    assert result.returncode != 0
    assert "contradictory-legacy-status" in result.stdout


@pytest.mark.parametrize("shell", SHELLS)
def test_structured_record_fails_explicitly_without_pyyaml(tmp_path, shell):
    blocked_import = tmp_path / "blocked-import"
    blocked_import.mkdir()
    (blocked_import / "yaml.py").write_text('raise ImportError("synthetic unavailable")\n', encoding="utf-8")
    review = (ROOT / "tests/fixtures/pr-review-state/modern-valid.md").read_text(encoding="utf-8")
    result = _parse_failure(
        shell,
        _review_repo(tmp_path, review),
        {"PYTHONPATH": str(blocked_import) + os.pathsep + os.environ.get("PYTHONPATH", "")},
    )

    assert result.returncode != 0
    assert "yaml" in (result.stderr + result.stdout).lower()


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize(
    ("gate", "staged_path", "expected_returncode"),
    [
        ("code-only", ".devspark.work/pr-review/pr-7.md", 1),
        ("review-only", "src/change.py", 1),
    ],
)
def test_commit_isolation_gates_remain_enforced(tmp_path, shell, gate, staged_path, expected_returncode):
    repo = _review_repo(tmp_path)
    path = repo / staged_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("synthetic\n", encoding="utf-8")
    subprocess.run(["git", "add", staged_path], cwd=repo, check=True, timeout=30, stdin=subprocess.DEVNULL)
    if shell == "pwsh":
        cmd = [PWSH, "-NoProfile", "-File", str(ROOT / "scripts/powershell/address-pr-review.ps1"), "-Gate", gate]
    else:
        cmd = [_bash(), str(ROOT / "scripts/bash/address-pr-review.sh"), "--gate", gate]

    done = subprocess.run(
        cmd, cwd=repo, capture_output=True, text=True, encoding="utf-8", timeout=60, stdin=subprocess.DEVNULL
    )

    assert done.returncode == expected_returncode
    assert "commit gate failed" in done.stderr.lower()


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
    assert "$idPattern = '(?:CON|PRD\\d+|C|H|M|L)-\\d{2,}'" in script
    assert "grep -oE '(CON|PRD[0-9]+|C|H|M|L)-[0-9]{2,}'" in bash_script
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
