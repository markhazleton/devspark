"""Contract tests for the Spec -> Plan and Plan -> Tasks freshness edges.

The state helper reports a tri-state per edge, `next` routes only on `stale`, and
no helper or router writes any planning artifact.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.test_judge_contract import feature, judge, repo, run_cli, write_child, write_judge  # noqa: F401
from tests.test_next_context_resolution_contract import SHELLS, _repo, _run

ZERO_STAMP = "sem1:" + "0" * 64
EDGES = [
    ("plan_spec_state", "plan.md", "spec_semantic_hash", "spec.md"),
    ("tasks_plan_state", "tasks.md", "plan_semantic_hash", "plan.md"),
]
JUDGE_RELATIVE_KEYS = {"spec_changed", "plan_changed", "tasks_changed", "tasks_stale", "judge_stale"}

STAMP_CASES = {
    "current": (lambda field, h: f"{field}: {h}", "current"),
    "stale": (lambda field, h: f"{field}: {ZERO_STAMP}", "stale"),
    "missing-field": (lambda field, h: "other: 1", "unknown"),
    "null": (lambda field, h: f"{field}: null", "unknown"),
    "wrong-type": (lambda field, h: f"{field}: 7", "unknown"),
    "bad-pattern": (lambda field, h: f"{field}: sem1:abc", "unknown"),
    "duplicate-key": (lambda field, h: f"{field}: {h}\n{field}: {h}", "unknown"),
    "unparsable-frontmatter": (lambda field, h: "{{", "unknown"),
    "no-frontmatter": (None, "unknown"),
}


def _snapshot(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file() and ".git" not in p.parts}


def _set_front(path: Path, front: str | None) -> None:
    body = path.read_text(encoding="utf-8")
    path.write_text(body if front is None else f"---\n{front}\n---\n{body}", encoding="utf-8")


def _add_judge(feature: Path, repo: Path) -> None:
    write_child(feature, repo, "analyze", semantic_hashes=True)
    write_child(feature, repo, "critic", semantic_hashes=True)
    write_judge(feature, repo, semantic_hashes=True)


# ------------------------------------------------------------ edge-state helper


@pytest.mark.parametrize("with_judge", [False, True])
@pytest.mark.parametrize("case", sorted(STAMP_CASES))
@pytest.mark.parametrize(("key", "downstream", "field", "upstream"), EDGES)
def test_edge_state_truth_table(feature, repo, key, downstream, field, upstream, case, with_judge):
    build, expected = STAMP_CASES[case]
    current = judge.semantic_hash(feature / upstream)
    _set_front(feature / downstream, build(field, current) if build else None)
    if with_judge:
        _add_judge(feature, repo)
    before = _snapshot(repo)

    state = judge.review_state(feature, repo)

    assert state[key] == expected
    assert _snapshot(repo) == before


@pytest.mark.parametrize(("key", "downstream", "field", "upstream"), EDGES)
def test_edge_state_is_unknown_when_either_file_is_missing(feature, key, downstream, field, upstream):
    stamp = judge.semantic_hash(feature / upstream)
    _set_front(feature / downstream, f"{field}: {stamp}")
    assert judge.edge_state(feature / downstream, field, feature / upstream) == "current"

    (feature / upstream).unlink()
    assert judge.edge_state(feature / downstream, field, feature / upstream) == "unknown"

    (feature / upstream).write_text("# restored\n", encoding="utf-8")
    (feature / downstream).unlink()
    assert judge.edge_state(feature / downstream, field, feature / upstream) == "unknown"


def test_edge_state_is_unknown_when_the_upstream_cannot_be_projected(feature):
    plan = feature / "plan.md"
    _set_front(plan, f"spec_semantic_hash: {judge.semantic_hash(feature / 'spec.md')}")
    (feature / "spec.md").write_text("# Spec\n\n```\nunclosed fence\n", encoding="utf-8")

    assert judge.semantic_hash(feature / "spec.md") is None
    assert judge.edge_state(plan, "spec_semantic_hash", feature / "spec.md") == "unknown"


def test_a_wrong_typed_plan_stamp_makes_the_tasks_edge_unknown(feature):
    tasks = feature / "tasks.md"
    _set_front(tasks, f"plan_semantic_hash: {judge.semantic_hash(feature / 'plan.md')}")
    assert judge.edge_state(tasks, "plan_semantic_hash", feature / "plan.md") == "current"

    _set_front(feature / "plan.md", "spec_semantic_hash: 7")

    assert judge.semantic_hash(feature / "plan.md") is None
    assert judge.edge_state(tasks, "plan_semantic_hash", feature / "plan.md") == "unknown"


def test_the_cli_reports_both_edge_states_for_a_feature_without_a_judge_artifact(feature, repo):
    _set_front(feature / "plan.md", f"spec_semantic_hash: {ZERO_STAMP}")
    before = _snapshot(repo)

    code, payload = run_cli("review-state", "--feature-dir", str(feature))

    assert code == 0
    assert payload["plan_spec_state"] == "stale"
    assert payload["tasks_plan_state"] == "unknown"
    assert _snapshot(repo) == before


# ------------------------------------------------------------- no-Judge payload


def test_the_no_judge_payload_keeps_missing_state_and_no_judge_relative_keys(feature, repo):
    state = judge.review_state(feature, repo)

    assert state["state"] == "missing"
    assert state["needs_recheck"] is False
    assert JUDGE_RELATIVE_KEYS.isdisjoint(state)
    assert {"plan_spec_state", "tasks_plan_state"} <= set(state)


def test_the_judge_payload_keeps_every_existing_key_and_adds_the_edge_states(feature, repo):
    _add_judge(feature, repo)

    state = judge.review_state(feature, repo)

    assert state["state"] == "present"
    assert JUDGE_RELATIVE_KEYS <= set(state)
    assert {"plan_spec_state", "tasks_plan_state"} <= set(state)
    assert state["tasks_stale"] is True  # missing Tasks provenance still counts as stale here


# ---------------------------------------------------------- projection exclusion


@pytest.mark.parametrize("front", [None, f"spec_semantic_hash: sem1:{'a' * 64}", "spec_semantic_hash: null", f"spec_semantic_hash: {ZERO_STAMP}"])
def test_the_plan_projection_ignores_the_spec_stamp(feature, front):
    plan = feature / "plan.md"
    baseline = judge.semantic_hash(plan)
    _set_front(plan, front)

    assert judge.semantic_hash(plan) == baseline


def test_a_wrong_typed_spec_stamp_makes_the_plan_fingerprint_unavailable(feature):
    _set_front(feature / "plan.md", "spec_semantic_hash: [1]")

    assert judge.semantic_hash(feature / "plan.md") is None


def test_a_plan_restamp_changes_no_review_comparison_or_edge_state(feature, repo):
    plan = feature / "plan.md"
    tasks = feature / "tasks.md"
    _set_front(tasks, f"plan_semantic_hash: {judge.semantic_hash(plan)}")
    _add_judge(feature, repo)
    before = judge.review_state(feature, repo)

    _set_front(plan, f"spec_semantic_hash: {judge.semantic_hash(feature / 'spec.md')}")
    after = judge.review_state(feature, repo)

    assert before["tasks_plan_state"] == "current"
    assert after["tasks_plan_state"] == "current"
    assert after["needs_recheck"] is before["needs_recheck"] is False
    assert after["plan_changed"] is before["plan_changed"] is False
    assert after["plan_spec_state"] == "current"
    children = judge.build_children_report(feature, repo)["children"]
    assert {name: info["state"] for name, info in children.items()} == {
        "analyze": "bookkeeping-changed",
        "critic": "bookkeeping-changed",
    }
    assert not any(info.get("blocking") for info in children.values())


def test_a_tasks_restamp_leaves_its_projection_unchanged(feature):
    tasks = feature / "tasks.md"
    _set_front(tasks, f"plan_semantic_hash: {ZERO_STAMP}")
    first = judge.semantic_hash(tasks)

    text = tasks.read_text(encoding="utf-8").replace(ZERO_STAMP, "sem1:" + "b" * 64)
    tasks.write_text(text, encoding="utf-8")

    assert judge.semantic_hash(tasks) == first


# ---------------------------------------------------------------- routing matrix

SPEC = (
    "---\nclassification: full-spec\nrequired_gates: checklist, analyze, critic\n---\n# S\n\n"
    "**Status**: Draft\n\n## Requirements\n\nThe system MUST report one result.\n"
)
SPEC_BOOKKEEPING = SPEC.replace("**Status**: Draft", "**Status**: In Progress")
SPEC_SEMANTIC = SPEC.replace("report one result", "report two results")
SPEC_UNPARSABLE = SPEC + "\n```\nunclosed fence\n"
PLAN_BODY = "# P\n\n## Design\n\nOne mechanism.\n"
PLAN_SEMANTIC = PLAN_BODY.replace("One mechanism", "Two mechanisms")
TASKS_BODY = "- [ ] T001 a\n"
JUDGE_PROCEED = "```yaml\ngate: judge\nverdict: PROCEED\n```\n"
JUDGE_STOP = "```yaml\ngate: judge\nverdict: STOP\n```\n"
JUDGE_CONDITIONAL = "```yaml\ngate: judge\nverdict: CONDITIONAL\n```\n"


def _seed(
    tmp_path: Path,
    *,
    plan: bool = True,
    plan_stamp: str | None = "current",
    spec_after: str | None = None,
    tasks: bool = False,
    tasks_stamp: str | None = "current",
    plan_after: str | None = None,
    spec: str = SPEC,
    judge_text: str | None = None,
    stale_spec_review: bool = False,
) -> Path:
    root = tmp_path / "case"
    root.mkdir()
    repo_root = _repo(root, "132-sync-work", specs=["132-spec-x"])
    feature_dir = repo_root / ".devspark.work" / "specs" / "132-spec-x"
    (feature_dir / "spec.md").write_text(spec, encoding="utf-8")
    plan_path = feature_dir / "plan.md"
    if plan:
        stamp = {"current": judge.semantic_hash(feature_dir / "spec.md"), "stale": ZERO_STAMP}.get(plan_stamp or "", plan_stamp)
        front = f"---\nspec_semantic_hash: {stamp}\n---\n" if plan_stamp is not None else ""
        plan_path.write_text(front + PLAN_BODY, encoding="utf-8")
    if tasks:
        stamp = {"current": judge.semantic_hash(plan_path), "stale": ZERO_STAMP}.get(tasks_stamp or "", tasks_stamp)
        front = f"---\nplan_semantic_hash: {stamp}\n---\n" if tasks_stamp is not None else ""
        (feature_dir / "tasks.md").write_text(front + TASKS_BODY, encoding="utf-8")
    if spec_after is not None:
        (feature_dir / "spec.md").write_text(spec_after, encoding="utf-8")
    if plan_after is not None:
        existing = plan_path.read_text(encoding="utf-8")
        plan_path.write_text(existing.replace(PLAN_BODY, plan_after), encoding="utf-8")
    if judge_text is not None:
        (feature_dir / "gates").mkdir(exist_ok=True)
        (feature_dir / "gates" / "judge.md").write_text(judge_text, encoding="utf-8")
    if stale_spec_review:
        (feature_dir / "gates").mkdir(exist_ok=True)
        (feature_dir / "gates" / "analyze.md").write_text(
            "```yaml\ngate: analyze\nreviewed_artifacts:\n  - path: spec.md\n    hash: \"0000\"\nfindings: []\n```\n",
            encoding="utf-8",
        )
    return repo_root


ROUTES = {
    "no-plan": (dict(plan=False), "spec-needs-plan", "/devspark-plan", "unknown", "unknown"),
    "current-plan-no-tasks": (dict(), "plan-needs-tasks", "/devspark-tasks", "current", "unknown"),
    "unstamped-plan-no-tasks": (dict(plan_stamp=None), "plan-needs-tasks", "/devspark-tasks", "unknown", "unknown"),
    "malformed-plan-stamp": (dict(plan_stamp="not-a-stamp"), "plan-needs-tasks", "/devspark-tasks", "unknown", "unknown"),
    "stale-plan-no-tasks": (dict(spec_after=SPEC_SEMANTIC), "plan-stale-against-spec", "/devspark-plan", "stale", "unknown"),
    "bookkeeping-spec-edit": (dict(spec_after=SPEC_BOOKKEEPING), "plan-needs-tasks", "/devspark-tasks", "current", "unknown"),
    "unparsable-spec": (dict(spec_after=SPEC_UNPARSABLE), "plan-needs-tasks", "/devspark-tasks", "unknown", "unknown"),
    "stale-plan-with-tasks": (
        dict(tasks=True, spec_after=SPEC_SEMANTIC),
        "plan-stale-against-spec",
        "/devspark-plan",
        "stale",
        "current",
    ),
    "stale-tasks": (
        dict(tasks=True, plan_after=PLAN_SEMANTIC),
        "tasks-stale-against-plan",
        "/devspark-tasks",
        "current",
        "stale",
    ),
    "unstamped-tasks": (dict(tasks=True, tasks_stamp=None), "tasks-need-review", "/devspark-planning-review", "current", "unknown"),
    "judge-proceed-stale-plan": (
        dict(tasks=True, spec_after=SPEC_SEMANTIC, judge_text=JUDGE_PROCEED),
        "plan-stale-against-spec",
        "/devspark-plan",
        "stale",
        "current",
    ),
    "judge-proceed-stale-tasks": (
        dict(tasks=True, plan_after=PLAN_SEMANTIC, judge_text=JUDGE_PROCEED),
        "tasks-stale-against-plan",
        "/devspark-tasks",
        "current",
        "stale",
    ),
    "judge-pending-decision": (
        dict(tasks=True, spec_after=SPEC_SEMANTIC, judge_text=JUDGE_CONDITIONAL),
        "review-needs-decision",
        "/devspark-planning-review",
        "stale",
        "current",
    ),
    "judge-proceed-spec-invalidated": (
        dict(tasks=True, spec_after=SPEC_SEMANTIC, judge_text=JUDGE_PROCEED, stale_spec_review=True),
        "review-needs-recheck",
        "/devspark-planning-review",
        "stale",
        "current",
    ),
    "judge-stop-spec-invalidated": (
        dict(tasks=True, spec_after=SPEC_SEMANTIC, judge_text=JUDGE_STOP, stale_spec_review=True),
        "review-needs-recheck",
        "/devspark-planning-review",
        "stale",
        "current",
    ),
    "judge-stop-stale-plan": (
        dict(tasks=True, spec_after=SPEC_SEMANTIC, judge_text=JUDGE_STOP),
        "review-blocked",
        "/devspark-tasks",
        "stale",
        "current",
    ),
}


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("case", sorted(ROUTES))
def test_next_routes_only_on_a_stale_edge_and_identically_in_both_shells(tmp_path, shell, case):
    options, state, command, plan_spec, tasks_plan = ROUTES[case]
    repo_root = _seed(tmp_path, **options)
    before = _snapshot(repo_root)

    result = _run(shell, repo_root)

    assert (result["STATE"], result["RECOMMENDED_COMMAND"]) == (state, command)
    assert (result["PLAN_SPEC_STATE"], result["TASKS_PLAN_STATE"]) == (plan_spec, tasks_plan)
    assert _snapshot(repo_root) == before


# ---------------------------------------------------------------- prompt wording

COMMANDS = Path(__file__).resolve().parent.parent / "templates" / "commands"


def _command(name: str) -> str:
    return " ".join((COMMANDS / f"{name}.md").read_text(encoding="utf-8").split())


def test_plan_states_the_before_and_after_judge_authority_boundary():
    text = _command("plan")
    for phrase in (
        "Before Judge (no `gates/judge.md`) the plan is a draft",
        "After Judge, revise stays Judge-driven in full",
        "only restamps when no content change is required",
        "applies Judge-owned `plan_revisions`",
        "explicit human authority given during that run",
        "never restamp or change Plan-owned content after Judge on stale review evidence",
    ):
        assert phrase in text, phrase


def test_plan_keeps_outcome_labels_out_of_every_artifact():
    text = _command("plan")
    for phrase in ("NO CONTENT CHANGE", "BOUNDED CORRECTION", "SUBSTANTIVE REVISION", "report-only"):
        assert phrase in text, phrase
    assert "never write them to the spec, plan, tasks, any support artifact or any gate artifact" in text


def test_plan_lists_all_ten_stops_and_their_resolution_channels():
    text = _command("plan")
    for number in range(1, 11):
        assert f"({number}) " in text.split("Stop without changing the stamp")[1].split("Every stop names")[0], number
    for channel in ("`/devspark-clarify`", "`/devspark-planning-review`", "`--reset` only when the developer states destructive intent"):
        assert channel in text, channel
    assert "never substitutes for the developer's answer to a Plan stop" in text


def test_plan_stamps_only_the_fingerprint_it_read():
    text = _command("plan")
    assert "never a value recomputed afterward" in text
    assert "never stamp to silence freshness" in text
    assert "If the fingerprint was unavailable, reconcile but do not stamp" in text


def test_plan_template_declares_an_empty_spec_stamp():
    template = (COMMANDS.parent / "plan-template.md").read_text(encoding="utf-8")
    assert "\nspec_semantic_hash: null\n" in template.split("\n---\n")[0] + "\n"


def test_tasks_has_a_restamp_only_outcome_and_reads_what_it_stamps():
    text = _command("tasks")
    assert 'report "Plan \u2192 Tasks: NO CONTENT CHANGE" in this run\'s output only and update just `plan_semantic_hash`' in text
    assert "that restamp never changes the Tasks projection" in text
    assert "never one recomputed afterward" in text


def test_next_documents_both_edge_states_and_that_unknown_never_routes():
    text = _command("next")
    for phrase in ("plan-stale-against-spec", "tasks-stale-against-plan", "`PLAN_SPEC_STATE`", "`TASKS_PLAN_STATE`", "`unknown` never routes"):
        assert phrase in text, phrase


def test_the_prompt_mapping_states_the_support_artifact_limitation():
    mapping = (Path(__file__).resolve().parent.parent / ".knowledge" / "governance" / "devspark-prompt-mapping.md").read_text(encoding="utf-8")
    text = " ".join(mapping.split())
    assert "`plan_semantic_hash` covers only `plan.md`" in text
    assert "Plan support artifacts is not detected by `tasks_plan_state`" in text


# ------------------------------------------------------------------ seeded fixtures

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "planning-edge-freshness"
PLAN_OUTCOMES = {"NO CONTENT CHANGE", "BOUNDED CORRECTION", "SUBSTANTIVE REVISION"}


def _cases(kind: str) -> list[dict]:
    import yaml

    return yaml.safe_load((FIXTURES / kind / "cases.yaml").read_text(encoding="utf-8"))["cases"]


def _apply(text: str, edit: dict, after_heading: str | None = None) -> str:
    if "replace" in edit:
        assert text.count(edit["replace"]) == 1, edit["replace"]
        return text.replace(edit["replace"], edit["with"])
    lines = text.rstrip("\n").split("\n")
    if after_heading is None:
        return "\n".join([*lines, edit["append"]]) + "\n"
    start = lines.index(after_heading)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    while lines[end - 1] == "":
        end -= 1
    return "\n".join([*lines[:end], edit["append"], *lines[end:]]) + "\n"


def _seed_pair(directory: Path, kind: str, upstream: str, downstream: str, field: str) -> tuple[Path, Path]:
    for name in (upstream, downstream):
        (directory / name).write_text((FIXTURES / kind / name).read_text(encoding="utf-8"), encoding="utf-8")
    stamp = judge.semantic_hash(directory / upstream)
    _set_front(directory / downstream, f"{field}: {stamp}")
    return directory / upstream, directory / downstream


@pytest.mark.parametrize("case", _cases("plan"), ids=lambda c: c["id"])
def test_every_plan_case_starts_current_and_becomes_stale_when_the_spec_edit_is_applied(tmp_path, case):
    spec, plan = _seed_pair(tmp_path, "plan", "spec.md", "plan.md", "spec_semantic_hash")
    assert judge.edge_state(plan, "spec_semantic_hash", spec) == "current"

    spec.write_text(_apply(spec.read_text(encoding="utf-8"), case["edit"], case.get("after_heading")), encoding="utf-8")

    assert judge.edge_state(plan, "spec_semantic_hash", spec) == case["plan_spec_state"] == "stale"
    assert case["judge"] in {"absent", "present"}
    assert case["stamp"] in {"updated", "unchanged"}
    if case["outcome"] in PLAN_OUTCOMES:
        assert case["stamp"] == "updated"
    else:
        assert case["outcome"].startswith("stop-") and case["stamp"] == "unchanged"
    if case["outcome"] == "stop-9":
        assert case["judge"] == "present" and case["names"] == "/devspark-planning-review"


@pytest.mark.parametrize("case", _cases("tasks"), ids=lambda c: c["id"])
def test_every_tasks_case_starts_current_and_becomes_stale_when_the_plan_edit_is_applied(tmp_path, case):
    plan, tasks = _seed_pair(tmp_path, "tasks", "plan.md", "tasks.md", "plan_semantic_hash")
    assert judge.edge_state(tasks, "plan_semantic_hash", plan) == "current"
    assert "- [x] T001" in tasks.read_text(encoding="utf-8")

    plan.write_text(_apply(plan.read_text(encoding="utf-8"), case["edit"]), encoding="utf-8")

    assert judge.edge_state(tasks, "plan_semantic_hash", plan) == case["tasks_plan_state"] == "stale"
    assert case["stamp"] in {"updated", "unchanged"}


def test_the_seeded_case_set_covers_the_required_scenarios():
    assert {c["id"] for c in _cases("plan")} == {
        "wording-only",
        "project-addition",
        "constrain-invalidates-mechanism",
        "context-only",
        "conflicting-decisions",
        "judge-present-unreviewed-spec-change",
    }
    assert {c["outcome"] for c in _cases("tasks")} == {"Plan -> Tasks: NO CONTENT CHANGE", "re-projection", "stop-ask-developer"}
