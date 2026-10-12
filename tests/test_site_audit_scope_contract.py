# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Every scope the site-audit command advertises must be accepted by both pre-scan scripts.

The documented scope table is the source of truth; a scope that appears there but is rejected by
a script is an advertised capability that cannot run. The scans run against a small fixture
repository so scope acceptance is verified without walking the whole workspace.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
COMMAND_DOC = ROOT / "templates" / "commands" / "site-audit.md"
POWERSHELL = ROOT / "scripts" / "powershell" / "site-audit.ps1"
BASH = ROOT / "scripts" / "bash" / "site-audit.sh"

DOCUMENTED_SCOPES = sorted(set(re.findall(r"`--scope=([a-z]+)`", COMMAND_DOC.read_text(encoding="utf-8"))))


def _wsl_path(path: Path) -> str:
    """The bash on PATH may be WSL, which cannot read a drive-letter path."""
    value = path.as_posix()
    if len(value) > 1 and value[1] == ":":
        return f"/mnt/{value[0].lower()}{value[2:]}"
    return value


@pytest.fixture(scope="module")
def sample_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    repo = tmp_path_factory.mktemp("site-audit-repo")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    knowledge = repo / ".knowledge" / "architecture"
    knowledge.mkdir(parents=True)
    (knowledge / "app.md").write_text(
        "---\nid: app\ntype: architecture\ntitle: App\n---\n\n# App\n\nCurrent behavior.\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init"], cwd=repo, capture_output=True, text=True, timeout=60, check=True)
    return repo


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=180)


def test_documented_scopes_are_discovered() -> None:
    assert {"full", "comments", "evidence", "knowledge"}.issubset(set(DOCUMENTED_SCOPES))


@pytest.mark.parametrize("scope", DOCUMENTED_SCOPES)
def test_powershell_accepts_every_documented_scope(scope: str, sample_repo: Path) -> None:
    if not shutil.which("pwsh"):
        pytest.skip("pwsh is not available")
    result = _run(
        ["pwsh", "-NoProfile", "-File", str(POWERSHELL), "-Scope", scope, "-OutputFormat", "summary"],
        sample_repo,
    )
    assert result.returncode == 0, f"scope '{scope}' rejected: {result.stderr}"


@pytest.mark.parametrize("scope", DOCUMENTED_SCOPES)
def test_bash_accepts_every_documented_scope(scope: str, sample_repo: Path) -> None:
    if not shutil.which("bash"):
        pytest.skip("bash is not available")
    result = _run(["bash", _wsl_path(BASH), f"--scope={scope}", "--summary"], sample_repo)
    assert result.returncode == 0, f"scope '{scope}' rejected: {result.stderr}"


def test_powershell_rejects_an_unknown_scope(sample_repo: Path) -> None:
    if not shutil.which("pwsh"):
        pytest.skip("pwsh is not available")
    result = _run(["pwsh", "-NoProfile", "-File", str(POWERSHELL), "-Scope", "not-a-scope"], sample_repo)
    assert result.returncode != 0


def test_bash_rejects_an_unknown_scope(sample_repo: Path) -> None:
    if not shutil.which("bash"):
        pytest.skip("bash is not available")
    result = _run(["bash", _wsl_path(BASH), "--scope=not-a-scope"], sample_repo)
    assert result.returncode != 0


def test_knowledge_scope_reports_index_currency(sample_repo: Path) -> None:
    if not shutil.which("pwsh"):
        pytest.skip("pwsh is not available")
    result = _run(["pwsh", "-NoProfile", "-File", str(POWERSHELL), "-Scope", "knowledge"], sample_repo)
    assert result.returncode == 0, result.stderr
    knowledge = json.loads(result.stdout)["knowledge"]
    assert knowledge["present"] is True
    assert "index_present" in knowledge
    assert "index_current" in knowledge
    assert "dangling_references" in knowledge
    assert knowledge["counts"]["documents"] == 1


def test_both_twins_report_the_same_knowledge_fields(sample_repo: Path) -> None:
    if not (shutil.which("pwsh") and shutil.which("bash")):
        pytest.skip("both pwsh and bash are required")
    ps_result = _run(
        ["pwsh", "-NoProfile", "-File", str(POWERSHELL), "-Scope", "knowledge"], sample_repo
    )
    bash_result = _run(["bash", _wsl_path(BASH), "--scope=knowledge"], sample_repo)
    assert ps_result.returncode == 0, ps_result.stderr
    assert bash_result.returncode == 0, bash_result.stderr
    ps_knowledge = json.loads(ps_result.stdout)["knowledge"]
    bash_knowledge = json.loads(bash_result.stdout)["knowledge"]
    assert set(ps_knowledge) == set(bash_knowledge)
