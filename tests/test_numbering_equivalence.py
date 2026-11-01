# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Numbering equivalence tests.

Verifies that the unified allocator (`Get-NextUnifiedIndex` / PowerShell,
`get_next_unified_index` / Bash) returns the exact golden values frozen in
`tests/fixtures/numbering_corpus.md` -- both for the legacy-only cases
(L1-L6, no quickfix records: these must match the now-removed
`Get-NextBranchNumber` baseline) and the unified cases (U1-U4, which add
quickfix records to the scan).

Run with: pytest tests/test_numbering_equivalence.py -v
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from tests.bash_twin import BASH_EXE

ROOT = Path(__file__).resolve().parent.parent

# (case_id, branches, spec_dirs, quickfix_filenames, expected_number)
GOLDEN_CASES = [
    ("L1", [], [], [], 1),
    ("L2", ["001-foo", "007-bar"], ["003-x"], [], 8),
    ("L3", [], ["012-y"], [], 13),
    ("L4", ["005-a"], ["005-a"], [], 6),
    ("L5", ["0042-z"], [], [], 43),
    ("L6", ["003-a", "feature/misc"], ["003-a"], [], 4),
    ("U1", ["007-spec-foo"], ["007-spec-foo"], ["QF-2026-003.md"], 8),
    ("U2", ["009-fix-x"], [], ["009-fix-x.md"], 10),
    ("U3", [], [], ["QF-2026-005.md"], 6),
    ("U4", ["002-spec-a"], ["002-spec-a"], [], 3),
]


def _has_bash() -> bool:
    return BASH_EXE is not None


def _has_pwsh() -> bool:
    return shutil.which("pwsh") is not None


def _copy_script_set(destination: Path) -> None:
    for rel_path in (
        Path("scripts/bash/common.sh"),
        Path("scripts/bash/new-branch.sh"),
        Path("scripts/powershell/common.ps1"),
        Path("scripts/powershell/new-branch.ps1"),
    ):
        target = destination / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel_path, target)


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


_BASE_TEMPLATE: Path | None = None
_TEMP_ROOT: tempfile.TemporaryDirectory | None = None


def _get_base_template() -> Path:
    global _BASE_TEMPLATE, _TEMP_ROOT
    if _BASE_TEMPLATE is None:
        _TEMP_ROOT = tempfile.TemporaryDirectory()
        _BASE_TEMPLATE = Path(_TEMP_ROOT.name) / "base"
        _BASE_TEMPLATE.mkdir(parents=True, exist_ok=True)
        _copy_script_set(_BASE_TEMPLATE)
        _git(["init"], _BASE_TEMPLATE)
        _git(["config", "user.name", "DevSpark Test"], _BASE_TEMPLATE)
        _git(["config", "user.email", "devspark@example.com"], _BASE_TEMPLATE)
        _git(["checkout", "-b", "main"], _BASE_TEMPLATE)
        (_BASE_TEMPLATE / "README.md").write_text("# test\n", encoding="utf-8")
        _git(["add", "."], _BASE_TEMPLATE)
        _git(["commit", "-m", "init"], _BASE_TEMPLATE)
    return _BASE_TEMPLATE


def _build_repo(branches: list[str], spec_dirs: list[str], quickfix_files: list[str]) -> Path:
    temp_dir = Path(tempfile.mkdtemp())
    repo_root = temp_dir / "numbering-fixture"
    base = _get_base_template()
    shutil.copytree(base, repo_root)

    for spec_dir in spec_dirs:
        spec_path = repo_root / ".devspark.work" / "specs" / spec_dir
        spec_path.mkdir(parents=True, exist_ok=True)
        (spec_path / "spec.md").write_text("# spec\n", encoding="utf-8")

    for quickfix_file in quickfix_files:
        quickfix_dir = repo_root / ".devspark.work" / "quickfixes"
        quickfix_dir.mkdir(parents=True, exist_ok=True)
        (quickfix_dir / quickfix_file).write_text("# quickfix\n", encoding="utf-8")

    if spec_dirs or quickfix_files:
        _git(["add", "."], repo_root)
        _git(["commit", "-m", "seed spec/quickfix records"], repo_root)

    for branch in branches:
        # feature/misc and similar non-numeric-prefixed branches must exist
        # too, to prove the allocator correctly ignores them.
        _git(["branch", branch], repo_root)

    return repo_root


