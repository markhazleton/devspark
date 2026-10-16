# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for `/devspark.merge-from-main`: wiring plus the script's merge lifecycle in both shells."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
GIT_BASH = Path(r"C:\Program Files\Git\bin\bash.exe")
PWSH = shutil.which("pwsh")
PS1 = ROOT / "scripts" / "powershell" / "merge-from-main.ps1"
SH = ROOT / "scripts" / "bash" / "merge-from-main.sh"


def _bash() -> str | None:
    if GIT_BASH.exists():
        return str(GIT_BASH)
    return shutil.which("bash")


SHELLS = [
    pytest.param("pwsh", marks=pytest.mark.skipif(PWSH is None, reason="pwsh not available")),
    pytest.param("bash", marks=pytest.mark.skipif(_bash() is None, reason="bash not available")),
]


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, timeout=60
    ).stdout.strip()


def _run(shell: str, repo: Path, *flags: str) -> tuple[int, dict]:
    if shell == "pwsh":
        mapping = {"--continue": "-Continue", "--abort": "-Abort", "--push": "-Push"}
        cmd = [PWSH, "-NoProfile", "-File", str(PS1), *[mapping[f] for f in flags], "-Json"]
    else:
        cmd = [_bash(), SH.as_posix(), *flags, "--json"]
    proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, timeout=120)
    return proc.returncode, json.loads(proc.stdout.strip().splitlines()[-1])


def _commit(repo: Path, name: str, content: str, message: str) -> None:
    (repo / name).write_text(content, encoding="utf-8")
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", message)


_TEMPLATE_CLONE: Path | None = None
_TEMP_ROOT: tempfile.TemporaryDirectory | None = None


def _init_template_clone(target: Path) -> None:
    origin = target / "origin.git"
    seed = target / "seed"
    work = target / "work"
    _git(target, "init", "-q", "--bare", "-b", "main", str(origin))
    _git(target, "clone", "-q", str(origin), str(seed))
    _git(seed, "config", "user.email", "test@example.com")
    _git(seed, "config", "user.name", "Test User")
    _commit(seed, "a.txt", "one\ntwo\nthree\n", "base")
    _git(seed, "push", "-q", "origin", "HEAD:main")
    _git(target, "clone", "-q", str(origin), str(work))
    _git(work, "config", "user.email", "test@example.com")
    _git(work, "config", "user.name", "Test User")
    _git(work, "checkout", "-q", "-b", "feature")


@pytest.fixture
def clone(tmp_path: Path) -> tuple[Path, Path]:
    global _TEMPLATE_CLONE, _TEMP_ROOT
    if _TEMPLATE_CLONE is None:
        _TEMP_ROOT = tempfile.TemporaryDirectory()
        _TEMPLATE_CLONE = Path(_TEMP_ROOT.name) / "tpl"
        _TEMPLATE_CLONE.mkdir()
        _init_template_clone(_TEMPLATE_CLONE)
    shutil.copytree(_TEMPLATE_CLONE / "origin.git", tmp_path / "origin.git")
    shutil.copytree(_TEMPLATE_CLONE / "seed", tmp_path / "seed")
    shutil.copytree(_TEMPLATE_CLONE / "work", tmp_path / "work")
    _git(tmp_path / "seed", "remote", "set-url", "origin", str(tmp_path / "origin.git"))
    _git(tmp_path / "work", "remote", "set-url", "origin", str(tmp_path / "origin.git"))
    return tmp_path / "seed", tmp_path / "work"


def test_command_is_wired() -> None:
    command = (ROOT / "templates" / "commands" / "merge-from-main.md").read_text(encoding="utf-8")
    assert "sh: .devspark/scripts/bash/merge-from-main.sh $ARGUMENTS" in command
    assert "ps: .devspark/scripts/powershell/merge-from-main.ps1 $ARGUMENTS" in command
    skill = (ROOT / ".github" / "skills" / "devspark-merge-from-main" / "SKILL.md").read_text(encoding="utf-8")
    assert "templates/commands/merge-from-main.md" in skill
    assert (ROOT / "templates" / "consumer-skills" / "devspark-merge-from-main" / "SKILL.md").is_file()


@pytest.mark.parametrize("shell", SHELLS)
def test_up_to_date_then_clean_merge(shell: str, clone: tuple[Path, Path]) -> None:
    seed, work = clone
    code, out = _run(shell, work)
    assert (code, out["status"]) == (0, "up-to-date")

    _commit(seed, "b.txt", "new\n", "main adds b")
    _git(seed, "push", "-q", "origin", "HEAD:main")
    code, out = _run(shell, work)
    assert (code, out["status"], out["behind"], out["files"]) == (0, "merged", 1, 1)
    assert (work / "b.txt").is_file()


@pytest.mark.parametrize("shell", SHELLS)
def test_conflict_reports_hunks_blocks_on_markers_and_continues(shell: str, clone: tuple[Path, Path]) -> None:
    seed, work = clone
    _commit(seed, "a.txt", "one\nMAIN\nthree\n", "main edits")
    _git(seed, "push", "-q", "origin", "HEAD:main")
    _commit(work, "a.txt", "one\nFEATURE\nthree\n", "feature edits")

    code, out = _run(shell, work)
    assert (code, out["status"]) == (2, "conflicts")
    assert out["conflicts"] == [{"path": "a.txt", "state": "UU", "hunks": ["L2-6"]}]

    code, out = _run(shell, work, "--continue")
    assert (code, out["status"]) == (2, "blocked")
    assert out["markers"]

    (work / "a.txt").write_text("one\nMAIN FEATURE\nthree\n", encoding="utf-8")
    code, out = _run(shell, work, "--continue")
    assert (code, out["status"]) == (0, "resolved")
    assert _git(work, "rev-list", "--count", "--merges", "HEAD") == "1"
    assert _git(work, "status", "--porcelain") == ""


@pytest.mark.parametrize("shell", SHELLS)
def test_abort_and_dirty_tree(shell: str, clone: tuple[Path, Path]) -> None:
    seed, work = clone
    _commit(seed, "a.txt", "MAIN\n", "main edits")
    _git(seed, "push", "-q", "origin", "HEAD:main")
    _commit(work, "a.txt", "FEATURE\n", "feature edits")
    assert _run(shell, work)[1]["status"] == "conflicts"
    code, out = _run(shell, work, "--abort")
    assert (code, out["status"]) == (0, "aborted")

    (work / "a.txt").write_text("dirty\n", encoding="utf-8")
    code, out = _run(shell, work)
    assert (code, out["status"]) == (2, "blocked")
    assert out["dirty"]
