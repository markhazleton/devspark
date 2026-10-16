# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Gate-bundle fixtures run through the lifecycle check and both next-context twins.

Each bundle under ``tests/fixtures/stage-evidence`` is committed into a throwaway repository and
read by ``judge.py lifecycle`` plus the PowerShell and Bash ``next-context`` scripts. The twins
must agree with each other on every bundle.

What the unchanged scripts return for each bundle (``judge.py lifecycle`` status and failure
codes, then the ``next-context`` STATE and RECOMMENDED_COMMAND); both twins agree on every row:

* deferred-post-deploy-captured: pass, no failures; ready-for-pr -> /devspark-create-pr.
* deferred-missing-captured-as: fail [closeout-not-complete]; closeout-not-complete -> /devspark-implement.
* mandatory-failure-deferral-attempt: fail [verify-not-passed, closeout-not-complete];
  implementation-needs-verification -> /devspark-verify.
* pre-merge-needs-deployment: fail [verify-not-passed, closeout-not-complete];
  implementation-needs-verification -> /devspark-verify.
* high-risk-missing-accepted-by: fail [closeout-not-complete]; closeout-not-complete -> /devspark-implement.
* legacy-no-stage: pass, no failures; ready-for-pr -> /devspark-create-pr.

The scripts read only each required mode's ``status`` and the closeout ``decision``. They never
read ``stage``, ``evidence_class``, ``captured_as`` or ``accepted_by``, so the blocking outcomes
above come from the decision the closeout author recorded. No script change is required to keep
these outcomes. The rules that decide *which* decision is correct live in the contract text, so
the checks that need that text are strict expected failures until it is written.
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


ROOT = Path(__file__).resolve().parent.parent
BUNDLES = ROOT / "tests" / "fixtures" / "stage-evidence"
JUDGE = ROOT / "scripts" / "judge.py"
PS_SCRIPT = ROOT / "scripts" / "powershell" / "next-context.ps1"
SH_SCRIPT = ROOT / "scripts" / "bash" / "next-context.sh"
GIT_BASH = Path(r"C:\Program Files\Git\bin\bash.exe")
FEATURE = "001-demo"

READY = ("pass", [], "ready-for-pr", "/devspark-create-pr")
CLOSEOUT_OPEN = ("fail", ["closeout-not-complete"], "closeout-not-complete", "/devspark-implement")
PROOF_OPEN = (
    "fail",
    ["verify-not-passed", "closeout-not-complete"],
    "implementation-needs-verification",
    "/devspark-verify",
)

EXPECTED = {
    "deferred-post-deploy-captured": READY,
    "deferred-missing-captured-as": CLOSEOUT_OPEN,
    "mandatory-failure-deferral-attempt": PROOF_OPEN,
    "pre-merge-needs-deployment": PROOF_OPEN,
    "high-risk-missing-accepted-by": CLOSEOUT_OPEN,
    "legacy-no-stage": READY,
}


def _bash() -> str | None:
    if os.name == "nt":
        return str(GIT_BASH) if GIT_BASH.exists() and shutil.which("jq") else None
    return shutil.which("bash") if shutil.which("jq") else None


SHELLS = [
    pytest.param("pwsh", marks=pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh not available")),
    pytest.param("bash", marks=pytest.mark.skipif(_bash() is None, reason="bash with jq not available")),
]

# Verdicts are cached per process; one worker keeps each bundle evaluated once.
pytestmark = pytest.mark.xdist_group("stage-evidence")


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, timeout=60, stdin=subprocess.DEVNULL)


def _repo(tmp_path: Path, bundle: str) -> Path:
    repo = tmp_path / "r"
    (repo / ".knowledge" / "governance").mkdir(parents=True)
    (repo / ".knowledge" / "governance" / "constitution.md").write_text("# C\n", encoding="utf-8")
    feature = repo / ".devspark.work" / "specs" / FEATURE
    shutil.copytree(BUNDLES / bundle, feature)
    _git(repo, "init", "-q", "-b", FEATURE)
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "T")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Synthetic bundle")
    return repo


def _lifecycle(repo: Path) -> dict:
    feature = repo / ".devspark.work" / "specs" / FEATURE
    proc = subprocess.run(
        [sys.executable, str(JUDGE), "lifecycle", "--feature-dir", str(feature)],
        cwd=repo, capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL,
    )
    payload = json.loads(proc.stdout)
    assert proc.returncode == (0 if payload["status"] == "pass" else 1), proc.stdout
    return payload


def _next(shell: str, repo: Path) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "DEVSPARK_FEATURE"}
    stubs = repo.parent / "host-stubs"
    stubs.mkdir(exist_ok=True)
    for command in ("gh", "az"):
        (stubs / command).write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        (stubs / command).chmod(0o755)
        (stubs / f"{command}.cmd").write_text("@exit /b 1\n", encoding="utf-8")
    env["PATH"] = str(stubs) + os.pathsep + str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    if shell == "pwsh":
        cmd = ["pwsh", "-NoProfile", "-File", str(PS_SCRIPT), "-Json"]
    else:
        cmd = [_bash(), str(SH_SCRIPT), "--json"]
    proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, timeout=120, stdin=subprocess.DEVNULL, env=env)
    return json.loads(proc.stdout)


