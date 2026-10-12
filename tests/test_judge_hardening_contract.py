# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Pending human decisions, Planning Review run provenance, lifecycle freshness, and the
Minimum Sufficient Change surfaces (Specify, Plan, Critic, Judge)."""

from __future__ import annotations

import yaml

from .test_judge_contract import (  # noqa: F401  (fixtures are consumed by name)
    ROOT,
    _read,
    _write_yaml_gate,
    afinding,
    cfinding,
    codes,
    concern,
    feature,
    judge,
    repo,
    run_cli,
    validate,
    write_child,
    write_judge,
)

RUN = "pr-20261004T000000Z-aaaaaa"
OTHER = "pr-20261003T000000Z-bbbbbb"
QUESTION = "Is the documented rollback procedure sufficient, or must this spec add a mechanism?"


def _pending(cid="J-001", source="critic-002"):
    return concern(
        cid,
        sources=(source,),
        classification="deferred-work",
        resolution=None,
        needs_authority=True,
        decision={"state": "pending", "question": QUESTION},
    )


def _decision(cid="J-001"):
    return {"id": "D-001", "concerns": [cid], "question": QUESTION}


def _significant_child(feature, repo):
    write_child(feature, repo, "analyze")
    write_child(feature, repo, "critic", [cfinding("critic-002", "high", "deferred-work")])


# ------------------------------------------------------- pending human decision


def test_an_unset_resolution_is_valid_only_while_a_human_decision_is_pending(feature, repo):
    _significant_child(feature, repo)
    write_judge(feature, repo, [_pending()], [_decision()])
    result = validate(feature, repo)
    assert result["errors"] == []
    assert result["derived_verdict"] == "CONDITIONAL"

    not_pending = _pending()
    not_pending["needs_authority"] = False
    write_judge(feature, repo, [not_pending], [])
    assert "unset-resolution" in codes(validate(feature, repo))


def test_a_pending_concern_that_vanishes_from_the_decision_list_is_rejected(feature, repo):
    _significant_child(feature, repo)
    write_judge(feature, repo, [_pending()], [])

    assert "authority-without-decision" in codes(validate(feature, repo))


def test_a_pending_decision_is_not_a_fifth_resolution(feature, repo):
    _significant_child(feature, repo)
    fake = _pending()
    fake["resolution"] = "pending"
    write_judge(feature, repo, [fake], [_decision()])

    assert "bad-resolution" in codes(validate(feature, repo))
    assert "pending" not in judge.RESOLUTIONS


def test_a_pending_decision_creates_no_task_no_future_work_and_is_not_accepted(feature, repo):
    _significant_child(feature, repo)
    header = write_judge(feature, repo, [_pending()], [_decision()])

    parts = judge.split_dispositions(header, repo)

    assert [p["id"] for p in parts["pending_decisions"]] == ["J-001"]
    assert parts["pending_decisions"][0]["question"] == QUESTION
    for bucket in ("current_planning_work", "future_work", "accepted", "routed_obligations"):
        assert parts[bucket] == []
    code, payload = run_cli("remediation", "--feature-dir", str(feature))
    assert code == 0 and payload["pending_decisions"][0]["id"] == "J-001"
    code, payload = run_cli("future-work", "--feature-dir", str(feature), "--write")
    assert payload["written"] == [] and payload["planned"] == []


def test_a_tentative_resolution_on_an_authority_concern_still_does_not_become_work(feature, repo):
    _significant_child(feature, repo)
    tentative = concern(
        sources=("critic-002",),
        classification="blocking-defect",
        resolution="simplify",
        needs_authority=True,
    )
    header = write_judge(feature, repo, [tentative], [_decision()])

    parts = judge.split_dispositions(header, repo)

    assert parts["current_planning_work"] == [] and len(parts["pending_decisions"]) == 1


def test_a_recorded_human_decision_releases_the_concern_to_its_resolution(feature, repo):
    _significant_child(feature, repo)

    required = concern(
        sources=("critic-002",),
        classification="deferred-work",
        resolution="require",
        promoted_by="human",
        decision={"state": "resolved", "question": QUESTION},
    )
    parts = judge.split_dispositions(write_judge(feature, repo, [required]), repo)
    assert validate(feature, repo)["errors"] == []
    assert [c["id"] for c in parts["current_planning_work"]] == ["J-001"] and parts["pending_decisions"] == []

    deferred = concern(
        sources=("critic-002",),
        classification="deferred-work",
        resolution="defer",
        future_work={"preserve": True, "type": "operational", "title": "Rollback tooling", "reason": "not required now"},
    )
    parts = judge.split_dispositions(write_judge(feature, repo, [deferred]), repo)
    assert validate(feature, repo)["errors"] == []
    assert [c["id"] for c in parts["future_work"]] == ["J-001"] and parts["pending_decisions"] == []


def test_a_resolved_decision_may_not_leave_the_resolution_unset(feature, repo):
    _significant_child(feature, repo)
    odd = _pending()
    odd["decision"]["state"] = "resolved"
    write_judge(feature, repo, [odd], [_decision()])

    assert "bad-decision-state" in codes(validate(feature, repo))


def test_lifecycle_refuses_a_pr_while_a_decision_is_pending(feature, repo):
    (feature / "tasks.md").write_text("- [x] T001 done\n", encoding="utf-8")
    _significant_child(feature, repo)
    write_judge(feature, repo, [_pending()], [_decision()])

    code, payload = run_cli("lifecycle", "--feature-dir", str(feature))

    assert code == 1 and "pending-decision" in {f["code"] for f in payload["failures"]}


# --------------------------------------------------------------- run provenance


def _stamp(run_id):
    return {"planning_review": {"run_id": run_id}}


def test_resolve_generates_one_run_id_for_the_hand_off(repo):
    code, payload = run_cli("resolve", "--repo-root", str(repo), "--branch", "132-anything")

    assert code == 0
    assert payload["run_id"].startswith("pr-")
    assert payload["handoff"]["PLANNING_REVIEW_RUN_ID"] == payload["run_id"]


def test_a_child_generated_by_this_run_is_accepted(feature, repo):
    write_child(feature, repo, "analyze", **_stamp(RUN))
    write_child(feature, repo, "critic", **_stamp(RUN))

    code, payload = run_cli("seal", "--feature-dir", str(feature), "--run-id", RUN, "--generated", "analyze,critic")

    assert code == 0 and payload["status"] == "sealed"
    assert {c["mode"] for c in payload["children"].values()} == {"generated"}


def test_a_fresh_child_from_an_earlier_run_is_intentionally_reused(feature, repo):
    write_child(feature, repo, "analyze", **_stamp(OTHER))
    write_child(feature, repo, "critic")

    code, payload = run_cli("seal", "--feature-dir", str(feature), "--run-id", RUN)
    report = judge.build_children_report(feature, repo, RUN)

    assert code == 0 and payload["status"] == "sealed"
    assert payload["children"]["analyze"]["mode"] == "reused"
    assert payload["children"]["analyze"]["artifact_run_id"] == OTHER
    assert payload["children"]["analyze"]["accepted_by_run_id"] == RUN
    assert report["children"]["analyze"]["state"] == "fresh" and report["children"]["analyze"]["mode"] == "reused"


def test_a_child_replaced_by_another_run_after_sealing_is_invalidated(feature, repo):
    write_child(feature, repo, "analyze", **_stamp(RUN))
    assert run_cli("seal", "--feature-dir", str(feature), "--run-id", RUN, "--generated", "analyze")[0] == 0

    write_child(feature, repo, "analyze", [afinding("analyze-001")], **_stamp(OTHER))
    code, payload = run_cli("seal", "--feature-dir", str(feature), "--run-id", RUN)
    assert code == 1 and payload["replaced_after_sealing"] == ["analyze"]

    code, payload = run_cli("guard", "begin", "--feature-dir", str(feature), "--run-id", RUN)
    assert code == 1 and payload["status"] == "invalidated"


def test_a_child_whose_hash_changes_unexpectedly_is_not_silently_consumed(feature, repo):
    write_child(feature, repo, "analyze", **_stamp(RUN))
    run_cli("seal", "--feature-dir", str(feature), "--run-id", RUN, "--generated", "analyze")

    path = feature / "gates" / "analyze.md"
    path.write_text(path.read_text(encoding="utf-8") + "\n<!-- edited -->\n", encoding="utf-8")
    code, payload = run_cli("guard", "begin", "--feature-dir", str(feature), "--run-id", RUN)

    assert code == 1 and payload["replaced_after_sealing"] == ["analyze"]


def test_a_child_claimed_as_generated_must_carry_this_runs_id(feature, repo):
    write_child(feature, repo, "analyze", **_stamp(OTHER))

    code, payload = run_cli("seal", "--feature-dir", str(feature), "--run-id", RUN, "--generated", "analyze")

    assert code == 1 and payload["not_stamped_with_this_run"] == ["analyze"]


def test_guard_requires_a_seal_when_a_run_id_is_given(feature, repo):
    write_child(feature, repo, "analyze", **_stamp(RUN))

    code, payload = run_cli("guard", "begin", "--feature-dir", str(feature), "--run-id", RUN)

    assert code == 1 and payload["status"] == "error"


def test_the_full_sealed_run_arms_and_disarms_the_guard(feature, repo):
    write_child(feature, repo, "analyze", **_stamp(RUN))
    write_child(feature, repo, "critic", **_stamp(RUN))
    run_cli("seal", "--feature-dir", str(feature), "--run-id", RUN, "--generated", "analyze,critic")

    assert run_cli("guard", "begin", "--feature-dir", str(feature), "--run-id", RUN)[0] == 0
    write_judge(feature, repo, planning_review={"run_id": RUN})
    code, payload = run_cli("guard", "end", "--feature-dir", str(feature), "--run-id", RUN)

    assert code == 0 and payload["status"] == "ok"


def _provenance_judge(feature, repo, analyze, critic):
    write_child(feature, repo, "analyze", **_stamp(RUN))
    write_child(feature, repo, "critic", **_stamp(RUN))
    header = write_judge(feature, repo, planning_review={"run_id": RUN})
    header["children"]["analyze"].update(analyze)
    header["children"]["critic"].update(critic)
    _write_yaml_gate(feature / "gates" / "judge.md", header)
    hdr, index, superseded = judge.load_judge_context(feature, repo)
    return judge.validate_judge(hdr, index, superseded, judge.child_run_ids(feature))


def test_judge_validates_the_recorded_provenance_against_the_artifacts(feature, repo):
    generated = {"mode": "generated", "run_id": RUN}
    assert _provenance_judge(feature, repo, generated, generated)["errors"] == []

    wrong = {"mode": "generated", "run_id": OTHER}
    assert "provenance-mismatch" in codes(_provenance_judge(feature, repo, wrong, generated))

    reused_wrongly = {"mode": "reused", "artifact_run_id": OTHER, "accepted_by_run_id": RUN}
    assert "provenance-mismatch" in codes(_provenance_judge(feature, repo, reused_wrongly, generated))

    assert "bad-child-provenance" in codes(_provenance_judge(feature, repo, {}, generated))


def test_legacy_artifacts_without_a_run_id_remain_valid(feature, repo):
    write_child(feature, repo, "analyze")
    write_child(feature, repo, "critic")
    write_judge(feature, repo)

    assert validate(feature, repo)["errors"] == []


def test_both_children_receive_the_same_parent_run_identity():
    planning = _read("templates/commands/planning-review.md")
    assert "PLANNING_REVIEW_RUN_ID" in planning and "seal" in planning
    for child in ("analyze", "critic"):
        body = _read(f"templates/commands/{child}.md")
        assert "PLANNING_REVIEW_RUN_ID" in body and "planning_review" in body, child


# ------------------------------------------------------------ lifecycle freshness


def _complete(feature):
    (feature / "tasks.md").write_text("- [x] T001 done\n", encoding="utf-8")


def test_a_fresh_proceed_lets_the_lifecycle_continue(feature, repo):
    _complete(feature)
    write_child(feature, repo, "analyze")
    write_child(feature, repo, "critic")
    write_judge(feature, repo)

    code, payload = run_cli("lifecycle", "--feature-dir", str(feature))

    assert code == 0, payload


def test_a_stale_proceed_is_not_evidence(feature, repo):
    _complete(feature)
    write_child(feature, repo, "analyze")
    write_child(feature, repo, "critic")
    write_judge(feature, repo)
    write_child(feature, repo, "analyze", [afinding("analyze-001", "low")])

    code, payload = run_cli("lifecycle", "--feature-dir", str(feature))

    assert code == 1 and "planning-review-stale" in {f["code"] for f in payload["failures"]}


def test_a_child_that_needs_a_recheck_fails_the_lifecycle(feature, repo):
    _complete(feature)
    write_child(feature, repo, "analyze")
    write_child(feature, repo, "critic")
    write_judge(feature, repo)
    (feature / "spec.md").write_text("---\nrequired_gates: analyze, critic\n---\n# Spec\nchanged\n", encoding="utf-8")

    code, payload = run_cli("lifecycle", "--feature-dir", str(feature))

    assert code == 1 and "planning-review-recheck-required" in {f["code"] for f in payload["failures"]}


def test_a_required_planning_review_that_never_ran_fails_the_lifecycle(feature, repo):
    _complete(feature)

    code, payload = run_cli("lifecycle", "--feature-dir", str(feature))

    assert code == 1 and "planning-review-missing" in {f["code"] for f in payload["failures"]}


def test_legacy_child_gates_still_satisfy_a_required_review_without_a_judge(feature, repo):
    _complete(feature)
    write_child(feature, repo, "analyze")
    write_child(feature, repo, "critic")

    code, payload = run_cli("lifecycle", "--feature-dir", str(feature))

    assert code == 0, payload


def test_captured_future_work_does_not_block_the_lifecycle_by_itself(feature, repo):
    _complete(feature)
    write_child(feature, repo, "analyze", [afinding("analyze-001")])
    write_child(feature, repo, "critic")
    deferred = concern(
        sources=("analyze-001",),
        classification="deferred-work",
        resolution="defer",
        future_work={"preserve": True, "type": "enhancement", "title": "Later", "reason": "not now"},
    )
    write_judge(feature, repo, [deferred])
    assert run_cli("future-work", "--feature-dir", str(feature), "--write")[0] == 0

    code, payload = run_cli("lifecycle", "--feature-dir", str(feature))

    assert code == 0, payload


def test_review_state_reports_missing_present_and_recheck(feature, repo):
    assert run_cli("review-state", "--feature-dir", str(feature))[1]["state"] == "missing"

    write_child(feature, repo, "analyze")
    write_child(feature, repo, "critic")
    write_judge(feature, repo)
    state = run_cli("review-state", "--feature-dir", str(feature))[1]
    assert state["state"] == "present" and state["verdict"] == "PROCEED" and state["needs_recheck"] is False

    (feature / "spec.md").write_text("---\nrequired_gates: analyze\n---\n# Spec\nchanged\n", encoding="utf-8")
    state = run_cli("review-state", "--feature-dir", str(feature))[1]
    assert state["needs_recheck"] is True and set(state["recheck_children"]) == {"analyze", "critic"}


# ----------------------------------------------- Minimum Sufficient Change surfaces


def test_specify_defines_the_mvp_boundary():
    spec = _read("templates/spec-template.md")
    for key in ("minimum_sufficient_change", "minimum_valuable_outcome", "explicitly_not_required", "acceptable_manual_operations"):
        assert key in spec
    assert "Minimum Sufficient Change" in _read("templates/commands/specify.md")


def test_plan_captures_operating_context_and_expected_mechanism_shape():
    plan = _read("templates/plan-template.md")
    block = next(
        yaml.safe_load(chunk.split("```", 1)[0])
        for chunk in plan.split("```yaml\n")[1:]
        if "operating_context" in chunk
    )
    assert {"expected_scale", "expected_frequency", "execution", "human_review_acceptable"} <= set(block["operating_context"])
    assert {"states", "runtime_settings", "endpoints", "persistent_stores", "caches", "background_workers"} <= set(
        block["expected_new_mechanisms"]
    )
    assert "not limits" in plan.lower() or "NOT limits" in plan


def test_critic_leads_with_the_least_complex_mitigation_and_does_not_prescribe_architecture():
    critic = _read("templates/commands/critic.md")
    assert "Least-complex mitigation first" in critic
    assert "A Critic finding identifies a risk. It does not prescribe architecture." in critic
    for field in ("least_complex_mitigation", "mitigation_kind"):
        assert field in critic


def test_judge_asks_the_subtraction_question_and_the_expected_shape_question():
    contract = _read("templates/judge-contract.md")
    assert "What can be removed or simplified while still satisfying every forcing requirement and invariant?" in contract
    assert "expected_new_mechanisms" in contract
    assert "what current requirement or demonstrated constraint forced this deviation?" in contract.lower()


def test_the_doctrine_is_stated_once_in_the_shared_preamble_with_its_safety_boundary():
    preamble = _read("templates/command-preamble-contract.md")
    for phrase in (
        "Minimum Sufficient Change",
        "MVP",
        "KISS",
        "YAGNI",
        "Complexity is a cost that requires justification.",
        "Correctness, security, safety, data integrity, and explicit contracts are not optional simplifications.",
    ):
        assert phrase in preamble, phrase


def test_proportionality_uses_existing_fields_and_authority_beyond_the_expected_shape():
    contract = _read("templates/judge-contract.md")
    assert "Where proportionality is recorded" in contract
    assert "there is no parallel field set" in contract
    assert "least-complex sufficient constraint" in contract
    assert "exceeding the approved Plan requires Judge-recorded or explicit human authority" in contract
    assert "proportionality:" not in contract


def test_the_plan_surface_has_consumers_and_is_orientation_not_an_allow_list():
    template = _read("templates/plan-template.md")
    assert "expected_change_surface:" in template
    assert "not an allow-list" in template
    assert "Do not store counts" in template

    for command in ("tasks", "analyze", "implement"):
        text = _read(f"templates/commands/{command}.md")
        assert "expected_change_surface" in text, command
        assert "explain-context" in text and "--files" in text, command
    critic = _read("templates/commands/critic.md")
    assert "optional orientation" in critic
    assert "does not limit what you examine" in critic
    assert "justified support" in _read("templates/commands/implement.md")


def test_there_is_no_standalone_simplify_command_or_gate():
    assert not (ROOT / "templates" / "commands" / "simplify.md").exists()
    assert not list((ROOT / ".github" / "agents").glob("devspark.simplify*"))
    assert not list((ROOT / ".github" / "prompts").glob("devspark.simplify*"))
