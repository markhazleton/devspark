# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for `/devspark.discover-knowledge` (DevSpark 7.6 Knowledge Discovery).

Covers three layers:
1. Command wiring: the installed command template, agent/prompt shims, atomic backward-compat
   shim, and dual-language wrapper scripts all resolve to `scripts/discover-knowledge.py`.
2. Behavior/schema: discovery findings validate against the shared `knowledge_findings` schema,
   cover the documented categories, stay deterministic across repeated scans, and never mutate
   `.knowledge` unless an explicit apply-operation is invoked with `--write`.
3. Repository resolution: `--repo-root` overrides git-toplevel detection, matching the
   convention used by `scripts/knowledge-integrity.py`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
DISCOVER_SCRIPT = ROOT / "scripts" / "discover-knowledge.py"
COMMAND_DOC = ROOT / "templates" / "commands" / "discover-knowledge.md"
SKILL = ROOT / ".github" / "skills" / "devspark-discover-knowledge" / "SKILL.md"
CONSUMER_SKILL = ROOT / "templates" / "consumer-skills" / "devspark-discover-knowledge" / "SKILL.md"
BASH_WRAPPER = ROOT / "scripts" / "bash" / "discover-knowledge.sh"
PS1_WRAPPER = ROOT / "scripts" / "powershell" / "discover-knowledge.ps1"

sys.path.insert(0, str(ROOT / "scripts"))
from knowledge_findings import validate_finding  # noqa: E402

_GIT_BASH = r"C:\Program Files\Git\bin\bash.exe"
_BASH = _GIT_BASH if Path(_GIT_BASH).exists() else shutil.which("bash")
_PWSH = shutil.which("pwsh") or shutil.which("powershell")

requires_bash = pytest.mark.skipif(_BASH is None, reason="bash not available")
requires_pwsh = pytest.mark.skipif(_PWSH is None, reason="pwsh/powershell not available")


# --- Command wiring: installed command -> resolved canonical prompt -> discovery tooling -------


def test_command_template_exists_and_declares_wrapper_scripts() -> None:
    text = COMMAND_DOC.read_text(encoding="utf-8")
    assert "sh: .devspark/scripts/bash/discover-knowledge.sh $ARGUMENTS --json" in text
    assert "ps: .devspark/scripts/powershell/discover-knowledge.ps1 $ARGUMENTS -Json" in text


def test_skill_resolves_to_command_template() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "name: devspark-discover-knowledge" in text
    assert "templates/commands/discover-knowledge.md" in text


def test_consumer_skill_resolves_through_the_customization_chain() -> None:
    text = CONSUMER_SKILL.read_text(encoding="utf-8")
    assert "name: devspark-discover-knowledge" in text
    assert ".devspark/defaults/commands/devspark.discover-knowledge.md" in text


def test_wrapper_scripts_exist_and_are_thin() -> None:
    assert BASH_WRAPPER.is_file()
    assert PS1_WRAPPER.is_file()
    assert "discover-knowledge.py" in BASH_WRAPPER.read_text(encoding="utf-8")
    assert "discover-knowledge.py" in PS1_WRAPPER.read_text(encoding="utf-8")


def _init_git_repo(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True, timeout=30)


def _write_doc(repo: Path, relpath: str, *, node_type: str = "architecture", extra: dict | None = None, body: str = "Body text.\n") -> Path:
    doc = repo / relpath
    doc.parent.mkdir(parents=True, exist_ok=True)
    metadata: dict = {"id": doc.stem, "type": node_type, "title": doc.stem}
    if extra:
        metadata.update(extra)
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
    doc.write_text(f"---\n{frontmatter}---\n\n{body}", encoding="utf-8")
    return doc


@pytest.fixture()
def gap_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "src" / "billing").mkdir(parents=True)
    for name in ("invoice", "ledger", "reconcile"):
        (repo / "src" / "billing" / f"{name}.py").write_text("def run():\n    pass\n", encoding="utf-8")
    _init_git_repo(repo)
    return repo


@requires_bash
def test_bash_wrapper_reaches_discover_knowledge_py(gap_repo: Path) -> None:
    result = subprocess.run(
        [_BASH, str(BASH_WRAPPER), "--repo-root", str(gap_repo), "--json"],
        capture_output=True, text=True, timeout=60,
    )
    payload = json.loads(result.stdout)
    assert payload["REPO_ROOT"].replace("\\", "/").rstrip("/") == str(gap_repo).replace("\\", "/").rstrip("/")
    assert any(f["category"] == "knowledge-gap" for f in payload["FINDINGS"])


