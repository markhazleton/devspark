#!/usr/bin/env python3
"""Contract checks for artifact version provenance, verify applicability, and route escalation.

Run directly (exit 0 = pass). `tests/test_contract_scripts.py` collects this file
automatically because it defines no `def test_` functions.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PREAMBLE = REPO / "templates" / "command-preamble-contract.md"
PROVENANCE_MODULE = REPO / "templates" / "preamble" / "provenance.md"
CONVERGENCE_MODULE = REPO / "templates" / "preamble" / "convergence.md"
VERIFICATION = REPO / "templates" / "verification-contract.md"
CLOSEOUT = REPO / "templates" / "closeout-contract.md"
QUICKFIX = REPO / "templates" / "commands" / "quickfix.md"
SPECIFY = REPO / "templates" / "commands" / "specify.md"
VERIFY_CMD = REPO / "templates" / "commands" / "verify.md"
PHILOSOPHY = REPO / ".knowledge" / "governance" / "devspark-philosophy.md"
COMMON_PS1 = REPO / "scripts" / "powershell" / "common.ps1"
COMMON_SH = REPO / "scripts" / "bash" / "common.sh"
FIXTURES = REPO / "tests" / "fixtures" / "provenance"

PROVENANCE_FIELD = "devspark_version"

# Artifacts whose template frontmatter must offer the provenance field.
AUTHORED_ARTIFACTS = [
    REPO / "templates" / "spec-template.md",
    REPO / "templates" / "quick-spec-template.md",
    REPO / "templates" / "plan-template.md",
    REPO / "templates" / "tasks-template.md",
]

# Gate artifact shapes that must carry per-instance provenance.
GATE_SHAPES = [
    (REPO / "templates" / "commands" / "analyze.md", "gate: analyze"),
    (REPO / "templates" / "commands" / "critic.md", "gate: critic"),
    (REPO / "templates" / "commands" / "quickfix.md", "gate: quickfix"),
    (REPO / "templates" / "commands" / "pr-review.md", "gate: pr-review"),
    (VERIFICATION, "gate: verify"),
    (CLOSEOUT, "gate: closeout"),
]

# The verify-sensitive change-shape vocabulary. Small, general, and technology-neutral.
VERIFY_SHAPES = [
    "runtime-configuration",
    "environment-dependent-behavior",
    "external-contract",
    "datastore-semantics",
    "mock-substituted-behavior",
    "deployment-state-assumption",
    "behavior-preservation-claim",
    "output-shape-contract",
    "defect-recurrence",
]

PROOF_MODES = [
    "snapshot-neutral",
    "golden",
    "regression-pinned",
    "shadow-agreement",
    "end-to-end",
]

ESCALATION_SIGNALS = [
    "architectural contract",
    "cross-subsystem dependency",
    "governance or constitution change",
    "public contract change",
    "persistent schema change",
    "security or trust-boundary issue",
    "unrelated remediation concerns",
]

# Counting metrics the historical audit showed to be misleading proxies for assurance quality.
FORBIDDEN_METRICS = [
    "finding_count",
    "task_count",
    "test_count",
    "spec_size",
    "command_count",
]


def read(path: Path) -> str:
    assert path.exists(), f"missing required file: {path.relative_to(REPO)}"
    return path.read_text(encoding="utf-8")


def frontmatter(text: str) -> str:
    assert text.startswith("---\n"), "expected YAML frontmatter"
    return text.split("---\n", 2)[1]


def validate_canonical_version_helper() -> None:
    """One version lookup, with a twin in each shell (Constitution Principle VI)."""
    ps1 = read(COMMON_PS1)
    sh = read(COMMON_SH)

    assert "function Get-DevSparkVersion" in ps1, "common.ps1 must define Get-DevSparkVersion"
    assert "get_devspark_version()" in sh, "common.sh must define get_devspark_version"

    # Both read the same canonical stamp, and both degrade to `unknown` rather than guessing.
    for text, label in ((ps1, "common.ps1"), (sh, "common.sh")):
        assert ".devspark/VERSION" in text, f"{label} must read the canonical stamp"
        assert "unknown" in text, f"{label} must fall back to `unknown`"

    # Revision is optional and separately obtained -- never required for provenance.
    assert "IncludeRevision" in ps1, "PowerShell helper must make revision opt-in"
    assert "get_devspark_revision()" in sh, "Bash twin must expose revision separately"


def validate_provenance_contract() -> None:
    body = read(PROVENANCE_MODULE)

    assert "## 12. Artifact Version Provenance" in body, "the provenance module must state the convention once"
    assert "Get-DevSparkVersion" in body and "get_devspark_version" in body, (
        "the contract must point at the shared helper so no prompt invents version detection"
    )

    # Artifact-local, not a central ledger.
    for forbidden in ("planned_with:", "analyzed_with:", "verified_with:"):
        assert forbidden in body, (
            f"the contract must explicitly prohibit {forbidden} accumulation in the spec"
        )
    assert "lifecycle ledger" in body

    # The two meanings of the one field name.
    assert "authored" in body
    assert "this specific instance" in body

    # Truthfulness: upgrades and later phases must not restamp.
    assert "does not rewrite existing artifacts" in body
    assert "never restamps an earlier artifact" in body

    # Backward compatibility is non-optional.
    assert "additive" in body
    assert "remain valid" in body
    assert "no historical artifact is migrated" in body

    # The reason the field exists at all.
    assert "infer from repository history only as a fallback" in body


def validate_authored_artifact_provenance() -> None:
    for path in AUTHORED_ARTIFACTS:
        fm = frontmatter(read(path))
        assert f"{PROVENANCE_FIELD}:" in fm, (
            f"{path.relative_to(REPO)} frontmatter must offer {PROVENANCE_FIELD}"
        )
        # Authored artifacts describe who wrote them, not who later touched them.
        assert "authored" in fm.split(f"{PROVENANCE_FIELD}:")[1].split("\n", 1)[0]


def validate_gate_artifact_provenance() -> None:
    for path, marker in GATE_SHAPES:
        body = read(path)
        assert marker in body, f"{path.relative_to(REPO)} must still declare `{marker}`"
        block = body.split(marker, 1)[1][:400]
        assert f"{PROVENANCE_FIELD}:" in block, (
            f"{path.relative_to(REPO)} `{marker}` shape must record {PROVENANCE_FIELD}"
        )
        # Convergence-loop observability: repeated runs must be distinguishable.
        assert "generated:" in block, (
            f"{path.relative_to(REPO)} `{marker}` shape must record a generation timestamp"
        )


def validate_no_centralized_ledger() -> None:
    """Provenance must not grow into a run database or a metrics subsystem."""
    for path in (PREAMBLE, PROVENANCE_MODULE, VERIFICATION, PHILOSOPHY):
        body = read(path)
        for metric in FORBIDDEN_METRICS:
            assert metric not in body, (
                f"{path.relative_to(REPO)} introduces `{metric}` as a tracked measure"
            )

    philosophy = read(PHILOSOPHY)
    assert "not analytics" in philosophy
    assert "are not success" in philosophy, (
        "philosophy must state that counting artifacts is not a success measure"
    )
    assert "more tests is not the right test" in philosophy


def validate_verify_shape_vocabulary() -> None:
    body = read(VERIFICATION)

    assert "## 2.1 When Empirical Proof Is Warranted" in body
    for shape in VERIFY_SHAPES:
        assert f"**{shape}**" in body, f"verification contract omits the `{shape}` shape"

    # Every shape must indicate a mode that already exists -- no new proof machinery.
    section = body.split("## 2.1", 1)[1].split("## 2.2", 1)[0]
    cited = set(re.findall(r"`(" + "|".join(PROOF_MODES) + r")`", section))
    assert cited, "the shape table must indicate existing proof modes"
    assert cited <= set(PROOF_MODES)

    # Shape, not label, is the switch -- and "no shape" is a legitimate answer.
    assert "not of the route label or the authored `risk_level`" in body
    assert "legitimate and common result" in body
    assert "not an engine" in body

    # Generality guard: the vocabulary must not absorb repository-specific technologies.
    assert "Do not extend this table with repository-specific technologies." in body


def validate_verify_decision_is_observable() -> None:
    body = read(VERIFICATION)

    assert "## 2.2 The Applicability Decision Is Reported, Not Hidden" in body
    assert "Empirical verification: REQUIRED" in body
    assert "Empirical verification: NOT REQUIRED" in body
    assert "Classification may be automatic; the reasoning may not be invisible." in body

    # Consequential proof stays a human decision.
    assert "proposed, not assumed" in body
    assert "never hide the commitment" in body

    # The deciding commands are wired to it.
    specify = read(SPECIFY)
    assert "§2.1 of the verification contract" in specify
    assert "observable change shape" in specify

    verify_cmd = read(VERIFY_CMD)
    assert "§2.1" in verify_cmd, "verify must check for an undeclared verify-sensitive shape"
    assert "§2.2" in verify_cmd, "verify must report the applicability decision"


def validate_verify_is_not_mandatory() -> None:
    """The correction is a better decision, not another required ritual."""
    body = read(VERIFICATION)
    assert "makes a mode **recommended**" in body
    assert "declaring it in `required_gates` is what makes it required" in body

    philosophy = read(PHILOSOPHY)
    assert "not universal" in philosophy
    assert "ceremony is what developers route around" in philosophy


def validate_route_escalation() -> None:
    body = read(QUICKFIX)

    assert "### Route Escalation on Discovered Scope" in body
    for signal in ESCALATION_SIGNALS:
        assert signal in body, f"quickfix escalation omits the `{signal}` signal"

    # Conservative by design -- not an automatic conversion.
    assert "Do not convert routinely" in body
    assert "most quickfixes exhibit none of these" in body.lower()

    # The decision belongs to the developer, and both options stay open.
    assert "Continue as quickfix, or promote to a full spec?" in body
    assert "The developer owns that decision." in body

    # The pre-existing effort-based mechanism is preserved, not replaced.
    assert "### Scope Creep Detection" in body


def validate_convergence_preserved() -> None:
    """The existing convergence model stands; history reinforces it."""
    closeout = read(CLOSEOUT)
    assert "gate: closeout" in closeout
    assert "decision: complete" in closeout

    preamble = read(CONVERGENCE_MODULE)
    assert "## 10. Convergence Discipline (finding classification)" in preamble
    assert "discovery alone does not expand the current specification" in preamble

    philosophy = read(PHILOSOPHY)
    assert "the historical evidence is the argument for keeping it" in philosophy


def validate_fixtures() -> None:
    assert FIXTURES.is_dir(), "tests/fixtures/provenance/ must exist"
    files = sorted(p for p in FIXTURES.glob("*.md"))
    assert len(files) >= 3, "expected a fixture per validated behavior"

    kinds = set()
    for path in files:
        text = read(path)
        fm = frontmatter(text)
        kind = fm.split("fixture_kind:", 1)[1].split("\n", 1)[0].strip()
        assert kind in {"provenance", "verify-applicability", "route-escalation"}, (
            f"{path.name} declares unknown fixture_kind `{kind}`"
        )
        kinds.add(kind)

        if kind == "verify-applicability":
            shapes = fm.split("shapes:", 1)[1].split("\n", 1)[0].strip()
            declared = [s for s in re.findall(r"[a-z-]+", shapes) if s]
            for shape in declared:
                assert shape in VERIFY_SHAPES, f"{path.name} names unknown shape `{shape}`"

    assert kinds == {"provenance", "verify-applicability", "route-escalation"}, (
        f"fixtures must cover all three validated behaviors; saw {sorted(kinds)}"
    )


def validate_helper_runs() -> None:
    """The Bash helper must actually resolve this repository's own stamp."""
    bash = _find_bash()
    if bash is None:
        return

    script = f'source "{COMMON_SH.as_posix()}"; get_devspark_version "{REPO.as_posix()}"'
    proc = subprocess.run(
        [bash, "-c", script], capture_output=True, text=True, timeout=30, cwd=str(REPO)
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    version = proc.stdout.strip()
    assert re.match(r"^\d+\.\d+\.\d+", version), (
        f"helper did not resolve a semver from the stamp: {version!r}"
    )


def _find_bash() -> str | None:
    # The `bash` on PATH under Windows may be WSL, which cannot read Windows-style repo paths.
    for candidate in (r"C:\Program Files\Git\bin\bash.exe", "/bin/bash"):
        if Path(candidate).exists():
            return candidate
    return None


def main() -> None:
    validate_canonical_version_helper()
    validate_provenance_contract()
    validate_authored_artifact_provenance()
    validate_gate_artifact_provenance()
    validate_no_centralized_ledger()
    validate_verify_shape_vocabulary()
    validate_verify_decision_is_observable()
    validate_verify_is_not_mandatory()
    validate_route_escalation()
    validate_convergence_preserved()
    validate_fixtures()
    validate_helper_runs()
    print("Provenance, verify applicability, and route escalation contracts validated.")


if __name__ == "__main__":
    main()
    sys.exit(0)
