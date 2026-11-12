# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for `/devspark-pr-review` finding legitimacy, attribution and Knowledge recall.

These pin the semantic anchors of the review discipline, not its wording. The semantic comparison
itself (does a Knowledge table still match the code) is model-driven and is not tested here; what
is tested is that the prompt demands it, and that the deterministic owner lookup it relies on
returns the right documents.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PR_REVIEW = ROOT / "templates" / "commands" / "pr-review.md"


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _section(text: str, start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]


@pytest.fixture(scope="module")
def prompt() -> str:
    return PR_REVIEW.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def legitimacy(prompt: str) -> str:
    return _flat(_section(prompt, "#### C. Finding Legitimacy Check", "#### D. Generate Findings"))


@pytest.fixture(scope="module")
def delta(prompt: str) -> str:
    return _flat(_section(prompt, "### 6. Durable Delta Consistency Validation", "### 6b."))


# --- Finding legitimacy ------------------------------------------------------------------------


def test_existing_legitimacy_tests_are_preserved(legitimacy: str) -> None:
    for name in ("Intent", "Actionability", "Ownership", "Self-consistency"):
        assert f"**{name}**" in legitimacy, name


def test_candidate_is_distinct_from_validated_finding_without_new_machinery(legitimacy: str) -> None:
    assert "only a **candidate** until it passes this check" in legitimacy
    assert "only validated concerns become numbered findings" in legitimacy
    assert "no artifact, no extra pass" in legitimacy


def test_basic_legitimacy_applies_to_every_numbered_finding_including_low(legitimacy: str) -> None:
    basic = legitimacy.split("**Basic legitimacy", 1)[1].split("CRITICAL, HIGH, and MEDIUM", 1)[0]
    assert "every numbered finding, including Low" in basic
    for element in ("concrete observation", "violated expectation", "relevance to *this* PR"):
        assert element in basic, element
    assert "approved intent" in basic and "not a defect" in basic
    assert "`### Observations`" in basic and "no ID and no severity" in basic


def test_consumer_trace_is_required_for_behavioral_medium_and_above(legitimacy: str) -> None:
    trace = legitimacy.split("**Consumer trace**", 1)[1].split("**Attribution**", 1)[0]
    assert "behavioral concern at MEDIUM or higher" in trace
    assert "reader of the changed value" in trace
    assert "this* instance can reach the claimed consequence" in trace
    assert "Not exhaustive tracing" in trace


def test_findings_and_handoffs_cannot_invent_operating_conditions_or_approvers(legitimacy: str) -> None:
    for rule in (
        "concrete scenario reachable in the supported environment",
        "evidence it can occur",
        "Hypothetical tenants, environments, scale or future consumers do not establish a defect",
        "never recover a planning bundle",
        "Applicable mandatory controls still bind even without a runtime failure",
        "Do not manufacture an external sign-off or coordination task there",
        "an optional recommendation stays explicitly optional",
    ):
        assert rule in legitimacy


def test_nearest_falsifying_evidence_is_sought_and_a_defeated_concern_is_dropped(legitimacy: str) -> None:
    trace = legitimacy.split("**Consumer trace**", 1)[1].split("**Attribution**", 1)[0]
    assert "would prove the concern wrong" in trace
    assert "drop it" in trace
    assert "do not keep a defeated concern at lower severity" in trace


def test_an_unconfirmed_risk_cannot_block_or_exceed_low(legitimacy: str) -> None:
    trace = legitimacy.split("**Consumer trace**", 1)[1].split("**Attribution**", 1)[0]
    assert "unconfirmed risk" in trace
    assert "never block on it" in trace and "never rate it above Low" in trace
    assert "Uncertainty alone is not evidence of a defect" in trace


def test_attribution_classes_and_their_treatment(legitimacy: str) -> None:
    attribution = legitimacy.split("**Attribution**", 1)[1].split("An item that fails Test 2", 1)[0]
    for cls in ("*introduced*", "*exposed*", "*pre-existing but material*", "*pre-existing and unrelated*"):
        assert cls in attribution, cls
    assert "never blocks" in attribution
    assert "may block" in attribution
    assert "Pre-existing is never automatically ignorable" in attribution
    assert "schema" not in attribution.lower()  # prose only, no new finding field


def test_observation_routing_replaces_dropping_for_failed_basic_legitimacy(legitimacy: str) -> None:
    assert "fails basic legitimacy or Test 1 is dropped, recorded as an Observation" in legitimacy


# --- Observations, approval, severity, remediation ----------------------------------------------


