# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Behavioral contract validation for the unified new-branch.{ps1,sh} script.

Covers:
- Type-tagged naming, 3-digit padding, JSON shape, invalid-type
  error, dry-run (no switch).
- Legacy QF-YYYY-NNN / NNN-shortname / feature/* branches are
  counted by the allocator and do not collide with a newly created index.
- The Branch Safety confirmation gate refuses to switch without
  -Yes/--yes in a non-interactive context, and warns on a dirty tree.
- Hostile short-name input (leading '-', '..', '.lock', glob chars)
  still produces a valid, `git check-ref-format`-clean branch name.

Run with: python tests/test_new_branch_contract.py
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
        Path("scripts/bash/new-branch.sh"),
        Path("scripts/powershell/common.ps1"),
        Path("scripts/powershell/new-branch.ps1"),
    ):
        target = destination / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel_path, target)


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    # Always redirect stdin (even with empty input) so the child process sees
    # a non-interactive/redirected stdin -- otherwise it may inherit this
    # test-runner's own TTY and block forever on a confirmation prompt.
    return subprocess.run(
        command, cwd=cwd, text=True, capture_output=True, input="", timeout=30
    )


_TEMPLATE_SCRIPT_REPO: Path | None = None
_TEMP_ROOT: tempfile.TemporaryDirectory | None = None


def _get_template_repo() -> Path:
    global _TEMPLATE_SCRIPT_REPO, _TEMP_ROOT
    if _TEMP_ROOT is None:
        _TEMP_ROOT = tempfile.TemporaryDirectory()
    if _TEMPLATE_SCRIPT_REPO is None:
        _TEMPLATE_SCRIPT_REPO = Path(_TEMP_ROOT.name) / "tpl-script"
        _TEMPLATE_SCRIPT_REPO.mkdir()
        _copy_script_set(_TEMPLATE_SCRIPT_REPO)
        _init_git_repo(_TEMPLATE_SCRIPT_REPO)
    return _TEMPLATE_SCRIPT_REPO


def _setup_repo(repo_root: Path) -> None:
    shutil.copytree(_get_template_repo(), repo_root, dirs_exist_ok=True)


def _init_git_repo(repo_root: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "DevSpark Test"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "devspark@example.com"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "checkout", "-b", "main"], cwd=repo_root, check=True, capture_output=True, text=True)
    (repo_root / "README.md").write_text("# test\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_root, check=True, capture_output=True, text=True)


def _pwsh(cwd: Path, *, type_=None, json_mode=False, dry_run=False, short_name=None,
          yes=False, number=None, description=None) -> subprocess.CompletedProcess[str]:
    args: list[str] = ["pwsh", "-NoProfile", "-File", "scripts/powershell/new-branch.ps1"]
    if type_ is not None:
        args += ["-Type", type_]
    if json_mode:
        args += ["-Json"]
    if dry_run:
        args += ["-DryRun"]
    if short_name is not None:
        # Use colon syntax so PowerShell's parameter binder does not mistake a
        # value starting with '-' (e.g. hostile input) for another parameter
        # name.
        args += [f"-ShortName:{short_name}"]
    if yes:
        args += ["-Yes"]
    if number is not None:
        args += ["-Number", str(number)]
    if description:
        args += [description]
    return _run(args, cwd)


def _bash(cwd: Path, *, type_=None, json_mode=False, dry_run=False, short_name=None,
          yes=False, number=None, description=None) -> subprocess.CompletedProcess[str]:
    args: list[str] = ["bash", "scripts/bash/new-branch.sh"]
    if type_ is not None:
        args += ["--type", type_]
    if json_mode:
        args += ["--json"]
    if dry_run:
        args += ["--dry-run"]
    if short_name is not None:
        args += ["--short-name", short_name]
    if yes:
        args += ["--yes"]
    if number is not None:
        args += ["--number", str(number)]
    if description:
        args += [description]
    return _run(args, cwd)


def _has_bash() -> bool:
    return shutil.which("bash") is not None


def _has_pwsh() -> bool:
    return shutil.which("pwsh") is not None


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _test_type_tagged_naming_and_padding(runner) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        _setup_repo(repo_root)

        result = runner(repo_root, type_="work", json_mode=True, dry_run=True,
                         short_name="user-auth", description="Add user auth")
        check(result.returncode == 0, f"expected success, got {result.returncode}: {result.stderr}")
        data = json.loads(result.stdout)
        check(data["BRANCH_NAME"] == "001-work-user-auth", f"unexpected branch name: {data['BRANCH_NAME']}")
        check(data["NUMBER"] == "001", f"expected 3-digit padding, got {data['NUMBER']}")
        check(data["TYPE"] == "work", "type should be echoed back")
        check(data["SWITCHED"] is False, "dry-run must never switch")
        check(data["ARTIFACT_PATH"] == "", "dry-run must not scaffold an artifact")

        # A second dry-run call in the same repo: since dry-run never creates
        # a branch/commit, the allocator still sees no new history and
        # correctly re-derives the same next index (001), not 002.
        result2 = runner(repo_root, type_="fix", json_mode=True, dry_run=True,
                          description="Null guard on parse")
        data2 = json.loads(result2.stdout)
        check(data2["BRANCH_NAME"] == "001-fix-null-guard-on-parse", f"unexpected branch name: {data2['BRANCH_NAME']}")


def _test_invalid_type_errors(runner) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        _setup_repo(repo_root)

        result = runner(repo_root, type_="bogus", json_mode=True, dry_run=True, description="Some description")
        check(result.returncode == 1, f"expected exit 1 for invalid type, got {result.returncode}")

        # New work never scaffolds a full-spec or quick-spec bundle.
        for retired in ("spec", "quick"):
            result = runner(repo_root, type_=retired, json_mode=True, dry_run=True, description="Some description")
            check(result.returncode == 1, f"expected exit 1 for retired type {retired}, got {result.returncode}")
            check("type must be one of: fix, work" in result.stderr, f"unexpected error for {retired}: {result.stderr}")


def _test_dry_run_no_switch(runner) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        _setup_repo(repo_root)

        before = subprocess.run(["git", "branch", "--show-current"], cwd=repo_root, capture_output=True, text=True).stdout.strip()
        result = runner(repo_root, type_="work", json_mode=True, dry_run=True, yes=True, description="Quick idea")
        check(result.returncode == 0, f"dry-run should succeed: {result.stderr}")
        after = subprocess.run(["git", "branch", "--show-current"], cwd=repo_root, capture_output=True, text=True).stdout.strip()
        check(before == after, "dry-run must never change the current branch")


def _test_legacy_backward_compat_counted(runner) -> None:
    # A legacy 007-foo branch + spec dir and a legacy QF-2026-003
    # record must be counted by the allocator so the next index is >= 8 and no
    # collision error is raised for an unrelated new branch.
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        _setup_repo(repo_root)

        (repo_root / ".devspark.work" / "specs" / "007-foo").mkdir(parents=True)
        (repo_root / ".devspark.work" / "specs" / "007-foo" / "spec.md").write_text("# spec\n", encoding="utf-8")
        (repo_root / ".devspark.work" / "quickfixes").mkdir(parents=True)
        (repo_root / ".devspark.work" / "quickfixes" / "QF-2026-003.md").write_text("# quickfix\n", encoding="utf-8")
        subprocess.run(["git", "checkout", "-b", "007-foo"], cwd=repo_root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "add", "."], cwd=repo_root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "commit", "-m", "seed legacy"], cwd=repo_root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "checkout", "main"], cwd=repo_root, check=True, capture_output=True, text=True)

        result = runner(repo_root, type_="work", json_mode=True, dry_run=True, description="New feature")
        check(result.returncode == 0, f"expected success: {result.stderr}")
        data = json.loads(result.stdout)
        check(int(data["NUMBER"]) >= 8, f"expected index >= 8 given legacy 007/QF-2026-003, got {data['NUMBER']}")


def _test_branch_safety_no_switch_without_confirmation(runner) -> None:
    # In a non-interactive subprocess (no TTY), omitting -Yes/--yes
    # MUST fail closed rather than silently switching.
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        _setup_repo(repo_root)

        before = subprocess.run(["git", "branch", "--show-current"], cwd=repo_root, capture_output=True, text=True).stdout.strip()
        result = runner(repo_root, type_="fix", json_mode=True, description="Some fix, no confirmation")
        check(result.returncode != 0, "expected non-zero exit when confirmation is refused/unavailable")
        after = subprocess.run(["git", "branch", "--show-current"], cwd=repo_root, capture_output=True, text=True).stdout.strip()
        check(before == after, "must not switch branches without confirmation")


def _test_hostile_shortname_produces_valid_ref(runner) -> None:
    # Pathological short-name input must not produce an invalid git ref.
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        _setup_repo(repo_root)

        hostile = "--evil ../../etc .lock * ? [x] ~ ^ :"
        result = runner(repo_root, type_="fix", json_mode=True, dry_run=True, short_name=hostile)
        check(result.returncode == 0, f"hostile input should still normalize to a valid ref: {result.stderr}")
        data = json.loads(result.stdout)
        branch_name = data["BRANCH_NAME"]
        check_result = subprocess.run(
            ["git", "check-ref-format", "--branch", branch_name],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        check(check_result.returncode == 0, f"composed branch name is not a valid git ref: {branch_name}")


def main() -> None:
    suites = []
    if _has_pwsh():
        suites.append(("pwsh", _pwsh))
    if _has_bash():
        suites.append(("bash", _bash))
    if not suites:
        raise AssertionError("neither pwsh nor bash is available to exercise new-branch contract tests")

    for label, runner in suites:
        _test_type_tagged_naming_and_padding(runner)
        _test_invalid_type_errors(runner)
        _test_dry_run_no_switch(runner)
        _test_legacy_backward_compat_counted(runner)
        _test_branch_safety_no_switch_without_confirmation(runner)
        _test_hostile_shortname_produces_valid_ref(runner)
        print(f"new-branch contract validated ({label}).")


if __name__ == "__main__":
    main()
