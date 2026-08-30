"""Validation for create-pr preflight lifecycle context.

Run with: python tests/test_create_pr_preflight.py
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
        Path("scripts/bash/platform.sh"),
        Path("scripts/bash/create-pr.sh"),
        Path("scripts/powershell/common.ps1"),
        Path("scripts/powershell/platform.ps1"),
        Path("scripts/powershell/create-pr.ps1"),
    ):
        target = destination / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel_path, target)


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=True)


def _init_git_repo(repo_root: Path, branch_name: str) -> None:
    _run(["git", "init"], repo_root)
    _run(["git", "config", "user.name", "DevSpark Test"], repo_root)
    _run(["git", "config", "user.email", "devspark@example.com"], repo_root)
    _run(["git", "checkout", "-b", branch_name], repo_root)
    _run(["git", "add", "."], repo_root)
    _run(["git", "commit", "-m", "initial commit"], repo_root)
    remote_root = repo_root.parent / f"{repo_root.name}-origin.git"
    subprocess.run(["git", "init", "--bare", remote_root.as_posix()], cwd=repo_root, text=True, capture_output=True, check=True)
    _run(["git", "remote", "add", "origin", remote_root.as_posix()], repo_root)
    _run(["git", "push", "-u", "origin", branch_name], repo_root)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_spec_repo(repo_root: Path) -> None:
    feature_dir = repo_root / ".documentation" / "specs" / "001-feature-sample"
    _write(
        feature_dir / "spec.md",
        """---
classification: quick-spec
risk_level: medium
target_workflow: specify-light
required_artifacts: intent, action-plan
recommended_next_step: plan
required_gates: checklist, analyze, critic
---

# Quick Specification: Sample Flow
""",
    )
    _write(
        feature_dir / "tasks.md",
        """# Tasks: Sample Flow

- [x] T001 Finish preparation
- [ ] T002 Complete remaining work

## Gate Acknowledgements

- Gate: analyze
- Concern: Coverage for rollback path remains partial
- Decision: proceed with explicit review note
""",
    )
    _write(
        feature_dir / "gates" / "analyze.md",
        """gate: analyze
status: warn
blocking: false
severity: warning
summary: Coverage drift remains in rollback requirements.

## Specification Analysis Report
""",
    )
    _write(
        feature_dir / "gates" / "critic.md",
        """gate: critic
status: fail
blocking: true
severity: showstopper
summary: Migration rollback plan is underspecified.

## Technical Risk Assessment
""",
    )
    _write(
        feature_dir / "checklists" / "quality.md",
        """# Checklist

- [x] CHK001 Requirements are specific
- [ ] CHK002 Rollback path is described
""",
    )
    (repo_root / ".github").mkdir(parents=True, exist_ok=True)
    _write(repo_root / "README.md", "sample repo\n")


def _build_quickfix_repo(repo_root: Path) -> None:
    _write(
        repo_root / ".documentation" / "quickfixes" / "QF-001.md",
        """---
classification: one-off-fix
risk_level: medium
target_workflow: quickfix
required_artifacts: quickfix-record
recommended_next_step: implement
required_gates: checklist
---

# Quickfix Record: QF-001

## Metadata

- **ID**: QF-001
- **Branch**: 007-fix-bug

## Problem Statement

Fix the broken fallback handler.

## Gate Acknowledgements

- Gate: checklist
- Concern: Error-path wording still needs cleanup
- Decision: proceed and capture in PR notes
""",
    )
    (repo_root / ".github").mkdir(parents=True, exist_ok=True)
    _write(repo_root / "README.md", "quickfix repo\n")


def _run_powershell_preflight(repo_root: Path) -> dict:
    result = _run(
        [
            "pwsh",
            "-NoLogo",
            "-NoProfile",
            "-File",
            "scripts/powershell/create-pr.ps1",
            "-Mode",
            "Preflight",
            "-Json",
        ],
        repo_root,
    )
    return json.loads(result.stdout)


def _run_bash_preflight(repo_root: Path) -> dict | None:
    if not shutil.which("bash") or not shutil.which("jq"):
        return None
    result = _run(["bash", "scripts/bash/create-pr.sh", "--mode", "preflight", "--json"], repo_root)
    return json.loads(result.stdout)


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        spec_repo = Path(temp_dir) / "spec-repo"
        spec_repo.mkdir()
        _copy_script_set(spec_repo)
        _build_spec_repo(spec_repo)
        _init_git_repo(spec_repo, "001-feature-sample")

        ps_preflight = _run_powershell_preflight(spec_repo)
        print(json.dumps(ps_preflight, indent=2))
        assert ps_preflight["feature"]["classification"] == "quick-spec"
        assert ps_preflight["prerequisites"]["clean_worktree"] is True
        assert ps_preflight["prerequisites"]["branch_pushed_to_remote"] is True
        assert ps_preflight["feature"]["tasks_total"] == 2
        assert len(ps_preflight["feature"]["gate_artifacts"]) == 2
        assert any(item["gate"] == "critic" and item["blocking"] for item in ps_preflight["feature"]["gate_artifacts"])
        assert ps_preflight["feature"]["gate_acknowledgements"]

        bash_preflight = _run_bash_preflight(spec_repo)
        if bash_preflight is not None:
            assert bash_preflight["feature"]["classification"] == "quick-spec"
            assert bash_preflight["feature"]["tasks_total"] == 2
            assert bash_preflight["feature"]["gate_acknowledgements"]

        quickfix_repo = Path(temp_dir) / "quickfix-repo"
        quickfix_repo.mkdir()
        _copy_script_set(quickfix_repo)
        _build_quickfix_repo(quickfix_repo)
        _init_git_repo(quickfix_repo, "007-fix-bug")

        quickfix_preflight = _run_powershell_preflight(quickfix_repo)
        assert quickfix_preflight["feature"]["classification"] == "one-off-fix"
        assert quickfix_preflight["quickfix_record"]["id"] == "QF-001"
        assert quickfix_preflight["feature"]["gate_acknowledgements"]

    print("create-pr preflight lifecycle validated.")


if __name__ == "__main__":
    main()
