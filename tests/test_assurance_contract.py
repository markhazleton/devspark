# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Static validation for the Analyze/Critic assurance boundary.

Pins the properties that keep the two planning-assurance capabilities
complementary rather than redundant: separated lane ownership, no duplicate
findings, no generic noise, no metadata self-policing, bounded passes, and a
derived verdict vocabulary.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "templates" / "assurance-contract.md"
ANALYZE = ROOT / "templates" / "commands" / "analyze.md"
CRITIC = ROOT / "templates" / "commands" / "critic.md"
FIXTURES = ROOT / "tests" / "fixtures" / "assurance"

# The four capabilities that evaluate work they did not author.
CAPABILITIES = ("Analyze", "Critic", "Verify", "PR Review")

# Repository-agnostic change-shape signals that decide Critic applicability.
# These describe software shape only -- never a product, vendor, or repository.
APPLICABILITY_SIGNALS = (
    "persistent-data-shape",
    "cross-boundary-interaction",
    "state-lifecycle",
    "nondeterministic-behavior",
    "new-entry-point",
)

# Verdict vocabulary. Nothing outside this set may be emitted.
VERDICTS = ("STOP", "CONDITIONAL", "PROCEED")

# Metadata findings removed by this contract: a capability must never
# manufacture a developer-facing defect because its own preferred
# classification metadata is absent.
REMOVED_METADATA_FINDINGS = (
    "archetype-ambiguity",
    "missing-risk-profile",
    "missing-change-type",
)

# Canonical convergence classifications. There is exactly one convergence
# model (templates/closeout-contract.md); assurance must not fork a second.
CLASSIFICATIONS = (
    "blocking-defect",
    "accepted-limitation",
    "deferred-work",
    "learning",
)

SPEC145_EXTERNAL_DEPENDENCY_EXCEPTION = """External Dependency Exception (MANDATORY):
- For outbound remote API calls (external dependencies), the caller MUST log each call attempt to Kusto regardless of outcome.
- Both success and failure outcomes MUST be logged for each attempt (including retries).
- Dependency-call logging MAY emit multiple entries within a single inbound transaction by design.
"""


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate_canonical_contract_exists() -> None:
    assert CONTRACT.exists(), "templates/assurance-contract.md must exist"
    body = _read(CONTRACT)

    # One canonical source, resolvable from both installed and source repos.
    assert "/.devspark/templates/assurance-contract.md" in body
    assert "templates/assurance-contract.md" in body

    # Every capability has a declared core question and an explicit
    # "does not own" column -- the boundary is stated once, here.
    for capability in CAPABILITIES:
        assert f"**{capability}**" in body, f"{capability} missing from capability table"
    assert "Are the planning artifacts internally sound?" in body
    assert "Is this internally sound plan wrong about the real system it will run in?" in body
    assert "Did the implementation actually work?" in body
    assert "Should this resulting delta be accepted?" in body
    assert "Explicitly does **not** own" in body


def validate_single_owner_invariant() -> None:
    body = _read(CONTRACT)

    assert "**A finding has exactly one assurance owner.**" in body

    # Cross-lane observations are routed, never emitted as findings.
    assert "routed_findings:" in body
    assert "never in `findings:`" in body

    # Both capabilities implement the routing escape.
    for path in (ANALYZE, CRITIC):
        text = _read(path)
        assert "routed_findings:" in text, f"{path.name} must support assurance escape routing"
        assert "owner:" in text, f"{path.name} findings must declare an owner"


def validate_lane_separation() -> None:
    critic = _read(CRITIC)
    analyze = _read(ANALYZE)

    # Critic must defer the closed-world artifact concerns to Analyze.
    for owned_by_analyze in (
        "Artifact consistency",
        "traceability",
        "Documentation drift",
        "Requirement *wording* precision",
    ):
        assert owned_by_analyze in critic, (
            f"critic.md must explicitly disclaim {owned_by_analyze!r}"
        )

    # Analyze must defer the open-world concerns to Critic.
    for owned_by_critic in (
        "achievable",
        "missing entirely",
        "sufficiency",
    ):
        assert owned_by_critic in analyze, (
            f"analyze.md must explicitly disclaim {owned_by_critic!r}"
        )

    # Neither file may re-define the boundary as a second source of truth.
    assert "not a second definition" in critic
    assert "it does not restate it" in critic
    assert "it does not restate it" in analyze


def validate_no_metadata_self_policing() -> None:
    body = _read(CONTRACT)
    critic = _read(CRITIC)

    assert "No Metadata Self-Policing" in body
    assert "resolved by inference and reported in the gate header" in body

    # Critic must no longer emit these as findings. The names may appear only
    # in the backward-compatibility note explaining their removal.
    for name in REMOVED_METADATA_FINDINGS:
        emitted = f"emit a HIGH finding (`{name}`)"
        assert emitted not in critic, f"critic.md still emits {name} as a finding"
    assert "missing metadata is **never** emitted as a finding" in critic


