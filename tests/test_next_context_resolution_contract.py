# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""next-context resolves the active spec by identity, not by exact branch name."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parent.parent
PS_SCRIPT = ROOT / "scripts" / "powershell" / "next-context.ps1"
SH_SCRIPT = ROOT / "scripts" / "bash" / "next-context.sh"
GIT_BASH = Path(r"C:\Program Files\Git\bin\bash.exe")


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, timeout=60, stdin=subprocess.DEVNULL)


def _bash() -> str | None:
    if os.name == "nt":
        return str(GIT_BASH) if GIT_BASH.exists() and shutil.which("jq") else None
    return shutil.which("bash") if shutil.which("jq") else None


SHELLS = [
    pytest.param("pwsh", marks=pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh not available")),
    pytest.param("bash", marks=pytest.mark.skipif(_bash() is None, reason="bash with jq not available")),
]


_TEMPLATE_CACHE: dict[tuple, Path] = {}
_TEMP_ROOT: tempfile.TemporaryDirectory | None = None


def _repo(tmp_path: Path, branch: str, specs=(), quickfixes=(), work_items=()) -> Path:
    global _TEMPLATE_CACHE, _TEMP_ROOT
    key = (branch, tuple(sorted(specs)), tuple(sorted(quickfixes)), tuple(sorted(work_items)))
    if key not in _TEMPLATE_CACHE:
        if _TEMP_ROOT is None:
            _TEMP_ROOT = tempfile.TemporaryDirectory()
        template = Path(_TEMP_ROOT.name) / f"tmpl_{len(_TEMPLATE_CACHE)}"
        (template / ".knowledge" / "governance").mkdir(parents=True)
        (template / ".knowledge" / "governance" / "constitution.md").write_text("# C\n", encoding="utf-8")
        for name in specs:
            spec = template / ".devspark.work" / "specs" / name
            spec.mkdir(parents=True)
            (spec / "spec.md").write_text("---\nclassification: full-spec\n---\n# S\n", encoding="utf-8")
        for name in quickfixes:
            record = template / ".devspark.work" / "quickfixes" / f"{name}.md"
            record.parent.mkdir(parents=True, exist_ok=True)
            record.write_text("# QF\n", encoding="utf-8")
        for name, status in work_items:
            record = template / ".devspark.work" / "specs" / name / "work.md"
            record.parent.mkdir(parents=True, exist_ok=True)
            record.write_text(f"# Work\n\n**Status**: {status}\n\n## Intended Outcome\nResume this change.\n", encoding="utf-8")
        _git(template, "init", "-q", "-b", branch)
        _git(template, "config", "user.email", "t@example.com")
        _git(template, "config", "user.name", "T")
        _git(template, "add", "-A")
        _git(template, "commit", "-q", "-m", "x")
        _TEMPLATE_CACHE[key] = template

    repo = tmp_path / "r"
    shutil.copytree(_TEMPLATE_CACHE[key], repo)
    return repo


def _run(shell: str, repo: Path, feature: str | None = None, pr: bool = False, python: bool = True) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "DEVSPARK_FEATURE"}
    host_stubs = repo.parent / "host-stubs"
    host_stubs.mkdir(exist_ok=True)
    for command in ("gh", "az"):
        executable = host_stubs / command
        reply = '{"number":123,"state":"OPEN"}' if pr and command == "gh" else ""
        executable.write_text("#!/bin/sh\n" + (f"printf '%s\\n' '{reply}'\n" if reply else "exit 1\n"), encoding="utf-8")
        executable.chmod(0o755)
        (host_stubs / f"{command}.cmd").write_text(f"@echo {reply}\n@exit /b 0\n" if reply else "@exit /b 1\n", encoding="utf-8")
    if not python:
        for command in ("python3", "python"):
            (host_stubs / command).write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            (host_stubs / command).chmod(0o755)
            (host_stubs / f"{command}.cmd").write_text("@exit /b 1\n", encoding="utf-8")
    # Planning Review state is computed by judge.py, so the shell needs this interpreter.
    env["PATH"] = str(host_stubs) + os.pathsep + str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    if feature:
        env["DEVSPARK_FEATURE"] = feature
    if shell == "pwsh":
        cmd = ["pwsh", "-NoProfile", "-File", str(PS_SCRIPT), "-Json"]
    else:
        cmd = [_bash(), str(SH_SCRIPT), "--json"]
    proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, timeout=120, stdin=subprocess.DEVNULL, env=env)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _run_prerequisites(shell: str, repo: Path) -> dict:
    if shell == "pwsh":
        command = ["pwsh", "-NoProfile", "-File", str(ROOT / "scripts/powershell/check-prerequisites.ps1"), "-Json", "-IncludeTasks"]
    else:
        command = [_bash(), str(ROOT / "scripts/bash/check-prerequisites.sh"), "--json", "--include-tasks"]
    proc = subprocess.run(command, cwd=repo, capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


@pytest.mark.parametrize("shell", SHELLS)
def test_branch_name_exactly_matches_the_spec_directory(tmp_path, shell):
    result = _run(shell, _repo(tmp_path, "001-demo", specs=["001-demo"]))

    assert result["SPEC_EXISTS"] is True and result["SPEC_FEATURE"] == "001-demo"


@pytest.mark.parametrize("shell", SHELLS)
def test_clean_default_branch_offers_one_universal_start(tmp_path, shell):
    result = _run(shell, _repo(tmp_path, "main"))

    assert result["STATE"] == "no-active-work"
    assert result["RECOMMENDED_COMMAND"] == "/devspark-specify"
    assert "quickfix" not in result["REASON"].lower()


@pytest.mark.parametrize("shell", SHELLS)
def test_new_work_branch_routes_to_implementation_without_a_record(tmp_path, shell):
    result = _run(shell, _repo(tmp_path, "132-work-catalog"))

    assert result["WORK_BRANCH"] is True
    assert result["WORK_RECORD_EXISTS"] is False
    assert result["SPEC_EXISTS"] is False
    assert result["STATE"] == "work-in-progress"
    assert result["RECOMMENDED_COMMAND"] == "/devspark-implement"


@pytest.mark.parametrize("shell", SHELLS)
def test_work_branch_prerequisites_do_not_require_a_bundle_or_record(tmp_path, shell):
    repo = _repo(tmp_path, "132-work-catalog")

    result = _run_prerequisites(shell, repo)

    assert Path(result["FEATURE_DIR"]).as_posix().endswith(".devspark.work/specs/132-work-catalog")
    assert result["AVAILABLE_DOCS"] == []


@pytest.mark.parametrize("shell", SHELLS)
def test_work_branch_prerequisites_expose_only_the_optional_resume_note(tmp_path, shell):
    repo = _repo(tmp_path, "132-work-catalog", work_items=[("132-work-catalog", "In Progress")])

    result = _run_prerequisites(shell, repo)

    assert result["AVAILABLE_DOCS"] == ["work.md"]


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("note", [False, True])
def test_work_branch_prerequisites_expose_an_optional_plan(tmp_path, shell, note):
    work_items = [("132-work-catalog", "In Progress")] if note else []
    repo = _repo(tmp_path, "132-work-catalog", work_items=work_items)
    plan = repo / ".devspark.work" / "specs" / "132-work-catalog" / "plan.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("# Plan\n\n## Decisions\n- Reuse the catalog loader.\n", encoding="utf-8")

    result = _run_prerequisites(shell, repo)

    assert result["AVAILABLE_DOCS"] == (["work.md", "plan.md"] if note else ["plan.md"])


def _work_branch_with_plan(tmp_path: Path, commit: bool, status: str | None = None) -> Path:
    work_items = [("132-work-catalog", status)] if status else []
    repo = _repo(tmp_path, "132-work-catalog", work_items=work_items)
    _git(repo, "branch", "main")
    plan = repo / ".devspark.work" / "specs" / "132-work-catalog" / "plan.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("# Plan\n\n## Decisions\n- Reuse the catalog loader.\n", encoding="utf-8")
    if commit:
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "plan")
    return repo