def test_report_template_has_a_nonblocking_observations_subsection(prompt: str) -> None:
    notes = _section(prompt, "## Deployment & Handoff Notes", "## Approval Decision")
    assert "### Observations" in notes
    observations = _flat(notes.split("### Observations", 1)[1])
    assert "No ID, no severity" in observations
    assert "never a reason for REQUEST CHANGES" in observations
    assert "unconfirmed risks" in observations


def test_observations_never_imply_request_changes_and_blocking_needs_a_validated_blocker(prompt: str) -> None:
    semantics = _flat(_section(prompt, "### Approval Semantics", "### Severity Guidelines"))
    assert "Observations do not imply REQUEST CHANGES" in semantics
    assert "Every REQUEST CHANGES decision must trace to at least one validated blocking finding" in semantics
    assert "APPROVE may coexist with" in semantics


def test_severity_no_longer_prefers_the_higher_tier(prompt: str) -> None:
    flat = _flat(prompt)
    assert "prefer the higher" not in flat.lower()
    guidelines = _flat(_section(prompt, "### Severity Guidelines", "| Finding Type"))
    assert "demonstrated consequence" in guidelines
    assert "confidence in the validated evidence" in guidelines
    assert "never automatic escalation" in guidelines


def test_severity_and_blocking_are_independent_throughout_the_prompt(prompt: str) -> None:
    flat = _flat(prompt).lower()
    assert "severity alone does not establish a blocker" in flat
    assert "blocking defect" in flat and "severity alone does not determine blocking" in flat
    assert "a binding non-waivable obligation remains blocking regardless of severity" in flat
    assert "high or critical alone does not block" in flat
    assert "requires an actual unresolved blocking obligation" in flat
    assert "named, authorized human and a reason; silence is never approval" in flat
    for obsolete in (
        "critical: violates mandatory (must) principle - blocks merge",
        "blocking (critical/high)",
        "critical (blocking)",
        "critical issues (blocking)",
        "critical issues must be resolved before merge",
    ):
        assert obsolete not in flat, obsolete


def test_remediation_prefers_the_least_complex_sufficient_correction(prompt: str) -> None:
    flat = _flat(_section(prompt, "#### D. Generate Findings", "### 5. Additional Review Dimensions"))
    assert "least-complex sufficient correction first" in flat
    assert "a risk does not prescribe architecture" in flat
    assert "Discovery alone does not make work mandatory" in flat


def test_duplicate_review_updates_guideline_is_gone_but_iteration_detection_remains(prompt: str) -> None:
    assert "### Review Updates" not in prompt
    assert "**Iteration Detection**" in prompt
    assert "`➡️ Carried`" in prompt  # status vocabulary still defined once, in the finding format


def test_followup_review_stops_without_discovery_but_checks_new_exposure(prompt: str) -> None:
    iteration = _flat(_section(prompt, "**Iteration Detection**", "**PR Number Detection**"))
    for safeguard in (
        "existing review of this PR",
        "no correction is pending and no relevant behavior changed",
        "refresh the report, and stop",
        "incoming changes and merge conflict resolutions",
        "Review new substantive changes in that intervening delta",
        "new callers, inputs, permissions, or configuration",
        "Preserve existing governed accepted/deferred/withdrawn decisions",
    ):
        assert safeguard in iteration


def test_update_is_a_terminal_path_that_checks_prerequisites_before_proof(prompt: str) -> None:
    flat = _flat(prompt)
    assert flat.index("Choose the route (Iteration Detection below) before investigating") < flat.index(
        "Initial-review execution limits"
    )
    iteration = _flat(_section(prompt, "**Iteration Detection**", "**PR Number Detection**"))
    assert "UPDATE is a terminal path" in iteration
    fall_through = iteration.split("Do not fall through into", 1)[1].split("No final discovery sweep", 1)[0]
    for excluded in (
        "§1b–§6d",
        "Knowledge retrieval or projection",
        "durable-learning harvest",
        "architectural exploration",
        "unrelated quality checks",
    ):
        assert excluded in fall_through, excluded
    assert "If the engine fails or rejects the record, report its diagnostic and stop" in iteration
    assert iteration.index("**Prerequisites before proof.**") < iteration.index("**Evaluate.**")
    assert "never invent an identity, evidence, or approval" in iteration
    assert "If findings await verification and none can proceed, report the missing prerequisites" in iteration
    assert "leave `reviewed_commit` at the previous evaluated commit, and stop" in iteration
    assert "a merge-only update records its new head only after this bounded check completes" in iteration
    assert "Only after this bounded evaluation completes, set `reviewed_commit` to that head" in iteration
    assert "a finding left pending in step 2 gets no verification event" in iteration
    assert "matter only through a demonstrated effect" in iteration
    assert "do not audit incoming commits" in iteration
    existing = _flat(_section(prompt, "#### Handle Existing Reviews", "#### Report Forms"))
    assert "An existing file means the UPDATE path" in existing
    assert "explicitly requested a fresh full review" in existing


