"""Contracts for the single DevSpark knowledge engine and its companion scripts."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ENGINE = "build_knowledge_index.py"
SCRIPTS = (ENGINE, "explain-context.py", "migrate-knowledge-to-entities.py")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")


def _consumer(tmp_path: Path) -> Path:
    """A consumer repository with the engine installed under .devspark/scripts/."""
    repo = tmp_path / "repo"
    for name in SCRIPTS:
        target = repo / ".devspark" / "scripts" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / "scripts" / name, target)
    _write(repo / "src" / "auth.py", "def refresh_token():\n    return 'token'\n")
    _write(repo / "tests" / "test_auth.py", "def test_refresh():\n    assert True\n")
    _write(
        repo / ".knowledge" / "entities" / "auth" / "_entity.yaml",
        """\
        id: auth
        name: Authentication
        kind: knowledge-model
        summary: Token refresh and session handling.
        constrained_by:
        - auth-strategy
        evidence:
        - type: test
          ref: tests/test_auth.py
          verified_by: execution
        """,
    )
    _write(
        repo / ".knowledge" / "entities" / "auth" / "architecture.md",
        """\
        ---
        aliases:
        - login
        source_of_truth:
        - src/auth.py
        last_verified: '2026-09-01'
        ---

        # Authentication Architecture

        Tokens refresh before expiry.
        """,
    )
    _write(
        repo / ".knowledge" / "governance" / "decisions" / "auth-strategy.md",
        """\
        ---
        id: auth-strategy
        type: governance-decision
        title: Auth Strategy
        constrains:
        - auth
        last_verified: '2026-09-01'
        evidence:
        - type: test
          ref: tests/test_auth.py
          verified_by: execution
        ---

        # Auth Strategy

        We refresh tokens proactively; we do not rely on retry-on-401.
        """,
    )
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    return repo


def _engine(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(repo / ".devspark" / "scripts" / ENGINE), "--root", str(repo), *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )


def _codes(result: subprocess.CompletedProcess[str]) -> set[str]:
    return {line.split(": ")[1] for line in result.stdout.splitlines() if line.startswith(("error: ", "warning: "))}


def test_default_mode_writes_json_outputs_and_check_never_writes(tmp_path: Path) -> None:
    repo = _consumer(tmp_path)
    ontology = repo / ".knowledge" / "ontology"

    stale = _engine(repo, "--check")
    assert stale.returncode == 1
    assert not (ontology / "index.json").exists(), "--check must never write"

    written = _engine(repo)
    assert written.returncode == 0, written.stdout + written.stderr
    index = json.loads((ontology / "index.json").read_text(encoding="utf-8"))
    coverage = json.loads((ontology / "coverage.json").read_text(encoding="utf-8"))
    assert index["decisions"][0]["constrains"] == ["auth"]
    assert index["entities"][0]["constrained_by"] == ["auth-strategy"]
    assert coverage["summary"]["errors"] == 0
    assert not list(ontology.glob("*.generated.md"))
    assert "Tokens refresh" not in (ontology / "index.json").read_text(encoding="utf-8"), "body prose stays out of index.json"

    assert _engine(repo, "--check").returncode == 0
    assert _engine(repo, "--write").returncode == 2, "there is no --write flag"


def test_constrains_and_constrained_by_must_reciprocate(tmp_path: Path) -> None:
    repo = _consumer(tmp_path)
    entity = repo / ".knowledge" / "entities" / "auth" / "_entity.yaml"
    entity.write_text(entity.read_text(encoding="utf-8").replace("constrained_by:\n- auth-strategy\n", ""), encoding="utf-8")
    result = _engine(repo)
    assert result.returncode == 1
    assert "missing-constrained-by" in _codes(result)

    _write(
        repo / ".knowledge" / "entities" / "billing" / "_entity.yaml",
        """\
        id: billing
        name: Billing
        kind: knowledge-model
        summary: Invoices.
        constrained_by:
        - auth-strategy
        evidence:
        - type: test
          ref: tests/test_auth.py
          verified_by: execution
        """,
    )
    assert "missing-constrains" in _codes(_engine(repo))


def test_banned_lifecycle_keys_and_decision_topic_rules(tmp_path: Path) -> None:
    repo = _consumer(tmp_path)
    decisions = repo / ".knowledge" / "governance" / "decisions"
    text = (decisions / "auth-strategy.md").read_text(encoding="utf-8")
    (decisions / "auth-strategy.md").write_text(text.replace("type: governance-decision\n", "type: governance-decision\nstatus: current\n"), encoding="utf-8")
    (decisions / "0002-auth-strategy.md").write_text(
        text.replace("id: auth-strategy", "id: 0002-auth-strategy"), encoding="utf-8"
    )
    codes = _codes(_engine(repo))
    assert "banned-lifecycle-key" in codes
    assert "sequential-decision-name" in codes
    assert "duplicate-decision-topic" in codes


def test_evidence_is_required_but_fallback_reason_only_warns(tmp_path: Path) -> None:
    repo = _consumer(tmp_path)
    entity = repo / ".knowledge" / "entities" / "auth" / "_entity.yaml"
    original = entity.read_text(encoding="utf-8")
    entity.write_text(
        original.replace(
            "- type: test\n  ref: tests/test_auth.py\n  verified_by: execution\n",
            "- type: code\n  ref: src/auth.py\n  verified_by: inspection\n",
        ),
        encoding="utf-8",
    )
    warned = _engine(repo)
    assert warned.returncode == 0, warned.stdout
    assert "inspection-without-fallback" in _codes(warned)

    entity.write_text(original.split("evidence:")[0], encoding="utf-8")
    missing = _engine(repo)
    assert missing.returncode == 1
    assert "missing-evidence" in _codes(missing)


def test_subfolder_documents_require_the_currency_pair(tmp_path: Path) -> None:
    repo = _consumer(tmp_path)
    assert _engine(repo).returncode == 0
    guide = repo / ".knowledge" / "entities" / "auth" / "guides" / "rotation.md"
    _write(guide, "# Rotation Guide\n")
    result = _engine(repo)
    assert result.returncode == 1
    assert {"missing-source-of-truth", "missing-last-verified"} <= _codes(result)
    guide.write_text("---\nsource_of_truth:\n- src/auth.py\nlast_verified: '2026-09-01'\n---\n\n# Rotation Guide\n", encoding="utf-8")
    assert _engine(repo).returncode == 0


def test_permanent_knowledge_cannot_cite_ephemeral_work(tmp_path: Path) -> None:
    repo = _consumer(tmp_path)
    _write(repo / ".devspark.work" / "specs" / "001-auth" / "spec.md", "# Spec\n")
    doc = repo / ".knowledge" / "entities" / "auth" / "architecture.md"
    doc.write_text(doc.read_text(encoding="utf-8").replace("- src/auth.py", "- .devspark.work/specs/001-auth/spec.md"), encoding="utf-8")
    assert "ephemeral-reference" in _codes(_engine(repo))


def test_entity_scope_limits_the_error_gate(tmp_path: Path) -> None:
    repo = _consumer(tmp_path)
    _write(
        repo / ".knowledge" / "entities" / "billing" / "_entity.yaml",
        "id: billing\nname: Billing\nkind: knowledge-model\nsummary: Invoices.\n",
    )
    assert _engine(repo).returncode == 1
    assert _engine(repo, "--check", "--entity", "auth").returncode == 0
    assert _engine(repo, "--check", "--entity", "billing").returncode == 1


def test_search_weights_each_class_once_per_term(tmp_path: Path) -> None:
    repo = _consumer(tmp_path)
    entity_dir = repo / ".knowledge" / "entities" / "auth"
    one = "\n".join(["---", "source_of_truth:", "- src/auth.py", "last_verified: '2026-09-01'", "---", "", "# One", "", "## Rotation", ""])
    many = "\n".join(["---", "source_of_truth:", "- src/auth.py", "last_verified: '2026-09-01'", "---", "", "# Many", ""] + ["## Rotation step"] * 10)
    (entity_dir / "one.md").write_text(one, encoding="utf-8")
    (entity_dir / "many.md").write_text(many, encoding="utf-8")

    result = _engine(repo, "--search", "rotation", "--limit", "0")
    assert result.returncode == 0, result.stderr
    ranked = {item["path"].rsplit("/", 1)[-1]: item for item in json.loads(result.stdout)["results"]}
    assert ranked["one.md"]["score"] == ranked["many.md"]["score"] == 30
    heading = [match for match in ranked["many.md"]["matched_on"] if match["class"] == "heading"][0]
    assert heading["occurrences"] == 10 and heading["weight"] == 30

    alias = json.loads(_engine(repo, "--search", "login").stdout)["results"][0]
    assert alias["path"].endswith("auth/architecture.md")
    assert alias["matched_on"][0]["class"] == "alias"


def test_explain_context_adds_body_search_at_query_time(tmp_path: Path) -> None:
    repo = _consumer(tmp_path)
    assert _engine(repo).returncode == 0
    script = repo / ".devspark" / "scripts" / "explain-context.py"
    result = subprocess.run(
        [sys.executable, str(script), "--root", str(repo), "expiry"],
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["body_searched"] is True
    top = payload["results"][0]
    assert top["path"].endswith("auth/architecture.md")
    assert [match["class"] for match in top["matched_on"]] == ["body"]
    assert _engine(repo, "--search", "expiry").stdout.count('"path"') == 0


def test_pinned_claim_drift_detection(tmp_path: Path) -> None:
    repo = _consumer(tmp_path)
    pinned = _engine(repo, "--pin-claim", "src/auth.py")
    assert pinned.returncode == 0, pinned.stderr
    claim = json.loads(pinned.stdout)
    assert claim["verification"] == {"state": "unverified"}, "the engine never asserts human verification"
    assert (repo / claim["baseline"]).is_file()

    claim["verification"] = {"state": "verified"}
    doc = repo / ".knowledge" / "entities" / "auth" / "architecture.md"
    doc.write_text(
        doc.read_text(encoding="utf-8").replace("- src/auth.py\n", "- " + json.dumps(claim) + "\n"),
        encoding="utf-8",
    )
    assert _engine(repo).returncode == 0

    assert _engine(repo, "--detect-drift").returncode == 2, "drift needs an explicit scope"
    current = json.loads(_engine(repo, "--detect-drift", "--full-inventory").stdout)
    assert [item["state"] for item in current["claims"]] == ["current"]
    assert current["human_verification_asserted"] is False

    (repo / "src" / "auth.py").write_text("def refresh_token():\n    return 'rotated'\n", encoding="utf-8")
    report = _engine(repo, "--detect-drift", "--full-inventory")
    assert report.returncode == 0, "last-verified enforcement reports drift without failing"
    drifted = json.loads(report.stdout)["claims"][0]
    assert drifted["state"] == "drifted"
    assert "+    return 'rotated'" in drifted["diff"]

    _write(repo / ".knowledge" / "knowledge.config.yaml", "knowledge_drift:\n  enforcement: pinned-claims\n")
    assert _engine(repo, "--detect-drift", "--full-inventory").returncode == 1


def test_git_scoped_drift_only_evaluates_changed_paths(tmp_path: Path) -> None:
    repo = _consumer(tmp_path)
    claim = json.loads(_engine(repo, "--pin-claim", "src/auth.py").stdout)
    doc = repo / ".knowledge" / "entities" / "auth" / "architecture.md"
    doc.write_text(doc.read_text(encoding="utf-8").replace("- src/auth.py\n", "- " + json.dumps(claim) + "\n"), encoding="utf-8")
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]
    subprocess.run([*git, "add", "-A"], cwd=repo, check=True)
    subprocess.run([*git, "commit", "-qm", "base"], cwd=repo, check=True)
    (repo / "README.md").write_text("unrelated\n", encoding="utf-8")
    subprocess.run([*git, "add", "-A"], cwd=repo, check=True)
    subprocess.run([*git, "commit", "-qm", "head"], cwd=repo, check=True)

    report = json.loads(_engine(repo, "--detect-drift", "--base", "HEAD~1").stdout)
    assert report["mode"] == "git-scope"
    assert report["claims"] == []


def test_migration_converts_legacy_layout_and_is_idempotent(tmp_path: Path) -> None:
    repo = _consumer(tmp_path)
    knowledge = repo / ".knowledge"
    entity = knowledge / "entities" / "auth" / "_entity.yaml"
    entity.write_text(entity.read_text(encoding="utf-8").replace("constrained_by:\n- auth-strategy\n", "lifecycle: current\n"), encoding="utf-8")
    _write(knowledge / "entities" / "auth" / "_derived.yaml", "constrained_by:\n- auth-strategy\ngenerated_by: x\n")
    _write(
        knowledge / "governance" / "decisions" / "auth-strategy.md",
        """\
        ---
        id: auth-strategy
        status: current
        governs:
        - auth
        evidence:
        - type: test
          ref: tests/test_auth.py
          verified_by: execution
        ---

        # Auth Strategy
        """,
    )
    _write(knowledge / "entities" / "auth" / "architecture.md", "# Authentication\n")
    _write(knowledge / "ontology" / "coverage.generated.md", "# old\n")

    migrate = [sys.executable, str(repo / ".devspark" / "scripts" / "migrate-knowledge-to-entities.py"), "--root", str(repo)]
    first = subprocess.run(migrate, text=True, capture_output=True, check=True)
    assert "delete .knowledge/entities/auth/_derived.yaml" in first.stdout
    assert _engine(repo).returncode == 0, _engine(repo).stdout
    assert _engine(repo, "--check").returncode == 0

    second = subprocess.run(migrate, text=True, capture_output=True, check=True)
    assert "changed 0 file(s)" in second.stdout


def test_decision_errors_gate_only_the_entities_they_constrain(tmp_path: Path) -> None:
    repo = _consumer(tmp_path)
    _write(
        repo / ".knowledge" / "entities" / "billing" / "_entity.yaml",
        """\
        id: billing
        name: Billing
        kind: knowledge-model
        summary: Invoices.
        constrained_by:
        - billing-policy
        evidence:
        - type: test
          ref: tests/test_auth.py
          verified_by: execution
        """,
    )
    _write(
        repo / ".knowledge" / "entities" / "billing" / "architecture.md",
        "---\nsource_of_truth:\n- src/auth.py\nlast_verified: '2026-09-01'\n---\n\n# Billing\n",
    )
    _write(
        repo / ".knowledge" / "governance" / "decisions" / "billing-policy.md",
        "---\nid: billing-policy\ntype: governance-decision\ntitle: Billing Policy\n"
        "constrains:\n- billing\nlast_verified: '2026-09-01'\n---\n\n# Billing Policy\n",
    )
    result = _engine(repo)
    assert "missing-evidence" in _codes(result)
    assert _engine(repo, "--check", "--entity", "auth").returncode == 0
    assert _engine(repo, "--check", "--entity", "billing").returncode == 1


def test_engine_writes_never_delete_pinned_baselines(tmp_path: Path) -> None:
    repo = _consumer(tmp_path)
    claim = json.loads(_engine(repo, "--pin-claim", "src/auth.py").stdout)
    baseline = repo / claim["baseline"]

    written = _engine(repo)
    assert written.returncode == 0, written.stdout
    assert baseline.is_file(), "a freshly pinned baseline must survive an engine write"
    assert "orphan-baseline" in _codes(written)


@pytest.mark.skipif(shutil.which("bash") is None or sys.platform == "win32", reason="requires POSIX bash")
def test_bash_resolver_prefers_framework_copy_and_reports_legacy(tmp_path: Path) -> None:
    repo = _consumer(tmp_path)

    def resolve() -> str:
        command = f'source "{ROOT}/scripts/bash/common.sh"; knowledge_engine_json "{repo}"'
        return subprocess.run(["bash", "-c", command], text=True, capture_output=True, check=True).stdout

    assert json.loads(resolve()) == {"engine": ".devspark/scripts/build_knowledge_index.py", "legacy_copies": []}
    legacy = repo / ".devspark" / "scripts" / "python" / ENGINE
    legacy.parent.mkdir(parents=True)
    shutil.copy(ROOT / "scripts" / ENGINE, legacy)
    assert json.loads(resolve())["legacy_copies"] == [".devspark/scripts/python/build_knowledge_index.py"]

    shutil.rmtree(repo / ".devspark")
    (repo / "scripts").mkdir()
    shutil.copy(ROOT / "scripts" / ENGINE, repo / "scripts" / ENGINE)
    assert json.loads(resolve()) == {"engine": "scripts/build_knowledge_index.py", "legacy_copies": []}


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="requires PowerShell 7")
def test_powershell_resolver_prefers_framework_copy_and_reports_legacy(tmp_path: Path) -> None:
    repo = _consumer(tmp_path)
    common = ROOT / "scripts" / "powershell" / "common.ps1"

    def resolve() -> dict:
        command = f". '{common}'; Get-KnowledgeEngineInfo -RepoRoot '{repo}' | ConvertTo-Json -Compress"
        result = subprocess.run(["pwsh", "-NoProfile", "-Command", command], text=True, capture_output=True, check=True)
        return json.loads(result.stdout)

    assert resolve() == {"engine": ".devspark/scripts/build_knowledge_index.py", "legacy_copies": []}
    legacy = repo / ".devspark" / "scripts" / "python" / ENGINE
    legacy.parent.mkdir(parents=True)
    shutil.copy(ROOT / "scripts" / ENGINE, legacy)
    assert resolve()["legacy_copies"] == [".devspark/scripts/python/build_knowledge_index.py"]

    shutil.rmtree(repo / ".devspark")
    (repo / "scripts").mkdir()
    shutil.copy(ROOT / "scripts" / ENGINE, repo / "scripts" / ENGINE)
    assert resolve() == {"engine": "scripts/build_knowledge_index.py", "legacy_copies": []}


def test_resolver_is_paired_and_used_by_every_entry_point() -> None:
    bash_common = (ROOT / "scripts/bash/common.sh").read_text(encoding="utf-8")
    ps_common = (ROOT / "scripts/powershell/common.ps1").read_text(encoding="utf-8")
    assert "resolve_knowledge_engine()" in bash_common
    assert "function Resolve-KnowledgeEngine" in ps_common
    for candidate in (".devspark/scripts/build_knowledge_index.py", "scripts/build_knowledge_index.py"):
        assert candidate in bash_common
        assert candidate in ps_common

    for name in ("explain-context", "site-audit", "create-pr", "get-pr-context", "release-context"):
        bash = (ROOT / f"scripts/bash/{name}.sh").read_text(encoding="utf-8")
        powershell = (ROOT / f"scripts/powershell/{name}.ps1").read_text(encoding="utf-8")
        assert "resolve_knowledge_engine" in bash or "knowledge_engine_json" in bash, name
        assert "Resolve-KnowledgeEngine" in powershell or "Get-KnowledgeEngineInfo" in powershell, name
    assert not (ROOT / "scripts" / "python").exists(), "one engine, one location"


def test_flat_nodes_follow_currency_rules_and_are_searchable(tmp_path: Path) -> None:
    repo = _consumer(tmp_path)
    guide = repo / ".knowledge" / "guides" / "local-setup.md"
    _write(guide, "# Local Setup\n\nRun the service locally.\n")
    missing = _engine(repo)
    assert missing.returncode == 1
    assert "missing-source-of-truth" in _codes(missing)

    guide.write_text(
        "---\nsource_of_truth:\n- src/auth.py\nlast_verified: '2026-09-01'\n---\n\n# Local Setup\n",
        encoding="utf-8",
    )
    assert _engine(repo).returncode == 0
    coverage = json.loads((repo / ".knowledge" / "ontology" / "coverage.json").read_text(encoding="utf-8"))
    assert coverage["flat_nodes"] == [{"id": "local-setup", "path": ".knowledge/guides/local-setup.md"}]
    top = json.loads(_engine(repo, "--search", "local setup").stdout)["results"][0]
    assert top["path"] == ".knowledge/guides/local-setup.md"

    _write(repo / ".knowledge" / "auth.md", "---\nsource_of_truth:\n- src/auth.py\nlast_verified: '2026-09-01'\n---\n\n# Auth\n")
    assert "duplicate-node-id" in _codes(_engine(repo)), "flat ids may not collide with entity ids"


def test_links_references_must_resolve(tmp_path: Path) -> None:
    repo = _consumer(tmp_path)
    doc = repo / ".knowledge" / "entities" / "auth" / "architecture.md"
    base = doc.read_text(encoding="utf-8")
    doc.write_text(base.replace("aliases:", "links:\n  references:\n  - auth-strategy\n  - src/auth.py\n  - https://example.com/rfc\naliases:"), encoding="utf-8")
    ok = _engine(repo)
    assert ok.returncode == 0, ok.stdout
    index = json.loads((repo / ".knowledge" / "ontology" / "index.json").read_text(encoding="utf-8"))
    layer = [item for item in index["documents"] if item["path"].endswith("auth/architecture.md")][0]
    assert layer["references"] == ["auth-strategy", "src/auth.py", "https://example.com/rfc"]

    doc.write_text(base.replace("aliases:", "links:\n  references:\n  - billing\n  - .devspark.work/specs/001-auth\naliases:"), encoding="utf-8")
    codes = _codes(_engine(repo))
    assert {"dangling-reference", "ephemeral-reference"} <= codes


def test_migration_reports_conflicts_and_needs_force(tmp_path: Path) -> None:
    repo = _consumer(tmp_path)
    knowledge = repo / ".knowledge"
    entity = knowledge / "entities" / "auth" / "_entity.yaml"
    entity.write_text("# Owned by the platform team\n" + entity.read_text(encoding="utf-8") + "lifecycle: current\n", encoding="utf-8")
    decision = knowledge / "governance" / "decisions" / "auth-strategy.md"
    decision.write_text(
        decision.read_text(encoding="utf-8").replace("constrains:\n- auth\n", "constrains:\n- auth\ngoverns:\n- billing\n"),
        encoding="utf-8",
    )
    migrate = [sys.executable, str(repo / ".devspark" / "scripts" / "migrate-knowledge-to-entities.py"), "--root", str(repo)]

    blocked = subprocess.run(migrate, text=True, capture_output=True, check=False)
    assert blocked.returncode == 1
    assert "conflict .knowledge/entities/auth/_entity.yaml: YAML comments would be lost" in blocked.stdout
    assert "conflict .knowledge/governance/decisions/auth-strategy.md: `governs` and `constrains` disagree" in blocked.stdout
    assert entity.read_text(encoding="utf-8").startswith("# Owned by the platform team"), "conflicting files are untouched"
    assert "governs:" in decision.read_text(encoding="utf-8")

    forced = subprocess.run([*migrate, "--force"], text=True, capture_output=True, check=False)
    assert forced.returncode == 0, forced.stdout + forced.stderr
    assert "lifecycle" not in entity.read_text(encoding="utf-8")
    assert "governs" not in decision.read_text(encoding="utf-8")


def test_drive_letter_paths_are_local_refs_not_urls() -> None:
    sys.dont_write_bytecode = True
    import importlib.util

    spec = importlib.util.spec_from_file_location("engine_under_test", ROOT / "scripts" / ENGINE)
    engine = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = engine
    spec.loader.exec_module(engine)
    assert engine.is_external("https://example.com/rfc")
    assert engine.is_external("mailto:team@example.com")
    assert not engine.is_external("C:/repo/src/auth.py")
    assert not engine.is_external("c:\\repo\\src\\auth.py")