def validate_evidence_requirement() -> None:
    body = _read(CONTRACT)
    critic = _read(CRITIC)

    assert "MUST inspect the relevant existing code, tests, and `.knowledge/`" in body
    assert "Baseline Evidence Pass" in critic
    assert "A claim about the baseline with no cited evidence MUST NOT be emitted" in critic
    assert "evidence:" in critic, "critic findings must carry an evidence field"


def validate_lifecycle_boundary() -> None:
    body = _read(CONTRACT)
    critic = _read(CRITIC)

    # Critic is planning-time assurance; it never becomes post-implementation review.
    assert "Baseline Reality Is Not Implementation Review" in body
    assert "never reviews the work performed to resolve its own earlier findings" in critic

    # A capability must not review its own remediation.
    assert "MUST NOT review the work performed to resolve its own earlier findings" in body


def validate_deduplication_rules() -> None:
    body = _read(CONTRACT)

    assert "### 5.1 Across Capabilities" in body
    assert "### 5.2 Within One Capability" in body
    assert "**do not create another finding**" in body
    assert "root_cause:" in body
    assert "Material unique findings" in body

    for path in (ANALYZE, CRITIC):
        text = _read(path)
        assert "Deduplicate across capabilities" in text, f"{path.name} missing cross-capability dedup"
        assert "Deduplicate within" in text, f"{path.name} missing intra-capability dedup"


def validate_finding_quality_bar() -> None:
    body = _read(CONTRACT)

    # All five questions must be answerable or the finding is not emitted.
    for question in (
        "**What** is wrong",
        "**Why** is it material",
        "**What evidence**",
        "**Why does this capability own it**",
        "**What decision, mitigation, or proof**",
    ):
        assert question in body, f"quality bar missing {question}"

    # Generic advice is named and prohibited by construction.
    for generic in ("consider scalability", "ensure observability", "think about security"):
        assert generic in body, f"quality bar must name {generic!r} as prohibited"


def validate_uncertainty_is_not_a_defect() -> None:
    body = _read(CONTRACT)
    critic = _read(CRITIC)

    assert "Uncertainty Is Not a Defect" in body
    assert "verification_obligations:" in body
    assert "verification_obligations:" in critic
    assert "Critic identifies the risk in time to plan for proof. Verify performs the proof." in body


def validate_bounded_passes() -> None:
    body = _read(CONTRACT)
    critic = _read(CRITIC)

    for phase in ("DISCOVERY", "REMEDIATION", "RECHECK", "STOP"):
        assert phase in body, f"bounded-pass model missing {phase}"

    assert "MUST NOT open a new open-ended discovery pass" in body
    assert "Do not open a new open-ended discovery pass" in critic


def validate_single_convergence_model() -> None:
    body = _read(CONTRACT)
    critic = _read(CRITIC)

    # Assurance binds to the existing convergence contract; it must not
    # introduce a parallel taxonomy.
    assert "closeout-contract.md" in body
    assert "There is no capability-specific taxonomy." in body

    for classification in CLASSIFICATIONS:
        assert classification in critic, f"critic.md must use canonical classification {classification}"

    # Severity and blocking remain independent dimensions.
    assert "separate dimensions" in body
    assert "separate dimensions" in critic


def validate_derived_verdict() -> None:
    body = _read(CONTRACT)
    critic = _read(CRITIC)

    assert "Verdicts Are Derived" in body
    for verdict in VERDICTS:
        assert f"**{verdict}**" in body, f"verdict table missing {verdict}"

    assert "computed from the findings, never authored independently" in body
    assert "The verdict is **derived**, never authored" in critic

    # Off-contract verdict words are named and prohibited.
    for off_contract in ("`GO`", "`PASS`", "`MOSTLY READY`"):
        assert off_contract in body, f"verdict vocabulary must prohibit {off_contract}"
    assert "No other verdict word is permitted." in critic


def validate_applicability_model() -> None:
    body = _read(CONTRACT)
    critic = _read(CRITIC)

    assert "## 11. Critic Applicability" in body

    # Applicability is driven by observable change shape, not authored risk.
    assert "`risk_level` MUST NOT be the primary run/skip switch" in body
    assert "Neither decides whether Critic runs" in critic

    for signal in APPLICABILITY_SIGNALS:
        assert f"`{signal}`" in body, f"contract missing applicability signal {signal}"
        assert signal in critic, f"critic.md missing applicability signal {signal}"

    # The decision is inspectable, in both directions.
    assert "applicable: true" in body
    assert "applicable: false" in body
    assert "signals:" in body
    assert "reason:" in body
    assert "Negative Controls" in body

    # Critic stays explicitly callable even when no signal fires.
    assert "remains explicitly callable on any route" in body


