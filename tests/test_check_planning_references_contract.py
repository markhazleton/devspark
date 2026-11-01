# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for the deterministic planning-reference backstop
(scripts/{powershell,bash}/check-planning-references.*).

Covers command-preamble-contract.md §0's one-way traceability rule: durable code/tests/.knowledge/
must never reference the branch name or a generic planning identifier (FR-###, T###, QF-####-###)
outside the roots that legitimately document the convention itself. Legacy code_ref/knowledge_ref
markers in planning records are ignored.

Every check subprocess-runs both the PowerShell and Bash scripts against the same fixture
so the two stay provably in agreement, per constitution §VI.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PS1 = ROOT / "scripts" / "powershell" / "check-planning-references.ps1"
SH = ROOT / "scripts" / "bash" / "check-planning-references.sh"

_PWSH = shutil.which("pwsh") or shutil.which("powershell")
_GIT_BASH = r"C:\Program Files\Git\bin\bash.exe"
_BASH = _GIT_BASH if Path(_GIT_BASH).exists() else shutil.which("bash")

requires_pwsh = pytest.mark.skipif(_PWSH is None, reason="pwsh/powershell not available")
requires_bash = pytest.mark.skipif(_BASH is None, reason="bash not available")


def _init_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, timeout=30)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, timeout=30)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True, timeout=30)
    return tmp_path


def _add(tmp_path: Path) -> None:
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, timeout=30)


def _run_pwsh(repo: Path, *extra_args: str) -> dict:
    result = subprocess.run(
        [_PWSH, "-File", str(PS1), "-RepoRoot", str(repo), "-Json", *extra_args],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode in (0, 1), result.stderr
    return json.loads(result.stdout)


def _run_bash(repo: Path, *extra_args: str) -> dict:
    result = subprocess.run(
        [_BASH, str(SH), "--repo-root", str(repo), "--json", *extra_args],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode in (0, 1), result.stderr
    return json.loads(result.stdout)


@requires_pwsh
@requires_bash
def test_durable_file_referencing_branch_name_is_flagged(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "widget.py").write_text(
        "# implements 042-spec-widget-thing\nprint('hi')\n", encoding="utf-8"
    )
    _add(tmp_path)

    ps_result = _run_pwsh(tmp_path, "-Branch", "042-spec-widget-thing")
    bash_result = _run_bash(tmp_path, "--branch", "042-spec-widget-thing")

    for result in (ps_result, bash_result):
        assert result["ok"] is False
        assert any(f["path"] == "scripts/widget.py" for f in result["branch_findings"])


@requires_pwsh
@requires_bash
def test_generic_id_in_durable_code_is_flagged(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "widget.py").write_text(
        "# FR-012 and T012 handled here\nprint('hi')\n", encoding="utf-8"
    )
    _add(tmp_path)

    ps_result = _run_pwsh(tmp_path)
    bash_result = _run_bash(tmp_path)

    for result in (ps_result, bash_result):
        assert result["ok"] is False
        assert {f["match"] for f in result["id_findings"]} == {"FR-012", "T012"}


@requires_pwsh
@requires_bash
def test_checker_scripts_do_not_flag_their_own_documentation(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    for source, relative in (
        (PS1, Path("scripts") / "powershell" / PS1.name),
        (SH, Path("scripts") / "bash" / SH.name),
    ):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    _add(tmp_path)

    ps_result = _run_pwsh(tmp_path)
    bash_result = _run_bash(tmp_path)

    for result in (ps_result, bash_result):
        assert result["ok"] is True
        assert result["id_findings"] == []


@requires_pwsh
@requires_bash
def test_generic_id_in_templates_is_not_flagged_by_default(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "tasks-template.md").write_text(
        "- [ ] T012 example task (Implements: FR-001)\n", encoding="utf-8"
    )
    _add(tmp_path)

    ps_result = _run_pwsh(tmp_path)
    bash_result = _run_bash(tmp_path)

    for result in (ps_result, bash_result):
        assert result["ok"] is True
        assert result["id_findings"] == []


@requires_pwsh
@requires_bash
def test_generic_id_in_tests_excluded_by_default_included_with_flag(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_widget.py").write_text(
        "# asserts FR-007 behavior\ndef test_x(): pass\n", encoding="utf-8"
    )
    _add(tmp_path)

    ps_default = _run_pwsh(tmp_path)
    bash_default = _run_bash(tmp_path)
    for result in (ps_default, bash_default):
        assert result["ok"] is True

    ps_strict = _run_pwsh(tmp_path, "-IncludeTests")
    bash_strict = _run_bash(tmp_path, "--include-tests")
    for result in (ps_strict, bash_strict):
        assert result["ok"] is False
        assert any(f["match"] == "FR-007" for f in result["id_findings"])


@requires_pwsh
@requires_bash
def test_legacy_pending_linkage_is_not_flagged(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    feature_dir = tmp_path / ".devspark.work" / "specs" / "001-widget"
    feature_dir.mkdir(parents=True)
    (feature_dir / "tasks.md").write_text(
        "- [X] T001 Done (code_ref: pending | knowledge_ref: pending)\n", encoding="utf-8"
    )
    quickfix_dir = tmp_path / ".devspark.work" / "quickfixes"
    quickfix_dir.mkdir(parents=True)
    (quickfix_dir / "001-fix-thing.md").write_text(
        "- [X] Fix applied (code_ref: pending | knowledge_ref: n/a)\n", encoding="utf-8"
    )
    _add(tmp_path)

    ps_result = _run_pwsh(tmp_path)
    bash_result = _run_bash(tmp_path)

    assert bash_result == ps_result
    for result in (ps_result, bash_result):
        assert result["ok"] is True
        assert "linkage_findings" not in result


@requires_pwsh
@requires_bash
def test_clean_repo_reports_ok(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "widget.py").write_text("print('hi')\n", encoding="utf-8")
    feature_dir = tmp_path / ".devspark.work" / "specs" / "001-widget"
    feature_dir.mkdir(parents=True)
    (feature_dir / "tasks.md").write_text(
        "- [X] T001 Done (code_ref: scripts/widget.py | knowledge_ref: n/a -- no doc needed)\n",
        encoding="utf-8",
    )
    _add(tmp_path)

    ps_result = _run_pwsh(tmp_path)
    bash_result = _run_bash(tmp_path)

    for result in (ps_result, bash_result):
        assert result["ok"] is True
        assert result["branch_findings"] == []
        assert result["id_findings"] == []


@pytest.mark.skipif(
    sys.platform != "win32", reason="pwsh/bash availability assumed on the dev workstation"
)
def test_exit_code_matches_ok_field() -> None:
    """Smoke-test the exit code contract against the real repo, without asserting on content
    (this repo's own findings are expected to change over time)."""
    if _PWSH:
        result = subprocess.run(
            [_PWSH, "-File", str(PS1), "-RepoRoot", str(ROOT), "-Json"],
            capture_output=True, text=True, timeout=60,
        )
        payload = json.loads(result.stdout)
        assert result.returncode == (0 if payload["ok"] else 1)
