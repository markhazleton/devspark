# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Create PR proves the committed Knowledge builds, and nothing mechanical beyond that.

Derived index files and `last_verified` dates are not compared or required: a stale date or an
out-of-date generated file never blocks a PR. These tests build real temporary Git repositories
and drive both the PowerShell and Bash Create PR scripts against them.
"""

from __future__ import annotations

import atexit
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.xdist_group("readiness_template")

ROOT = Path(__file__).resolve().parent.parent
PWSH = shutil.which("pwsh")
BASH_CANDIDATES = [r"C:\Program Files\Git\bin\bash.exe", shutil.which("bash")]
TIMEOUT = 180

BASE_DATE = "2026-10-01T09:00:00+00:00"
WORK_DATE = "2026-10-05T09:00:00+00:00"
BRANCH = "001-readiness"

ARCH_PATH = ".knowledge/entities/widget/architecture.md"
INDEX_PATH = ".knowledge/index.json"


def _find_bash() -> str | None:
    for candidate in BASH_CANDIDATES:
        if not candidate or not Path(candidate).exists() and not shutil.which(candidate):
            continue
        probe = subprocess.run(
            [candidate, "-c", "command -v jq >/dev/null && command -v git >/dev/null"],
            capture_output=True,
            timeout=60,
            check=False,
        )
        if probe.returncode == 0:
            return candidate
    return None


BASH = _find_bash()
SHELLS = [
    pytest.param("ps", marks=pytest.mark.skipif(not PWSH, reason="pwsh required")),
    pytest.param("bash", marks=pytest.mark.skipif(not BASH, reason="bash with jq required")),
]


def _env(path_override: str | None = None) -> dict[str, str]:
    env = dict(os.environ)
    python_dir = str(Path(sys.executable).parent)
    env["PATH"] = path_override if path_override is not None else os.pathsep.join([python_dir, env.get("PATH", "")])
    env["DEVSPARK_PLATFORM"] = "gitlab"  # unsupported for creation, so a leaked run can never reach a real platform
    for key in ("DEVSPARK_FEATURE", "GIT_COMMITTER_DATE", "GIT_AUTHOR_DATE"):
        env.pop(key, None)
    return env


def git(repo: Path, *args: str, date: str | None = None) -> str:
    env = _env()
    if date:
        env["GIT_COMMITTER_DATE"] = date
        env["GIT_AUTHOR_DATE"] = date
    done = subprocess.run(
        ["git", *args], cwd=repo, env=env, capture_output=True, text=True, timeout=TIMEOUT, check=False
    )
    assert done.returncode == 0, f"git {args} failed: {done.stderr}"
    return done.stdout.strip()


def engine(repo: Path, *flags: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(repo / "scripts/build_knowledge_index.py"), "--repo-root", str(repo), *flags],
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        check=False,
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def layer_doc(last_verified: str, source: str = "src/widget.py", extra: str = "") -> str:
    return (
        "---\ntype: entity-layer\nlayer: architecture\ntitle: Widget Architecture\n"
        f"last_verified: {last_verified}\nsource_of_truth:\n  - {source}\n---\n\n"
        f"# Widget Architecture\n\nCurrent behavior.\n{extra}"
    )


_TEMPLATES: dict[tuple[str, bool], Path] = {}


def build_repo(tmp_path: Path, *, engine_mode: str = "real", with_knowledge: bool = True) -> Path:
    """A pushed `main` plus a pushed feature branch with no feature commits yet.

    Each distinct shape is built once and copied per test; the copy gets its own origin.
    """
    key = (engine_mode, with_knowledge)
    if key not in _TEMPLATES:
        template = Path(tempfile.mkdtemp(prefix="readiness-template-"))
        atexit.register(shutil.rmtree, template, ignore_errors=True)
        _build_repo_at(template, engine_mode=engine_mode, with_knowledge=with_knowledge)
        _TEMPLATES[key] = template
    template = _TEMPLATES[key]
    shutil.copytree(template / "origin.git", tmp_path / "origin.git")
    shutil.copytree(template / "repo", tmp_path / "repo")
    repo = tmp_path / "repo"
    git(repo, "remote", "set-url", "origin", str(tmp_path / "origin.git"))
    return repo


def _build_repo_at(tmp_path: Path, *, engine_mode: str, with_knowledge: bool) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True, timeout=TIMEOUT)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.name", "Readiness Test")
    git(repo, "config", "user.email", "readiness@example.com")
    for rel in (
        "scripts/bash/common.sh",
        "scripts/bash/platform.sh",
        "scripts/bash/create-pr.sh",
        "scripts/powershell/common.ps1",
        "scripts/powershell/platform.ps1",
        "scripts/powershell/create-pr.ps1",
        "scripts/judge.py",
    ):
        _write(repo / rel, (ROOT / rel).read_text(encoding="utf-8"))
    engines = {
        "real": (ROOT / "scripts/build_knowledge_index.py").read_text(encoding="utf-8"),
        "exit2": "import sys\nsys.exit(2)\n",
    }
    if engine_mode in engines:
        _write(repo / "scripts/build_knowledge_index.py", engines[engine_mode])
    _write(repo / ".gitignore", "__pycache__/\n")
    _write(repo / "README.md", "readiness fixture\n")
    _write(repo / f".devspark.work/specs/{BRANCH}/spec.md", "---\nclassification: quick-spec\n---\n\n# Quick Spec: Readiness\n")
    if with_knowledge:
        base = repo / ".knowledge/entities/widget"
        _write(base / "_entity.yaml", "id: widget\ntype: subsystem\nowner: team-x\n")
        _write(base / "architecture.md", layer_doc("2026-10-01"))
        _write(repo / "src/widget.py", "value = 1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "baseline", date=BASE_DATE)
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "push", "-q", "-u", "origin", "main")
    git(repo, "checkout", "-q", "-b", BRANCH)
    git(repo, "push", "-q", "-u", "origin", BRANCH)
    return repo


def commit_and_push(repo: Path, message: str, date: str = WORK_DATE) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message, date=date)
    git(repo, "push", "-q", "origin", BRANCH)


def break_the_build(repo: Path) -> None:
    _write(repo / ARCH_PATH, layer_doc("2026-10-01", source="src/missing.py"))
    commit_and_push(repo, "cite a file that does not exist")


def _invoke(repo: Path, shell: str, mode: str, env: dict[str, str] | None = None) -> tuple[dict, int]:
    env = env or _env()
    if shell == "ps":
        cmd = [PWSH, "-NoLogo", "-NoProfile", "-File", "scripts/powershell/create-pr.ps1", "-Mode", mode, "-Json"]
        if mode != "Preflight":
            cmd += ["-Title", "t", "-Body", "b"]
    else:
        cmd = [BASH, "scripts/bash/create-pr.sh", "--mode", mode.lower(), "--json"]
        if mode != "Preflight":
            cmd += ["--title", "t", "--body", "b"]
    done = subprocess.run(
        cmd, cwd=repo, env=env, capture_output=True, encoding="utf-8", timeout=TIMEOUT, check=False
    )
    try:
        return json.loads(done.stdout), done.returncode
    except json.JSONDecodeError as exc:  # pragma: no cover - failure detail
        raise AssertionError(f"{shell} {mode} produced no JSON.\nstdout={done.stdout}\nstderr={done.stderr}") from exc


def _run_shell(repo: Path, shell: str, mode: str, env: dict[str, str] | None = None) -> dict:
    return _invoke(repo, shell, mode, env)[0]


def knowledge(repo: Path, shell: str) -> dict:
    return _run_shell(repo, shell, "Preflight")["knowledge"]


@pytest.mark.parametrize("shell", SHELLS)
def test_buildable_knowledge_is_ready(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    with (repo / "src/widget.py").open("a", encoding="utf-8") as handle:
        handle.write("value += 1\n")
    commit_and_push(repo, "feature")

    result = knowledge(repo, shell)
    assert result["readiness"] == "ready"
    assert result["blockers"] == []
    assert result["checked_head"] == git(repo, "rev-parse", "HEAD")


@pytest.mark.parametrize("shell", SHELLS)
def test_stale_last_verified_and_a_missing_or_corrupt_index_do_not_block(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    # The cited source changes after `last_verified`, and a hand-edited index disagrees with a fresh build.
    with (repo / "src/widget.py").open("a", encoding="utf-8") as handle:
        handle.write("value += 1\n")
    _write(repo / INDEX_PATH, '{"nodes": []}\n')
    commit_and_push(repo, "code change and a stale, tracked index")

    assert knowledge(repo, shell)["readiness"] == "ready"


def test_engine_check_proves_the_build_and_never_writes(tmp_path: Path) -> None:
    repo = build_repo(tmp_path)
    _write(repo / INDEX_PATH, '{"nodes": []}\n')
    commit_and_push(repo, "drifted derived index")
    before = (repo / INDEX_PATH).read_bytes()

    assert engine(repo, "--check").returncode == 0
    assert (repo / INDEX_PATH).read_bytes() == before, "--check must never write"
    assert git(repo, "status", "--porcelain") == ""

    break_the_build(repo)
    assert engine(repo, "--check").returncode == 1


@pytest.mark.parametrize("shell", SHELLS)
def test_no_tracked_knowledge_is_not_applicable(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path, with_knowledge=False)
    result = knowledge(repo, shell)
    assert result["readiness"] == "not-applicable"
    assert result["blockers"] == []


@pytest.mark.parametrize("shell", SHELLS)
def test_missing_engine_is_unknown(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path, engine_mode="none")
    assert knowledge(repo, shell)["readiness"] == "unknown"


@pytest.mark.parametrize("shell", SHELLS)
def test_unsupported_engine_usage_is_unknown(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path, engine_mode="exit2")
    result = knowledge(repo, shell)
    assert result["readiness"] == "unknown"
    assert result["blockers"] == []


@pytest.mark.parametrize("shell", SHELLS)
def test_missing_interpreter_is_unknown_not_a_crash(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    tool_dirs = [str(Path(shutil.which(tool)).parent) for tool in ("git", "jq") if shutil.which(tool)]
    minimal = os.pathsep.join(tool_dirs)
    if shutil.which("python3", path=minimal) or shutil.which("python", path=minimal):
        pytest.skip("a Python interpreter shares a directory with git/jq on this machine")
    result = _run_shell(repo, shell, "Preflight", _env(minimal))["knowledge"]
    assert result["readiness"] == "unknown"
    assert result["blockers"] == []


@pytest.mark.parametrize("shell", SHELLS)
def test_a_build_failure_blocks_with_the_error(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    break_the_build(repo)
    result = knowledge(repo, shell)
    assert result["readiness"] == "blocked"
    assert [b["kind"] for b in result["blockers"]] == ["build-error"]
    assert "does not exist" in result["blockers"][0]["message"]


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("mode", ["Create", "Update"])
def test_create_and_update_modes_block_identically_and_change_nothing(
    tmp_path: Path, shell: str, mode: str
) -> None:
    repo = build_repo(tmp_path)
    break_the_build(repo)

    result = _run_shell(repo, shell, mode)
    assert result["error"] is True
    assert result["message"] == "CREATE PR BLOCKED — KNOWLEDGE CANNOT BE BUILT"
    assert "Committed HEAD: " + git(repo, "rev-parse", "HEAD") in result["details"]
    assert "does not exist" in result["details"]
    assert "Rerun /devspark-create-pr" in result["details"]
    assert [b["kind"] for b in result["blockers"]] == ["build-error"]
    assert git(repo, "status", "--porcelain") == "", "Create PR must not modify the working tree"
    assert git(repo, "rev-parse", "HEAD") == result["checked_head"], "Create PR must not commit"


@pytest.mark.skipif(not PWSH or not BASH, reason="both shells required")
@pytest.mark.parametrize("scenario", ["ready", "build-error", "not-applicable"])
def test_bash_and_powershell_agree(tmp_path: Path, scenario: str) -> None:
    repo = build_repo(tmp_path, with_knowledge=scenario != "not-applicable")
    if scenario == "build-error":
        break_the_build(repo)

    ps = knowledge(repo, "ps")
    sh = knowledge(repo, "bash")
    for field in ("readiness", "checked_head"):
        assert ps[field] == sh[field], field
    assert ps["blockers"] == sh["blockers"]
    assert set(ps) == set(sh) == {"gap_summary", "readiness", "blockers", "checked_head", "check_output"}
    for blocker in ps["blockers"]:
        assert set(blocker) == {"kind", "path", "message"}


@pytest.mark.skipif(not PWSH, reason="pwsh required")
def test_powershell_result_reports_checked_head_without_stray_statements() -> None:
    script = (
        "$e=$null; $a=[System.Management.Automation.Language.Parser]::ParseFile("
        "$env:CREATE_PR_SCRIPT,[ref]$null,[ref]$e);"
        "$stray=@($a.FindAll({param($n) $n -is [System.Management.Automation.Language.CommandAst] "
        "-and $n.GetCommandName() -eq 'checked_head'},$true)).Count;"
        "$keys=@($a.FindAll({param($n) $n -is [System.Management.Automation.Language.HashtableAst]},$true) "
        "| Where-Object { $_.Extent.Text -match 'status\\s*=\\s*.ok.' } "
        "| ForEach-Object { $_.KeyValuePairs | ForEach-Object { $_.Item1.Value } });"
        "@{stray=$stray;keys=$keys} | ConvertTo-Json -Compress"
    )
    proc = subprocess.run(
        [PWSH, "-NoProfile", "-Command", script],
        env={**os.environ, "CREATE_PR_SCRIPT": str(ROOT / "scripts/powershell/create-pr.ps1")},
        capture_output=True, text=True, timeout=TIMEOUT, check=False,
    )
    result = json.loads(proc.stdout)
    assert result["stray"] == 0
    assert "checked_head" in result["keys"]


WORK_BRANCH = "002-work-delivery"
OBLIGATION = "- [ ] Privacy review of the export — Authority: Privacy Office"


def start_work_branch(repo: Path, status: str = "Complete", obligations: str = "") -> None:
    """A pushed universal work branch whose optional work.md carries the given status and obligations."""
    git(repo, "checkout", "-q", "-b", WORK_BRANCH)
    note = f"# Work: Delivery\n\n**Status**: {status}\n"
    if obligations:
        note += f"\n## Required Obligations\n\n{obligations}\n"
    _write(repo / f".devspark.work/specs/{WORK_BRANCH}/work.md", note)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "work", date=WORK_DATE)
    git(repo, "push", "-q", "-u", "origin", WORK_BRANCH)


def lifecycle(repo: Path, shell: str) -> dict:
    return _run_shell(repo, shell, "Preflight")["lifecycle"]


@pytest.mark.parametrize("shell", SHELLS)
def test_preflight_reports_the_lifecycle_check_for_finished_work(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    start_work_branch(repo)
    assert lifecycle(repo, shell) == {"status": "pass", "failures": [], "pending_later_phase": []}


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("mode", ["Create", "Update"])
def test_an_unresolved_obligation_refuses_creation_and_names_its_authority(
    tmp_path: Path, shell: str, mode: str
) -> None:
    repo = build_repo(tmp_path)
    start_work_branch(repo, obligations=OBLIGATION)

    check = lifecycle(repo, shell)
    assert check["status"] == "fail"
    assert [f["code"] for f in check["failures"]] == ["required-obligation-unresolved"]

    result = _run_shell(repo, shell, mode)
    assert result["error"] is True
    assert result["message"] == "CREATE PR BLOCKED — REQUIRED OBLIGATION UNRESOLVED"
    assert "Committed HEAD: " + git(repo, "rev-parse", "HEAD") in result["details"]
    assert "authority: Privacy Office" in result["details"]
    assert "no flag or acknowledgement bypasses it" in result["details"]
    assert result["obligations"] == [
        {"obligation": "Privacy review of the export", "authority": "Privacy Office", "missing": "satisfying evidence"}
    ]
    assert git(repo, "status", "--porcelain") == "", "Create PR must not modify the working tree"


@pytest.mark.parametrize("shell", SHELLS)
def test_a_checked_obligation_without_an_evidence_reference_still_refuses(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    start_work_branch(repo, obligations=OBLIGATION.replace("[ ]", "[x]"))

    result = _run_shell(repo, shell, "Create")
    assert result["error"] is True
    assert result["message"] == "CREATE PR BLOCKED — REQUIRED OBLIGATION UNRESOLVED"
    assert "is checked without an evidence reference" in result["details"]
    assert "Evidence: " in result["details"]
    assert result["obligations"][0]["missing"] == "an evidence reference"


@pytest.mark.skipif(not PWSH, reason="pwsh required")
def test_an_in_process_preflight_reports_success_when_the_lifecycle_check_fails(tmp_path: Path) -> None:
    # Agent terminals call the script in-process and read $LASTEXITCODE, which a nested judge.py run must not leak into.
    repo = build_repo(tmp_path)
    start_work_branch(repo, obligations=OBLIGATION)
    script = "& ./scripts/powershell/create-pr.ps1 -Mode Preflight -Json | Out-Null; exit $LASTEXITCODE"
    done = subprocess.run(
        [PWSH, "-NoLogo", "-NoProfile", "-Command", script],
        cwd=repo, env=_env(), capture_output=True, encoding="utf-8", timeout=TIMEOUT, check=False,
    )
    assert done.returncode == 0, done.stderr
    assert lifecycle(repo, "ps")["status"] == "fail"


@pytest.mark.parametrize("shell", SHELLS)
def test_a_satisfied_obligation_no_longer_refuses(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    start_work_branch(repo, obligations=OBLIGATION.replace("[ ]", "[x]") + " — Evidence: PRIV-0000 approval")

    assert lifecycle(repo, shell)["status"] == "pass"
    result = _run_shell(repo, shell, "Create")
    # Creation then stops at the platform check, never at the obligation.
    assert "OBLIGATION" not in result.get("message", "")


@pytest.mark.parametrize("shell", SHELLS)
def test_other_lifecycle_failures_are_reported_but_left_to_the_prompt(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    start_work_branch(repo, status="In Progress")

    check = lifecycle(repo, shell)
    assert check["status"] == "fail"
    assert [f["code"] for f in check["failures"]] == ["work-incomplete"]
    assert "OBLIGATION" not in _run_shell(repo, shell, "Create").get("message", "")


@pytest.mark.parametrize("shell", SHELLS)
def test_legacy_spec_bundle_reports_lifecycle_without_refusing(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    check = lifecycle(repo, shell)
    assert check["status"] == "pass"
    assert "OBLIGATION" not in _run_shell(repo, shell, "Create").get("message", "")


@pytest.mark.parametrize("shell", SHELLS)
def test_a_branch_without_a_work_directory_is_not_applicable(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    git(repo, "checkout", "-q", "-b", "003-work-untracked")
    git(repo, "push", "-q", "-u", "origin", "003-work-untracked")
    assert lifecycle(repo, shell)["status"] == "not-applicable"


def _stub_dir(repo: Path, name: str, scripts: dict[str, tuple[str, str]]) -> Path:
    """Host command stubs, one POSIX script and one Windows .cmd per command, placed before the real PATH."""
    stubs = repo.parent / name
    stubs.mkdir(exist_ok=True)
    for command, (posix, windows) in scripts.items():
        (stubs / command).write_text("#!/bin/sh\n" + posix, encoding="utf-8", newline="\n")
        (stubs / command).chmod(0o755)
        (stubs / f"{command}.cmd").write_text("@echo off\r\n" + windows, encoding="utf-8", newline="")
    return stubs


def _env_with(stubs: Path, **extra: str) -> dict[str, str]:
    env = _env()
    env["PATH"] = os.pathsep.join([str(stubs), env["PATH"]])
    env.update(extra)
    return env


def break_the_lifecycle_check(repo: Path, cause: str) -> dict[str, str] | None:
    """Make judge.py unable to evaluate; returns the environment that reproduces the cause."""
    if cause == "judge-missing":
        (repo / "scripts/judge.py").unlink()
    elif cause == "invalid-output":
        _write(repo / "scripts/judge.py", "print('not a lifecycle result')\n")
    if cause != "python-unavailable":
        git(repo, "add", "-A")
        commit_and_push_branch(repo, WORK_BRANCH, f"lifecycle check: {cause}")
        return None
    failing = ("exit 1\n", "exit /b 1\r\n")
    return _env_with(_stub_dir(repo, "no-python", {"python3": failing, "python": failing}))


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("cause", ["judge-missing", "python-unavailable", "invalid-output"])
@pytest.mark.parametrize("mode", ["Create", "Update"])
def test_an_unevaluated_obligation_refuses_creation_and_says_why(
    tmp_path: Path, shell: str, cause: str, mode: str
) -> None:
    repo = build_repo(tmp_path)
    start_work_branch(repo, obligations=OBLIGATION)
    env = break_the_lifecycle_check(repo, cause)

    preflight = _run_shell(repo, shell, "Preflight", env)["lifecycle"]
    assert preflight == {
        "status": "unavailable", "reason": cause, "obligations_declared": True, "failures": [], "pending_later_phase": [],
    }

    result, code = _invoke(repo, shell, mode, env)
    assert code == 1
    assert result["error"] is True
    assert result["message"] == "CREATE PR BLOCKED — LIFECYCLE CHECK UNAVAILABLE"
    assert result["reason"] == cause
    assert "Committed HEAD: " + git(repo, "rev-parse", "HEAD") in result["details"]
    assert "not an obligation that passed" in result["details"]
    assert "Rerun /devspark-create-pr" in result["details"]
    assert "organizational policy authorizes a different approval path" in result["details"]
    assert git(repo, "status", "--porcelain") == "", "Create PR must not modify the working tree"


@pytest.mark.parametrize("shell", SHELLS)
def test_an_unavailable_check_without_declared_obligations_is_reported_not_refused(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    start_work_branch(repo)
    break_the_lifecycle_check(repo, "judge-missing")

    check = lifecycle(repo, shell)
    assert check["status"] == "unavailable" and check["obligations_declared"] is False
    # Creation then stops at the platform check, never at the lifecycle check.
    assert "LIFECYCLE" not in _run_shell(repo, shell, "Create").get("message", "")


def commit_and_push_branch(repo: Path, branch: str, message: str) -> None:
    git(repo, "commit", "-q", "-m", message, date=WORK_DATE)
    git(repo, "push", "-q", "origin", branch)


_PR_VIEW = '{"number":7,"url":"https://example.invalid/pr/7","title":"t","state":"OPEN","isDraft":false}'
_GH_POSIX = f"""case "$1 $2" in
  "auth status"|"pr edit") exit 0 ;;
  "repo view") echo main ;;
  "pr list") if [ -n "$GH_STUB_PR" ]; then echo '[{_PR_VIEW}]'; else echo '[]'; fi ;;
  "pr create") echo https://example.invalid/pr/7 ;;
  "pr view") echo '{_PR_VIEW}' ;;
  *) exit 1 ;;
