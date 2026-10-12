# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""The lifecycle router recognizes temporary unified quickfix records.

Run with: python tests/test_unified_quickfix_recognition_contract.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _copy_script_set(destination: Path) -> None:
    for rel_path in (
        Path("scripts/bash/common.sh"),
        Path("scripts/bash/next-context.sh"),
        Path("scripts/powershell/common.ps1"),
        Path("scripts/powershell/next-context.ps1"),
    ):
        target = destination / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel_path, target)


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, input="", timeout=30)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _init_git_repo(repo_root: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "DevSpark Test"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "devspark@example.com"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "checkout", "-b", "main"], cwd=repo_root, check=True, capture_output=True, text=True)


def _commit_all(repo_root: Path, message: str) -> None:
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo_root, check=True, capture_output=True, text=True)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _test_next_context_recognizes_unified_quickfix_branch() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "unified-quickfix-branch-fixture"
        repo_root.mkdir(parents=True, exist_ok=True)
        _copy_script_set(repo_root)
        _init_git_repo(repo_root)
        _write(repo_root / "pyproject.toml", '[project]\nname = "devspark-test"\nversion = "1.0.0"\n')
        _write(repo_root / ".knowledge" / "governance" / "constitution.md", "# Constitution\n")
        _commit_all(repo_root, "Initial commit")
        subprocess.run(["git", "checkout", "-b", "010-fix-timeout-retry"], cwd=repo_root, check=True, capture_output=True, text=True)
        _write(
            repo_root / ".devspark.work" / "quickfixes" / "010-fix-timeout-retry.md",
            "# Quickfix\n\n- **Completed**: 2026-07-24\n",
        )
        _commit_all(repo_root, "Add quickfix record for current branch")

        result = _run(["pwsh", "-NoProfile", "-File", "scripts/powershell/next-context.ps1", "-Json"], repo_root)
        check(result.returncode == 0, f"next-context.ps1 failed: {result.stderr}")
        data = json.loads(result.stdout)
        check(data.get("QUICKFIX_EXISTS") is True, f"expected unified-format quickfix branch to be recognized, got: {data}")
        check(data.get("QUICKFIX_COMPLETE") is True, f"expected quickfix completion to be detected, got: {data}")
        check(data.get("RECOMMENDED_COMMAND") == "/devspark-create-pr", f"expected a completed, committed quickfix to proceed to the PR, got: {data}")


def main() -> None:
    _test_next_context_recognizes_unified_quickfix_branch()
    print("unified quickfix recognition validated.")


if __name__ == "__main__":
    main()
