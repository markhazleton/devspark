"""Contract tests for Agent Skills under templates/skills/.

Discovers every directory under templates/skills/ that contains a SKILL.md,
parses its YAML frontmatter using yaml.safe_load() (SafeLoader avoids YAML 1.1
boolean surprises), and asserts all rules from SKILL-validation-contract.md.

Includes a deliberate-violation fixture set to confirm each rule fails correctly.
"""
import re
import textwrap
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent
SKILLS_DIR = REPO_ROOT / "templates" / "skills"

PROHIBITED_KEYS = {
    "handoffs",
    "scripts",
    "classification",
    "required_gates",
    "recommended_next_step",
    "version",
}

PROHIBITED_BODY_STRINGS = [
    ".devspark/",
    "{SCRIPT}",
    "FEATURE_DIR",
    "{AGENT_SCRIPT}",
    "handoffs:",
]

NAME_REGEX = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
VERSION_REGEX = re.compile(r"^\d+\.\d+\.\d+$")

BODY_WARN_LINES = 400
BODY_FAIL_LINES = 500


def discover_skills():
    """Return list of (skill_dir, skill_name) for all valid skill directories."""
    if not SKILLS_DIR.exists():
        return []
    return [
        (d, d.name)
        for d in sorted(SKILLS_DIR.iterdir())
        if d.is_dir() and (d / "SKILL.md").exists()
    ]


def parse_skill(skill_dir: Path):
    """Parse SKILL.md and return (frontmatter_dict, body_lines)."""
    content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}, content.splitlines()
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content.splitlines()
    frontmatter = yaml.safe_load(parts[1]) or {}
    body = parts[2]
    return frontmatter, body.splitlines()


@pytest.mark.parametrize("skill_dir,skill_name", discover_skills())
class TestSkillContract:
    def test_name_present(self, skill_dir, skill_name):
        fm, _ = parse_skill(skill_dir)
        assert "name" in fm, "[name-missing] frontmatter must contain 'name' field"

    def test_name_matches_directory(self, skill_dir, skill_name):
        fm, _ = parse_skill(skill_dir)
        name = fm.get("name", "")
        assert name == skill_name, (
            f"[name-mismatch] [{name}] name '{name}' does not match "
            f"directory '{skill_name}'"
        )

    def test_name_format(self, skill_dir, skill_name):
        fm, _ = parse_skill(skill_dir)
        name = fm.get("name", "")
        assert NAME_REGEX.match(name), (
            f"[name-format] [{name}] name must match [a-z0-9]+(-[a-z0-9]+)* "
            f"— no leading/trailing/consecutive hyphens, no uppercase"
        )

    def test_name_length(self, skill_dir, skill_name):
        fm, _ = parse_skill(skill_dir)
        name = fm.get("name", "")
        assert len(name) <= 64, (
            f"[name-length] [{len(name)}] name length {len(name)} exceeds limit of 64"
        )

    def test_description_present(self, skill_dir, skill_name):
        fm, _ = parse_skill(skill_dir)
        assert "description" in fm, (
            "[description-missing] frontmatter must contain 'description' field"
        )

    def test_description_non_empty(self, skill_dir, skill_name):
        fm, _ = parse_skill(skill_dir)
        desc = fm.get("description", "")
        assert desc and len(str(desc).strip()) > 0, (
            "[description-empty] description must be non-empty"
        )

    def test_description_length(self, skill_dir, skill_name):
        fm, _ = parse_skill(skill_dir)
        desc = str(fm.get("description", ""))
        assert len(desc) <= 1024, (
            f"[description-length] [{len(desc)}] description length {len(desc)} "
            f"exceeds limit of 1024 characters"
        )

    def test_metadata_version_present(self, skill_dir, skill_name):
        fm, _ = parse_skill(skill_dir)
        metadata = fm.get("metadata", {})
        assert isinstance(metadata, dict) and "version" in metadata, (
            "[version-missing] metadata.version is required for DevSpark skills"
        )

    def test_metadata_version_is_string(self, skill_dir, skill_name):
        fm, _ = parse_skill(skill_dir)
        metadata = fm.get("metadata", {})
        version = metadata.get("version")
        assert isinstance(version, str), (
            f"[version-type] [{version!r}] metadata.version must be a quoted string; "
            f"got {type(version).__name__}"
        )

    def test_metadata_version_semver(self, skill_dir, skill_name):
        fm, _ = parse_skill(skill_dir)
        metadata = fm.get("metadata", {})
        version = str(metadata.get("version", ""))
        assert VERSION_REGEX.match(version), (
            f"[version-format] [{version!r}] metadata.version '{version}' does not "
            f"match MAJOR.MINOR.PATCH (e.g., '0.1.0')"
        )

    def test_no_prohibited_keys(self, skill_dir, skill_name):
        fm, _ = parse_skill(skill_dir)
        found = PROHIBITED_KEYS & set(fm.keys())
        assert not found, (
            f"[prohibited-key] {sorted(found)} frontmatter key(s) are not permitted "
            f"in SKILL.md: {sorted(found)}"
        )

    def test_body_length_pass(self, skill_dir, skill_name):
        _, body_lines = parse_skill(skill_dir)
        count = len(body_lines)
        assert count <= BODY_FAIL_LINES, (
            f"[body-length] [{count}] body line count {count} exceeds maximum of "
            f"{BODY_FAIL_LINES}"
        )

    def test_body_portability_scan(self, skill_dir, skill_name):
        _, body_lines = parse_skill(skill_dir)
        body = "\n".join(body_lines)
        violations = [s for s in PROHIBITED_BODY_STRINGS if s in body]
        assert not violations, (
            f"[body-scan] {violations} body contains DevSpark-specific string(s) "
            f"that indicate portability violations: {violations}"
        )


