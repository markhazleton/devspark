# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""7.5.1: one canonical `.knowledge` index engine.

`resolve_knowledge_engine` (bash) / `Resolve-KnowledgeEngine` (PowerShell) are the single
resolution mechanism shared by site-audit, create-pr, get-pr-context, and release-context. Every
entry point must agree: prefer the framework-managed `.devspark/scripts/build_knowledge_index.py`,
fall back to a legacy repo-root copy only when the framework-managed copy is absent (this
framework's own source repo, which does not materialize `.devspark/scripts/`), and resolve to
nothing when neither exists.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from tests.bash_twin import BASH_EXE, to_bash_path

ROOT = Path(__file__).resolve().parent.parent
HAS_PWSH = shutil.which("pwsh") is not None
HAS_BASH = BASH_EXE is not None


def _wsl_path(path: Path) -> str:
    return to_bash_path(path)


def _write(path: Path, content: str = "# stub\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _resolve_bash(repo_root: Path) -> str:
    script = (
        f"source {_wsl_path(ROOT / 'scripts/bash/common.sh')} >/dev/null 2>&1; "
        f"resolve_knowledge_engine '{_wsl_path(repo_root)}'"
    )
    result = subprocess.run(
        [BASH_EXE, "-c", script], text=True, capture_output=True, timeout=30
    )
    return result.stdout.strip()


def _resolve_pwsh(repo_root: Path) -> str:
    script = (
        f". '{ROOT / 'scripts/powershell/common.ps1'}'; "
        f"$r = Resolve-KnowledgeEngine -RepoRoot '{repo_root}'; "
        "if ($r) { Write-Output $r }"
    )
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-Command", script],
        text=True,
        capture_output=True,
        timeout=30,
    )
    return result.stdout.strip()


@pytest.mark.skipif(not HAS_BASH, reason="Bash required")
def test_bash_prefers_devspark_managed_engine_over_legacy_root_copy(tmp_path: Path) -> None:
    _write(tmp_path / "scripts" / "build_knowledge_index.py")
    devspark_copy = tmp_path / ".devspark" / "scripts" / "build_knowledge_index.py"
    _write(devspark_copy)
    assert _resolve_bash(tmp_path) == _wsl_path(devspark_copy)


@pytest.mark.skipif(not HAS_BASH, reason="Bash required")
def test_bash_falls_back_to_legacy_root_copy_when_devspark_copy_absent(tmp_path: Path) -> None:
    root_copy = tmp_path / "scripts" / "build_knowledge_index.py"
    _write(root_copy)
    assert _resolve_bash(tmp_path) == _wsl_path(root_copy)


@pytest.mark.skipif(not HAS_BASH, reason="Bash required")
def test_bash_resolves_to_nothing_when_neither_copy_exists(tmp_path: Path) -> None:
    assert _resolve_bash(tmp_path) == ""


@pytest.mark.skipif(not HAS_PWSH, reason="PowerShell required")
def test_pwsh_prefers_devspark_managed_engine_over_legacy_root_copy(tmp_path: Path) -> None:
    _write(tmp_path / "scripts" / "build_knowledge_index.py")
    devspark_copy = tmp_path / ".devspark" / "scripts" / "build_knowledge_index.py"
    _write(devspark_copy)
    assert _resolve_pwsh(tmp_path) == str(devspark_copy)


@pytest.mark.skipif(not HAS_PWSH, reason="PowerShell required")
def test_pwsh_falls_back_to_legacy_root_copy_when_devspark_copy_absent(tmp_path: Path) -> None:
    root_copy = tmp_path / "scripts" / "build_knowledge_index.py"
    _write(root_copy)
    assert _resolve_pwsh(tmp_path) == str(root_copy)


@pytest.mark.skipif(not HAS_PWSH, reason="PowerShell required")
def test_pwsh_resolves_to_nothing_when_neither_copy_exists(tmp_path: Path) -> None:
    assert _resolve_pwsh(tmp_path) == ""