def _both_twins(bundle: str) -> tuple[dict, dict, dict]:
    return _outcome(bundle, "lifecycle"), _outcome(bundle, "pwsh"), _outcome(bundle, "bash")


_OUTCOMES: dict[tuple[str, str], dict] = {}
_BUNDLE_REPOS: dict[str, Path] = {}


def _outcome(bundle: str, reader: str) -> dict:
    """The lifecycle or one next-context twin's verdict on a bundle, computed once per run.

    Each verdict is a pure function of the committed bundle, so several contracts that read
    the same verdict share one repository and one invocation.
    """
    key = (bundle, reader)
    if key not in _OUTCOMES:
        if bundle not in _BUNDLE_REPOS:
            base = Path(tempfile.mkdtemp(prefix="stage-evidence-"))
            atexit.register(shutil.rmtree, base, ignore_errors=True)
            _BUNDLE_REPOS[bundle] = _repo(base, bundle)
        repo = _BUNDLE_REPOS[bundle]
        _OUTCOMES[key] = _lifecycle(repo) if reader == "lifecycle" else _next(reader, repo)
    return _OUTCOMES[key]


needs_both = pytest.mark.skipif(
    shutil.which("pwsh") is None or _bash() is None, reason="both next-context twins are required"
)


def _failure_codes(payload: dict) -> list[str]:
    return sorted(str(f.get("code")) for f in payload.get("failures", []))


def test_every_bundle_has_an_expected_outcome():
    on_disk = sorted(p.name for p in BUNDLES.iterdir() if p.is_dir())
    assert on_disk == sorted(EXPECTED)
    for name in on_disk:
        for rel in ("spec.md", "plan.md", "tasks.md", "gates/verify.md", "gates/closeout.md"):
            assert (BUNDLES / name / rel).is_file(), f"{name}/{rel}"


@pytest.mark.parametrize("bundle", sorted(EXPECTED))
@pytest.mark.parametrize("shell", SHELLS)
def test_next_context_and_lifecycle_report_the_recorded_outcome(bundle, shell):
    status, codes, state, command = EXPECTED[bundle]
    lifecycle = _outcome(bundle, "lifecycle")
    assert lifecycle["status"] == status
    assert _failure_codes(lifecycle) == sorted(codes)
    result = _outcome(bundle, shell)
    assert result["STATE"] == state
    assert result["RECOMMENDED_COMMAND"] == command


@needs_both
@pytest.mark.parametrize("bundle", sorted(EXPECTED))
def test_powershell_and_bash_agree_on_every_bundle(bundle):
    _, ps, sh = _both_twins(bundle)
    for key in ("STATE", "RECOMMENDED_COMMAND", "VERIFY_REQUIRED", "VERIFY_PASSED", "CLOSEOUT_DECISION", "TASKS_COMPLETE"):
        assert ps[key] == sh[key], key


@needs_both
def test_a_deferred_post_deploy_item_with_a_durable_record_does_not_block_delivery():
    lifecycle, ps, sh = _both_twins("deferred-post-deploy-captured")
    record = BUNDLES / "deferred-post-deploy-captured" / "tracker-records" / "WI-4821.md"
    assert record.is_file() and "Status: open" in record.read_text(encoding="utf-8")
    assert lifecycle["status"] == "pass"
    assert ps["CLOSEOUT_DECISION"] == sh["CLOSEOUT_DECISION"] == "complete"
    assert ps["STATE"] == sh["STATE"] == "ready-for-pr"

    for name in (
        "mandatory-failure-deferral-attempt",
        "pre-merge-needs-deployment",
        "deferred-missing-captured-as",
        "high-risk-missing-accepted-by",
    ):
        blocked, ps_b, sh_b = _both_twins(name)
        assert blocked["status"] == "fail", name
        assert ps_b["STATE"] == sh_b["STATE"] != "ready-for-pr", name


def test_a_bundle_without_stage_or_evidence_class_keeps_the_old_behavior():
    bundle = BUNDLES / "legacy-no-stage"
    text = "".join(p.read_text(encoding="utf-8") for p in bundle.rglob("*.md"))
    assert "stage:" not in text and "evidence_class" not in text
    assert _outcome("legacy-no-stage", "lifecycle")["status"] == "pass"


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_verification_contract_defines_the_stage_and_evidence_class_vocabulary():
    text = _read("templates/verification-contract.md")
    assert "evidence_class" in text and "post-deploy" in text


def test_closeout_contract_defers_post_deploy_work_only_with_a_durable_record():
    text = _read("templates/closeout-contract.md")
    assert "post-deploy" in text and "captured_as" in text and "evidence_class" in text


def test_closeout_contract_requires_a_named_acceptor_for_high_risk_deferral():
    text = _read("templates/closeout-contract.md")
    assert "high-risk" in text and "post-deploy" in text and "accepted_by" in text


def test_verification_contract_routes_a_premerge_mode_that_needs_deployment_back_to_the_spec():
    text = _read("templates/verification-contract.md").lower()
    assert "authoring defect" in text and "deployed" in text


def test_pull_request_command_states_ready_to_deploy_not_deployed():
    assert "ready to deploy, not deployed" in _read("templates/commands/create-pr.md")
