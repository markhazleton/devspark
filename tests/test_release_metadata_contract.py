# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for the 9.0.0 release metadata.

The version is declared in `pyproject.toml` and the framework version stamp. The stamp carries no
migration marker or compatibility field (retirement is stateless). The changelog records the
breaking change as a new entry and leaves every 8.x entry in place; the upgrade page and the
invocation-format note state the new convention.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAMP = ROOT / ".devspark" / "VERSION"
CHANGELOG = ROOT / "CHANGELOG.md"
UPGRADE_PAGE = ROOT / "site" / "src" / "get-started" / "upgrade.md"
INVOCATION_NOTE = ROOT / "site" / "src" / "guides" / "prompt-lifecycle-mapping.md"

STAMP_KEYS = {"product", "edition", "version", "installed", "method", "note"}
FORBIDDEN_STAMP_KEY = re.compile(r"migrat|compat|legacy|retire|upgrade", re.IGNORECASE)


def _stamp() -> dict[str, str]:
    data = {}
    for line in STAMP.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition(":")
        if separator:
            data[key.strip()] = value.strip()
    return data


def _changelog_headings() -> list[str]:
    return re.findall(r"^## \[([^\]]+)\]", CHANGELOG.read_text(encoding="utf-8"), re.MULTILINE)


def _changelog_entry(version: str) -> str:
    text = CHANGELOG.read_text(encoding="utf-8")
    match = re.search(rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)", text, re.MULTILINE | re.DOTALL)
    assert match, f"changelog has no {version} entry"
    return match.group(1)


def test_pyproject_reads_nine_zero_zero() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["version"] == "9.0.0"


def test_version_stamp_reads_nine_zero_zero() -> None:
    assert _stamp()["version"] == "9.0.0"


def test_version_stamp_carries_no_migration_marker_or_compatibility_field() -> None:
    stamp = _stamp()
    assert {"product", "version"} <= set(stamp)
    assert not [key for key in stamp if FORBIDDEN_STAMP_KEY.search(key)]
    assert set(stamp) <= STAMP_KEYS


def test_changelog_has_a_nine_zero_breaking_change_entry_above_the_eight_x_entries() -> None:
    headings = _changelog_headings()
    assert "9.0.0" in headings
    assert headings.index("9.0.0") < headings.index("8.3.0")
    entry = _changelog_entry("9.0.0")
    assert re.search(r"breaking", entry, re.IGNORECASE)
    assert re.search(r"/devspark-[a-z]", entry)
    assert re.search(r"skills", entry, re.IGNORECASE)
    assert re.search(r"8\.x", entry)


def test_eight_x_changelog_entries_are_still_present() -> None:
    headings = _changelog_headings()
    for version in ("8.3.0", "8.2.0", "8.1.0", "8.0.0", "7.8.0"):
        assert version in headings, version


def test_upgrade_page_has_an_upgrading_from_eight_x_section() -> None:
    text = UPGRADE_PAGE.read_text(encoding="utf-8")
    match = re.search(r"^(#{2,3})\s+Upgrading from 8\.x\s*$", text, re.MULTILINE | re.IGNORECASE)
    assert match, "upgrade page has no 'Upgrading from 8.x' section"
    section = text[match.end() :]
    assert re.search(r"/devspark-[a-z]", section)
    assert re.search(r"\.github/skills|skills", section, re.IGNORECASE)
    assert ".devspark.work/migration/8.x-entry-points" in section


def test_invocation_format_note_states_the_nine_zero_convention() -> None:
    text = INVOCATION_NOTE.read_text(encoding="utf-8")
    match = re.search(r"^## Invocation format\s*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    assert match, "invocation format section missing"
    note = re.sub(r"\s+", " ", match.group(1))
    assert "9.0" in note
    assert "/devspark-plan" in note
    assert re.search(r"skills", note, re.IGNORECASE)
    assert not re.search(r"8\.3[^.]*distributed|undergoing acceptance testing", note, re.IGNORECASE)
