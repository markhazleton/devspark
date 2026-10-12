# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""next-context resolves the active spec by identity, not by exact branch name."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
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


def _repo(tmp_path: Path, branch: str, specs=(), quickfixes=()) -> Path:
    repo = tmp_path / "r"
    (repo / ".knowledge" / "governance").mkdir(parents=True)
    (repo / ".knowledge" / "governance" / "constitution.md").write_text("# C\n", encoding="utf-8")
    for name in specs:
        spec = repo / ".devspark.work" / "specs" / name
        spec.mkdir(parents=True)
        (spec / "spec.md").write_text("---\nclassification: full-spec\n---\n# S\n", encoding="utf-8")
    for name in quickfixes:
        record = repo / ".devspark.work" / "quickfixes" / f"{name}.md"
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text("# QF\n", encoding="utf-8")
    _git(repo, "init", "-q", "-b", branch)
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "T")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "x")
    return repo


def _run(shell: str, repo: Path, feature: str | None = None, pr: bool = False) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "DEVSPARK_FEATURE"}
    host_stubs = repo.parent / "host-stubs"
    host_stubs.mkdir(exist_ok=True)
    for command in ("gh", "az"):
        executable = host_stubs / command
        reply = '{"number":123,"state":"OPEN"}' if pr and command == "gh" else ""
        executable.write_text("#!/bin/sh\n" + (f"printf '%s\\n' '{reply}'\n" if reply else "exit 1\n"), encoding="utf-8")
        executable.chmod(0o755)
        (host_stubs / f"{command}.cmd").write_text(f"@echo {reply}\n@exit /b 0\n" if reply else "@exit /b 1\n", encoding="utf-8")
    # Planning Review state is computed by judge.py, so the shell needs this interpreter.
    env["PATH"] = str(host_stubs) + os.pathsep + str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    if feature:
        env["DEVSPARK_FEATURE"] = feature
    if shell == "pwsh":
        cmd = ["pwsh", "-NoProfile", "-File", str(PS_SCRIPT), "-Json"]
    else:
        cmd = [_bash(), str(SH_SCRIPT), "--json"]
    proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, timeout=120, stdin=subprocess.DEVNULL, env=env)
    return json.loads(proc.stdout)


@pytest.mark.parametrize("shell", SHELLS)
def test_branch_name_exactly_matches_the_spec_directory(tmp_path, shell):
    result = _run(shell, _repo(tmp_path, "001-demo", specs=["001-demo"]))

    assert result["SPEC_EXISTS"] is True and result["SPEC_FEATURE"] == "001-demo"


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