LEGACY_PLANNING_COMMANDS = {"/devspark-plan", "/devspark-tasks", "/devspark-analyze", "/devspark-critic", "/devspark-planning-review"}


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("commit,status,state,command", [
    (False, None, "work-in-progress", "/devspark-implement"),
    (False, "In Progress", "work-in-progress", "/devspark-implement"),
    (True, "In Progress", "work-in-progress", "/devspark-implement"),
    (True, None, "ready-for-pr", "/devspark-create-pr"),
    (True, "Complete", "ready-for-pr", "/devspark-create-pr"),
])
def test_an_optional_plan_keeps_work_on_the_universal_route(tmp_path, shell, commit, status, state, command):
    result = _run(shell, _work_branch_with_plan(tmp_path, commit, status))

    assert result["WORK_BRANCH"] is True
    assert result["SPEC_EXISTS"] is False
    assert result["IS_FULL_SPEC"] is False
    assert result["PLAN_EXISTS"] is False and result["TASKS_EXISTS"] is False
    assert result["STATE"] == state
    assert result["RECOMMENDED_COMMAND"] == command
    assert result["RECOMMENDED_COMMAND"] not in LEGACY_PLANNING_COMMANDS


@pytest.mark.parametrize("shell", SHELLS)
def test_work_resume_note_restores_in_progress_state(tmp_path, shell):
    result = _run(
        shell,
        _repo(tmp_path, "132-work-catalog", work_items=[("132-work-catalog", "In Progress")]),
    )

    assert result["WORK_RECORD_EXISTS"] is True
    assert result["WORK_STATUS"] == "In Progress"
    assert result["STATE"] == "work-in-progress"
    assert result["RECOMMENDED_COMMAND"] == "/devspark-implement"


@pytest.mark.parametrize("shell", SHELLS)
def test_completed_work_resume_note_reaches_existing_pr_path(tmp_path, shell):
    result = _run(
        shell,
        _repo(tmp_path, "132-work-catalog", work_items=[("132-work-catalog", "Complete")]),
    )

    assert result["WORK_RECORD_EXISTS"] is True
    assert result["WORK_STATUS"] == "Complete"
    assert result["WORK_COMPLETE"] is True
    assert result["STATE"] == "ready-for-pr"
    assert result["RECOMMENDED_COMMAND"] == "/devspark-create-pr"
    assert "not proof" not in result["REASON"]


@pytest.mark.parametrize("shell", SHELLS)
def test_completed_note_with_uncommitted_changes_routes_to_commit(tmp_path, shell):
    repo = _repo(tmp_path, "132-work-catalog", work_items=[("132-work-catalog", "Complete")])
    (repo / "change.txt").write_text("finished but not committed\n", encoding="utf-8")

    result = _run(shell, repo)

    assert result["DIRTY"] is True
    assert result["WORK_COMPLETE"] is True
    assert result["STATE"] == "uncommitted-changes"
    assert result["RECOMMENDED_COMMAND"] == "commit"


@pytest.mark.parametrize("shell", SHELLS)
def test_unfinished_note_with_uncommitted_changes_keeps_implementing(tmp_path, shell):
    repo = _repo(tmp_path, "132-work-catalog", work_items=[("132-work-catalog", "In Progress")])
    (repo / "change.txt").write_text("partial change\n", encoding="utf-8")

    result = _run(shell, repo)

    assert result["STATE"] == "work-in-progress"
    assert result["RECOMMENDED_COMMAND"] == "/devspark-implement"


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("status", ["complete", "COMPLETE", "  Complete  "])
def test_completion_status_is_read_case_insensitively(tmp_path, shell, status):
    result = _run(shell, _repo(tmp_path, "132-work-catalog", work_items=[("132-work-catalog", status)]))

    assert result["WORK_COMPLETE"] is True
    assert result["STATE"] == "ready-for-pr"


