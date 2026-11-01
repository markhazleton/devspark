# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""The universal Specify entry point must not require a spec-drafting adapter."""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
SPECIFY_MD = REPO_ROOT / "templates" / "commands" / "specify.md"
ADAPTER_CONTRACT = REPO_ROOT / "templates" / "skills" / "ADAPTER-contract.md"
SKILL_MD = REPO_ROOT / "templates" / "skills" / "write-spec" / "SKILL.md"

ADAPTER_VARIABLES = [
    "$FEATURE_DESCRIPTION",
    "$CONSTITUTION_PATH",
    "$PRIOR_SPEC_SUMMARY",
]


class TestAdapterContractFiles:
    def test_specify_md_exists(self):
        assert SPECIFY_MD.exists(), f"specify.md not found at {SPECIFY_MD}"

    def test_adapter_contract_exists(self):
        assert ADAPTER_CONTRACT.exists(), (
            f"ADAPTER-contract.md not found at {ADAPTER_CONTRACT}"
        )

    def test_skill_md_exists(self):
        assert SKILL_MD.exists(), (
            f"write-spec/SKILL.md not found at {SKILL_MD}"
        )


class TestUniversalStartContract:
    def test_specify_does_not_delegate_to_spec_drafting_adapter(self):
        content = SPECIFY_MD.read_text(encoding="utf-8")
        assert "write-spec" not in content
        assert not any(variable in content for variable in ADAPTER_VARIABLES)
        assert "--type work" in content and "-Type work" in content
        assert "does not ask the developer to" in content
        assert "work.md" in content

    def test_specify_does_not_duplicate_drafting_procedure(self):
        content = SPECIFY_MD.read_text(encoding="utf-8")
        # After 2D refactor, the inline drafting steps 1-8 must not appear.
        # The old inline procedure contained this specific text that is now removed.
        inline_procedure_marker = "Parse user description from Input"
        assert inline_procedure_marker not in content, (
            "specify.md must not contain the old inline drafting procedure after 2D refactor"
        )

    def test_specify_includes_assurance_discovery_without_a_risk_score(self):
        content = SPECIFY_MD.read_text(encoding="utf-8")
        assert "Perform assurance discovery as part of understanding" in content
        assert "smallest useful activity" in content
        assert "risk-scoring engine" not in content


class TestSpecifyUniversalPath:
    def test_specify_recommends_implementation_without_a_bundle(self):
        content = SPECIFY_MD.read_text(encoding="utf-8")
        assert "smallest useful implementation increment" in content
        assert "No Plan, Tasks, checklist, specification, or review artifact" in content
        assert "applicable mandatory control" in content

    def test_specify_keeps_verification_safeguards_without_a_bundle(self):
        content = " ".join(SPECIFY_MD.read_text(encoding="utf-8").split())
        assert "`verify:snapshot-neutral`" in content
        assert "`verify:golden` and `verify:end-to-end`" in content
        assert "verify-sensitive shape from §2.1" in content
        assert "two-line form of §2.2" in content
        assert "`stage: post-deploy`" in content

    def test_work_route_keeps_verification_safeguards(self):
        implement = (REPO_ROOT / "templates" / "commands" / "implement.md").read_text(encoding="utf-8")
        work_route = " ".join(implement.split("## Work Route (no planning bundle)")[1].split("## Quickfix Route")[0].split())
        assert "`verify:snapshot-neutral`" in work_route
        assert "`verify:golden` and `verify:end-to-end`" in work_route
        assert "§2.1 of the verification contract" in work_route
        assert "acceptance evidence observed and applicable verification reported" in work_route

    def test_specify_names_the_retired_legacy_entry_point(self):
        content = " ".join(SPECIFY_MD.read_text(encoding="utf-8").split())
        assert "Existing v9.3 full-spec and quick-spec bundles remain usable" in content
        assert "DevSpark does not create a **new** full-spec or quick-spec bundle" in content
        assert "temporarily unavailable" not in content
