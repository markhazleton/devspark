"""Contract tests for optional participant metadata and terminology.

These tests protect the phase-one participant vocabulary decision:
``agent`` remains an AI runtime/client integration, while ``participant`` is
the advisory team-member concept carried only in documentation artifacts.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent

DOC_PATHS = [
    ROOT / "README.md",
    ROOT / ".documentation" / "implementation-lifecycle.md",
    ROOT / ".documentation" / "constitution-guide.md",
    ROOT / "templates" / "README.md",
]

LIFECYCLE_TEMPLATE_PATHS = [
    ROOT / "templates" / "spec-template.md",
    ROOT / "templates" / "quick-spec-template.md",
    ROOT / "templates" / "plan-template.md",
    ROOT / "templates" / "tasks-template.md",
]

ROLE_NAMES = {"owner", "planner", "implementer", "reviewer", "critic", "scribe"}
KINDS = {"human", "ai"}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def frontmatter_and_body(path: Path) -> tuple[dict, str]:
    text = read(path)
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("---", 2)
    assert len(parts) == 3, f"{path} has malformed frontmatter"
    return yaml.safe_load(parts[1]) or {}, parts[2].lstrip()


def participants_from(path: Path) -> dict:
    frontmatter, _ = frontmatter_and_body(path)
    participants = frontmatter.get("participants")
    assert isinstance(participants, dict), f"{path} must include participants metadata"
    return participants


def test_existing_artifacts_without_participants_metadata_remain_valid() -> None:
    sample_without_participants = """---
classification: full-spec
risk_level: medium
target_workflow: specify-full
required_artifacts: spec, plan, tasks
recommended_next_step: plan
required_gates: checklist, analyze, critic
---

# Feature Specification: Existing Artifact
"""
    frontmatter = yaml.safe_load(sample_without_participants.split("---", 2)[1])
    assert "participants" not in frontmatter

    contract = read(ROOT / "templates" / "spec-validation-contract.md").lower()
    assert "participants" in contract
    assert "optional" in contract
    assert "must not fail" in contract or "not fail" in contract


def test_stock_docs_reserve_agent_for_runtime_integrations() -> None:
    combined = "\n".join(read(path) for path in DOC_PATHS).lower()
    assert "agent" in combined
    assert "ai runtime" in combined or "runtime/client integration" in combined
    assert "agents-registry.json" in combined
    assert "participant" in combined
    assert "team member" in combined or "team-member" in combined
    assert "agent as a team member" not in combined
    assert "agents are participants" not in combined


def test_participant_metadata_examples_avoid_pii_and_runtime_behavior() -> None:
    combined = "\n".join(read(path) for path in [*LIFECYCLE_TEMPLATE_PATHS, ROOT / "templates" / "spec-validation-contract.md"]).lower()

    assert "personally identifying information" in combined
    assert "artifact-only" in combined or "advisory" in combined
    assert "silent" in combined or "command output" in combined

    forbidden_recommendations = [
        "recommended to store personal",
        "recommend storing personal",
        "required name",
        "participant routing",
        "participant inheritance",
        "participant override",
        "print participant",
    ]
    assert not [phrase for phrase in forbidden_recommendations if phrase in combined]


def test_readme_defines_required_glossary_terms() -> None:
    readme = read(ROOT / "README.md").lower()
    for term in ["prompt", "agent", "skill", "participant", "role"]:
        pattern = rf"\*\*{re.escape(term)}\*\*"
        assert re.search(pattern, readme), f"README glossary must define {term}"

    assert "workflow command surface" in readme
    assert "ai runtime or client integration" in readme
    assert "portable capability package" in readme
    assert "human or ai-filled team member" in readme
    assert "responsibility label" in readme


def test_customization_resolution_layers_remain_documented() -> None:
    readme = read(ROOT / "README.md")
    assert "**3-tier prompt resolution**" in readme
    assert ".documentation/{git-user}/commands/" in readme
    assert ".documentation/commands/" in readme
    assert ".devspark/defaults/commands/" in readme
    assert "**2-tier script resolution**" in readme
    assert ".documentation/scripts/" in readme
    assert ".devspark/scripts/" in readme


def test_participant_guidance_does_not_add_override_or_inheritance_model() -> None:
    combined = "\n".join(read(path) for path in DOC_PATHS).lower()
    assert "participant override" not in combined
    assert "participant inheritance" not in combined
    assert "upstream participant" not in combined
    assert "new customization layer" not in combined
    assert "customization layers and precedence are unchanged" in combined


def test_lifecycle_templates_include_optional_participants_metadata() -> None:
    for path in LIFECYCLE_TEMPLATE_PATHS:
        participants = participants_from(path)
        assert ROLE_NAMES <= set(participants)
        for role, value in participants.items():
            if isinstance(value, str):
                assert value in KINDS, f"{path} participant {role} has invalid kind"
                continue
            assert isinstance(value, dict), f"{path} participant {role} must be string or map"
            assert value.get("kind") in KINDS
            assert "name" not in value, f"{path} stock examples must avoid personal names"


def test_plan_template_body_heading_survives_frontmatter() -> None:
    _, body = frontmatter_and_body(ROOT / "templates" / "plan-template.md")
    first_heading = next(line for line in body.splitlines() if line.startswith("#"))
    assert first_heading == "# Implementation Plan: [FEATURE]"


def test_spec_validation_contract_documents_nonblocking_participants() -> None:
    contract = read(ROOT / "templates" / "spec-validation-contract.md").lower()
    assert "participants" in contract
    assert "optional advisory metadata" in contract
    assert "absence" in contract
    assert "must not fail" in contract or "must not block" in contract