def _next_number_pwsh(repo_root: Path) -> int:
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-File", "scripts/powershell/new-branch.ps1", "-Type", "fix", "-Json", "-DryRun", "probe"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        input="",
        timeout=30,
    )
    assert result.returncode == 0, f"new-branch.ps1 failed: {result.stderr}"
    return int(json.loads(result.stdout)["NUMBER"])


def _next_number_bash(repo_root: Path) -> int:
    result = subprocess.run(
        [BASH_EXE, "scripts/bash/new-branch.sh", "--type", "fix", "--json", "--dry-run", "probe"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        input="",
        timeout=30,
    )
    assert result.returncode == 0, f"new-branch.sh failed: {result.stderr}"
    return int(json.loads(result.stdout)["NUMBER"])


def _create_work_branch(repo_root: Path, shell: str) -> dict:
    if shell == "pwsh":
        command = ["pwsh", "-NoProfile", "-File", "scripts/powershell/new-branch.ps1", "-Type", "work", "-Json", "-Yes", "Resume a bug fix"]
    else:
        command = [BASH_EXE, "scripts/bash/new-branch.sh", "--type", "work", "--json", "--yes", "Resume a bug fix"]
    result = subprocess.run(command, cwd=repo_root, text=True, capture_output=True, timeout=30, stdin=subprocess.DEVNULL)
    assert result.returncode == 0, f"work branch creation failed: {result.stderr}"
    return json.loads(result.stdout)


@pytest.mark.skipif(not _has_pwsh(), reason="pwsh not available")
@pytest.mark.parametrize("case_id,branches,spec_dirs,quickfix_files,expected", GOLDEN_CASES, ids=[c[0] for c in GOLDEN_CASES])
def test_unified_allocator_matches_golden_case_pwsh(case_id, branches, spec_dirs, quickfix_files, expected) -> None:
    repo_root = _build_repo(branches, spec_dirs, quickfix_files)
    try:
        assert _next_number_pwsh(repo_root) == expected, f"{case_id}: expected {expected}"
    finally:
        shutil.rmtree(repo_root.parent, ignore_errors=True)


@pytest.mark.skipif(not _has_bash(), reason="bash not available")
@pytest.mark.parametrize("case_id,branches,spec_dirs,quickfix_files,expected", GOLDEN_CASES, ids=[c[0] for c in GOLDEN_CASES])
def test_unified_allocator_matches_golden_case_bash(case_id, branches, spec_dirs, quickfix_files, expected) -> None:
    repo_root = _build_repo(branches, spec_dirs, quickfix_files)
    try:
        assert _next_number_bash(repo_root) == expected, f"{case_id}: expected {expected}"
    finally:
        shutil.rmtree(repo_root.parent, ignore_errors=True)


@pytest.mark.skipif(not _has_pwsh(), reason="pwsh not available")
def test_work_branch_creates_no_artifact_pwsh() -> None:
    repo_root = _build_repo([], [], [])
    try:
        result = _create_work_branch(repo_root, "pwsh")
        assert result["TYPE"] == "work"
        assert result["BRANCH_NAME"].startswith("001-work-")
        assert result["SWITCHED"] is True
        assert not Path(result["ARTIFACT_PATH"]).exists()
        assert not (repo_root / ".devspark.work" / "specs" / result["BRANCH_NAME"]).exists()
    finally:
        shutil.rmtree(repo_root.parent, ignore_errors=True)


@pytest.mark.skipif(not _has_bash(), reason="bash not available")
def test_work_branch_creates_no_artifact_bash() -> None:
    repo_root = _build_repo([], [], [])
    try:
        result = _create_work_branch(repo_root, "bash")
        assert result["TYPE"] == "work"
        assert result["BRANCH_NAME"].startswith("001-work-")
        assert result["SWITCHED"] is True
        assert not Path(result["ARTIFACT_PATH"]).exists()
        assert not (repo_root / ".devspark.work" / "specs" / result["BRANCH_NAME"]).exists()
    finally:
        shutil.rmtree(repo_root.parent, ignore_errors=True)


@pytest.mark.parametrize("shell", ["pwsh", "bash"])
def test_work_branch_requires_git(shell: str, tmp_path: Path) -> None:
    repo_root = tmp_path / "no-git-repo"
    repo_root.mkdir()
    _copy_script_set(repo_root)
    (repo_root / "README.md").write_text("# test\n", encoding="utf-8")
    if shell == "pwsh":
        command = ["pwsh", "-NoProfile", "-File", "scripts/powershell/new-branch.ps1", "-Type", "work", "-Json", "-Yes", "Resume a bug fix"]
    else:
        command = [BASH_EXE, "scripts/bash/new-branch.sh", "--type", "work", "--json", "--yes", "Resume a bug fix"]
    result = subprocess.run(command, cwd=repo_root, text=True, capture_output=True, timeout=30, stdin=subprocess.DEVNULL)
    assert result.returncode != 0
    assert "work branches require a Git repository" in result.stderr


def _declared_specify_command(shell: str, description: str, confirmed: bool = True) -> list[str]:
    """The exact branch-creation command /devspark-specify declares, mapped onto source paths."""
    import shlex

    import yaml

    text = (ROOT / "templates" / "commands" / "specify.md").read_text(encoding="utf-8")
    frontmatter = yaml.safe_load(text.split("---", 2)[1])
    declared = frontmatter["scripts"]["ps" if shell == "pwsh" else "sh"]
    argv = shlex.split(declared.replace(".devspark/scripts/", "scripts/"))
    argv = [description if token == "$ARGUMENTS" else token for token in argv]
    if not confirmed:
        argv = [token for token in argv if token not in ("--yes", "-Yes")]
    return ["pwsh", "-NoProfile", "-File", *argv] if shell == "pwsh" else [BASH_EXE, *argv]


@pytest.mark.parametrize("shell", ["pwsh", "bash"])
def test_specify_declares_the_confirmed_noninteractive_branch_flag(shell: str) -> None:
    command = _declared_specify_command(shell, "probe")
    assert ("-Yes" if shell == "pwsh" else "--yes") in command
    assert ("-Type" if shell == "pwsh" else "--type") in command and "work" in command


@pytest.mark.parametrize("shell", ["pwsh", "bash"])
def test_specify_declared_command_creates_the_work_branch_without_a_tty(shell: str) -> None:
    if shell == "pwsh" and not _has_pwsh():
        pytest.skip("pwsh not available")
    if shell == "bash" and not _has_bash():
        pytest.skip("bash not available")
    repo_root = _build_repo([], [], [])
    try:
        result = subprocess.run(
            _declared_specify_command(shell, "Start catalog search"),
            cwd=repo_root, text=True, capture_output=True, timeout=30, stdin=subprocess.DEVNULL,
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["TYPE"] == "work" and payload["SWITCHED"] is True
        current = subprocess.run(
            ["git", "branch", "--show-current"], cwd=repo_root, text=True, capture_output=True, timeout=30, check=True
        ).stdout.strip()
        assert current == payload["BRANCH_NAME"] and current.startswith("001-work-")
    finally:
        shutil.rmtree(repo_root.parent, ignore_errors=True)


@pytest.mark.parametrize("shell", ["pwsh", "bash"])
def test_branch_creation_still_fails_closed_without_confirmation(shell: str) -> None:
    if shell == "pwsh" and not _has_pwsh():
        pytest.skip("pwsh not available")
    if shell == "bash" and not _has_bash():
        pytest.skip("bash not available")
    repo_root = _build_repo([], [], [])
    try:
        result = subprocess.run(
            _declared_specify_command(shell, "Start catalog search", confirmed=False),
            cwd=repo_root, text=True, capture_output=True, timeout=30, stdin=subprocess.DEVNULL,
        )
        assert result.returncode != 0
        assert "refusing to switch branches without confirmation" in result.stderr
        current = subprocess.run(
            ["git", "branch", "--show-current"], cwd=repo_root, text=True, capture_output=True, timeout=30, check=True
        ).stdout.strip()
        assert current == "main"
    finally:
        shutil.rmtree(repo_root.parent, ignore_errors=True)