def test_findings_may_rest_on_non_constitution_expectations(prompt: str) -> None:
    authority = _flat(_section(prompt, "### Constitution Authority", "### Evidence-Based Feedback"))
    assert "another legitimate expectation under §4C" in authority
    assert "Use `CON` only when the constitution itself should change" in authority
    flat = _flat(prompt)
    assert "If a concern is not in the constitution, flag it LOW" not in flat
    assert "flagged as a `CON` candidate" not in flat
    assert "Extract all core principles" not in flat


def test_prd_prefix_alone_does_not_block(delta: str, prompt: str) -> None:
    assert "the `PRD` prefix alone does not block" in delta
    assert "strong, blocking gate" not in delta.lower()
    assert "every open one belongs in the Immediate Actions" not in delta
    assert "every unresolved blocking `PRD{N}` finding" in delta
    assert "including each open `PRD{N}`" not in _flat(prompt)


def test_report_validation_recovery_is_bounded(prompt: str) -> None:
    section = _flat(_section(prompt, "### 9. Write Review File", "### 10. Output Summary to User"))
    assert "make one targeted correction through the state engine and validate once more" in section
    assert "report the diagnostic, state that the review file is unvalidated" in section
    assert "Do not repair framework scripts or templates, change product code" in section
    assert "Never silently skip this required check" in section


def test_accidental_complexity_review_evaluates_proportionality_and_preserves_guarantees(prompt: str) -> None:
    flat = _flat(_section(prompt, "#### Accidental Complexity & Duplication Review", "#### Testing Validation"))
    assert "Evaluate whether avoidable accidental complexity remains" in flat
    assert "rather than merely certifying that the implementation followed a plan" in flat
    for pattern in (
        "Repeated wiring",
        "Redundant processing",
        "Duplicate or excessive abstraction",
        "Speculative extension",
        "Unnecessary indirection",
    ):
        assert pattern in flat, pattern
    assert "A smaller implementation that drops validation guarantees or changes exception behavior is NOT equivalent" in flat
    assert "Line count, file count, or abstraction count are NEVER automatic failure conditions" in flat
    assert "Do not turn PR review into a mandatory redesign exercise" in flat


def test_architectural_fitness_checks_material_design_risks_without_becoming_a_style_gate(prompt: str) -> None:
    flat = _flat(_section(prompt, "#### Accidental Complexity & Duplication Review", "#### Testing Validation"))
    for concern in (
        "coupling across established responsibilities",
        "duplicated behavior or parallel mechanisms",
        "unnecessary abstractions",
        "accumulating conditional complexity",
        "fragile state",
        "temporal or persistence assumptions",
        "compatibility",
        "data-integrity",
    ):
        assert concern in flat, concern
    for requirement in (
        "actual changed code",
        "applicable expectation or demonstrated engineering obligation",
        "concrete consequence on this PR's path",
        "smallest justified correction",
        "within the Delta's blast radius",
        "A stylistic preference",
        "do not redesign for architectural perfection",
    ):
        assert requirement in flat, requirement


def test_change_sensitivity_is_evidence_grounded_and_bounded(prompt: str) -> None:
    flat = _flat(_section(prompt, "#### Accidental Complexity & Duplication Review", "#### Testing Validation"))
    assert "at most one or two reasonably foreseeable next changes" in flat
    assert "current contracts, observed consumers, established domain behavior" in flat
    assert "Do not invent future requirements" in flat
    assert "Passing functional tests" in flat
    assert "does not establish that historical evidence" in flat


# --- Code <-> Knowledge recall -----------------------------------------------------------------


def test_knowledge_owners_come_from_the_existing_files_lookup(delta: str) -> None:
    assert "explain-context.py --files" in delta
    assert "explain-context.sh" in delta and "explain-context.ps1" in delta
    assert "read-only" in delta
    assert "cites it through `source_of_truth`" in delta
    assert "Do not read the Knowledge corpus" in delta


def test_claim_targeted_check_is_word_bounded_and_reads_before_promoting(delta: str) -> None:
    check = delta.split("**Claim-targeted check.**", 1)[1].split("**`last_verified`**", 1)[0]
    for family in ("operators", "enums", "state values", "configuration keys", "status codes", "defaults"):
        assert family in check, family
    assert "**word-bounded**" in check
    assert "`field_eq` hit `field_equals`" in check
    assert "omits the new member" in check
    assert "A search hit alone proves nothing" in check
    assert "rests on a claim you read" in check


