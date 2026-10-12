# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Create PR proves committed-state Knowledge readiness for the exact HEAD it submits.

`stale_entities` in `.knowledge/index.json` comes from committed Git history, so a green
pre-commit regeneration proves nothing about the commit that will be reviewed. These tests build
real temporary Git repositories with controlled commit dates and drive both the PowerShell and
Bash Create PR scripts against them.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PWSH = shutil.which("pwsh")
BASH_CANDIDATES = [r"C:\Program Files\Git\bin\bash.exe", shutil.which("bash")]
TIMEOUT = 180

BASE_DATE = "2026-10-01T09:00:00+00:00"
WORK_DATE = "2026-10-05T09:00:00+00:00"
LATER_DATE = "2026-10-09T09:00:00+00:00"
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


def _entity(repo: Path, entity_id: str, source: str, last_verified: str) -> None:
    base = repo / ".knowledge/entities" / entity_id
    _write(base / "_entity.yaml", f"id: {entity_id}\ntype: subsystem\nowner: team-x\n")
    doc = layer_doc(last_verified, source).replace("Widget", entity_id.capitalize())
    _write(base / "architecture.md", doc)
    _write(repo / source, "value = 1\n")


def build_repo(
    tmp_path: Path,
    *,
    engine_mode: str = "real",
    track_index: bool = True,
    with_unrelated_stale: bool = False,
) -> Path:
    """A pushed `main` plus a pushed feature branch with no feature commits yet."""
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
    _write(repo / "src/other.py", "other = 1\n")
    _write(repo / f".devspark.work/specs/{BRANCH}/spec.md", "---\nclassification: quick-spec\n---\n\n# Quick Spec: Readiness\n")
    _entity(repo, "widget", "src/widget.py", "2026-10-01")
    if with_unrelated_stale:
        _entity(repo, "gadget", "src/gadget.py", "2026-10-01")
    if engine_mode == "real" and track_index:
        assert engine(repo).returncode == 0
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "baseline", date=BASE_DATE)
    if with_unrelated_stale:
        # Another change already on main made `gadget` stale; this branch never touches it.
        _write(repo / "src/gadget.py", "value = 2\n")
        assert engine(repo).returncode == 0
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "gadget changed on main", date="2026-10-03T09:00:00+00:00")
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "push", "-q", "-u", "origin", "main")
    git(repo, "checkout", "-q", "-b", BRANCH)
    git(repo, "push", "-q", "-u", "origin", BRANCH)
    return repo


def feature_commit(
    repo: Path,
    date: str,
    *,
    verified: str,
    source: str = "src/widget.py",
    regenerate: bool = True,
    message: str = "feature",
) -> None:
    """Change a source and its Knowledge doc, optionally regenerate, then commit and push."""
    with (repo / source).open("a", encoding="utf-8") as handle:
        handle.write("value += 1\n")
    _write(repo / ARCH_PATH, layer_doc(verified))
    if regenerate:
        assert engine(repo).returncode == 0
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message, date=date)
    git(repo, "push", "-q", "origin", BRANCH)


def finalize(repo: Path, date: str) -> None:
    """The developer's remediation: regenerate against committed state, commit, push."""
    assert engine(repo).returncode == 0
    git(repo, "add", "-A")
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo, check=False).returncode == 0:
        return  # regeneration was byte-identical; nothing to commit
    git(repo, "commit", "-q", "-m", "finalize derived knowledge", date=date)
    git(repo, "push", "-q", "origin", BRANCH)


def _run_shell(repo: Path, shell: str, mode: str, env: dict[str, str] | None = None) -> dict:
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
        return json.loads(done.stdout)
    except json.JSONDecodeError as exc:  # pragma: no cover - failure detail
        raise AssertionError(f"{shell} {mode} produced no JSON.\nstdout={done.stdout}\nstderr={done.stderr}") from exc


def knowledge(repo: Path, shell: str) -> dict:
    return _run_shell(repo, shell, "Preflight")["knowledge"]


def blockers(result: dict) -> list[tuple]:
    return sorted(
        (b["kind"], b["path"], b["source"], b["source_date"], b["last_verified"]) for b in result["blockers"]
    )


