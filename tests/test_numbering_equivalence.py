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
    return shutil.which("bash") is not None


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


def _build_repo(branches: list[str], spec_dirs: list[str], quickfix_files: list[str]) -> Path:
    temp_dir = Path(tempfile.mkdtemp())
    repo_root = temp_dir / "numbering-fixture"
    repo_root.mkdir(parents=True, exist_ok=True)
    _copy_script_set(repo_root)

    _git(["init"], repo_root)
    _git(["config", "user.name", "DevSpark Test"], repo_root)
    _git(["config", "user.email", "devspark@example.com"], repo_root)
    _git(["checkout", "-b", "main"], repo_root)
    (repo_root / "README.md").write_text("# test\n", encoding="utf-8")
    _git(["add", "."], repo_root)
    _git(["commit", "-m", "init"], repo_root)

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
        ["pwsh", "-NoProfile", "-File", "scripts/powershell/new-branch.ps1", "-Type", "spec", "-Json", "-DryRun", "probe"],
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
        ["bash", "scripts/bash/new-branch.sh", "--type", "spec", "--json", "--dry-run", "probe"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        input="",
        timeout=30,
    )
    assert result.returncode == 0, f"new-branch.sh failed: {result.stderr}"
    return int(json.loads(result.stdout)["NUMBER"])


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
