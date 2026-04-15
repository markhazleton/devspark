"""Validation for release-context recovery from archive and git history.

Run with: python tests/test_release_context_recovery.py
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
        Path("scripts/bash/release-context.sh"),
        Path("scripts/bash/release-history-context.sh"),
        Path("scripts/powershell/common.ps1"),
        Path("scripts/powershell/release-context.ps1"),
        Path("scripts/powershell/release-history-context.ps1"),
    ):
        target = destination / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel_path, target)


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=True)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _init_git_repo(repo_root: Path) -> None:
    _run(["git", "init"], repo_root)
    _run(["git", "config", "user.name", "DevSpark Test"], repo_root)
    _run(["git", "config", "user.email", "devspark@example.com"], repo_root)
    _run(["git", "checkout", "-b", "main"], repo_root)


def _commit_all(repo_root: Path, message: str) -> None:
    _run(["git", "add", "."], repo_root)
    _run(["git", "commit", "-m", message], repo_root)


def _build_release_fixture(repo_root: Path) -> None:
    _write(repo_root / "pyproject.toml", '[project]\nname = "devspark-test"\nversion = "1.0.0"\n')
    _write(repo_root / ".documentation" / "memory" / "constitution.md", "# Constitution\n")
    _write(repo_root / ".documentation" / "specs" / "001-release-recovery" / "spec.md", "# Spec\n")
    _write(
        repo_root / ".documentation" / "specs" / "001-release-recovery" / "tasks.md",
        "# Tasks\n\n- [x] T001 Completed\n- [x] T002 Completed\n",
    )
    _write(repo_root / ".documentation" / "quickfixes" / "QF-2026-001.md", "# Quickfix\n")
    _write(
        repo_root / ".documentation" / "specs" / "pr-review" / "pr-22.md",
        """---
pr_number: 22
---

# PR Review: #22 Release Recovery

## Stats

- Files changed: 7
- Tests added: 3
- Breaking changes: 1

## Findings

### H-01 Resolved