@pytest.mark.parametrize("shell", SHELLS)
def test_t1_pre_commit_green_then_commit_drifts(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    feature_commit(repo, WORK_DATE, verified="2026-10-04", regenerate=True)

    result = knowledge(repo, shell)
    assert result["readiness"] == "blocked"
    assert [b["kind"] for b in result["blockers"]] == ["drift"]
    assert result["index_fresh"] is False
    assert "DRIFT:" in result["check_output"]
    assert result["checked_head"] == git(repo, "rev-parse", "HEAD")


def test_t1_provisional_check_was_green_before_the_commit(tmp_path: Path) -> None:
    repo = build_repo(tmp_path)
    with (repo / "src/widget.py").open("a", encoding="utf-8") as handle:
        handle.write("value += 1\n")
    _write(repo / ARCH_PATH, layer_doc("2026-10-04"))
    assert engine(repo).returncode == 0
    assert engine(repo, "--check").returncode == 0
    assert json.loads((repo / INDEX_PATH).read_text(encoding="utf-8"))["stale_entities"] == []


@pytest.mark.parametrize("shell", SHELLS)
def test_t2_mechanical_finalization_makes_the_commit_ready(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    assert engine(repo).returncode == 0
    # Knowledge doc gains a heading after the last regeneration: mechanical drift only.
    _write(repo / ARCH_PATH, layer_doc("2026-10-01", extra="\n## Behavior\n\nDetails.\n"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "doc edit without regeneration", date=BASE_DATE)
    git(repo, "push", "-q", "origin", BRANCH)
    assert knowledge(repo, shell)["readiness"] == "blocked"

    finalize(repo, BASE_DATE)
    result = knowledge(repo, shell)
    assert result["readiness"] == "ready"
    assert result["blockers"] == []
    assert result["index_fresh"] is True


@pytest.mark.parametrize("shell", SHELLS)
def test_t3_stale_touched_entity_blocks_and_regeneration_alone_does_not_clear_it(
    tmp_path: Path, shell: str
) -> None:
    repo = build_repo(tmp_path)
    feature_commit(repo, WORK_DATE, verified="2026-10-04")
    finalize(repo, WORK_DATE)

    result = knowledge(repo, shell)
    assert result["readiness"] == "blocked"
    assert result["index_fresh"] is True, "index is mechanically current; the entity itself is stale"
    assert blockers(result) == [("stale-entity", ARCH_PATH, "src/widget.py", "2026-10-05", "2026-10-04")]

    finalize(repo, WORK_DATE)  # regenerating again must not turn stale into fresh
    assert knowledge(repo, shell)["readiness"] == "blocked"


@pytest.mark.parametrize("shell", SHELLS)
def test_t4_genuine_reverification_makes_it_ready(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    feature_commit(repo, WORK_DATE, verified="2026-10-04")
    finalize(repo, WORK_DATE)
    assert knowledge(repo, shell)["readiness"] == "blocked"

    _write(repo / ARCH_PATH, layer_doc("2026-10-05"))  # stands in for a genuine re-verification
    finalize(repo, WORK_DATE)
    result = knowledge(repo, shell)
    assert result["readiness"] == "ready"
    assert result["stale_untouched_count"] == 0


@pytest.mark.parametrize("shell", SHELLS)
def test_t5_uncited_code_change_needs_no_finalization(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    feature_commit(repo, WORK_DATE, verified="2026-10-01", source="src/other.py")
    result = knowledge(repo, shell)
    assert result["readiness"] == "ready"
    assert result["blockers"] == []


@pytest.mark.parametrize("shell", SHELLS)
def test_t6_no_tracked_index_is_not_applicable(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path, track_index=False)
    result = knowledge(repo, shell)
    assert result["readiness"] == "not-applicable"
    assert result["blockers"] == []
    assert result["index_fresh"] is None


@pytest.mark.parametrize("shell", SHELLS)
def test_t7_missing_engine_is_unknown(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path, engine_mode="none")
    result = knowledge(repo, shell)
    assert result["readiness"] == "unknown"
    assert result["index_fresh"] is None


@pytest.mark.parametrize("shell", SHELLS)
def test_t7_unsupported_engine_usage_is_unknown(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path, engine_mode="exit2")
    _write(repo / INDEX_PATH, "{}\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "track an index", date=BASE_DATE)
    git(repo, "push", "-q", "origin", BRANCH)
    result = knowledge(repo, shell)
    assert result["readiness"] == "unknown"
    assert result["blockers"] == []


@pytest.mark.parametrize("shell", SHELLS)
def test_t7_missing_interpreter_is_unknown_not_a_crash(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    tool_dirs = [str(Path(shutil.which(tool)).parent) for tool in ("git", "jq") if shutil.which(tool)]
    minimal = os.pathsep.join(tool_dirs)
    if shutil.which("python3", path=minimal) or shutil.which("python", path=minimal):
        pytest.skip("a Python interpreter shares a directory with git/jq on this machine")
    env = _env(minimal)
    result = _run_shell(repo, shell, "Preflight", env)["knowledge"]
    assert result["readiness"] == "unknown"
    assert result["blockers"] == []


@pytest.mark.parametrize("shell", SHELLS)
def test_a_build_failure_blocks_with_the_error(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    _write(repo / ARCH_PATH, layer_doc("2026-10-01", source="src/missing.py"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "cite a file that does not exist", date=BASE_DATE)
    git(repo, "push", "-q", "origin", BRANCH)
    result = knowledge(repo, shell)
    assert result["readiness"] == "blocked"
    assert [b["kind"] for b in result["blockers"]] == ["build-error"]
    assert "does not exist" in result["blockers"][0]["message"]


@pytest.mark.parametrize("shell", SHELLS)
def test_t8_rebase_to_later_dates_blocks_a_previously_green_branch(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    feature_commit(repo, WORK_DATE, verified="2026-10-05")
    assert knowledge(repo, shell)["readiness"] == "ready"

    git(repo, "rebase", "-q", "--force-rebase", "origin/main", date=LATER_DATE)
    git(repo, "push", "-q", "--force", "origin", BRANCH)
    result = knowledge(repo, shell)
    assert result["readiness"] == "blocked"
    assert result["checked_head"] == git(repo, "rev-parse", "HEAD")


@pytest.mark.parametrize("shell", SHELLS)
def test_t9_committing_generated_artifacts_converges(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    feature_commit(repo, WORK_DATE, verified="2026-10-05")
    for _ in range(2):
        finalize(repo, LATER_DATE)  # regenerate and commit again, later than the source commit
        assert engine(repo, "--check").returncode == 0
        assert knowledge(repo, shell)["readiness"] == "ready"


@pytest.mark.parametrize("shell", SHELLS)
def test_t10_corrupt_index_is_caught_by_a_read_only_check(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    feature_commit(repo, WORK_DATE, verified="2026-10-05")
    assert knowledge(repo, shell)["readiness"] == "ready"

    payload = json.loads((repo / INDEX_PATH).read_text(encoding="utf-8"))
    payload["nodes"] = []
    _write(repo / INDEX_PATH, json.dumps(payload, indent=2) + "\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "corrupt index", date=WORK_DATE)
    git(repo, "push", "-q", "origin", BRANCH)
    before = (repo / INDEX_PATH).read_bytes()

    checked = engine(repo, "--check")
    assert checked.returncode == 1 and "DRIFT:" in checked.stderr
    assert (repo / INDEX_PATH).read_bytes() == before, "--check must never write"
    assert git(repo, "status", "--porcelain") == ""
    assert knowledge(repo, shell)["readiness"] == "blocked"


@pytest.mark.parametrize("shell", SHELLS)
def test_t12_unrelated_stale_entity_is_counted_not_blocking(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path, with_unrelated_stale=True)
    feature_commit(repo, WORK_DATE, verified="2026-10-05")
    result = knowledge(repo, shell)
    assert result["readiness"] == "ready"
    assert result["stale_untouched_count"] == 1
    assert result["blockers"] == []


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("mode", ["Create", "Update"])
def test_t12_create_and_update_modes_block_identically(tmp_path: Path, shell: str, mode: str) -> None:
    repo = build_repo(tmp_path)
    feature_commit(repo, WORK_DATE, verified="2026-10-04")
    finalize(repo, WORK_DATE)  # mechanically current, but a touched entity is stale

    result = _run_shell(repo, shell, mode)
    assert result["error"] is True
    assert result["message"] == "CREATE PR BLOCKED — KNOWLEDGE RE-VERIFICATION REQUIRED"
    assert ARCH_PATH in result["details"] and "src/widget.py" in result["details"]
    assert "2026-10-05" in result["details"] and "2026-10-04" in result["details"]
    assert result["checked_head"] == git(repo, "rev-parse", "HEAD")
    assert [b["kind"] for b in result["blockers"]] == ["stale-entity"]


@pytest.mark.parametrize("shell", SHELLS)
def test_drift_failure_is_actionable_and_names_the_stale_lines(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    feature_commit(repo, WORK_DATE, verified="2026-10-04")
    result = _run_shell(repo, shell, "Create")
    assert result["message"] == "CREATE PR BLOCKED — COMMITTED KNOWLEDGE FINALIZATION REQUIRED"
    assert "Committed HEAD: " + git(repo, "rev-parse", "HEAD") in result["details"]
    assert "STALE:" in result["details"]
    assert "build_knowledge_index.py --repo-root ." in result["details"]
    assert "Rerun /devspark.create-pr" in result["details"]
    assert git(repo, "status", "--porcelain") == "", "Create PR must not modify the working tree"
    assert git(repo, "rev-parse", "HEAD") == result["checked_head"], "Create PR must not commit"


@pytest.mark.parametrize("shell", SHELLS)
def test_build_failure_message_has_its_own_headline(tmp_path: Path, shell: str) -> None:
    repo = build_repo(tmp_path)
    _write(repo / ARCH_PATH, layer_doc("2026-10-01", source="src/missing.py"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "cite a file that does not exist", date=BASE_DATE)
    git(repo, "push", "-q", "origin", BRANCH)
    result = _run_shell(repo, shell, "Create")
    assert result["message"] == "CREATE PR BLOCKED — KNOWLEDGE INDEX CANNOT BE BUILT"
    assert "does not exist" in result["details"]


@pytest.mark.skipif(not PWSH or not BASH, reason="both shells required")
@pytest.mark.parametrize("scenario", ["ready", "drift", "stale", "untouched-stale", "not-applicable"])
def test_t11_bash_and_powershell_agree(tmp_path: Path, scenario: str) -> None:
    if scenario == "not-applicable":
        repo = build_repo(tmp_path, track_index=False)
    elif scenario == "untouched-stale":
        repo = build_repo(tmp_path, with_unrelated_stale=True)
        feature_commit(repo, WORK_DATE, verified="2026-10-05")
    else:
        repo = build_repo(tmp_path)
        if scenario == "ready":
            feature_commit(repo, WORK_DATE, verified="2026-10-05")
        elif scenario == "drift":
            feature_commit(repo, WORK_DATE, verified="2026-10-04")
        else:
            feature_commit(repo, WORK_DATE, verified="2026-10-04")
            finalize(repo, WORK_DATE)

    ps = knowledge(repo, "ps")
    sh = knowledge(repo, "bash")
    for field in ("readiness", "index_fresh", "stale_untouched_count", "checked_head"):
        assert ps[field] == sh[field], field
    assert blockers(ps) == blockers(sh)
    assert set(ps) == set(sh) == {
        "index_fresh",
        "gap_summary",
        "readiness",
        "blockers",
        "stale_untouched_count",
        "checked_head",
        "check_output",
    }
    for blocker in ps["blockers"]:
        assert set(blocker) == {"kind", "path", "source", "source_date", "last_verified", "message"}
        assert "\\" not in (blocker["path"] or "")


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
    assert "never regenerates" in text and "last_verified" in text


def test_pr_review_knowledge_check_is_read_only_and_head_verified() -> None:
    section = _read("templates/commands/pr-review.md").split("### 6c.", 1)[1].split("### 6d.", 1)[0]
    flat = " ".join(section.replace("`", "").split())
    assert "--check" in flat
    assert "git rev-parse HEAD" in flat and "commit SHA" in flat
    assert "never regenerate" in flat.lower()
    assert "default (non-`--check`)" not in section


def test_implement_marks_git_dependent_generated_knowledge_provisional() -> None:
    text = _flat("templates/commands/implement.md")
    assert "provisional" in text and "Create PR" in text and "committed" in text


@pytest.mark.parametrize(
    "rel",
    [".knowledge/governance/devspark-prompt-mapping.md", "site/src/guides/prompt-lifecycle-mapping.md"],
)
def test_canonical_lifecycle_and_published_twin_state_the_boundary(rel: str) -> None:
    text = _flat(rel)
    assert "ready for other people to review" in text
    assert "not completion detection" in text
