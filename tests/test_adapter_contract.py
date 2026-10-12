# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Adapter contract tests for the write-spec skill integration.

Verifies:
  (a) templates/commands/specify.md references the write-spec skill.
  (b) The three named adapter input variables appear in both specify.md
      delegation block and ADAPTER-contract.md (machine-verifiable variable
      contract; variable names are part of the versioned contract surface).
  (c) specify.md does not duplicate the drafting procedure inline.
"""
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


class TestAdapterVariableContract:
    """Assert the three named adapter input variables appear in ADAPTER-contract.md.

    Variable names are part of the versioned contract surface and must be
    machine-verifiable in both the contract document and specify.md's
    delegation block.
    """

    def test_feature_description_in_adapter_contract(self):
        content = ADAPTER_CONTRACT.read_text(encoding="utf-8")
        assert "$FEATURE_DESCRIPTION" in content, (
            "ADAPTER-contract.md must reference $FEATURE_DESCRIPTION"
        )

    def test_constitution_path_in_adapter_contract(self):
        content = ADAPTER_CONTRACT.read_text(encoding="utf-8")
        assert "$CONSTITUTION_PATH" in content, (
            "ADAPTER-contract.md must reference $CONSTITUTION_PATH"
        )

    def test_prior_spec_summary_in_adapter_contract(self):
        content = ADAPTER_CONTRACT.read_text(encoding="utf-8")
        assert "$PRIOR_SPEC_SUMMARY" in content, (
            "ADAPTER-contract.md must reference $PRIOR_SPEC_SUMMARY"
        )

    def test_adapter_variables_in_specify_delegation_block(self):
        content = SPECIFY_MD.read_text(encoding="utf-8")
        missing = [v for v in ADAPTER_VARIABLES if v not in content]
        assert not missing, (
            f"specify.md delegation block is missing adapter variables: {missing}"
        )

    def test_specify_does_not_duplicate_drafting_procedure(self):
        content = SPECIFY_MD.read_text(encoding="utf-8")
        # After 2D refactor, the inline drafting steps 1-8 must not appear.
        # The old inline procedure contained this specific text that is now removed.
        inline_procedure_marker = "Parse user description from Input"
        assert inline_procedure_marker not in content, (
            "specify.md must not contain the old inline drafting procedure after 2D refactor"
        )


class TestSpecifyReferencesSkill:
    """Assert specify.md references the write-spec skill."""

    def test_specify_references_write_spec(self):
        content = SPECIFY_MD.read_text(encoding="utf-8")
        assert "write-spec" in content, (
            "specify.md must reference the write-spec skill after 2D refactor"
        )
