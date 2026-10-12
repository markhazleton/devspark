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


def test_remediation_prefers_the_least_complex_sufficient_correction(prompt: str) -> None:
    flat = _flat(_section(prompt, "#### D. Generate Findings", "### 5. Additional Review Dimensions"))
    assert "least-complex sufficient correction first" in flat
    assert "a risk does not prescribe architecture" in flat
    assert "Discovery alone does not make work mandatory" in flat


def test_duplicate_review_updates_guideline_is_gone_but_iteration_detection_remains(prompt: str) -> None:
    assert "### Review Updates" not in prompt
    assert "**Iteration Detection**" in prompt
    assert "`➡️ Carried`" in prompt  # status vocabulary still defined once, in the finding format


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


def test_last_verified_is_a_claim_not_proof(delta: str) -> None:
    text = delta.split("**`last_verified`**", 1)[1].split("**No unsupported", 1)[0]
    assert "not proof that every claim is correct" in text
    assert "triggers the claim check" in text
    assert "not itself a defect" in text


def test_negative_knowledge_assertions_require_compared_claims(delta: str) -> None:
    text = delta.split("**No unsupported", 1)[1].split("2. **`PRD1`", 1)[0]
    for phrase in ("Knowledge matches", "PRD1: none", "operator tables match"):
        assert phrase in text, phrase
    assert "freshly dated" in text
    assert "claims you actually compared" in text


def test_prd1_is_semantic_and_leaves_mechanical_freshness_to_create_pr(delta: str) -> None:
    prd1 = delta.split("2. **`PRD1`", 1)[1].split("3. **`PRD2`", 1)[0]
    assert "material claim you read" in prd1
    assert "relevant to this PR" in prd1
    assert "`/devspark-create-pr`" in prd1 and "semantic truth" in prd1


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
    assert "--check" in section and "read-only" in section.lower()
    assert "Never regenerate Knowledge during review" in section
    assert "git rev-parse HEAD" in section


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