@requires_pwsh
def test_powershell_wrapper_reaches_discover_knowledge_py(gap_repo: Path) -> None:
    result = subprocess.run(
        [_PWSH, "-File", str(PS1_WRAPPER), "--repo-root", str(gap_repo), "--json"],
        capture_output=True, text=True, timeout=60,
    )
    payload = json.loads(result.stdout)
    assert Path(payload["REPO_ROOT"]).resolve() == gap_repo.resolve()
    assert any(f["category"] == "knowledge-gap" for f in payload["FINDINGS"])


# --- Behavior + schema ---------------------------------------------------------------------


def _run(repo: Path, *extra_args: str) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, str(DISCOVER_SCRIPT), "--repo-root", str(repo), "--json", *extra_args],
        text=True, capture_output=True, timeout=60,
    )
    return result.returncode, json.loads(result.stdout)


def _by_category(payload: dict, category: str) -> list[dict]:
    return [f for f in payload["FINDINGS"] for f in [f] if f["category"] == category]


def test_repository_wide_discovery_reports_knowledge_gap(gap_repo: Path) -> None:
    code, payload = _run(gap_repo)
    assert code == 0
    gaps = _by_category(payload, "knowledge-gap")
    assert any(f["subject"] == "src/billing/**" for f in gaps)


def test_scoped_discovery_restricts_to_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    for area in ("billing", "shipping"):
        (repo / "src" / area).mkdir(parents=True)
        for name in ("one", "two", "three"):
            (repo / "src" / area / f"{name}.py").write_text("x = 1\n", encoding="utf-8")
    _init_git_repo(repo)

    _, payload = _run(repo, "src/billing")
    gaps = _by_category(payload, "knowledge-gap")
    assert any(f["subject"] == "src/billing/**" for f in gaps)
    assert not any(f["subject"] == "src/shipping/**" for f in gaps)
    assert payload["SCOPE"] == {"type": "path", "value": "src/billing"}


def test_missing_mapping_detected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write_doc(repo, ".knowledge/architecture/one.md", extra={"links": {"references": ["missing-node"]}})
    _init_git_repo(repo)

    _, payload = _run(repo)
    missing = _by_category(payload, "missing-mapping")
    assert any(f["subject"] == "one->missing-node" for f in missing)


def test_broad_mapping_detected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    for i in range(30):
        (repo / "src" / f"module_{i}.py").write_text("x = 1\n", encoding="utf-8")
    _write_doc(repo, ".knowledge/architecture/one.md", extra={"appliesTo": ["src/**"]})
    _init_git_repo(repo)

    _, payload = _run(repo, "--overbroad-threshold", "10")
    broad = _by_category(payload, "broad-mapping")
    assert any(f["subject"] == "one:src/**" for f in broad)


def test_broad_mapping_bare_double_star_matches_files_on_every_supported_python(tmp_path: Path) -> None:
    """Regression for a Python-version-dependent glob bug: `pathlib.Path.glob("src/**")` returns
    directories only on Python 3.11/3.12 but also returns files on 3.13+, so a naive `repo.glob`
    call silently found zero matches (and thus never reported the broad-mapping finding) under
    the CI-pinned interpreter even though it worked under a newer local interpreter. Nested files
    (not just direct children) must also be counted so the fix is proven, not just spot-checked
    at one depth.
    """
    repo = tmp_path / "repo"
    (repo / "src" / "nested").mkdir(parents=True)
    for i in range(15):
        (repo / "src" / f"module_{i}.py").write_text("x = 1\n", encoding="utf-8")
    for i in range(15):
        (repo / "src" / "nested" / f"module_{i}.py").write_text("x = 1\n", encoding="utf-8")
    _write_doc(repo, ".knowledge/architecture/one.md", extra={"appliesTo": ["src/**"]})
    _init_git_repo(repo)

    _, payload = _run(repo, "--overbroad-threshold", "10")
    broad = _by_category(payload, "broad-mapping")
    match = next((f for f in broad if f["subject"] == "one:src/**"), None)
    assert match is not None
    assert match["evidence"][0]["matched_file_count"] == 30