Resolved high-severity issue.
""",
    )


def _archive_release_inputs(repo_root: Path, archive_date: str) -> None:
    spec_src = repo_root / ".documentation" / "specs" / "001-release-recovery"
    spec_dest = repo_root / ".archive" / archive_date / ".documentation" / "specs" / "001-release-recovery"
    quickfix_src = repo_root / ".documentation" / "quickfixes" / "QF-2026-001.md"
    quickfix_dest = repo_root / ".archive" / archive_date / ".documentation" / "quickfixes" / "QF-2026-001.md"

    spec_dest.parent.mkdir(parents=True, exist_ok=True)
    quickfix_dest.parent.mkdir(parents=True, exist_ok=True)

    shutil.move(spec_src.as_posix(), spec_dest.as_posix())
    shutil.move(quickfix_src.as_posix(), quickfix_dest.as_posix())

    (repo_root / ".documentation" / "specs").mkdir(parents=True, exist_ok=True)
    (repo_root / ".documentation" / "quickfixes").mkdir(parents=True, exist_ok=True)


def _run_pwsh_release_context(repo_root: Path) -> dict:
    result = _run(["pwsh", "-NoProfile", "-File", "scripts/powershell/release-context.ps1", "-Json"], repo_root)
    return json.loads(result.stdout)


def _run_pwsh_release_history(repo_root: Path, base_ref: str) -> dict:
    result = _run(
        ["pwsh", "-NoProfile", "-File", "scripts/powershell/release-history-context.ps1", "-BaseRef", base_ref, "-Json"],
        repo_root,
    )
    return json.loads(result.stdout)


def _run_bash_release_context(repo_root: Path) -> dict | None:
    if not shutil.which("bash") or not shutil.which("jq"):
        return None
    result = _run(["bash", "scripts/bash/release-context.sh", "--json"], repo_root)
    return json.loads(result.stdout)


def _run_bash_release_history(repo_root: Path, base_ref: str) -> dict | None:
    if not shutil.which("bash"):
        return None
    result = _run(["bash", "scripts/bash/release-history-context.sh", "--json", "--base-ref", base_ref], repo_root)
    return json.loads(result.stdout)


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "release-recovery-fixture"
        repo_root.mkdir(parents=True, exist_ok=True)
        _copy_script_set(repo_root)
        _init_git_repo(repo_root)
        _build_release_fixture(repo_root)
        _commit_all(repo_root, "Initial release inputs")
        _run(["git", "tag", "v1.0.0"], repo_root)

        _archive_release_inputs(repo_root, "2026-04-15")

        pwsh_context = _run_pwsh_release_context(repo_root)
        assert "001-release-recovery" in pwsh_context["COMPLETED_SPECS"]
        assert "QF-2026-001" in pwsh_context["QUICKFIXES"]
        assert pwsh_context["ARCHIVE_RECOVERY_USED"] is True

        bash_context = _run_bash_release_context(repo_root)
        if bash_context is not None:
            assert "001-release-recovery" in bash_context["COMPLETED_SPECS"]
            assert "QF-2026-001" in bash_context["QUICKFIXES"]
            assert bash_context["ARCHIVE_RECOVERY_USED"] is True

        _commit_all(repo_root, "Archive completed release inputs (#22)")

        pwsh_context_after_commit = _run_pwsh_release_context(repo_root)
        assert pwsh_context_after_commit["RELEASE_FROM"] == "2026-04-15"
        assert pwsh_context_after_commit["RELEASE_TO"] == "2026-04-15"
        assert pwsh_context_after_commit["MERGED_PR_COUNT"] == 1
        assert 22 in pwsh_context_after_commit["MERGED_PR_NUMBERS"]
        assert pwsh_context_after_commit["PR_REVIEW_SUMMARY"]["files_changed"] == 7
        assert pwsh_context_after_commit["PR_REVIEW_SUMMARY"]["tests_added"] == 3
        assert pwsh_context_after_commit["PR_REVIEW_SUMMARY"]["breaking_changes"] == 1

        bash_context_after_commit = _run_bash_release_context(repo_root)
        if bash_context_after_commit is not None:
            assert bash_context_after_commit["RELEASE_FROM"] == "2026-04-15"
            assert bash_context_after_commit["RELEASE_TO"] == "2026-04-15"
            assert bash_context_after_commit["MERGED_PR_COUNT"] == 1
            assert 22 in bash_context_after_commit["MERGED_PR_NUMBERS"]
            assert bash_context_after_commit["PR_REVIEW_SUMMARY"]["files_changed"] == 7
            assert bash_context_after_commit["PR_REVIEW_SUMMARY"]["tests_added"] == 3
            assert bash_context_after_commit["PR_REVIEW_SUMMARY"]["breaking_changes"] == 1

        pwsh_history = _run_pwsh_release_history(repo_root, "v1.0.0")
        assert pwsh_history["RELEASE_FROM"] == "2026-04-15"
        assert pwsh_history["RELEASE_TO"] == "2026-04-15"
        assert pwsh_history["MERGED_PR_COUNT"] == 1
        assert 22 in pwsh_history["MERGED_PR_NUMBERS"]
        assert pwsh_history["PR_REVIEW_SUMMARY"]["files_changed"] == 7
        assert pwsh_history["PR_REVIEW_SUMMARY"]["tests_added"] == 3
        assert pwsh_history["PR_REVIEW_SUMMARY"]["breaking_changes"] == 1
        assert any(item["name"] == "001-release-recovery" and item["completed"] for item in pwsh_history["RECOVERED_SPECS"])
        assert any(item["id"] == "QF-2026-001" for item in pwsh_history["RECOVERED_QUICKFIXES"])
        assert pwsh_history["ARCHIVE_MOVES_DETECTED"] is True

        bash_history = _run_bash_release_history(repo_root, "v1.0.0")
        if bash_history is not None:
            assert bash_history["RELEASE_FROM"] == "2026-04-15"
            assert bash_history["RELEASE_TO"] == "2026-04-15"
            assert bash_history["MERGED_PR_COUNT"] == 1
            assert 22 in bash_history["MERGED_PR_NUMBERS"]
            assert bash_history["PR_REVIEW_SUMMARY"]["files_changed"] == 7
            assert bash_history["PR_REVIEW_SUMMARY"]["tests_added"] == 3
            assert bash_history["PR_REVIEW_SUMMARY"]["breaking_changes"] == 1
            assert any(item["name"] == "001-release-recovery" and item["completed"] for item in bash_history["RECOVERED_SPECS"])
            assert any(item["id"] == "QF-2026-001" for item in bash_history["RECOVERED_QUICKFIXES"])
            assert bash_history["ARCHIVE_MOVES_DETECTED"] is True

    print("release-context recovery validated.")


if __name__ == "__main__":
    main()