@pytest.mark.parametrize("shell", SHELLS)
def test_completion_status_survives_crlf_line_endings(tmp_path, shell):
    repo = _repo(tmp_path, "132-work-catalog")
    note = repo / ".devspark.work" / "specs" / "132-work-catalog" / "work.md"
    note.parent.mkdir(parents=True)
    note.write_bytes(b"# Work\r\n\r\n**Status**: Complete\r\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "note")

    result = _run(shell, repo)

    assert result["WORK_STATUS"] == "Complete"
    assert result["WORK_COMPLETE"] is True
    assert result["STATE"] == "ready-for-pr"


@pytest.mark.parametrize("shell", SHELLS)
def test_clean_committed_work_without_a_note_is_not_treated_as_proof_of_completion(tmp_path, shell):
    repo = _repo(tmp_path, "132-work-catalog")
    _git(repo, "branch", "main")
    (repo / "change.txt").write_text("committed change\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "change")

    result = _run(shell, repo)

    assert result["DIRTY"] is False
    assert result["WORK_HAS_CHANGES"] is True
    assert result["WORK_RECORD_EXISTS"] is False
    assert result["WORK_COMPLETE"] is False
    assert result["STATE"] == "ready-for-pr"
    assert result["RECOMMENDED_COMMAND"] == "/devspark-create-pr"
    assert "not proof the requested change is complete" in result["REASON"]
    assert "acceptance criteria, applicable verification, and any unresolved obligations" in result["REASON"]
    assert result["LIFECYCLE_STATUS"] == "" and result["LIFECYCLE_BLOCKERS"] == []


OBLIGATION = "Security review approved by the designated authority — Authority: Security Office"


def _work_note(tmp_path: Path, body: str, status: str = "Complete", dirty: bool = False) -> Path:
    repo = _repo(tmp_path, "132-work-catalog")
    _git(repo, "branch", "main")
    note = repo / ".devspark.work" / "specs" / "132-work-catalog" / "work.md"
    note.parent.mkdir(parents=True)
    note.write_text(f"# Work\n\n**Status**: {status}\n\n{body}", encoding="utf-8")
    (repo / "change.txt").write_text("committed change\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "change")
    if dirty:
        (repo / "change.txt").write_text("edited again\n", encoding="utf-8")
    return repo


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("body", [
    "## Intended Outcome\nReject invalid quantities.\n",
    f"## Required Obligations\n- [x] {OBLIGATION} (evidence: review record SR-0)\n",
    "## Material Decisions\n- Keep v1 alongside v2 — Basis: src/api.py @ abc1234\n\n"
    "## Assurance Findings\n- [ ] critic-001 consider caching quotes (advisory)\n",
], ids=["no-obligations", "obligation-satisfied", "advisory-finding-only"])
def test_work_that_passes_lifecycle_reaches_the_pr_path(tmp_path, shell, body):
    result = _run(shell, _work_note(tmp_path, body))

    assert result["LIFECYCLE_STATUS"] == "pass" and result["LIFECYCLE_BLOCKERS"] == []
    assert result["STATE"] == "ready-for-pr"
    assert result["RECOMMENDED_COMMAND"] == "/devspark-create-pr"
    assert "Delivery stays blocked" not in result["REASON"]


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh not available")
def test_an_in_process_run_reports_success_when_the_lifecycle_check_fails(tmp_path):
    # Agent terminals call the script in-process and read $LASTEXITCODE, which a nested judge.py run must not leak into.
    repo = _work_note(tmp_path, f"## Required Obligations\n- [ ] {OBLIGATION}\n")
    env = {k: v for k, v in os.environ.items() if k != "DEVSPARK_FEATURE"}
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    script = f"& '{PS_SCRIPT}' -Json | Out-Null; exit $LASTEXITCODE"
    proc = subprocess.run(["pwsh", "-NoProfile", "-Command", script], cwd=repo, capture_output=True, text=True,
                          timeout=120, stdin=subprocess.DEVNULL, env=env)
    assert proc.returncode == 0, proc.stderr
    assert _run("pwsh", repo)["STATE"] == "delivery-blocked"


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("pr", [False, True])
def test_an_unresolved_obligation_blocks_the_pr_recommendation(tmp_path, shell, pr):
    result = _run(shell, _work_note(tmp_path, f"## Required Obligations\n- [ ] {OBLIGATION}\n"), pr=pr)

    assert result["LIFECYCLE_STATUS"] == "fail"
    assert result["LIFECYCLE_BLOCKERS"] == ["required-obligation-unresolved"]
    assert result["STATE"] == "delivery-blocked"
    assert result["RECOMMENDED_COMMAND"] == "resolve-obligation"
    assert "Security review approved by the designated authority" in result["REASON"]
    assert "authority: Security Office" in result["REASON"]
    assert "not ready for a PR" in result["REASON"]


@pytest.mark.parametrize("shell", SHELLS)
def test_a_checked_obligation_without_an_evidence_reference_still_blocks_delivery(tmp_path, shell):
    result = _run(shell, _work_note(tmp_path, f"## Required Obligations\n- [x] {OBLIGATION}\n"))

    assert result["LIFECYCLE_BLOCKERS"] == ["required-obligation-unresolved"]
    assert result["STATE"] == "delivery-blocked"
    assert result["RECOMMENDED_COMMAND"] == "resolve-obligation"
    assert "is checked without an evidence reference" in result["REASON"]


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("status,dirty,state,command", [
    ("In Progress", False, "work-in-progress", "/devspark-implement"),
    ("Complete", True, "uncommitted-changes", "commit"),
])
def test_an_open_obligation_is_named_before_delivery_without_changing_the_route(tmp_path, shell, status, dirty, state, command):
    repo = _work_note(tmp_path, f"## Required Obligations\n- [ ] {OBLIGATION}\n", status=status, dirty=dirty)

    result = _run(shell, repo)

    assert "required-obligation-unresolved" in result["LIFECYCLE_BLOCKERS"]
    assert result["STATE"] == state
    assert result["RECOMMENDED_COMMAND"] == command
    assert "Delivery stays blocked until this is resolved" in result["REASON"]
    assert "Security review approved by the designated authority" in result["REASON"]
    assert "is not marked Complete" not in result["REASON"]


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("declared", [True, False], ids=["obligations-declared", "no-obligations"])
def test_an_unavailable_lifecycle_check_is_unconfirmed_not_passed(tmp_path, shell, declared):
    body = f"## Required Obligations\n- [ ] {OBLIGATION}\n" if declared else "## Intended Outcome\nResume this change.\n"
    result = _run(shell, _work_note(tmp_path, body), python=False)

    assert result["LIFECYCLE_STATUS"] == "unavailable" and result["LIFECYCLE_BLOCKERS"] == []
    assert result["STATE"] == "ready-for-pr"
    assert "delivery readiness is unconfirmed, not passed" in result["REASON"]
    refusal = "/devspark-create-pr will refuse until the check can run"
    assert (refusal in result["REASON"]) is declared


@pytest.mark.parametrize("shell", SHELLS)
def test_routing_reads_the_lifecycle_check_without_changing_the_note(tmp_path, shell):
    repo = _work_note(tmp_path, f"## Required Obligations\n- [ ] {OBLIGATION}\n")
    note = repo / ".devspark.work" / "specs" / "132-work-catalog" / "work.md"
    before = note.read_bytes()

    _run(shell, repo)

    assert note.read_bytes() == before
    assert sorted(p.name for p in note.parent.iterdir()) == ["work.md"]


def test_next_auto_stops_before_pr_for_unconfirmed_work() -> None:
    text = " ".join((ROOT / "templates" / "commands" / "next.md").read_text(encoding="utf-8").split())
    assert "`ready-for-pr` is reached on a work branch (`WORK_BRANCH` true) whose `WORK_COMPLETE` is false" in text
    assert "Git cleanliness and commits do not prove the requested change is complete" in text


def test_next_prompt_routes_delivery_on_the_lifecycle_check() -> None:
    """Prompt-wording check only: it does not observe agent behaviour."""
    text = " ".join((ROOT / "templates" / "commands" / "next.md").read_text(encoding="utf-8").split())
    assert "the same check `/devspark-create-pr` runs before publishing" in text
    assert "do not re-parse `work.md` to second-guess it" in text
    assert "| `resolve-obligation` |" in text
    assert "Never check the entry without evidence and never route to `/devspark-create-pr` while it is open" in text
    assert "The recommendation becomes `commit`, `sync`, `merge`, or `resolve-obligation`" in text


def test_work_branch_planning_is_advisory_in_prompts() -> None:
    """Prompt-wording check only: it does not observe agent behaviour."""
    def flat(name: str) -> str:
        return " ".join((ROOT / "templates" / "commands" / name).read_text(encoding="utf-8").split())

    plan, implement, next_cmd = flat("plan.md"), flat("implement.md"), flat("next.md")
    assert "If `WORK_BRANCH` is true, follow **Work Branch Planning**" in plan
    work_section = plan[plan.index("## Work Branch Planning"):plan.index("## Phases")]
    assert "the plan is optional and advisory" in work_section
    assert "`work.md` is a resume note, not a specification" in work_section
    assert "compute or stamp `spec_semantic_hash`" in work_section
    assert "Do not run, schedule or require `/devspark-analyze`, `/devspark-critic`, `/devspark-planning-review` or `/devspark-tasks`" in work_section
    assert "The next step is `/devspark-implement`, which may consume the plan but never requires it" in work_section
    assert "Read `FEATURE_DIR/plan.md` when `AVAILABLE_DOCS` lists it; its absence is also valid" in implement
    assert "It is advisory. It adds no required gate, task list, or Planning Review, and its absence never blocks implementation" in implement
    assert "the work stays on this route and resumes here" in implement
    assert "An optional `plan.md` on a work branch is advisory: it does not set these fields, change the work route" in next_cmd


def _require_plan(shell: str, repo: Path) -> subprocess.CompletedProcess:
    if shell == "pwsh":
        command = ["pwsh", "-NoProfile", "-File", str(ROOT / "scripts/powershell/check-prerequisites.ps1"), "-Json", "-RequirePlan"]
    else:
        command = [_bash(), str(ROOT / "scripts/bash/check-prerequisites.sh"), "--json", "--require-plan"]
    return subprocess.run(command, cwd=repo, capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("note", [False, True])
def test_task_coordination_on_a_work_branch_needs_no_plan(tmp_path, shell, note):
    work_items = [("132-work-catalog", "In Progress")] if note else []
    proc = _require_plan(shell, _repo(tmp_path, "132-work-catalog", work_items=work_items))

    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["AVAILABLE_DOCS"] == (["work.md"] if note else [])


@pytest.mark.parametrize("shell", SHELLS)
def test_legacy_task_generation_still_requires_a_plan(tmp_path, shell):
    proc = _require_plan(shell, _repo(tmp_path, "045-spec-catalog", specs=["045-spec-catalog"]))

    assert proc.returncode != 0
    assert "plan.md not found" in proc.stdout + proc.stderr


def _declared_script(command: str, shell: str) -> list[str]:
    line = _frontmatter(command)["scripts"]["ps" if shell == "pwsh" else "sh"].split()
    script = str(ROOT / line[0].removeprefix(".devspark/"))
    return ["pwsh", "-NoProfile", "-File", script, *line[1:]] if shell == "pwsh" else [_bash(), script, *line[1:]]


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("command", ["analyze.md", "critic.md"])
@pytest.mark.parametrize("branch,kwargs", [
    ("132-work-catalog", {}),
    ("132-work-catalog", {"work_items": [("132-work-catalog", "In Progress")]}),
    ("007-fix-typo", {"quickfixes": ["007-fix-typo"]}),
])
def test_assurance_can_be_invoked_without_a_task_list(tmp_path, shell, command, branch, kwargs):
    proc = subprocess.run(
        _declared_script(command, shell), cwd=_repo(tmp_path, branch, **kwargs),
        capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "tasks.md" not in json.loads(proc.stdout)["AVAILABLE_DOCS"]


def test_quickfix_scope_growth_adds_assurance_without_converting_the_route():
    """Handoff structure is checked here; the surrounding guidance is prompt wording only."""
    handoffs = _frontmatter("quickfix.md")["handoffs"]

    assert "devspark-specify" not in [h["agent"] for h in handoffs]
    assert all(h.get("send") is not True for h in handoffs)
    assert "devspark-critic" in [h["agent"] for h in handoffs]


DELIVERABLES_NOTE = (
    "# Work\n\n**Status**: {status}\n\n## Remaining Deliverables\n"
    "- [x] Loader returns the catalog\n- [ ] Search uses the loader (after: Loader returns the catalog)\n"
)


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("status,state,command", [
    ("In Progress", "work-in-progress", "/devspark-implement"),
    ("Complete", "ready-for-pr", "/devspark-create-pr"),
])
def test_persisted_deliverables_keep_work_on_the_universal_route(tmp_path, shell, status, state, command):
    repo = _repo(tmp_path, "132-work-catalog")
    _git(repo, "branch", "main")
    note = repo / ".devspark.work" / "specs" / "132-work-catalog" / "work.md"
    note.parent.mkdir(parents=True)
    note.write_text(DELIVERABLES_NOTE.format(status=status), encoding="utf-8")
    # An unchecked task list without a spec is coordination; it never reroutes or gates the work.
    (note.parent / "tasks.md").write_text("- [ ] T001 optional cache warm-up\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "coordinate")

    result = _run(shell, repo)

    assert result["WORK_BRANCH"] is True
    assert result["SPEC_EXISTS"] is False and result["IS_FULL_SPEC"] is False
    assert result["TASKS_EXISTS"] is False
    assert result["WORK_COMPLETE"] is (status == "Complete")
    assert result["STATE"] == state
    assert result["RECOMMENDED_COMMAND"] == command
    assert result["RECOMMENDED_COMMAND"] not in LEGACY_PLANNING_COMMANDS


INCIDENTAL_SPEC = "---\nclassification: full-spec\nrequired_gates: checklist, analyze, critic\n---\n# Notes\n"


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("status,state,command", [
    ("In Progress", "work-in-progress", "/devspark-implement"),
    ("Complete", "ready-for-pr", "/devspark-create-pr"),
])
def test_an_incidental_spec_file_never_converts_a_work_branch(tmp_path, shell, status, state, command):
    repo = _repo(tmp_path, "132-work-catalog")
    _git(repo, "branch", "main")
    work_dir = repo / ".devspark.work" / "specs" / "132-work-catalog"
    work_dir.mkdir(parents=True)
    (work_dir / "work.md").write_text(DELIVERABLES_NOTE.format(status=status), encoding="utf-8")
    (work_dir / "plan.md").write_text("# Plan\n\nUse the existing loader.\n", encoding="utf-8")
    (work_dir / "tasks.md").write_text("- [ ] T001 optional cache warm-up\n", encoding="utf-8")
    # A file named like a legacy bundle does not make this work a legacy bundle: the branch type decides.
    (work_dir / "spec.md").write_text(INCIDENTAL_SPEC, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "work with incidental files")

    result = _run(shell, repo)

    assert result["WORK_BRANCH"] is True
    assert result["SPEC_EXISTS"] is False and result["IS_FULL_SPEC"] is False
    assert result["TASKS_EXISTS"] is False and result["PENDING_GATES"].strip() == ""
    assert result["STATE"] == state
    assert result["RECOMMENDED_COMMAND"] == command


def test_judge_treats_a_work_directory_with_an_incidental_spec_file_as_universal_work(tmp_path):
    repo = _repo(tmp_path, "132-work-catalog")
    work_dir = repo / ".devspark.work" / "specs" / "132-work-catalog"
    work_dir.mkdir(parents=True)
    (work_dir / "work.md").write_text(DELIVERABLES_NOTE.format(status="Complete"), encoding="utf-8")
    (work_dir / "tasks.md").write_text("- [ ] T001 optional cache warm-up\n", encoding="utf-8")
    (work_dir / "spec.md").write_text(INCIDENTAL_SPEC, encoding="utf-8")
    judge = ROOT / "scripts" / "judge.py"

    def judge_json(*args: str) -> dict:
        proc = subprocess.run(
            [sys.executable, str(judge), *args], cwd=repo,
            capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL,
        )
        return json.loads(proc.stdout)

    lifecycle = judge_json("lifecycle", "--feature-dir", str(work_dir))
    resolved = judge_json("resolve", "--branch", "132-work-catalog")

    assert lifecycle["status"] == "pass", lifecycle
    assert resolved["status"] == "work-branch", resolved


def _frontmatter(name: str) -> dict:
    text = (ROOT / "templates" / "commands" / name).read_text(encoding="utf-8")
    return yaml.safe_load(text.split("---", 2)[1])


@pytest.mark.parametrize("name", ["plan.md", "tasks.md"])
def test_plan_and_tasks_hand_off_only_to_route_aware_next(name):
    handoffs = _frontmatter(name)["handoffs"]

    assert [h["agent"] for h in handoffs] == ["devspark-next"]
    assert all(h.get("send") is not True for h in handoffs)


def test_work_branch_task_coordination_is_optional_in_prompts() -> None:
    """Prompt-wording check only: it does not observe agent behaviour."""
    def flat(name: str) -> str:
        return " ".join((ROOT / "templates" / "commands" / name).read_text(encoding="utf-8").split())

    tasks, implement, specify = flat("tasks.md"), flat("implement.md"), flat("specify.md")
    assert "If the branch matches `NNN-work-*`, follow **Work Branch Coordination**" in tasks
    section = tasks[tasks.index("## Work Branch Coordination"):tasks.index("## Definition of Done")]
    assert "they are not a workflow stage" in section
    assert "Simple or single-deliverable work needs no decomposition" in section
    assert "A plan is never required" in section
    assert "not one entry per file edit" in section
    assert "with your agent's built-in task tracking" in section
    assert "Write nothing to the repository for this" in section
    assert "`## Remaining Deliverables`" in section
    assert "Do not create `tasks.md`, `spec.md`, `plan.md`, a checklist or a gate artifact" in section
    assert "no Analyze, Critic, Judge or Planning Review" in section
    assert "Open deliverables are coordination, not a completion gate" in section
    assert "`/devspark-tasks` coordinates them. Either way the work stays on this route" in implement
    assert "It is coordination, not a gate, and its absence is normal" in implement
    assert "Remaining deliverables, only when `/devspark-tasks` found that coordination must persist" in specify


@pytest.mark.parametrize("shell", SHELLS)
def test_legacy_full_spec_keeps_its_recorded_route(tmp_path, shell):
    result = _run(shell, _repo(tmp_path, "045-spec-catalog", specs=["045-spec-catalog"]))

    assert result["WORK_BRANCH"] is False
    assert result["SPEC_EXISTS"] is True and result["IS_FULL_SPEC"] is True
    assert result["STATE"] == "spec-needs-plan"
    assert result["RECOMMENDED_COMMAND"] == "/devspark-plan"


@pytest.mark.parametrize("shell", SHELLS)
def test_legacy_quick_spec_continues_without_conversion(tmp_path, shell):
    repo = _repo(tmp_path, "046-quick-banner")
    spec = repo / ".devspark.work" / "specs" / "046-quick-banner" / "spec.md"
    spec.parent.mkdir(parents=True)
    original = "---\nclassification: quick-spec\n---\n# Quick Spec\n\n**Status**: In Progress\n\n## Action Plan\n- [ ] 1. Fix banner\n"
    spec.write_text(original, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "quick spec")

    result = _run(shell, repo)

    assert result["WORK_BRANCH"] is False
    assert result["IS_FULL_SPEC"] is False
    assert result["STATE"] == "quickspec-needs-implement"
    assert result["RECOMMENDED_COMMAND"] == "/devspark-implement"
    assert spec.read_text(encoding="utf-8") == original
    assert not (spec.parent / "work.md").exists()


@pytest.mark.parametrize("shell", SHELLS)
def test_work_branch_never_resolves_a_same_prefix_legacy_spec(tmp_path, shell):
    result = _run(shell, _repo(tmp_path, "132-work-catalog", specs=["132-spec-legacy"]))

    assert result["WORK_BRANCH"] is True
    assert result["SPEC_EXISTS"] is False
    assert result["SPEC_AMBIGUOUS"] is False
    assert result["RECOMMENDED_COMMAND"] == "/devspark-implement"


@pytest.mark.parametrize("shell", SHELLS)
def test_a_different_branch_name_resolves_by_numeric_prefix(tmp_path, shell):
    result = _run(shell, _repo(tmp_path, "132-sync-work", specs=["132-complaint-catalog"]))

    assert result["SPEC_EXISTS"] is True
    assert result["SPEC_FEATURE"] == "132-complaint-catalog"
    assert result["SPEC_AMBIGUOUS"] is False


@pytest.mark.parametrize("shell", SHELLS)
def test_a_fix_named_branch_without_a_quickfix_record_resolves_to_its_spec(tmp_path, shell):
    result = _run(shell, _repo(tmp_path, "132-fix-enhance-endpoint", specs=["132-spec-complaint-catalog"]))

    assert result["SPEC_FEATURE"] == "132-spec-complaint-catalog"
    assert result["QUICKFIX_EXISTS"] is False


@pytest.mark.parametrize("shell", SHELLS)
def test_a_quickfix_record_for_the_branch_still_means_a_quickfix(tmp_path, shell):
    result = _run(
        shell, _repo(tmp_path, "132-fix-x", specs=["132-spec-other"], quickfixes=["132-fix-x"])
    )

    assert result["QUICKFIX_EXISTS"] is True
    assert result["SPEC_EXISTS"] is False


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("completed,newline,complete,command", [
    ("", "\n", False, "/devspark-implement"),
    ("", "\r\n", False, "/devspark-implement"),
    (" 2026-07-24", "\n", True, "/devspark-create-pr"),
], ids=["blank", "blank-crlf", "dated"])
def test_a_blank_completed_field_keeps_the_quickfix_open(tmp_path, shell, completed, newline, complete, command):
    repo = _repo(tmp_path, "QF-2026-001", quickfixes=["QF-2026-001"])
    record = "\n".join([
        "# Quickfix QF-2026-001", "", "## Completion", "", f"- **Completed**:{completed}", "- **Commit**:", "- **PR**:", "",
    ])
    (repo / ".devspark.work" / "quickfixes" / "QF-2026-001.md").write_bytes(record.replace("\n", newline).encode("utf-8"))
    _git(repo, "commit", "-q", "-am", "record")

    result = _run(shell, repo)

    assert result["QUICKFIX_COMPLETE"] is complete
    assert result["RECOMMENDED_COMMAND"] == command


@pytest.mark.parametrize("shell", SHELLS)
def test_an_explicit_feature_override_wins_over_an_ambiguous_branch(tmp_path, shell):
    repo = _repo(tmp_path, "132-whatever", specs=["132-spec-a", "132-spec-b"])

    result = _run(shell, repo, feature="132-spec-b")

    assert result["SPEC_FEATURE"] == "132-spec-b"
    assert result["SPEC_AMBIGUOUS"] is False


@pytest.mark.parametrize("shell", SHELLS)
def test_ambiguous_resolution_fails_instead_of_guessing(tmp_path, shell):
    result = _run(shell, _repo(tmp_path, "132-whatever", specs=["132-spec-a", "132-spec-b"]))

    assert result["SPEC_AMBIGUOUS"] is True
    assert result["SPEC_EXISTS"] is False
    assert result["STATE"] == "ambiguous-spec"
    assert result["RECOMMENDED_COMMAND"] == "resolve"


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize(
    ("verdict", "remediation", "state", "command"),
    [
        ("STOP", False, "review-blocked", "/devspark-tasks"),
        ("STOP", True, "review-needs-recheck", "/devspark-planning-review"),
        ("CONDITIONAL", False, "review-needs-decision", "/devspark-planning-review"),
        ("PROCEED", False, "tasks-incomplete", "/devspark-implement"),
    ],
)
def test_next_follows_the_planning_review_verdict_before_implementation(
    tmp_path, shell, verdict, remediation, state, command
):
    repo = _repo(tmp_path, "132-sync-work", specs=["132-spec-x"])
    spec = repo / ".devspark.work" / "specs" / "132-spec-x"
    tasks = "- [ ] T001 a\n" + ("\n## Gate Remediation\n\n- [ ] T050 fix (resolves: analyze-001)\n" if remediation else "")
    (spec / "tasks.md").write_text(tasks, encoding="utf-8")
    (spec / "plan.md").write_text("# P\n", encoding="utf-8")
    (spec / "spec.md").write_text(
        "---\nclassification: full-spec\nrequired_gates: checklist, analyze, critic\n---\n# S\n", encoding="utf-8"
    )
    (spec / "gates").mkdir()
    (spec / "gates" / "judge.md").write_text(f"```yaml\ngate: judge\nverdict: {verdict}\n```\n", encoding="utf-8")

    result = _run(shell, repo)

    assert result["STATE"] == state
    assert result["RECOMMENDED_COMMAND"] == command
    assert result["JUDGE_VERDICT"] == verdict



TASK_STATES = {
    "none": "- [ ] T001 a\n- [ ] T002 b\n",
    "some": "- [x] T001 a\n- [ ] T002 b\n",
    "all": "- [x] T001 a\n- [x] T002 b\n",
}


def _reviewed_spec(tmp_path: Path, tasks: str, judge: str | None, analyze_hash: str | None = None) -> Path:
    repo = _repo(tmp_path, "132-sync-work", specs=["132-spec-x"])
    spec = repo / ".devspark.work" / "specs" / "132-spec-x"
    (spec / "tasks.md").write_text(tasks, encoding="utf-8")
    (spec / "plan.md").write_text("# P\n", encoding="utf-8")
    (spec / "spec.md").write_text(
        "---\nclassification: full-spec\nrequired_gates: checklist, analyze, critic\n---\n# S\n", encoding="utf-8"
    )
    (spec / "gates").mkdir()
    if judge is not None:
        (spec / "gates" / "judge.md").write_text(judge, encoding="utf-8")
    if analyze_hash is not None:
        (spec / "gates" / "analyze.md").write_text(
            "```yaml\ngate: analyze\nreviewed_artifacts:\n  - path: spec.md\n    hash: \"" + analyze_hash + "\"\nfindings: []\n```\n",
            encoding="utf-8",
        )
    return repo


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("progress", sorted(TASK_STATES))
@pytest.mark.parametrize(
    ("verdict", "state", "command"),
    [
        ("STOP", "review-blocked", "/devspark-tasks"),
        ("CONDITIONAL", "review-needs-decision", "/devspark-planning-review"),
    ],
)
def test_an_unresolved_review_outranks_task_progress(tmp_path, shell, progress, verdict, state, command):
    repo = _reviewed_spec(tmp_path, TASK_STATES[progress], f"```yaml\ngate: judge\nverdict: {verdict}\n```\n")

    result = _run(shell, repo)

    assert result["STATE"] == state and result["RECOMMENDED_COMMAND"] == command


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("progress", sorted(TASK_STATES))
def test_a_missing_required_review_outranks_task_progress(tmp_path, shell, progress):
    result = _run(shell, _reviewed_spec(tmp_path, TASK_STATES[progress], None))

    assert result["STATE"] == "tasks-need-review"


@pytest.mark.parametrize("shell", SHELLS)
def test_existing_children_do_not_replace_required_judge(tmp_path, shell):
    repo = _reviewed_spec(tmp_path, TASK_STATES["all"], None)
    gates = repo / ".devspark.work/specs/132-spec-x/gates"
    for name in ("analyze", "critic"):
        (gates / f"{name}.md").write_text(f"```yaml\ngate: {name}\nstatus: pass\n```\n", encoding="utf-8")
    result = _run(shell, repo)
    assert result["STATE"] == "tasks-need-review"


@pytest.mark.parametrize("shell", SHELLS)
def test_pending_authority_precedes_stop_remediation(tmp_path, shell):
    header = "```yaml\ngate: judge\nverdict: STOP\nconcerns:\n  - id: J-001\n    needs_authority: true\n```\n"
    repo = _reviewed_spec(tmp_path, TASK_STATES["all"], header)
    assert _run(shell, repo)["STATE"] == "review-needs-decision"


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("pr,state", [(False, "ready-for-pr"), (True, "pr-needs-review")])
def test_completed_retained_bundle_reaches_git_and_pr_states(tmp_path, shell, pr, state):
    repo = _reviewed_spec(tmp_path, TASK_STATES["all"], "```yaml\ngate: judge\nverdict: PROCEED\n```\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Complete synthetic work")
    result = _run(shell, repo, pr=pr)
    assert result["STATE"] == state
    assert result["SPEC_EXISTS"] is True
    assert "delete" not in result["REASON"].lower()


@pytest.mark.parametrize("shell", SHELLS)
def test_semantic_completion_bookkeeping_reaches_delivery_without_recheck(tmp_path, shell):
    repo = _reviewed_spec(tmp_path, TASK_STATES["none"], None)
    feature = repo / ".devspark.work/specs/132-spec-x"
    spec = feature / "spec.md"
    spec.write_text(
        spec.read_text(encoding="utf-8").replace("checklist, analyze, critic", "analyze, critic, verify:regression-pinned")
        + "\n**Status**: Draft\n", encoding="utf-8",
    )

    def record(path):
        raw = subprocess.run(["git", "hash-object", str(path)], cwd=repo, capture_output=True,
                             text=True, check=True, timeout=15, stdin=subprocess.DEVNULL)
        semantic = subprocess.run([sys.executable, str(ROOT / "scripts/judge.py"), "semantic-hash", "--path", str(path)],
                                  cwd=repo, capture_output=True, text=True, check=True, timeout=15, stdin=subprocess.DEVNULL)
        return {"hash": raw.stdout.strip(), "semantic_hash": json.loads(semantic.stdout)["semantic_hash"]}

    reviewed = [{"path": name, **record(feature / name)} for name in ("spec.md", "plan.md", "tasks.md")]
    children = {}
    for name in ("analyze", "critic"):
        path = feature / "gates" / f"{name}.md"
        data = {"gate": name, "status": "pass", "blocking": False, "reviewed_artifacts": reviewed, "findings": []}
        path.write_text("```yaml\n" + yaml.safe_dump(data, sort_keys=False) + "```\n", encoding="utf-8")
        children[name] = {"artifact": f"gates/{name}.md", "state": "fresh", "ran": True, **record(path)}
    header = {"gate": "judge", "verdict": "PROCEED", "children": children, "concerns": [], "decisions_needed": []}
    (feature / "gates/judge.md").write_text("```yaml\n" + yaml.safe_dump(header, sort_keys=False) + "```\n", encoding="utf-8")
    gate_bytes = {path: path.read_bytes() for path in (feature / "gates").glob("*.md")}
    spec.write_text(spec.read_text(encoding="utf-8").replace("Draft", "Complete"), encoding="utf-8")
    (feature / "tasks.md").write_text(TASK_STATES["all"] + "\n**Checkpoint**: Phase complete - 2026-10-04.\n", encoding="utf-8")
    plan = feature / "plan.md"
    plan.write_text(plan.read_text(encoding="utf-8") + "\n## Implementation Notes\nApproved tests passed.\n", encoding="utf-8")
    (feature / "gates/verify.md").write_text("```yaml\ngate: verify\nstatus: pass\nmodes:\n  - mode: regression-pinned\n    status: pass\n```\n", encoding="utf-8")
    (feature / "gates/closeout.md").write_text("```yaml\ngate: closeout\ndecision: complete\n```\n", encoding="utf-8")

    result = _run(shell, repo)

    assert result["STATE"] == "uncommitted-changes"
    assert result["JUDGE_NEEDS_RECHECK"] is False
    assert result["VERIFY_PASSED"] is True
    assert all(path.read_bytes() == content for path, content in gate_bytes.items())


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("owner", ["plan", "tasks", "unowned"])
def test_owned_stop_correction_routes_to_focused_recheck(tmp_path, shell, owner):
    header = "```yaml\ngate: judge\nverdict: STOP\nconcerns:\n  - id: J-001\n    resolution: simplify\n    classification: blocking-defect\n    change_shape: planning\n    needs_authority: false\n    revision_target: " + owner + "\n```\n"
    if owner == "unowned":
        header = "```yaml\ngate: judge\nverdict: PROCEED\n```\n"
    repo = _reviewed_spec(tmp_path, TASK_STATES["none"], header)
    feature = repo / ".devspark.work/specs/132-spec-x"
    artifacts = []
    for name in ("spec.md", "plan.md", "tasks.md"):
        result = subprocess.run(["git", "hash-object", str(feature / name)], cwd=repo, capture_output=True,
                                text=True, check=True, timeout=15, stdin=subprocess.DEVNULL)
        artifacts.append({"path": name, "hash": result.stdout.strip()})
    for name in ("analyze", "critic"):
        (feature / "gates" / f"{name}.md").write_text("```yaml\n" + yaml.safe_dump({"gate": name, "reviewed_artifacts": artifacts}) + "```\n", encoding="utf-8")
    before = (feature / "gates/judge.md").read_bytes()
    assert _run(shell, repo)["STATE"] == {"plan": "review-needs-plan", "tasks": "review-blocked", "unowned": "tasks-incomplete"}[owner]
    spec = feature / "spec.md"
    original_spec = spec.read_text(encoding="utf-8")
    spec.write_text(original_spec + "\n## Requirement\nNew scope requires authority.\n", encoding="utf-8")
    assert _run(shell, repo)["STATE"] == "review-needs-recheck"
    spec.write_text(original_spec, encoding="utf-8")
    if owner == "unowned":
        (feature / "plan.md").write_text("# Unreviewed design\n", encoding="utf-8")
        assert _run(shell, repo)["STATE"] == "review-needs-recheck"
        return
    if owner == "plan":
        plan = feature / "plan.md"
        plan.write_text(plan.read_text(encoding="utf-8") + "\n## Design\nRemove excess machinery.\n", encoding="utf-8")
        assert _run(shell, repo)["STATE"] == "plan-needs-reprojection"
        result = subprocess.run([sys.executable, str(ROOT / "scripts/judge.py"), "semantic-hash", "--path", str(plan)],
                                cwd=repo, capture_output=True, text=True, check=True, timeout=15, stdin=subprocess.DEVNULL)
        fingerprint = json.loads(result.stdout)["semantic_hash"]
        (feature / "tasks.md").write_text(f"---\nplan_semantic_hash: {fingerprint}\n---\n" + TASK_STATES["none"], encoding="utf-8")
    else:
        (feature / "tasks.md").write_text(TASK_STATES["none"] + "- [ ] T099 Apply the approved correction\n", encoding="utf-8")
    assert _run(shell, repo)["STATE"] == "review-needs-recheck"
    assert (feature / "gates/judge.md").read_bytes() == before


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("proof,closeout,state", [
    ("missing", "", "implementation-needs-verification"),
    ("wrong-mode", "complete", "implementation-needs-verification"),
    ("pass", "", "verification-needs-closeout"),
    ("pass", "not-complete", "closeout-not-complete"),
    ("pass", "complete", "uncommitted-changes"),
])
def test_completed_bundle_routes_through_required_proof(tmp_path, shell, proof, closeout, state):
    repo = _reviewed_spec(tmp_path, TASK_STATES["all"], "```yaml\ngate: judge\nverdict: PROCEED\n```\n")
    feature = repo / ".devspark.work/specs/132-spec-x"
    spec = feature / "spec.md"
    spec.write_text(spec.read_text(encoding="utf-8").replace("checklist, analyze, critic", "analyze, critic, verify:regression-pinned"), encoding="utf-8")
    if proof != "missing":
        mode = "end-to-end" if proof == "wrong-mode" else "regression-pinned"
        (feature / "gates/verify.md").write_text(
            f"```yaml\ngate: verify\nstatus: pass\nmodes:\n  - mode: {mode}\n    status: pass\n```\n", encoding="utf-8"
        )
    if closeout:
        (feature / "gates/closeout.md").write_text(f"```yaml\ngate: closeout\ndecision: {closeout}\n```\n", encoding="utf-8")
    result = _run(shell, repo)
    assert result["STATE"] == state
    assert result["VERIFY_PASSED"] is (proof == "pass")
    assert "delete" not in result["REASON"].lower()


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("progress", sorted(TASK_STATES))
def test_a_child_that_needs_a_recheck_outranks_task_progress(tmp_path, shell, progress):
    repo = _reviewed_spec(
        tmp_path, TASK_STATES[progress], "```yaml\ngate: judge\nverdict: PROCEED\n```\n", analyze_hash="0" * 40
    )

    result = _run(shell, repo)

    assert result["STATE"] == "review-needs-recheck" and result["JUDGE_NEEDS_RECHECK"] is True


@pytest.mark.parametrize("shell", SHELLS)
def test_a_resolved_review_lets_finalization_proceed_once_tasks_are_complete(tmp_path, shell):
    repo = _reviewed_spec(tmp_path, TASK_STATES["all"], "```yaml\ngate: judge\nverdict: PROCEED\n```\n")

    result = _run(shell, repo)

    assert result["STATE"] == "uncommitted-changes"
    assert result["JUDGE_NEEDS_RECHECK"] is False