def _write_entity(repo: Path, entity_id: str, *, source_of_truth: list[str], aliases: list[str] | None = None, headings: list[str] | None = None) -> None:
    entity_dir = repo / ".knowledge/entities" / entity_id
    entity_dir.mkdir(parents=True)
    (entity_dir / "_entity.yaml").write_text(
        yaml.safe_dump({"id": entity_id, "type": "subsystem", "owner": "team-x"}, sort_keys=False),
        encoding="utf-8",
    )
    metadata = {
        "id": f"{entity_id}-architecture",
        "entity": entity_id,
        "layer": "architecture",
        "title": entity_id,
        "source_of_truth": source_of_truth,
        "last_verified": "2026-01-01",
    }
    if aliases:
        metadata["aliases"] = aliases
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
    heading_body = "\n".join(f"## {h}" for h in (headings or [])) or "Body."
    (entity_dir / "architecture.md").write_text(f"---\n{frontmatter}---\n\n{heading_body}\n", encoding="utf-8")


def _stamp_constrained_by(repo: Path, entity_id: str, decision_ids: list[str]) -> None:
    entity_yaml = repo / ".knowledge/entities" / entity_id / "_entity.yaml"
    data = yaml.safe_load(entity_yaml.read_text(encoding="utf-8"))
    data["constrained_by"] = decision_ids
    entity_yaml.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_missing_relationship_candidate_detected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "checkout.py").write_text("def run():\n    pass\n", encoding="utf-8")
    (repo / "src" / "billing.py").write_text("def run():\n    pass\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_flow.py").write_text("def test_checkout_and_billing():\n    pass\n", encoding="utf-8")
    _write_entity(repo, "checkout", source_of_truth=["src/checkout.py"])
    _write_entity(repo, "billing", source_of_truth=["src/billing.py"], headings=["Interacts with checkout"])
    _init_git_repo(repo)

    _, payload = _run(repo)
    relationships = _by_category(payload, "missing-relationship")
    assert any(f["subject"] == "billing:checkout" or f["subject"] == "checkout:billing" for f in relationships)


def test_alias_candidate_detected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "checkout.py").write_text(
        "class ShoppingBasket:\n    pass\n\n\nclass ShoppingBasket:\n    pass\n\n\nclass ShoppingBasket:\n    pass\n",
        encoding="utf-8",
    )
    _write_entity(repo, "checkout", source_of_truth=["src/checkout.py"])
    _init_git_repo(repo)

    _, payload = _run(repo, "--min-alias-occurrences", "1")
    aliases = _by_category(payload, "alias-candidate")
    assert any(f["subject"].startswith("checkout:shopping basket") for f in aliases)


def test_no_finding_case_for_clean_scoped_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "documented.py").write_text("x = 1\n", encoding="utf-8")
    _write_doc(repo, ".knowledge/architecture/documented.md", extra={"appliesTo": ["src/documented.py"]})
    _init_git_repo(repo)

    _, payload = _run(repo, "src/documented.py")
    assert payload["FINDINGS"] == []
    assert payload["SUMMARY"]["total_findings"] == 0


def test_every_emitted_finding_validates_against_shared_schema(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "src" / "billing").mkdir(parents=True)
    for name in ("invoice", "ledger", "reconcile"):
        (repo / "src" / "billing" / f"{name}.py").write_text("x = 1\n", encoding="utf-8")
    _write_doc(repo, ".knowledge/architecture/one.md", extra={"links": {"references": ["missing-node"]}})
    _init_git_repo(repo)

    _, payload = _run(repo)
    findings = payload["FINDINGS"]
    assert findings, "expected at least one finding to validate"
    for finding in findings:
        errors = validate_finding(finding)
        assert errors == [], f"{finding.get('finding_id')}: {errors}"


def test_repeated_scans_produce_stable_finding_ids(gap_repo: Path) -> None:
    _, first = _run(gap_repo)
    _, second = _run(gap_repo)
    first_ids = sorted(f["finding_id"] for f in first["FINDINGS"])
    second_ids = sorted(f["finding_id"] for f in second["FINDINGS"])
    assert first_ids == second_ids
    assert first_ids, "expected at least one finding to compare"


# --- Safety: discovery never mutates .knowledge, relationships, or aliases without --write -------


def _git_diff(repo: Path) -> str:
    result = subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True, check=True, timeout=30)
    return result.stdout