esac
"""
_GH_WINDOWS = f"""if "%1 %2"=="auth status" exit /b 0
if "%1 %2"=="pr edit" exit /b 0
if "%1 %2"=="repo view" (echo main& exit /b 0)
if "%1 %2"=="pr create" (echo https://example.invalid/pr/7& exit /b 0)
if "%1 %2"=="pr view" goto view
if not "%1 %2"=="pr list" exit /b 1
if not defined GH_STUB_PR (echo []& exit /b 0)
echo [{_PR_VIEW}]
exit /b 0
:view
echo {_PR_VIEW}
exit /b 0
"""


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("mode", ["Create", "Update"])
def test_create_and_update_exit_codes_separate_success_from_refusal(tmp_path: Path, shell: str, mode: str) -> None:
    """Automation reads the exit code: 0 for a published PR, 1 for any refusal, never a parsed message."""
    repo = build_repo(tmp_path)
    start_work_branch(repo)
    gh = _env_with(
        _stub_dir(repo, "gh-stub", {"gh": (_GH_POSIX, _GH_WINDOWS)}),
        DEVSPARK_PLATFORM="github",
        **({"GH_STUB_PR": "1"} if mode == "Update" else {}),
    )

    preflight, code = _invoke(repo, shell, "Preflight", gh)
    assert code == 0 and preflight["creation_supported"] is True and preflight["auth_ok"] is True

    result, code = _invoke(repo, shell, mode, gh)
    assert code == 0, result
    assert result["status"] == "ok" and result["action"] == mode.lower() and result["pr_number"] == 7

    _write(repo / f".devspark.work/specs/{WORK_BRANCH}/work.md", f"# Work\n\n**Status**: Complete\n\n## Required Obligations\n\n{OBLIGATION}\n")
    git(repo, "add", "-A")
    commit_and_push_branch(repo, WORK_BRANCH, "an obligation appears")
    result, code = _invoke(repo, shell, mode, gh)
    assert code == 1
    assert result["error"] is True and "OBLIGATION" in result["message"]

    (repo / "README.md").write_text("uncommitted\n", encoding="utf-8")
    result, code = _invoke(repo, shell, mode, gh)
    assert code == 1
    assert result["error"] is True and result["message"] == "Working tree has unmanaged changes"


@pytest.mark.skipif(not PWSH or not BASH, reason="both shells required")
@pytest.mark.parametrize(
    "obligations",
    ["", OBLIGATION, OBLIGATION.replace("[ ]", "[x]"), OBLIGATION.replace("[ ]", "[x]") + " — Evidence: PRIV-0000"],
    ids=["none", "open", "checked-without-evidence", "checked-with-evidence"],
)
def test_both_shells_report_the_same_lifecycle(tmp_path: Path, obligations: str) -> None:
    repo = build_repo(tmp_path)
    start_work_branch(repo, obligations=obligations)
    assert lifecycle(repo, "ps") == lifecycle(repo, "bash")


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _flat(rel: str) -> str:
    return " ".join(_read(rel).replace("**", "").replace("`", "").split())


def test_create_pr_prompt_states_the_readiness_boundary() -> None:
    text = _flat("templates/commands/create-pr.md")
    assert "readiness boundary" in text
    assert "knowledge.readiness" in text and "blocked" in text
    assert "draft" in text and "--auto" in text and "do not bypass" in text
    assert "no readiness override" in text
    assert "never regenerates" in text
    assert "builds" in text
    assert "stale_entities" not in text and "stale-entity" not in text


def test_pr_review_knowledge_check_is_read_only_and_head_verified() -> None:
    section = _read("templates/commands/pr-review.md").split("### 6c.", 1)[1].split("### 6d.", 1)[0]
    flat = " ".join(section.replace("`", "").split())
    assert "check it out or stop" in flat
    assert "never regenerate" in flat.lower()
    assert "--check" not in section


def test_implement_does_not_require_regenerating_or_committing_derived_indexes() -> None:
    text = _flat("templates/commands/implement.md")
    assert "Regenerate .knowledge/index.json" not in text
    assert "provisional" not in text


@pytest.mark.parametrize(
    "rel",
    [".knowledge/governance/devspark-prompt-mapping.md", "site/src/guides/prompt-lifecycle-mapping.md"],
)
def test_canonical_lifecycle_and_published_twin_state_the_boundary(rel: str) -> None:
    text = _flat(rel)
    assert "ready for other people to review" in text
    assert "not completion detection" in text