def validate_signals_are_repository_agnostic() -> None:
    """Signals must describe software shape, never a specific product."""
    body = _read(CONTRACT)
    critic = _read(CRITIC)

    assert "Signals describe **software shape**. They never name a product" in body

    # Guard against leaking the product names of the repository that motivated
    # this model into the framework's generic vocabulary.
    forbidden = ("Clearstep", "Epic", "Cosmos DB", "Triage repo")
    for path, text in ((CONTRACT, body), (CRITIC, critic), (ANALYZE, _read(ANALYZE))):
        for name in forbidden:
            assert name not in text, f"{path.name} leaks repository-specific name {name!r}"


def validate_interaction_policy() -> None:
    body = _read(CONTRACT)
    critic = _read(CRITIC)

    assert "## 10. Interaction Policy" in body
    assert "interacts with **decisions**" in body
    assert "Interaction Policy" in critic
    assert "not by itself a reason to interrupt the developer" in critic


def validate_analyze_hardened_passes() -> None:
    """Analyze must own the bookkeeping defects Critic was compensating for."""
    analyze = _read(ANALYZE)

    assert "Missing requirement anchor" in analyze
    assert "Completion bookkeeping" in analyze
    assert "Declared-contract conformance" in analyze
    assert "Task sequencing validity" in analyze


def validate_risk_checklist_resolution_path() -> None:
    """Installed repos keep framework templates under .devspark/templates/.

    The manifest maps templates/** (minus commands/) to .devspark/templates/**,
    and the quickstart guides treat a root-level .devspark/risk-checklists/ as a
    legacy leftover to delete. Resolving checklists from the root path therefore
    never finds them in an installed repository.
    """
    critic = _read(CRITIC)

    assert "/.devspark/templates/risk-checklists/" in critic
    assert "/.devspark/risk-checklists/" not in critic, (
        "critic.md resolves risk checklists from the .devspark/ root, which the "
        "manifest never installs and the quickstart guides instruct users to delete"
    )
    # Source-repo and team-override paths remain available.
    assert "templates/risk-checklists/" in critic
    assert ".devspark.work/risk-checklists/" in critic


def validate_fixtures() -> None:
    """Fixtures document the change shapes this model must classify correctly.

    Each fixture declares the owner or applicability outcome it expects. The
    declared values must be ones the contract actually defines, so a fixture
    cannot drift into asserting a vocabulary that no longer exists.
    """
    assert FIXTURES.is_dir(), "tests/fixtures/assurance/ must exist"

    fixtures = sorted(FIXTURES.glob("*.md"), key=lambda p: p.as_posix())
    assert len(fixtures) >= 6, "expected positive and negative assurance fixtures"

    valid_owners = {"analyze", "critic", "verify", "pr-review"}
    saw_applicable = False
    saw_not_applicable = False
    saw_analyze_owned = False
    saw_critic_owned = False

    for fixture in fixtures:
        text = _read(fixture)
        name = fixture.name

        assert "expected_owner:" in text, f"{name} must declare expected_owner"
        owner = text.split("expected_owner:", 1)[1].split("\n", 1)[0].strip()
        assert owner in valid_owners, f"{name} declares unknown owner {owner!r}"
        saw_analyze_owned |= owner == "analyze"
        saw_critic_owned |= owner == "critic"

        assert "expected_applicable:" in text, f"{name} must declare expected_applicable"
        applicable = text.split("expected_applicable:", 1)[1].split("\n", 1)[0].strip()
        assert applicable in {"true", "false"}, f"{name} declares unknown applicability {applicable!r}"

        signals = text.split("signals:", 1)[1].split("\n", 1)[0].strip()
        if applicable == "true":
            saw_applicable = True
            declared = [s.strip() for s in signals.strip("[]").split(",") if s.strip()]
            assert declared, f"{name} is applicable but declares no signal"
            for signal in declared:
                assert signal in APPLICABILITY_SIGNALS, (
                    f"{name} declares signal {signal!r} that the contract does not define"
                )
        else:
            saw_not_applicable = True
            assert signals.strip("[]").strip() == "", (
                f"{name} is a negative control but declares signals"
            )

    assert saw_applicable, "need at least one applicable fixture"
    assert saw_not_applicable, "need at least one negative control fixture"
    assert saw_analyze_owned, "need at least one Analyze-owned fixture"
    assert saw_critic_owned, "need at least one Critic-owned fixture"