def test_review_does_not_gate_on_derived_index_or_date_freshness(delta: str, prompt: str) -> None:
    section = _flat(_section(prompt, "### 6c.", "### 6d."))
    assert "never judge a PR on whether derived index files" in section
    assert "last_verified" not in delta and "INDEX_FRESH" not in delta


def test_negative_knowledge_assertions_require_compared_claims(delta: str) -> None:
    text = delta.split("**No unsupported", 1)[1].split("2. **`PRD1`", 1)[0]
    for phrase in ("Knowledge matches", "PRD1: none"):
        assert phrase in text, phrase
    assert "claims you actually compared" in text


def test_review_resolves_further_knowledge_only_for_an_open_question(delta: str, prompt: str) -> None:
    retrieval = delta.split("**Resolve further Knowledge only for an open question.**", 1)[1].split(
        "**Claim-targeted check.**", 1
    )[0]
    for requirement in (
        "canonical `explain-context.py` topic retrieval",
        "accepted relationships",
        "only to answer a specific unresolved contract or ownership question",
        "name the question and stop when it is answered",
        "Neither the report form nor an empty owner lookup alone decides this",
        "an unmapped, materially new contract may still need it",
        "retain only candidates",
        "read each retained source",
        "cite the Knowledge path and heading",
        "not current truth",
        "unaccepted projection candidate",
    ):
        assert requirement in retrieval, requirement
    for obsolete in ("concise packet", "Carry durable learning forward", "Build the review's applicable Knowledge context"):
        assert obsolete not in delta, obsolete
    prd5 = delta.split("6. **`PRD5`", 1)[1].split("7. ", 1)[0]
    assert "do not copy source code, test details, ephemeral history" in prd5
    report = _flat(_section(prompt, "## Applicable Knowledge", "## Security"))
    assert "Only when Knowledge was consulted to settle a finding or an open question" in report
    assert "applicable invariants" in report
    assert "Cite each authoritative `.knowledge/` path and heading" in report
    assert "Omit unrelated candidates" in report


def test_review_context_contract_covers_the_pr_review_prompt() -> None:
    contract_path = ROOT / ".knowledge" / "governance" / "knowledge-framework-contract.md"
    contract = contract_path.read_text(encoding="utf-8")
    frontmatter = contract.split("---", 2)[1]
    lifecycle = contract.split("## 23. Lifecycle responsibilities", 1)[1].split(
        "## 24.", 1
    )[0]
    assert "templates/commands/pr-review.md" in frontmatter
    assert "canonical topic retrieval" in lifecycle
    assert "only to answer a specific unresolved contract or ownership question" in lifecycle
    assert "cite the invariants a finding or decision relied on" in lifecycle
    assert "existing owner is reconciled in the same change" in lifecycle
    assert "A focused update evaluates corrections only" in lifecycle


def test_prd1_is_semantic_truth_judged_from_claims_read(delta: str) -> None:
    prd1 = delta.split("2. **`PRD1`", 1)[1].split("3. **`PRD2`", 1)[0]
    assert "material claim you read" in prd1
    assert "relevant to this PR" in prd1
    assert "semantic truth" in prd1


def test_prd3_coverage_is_proportionate_to_behavior_and_delegation(delta: str) -> None:
    prd3 = delta.split("4. **`PRD3`", 1)[1].split("5. **`PRD4`", 1)[0]
    assert "externally observable behavior" in prd3
    assert "directly tested helper" in prd3
    assert "simple delegation" in prd3 and "does not require duplicated caller tests" in prd3
    assert "unrelated historical test debt" in prd3
    assert "blocks only when the changed behavior lacks coverage at a layer proportionate" in prd3


# --- Boundaries that must not move --------------------------------------------------------------


def test_knowledge_check_stays_read_only_and_head_verified(prompt: str) -> None:
    section = _flat(_section(prompt, "### 6c.", "### 6d."))
    assert "Never regenerate Knowledge during review" in section
    assert "git show <head-sha>:<path>" in section
    assert "never move HEAD to reach it" in section
    assert "check it out" not in section


def test_pr_review_does_not_load_the_assurance_contract_or_add_machinery(prompt: str) -> None:
    flat = _flat(prompt)
    assert "assurance-contract" not in flat
    for forbidden in ("second pass", "candidate artifact file", "confidence score"):
        assert forbidden not in flat.lower(), forbidden


