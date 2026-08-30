"""Contract test: skills surface must be installed by quickstarts and release packaging.

Closes GitHub issues #42, #43, #44 — `templates/skills/` (and specifically the
`write-spec` skill required by `/devspark.specify`) MUST be installed alongside
helper templates and scripts. This test guards against regressions where the
skills directory is omitted from any install, upgrade, or repair surface.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
QUICKSTART_DIR = ROOT / "quickstart"
RELEASE_PACKAGER = ROOT / ".github" / "workflows" / "scripts" / "create-release-packages.sh"
SKILLS_ROOT = ROOT / "templates" / "skills"

REQUIRED_SKILL_FILES = [
    "ADAPTER-contract.md",
    "SKILL-validation-contract.md",
    "write-spec/SKILL.md",
    "write-spec/scripts/gather-context.ps1",
    "write-spec/scripts/gather-context.sh",
    "write-spec/references/spec-template.md",
]

QUICKSTART_FILES = [
    QUICKSTART_DIR / "devspark_quickstart_claudecode.md",
    QUICKSTART_DIR / "devspark_quickstart_codex.md",
    QUICKSTART_DIR / "devspark_quickstart_copilot.md",
    QUICKSTART_DIR / "devspark_quickstart_cursor.md",
    QUICKSTART_DIR / "devspark_quickstart_generic.md",
]


def test_skill_source_files_exist() -> None:
    """The skill files referenced by quickstarts must actually exist in the source repo."""
    for rel in REQUIRED_SKILL_FILES:
        assert (SKILLS_ROOT / rel).is_file(), f"Source skill file missing: templates/skills/{rel}"


@pytest.mark.parametrize("quickstart", QUICKSTART_FILES, ids=lambda p: p.name)
def test_quickstart_installs_skills(quickstart: Path) -> None:
    """Every quickstart guide must include a Step that fetches templates/skills/ into .devspark/templates/skills/."""
    assert quickstart.is_file(), f"Quickstart not found: {quickstart}"
    text = quickstart.read_text(encoding="utf-8")

    assert ".devspark/templates/skills/" in text, (
        f"{quickstart.name} does not reference .devspark/templates/skills/ — "
        "skills won't be installed (regression of #42/#43/#44)."
    )
    assert "templates/skills/write-spec/SKILL.md" in text, (
        f"{quickstart.name} does not fetch the write-spec SKILL.md — "
        "/devspark.specify will silently degrade after install."
    )
    assert "Pull Agent Skills" in text or "Agent Skill" in text, (
        f"{quickstart.name} is missing a dedicated Agent Skills install step."
    )


def test_release_packager_copies_skills() -> None:
    """create-release-packages.sh must copy templates/skills/ into release ZIPs."""
    text = RELEASE_PACKAGER.read_text(encoding="utf-8")
    # Current implementation copies via a templates-recursive copy that excludes
    # only templates/commands/ and vscode-settings.json — that path implicitly
    # includes templates/skills/. Guard against a future filter that would
    # exclude skills.
    assert "templates/skills" not in text or "-not -path \"templates/skills" not in text, (
        "create-release-packages.sh appears to exclude templates/skills/ from release ZIPs."
    )
    # And confirm the templates copy block is still present.
    assert "templates" in text and "DEVSPARK_DIR" in text, (
        "create-release-packages.sh no longer copies templates/ — skills will not ship."
    )