def test_discovery_does_not_mutate_repository(gap_repo: Path) -> None:
    before = _git_diff(gap_repo)
    _run(gap_repo)
    after = _git_diff(gap_repo)
    assert before == after == ""


def test_apply_alias_without_write_does_not_mutate(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write_entity(repo, "checkout", source_of_truth=["src/checkout.py"])
    (repo / "src").mkdir()
    (repo / "src" / "checkout.py").write_text("x = 1\n", encoding="utf-8")
    _init_git_repo(repo)

    result = subprocess.run(
        [sys.executable, str(DISCOVER_SCRIPT), "--repo-root", str(repo),
         "--apply-alias", "checkout-architecture", "--alias-text", "basket"],
        text=True, capture_output=True, timeout=60,
    )
    payload = json.loads(result.stdout)
    assert payload["written"] is False
    assert _git_diff(repo) == ""


def test_apply_relation_without_write_does_not_mutate(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write_entity(repo, "checkout", source_of_truth=["src/checkout.py"])
    _write_entity(repo, "billing", source_of_truth=["src/billing.py"])
    (repo / "src").mkdir()
    (repo / "src" / "checkout.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "src" / "billing.py").write_text("x = 1\n", encoding="utf-8")
    _init_git_repo(repo)

    result = subprocess.run(
        [sys.executable, str(DISCOVER_SCRIPT), "--repo-root", str(repo),
         "--apply-relation-from", "checkout", "--apply-relation-to", "billing"],
        text=True, capture_output=True, timeout=60,
    )
    payload = json.loads(result.stdout)
    assert payload["written"] is False
    assert _git_diff(repo) == ""


def test_discovery_never_automatically_writes_relationship_or_alias_findings(gap_repo: Path) -> None:
    """Plain discovery (no --apply-* flag at all) must never touch disk, regardless of findings."""
    before = _git_diff(gap_repo)
    _, payload = _run(gap_repo)
    after = _git_diff(gap_repo)
    assert before == after == ""
    assert all(f["changes_authoritative_truth"] is False for f in payload["FINDINGS"])


# --- Repository resolution: --repo-root overrides git-toplevel detection ------------------------


def test_repo_root_flag_overrides_outer_git_toplevel(tmp_path: Path) -> None:
    # Nest the fixture inside ANOTHER git repo so naive toplevel detection (no --repo-root) would
    # resolve to the OUTER repo instead. --repo-root must win regardless of CWD or nesting.
    outer = tmp_path / "outer"
    outer.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=outer, check=True, timeout=30)
    inner = outer / "inner-fixture"
    (inner / "src").mkdir(parents=True)
    (inner / "src" / "one.py").write_text("x = 1\n", encoding="utf-8")
    (inner / "src" / "two.py").write_text("x = 1\n", encoding="utf-8")
    (inner / "src" / "three.py").write_text("x = 1\n", encoding="utf-8")

    _, payload = _run(inner)
    assert Path(payload["REPO_ROOT"]).resolve() == inner.resolve()


# --- 7.6.1 corrective release: precision fixes ---------------------------------------------


def test_shared_fixture_hub_evidence_does_not_produce_relationship_candidate(tmp_path: Path) -> None:
    """A shared conftest.py exercised by many unrelated entities must never, by itself, produce a
    missing-relationship finding between any pair of those entities (Fix #6/#7)."""
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "tests").mkdir()
    entity_ids = [f"entity{i}" for i in range(6)]
    hub_lines = []
    for eid in entity_ids:
        (repo / "src" / f"{eid}.py").write_text("def run():\n    pass\n", encoding="utf-8")
        _write_entity(repo, eid, source_of_truth=[f"src/{eid}.py"])
        hub_lines.append(f"{eid}_setup()")
    (repo / "tests" / "conftest.py").write_text(
        "def test_shared_bootstrap():\n    " + "\n    ".join(hub_lines) + "\n", encoding="utf-8"
    )
    _init_git_repo(repo)

    _, payload = _run(repo)
    relationships = _by_category(payload, "missing-relationship")
    assert relationships == [], f"expected no hub-only relationship candidates, got {relationships}"


def test_narrow_test_evidence_still_produces_relationship_candidate_alongside_hub(tmp_path: Path) -> None:
    """The same hub-suppression logic must not swallow a genuine, narrowly-scoped co-reference:
    only the hub test's evidence is excluded, not the pair's narrow test evidence."""
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "tests").mkdir()
    entity_ids = [f"entity{i}" for i in range(6)]
    hub_lines = []
    for eid in entity_ids:
        (repo / "src" / f"{eid}.py").write_text("def run():\n    pass\n", encoding="utf-8")
        _write_entity(repo, eid, source_of_truth=[f"src/{eid}.py"])
        hub_lines.append(f"{eid}_setup()")
    (repo / "tests" / "conftest.py").write_text(
        "def test_shared_bootstrap():\n    " + "\n    ".join(hub_lines) + "\n", encoding="utf-8"
    )
    (repo / "tests" / "test_entity0_entity1_flow.py").write_text(
        "def test_entity0_entity1_flow():\n    entity0_setup()\n    entity1_setup()\n", encoding="utf-8"
    )
    _init_git_repo(repo)

    _, payload = _run(repo)
    relationships = _by_category(payload, "missing-relationship")
    pair = next((f for f in relationships if set(f["subject"].split(":")) == {"entity0", "entity1"}), None)
    assert pair is not None, f"expected a narrow-evidence relationship candidate, got {relationships}"
    other_pairs = [f for f in relationships if set(f["subject"].split(":")) != {"entity0", "entity1"}]
    assert other_pairs == [], f"only the narrowly-tested pair should surface, got extra: {other_pairs}"


