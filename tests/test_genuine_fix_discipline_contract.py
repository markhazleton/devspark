"""Contract tests for Genuine Fix Discipline command surfaces."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_command_preamble_contains_section_9_contract() -> None:
    text = _read("templates/command-preamble-contract.md")
    assert "## 9. Genuine Fix Discipline" in text
    assert "### 9.1 Intent Cues" in text
    assert "### 9.2 Constitution Citation Hook" in text
    assert "intent_cue" in text
    assert "JavaScript, TypeScript, C#, and Java" in text
    assert "behavioral intent" in text
    assert "metric" in text


def test_required_commands_reference_genuine_fix_guidance() -> None:
    for rel_path in (
        "templates/commands/implement.md",
        "templates/commands/quickfix.md",
        "templates/commands/pr-review.md",
        "templates/commands/address-pr-review.md",
    ):
        text = _read(rel_path)
        assert "Genuine Fix Discipline" in text
        assert "templates/command-preamble-contract.md" in text
        assert "§9" in text


def test_findings_require_intent_fields() -> None:
    analyze = _read("templates/commands/analyze.md")
    critic = _read("templates/commands/critic.md")
    site_audit = _read("templates/commands/site-audit.md")

    assert "intent_cue: <behavioral intent that must be repaired or preserved>" in analyze
    assert "intent_cue: <behavioral intent that must be repaired or preserved>" in critic
    assert "**Intent**" in site_audit
    assert "| Issue | Intent |" in site_audit


def test_verify_command_and_atomic_shim_define_guard() -> None:
    verify = _read("templates/commands/verify.md")
    shim = _read("templates/prompts/atomic/verify.md")

    assert "Genuine Fix Guard" in verify
    assert "metric-only" in verify
    assert "unchanged behavior" in verify
    assert "status: fail" in verify
    assert "legacy_command: verify" in shim
    assert "templates/commands/verify.md" in shim


def test_constitution_surfaces_genuine_fix_principle() -> None:
    command = _read("templates/commands/constitution.md")
    constitution = _read(".documentation/memory/constitution.md")
    contract = _read(".documentation/specs/001-okf-genuine-fix/contracts/genuine-fix-discipline.md")

    assert "Genuine Fix Discipline" in command
    assert "behavioral intent before metric movement" in command
    assert "### IX. Genuine Fix Discipline (MUST)" in constitution
    assert "**Version**: 1.5.0" in constitution
    assert "v1.4.0 → v1.5.0" in constitution
    assert "Approval: the user requested" in contract
    assert "Migration plan: existing features remain valid" in contract


def test_verify_is_discoverable_through_atomic_catalog() -> None:
    shim = _read("templates/prompts/atomic/verify.md")
    assert "id: verify" in shim
    assert "exposed: false" in shim
    assert "category: legacy-command" in shim
    assert "legacy_command: verify" in shim


def test_release_packagers_ship_genuine_fix_surfaces() -> None:
    bash_packager = _read(".github/workflows/scripts/create-release-packages.sh")
    ps_packager = _read(".github/workflows/scripts/create-release-packages.ps1")

    assert "templates" in bash_packager
    assert "templates" in ps_packager
    assert "templates[/\\\\]commands" in ps_packager
    assert "Copy-Item -Path \"scripts/bash\"" in ps_packager
    assert "Copy-Item -Path \"scripts/powershell\"" in ps_packager


def test_docs_list_verify_and_genuine_fix_contracts() -> None:
    readme = _read("README.md")
    templates_readme = _read("templates/README.md")
    changelog = _read("CHANGELOG.md")

    assert "/devspark.verify" in readme
    assert "29 active commands" in templates_readme
    assert "command-preamble-contract.md" in templates_readme
    assert "okf-knowledge-document.schema.json" in templates_readme
    assert "Genuine Fix Discipline" in changelog
