# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Behavior-neutral snapshot: command bodies and lifecycle outputs against the captured baseline.

Command bodies are compared as hashes after the narrow spelling normalization defined in the capture
helper, so respelling slash invocations is not read as a content change. Any other difference must be
listed in NAMED_DELTAS with a reason; the table starts empty and every entry is reviewed.
"""

from __future__ import annotations

import json
import shutil

import pytest

import tests.snapshot_baseline_helpers as snap


# command name (or "lifecycle:<bundle>") -> reason the difference is intended
NAMED_DELTAS: dict[str, str] = {
    "analyze": "independent constitutional backstop checks complete clauses and exceptions; rationale belongs in Spec/Plan, not Tasks",
    "checklist": "lean artifact ownership: assess concrete gaps without copying authoritative prose or imposing a target item count",
    "clarify": "shift-left: recheck materially changed requirements against complete constitutional text and surface unresolved conflicts",
    "release": "archival runs through the journaled release-archive script (plan, apply, validate) after the version is settled, and ambiguous artifacts are reported for a decision",
    "upgrade": "9.0 install and upgrade guidance: command entry points, skill category, and 8.x entry point retirement",
    "verify": "stage and evidence class: records the evidence class obtained, routes a pre-merge mode that needs deployment to the spec, and carries post-deploy items",
    "closeout": "stage and evidence class: post-deploy requirements are deferred with an existing durable record, never a created work item, and never block merge",
    "implement": "stage split: required verify modes stay pre-merge and post-deploy obligations never block Done",
    "create-pr": "pull request body states ready to deploy, not deployed, and lists carried post-deploy items",
    "specify": "stage split: authors the pre-merge mode and the post-deploy obligation as two halves",
    "plan": "stage split preserved in planning",
    "tasks": "post-merge capture rule applies to every tasks derivation",
    "critic": "deployment rollback concern stays pre-merge and critical beside post-deploy deferrals; a closer existing implementation than the planned new mechanism is a Critic finding; report tables project the YAML findings",
    "planning-review": "adjudication asks first whether the plan reuses the closest existing pattern",
    "workitem-create": "permanent rule: never creates a User Story, is never invoked by another command, and is never a lifecycle dependency",
    "workitem-review": "permanent rule: no handoff to the creating command",
    "next": "terminology: the /devspark-* wildcard names skills, not commands; routing is unchanged",
    "personalize": "terminology: the override-resolution sentence names the skill; resolution is unchanged",
    "pr-review": "engineering judgment: challenge accidental complexity and distinguish repeated integration from justified complexity",
    "address-pr-review": "bounded finding closeout and severity/blocking separation: closure follows the recorded review state, and blocking is an explicit field rather than inferred from severity",
    "quickfix": "Code First entry: reconcile an existing diff into the same quickfix record, route to implementation finalization, and keep advisory route guidance from waiving mandatory requirements",
    "explain": "Knowledge is judged by content against code; no derived-index freshness gate and no date-only finding",
    "site-audit": "Knowledge completeness checks that the Knowledge builds and reads coverage; a date alone is never a finding",
    "constitution": "one flow: the handoff starts new work rather than a feature specification",
}

BASELINE_BODIES = json.loads((snap.BASELINE / "command-bodies.json").read_text(encoding="utf-8"))
BASELINE_LIFECYCLE = json.loads((snap.BASELINE / "lifecycle-outputs.json").read_text(encoding="utf-8"))


def test_delta_table_entries_carry_a_reason():
    assert all(reason.strip() for reason in NAMED_DELTAS.values())


def test_spelling_normalization_is_narrow():
    normalize = snap.normalize_spelling
    assert normalize("run /devspark-specify now") == "run /devspark.specify now"
    assert normalize("run /devspark.specify now") == "run /devspark.specify now"
    assert normalize("/devspark-next-context stays") == "/devspark-next-context stays"
    assert normalize("/devspark-unknown stays") == "/devspark-unknown stays"
    assert normalize("devspark-specify with or without slash") == "devspark.specify with or without slash"
    assert normalize("skills/devspark-specify/SKILL.md stays") == "skills/devspark-specify/SKILL.md stays"
    assert normalize("a\r\nb") == "a\nb"


def test_baseline_covers_every_stock_command():
    assert sorted(BASELINE_BODIES) == snap.stock_commands() or set(BASELINE_BODIES) <= set(snap.stock_commands())
    assert len(BASELINE_BODIES) == 38


def test_command_bodies_match_the_baseline_after_spelling_normalization():
    current = snap.command_hashes()
    changed = sorted(
        name for name in set(current) | set(BASELINE_BODIES) if current.get(name) != BASELINE_BODIES.get(name)
    )
    unexplained = [name for name in changed if name not in NAMED_DELTAS]
    assert not unexplained, f"command bodies changed without a named delta: {unexplained}"
    stale = [name for name in NAMED_DELTAS if not name.startswith("lifecycle:") and name not in changed]
    assert not stale, f"named deltas that no longer differ: {stale}"


def test_baseline_bundles_match_the_fixture_bundles():
    assert sorted(BASELINE_LIFECYCLE) == snap.bundles()


@pytest.mark.skipif(shutil.which("pwsh") is None or snap._bash() is None, reason="both next-context twins are required")
@pytest.mark.parametrize("bundle", snap.bundles())
def test_lifecycle_outputs_match_the_baseline(bundle, tmp_path):
    repo = snap.make_repo(tmp_path, bundle)
    outputs = {
        "judge_lifecycle": snap.judge_lifecycle(repo),
        "next_context_pwsh": snap.next_context("pwsh", repo),
        "next_context_bash": snap.next_context("bash", repo),
    }
    assert outputs["next_context_pwsh"] == outputs["next_context_bash"], bundle
    baseline = BASELINE_LIFECYCLE.get(bundle)
    if outputs != baseline:
        delta_key = f"lifecycle:{bundle}"
        assert delta_key in NAMED_DELTAS, f"lifecycle output for {bundle} changed without a named delta: {outputs}"


def test_no_stale_lifecycle_deltas():
    stale = [name for name in NAMED_DELTAS if name.startswith("lifecycle:") and name.split(":", 1)[1] not in BASELINE_LIFECYCLE]
    assert not stale, f"stale lifecycle deltas: {stale}"