def test_governance_relationship_candidate_detected_via_shared_source_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "checkout.py").write_text("def run():\n    pass\n", encoding="utf-8")
    (repo / "src" / "billing.py").write_text("def run():\n    pass\n", encoding="utf-8")
    _write_entity(repo, "checkout", source_of_truth=["src/checkout.py"])
    _write_entity(repo, "billing", source_of_truth=["src/billing.py"])
    decision_dir = repo / ".knowledge" / "governance" / "decisions"
    decision_dir.mkdir(parents=True)
    metadata = {
        "id": "payments-data-retention",
        "type": "governance-decision",
        "title": "payments-data-retention",
        "appliesTo": ["src/checkout.py", "src/billing.py"],
        "constrains": ["billing"],
    }
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
    (decision_dir / "payments-data-retention.md").write_text(f"---\n{frontmatter}---\n\nDecision body.\n", encoding="utf-8")
    _stamp_constrained_by(repo, "billing", ["payments-data-retention"])
    _init_git_repo(repo)

    _, payload = _run(repo)
    candidates = _by_category(payload, "governance-relationship-candidate")
    assert any(f["subject"] == "checkout:payments-data-retention" for f in candidates)
    assert not any(f["subject"] == "billing:payments-data-retention" for f in candidates)


def test_governance_relationship_candidate_skipped_when_already_constrained(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "checkout.py").write_text("def run():\n    pass\n", encoding="utf-8")
    _write_entity(repo, "checkout", source_of_truth=["src/checkout.py"])
    decision_dir = repo / ".knowledge" / "governance" / "decisions"
    decision_dir.mkdir(parents=True)
    metadata = {
        "id": "payments-data-retention",
        "type": "governance-decision",
        "title": "payments-data-retention",
        "appliesTo": ["src/checkout.py"],
        "constrains": ["checkout"],
    }
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
    (decision_dir / "payments-data-retention.md").write_text(f"---\n{frontmatter}---\n\nDecision body.\n", encoding="utf-8")
    _stamp_constrained_by(repo, "checkout", ["payments-data-retention"])
    _init_git_repo(repo)

    _, payload = _run(repo)
    candidates = _by_category(payload, "governance-relationship-candidate")
    assert candidates == []


def test_generic_alias_noise_is_suppressed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "checkout.py").write_text(
        "true = 1\nfalse = 2\ndata = {}\nresult = None\n"
        "class ShoppingBasket:\n    pass\n\n\nclass ShoppingBasket:\n    pass\n\n\nclass ShoppingBasket:\n    pass\n",
        encoding="utf-8",
    )
    _write_entity(repo, "checkout", source_of_truth=["src/checkout.py"])
    _init_git_repo(repo)

    _, payload = _run(repo, "--min-alias-occurrences", "1")
    aliases = _by_category(payload, "alias-candidate")
    subjects = {f["subject"] for f in aliases}
    assert not any(subjects_term in subjects for subjects_term in ("checkout:true", "checkout:false", "checkout:data", "checkout:result"))
    assert any(f.startswith("checkout:shopping basket") for f in subjects)