def validate_scope_authority() -> None:
    """No path turns a finding into work without Judge or human authority."""
    tasks = _read(ROOT / "templates" / "commands" / "tasks.md")
    analyze = _read(ANALYZE)
    address = _read(ROOT / "templates" / "commands" / "address-pr-review.md")

    # Tasks is derivative: six forcing sources and a PLANNING GAP stop.
    assert "Derivative Contract" in tasks
    for source in ("requirement", "design decision", "verification obligation", "constitution obligation",
                   "Knowledge ownership update", "approved Judge remediation"):
        assert source in tasks, source
    for mechanism in ("endpoint", "cache", "persisted record", "dependency", "rollback design"):
        assert mechanism in tasks, mechanism
    assert "PLANNING GAP" in tasks and "`/devspark-plan` revise" in tasks
    assert "agent: devspark-planning-review" in tasks and "agent: devspark-implement" not in tasks

    # Legacy merge cannot promote ordinary observations.
    assert "Medium and Low findings are never auto-selected" in tasks
    assert "execution_mode: selective` findings are selected" not in tasks

    # Analyze distinguishes justified support from new architecture.
    assert "Unsupported mechanism" in analyze and "justified support" in analyze
    assert "not a path allowlist" in analyze

    # PR remediation selects only helper-derived eligibility; fixes are evidence.
    assert "auto_eligible: true" in address
    assert "`CON` findings route to `/devspark-evolve-constitution`" in address
    assert "suggested fix is evidence" in address and "`--auto` never grants it" in address
    assert "select `all` open findings" not in address


def validate_shift_left_constitution_contract() -> None:
    specify = " ".join(_read(ROOT / "templates" / "commands" / "specify.md").split())
    clarify = _read(ROOT / "templates" / "commands" / "clarify.md")
    plan = _read(ROOT / "templates" / "commands" / "plan.md")
    analyze = _read(ANALYZE)
    exception = SPEC145_EXTERNAL_DEPENDENCY_EXCEPTION
    contradictory = (
        "Build an API that calls Azure OpenAI. To reduce logging volume, prohibit per-attempt "
        "Kusto telemetry, including retries. Record only a single aggregate event per conversation."
    )
    negative_control = "Limit unrelated internal debug logging without prohibiting required dependency-attempt telemetry."

    assert "MUST log each call attempt to Kusto regardless of outcome" in exception
    assert "including retries" in exception and "prohibit per-attempt Kusto telemetry" in contradictory
    assert "prohibit per-attempt Kusto telemetry" not in negative_control
    for prompt in (specify, clarify):
        assert "complete applicable MUST/SHOULD text" in prompt or "complete applicable MUST/SHOULD" in prompt
        assert "embedded exceptions" in prompt or "exceptions" in prompt
        assert "Do not repeat the check for unchanged requirements" in prompt or "Recheck changed requirements only" in prompt
    assert "before proceeding with the affected behavior" in specify
    assert "Before closing the clarification" in clarify
    assert "In the existing pre-design Constitution Check" in plan
    assert "complete applicable principle text, including embedded exceptions and scope" in plan
    assert "repeat the same focused check after design changes" in plan
    assert "This is part of the existing check, not another gate" in plan
    assert "Independently compare the authored requirements with the full applicable MUST/SHOULD text" in analyze
    assert "do not rely on Specify, Clarify, or Plan having passed" in analyze
    assert "Constitution conflicts are automatically CRITICAL" in analyze


def test_authoring_prompts_compare_changed_requirements_to_full_constitution_clause() -> None:
    validate_shift_left_constitution_contract()


def test_critic_preserves_raw_execution_evidence_without_reopening_planning() -> None:
    critic = " ".join(_read(ROOT / "templates" / "commands" / "critic.md").split())
    for phrase in (
        "implementation does not refresh them",
        "within the approved Plan surface",
        "does not by itself require Critic to rerun",
        "Verify and PR Review retain",
        "An out-of-surface or governance change",
    ):
        assert phrase in critic


def main() -> None:
    validate_canonical_contract_exists()
    validate_single_owner_invariant()
    validate_lane_separation()
    validate_no_metadata_self_policing()
    validate_evidence_requirement()
    validate_lifecycle_boundary()
    validate_deduplication_rules()
    validate_finding_quality_bar()
    validate_uncertainty_is_not_a_defect()
    validate_bounded_passes()
    validate_single_convergence_model()
    validate_derived_verdict()
    validate_applicability_model()
    validate_signals_are_repository_agnostic()
    validate_interaction_policy()
    validate_analyze_hardened_passes()
    validate_risk_checklist_resolution_path()
    validate_fixtures()
    validate_scope_authority()
    validate_shift_left_constitution_contract()

    print("Assurance contract validated.")


if __name__ == "__main__":
    main()