# --- Deterministic evidence targeting (the owner lookup PRD1 relies on) --------------------------


def _load_explain_context():
    spec = importlib.util.spec_from_file_location("explain_context_pr_review", ROOT / "scripts" / "explain-context.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _knowledge_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    for name in ("resolver.py", "models.py", "unrelated.py"):
        (repo / "src" / name).write_text("VALUE = 1\n", encoding="utf-8")
    guide = repo / ".knowledge" / "entities" / "flow"
    guide.mkdir(parents=True)
    (guide / "_entity.yaml").write_text("id: flow\ntype: subsystem\nowner: Team\n", encoding="utf-8")
    # Touched by the change and freshly re-dated, yet still the owner that must be inspected.
    (guide / "integration.md").write_text(
        "---\nid: flow-integration\nlayer: integration\ntitle: Flow guide\n"
        "source_of_truth:\n  - src/resolver.py\nlast_verified: 2099-01-01\n---\n\n"
        "# Flow guide\n\n| Operator | Meaning |\n|---|---|\n| `field_equals` | equal |\n",
        encoding="utf-8",
    )
    (repo / ".knowledge" / "governance").mkdir(parents=True)
    (repo / ".knowledge" / "governance" / "models.md").write_text(
        "---\nid: models-contract\ntype: governance\ntitle: Models contract\nappliesTo:\n  - src/models.py\n---\n\n# Models\n",
        encoding="utf-8",
    )
    return repo


def test_files_lookup_returns_owner_citing_a_changed_source_even_when_touched_and_redated(
    monkeypatch, capsys, tmp_path: Path
) -> None:
    explain = _load_explain_context()
    repo = _knowledge_repo(tmp_path)
    before = sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*"))
    monkeypatch.setattr(explain, "repository_root", lambda: repo)
    monkeypatch.setattr("sys.argv", ["explain-context.py", "--files", "src/resolver.py", "src/models.py", "src/unrelated.py"])

    assert explain.main() == 0
    payload = json.loads(capsys.readouterr().out)

    owners = {item["path"]: {(o["id"], o["relationship"]) for o in item["owners"]} for item in payload["FILES"]}
    assert ("flow-integration", "source_of_truth") in owners["src/resolver.py"]
    assert ("models-contract", "appliesTo") in owners["src/models.py"]
    assert payload["UNMAPPED_FILES"] == ["src/unrelated.py"]
    assert sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*")) == before  # read-only


def test_updated_durable_invariant_is_retrieved_without_unrelated_knowledge(
    monkeypatch, capsys, tmp_path: Path
) -> None:
    explain = _load_explain_context()
    repo = _knowledge_repo(tmp_path)
    source = repo / "src" / "resolver.py"
    source.write_text(
        "def classify(need_definitions, retry_catalog):\n"
        "    invocation_snapshot = (tuple(need_definitions), tuple(retry_catalog))\n"
        "    return retry_with_snapshot(invocation_snapshot)\n",
        encoding="utf-8",
    )
    owner = repo / ".knowledge" / "entities" / "flow" / "integration.md"
    owner.write_text(
        "---\nid: flow-integration\nlayer: integration\ntitle: Classifier evaluation\n"
        "source_of_truth:\n  - src/resolver.py\nlast_verified: 2026-10-15\n---\n\n"
        "# Historical classifier evaluation\n\n"
        "A classifier invocation captures its Need definitions and retry catalog once. Every "
        "retry uses that invocation snapshot rather than reconstructing historical evidence from "
        "mutable current configuration.\n",
        encoding="utf-8",
    )

    index = explain.build_index(repo)
    assert any(node["id"] == "flow-integration" for node in index["nodes"])

    monkeypatch.setattr(explain, "repository_root", lambda: repo)
    monkeypatch.setattr(
        "sys.argv",
        ["explain-context.py", "classifier evaluation historical Need retry catalog"],
    )

    assert explain.main() == 0
    payload = json.loads(capsys.readouterr().out)
    matches = {item["id"]: item for item in payload["MATCHED_KNOWLEDGE"]}
    assert "INDEX_FRESH" not in payload
    assert "flow-integration" in matches
    assert "models-contract" not in matches
    source_status = matches["flow-integration"]["source_status"][0]
    assert source_status["path"] == "src/resolver.py" and source_status["exists"] is True
    assert "Need definitions and retry catalog once" in owner.read_text(encoding="utf-8")

    source.unlink()
    assert explain.main() == 1
    error_payload = json.loads(capsys.readouterr().out)
    assert "source_of_truth path does not exist" in error_payload["ERROR"]