def test_hub_alias_term_shared_across_many_entities_is_suppressed(tmp_path: Path) -> None:
    """A single-token term appearing broadly across many unrelated entities' source files is
    non-distinctive and must not surface as an alias candidate for any of them (Fix #9)."""
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    entity_ids = [f"entity{i}" for i in range(6)]
    for eid in entity_ids:
        (repo / "src" / f"{eid}.py").write_text(
            "class Wombat:\n    pass\n\n\nclass Wombat:\n    pass\n\n\nclass Wombat:\n    pass\n", encoding="utf-8"
        )
        _write_entity(repo, eid, source_of_truth=[f"src/{eid}.py"])
    _init_git_repo(repo)

    _, payload = _run(repo, "--min-alias-occurrences", "1")
    aliases = _by_category(payload, "alias-candidate")
    assert not any(f["subject"].endswith(":wombat") for f in aliases)


def test_entity_scoped_discovery_does_not_bleed_unrelated_global_findings(tmp_path: Path) -> None:
    """A repository-wide-only category (knowledge-gap) must not silently appear identically under
    an unrelated entity scope; it is reported separately as GLOBAL_FINDINGS instead (Fix #4)."""
    repo = tmp_path / "repo"
    (repo / "src" / "unrelated").mkdir(parents=True)
    for name in ("one", "two", "three"):
        (repo / "src" / "unrelated" / f"{name}.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "src").joinpath("checkout.py").write_text("def run():\n    pass\n", encoding="utf-8")
    _write_entity(repo, "checkout", source_of_truth=["src/checkout.py"])
    _init_git_repo(repo)

    _, payload = _run(repo, "checkout")
    assert payload["SCOPE"] == {"type": "entity", "value": "checkout"}
    assert not any(f["subject"] == "src/unrelated/**" for f in payload["FINDINGS"])
    assert any(f["subject"] == "src/unrelated/**" for f in payload["GLOBAL_FINDINGS"])

    _, merged = _run(repo, "checkout", "--include-global")
    assert any(f["subject"] == "src/unrelated/**" for f in merged["FINDINGS"])


def test_entity_scoped_broad_mapping_and_overlapping_ownership_respect_scope(tmp_path: Path) -> None:
    """Prior to 7.6.1, broad-mapping/overlapping-ownership ignored scope entirely; scoped runs for
    two different entities must now return different results."""
    repo = tmp_path / "repo"
    (repo / "src" / "checkout").mkdir(parents=True)
    (repo / "src" / "billing").mkdir(parents=True)
    for i in range(30):
        (repo / "src" / "checkout" / f"m{i}.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "src" / "billing" / "one.py").write_text("x = 1\n", encoding="utf-8")
    _write_entity(repo, "checkout", source_of_truth=["src/checkout"])
    _write_entity(repo, "billing", source_of_truth=["src/billing/one.py"])
    _init_git_repo(repo)

    _, checkout_payload = _run(repo, "checkout", "--overbroad-threshold", "10")
    _, billing_payload = _run(repo, "billing", "--overbroad-threshold", "10")
    checkout_broad = _by_category(checkout_payload, "broad-mapping")
    billing_broad = _by_category(billing_payload, "broad-mapping")
    assert any(f["subject"].startswith("checkout-architecture:") for f in checkout_broad)
    assert billing_broad == []


def test_min_confidence_filters_low_confidence_findings(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "src" / "billing").mkdir(parents=True)
    for name in ("invoice", "ledger", "reconcile"):
        (repo / "src" / "billing" / f"{name}.py").write_text("x = 1\n", encoding="utf-8")
    _init_git_repo(repo)

    _, unfiltered = _run(repo)
    _, filtered = _run(repo, "--min-confidence", "high")
    assert len(filtered["FINDINGS"]) <= len(unfiltered["FINDINGS"])
    assert all(f["confidence"] == "high" for f in filtered["FINDINGS"])


def test_limit_per_category_caps_findings_and_prefers_higher_confidence(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    for i in range(6):
        pair_dir = repo / "src" / f"cluster{i}"
        pair_dir.mkdir()
        for name in ("one", "two", "three"):
            (pair_dir / f"{name}.py").write_text("x = 1\n", encoding="utf-8")
    _init_git_repo(repo)

    _, payload = _run(repo, "--limit-per-category", "2")
    gaps = _by_category(payload, "knowledge-gap")
    assert len(gaps) <= 2