class TestSkillContractViolationFixtures:
    """Deliberate-violation fixtures — each must fail with a named rule message."""

    def _parse_fixture(self, content: str):
        content = textwrap.dedent(content).lstrip()
        if not content.startswith("---"):
            return {}, content.splitlines()
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}, content.splitlines()
        fm = yaml.safe_load(parts[1]) or {}
        body = parts[2]
        return fm, body.splitlines()

    def test_fixture_uppercase_name_fails_format(self):
        content = """\
            ---
            name: WriteSpec
            description: A valid description for testing.
            metadata:
              version: "0.1.0"
            ---
            Body text here.
        """
        fm, _ = self._parse_fixture(content)
        name = fm.get("name", "")
        assert not NAME_REGEX.match(name), (
            "Expected uppercase name to fail NAME_REGEX"
        )

    def test_fixture_description_too_long_fails(self):
        content = f"""\
            ---
            name: write-spec
            description: {'x' * 1025}
            metadata:
              version: "0.1.0"
            ---
            Body text here.
        """
        fm, _ = self._parse_fixture(content)
        desc = str(fm.get("description", ""))
        assert len(desc) > 1024, "Expected description length to exceed 1024"

    def test_fixture_unquoted_float_version_fails_type(self):
        content = """\
            ---
            name: write-spec
            description: A valid description.
            metadata:
              version: 1.0
            ---
            Body text here.
        """
        fm, _ = self._parse_fixture(content)
        metadata = fm.get("metadata", {})
        version = metadata.get("version")
        assert not isinstance(version, str), (
            "Expected unquoted 1.0 to parse as float (not string)"
        )

    def test_fixture_partial_semver_fails_regex(self):
        content = """\
            ---
            name: write-spec
            description: A valid description.
            metadata:
              version: "1.0"
            ---
            Body text here.
        """
        fm, _ = self._parse_fixture(content)
        metadata = fm.get("metadata", {})
        version = str(metadata.get("version", ""))
        assert not VERSION_REGEX.match(version), (
            "Expected partial semver '1.0' to fail VERSION_REGEX"
        )

    def test_fixture_prohibited_key_fails(self):
        content = """\
            ---
            name: write-spec
            description: A valid description.
            metadata:
              version: "0.1.0"
            handoffs:
              - label: Next step
            ---
            Body text here.
        """
        fm, _ = self._parse_fixture(content)
        found = PROHIBITED_KEYS & set(fm.keys())
        assert found, "Expected prohibited key 'handoffs' to be detected"

    def test_fixture_body_with_devspark_string_fails(self):
        content = """\
            ---
            name: write-spec
            description: A valid description.
            metadata:
              version: "0.1.0"
            ---
            Run {SCRIPT} to gather context from .devspark/ directory.
        """
        _, body_lines = self._parse_fixture(content)
        body = "\n".join(body_lines)
        violations = [s for s in PROHIBITED_BODY_STRINGS if s in body]
        assert violations, (
            "Expected DevSpark-specific strings to be detected in body"
        )
