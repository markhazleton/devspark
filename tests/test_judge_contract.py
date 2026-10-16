# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for Planning Review and the Judge adjudication phase.

Judge consumes child evidence and adjudicates scope. It does not discover and it
does not remediate. These tests pin the deterministic half of that contract
(scripts/judge.py) and the prompt-level surfaces that make the lifecycle honest.
"""

from __future__ import annotations

import importlib.util
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from difflib import unified_diff
from pathlib import Path
from time import perf_counter

import pytest
import yaml


ROOT = Path(__file__).resolve().parent.parent
JUDGE_PY = ROOT / "scripts" / "judge.py"

_spec = importlib.util.spec_from_file_location("devspark_judge", JUDGE_PY)
judge = importlib.util.module_from_spec(_spec)
sys.modules["devspark_judge"] = judge
_spec.loader.exec_module(judge)


# ------------------------------------------------------------------ fixtures


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _write_yaml_gate(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("```yaml\n" + yaml.safe_dump(data, sort_keys=False) + "```\n", encoding="utf-8")


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, timeout=60, stdin=subprocess.DEVNULL)


SPEC145_REPO = Path(os.environ.get("DEVSPARK_SPEC145_REPO", r"C:\FCNFULL\Triage"))
SPEC145_FEATURE = ".devspark.work/specs/145-spec-consolidate-scope-clarifiers"
SPEC145_APPROVED = "f941e34c"
SPEC145_IMPLEMENTED = "cf8d8407"
SPEC145_EXECUTION_PATHS = {"app/clarifier/_telemetry.py", "app/tests/clarifier/test_telemetry.py"}
TASK_START = re.compile(r"^\s*[-*]\s+\[[ xX]\]\s+(T\d{2,4})\b")
BOOKKEEPING_CHECKPOINT = re.compile(r"Phase complete\s+(?:-|\u2014)\s+\d{4}-\d{2}-\d{2}\.?$")


def _spec145_blob(commit: str, relative_path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=SPEC145_REPO,
        capture_output=True,
        timeout=60,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    assert result.returncode == 0, f"missing Spec 145 fixture blob: {commit}:{relative_path}"
    return result.stdout


def _spec145_ready() -> bool:
    return SPEC145_REPO.is_dir() and all(
        subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            cwd=SPEC145_REPO,
            capture_output=True,
            timeout=30,
            stdin=subprocess.DEVNULL,
            check=False,
        ).returncode == 0
        for commit in (SPEC145_APPROVED, SPEC145_IMPLEMENTED)
    )


def _git_blob_digest(content: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(content) + content).hexdigest()


def _spec145_reviewed_blob(relative: str, digest: str) -> bytes:
    try:
        return _spec145_blob(SPEC145_APPROVED, relative)
    except AssertionError:
        object_blob = subprocess.run(
            ["git", "cat-file", "blob", digest],
            cwd=SPEC145_REPO,
            capture_output=True,
            timeout=30,
            stdin=subprocess.DEVNULL,
            check=False,
        )
        if object_blob.returncode == 0 and _git_blob_digest(object_blob.stdout) == digest:
            return object_blob.stdout
        worktree_file = SPEC145_REPO / relative
        if worktree_file.is_file():
            content = worktree_file.read_bytes()
            if _git_blob_digest(content) == digest:
                return content
        pytest.skip(f"approved bytes for Spec 145 reviewed artifact are unavailable: {relative}")


def _install_spec145_approved(repo: Path) -> Path:
    if not _spec145_ready():
        pytest.skip("offline Spec 145 commit evidence is unavailable; set DEVSPARK_SPEC145_REPO")

    feature = repo / SPEC145_FEATURE
    for relative in (
        "spec.md",
        "plan.md",
        "tasks.md",
        "research.md",
        "gates/analyze.md",
        "gates/critic.md",
        "gates/judge.md",
    ):
        destination = feature / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(_spec145_blob(SPEC145_APPROVED, f"{SPEC145_FEATURE}/{relative}"))

    for gate_name in ("analyze", "critic"):
        gate = judge.load_gate(feature / "gates" / f"{gate_name}.md")
        for entry in gate["reviewed_artifacts"]:
            relative = str(entry.get("path") or "")
            path = Path(relative)
            if not relative or path.is_absolute() or ".." in path.parts:
                continue
            if relative in {"spec.md", "plan.md", "tasks.md", "research.md"}:
                continue
            destination = repo / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(_spec145_reviewed_blob(relative, str(entry.get("hash") or "")))
    return feature


@pytest.fixture(scope="session")
def spec145_snapshot(tmp_path_factory) -> Path:
    if not _spec145_ready():
        pytest.skip("offline Spec 145 commit evidence is unavailable; set DEVSPARK_SPEC145_REPO")
    return _install_spec145_approved(tmp_path_factory.mktemp("spec145-approved"))


def _copy_spec145_approved(snapshot_feature: Path, repo: Path) -> Path:
    snapshot_root = snapshot_feature.parents[2]
    feature = repo / SPEC145_FEATURE
    shutil.copytree(snapshot_feature, feature)
    for source in snapshot_root.rglob("*"):
        if not source.is_file() or snapshot_feature in source.parents:
            continue
        relative = source.relative_to(snapshot_root).as_posix()
        destination = repo / Path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if relative in SPEC145_EXECUTION_PATHS:
            shutil.copyfile(source, destination)
        else:
            try:
                destination.hardlink_to(source)
            except OSError:
                shutil.copyfile(source, destination)
    return feature


def _task_blocks(text: str) -> dict[str, tuple[int, int, str]]:
    lines = text.splitlines(keepends=True)
    starts = [(index, match.group(1)) for index, line in enumerate(lines) if (match := TASK_START.match(line))]
    blocks = {}
    for position, (start, task_id) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        blocks[task_id] = (start, end, "".join(lines[start:end]))
    return blocks


def _implementation_bookkeeping_projection(block: str) -> str:
    lines = []
    for line in block.splitlines(keepends=True):
        line = re.sub(r"^(\s*[-*]\s+\[)[xX](\])", r"\1 \2", line)
        line = re.sub(r" <!-- WIP: [^\r\n]* -->(?=\r?\n?$)", "", line)
        if "(code_ref:" in line:
            line = line[:line.index("(code_ref:")].rstrip() + ("\n" if line.endswith("\n") else "")
        if BOOKKEEPING_CHECKPOINT.search(line.rstrip("\r\n")):
            continue
        lines.append(line)
    return "".join(lines)


def _replay_spec145_bookkeeping(approved: str, implemented: str) -> tuple[str, set[str]]:
    approved_blocks = _task_blocks(approved)
    implemented_blocks = _task_blocks(implemented)
    replacements = {}
    for task_id in approved_blocks.keys() & implemented_blocks.keys():
        old = approved_blocks[task_id][2]
        new = implemented_blocks[task_id][2]
        if old != new and _implementation_bookkeeping_projection(old) == _implementation_bookkeeping_projection(new):
            replacements[task_id] = new

    lines = approved.splitlines(keepends=True)
    for task_id, (start, end, _) in sorted(approved_blocks.items(), key=lambda item: item[1][0], reverse=True):
        if task_id in replacements:
            lines[start:end] = replacements[task_id].splitlines(keepends=True)

    checkpoint = next(
        (line for line in implemented.splitlines(keepends=True) if BOOKKEEPING_CHECKPOINT.search(line.rstrip("\r\n"))),
        None,
    )
    if checkpoint:
        original_checkpoint = re.sub(
            r"[ \t]+Phase complete (?:-|\u2014) \d{4}-\d{2}-\d{2}\.?$",
            "",
            checkpoint.rstrip("\r\n"),
        )
        for index, line in enumerate(lines):
            if line.strip() == original_checkpoint.strip():
                lines[index] = checkpoint
                break
        else:
            lines.append("\n" if lines and not lines[-1].endswith("\n") else "")
            lines.append(checkpoint)
    return "".join(lines), set(replacements)


_TEMPLATE_REPO: Path | None = None
_TEMP_ROOT: tempfile.TemporaryDirectory | None = None


def _init_template_repo(root: Path) -> Path:
    feature = root / ".devspark.work" / "specs" / "132-clearstep-catalog-sync"
    feature.mkdir(parents=True)
    (feature / "spec.md").write_text("---\nrequired_gates: checklist, analyze, critic\n---\n# Spec\n", encoding="utf-8")
    (feature / "plan.md").write_text("# Plan\n", encoding="utf-8")
    (feature / "tasks.md").write_text("# Tasks\n\n- [ ] T001 Build the thing (Implements: FR-001)\n", encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test User")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    global _TEMPLATE_REPO, _TEMP_ROOT
    if _TEMPLATE_REPO is None:
        _TEMP_ROOT = tempfile.TemporaryDirectory()
        _TEMPLATE_REPO = Path(_TEMP_ROOT.name) / "repo"
        _TEMPLATE_REPO.mkdir(parents=True, exist_ok=True)
        _init_template_repo(_TEMPLATE_REPO)
    root = tmp_path / "repo"
    shutil.copytree(_TEMPLATE_REPO, root)
    return root


@pytest.fixture
def feature(repo: Path) -> Path:
    return repo / ".devspark.work" / "specs" / "132-clearstep-catalog-sync"


def _reviewed(feature: Path, repo: Path, names=("spec.md", "plan.md", "tasks.md")) -> list[dict]:
    return [{"path": n, "hash": judge.hash_file(feature / n, repo)} for n in names]


def write_child(feature: Path, repo: Path, name: str, findings=(), obligations=(), routed=(), **extra) -> None:
    semantic_hashes = extra.pop("semantic_hashes", False)
    data = {
        "gate": name,
        "status": "pass",
        "blocking": False,
        "reviewed_artifacts": _reviewed(feature, repo),
        "findings": list(findings),
    }
    if semantic_hashes:
        for entry in data["reviewed_artifacts"]:
            entry["semantic_hash"] = judge.semantic_hash(feature / entry["path"])
    if obligations:
        data["verification_obligations"] = list(obligations)
    if routed:
        data["routed_findings"] = list(routed)
    data.update(extra)
    _write_yaml_gate(feature / "gates" / f"{name}.md", data)


def afinding(fid: str, severity: str = "medium", classification: str | None = "deferred-work", **kw) -> dict:
    entry = {"finding_id": fid, "owner": "analyze", "severity": severity, "description": f"{fid} text", "status": "open"}
    if classification:
        entry["classification"] = classification
    entry.update(kw)
    return entry


def cfinding(fid: str, effective: str = "medium", classification: str | None = "deferred-work", **kw) -> dict:
    entry = {
        "finding_id": fid,
        "owner": "critic",
        "category": "scale_bottlenecks",
        "base_severity": effective,
        "effective_severity": effective,
        "description": f"{fid} text",
        "status": "open",
    }
    if classification:
        entry["classification"] = classification
    entry.update(kw)
    return entry


def concern(cid="J-001", sources=("analyze-001",), classification="deferred-work", resolution="accept", **kw) -> dict:
    base = {
        "id": cid,
        "sources": list(sources),
        "classification": classification,
        "classification_source": "child",
        "resolution": resolution,
        "change_shape": "planning",
        "forcing_requirement": [],
        "action": "act on it",
        "route": None,
        "future_work": None,
        "needs_authority": False,
        "classification_change": None,
    }
    if resolution == "accept":
        base["classification"] = kw.pop("classification", "accepted-limitation")
        base["classification_source"] = "judge-inferred"
        base["accepted_by"] = "planning-review"
    base.update(kw)
    return base


def write_judge(feature: Path, repo: Path, concerns=(), decisions=(), routed=(), verdict=None, **extra) -> dict:
    semantic_hashes = extra.pop("semantic_hashes", False)
    children = {}
    for name in ("analyze", "critic"):
        path = feature / "gates" / f"{name}.md"
        children[name] = {
            "artifact": f"gates/{name}.md",
            "hash": judge.hash_file(path, repo) if path.exists() else None,
            "state": "fresh",
            "ran": True,
        }
        if semantic_hashes and path.exists():
            children[name]["semantic_hash"] = judge.semantic_hash(path)
    children["critic"]["applicable"] = True
    children["critic"]["signals"] = ["persistent-data-shape"]
    header = {
        "gate": "judge",
        "devspark_version": "test",
        "generated": "2026-10-03T00:00:00Z",
        "feature": feature.name,
        "objective": "Keep the catalog synchronized safely.",
        "children": children,
        "concerns": list(concerns),
        "decisions_needed": list(decisions),
        "routed_obligations": list(routed),
    }
    header["verdict"] = verdict or judge.derive_verdict(header["concerns"], header["decisions_needed"])
    header.update(extra)
    _write_yaml_gate(feature / "gates" / "judge.md", header)
    return header


def validate(feature: Path, repo: Path) -> dict:
    header, index, superseded = judge.load_judge_context(feature, repo)
    return judge.validate_judge(header, index, superseded)


def codes(result: dict) -> set[str]:
    return {e["code"] for e in result["errors"]}


def run_cli(*args: str, cwd: Path | None = None) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(JUDGE_PY), *args],
        capture_output=True,
        text=True,
        timeout=60,
        stdin=subprocess.DEVNULL,
        cwd=str(cwd) if cwd else None,
    )
    return proc.returncode, json.loads(proc.stdout) if proc.stdout.strip() else {}


# ------------------------------------------------------------- clean / merging


def test_clean_plan_proceeds_without_inventing_concerns(feature, repo):
    write_child(feature, repo, "analyze")
    write_child(feature, repo, "critic")
    write_judge(feature, repo)

    result = validate(feature, repo)

    assert result["errors"] == []
    assert result["derived_verdict"] == "PROCEED"


def test_critic_not_applicable_is_recorded_and_not_a_finding(feature, repo):
    write_child(feature, repo, "analyze", [afinding("analyze-001", "low")])
    header = write_judge(feature, repo, [concern(sources=("analyze-001",))])
    header["children"]["critic"] = {"state": "not-applicable", "ran": False, "applicable": False, "signals": []}
    _write_yaml_gate(feature / "gates" / "judge.md", header)

    result = validate(feature, repo)
    report = judge.build_children_report(feature, repo)

    assert result["errors"] == []
    assert report["children"]["critic"]["state"] == "not-applicable"


def test_duplicate_findings_become_one_concern_with_both_sources(feature, repo):
    write_child(feature, repo, "analyze", [afinding("analyze-006")])
    write_child(feature, repo, "critic", [cfinding("critic-003")])
    merged = concern(
        sources=("analyze-006", "critic-003"),
        merge_basis="deterministic",
        merge_reason="same requirement and same anchor",
        resolution="defer",
        classification="deferred-work",
        future_work={"preserve": True, "type": "enhancement", "title": "Runtime tuning", "reason": "no current requirement"},
    )
    write_judge(feature, repo, [merged])

    assert validate(feature, repo)["errors"] == []

    unexplained = dict(merged)
    unexplained.pop("merge_reason")
    write_judge(feature, repo, [unexplained])
    assert "missing-merge-reason" in codes(validate(feature, repo))


def test_judge_concern_without_sources_is_invalid(feature, repo):
    write_child(feature, repo, "analyze", [afinding("analyze-001")])
    write_child(feature, repo, "critic")
    write_judge(feature, repo, [concern(sources=())])

    assert "empty-sources" in codes(validate(feature, repo))


def test_judge_cannot_invent_a_finding(feature, repo):
    write_child(feature, repo, "analyze", [afinding("analyze-001")])
    write_child(feature, repo, "critic")
    write_judge(feature, repo, [concern(sources=("analyze-001",)), concern(cid="J-002", sources=("judge-new-risk",))])

    assert "unknown-source" in codes(validate(feature, repo))


# ------------------------------------------------------------ anti-laundering


def _blocker_fixture(feature, repo):
    write_child(feature, repo, "analyze", [afinding("analyze-001", "low")])
    write_child(
        feature,
        repo,
        "critic",
        [cfinding("critic-002", "critical", "blocking-defect", category="data_loss_continuity")],
    )


def test_independent_blocker_survives_a_merge(feature, repo):
    _blocker_fixture(feature, repo)
    merged = concern(
        sources=("analyze-001", "critic-002"),
        classification="deferred-work",
        resolution="defer",
        merge_basis="judgment",
        merge_reason="looked related",
        future_work={"preserve": True, "type": "bug", "title": "x", "reason": "y"},
    )
    write_judge(feature, repo, [merged])

    assert {"missing-classification-change"} <= codes(validate(feature, repo))


def test_downgrading_a_significant_finding_requires_authority(feature, repo):
    _blocker_fixture(feature, repo)
    change = {"from": "blocking-defect", "source": "critic-002", "reason": "judge thinks it is fine"}
    base = concern(
        sources=("analyze-001", "critic-002"),
        classification="deferred-work",
        resolution="defer",
        classification_source="judge-inferred",
        merge_basis="judgment",
        merge_reason="related",
        future_work={"preserve": True, "type": "bug", "title": "x", "reason": "y"},
        classification_change=change,
    )
    write_judge(feature, repo, [base])
    assert "unauthorized-downgrade" in codes(validate(feature, repo))

    base["classification_change"] = {**change, "authority": "human"}
    write_judge(feature, repo, [base])
    assert validate(feature, repo)["errors"] == []


def test_a_significant_finding_cannot_be_dropped(feature, repo):
    _blocker_fixture(feature, repo)
    write_judge(feature, repo, [concern(sources=("analyze-001",))])

    assert "undisposed-finding" in codes(validate(feature, repo))


def test_significant_finding_cannot_be_accepted_on_planning_review_authority(feature, repo):
    write_child(feature, repo, "analyze")
    write_child(feature, repo, "critic", [cfinding("critic-001", "high", "accepted-limitation")])
    write_judge(feature, repo, [concern(sources=("critic-001",))])

    assert "significant-acceptance-needs-authority" in codes(validate(feature, repo))


# ------------------------------------------------ machinery / simplification


def test_machinery_is_not_auto_promoted_without_a_forcing_requirement(feature, repo):
    write_child(feature, repo, "analyze")
    write_child(feature, repo, "critic", [cfinding("critic-001", "high", "blocking-defect")])
    machinery = concern(
        sources=("critic-001",),
        classification="blocking-defect",
        resolution="require",
        change_shape="machinery",
        action="add a runtime configuration subsystem",
    )
    write_judge(feature, repo, [machinery])
    assert "machinery-without-forcing-requirement" in codes(validate(feature, repo))

    machinery["forcing_requirement"] = ["FR-027"]
    write_judge(feature, repo, [machinery])
    assert validate(feature, repo)["errors"] == []


def test_blocking_defect_can_be_resolved_by_simplifying(feature, repo):
    write_child(feature, repo, "analyze")
    write_child(feature, repo, "critic", [cfinding("critic-001", "high", "blocking-defect")])
    simplified = concern(sources=("critic-001",), classification="blocking-defect", resolution="simplify", change_shape="planning")
    write_judge(feature, repo, [simplified])

    result = validate(feature, repo)

    assert result["errors"] == []
    assert result["derived_verdict"] == "STOP"


def test_blocking_defect_awaiting_a_human_decision_is_conditional(feature, repo):
    write_child(feature, repo, "analyze")
    write_child(feature, repo, "critic", [cfinding("critic-001", "high", "blocking-defect")])
    pending = concern(
        sources=("critic-001",),
        classification="blocking-defect",
        resolution="simplify",
        needs_authority=True,
    )
    decision = {"id": "D-001", "concerns": ["J-001"], "question": "Remove OBSERVE mode?"}
    write_judge(feature, repo, [pending], [decision])

    result = validate(feature, repo)

    assert result["errors"] == []
    assert result["derived_verdict"] == "CONDITIONAL"


def test_a_blocking_concern_routed_to_a_later_phase_does_not_stop_planning_review(feature, repo):
    write_child(feature, repo, "analyze")
    write_child(feature, repo, "critic", [cfinding("critic-001", "high", "blocking-defect")])
    routed = concern(
        sources=("critic-001",),
        classification="blocking-defect",
        resolution="require",
        route={"owner": "implement", "reason": "already planned as a task"},
    )
    write_judge(feature, repo, [routed])

    result = validate(feature, repo)

    assert result["errors"] == []
    assert result["derived_verdict"] == "PROCEED"
    (feature / "tasks.md").write_text("- [ ] T001 still open\n", encoding="utf-8")
    code, payload = run_cli("lifecycle", "--feature-dir", str(feature))
    assert code == 1 and "incomplete-tasks" in {f["code"] for f in payload["failures"]}


@pytest.mark.parametrize("shape,target,partition", [
    ("planning", None, "plan_revisions"),
    ("machinery", None, "plan_revisions"),
    ("test", "tasks", "task_work"),
    ("documentation", "plan", "plan_revisions"),
    ("code", None, "pending_decisions"),
    ("test", "unknown", "pending_decisions"),
])
def test_remediation_is_partitioned_by_authorized_owner(repo, shape, target, partition):
    item = concern(classification="blocking-defect", resolution="simplify", change_shape=shape)
    if target is not None:
        item["revision_target"] = target
    result = judge.split_dispositions({"concerns": [item]}, repo)
    assert [entry["id"] for entry in result[partition]] == ["J-001"]
    assert sum(len(result[key]) for key in ("plan_revisions", "task_work", "pending_decisions")) == 1
    if partition == "pending_decisions":
        assert result["current_planning_work"] == []


@pytest.mark.parametrize("recorded,changed,stale", [("matching", False, False), ("matching", True, True), ("missing", False, True), ("different", False, True)])
def test_revision_state_tracks_plan_inputs_without_resolving_concerns(feature, repo, recorded, changed, stale):
    plan = feature / "plan.md"
    tasks = feature / "tasks.md"
    if recorded != "missing":
        fingerprint = judge.semantic_hash(plan) if recorded == "matching" else "sem1:" + "0" * 64
        tasks.write_text(f"---\nplan_semantic_hash: {fingerprint}\n---\n" + tasks.read_text(encoding="utf-8"), encoding="utf-8")
    write_child(feature, repo, "analyze", [afinding("analyze-001", "high", "blocking-defect")], semantic_hashes=True)
    write_child(feature, repo, "critic", semantic_hashes=True)
    item = concern(classification="blocking-defect", resolution="simplify")
    write_judge(feature, repo, [item], semantic_hashes=True)
    original = (feature / "gates/judge.md").read_bytes()
    if changed:
        plan.write_text(plan.read_text(encoding="utf-8") + "\n## Design\nRemove unnecessary machinery.\n", encoding="utf-8")
    state = judge.review_state(feature, repo)
    assert state["plan_changed"] is changed
    assert state["tasks_stale"] is stale
    assert state["plan_revision_count"] == 1
    assert state["task_work_count"] == 0
    assert state["verdict"] == "STOP"
    assert (feature / "gates/judge.md").read_bytes() == original


def test_invalid_revision_owner_is_rejected(feature, repo):
    write_child(feature, repo, "analyze", [afinding("analyze-001", "high", "blocking-defect")])
    write_child(feature, repo, "critic")
    item = concern(classification="blocking-defect", resolution="require", revision_target="unknown")
    write_judge(feature, repo, [item])
    assert "bad-revision-target" in codes(validate(feature, repo))


def test_a_declared_verdict_must_match_the_derived_one(feature, repo):
    write_child(feature, repo, "analyze")
    write_child(feature, repo, "critic", [cfinding("critic-001", "high", "blocking-defect")])
    blocked = concern(sources=("critic-001",), classification="blocking-defect", resolution="require")
    write_judge(feature, repo, [blocked], verdict="PROCEED")

    assert "verdict-mismatch" in codes(validate(feature, repo))


def test_non_blocking_concern_enters_current_scope_only_when_promoted(feature, repo):
    write_child(feature, repo, "analyze", [afinding("analyze-001")])
    write_child(feature, repo, "critic")
    promoted = concern(sources=("analyze-001",), classification="deferred-work", resolution="require")
    write_judge(feature, repo, [promoted])
    assert "unpromoted-scope-growth" in codes(validate(feature, repo))

    promoted["promoted_by"] = "mark, 2026-10-03"
    write_judge(feature, repo, [promoted])
    assert "unpromoted-scope-growth" not in codes(validate(feature, repo))


# ---------------------------------------------------- routing / future work


def test_verification_obligation_is_routed_not_deferred_and_not_a_task(feature, repo):
    write_child(
        feature,
        repo,
        "critic",
        obligations=[{"assumption": "real Cosmos honors the ETag", "why_material": "x", "proposed_proof": "verify end-to-end"}],
    )
    write_child(feature, repo, "analyze")
    routed = [{"source": "critic-vo-001", "owner": "verify", "reason": "Requires empirical real-Cosmos validation"}]
    write_judge(feature, repo, routed=routed)

    assert validate(feature, repo)["errors"] == []

    write_judge(feature, repo)
    assert "undisposed-finding" in codes(validate(feature, repo))

    write_judge(feature, repo, routed=routed)
    parts = judge.split_dispositions(judge.load_gate(feature / "gates" / "judge.md")["header"], repo)
    assert parts["current_planning_work"] == []
    assert parts["future_work"] == []
    assert parts["routed_obligations"][0]["owner"] == "verify"


def test_a_routed_concern_cannot_be_deferred(feature, repo):
    write_child(feature, repo, "analyze", [afinding("analyze-001")])
    write_child(feature, repo, "critic")
    dropped = concern(
        sources=("analyze-001",),
        classification="deferred-work",
        resolution="defer",
        route={"owner": "verify", "reason": "needs proof"},
        future_work={"preserve": True, "type": "research", "title": "x", "reason": "y"},
    )
    write_judge(feature, repo, [dropped])

    assert "routed-but-dropped" in codes(validate(feature, repo))


def test_future_work_is_a_disposition_not_a_current_task(feature, repo):
    write_child(feature, repo, "analyze", [afinding("analyze-001")])
    write_child(feature, repo, "critic")
    deferred = concern(
        sources=("analyze-001",),
        classification="deferred-work",
        resolution="defer",
        future_work={"preserve": True, "type": "enhancement", "title": "Bulk change review", "reason": "not required now"},
    )
    write_judge(feature, repo, [deferred])
    assert validate(feature, repo)["errors"] == []

    code, payload = run_cli("remediation", "--feature-dir", str(feature))
    assert code == 0
    assert payload["current_planning_work"] == []
    assert [f["id"] for f in payload["future_work"]] == ["J-001"]

    missing = dict(deferred)
    missing["future_work"] = None
    write_judge(feature, repo, [missing])
    assert "defer-without-future-work" in codes(validate(feature, repo))


def test_future_work_is_materialized_outside_the_spec_and_is_idempotent(feature, repo):
    write_child(feature, repo, "analyze", [afinding("analyze-001")])
    write_child(feature, repo, "critic")
    deferred = concern(
        sources=("analyze-001",),
        classification="deferred-work",
        resolution="defer",
        future_work={"preserve": True, "type": "enhancement", "title": "Bulk change review", "reason": "not required now"},
    )
    write_judge(feature, repo, [deferred])

    code, payload = run_cli("future-work", "--feature-dir", str(feature), "--write")
    assert code == 0 and len(payload["written"]) == 1
    written = Path(payload["written"][0])
    body = written.read_text(encoding="utf-8")
    assert written.parent == repo / ".devspark.work" / "intake"
    for heading in judge.FUTURE_WORK_SECTIONS:
        assert f"## {heading}" in body
    for forbidden in ("required_gates", "## Tasks", "Acceptance Criteria", "Status"):
        assert forbidden not in body

    code, payload = run_cli("future-work", "--feature-dir", str(feature), "--write")
    assert payload["written"] == [] and len(payload["skipped"]) == 1


def test_accepted_limitation_makes_no_future_work_promise(feature, repo):
    write_child(feature, repo, "analyze", [afinding("analyze-001")])
    write_child(feature, repo, "critic")
    accepted = concern(sources=("analyze-001",))
    write_judge(feature, repo, [accepted])
    assert validate(feature, repo)["errors"] == []

    accepted["future_work"] = {"preserve": True, "type": "bug", "title": "x", "reason": "y"}
    write_judge(feature, repo, [accepted])
    assert "accept-with-future-work" in codes(validate(feature, repo))

    unnamed = concern(sources=("analyze-001",))
    unnamed["accepted_by"] = ""
    write_judge(feature, repo, [unnamed])
    assert "missing-accepted-by" in codes(validate(feature, repo))


# ------------------------------------------------------ semantic freshness


def test_semantic_fixture_metadata_is_opt_in(feature, repo, monkeypatch):
    monkeypatch.setattr(judge, "semantic_hash", lambda path: "sem1:" + path.name, raising=False)
    write_child(feature, repo, "analyze")
    legacy = judge.load_gate(feature / "gates/analyze.md")
    assert all("semantic_hash" not in entry for entry in legacy["reviewed_artifacts"])
    write_child(feature, repo, "critic", semantic_hashes=True)
    current = judge.load_gate(feature / "gates/critic.md")
    assert all(entry["semantic_hash"] == "sem1:" + entry["path"] for entry in current["reviewed_artifacts"])
    header = write_judge(feature, repo, semantic_hashes=True)
    assert header["children"]["analyze"]["semantic_hash"] == "sem1:analyze.md"
    assert header["children"]["critic"]["semantic_hash"] == "sem1:critic.md"


def test_semantic_metadata_producers_preserve_raw_and_legacy_evidence():
    for name in ("analyze", "critic"):
        prompt = _read(f"templates/commands/{name}.md")
        assert "semantic-hash --path" in prompt
        assert "semantic_hash" in prompt
        assert "git hash-object" in prompt
        assert "unavailable" in prompt
    contract = _read("templates/judge-contract.md")
    assert 'semantic_hash: "sem1:<digest>"' in contract
    assert "never add semantic metadata retroactively" in contract.lower()
    assert "bookkeeping-changed" in _read("templates/commands/planning-review.md")
    assert "bookkeeping-changed" in judge.CHILD_STATES


def test_semantic_hash_cli_ignores_only_spec_status(feature, repo):
    path = feature / "spec.md"
    original = "# Spec\n\n**Status**: Draft\n\n## Requirements\nPreserve the approved behavior.\n"
    path.write_text(original, encoding="utf-8")
    returncode, before = run_cli("semantic-hash", "--path", str(path), cwd=repo)
    assert returncode == 0
    assert before["algorithm"] == "sem1"
    assert before["role"] == "spec"
    assert before["semantic_hash"].startswith("sem1:")
    path.write_text(original.replace("Draft", "In Progress"), encoding="utf-8")
    returncode, after = run_cli("semantic-hash", "--path", str(path), cwd=repo)
    assert returncode == 0
    assert after["semantic_hash"] == before["semantic_hash"]
    path.write_text(original.replace("approved behavior", "a different requirement"), encoding="utf-8")
    assert judge.semantic_hash(path) != before["semantic_hash"]


@pytest.mark.parametrize("algorithm,expected", [("sem1", "bookkeeping-changed"), ("sem0", "stale-recheck-required")])
def test_recorded_semantics_handle_status_without_rewriting_gates(feature, repo, algorithm, expected):
    path = feature / "spec.md"
    original = path.read_text(encoding="utf-8") + "\n**Status**: Draft\n"
    path.write_text(original, encoding="utf-8")
    for name in ("analyze", "critic"):
        write_child(feature, repo, name, semantic_hashes=True)
        if algorithm != "sem1":
            gate_path = feature / "gates" / f"{name}.md"
            data = judge.load_gate(gate_path)["header"]
            for entry in data["reviewed_artifacts"]:
                entry["semantic_hash"] = entry["semantic_hash"].replace("sem1:", algorithm + ":")
            _write_yaml_gate(gate_path, data)
    write_judge(feature, repo, semantic_hashes=True)
    gate_bytes = {gate: gate.read_bytes() for gate in (feature / "gates").glob("*.md")}
    before = judge.build_children_report(feature, repo)
    assert all(child["state"] == "fresh" for child in before["children"].values())
    assert validate(feature, repo)["derived_verdict"] == "PROCEED"
    path.write_text(original.replace("Draft", "In Progress"), encoding="utf-8")

    report = judge.build_children_report(feature, repo)

    assert all(child["state"] == expected for child in report["children"].values())
    if expected == "bookkeeping-changed":
        assert all(child["action"] == "none" and not child["blocking"] for child in report["children"].values())
        assert judge.review_state(feature, repo)["needs_recheck"] is False
    assert report["judge"]["state"] == "fresh"
    assert all(gate.read_bytes() == content for gate, content in gate_bytes.items())


@pytest.mark.parametrize("name,addition", [
    ("spec.md", "\n## Requirement\nAdd new behavior.\n"),
    ("plan.md", "\n## Design\nAdd a background worker.\n"),
    ("tasks.md", "\n- [ ] T099 Add new behavior.\n"),
])
def test_recorded_semantics_reject_scope_changes_during_execution(feature, repo, name, addition):
    for child in ("analyze", "critic"):
        write_child(feature, repo, child, semantic_hashes=True)
    write_judge(feature, repo, semantic_hashes=True)
    tasks = feature / "tasks.md"
    tasks.write_text(tasks.read_text(encoding="utf-8").replace("[ ]", "[X]"), encoding="utf-8")
    path = feature / name
    path.write_text(path.read_text(encoding="utf-8") + addition, encoding="utf-8")

    report = judge.build_children_report(feature, repo)

    assert all(child["state"] == "stale-recheck-required" for child in report["children"].values())


def test_spec145_approved_implementation_bookkeeping_preserves_judge_approval(repo, spec145_snapshot):
    feature = _copy_spec145_approved(spec145_snapshot, repo)
    approved_tasks = (feature / "tasks.md").read_text(encoding="utf-8")
    implemented_tasks = _spec145_blob(
        SPEC145_IMPLEMENTED, f"{SPEC145_FEATURE}/tasks.md"
    ).decode("utf-8")
    replayed_tasks, replayed_ids = _replay_spec145_bookkeeping(approved_tasks, implemented_tasks)
    assert replayed_ids
    assert any(len(_task_blocks(implemented_tasks)[task_id][2].splitlines()) > 2 for task_id in replayed_ids)
    assert any(
        re.search(r"knowledge_ref:[^\r\n]*\([^)]*\)", _task_blocks(implemented_tasks)[task_id][2])
        for task_id in replayed_ids
    )

    critic_tasks = next(
        entry for entry in judge.load_gate(feature / "gates/critic.md")["reviewed_artifacts"]
        if entry.get("path") == "tasks.md"
    )
    assert judge.semantic_hash(feature / "tasks.md") == critic_tasks["semantic_hash"]
    approved_projection = judge.semantic_projection(feature / "tasks.md")
    judge_path = feature / "gates/judge.md"
    judge_evidence = judge_path.read_bytes()
    (feature / "tasks.md").write_text(replayed_tasks, encoding="utf-8")
    assert judge.semantic_hash(feature / "tasks.md") == critic_tasks["semantic_hash"], "\n".join(
        list(unified_diff(
            approved_projection.splitlines(),
            judge.semantic_projection(feature / "tasks.md").splitlines(),
        ))[:40]
    )

    report = judge.build_children_report(feature, repo)

    assert all(child["state"] == "bookkeeping-changed" for child in report["children"].values()), report["children"]
    assert judge.review_state(feature, repo)["needs_recheck"] is False
    assert judge_path.read_bytes() == judge_evidence


@pytest.mark.parametrize(
    "artifact,change",
    [
        ("spec.md", "\n## Requirements\nAdd a new externally visible behavior.\n"),
        ("spec.md", "\n## Acceptance Criteria\nThe new behavior completes within a stricter target.\n"),
        ("plan.md", "\n## Architecture Change\nReplace the approved boundary with asynchronous fan-out.\n"),
        ("tasks.md", None),
    ],
    ids=("requirement-change", "acceptance-change", "architecture-change", "task-intent-change"),
)
def test_spec145_genuine_planning_changes_still_require_recheck(repo, spec145_snapshot, artifact, change):
    feature = _copy_spec145_approved(spec145_snapshot, repo)
    path = feature / artifact
    content = path.read_text(encoding="utf-8")
    if change is None:
        assert "- [ ] T001 Run " in content
        content = content.replace("- [ ] T001 Run ", "- [ ] T001 Repeat ", 1)
    else:
        content += change
    path.write_text(content, encoding="utf-8")

    report = judge.build_children_report(feature, repo)

    assert all(child["state"] == "stale-recheck-required" for child in report["children"].values())
    assert judge.review_state(feature, repo)["needs_recheck"] is True


def test_spec145_approved_source_and_test_changes_remain_execution_evidence(repo, spec145_snapshot):
    feature = _copy_spec145_approved(spec145_snapshot, repo)
    changed_paths = tuple(sorted(SPEC145_EXECUTION_PATHS))
    critic = judge.load_gate(feature / "gates/critic.md")
    reviewed_paths = {str(entry.get("path")) for entry in critic["reviewed_artifacts"]}
    assert set(changed_paths) <= reviewed_paths

    implemented_tasks = _spec145_blob(
        SPEC145_IMPLEMENTED, f"{SPEC145_FEATURE}/tasks.md"
    ).decode("utf-8")
    replayed_tasks, _ = _replay_spec145_bookkeeping(
        (feature / "tasks.md").read_text(encoding="utf-8"), implemented_tasks
    )
    (feature / "tasks.md").write_text(replayed_tasks, encoding="utf-8")
    for relative in changed_paths:
        original = repo / relative
        implemented = _spec145_blob(SPEC145_IMPLEMENTED, relative)
        assert original.read_bytes() != implemented
        original.write_bytes(implemented)

    judge_path = feature / "gates/judge.md"
    judge_evidence = judge_path.read_bytes()
    gate_bytes = {name: (feature / f"gates/{name}.md").read_bytes() for name in ("analyze", "critic")}

    report = judge.build_children_report(feature, repo)

    analyze = report["children"]["analyze"]
    assert analyze["state"] in {"bookkeeping-changed", "stale-nonblocking"}
    assert analyze["action"] == "none" and analyze["blocking"] is False
    critic = report["children"]["critic"]
    assert critic["state"] == "stale-nonblocking"
    assert critic["action"] == "none" and critic["blocking"] is False
    assert set(critic["execution_changes"]) == set(changed_paths)
    assert "Verify and PR Review" in " ".join(critic["reasons"])
    assert all(
        item["state"] == "SEMANTICALLY_STALE"
        for item in critic["artifacts"]
        if item["path"] in changed_paths
    )
    assert judge.review_state(feature, repo)["needs_recheck"] is False
    assert judge_path.read_bytes() == judge_evidence
    assert gate_bytes == {
        name: (feature / f"gates/{name}.md").read_bytes() for name in ("analyze", "critic")
    }


def test_spec145_approved_source_and_test_changes_before_first_task_remain_execution_evidence(
    repo, spec145_snapshot
):
    feature = _copy_spec145_approved(spec145_snapshot, repo)
    tasks_before = (feature / "tasks.md").read_bytes()
    assert not re.search(rb"(?m)^-\s*\[[xX]\]", tasks_before)

    changed_paths = tuple(sorted(SPEC145_EXECUTION_PATHS))
    critic = judge.load_gate(feature / "gates/critic.md")
    reviewed_paths = {str(entry.get("path")) for entry in critic["reviewed_artifacts"]}
    assert set(changed_paths) <= reviewed_paths
    for relative in changed_paths:
        source = repo / relative
        original = source.read_bytes()
        implemented = _spec145_blob(SPEC145_IMPLEMENTED, relative)
        assert original != implemented
        source.write_bytes(implemented)

    judge_path = feature / "gates/judge.md"
    judge_evidence = judge_path.read_bytes()
    report = judge.build_children_report(feature, repo)

    critic_result = report["children"]["critic"]
    assert critic_result["state"] == "stale-nonblocking"
    assert critic_result["action"] == "none" and critic_result["blocking"] is False
    assert set(critic_result["execution_changes"]) == set(changed_paths)
    assert "Verify and PR Review" in " ".join(critic_result["reasons"])
    assert (feature / "tasks.md").read_bytes() == tasks_before
    assert judge_path.read_bytes() == judge_evidence
    assert judge.review_state(feature, repo)["needs_recheck"] is False


@pytest.mark.parametrize(
    "case",
    [
        "planned",
        "planned-before-first-task",
        "unexplained",
        "unexplained-before-first-task",
        "governance",
        "governance-before-first-task",
        "assurance-template-before-first-task",
        "assurance-engine-before-first-task",
        "missing",
        "legacy",
    ],
)
def test_execution_evidence_retains_planning_boundaries(feature, repo, case):
    before_first_task = case.endswith("-before-first-task")
    base_case = case.removesuffix("-before-first-task")
    relative = {
        "governance": ".knowledge/governance/rules.md",
        "assurance-template": "templates/commands/critic.md",
        "assurance-engine": "scripts/judge.py",
    }.get(base_case, "scripts/runtime.py")
    source = repo / relative
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("original behavior\n", encoding="utf-8")
    planned = "scripts/different.py" if base_case == "unexplained" else relative
    (feature / "plan.md").write_text(
        "# Plan\n\n```yaml\nexpected_change_surface:\n"
        f"  - path: {planned}\n    change: modify\n    why: approved behavior\n```\n",
        encoding="utf-8",
    )
    for name in ("analyze", "critic"):
        write_child(feature, repo, name, semantic_hashes=case != "legacy")
        gate = feature / "gates" / f"{name}.md"
        data = judge.load_gate(gate)["header"]
        data["reviewed_artifacts"].append({"path": relative, "hash": judge.hash_file(source, repo)})
        _write_yaml_gate(gate, data)
    write_judge(feature, repo, semantic_hashes=case != "legacy")
    tasks = feature / "tasks.md"
    if not before_first_task:
        tasks.write_text(tasks.read_text(encoding="utf-8").replace("[ ]", "[X]"), encoding="utf-8")
    if case == "missing":
        source.unlink()
    else:
        source.write_text("implemented approved behavior\n", encoding="utf-8")

    report = judge.build_children_report(feature, repo)

    for child in report["children"].values():
        if base_case == "planned":
            assert child["state"] == "stale-nonblocking"
            assert child["action"] == "none"
            assert child["execution_changes"] == [relative]
            assert child["blocking"] is False
        elif case == "legacy":
            assert child["action"] == "optional-recheck"
            assert not child.get("execution_changes")
        else:
            assert child["state"] == "stale-recheck-required"


@pytest.mark.parametrize("change,expected", [
    ("outcome", "fresh"), ("producer", "fresh"), ("reopen", "stale"),
    ("unknown-status", "stale"), ("obligation", "stale"), ("classification", "stale"),
])
def test_child_annotations_cannot_hide_reopened_blockers_or_weakened_proof(feature, repo, change, expected):
    write_child(feature, repo, "analyze", semantic_hashes=True)
    write_child(feature, repo, "critic", [cfinding("critic-001", "critical", "blocking-defect", status="resolved")],
                obligations=[{"description": "Prove atomic publication."}], semantic_hashes=True)
    write_judge(feature, repo, routed=[{"source": "critic-vo-001", "owner": "verify"}], semantic_hashes=True)
    path = feature / "gates/critic.md"
    data = judge.load_gate(path)["header"]
    if change == "outcome":
        data["findings"][0]["outcome"] = "The approved regression passes."
    elif change == "producer":
        data["devspark_version"] = "test-new"
    elif change in ("reopen", "unknown-status"):
        data["findings"][0]["status"] = "open" if change == "reopen" else "unknown"
    elif change == "obligation":
        data["verification_obligations"][0]["description"] = "No publication proof required."
    else:
        data["findings"][0]["classification"] = "learning"
    _write_yaml_gate(path, data)

    report = judge.build_children_report(feature, repo)

    assert report["judge"]["state"] == expected
    assert judge.review_state(feature, repo)["needs_recheck"] is (expected == "stale")


def test_malformed_tasks_never_use_the_post_start_exemption(feature, repo):
    for name in ("analyze", "critic"):
        write_child(feature, repo, name, semantic_hashes=True)
    write_judge(feature, repo, semantic_hashes=True)
    (feature / "tasks.md").write_text("---\nbroken: [\n---\n# Tasks\n- [X] T001 Done\n", encoding="utf-8")
    assert all(child["blocking"] for child in judge.build_children_report(feature, repo)["children"].values())


def test_completion_bookkeeping_preserves_review_and_lifecycle(feature, repo):
    spec = feature / "spec.md"
    original = "---\nrequired_gates: analyze, critic, verify:regression-pinned\n---\n# Spec\n\n**Status**: Draft\n"
    spec.write_text(original, encoding="utf-8")
    write_child(feature, repo, "analyze", semantic_hashes=True)
    write_child(feature, repo, "critic", [cfinding("critic-001", "low", "learning", status="resolved")], semantic_hashes=True)
    write_judge(feature, repo, semantic_hashes=True)
    judge_bytes = (feature / "gates/judge.md").read_bytes()
    spec.write_text(original.replace("Draft", "Complete"), encoding="utf-8")
    tasks = feature / "tasks.md"
    tasks.write_text(
        tasks.read_text(encoding="utf-8").replace("[ ]", "[X]").rstrip("\n")
        + " (code_ref: scripts/judge.py | knowledge_ref: n/a)\n\n**Checkpoint**: Phase complete - 2026-10-04.\n",
        encoding="utf-8",
    )
    plan = feature / "plan.md"
    plan.write_text(plan.read_text(encoding="utf-8") + "\n## Implementation Notes\nApproved tests pass.\n", encoding="utf-8")
    critic = feature / "gates/critic.md"
    data = judge.load_gate(critic)["header"]
    data["findings"][0]["outcome"] = "Regression evidence recorded."
    _write_yaml_gate(critic, data)
    _write_yaml_gate(feature / "gates/verify.md", {"gate": "verify", "status": "pass", "modes": [{"mode": "regression-pinned", "status": "pass"}]})
    _write_yaml_gate(feature / "gates/closeout.md", {"gate": "closeout", "decision": "complete"})

    report = judge.build_children_report(feature, repo)

    assert all(child["state"] == "bookkeeping-changed" for child in report["children"].values())
    assert report["judge"]["state"] == "fresh"
    assert judge.review_state(feature, repo)["needs_recheck"] is False
    assert judge.lifecycle_check(feature, repo)["status"] == "pass"
    assert (feature / "gates/judge.md").read_bytes() == judge_bytes


@pytest.mark.parametrize("name,before,after,equal", [
    ("spec.md", "# Spec\n**Status**: Draft\n", "# Spec\n**Status**: Complete\n", True),
    ("spec.md", "# Spec\n## Rule\n**Status**: Draft\n", "# Spec\n## Rule\n**Status**: Complete\n", False),
    ("spec.md", "# Spec\n### User Story 1 - Work (Priority: P1)\n", "# Spec\n### User Story 1 - Work (Priority: P1)\u2705 Complete\n", False),
    ("spec.md", "# Spec\n### User Story 1 - Work (Priority: P1)\n", "# Spec\n### User Story 1 - Work (Priority: P1) \u2705 Complete\n", True),
    ("spec.md", "# Spec\n### User Story 1 — Work (Priority: P1)\n", "# Spec\n### User Story 1 — Work (Priority: P1) \u2705 Complete\n", True),
    ("plan.md", "# Plan\n\n## Design\nKeep one writer.\n", "# Plan\n\n## Design\nKeep one writer.\n\n## Implementation Notes\nTests passed.\n", True),
    ("plan.md", "# Plan\n\n## Design\nKeep one writer.\n", "# Plan\n\n## Design\nAdd a second writer.\n", False),
    ("tasks.md", "# Tasks\n- [ ] T001 Preserve behavior (code_ref: pending | knowledge_ref: pending)\n", "# Tasks\n- [X] T001 Preserve behavior (code_ref: scripts/judge.py | knowledge_ref: n/a)\n", True),
    ("tasks.md", "# Tasks\n- [ ] T001 Preserve behavior\n", "# Tasks\n- [X] T001 Add a worker\n", False),
    ("tasks.md", "# Tasks\n- [ ] T001 Preserve behavior\n", "# Tasks\n- [ ] T001 Preserve behavior Phase complete - 2026-10-04.\n", False),
    ("tasks.md", "# Tasks\n- [ ] T001 Preserve behavior\n", "# Tasks\n- [ ] T001 Preserve behavior\n\n**Checkpoint**: Phase complete - 2026-10-04.\n", True),
    ("spec.md", "---\ndevspark_version: old\nunknown: keep\n---\n# Spec\n", "---\ndevspark_version: new\nunknown: keep\n---\n# Spec\n", True),
    ("spec.md", "---\nunknown: keep\n---\n# Spec\n", "---\nunknown: changed\n---\n# Spec\n", False),
    ("spec.md", "# Spec\n```text\n**Status**: Draft\n```\n", "# Spec\n```text\n**Status**: Complete\n```\n", False),
    ("plan.md", "# Plan\n```text\n  literal\n```\n", "# Plan\n```text\n literal\n```\n", False),
    ("tasks.md", "# Tasks\n- [ ] T001 Preserve behavior\n", "# Tasks\n- [ ] T001 Preserve behavior\n\n## Gate Acknowledgements\nWaive an obligation.\n", False),
])
def test_semantic_projection_preserves_decisions(feature, name, before, after, equal):
    path = feature / name
    path.write_text(before, encoding="utf-8")
    original = judge.semantic_hash(path)
    assert original is not None
    path.write_text(after, encoding="utf-8")
    changed = judge.semantic_hash(path)
    assert changed is not None
    assert (original == changed) is equal


@pytest.mark.parametrize("content", [
    "---\nunknown: [\n---\n# Spec\n",
    "---\nunknown: first\nunknown: second\n---\n# Spec\n",
    "# Spec\n```text\nunclosed literal\n",
])
def test_semantic_projection_unavailable_for_unsafe_input(feature, content):
    path = feature / "spec.md"
    path.write_text(content, encoding="utf-8")
    assert judge.semantic_hash(path) is None


def _remediation_tasks(feature: Path, line: str) -> None:
    tasks = feature / "tasks.md"
    tasks.write_text(tasks.read_text(encoding="utf-8") + "\n## Gate Remediation\n\n" + line + "\n", encoding="utf-8")


def test_fresh_children_need_no_rerun(feature, repo):
    write_child(feature, repo, "analyze", [afinding("analyze-001")])
    write_child(feature, repo, "critic")

    report = judge.build_children_report(feature, repo)

    assert report["children"]["analyze"]["state"] == "fresh"
    assert report["children"]["analyze"]["action"] == "none"


@pytest.mark.parametrize("task_count", [11, 17, 29], ids=["small", "bookkeeping", "medium"])
def test_legacy_status_transition_preserves_raw_freshness_evidence(feature, repo, task_count):
    spec_path = feature / "spec.md"
    original = spec_path.read_text(encoding="utf-8") + "\n**Status**: Draft\n\nPreserve the approved behavior.\n"
    spec_path.write_text(original, encoding="utf-8")
    (feature / "tasks.md").write_text(
        "# Tasks\n\n" + "".join(
            f"- [ ] T{position:03d} Verify approved behavior {position}.\n"
            for position in range(1, task_count + 1)
        ),
        encoding="utf-8",
    )
    write_child(feature, repo, "analyze")
    write_child(feature, repo, "critic")
    write_judge(feature, repo)
    gate_bytes = {path: path.read_bytes() for path in (feature / "gates").glob("*.md")}
    artifacts = [feature / name for name in ("spec.md", "plan.md", "tasks.md")]
    started = perf_counter()
    returncode, before = run_cli("children", "--feature-dir", str(feature), cwd=repo)
    elapsed = perf_counter() - started
    assert returncode == 0
    assert all(child["state"] == "fresh" for child in before["children"].values())
    assert validate(feature, repo)["derived_verdict"] == "PROCEED"

    spec_path.write_text(original.replace("**Status**: Draft", "**Status**: In Progress"), encoding="utf-8")
    after = judge.build_children_report(feature, repo)

    for child in after["children"].values():
        assert child["state"] == "stale-recheck-required"
        assert child["action"] == "rerun"
        assert child["changed"] == ["spec.md"]
    assert after["judge"]["state"] == "fresh"
    assert after["judge"]["verdict"] == "PROCEED"
    assert all(path.read_bytes() == content for path, content in gate_bytes.items())
    print(json.dumps({
        "tasks": task_count,
        "planning_artifacts": len(artifacts),
        "planning_bytes": sum(path.stat().st_size for path in artifacts),
        "planning_lines": sum(len(path.read_text(encoding="utf-8").splitlines()) for path in artifacts),
        "shared_preamble_core_bytes": (ROOT / "templates/command-preamble-contract.md").stat().st_size,
        "children_seconds": round(elapsed, 3),
        "requested_full_child_reruns": sum(child["action"] == "rerun" for child in after["children"].values()),
        "executed_review_rounds": 0,
        "model_passes": None,
        "index_builds": 0,
    }))


@pytest.mark.parametrize("task_count", [11, 17, 29], ids=["small", "bookkeeping", "medium"])
def test_recorded_semantics_remove_the_rerun_across_fixture_sizes(feature, repo, task_count):
    spec_path = feature / "spec.md"
    original = spec_path.read_text(encoding="utf-8") + "\n**Status**: Draft\n\nPreserve the approved behavior.\n"
    spec_path.write_text(original, encoding="utf-8")
    tasks_path = feature / "tasks.md"
    open_tasks = "# Tasks\n\n" + "".join(
        f"- [ ] T{position:03d} Verify approved behavior {position}.\n" for position in range(1, task_count + 1)
    )
    tasks_path.write_text(open_tasks, encoding="utf-8")
    for name in ("analyze", "critic"):
        write_child(feature, repo, name, semantic_hashes=True)
    write_judge(feature, repo, semantic_hashes=True)
    gate_bytes = {path: path.read_bytes() for path in (feature / "gates").glob("*.md")}

    # The Spec 134 shape: status, every task checked, notes appended, all after PROCEED.
    spec_path.write_text(original.replace("**Status**: Draft", "**Status**: Complete"), encoding="utf-8")
    tasks_path.write_text(open_tasks.replace("[ ]", "[X]"), encoding="utf-8")
    plan_path = feature / "plan.md"
    plan_path.write_text(plan_path.read_text(encoding="utf-8") + "\n## Implementation Notes\nAll tasks verified.\n", encoding="utf-8")
    started = perf_counter()
    after = judge.build_children_report(feature, repo)
    elapsed = perf_counter() - started

    assert all(child["state"] == "bookkeeping-changed" for child in after["children"].values())
    assert sum(child["action"] == "rerun" for child in after["children"].values()) == 0
    assert after["judge"]["state"] == "fresh" and judge.review_state(feature, repo)["needs_recheck"] is False
    assert all(path.read_bytes() == content for path, content in gate_bytes.items())

    # The control: a task definition added afterwards is a real scope change.
    tasks_path.write_text(tasks_path.read_text(encoding="utf-8") + "- [ ] T999 Add a brand new behavior.\n", encoding="utf-8")
    stale = judge.build_children_report(feature, repo)
    assert all(child["state"] == "stale-recheck-required" for child in stale["children"].values())
    print(json.dumps({
        "tasks": task_count,
        "requested_full_child_reruns": 0,
        "children_seconds": round(elapsed, 3),
        "executed_review_rounds": 0,
        "model_passes": None,
        "index_builds": 0,
    }))


def test_bounded_remediation_does_not_force_a_full_rerun(feature, repo):
    write_child(feature, repo, "analyze", [afinding("analyze-001", "high", "blocking-defect")])
    write_child(feature, repo, "critic")
    fix = concern(sources=("analyze-001",), classification="blocking-defect", resolution="require", change_shape="documentation")
    write_judge(feature, repo, [fix])
    _remediation_tasks(feature, "- [ ] T050 Correct the wording in plan.md (resolves: analyze-001) (code_ref: pending)")

    child = judge.build_children_report(feature, repo)["children"]["analyze"]

    assert child["state"] == "stale-nonblocking"
    assert child["blocking"] is False
    assert child["action"] == "optional-recheck"


def test_material_architectural_change_requires_a_critic_recheck(feature, repo):
    write_child(feature, repo, "analyze", [afinding("analyze-001", "high", "blocking-defect")])
    write_child(feature, repo, "critic", [cfinding("critic-001", "high", "blocking-defect")])
    fix = concern(sources=("critic-001",), classification="blocking-defect", resolution="require", change_shape="planning")
    write_judge(feature, repo, [fix, concern(cid="J-002", sources=("analyze-001",), classification="blocking-defect", resolution="require")])
    _remediation_tasks(feature, "- [ ] T060 Add a persistence table and status field for claims (resolves: critic-001) (code_ref: pending)")

    children = judge.build_children_report(feature, repo)["children"]

    assert children["critic"]["state"] == "stale-recheck-required"
    assert children["critic"]["action"] == "recheck"
    assert children["critic"]["blocking"] is True
    assert "persist" in children["critic"]["mechanism_signals"]


def test_a_changed_spec_requires_rerun(feature, repo):
    write_child(feature, repo, "analyze", [afinding("analyze-001")])
    write_child(feature, repo, "critic")
    (feature / "spec.md").write_text("# Spec\nA requirement changed.\n", encoding="utf-8")

    child = judge.build_children_report(feature, repo)["children"]["analyze"]

    assert child["state"] == "stale-recheck-required"
    assert child["action"] == "rerun"


def test_superseded_gate_does_not_block_current_work(feature, repo):
    write_child(feature, repo, "analyze")
    write_child(feature, repo, "critic", [cfinding("critic-001", "critical", "blocking-defect")])
    (feature / "plan.md").write_text("# Plan\nThe mechanism was removed.\n", encoding="utf-8")
    header = write_judge(feature, repo)
    header["children"]["critic"]["state"] = "superseded"
    _write_yaml_gate(feature / "gates" / "judge.md", header)

    report = judge.build_children_report(feature, repo)
    assert report["children"]["critic"]["state"] == "superseded"
    assert report["children"]["critic"]["blocking"] is False
    assert validate(feature, repo)["errors"] == []

    write_child(feature, repo, "critic", [cfinding("critic-009", "critical", "blocking-defect")])
    assert judge.build_children_report(feature, repo)["children"]["critic"]["state"] != "superseded"


def test_staleness_alone_is_not_blocking_during_implementation(feature, repo):
    write_child(feature, repo, "analyze", [afinding("analyze-001", "high", "blocking-defect")])
    write_child(feature, repo, "critic")
    tasks = feature / "tasks.md"
    tasks.write_text(tasks.read_text(encoding="utf-8").replace("- [ ] T001", "- [x] T001"), encoding="utf-8")

    child = judge.build_children_report(feature, repo)["children"]["analyze"]

    assert child["state"] == "stale-nonblocking"
    assert child["blocking"] is False


def test_ratchet_detection_is_advisory_and_never_changes_the_verdict(feature, repo):
    write_child(
        feature,
        repo,
        "analyze",
        [
            afinding("analyze-001", "medium", "deferred-work"),
            afinding("analyze-002", "medium", "deferred-work", location="tasks.md#T050"),
            afinding("analyze-003", "medium", "deferred-work", location="tasks.md#T051"),
        ],
    )
    write_child(feature, repo, "critic")
    _remediation_tasks(feature, "- [ ] T050 first fix (resolves: analyze-001)\n- [ ] T051 second fix (resolves: analyze-002)")

    report = judge.build_children_report(feature, repo)
    depths = {c["finding"]: c["chain_depth"] for c in report["ratchet_candidates"]}

    assert depths == {"analyze-002": 1, "analyze-003": 2}
    assert "remediation-on-remediation" in [c for c in report["ratchet_candidates"] if c["finding"] == "analyze-003"][0]["advisory"]


# ------------------------------------------------------------- compatibility


def test_legacy_artifacts_without_classification_stay_readable(feature, repo):
    legacy = {
        "gate": "analyze",
        "status": "pass",
        "reviewed_artifacts": _reviewed(feature, repo),
        "findings": [
            {"finding_id": "analyze-001", "severity": "critical", "summary": "old shape", "status": "open"},
            {"finding_id": "analyze-002", "severity": "low", "summary": "old shape", "status": "resolved"},
        ],
    }
    _write_yaml_gate(feature / "gates" / "analyze.md", legacy)

    records = {r["source_id"]: r for r in judge.normalize_gate("analyze", judge.load_gate(feature / "gates" / "analyze.md"))}

    assert records["analyze-001"]["classification"] == "blocking-defect"
    assert records["analyze-001"]["classification_source"] == "judge-inferred"
    assert records["analyze-002"]["open"] is False


def test_front_matter_gate_artifacts_are_readable(feature):
    path = feature / "gates" / "verify.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\ngate: verify\nstatus: pass\n---\n\n# Verify\n\nbody: not yaml\n", encoding="utf-8")

    header = judge.load_gate(path)["header"]

    assert header["gate"] == "verify" and header["status"] == "pass"


def test_child_supplied_classification_is_recorded_as_child(feature, repo):
    write_child(feature, repo, "critic", [cfinding("critic-001", "critical", "accepted-limitation")])

    record = judge.normalize_gate("critic", judge.load_gate(feature / "gates" / "critic.md"))[0]

    assert record["classification"] == "accepted-limitation"
    assert record["classification_source"] == "child"


def test_real_legacy_gate_in_this_repo_parses_when_present():
    gate = ROOT / ".devspark.work" / "specs" / "001-spec-azdo-work-tracking" / "gates" / "analyze.md"
    if not gate.exists():
        pytest.skip("legacy dogfood artifact not present")
    records = judge.normalize_gate("analyze", judge.load_gate(gate))
    assert records, "a legacy gate must normalize to at least one finding"
    assert all(r["classification"] in judge.CLASSIFICATIONS for r in records)


# --------------------------------------------------- feature resolution once


def test_branch_name_differs_from_spec_folder_resolves_once_by_prefix(repo):
    code, payload = run_cli("resolve", "--repo-root", str(repo), "--branch", "132-sync-work")

    assert code == 0
    assert payload["feature"] == "132-clearstep-catalog-sync"
    assert payload["handoff"]["DEVSPARK_FEATURE"] == "132-clearstep-catalog-sync"
    assert payload["handoff"]["FEATURE_DIR"].endswith("132-clearstep-catalog-sync")


def test_ambiguous_or_unknown_feature_fails_instead_of_guessing(repo):
    other = repo / ".devspark.work" / "specs" / "132-another"
    other.mkdir()
    (other / "spec.md").write_text("# Other\n", encoding="utf-8")

    code, payload = run_cli("resolve", "--repo-root", str(repo), "--branch", "132-sync-work")
    assert code == 1 and payload["status"] == "error"

    code, payload = run_cli("resolve", "--repo-root", str(repo), "--branch", "main")
    assert code == 1


def test_explicit_feature_dir_wins_over_the_branch(repo):
    explicit = repo / ".devspark.work" / "specs" / "132-clearstep-catalog-sync"
    code, payload = run_cli("resolve", "--repo-root", str(repo), "--feature-dir", str(explicit), "--branch", "999-unrelated")

    assert code == 0 and payload["feature"] == explicit.name


def test_children_are_told_to_use_the_resolved_feature_instead_of_guessing():
    planning = _read("templates/commands/planning-review.md")
    assert "DEVSPARK_FEATURE" in planning and "FEATURE_DIR" in planning
    for child in ("analyze", "critic"):
        body = _read(f"templates/commands/{child}.md")
        assert "Planning Review hand-off" in body, f"{child}.md must honor a resolved hand-off"
        assert "do not re-resolve" in body.lower()


# -------------------------------------------------------- read-only authority


def test_judge_guard_allows_only_the_judge_artifact_to_change(feature, repo):
    write_child(feature, repo, "analyze")
    write_child(feature, repo, "critic")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "gates")

    assert run_cli("guard", "begin", "--feature-dir", str(feature))[0] == 0
    write_judge(feature, repo)
    code, payload = run_cli("guard", "end", "--feature-dir", str(feature))
    assert code == 0 and payload["status"] == "ok"


@pytest.mark.parametrize("target", ["spec.md", "plan.md", "tasks.md", "gates/analyze.md", "gates/critic.md"])
def test_judge_guard_detects_a_modified_planning_artifact(feature, repo, target):
    write_child(feature, repo, "analyze")
    write_child(feature, repo, "critic")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "gates")

    run_cli("guard", "begin", "--feature-dir", str(feature))
    path = feature / target
    path.write_text(path.read_text(encoding="utf-8") + "\nsneaky edit\n", encoding="utf-8")
    code, payload = run_cli("guard", "end", "--feature-dir", str(feature))

    assert code == 1 and payload["status"] == "violated"
    assert any(target in m for m in payload["modified"])


def test_changes_outside_the_planning_bundle_are_not_attributed_to_judge(feature, repo):
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "more")

    run_cli("guard", "begin", "--feature-dir", str(feature))
    (repo / "src" / "app.py").write_text("x = 2\n", encoding="utf-8")
    code, payload = run_cli("guard", "end", "--feature-dir", str(feature))
    assert code == 0 and payload["status"] == "concurrent-change-detected"
    assert "src/app.py" in payload["unattributed"]

    run_cli("guard", "begin", "--feature-dir", str(feature))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "someone committed")
    code, payload = run_cli("guard", "end", "--feature-dir", str(feature))
    assert code == 0 and payload["status"] == "concurrent-change-detected"
    assert "<HEAD moved>" in payload["unattributed"]


def test_a_protected_change_is_still_a_violation_amid_unrelated_concurrent_work(feature, repo):
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "more")

    run_cli("guard", "begin", "--feature-dir", str(feature))
    (repo / "src" / "app.py").write_text("x = 2\n", encoding="utf-8")
    (feature / "plan.md").write_text("# Plan\nedited\n", encoding="utf-8")
    code, payload = run_cli("guard", "end", "--feature-dir", str(feature))

    assert code == 1 and payload["status"] == "violated"
    assert any("plan.md" in m for m in payload["modified"])
    assert not any("app.py" in m for m in payload["modified"])



# ----------------------------------------------------- Create PR / lifecycle


def test_lifecycle_requires_all_spec_work_to_be_complete(feature, repo):
    write_child(feature, repo, "analyze")
    write_child(feature, repo, "critic")
    write_judge(feature, repo)

    code, payload = run_cli("lifecycle", "--feature-dir", str(feature))
    assert code == 1
    assert "incomplete-tasks" in {f["code"] for f in payload["failures"]}

    tasks = feature / "tasks.md"
    tasks.write_text(tasks.read_text(encoding="utf-8").replace("- [ ] T001", "- [x] T001"), encoding="utf-8")
    code, payload = run_cli("lifecycle", "--feature-dir", str(feature))
    assert code == 0, payload


def test_lifecycle_blocks_unhandled_routed_obligations_and_uncaptured_future_work(feature, repo):
    tasks = feature / "tasks.md"
    tasks.write_text("- [x] T001 done\n", encoding="utf-8")
    write_child(feature, repo, "analyze", [afinding("analyze-001")])
    write_child(
        feature,
        repo,
        "critic",
        obligations=[{"assumption": "a", "why_material": "b", "proposed_proof": "c"}],
    )
    deferred = concern(
        sources=("analyze-001",),
        classification="deferred-work",
        resolution="defer",
        future_work={"preserve": True, "type": "enhancement", "title": "Later", "reason": "not now"},
    )
    routed = [{"source": "critic-vo-001", "owner": "verify", "reason": "needs real validation"}]
    write_judge(feature, repo, [deferred], routed=routed)

    code, payload = run_cli("lifecycle", "--feature-dir", str(feature))
    failed = {f["code"] for f in payload["failures"]}
    assert code == 1
    assert {"future-work-not-captured", "routed-verify-incomplete"} <= failed

    assert run_cli("future-work", "--feature-dir", str(feature), "--write")[0] == 0
    _write_yaml_gate(feature / "gates" / "verify.md", {"gate": "verify", "status": "pass"})
    code, payload = run_cli("lifecycle", "--feature-dir", str(feature))
    assert code == 0, payload


def test_lifecycle_passes_once_the_planning_bundle_is_finalized(feature, repo):
    shutil.rmtree(feature)

    code, payload = run_cli("lifecycle", "--feature-dir", str(feature))

    assert code == 0 and payload["note"] == "planning bundle already finalized"


def test_lifecycle_defers_pr_review_obligations_to_the_later_phase(feature, repo):
    (feature / "tasks.md").write_text("- [x] T001 done\n", encoding="utf-8")
    write_child(feature, repo, "analyze")
    write_child(feature, repo, "critic", obligations=[{"assumption": "a", "why_material": "b", "proposed_proof": "c"}])
    write_judge(feature, repo, routed=[{"source": "critic-vo-001", "owner": "pr-review", "reason": "diff-level"}])

    code, payload = run_cli("lifecycle", "--feature-dir", str(feature))

    assert code == 0, payload
    assert payload["pending_later_phase"][0]["owner"] == "pr-review"


# ------------------------------------------------ prompt / documentation surfaces


def test_planning_review_is_a_wired_command_with_both_script_twins():
    command = _read("templates/commands/planning-review.md")
    for phrase in (
        "Analyze and Critic discover. Judge adjudicates scope.",
        "Judge does not discover.",
        "Judge does not remediate.",
        "judge-contract.md",
        "--judge-only",
        "guard begin",
        "guard end",
    ):
        assert phrase in command, f"planning-review.md missing {phrase!r}"
    for rel in (
        ".github/skills/devspark-planning-review/SKILL.md",
        "templates/consumer-skills/devspark-planning-review/SKILL.md",
    ):
        assert (ROOT / rel).exists(), f"{rel} must exist"
    assert "judge.py" in _read("scripts/bash/judge.sh")
    assert "judge.py" in _read("scripts/powershell/judge.ps1")


def test_judge_contract_states_its_boundary_and_vocabularies():
    contract = _read("templates/judge-contract.md")
    for phrase in (
        "Judge does not discover.",
        "Judge does not remediate.",
        "A finding is evidence, not automatically work.",
        "Severity, convergence classification, and remediation choice are different concepts.",
        "Staleness is not blocking by itself.",
        "DEFER is a disposition, not a task status.",
        "One decision by one owner resolves all of them.",
        "classification_source",
        "classification_change",
        "change_shape",
        "stale-recheck-required",
        "superseded",
    ):
        assert phrase in contract, f"judge-contract.md missing {phrase!r}"
    for classification in judge.CLASSIFICATIONS:
        assert classification in contract
    for resolution in judge.RESOLUTIONS:
        assert f"`{resolution}`" in contract
    for verdict in judge.VERDICTS:
        assert verdict in contract


def test_analyze_emits_the_shared_classification_and_one_id_scheme():
    analyze = _read("templates/commands/analyze.md")
    assert "classification: blocking-defect | accepted-limitation | deferred-work | learning" in analyze
    assert "severity: critical | high | medium | low" in analyze
    assert "| A1  |" not in analyze, "the report table and the machine-readable block must share one id"
    assert "analyze-001" in analyze


def test_critic_populates_root_cause_only_when_supported():
    critic = _read("templates/commands/critic.md")
    assert "root_cause" in critic
    assert "Do not fabricate" in critic


def test_gate_remediation_consumes_judge_dispositions_not_raw_findings():
    tasks = _read("templates/commands/tasks.md")
    assert "judge.py remediation" in tasks
    assert "A finding is evidence, not automatically work." in tasks
    for rule in ("require", "simplify", "accept", "defer"):
        assert f"`{rule}`" in tasks
    assert "judge.py future-work" in tasks and "--write" in tasks


def test_implement_preflight_reads_the_planning_review_and_semantic_freshness():
    implement = _read("templates/commands/implement.md")
    assert "Planning Review" in implement
    assert "judge.py children" in implement
    assert "Staleness is not blocking by itself." in implement
    assert "judge.py lifecycle" in implement


def test_create_pr_states_the_completed_work_invariant():
    create_pr = _read("templates/commands/create-pr.md")
    assert "A pull request represents completed spec work offered for acceptance." in create_pr
    assert "Merge terminates the spec lifecycle." in create_pr
    assert "judge.py lifecycle" in create_pr


def test_discovery_alone_does_not_expand_scope_in_the_shared_contracts():
    for rel in ("templates/assurance-contract.md", "templates/preamble/convergence.md", "templates/closeout-contract.md"):
        text = _read(rel).replace("**", "").replace("> ", "")
        assert "discovery alone does not expand" in text.lower(), rel
    assert "A risk does not prescribe its remediation." in _read("templates/judge-contract.md")


def test_next_surfaces_planning_review_instead_of_analyze_then_critic():
    for rel in ("scripts/bash/next-context.sh", "scripts/powershell/next-context.ps1"):
        text = _read(rel)
        assert "tasks-need-review" in text, rel
        assert "/devspark-planning-review" in text, rel
    nxt = _read("templates/commands/next.md")
    assert "tasks-need-review" in nxt and "planning-review" in nxt


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh not available")
def test_next_context_recommends_one_planning_review_step(tmp_path):
    repo = tmp_path / "r"
    spec = repo / ".devspark.work" / "specs" / "001-demo"
    spec.mkdir(parents=True)
    (spec / "spec.md").write_text(
        "---\nclassification: full-spec\nrequired_gates: checklist, analyze, critic\n---\n# S\n", encoding="utf-8"
    )
    (spec / "plan.md").write_text("# P\n", encoding="utf-8")
    (spec / "tasks.md").write_text("- [ ] T001 a\n", encoding="utf-8")
    gov = repo / ".knowledge" / "governance"
    gov.mkdir(parents=True)
    (gov / "constitution.md").write_text("# C\n", encoding="utf-8")
    _git(repo, "init", "-q", "-b", "001-demo")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "T")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "x")

    script = ROOT / "scripts" / "powershell" / "next-context.ps1"
    proc = subprocess.run(
        ["pwsh", "-NoProfile", "-File", str(script), "-Json"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=120,
        stdin=subprocess.DEVNULL,
    )
    payload = json.loads(proc.stdout)
    assert payload["STATE"] == "tasks-need-review", payload
    assert payload["RECOMMENDED_COMMAND"] == "/devspark-planning-review"

    gates = spec / "gates"
    gates.mkdir()
    (gates / "judge.md").write_text("```yaml\ngate: judge\nverdict: PROCEED\n```\n", encoding="utf-8")
    proc = subprocess.run(
        ["pwsh", "-NoProfile", "-File", str(script), "-Json"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=120,
        stdin=subprocess.DEVNULL,
    )
    assert json.loads(proc.stdout)["STATE"] == "tasks-incomplete"


def test_future_work_template_matches_the_materialized_shape():
    template = _read("templates/future-work-plan-template.md")
    for heading in judge.FUTURE_WORK_SECTIONS:
        assert f"## {heading}" in template
    for forbidden in ("required_gates", "Acceptance Criteria", "## Tasks"):
        assert forbidden not in template
    assert "Capture discovery without converting discovery into scope." in template


def test_lifecycle_documentation_names_planning_review():
    for rel in (".knowledge/governance/devspark-prompt-mapping.md", "site/src/guides/prompt-lifecycle-mapping.md"):
        text = _read(rel)
        assert "planning-review" in text, rel
        assert "Judge does not discover" in text, rel
