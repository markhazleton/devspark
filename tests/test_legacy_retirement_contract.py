# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for retiring the old dotted entry points when upgrading to the skills distribution.

Two halves:

* The prose procedure in each quickstart and in the upgrade command, checked structurally: it must
  exist as its own section, follow the skills install, never block it, and state the rules the
  procedure depends on (one confirmation, quarantine, untouched user content, stateless).
* The test-only oracle, which encodes the same rules, run over every upgrade fixture three times to
  prove idempotence and byte preservation.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

import tests.legacy_retirement_oracle as oracle

ROOT = Path(__file__).resolve().parent.parent
UPGRADE = ROOT / "tests" / "fixtures" / "upgrade"
QUICKSTART_DIR = ROOT / "quickstart"
UPGRADE_PROMPT = ROOT / "templates" / "commands" / "upgrade.md"

# quickstart file -> registry key whose commands_dir and extension it must name (None: generic)
QUICKSTART_AGENT = {
    "devspark_quickstart_antigravity.md": "antigravity",
    "devspark_quickstart_claudecode.md": "claude",
    "devspark_quickstart_codex.md": "codex",
    "devspark_quickstart_copilot.md": "copilot",
    "devspark_quickstart_cursor.md": "cursor-agent",
    "devspark_quickstart_generic.md": None,
}
HEADING = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
SECTION_TITLE = re.compile(r"8\.x.*entry[- ]point|entry[- ]point.*8\.x", re.IGNORECASE)
INSTALL_TITLE = re.compile(r"install canonical framework files|perform the upgrade", re.IGNORECASE)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def retirement_section(text: str) -> tuple[str, int, int] | None:
    """Return (section text, section start, install-step start) or None when absent."""
    headings = list(HEADING.finditer(text))
    install = next((h.start() for h in headings if INSTALL_TITLE.search(h.group(2))), -1)
    for index, heading in enumerate(headings):
        if not SECTION_TITLE.search(heading.group(2)):
            continue
        level = len(heading.group(1))
        end = len(text)
        for later in headings[index + 1 :]:
            if len(later.group(1)) <= level:
                end = later.start()
                break
        return text[heading.start() : end], heading.start(), install
    return None


def _registry_release(key: str) -> dict:
    if key == "copilot":
        # Copilot's 8.x locations are retired history; the registry now names only its skills directory.
        return {"commands_dir": ".github/agents", "extension": "agent.md", "prompt_dir": ".github/prompts"}
    registry = json.loads(_read(ROOT / "agents-registry.json"))
    return next(a for a in registry["agents"] if a["key"] == key)["release"]


def _surfaces() -> list[tuple[str, Path]]:
    return [(name, QUICKSTART_DIR / name) for name in QUICKSTART_AGENT] + [("upgrade.md", UPGRADE_PROMPT)]


def _section(path: Path) -> str:
    found = retirement_section(_read(path))
    assert found is not None, f"{path.name} has no 8.x entry-point retirement section"
    return found[0]


def _in_order(text: str, *patterns: str) -> bool:
    position = 0
    for pattern in patterns:
        match = re.search(pattern, text[position:], re.IGNORECASE)
        if not match:
            return False
        position += match.end()
    return True


SURFACES = pytest.mark.parametrize("name,path", _surfaces(), ids=[n for n, _ in _surfaces()])


def test_section_extractor_finds_a_nested_section_and_stops_at_the_next_peer() -> None:
    text = "## Step 4: Install Canonical Framework Files\nx\n## Retire 8.x entry points\nbody\n### sub\nmore\n## Next\nend\n"
    section, start, install = retirement_section(text)
    assert section.startswith("## Retire 8.x entry points") and "more" in section and "end" not in section
    assert 0 <= install < start
    assert retirement_section("## Something else\n") is None


@SURFACES
def test_retirement_section_follows_the_skills_install_and_never_blocks_it(name: str, path: Path) -> None:
    found = retirement_section(_read(path))
    assert found is not None, f"{name} has no 8.x entry-point retirement section"
    section, start, install = found
    assert 0 <= install < start, "retirement must come after the install step"
    assert re.search(r"never\s+blocks?|must\s+not\s+block|does\s+not\s+block", section, re.IGNORECASE)
    assert re.search(r"skills?", section, re.IGNORECASE)


@SURFACES
def test_retirement_asks_for_one_confirmation_between_the_list_and_the_deletion(name: str, path: Path) -> None:
    section = _section(path)
    assert re.search(r"(one|single)\s+confirmation", section, re.IGNORECASE)
    assert _in_order(section, r"\blist\b|\bshow\b", r"confirm", r"\bdelete")


@SURFACES
def test_retirement_quarantines_edited_files_without_overwriting(name: str, path: Path) -> None:
    section = _section(path)
    assert ".devspark.work/migration/8.x-entry-points" in section
    assert "byte-identical" in section
    assert re.search(r"numeric suffix", section, re.IGNORECASE)
    assert re.search(r"never\s+overwrit", section, re.IGNORECASE)
    assert re.search(r"customi[sz]ation", section, re.IGNORECASE), "recreate-as-customization remedy missing"


@SURFACES
def test_retirement_leaves_foreign_content_alone_and_reports_conflicts_and_orphans(name: str, path: Path) -> None:
    section = _section(path)
    assert re.search(r"foreign", section, re.IGNORECASE)
    assert re.search(r"untouched|left alone|not touch", section, re.IGNORECASE)
    assert re.search(r"devspark-<[^>]+>|devspark-\{[^}]+\}", section), "skill folder naming missing"
    assert re.search(r"conflict", section, re.IGNORECASE)
    assert re.search(r"orphan", section, re.IGNORECASE)


@SURFACES
def test_retirement_never_touches_user_owned_roots(name: str, path: Path) -> None:
    section = _section(path)
    for owned in (".devspark.work/", ".knowledge/", ".archive/"):
        assert owned in section, owned
    assert re.search(r"never\s+(touch|modif|delet|overwrit)|not\s+(touch|modif)", section, re.IGNORECASE)


@SURFACES
def test_retirement_is_stateless_and_keyed_to_the_installed_major_version(name: str, path: Path) -> None:
    section = _section(path)
    assert re.search(r"installed\s+(major\s+)?version", section, re.IGNORECASE)
    assert re.search(r"major", section, re.IGNORECASE)
    assert re.search(r"stateless", section, re.IGNORECASE)
    assert re.search(r"no\s+(migration\s+)?(marker|flag)", section, re.IGNORECASE)


@pytest.mark.parametrize("name", [n for n, k in QUICKSTART_AGENT.items() if k])
def test_each_quickstart_names_its_own_commands_directory_and_extension(name: str) -> None:
    section = _section(QUICKSTART_DIR / name)
    release = _registry_release(QUICKSTART_AGENT[name])
    assert release["commands_dir"] in section
    assert re.search(rf"devspark\.[^\s`/]*\.{re.escape(release['extension'])}\b", section)
    if "prompt_dir" in release:
        assert release["prompt_dir"] in section and "prompt.md" in section


@pytest.mark.parametrize(
    "path", [QUICKSTART_DIR / "devspark_quickstart_copilot.md", UPGRADE_PROMPT], ids=lambda p: p.name
)
def test_copilot_retirement_prunes_only_managed_prompt_recommendations(path: Path) -> None:
    section = _section(path)
    assert "promptFilesRecommendations" in section
    assert re.search(r"only\s+(the\s+)?managed|managed\s+entries", section, re.IGNORECASE)
    assert re.search(r"user-added|leave", section, re.IGNORECASE)


@pytest.mark.parametrize("name", sorted(p.name for p in UPGRADE.iterdir() if p.is_dir() and p.name != "_common"))
def test_oracle_is_idempotent_and_preserves_bytes_over_three_runs(tmp_path: Path, name: str) -> None:
    root = tmp_path / "tree"
    for source in (UPGRADE / "_common", UPGRADE / name):
        shutil.copytree(source, root, dirs_exist_ok=True)

    def snapshot() -> dict[str, bytes]:
        return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}

    before = snapshot()
    first = oracle.apply(root)
    after_first = snapshot()
    preserved = [r for r in before if r.startswith((".devspark/", ".devspark.work/", ".knowledge/", ".archive/"))]
    preserved += list(first.untouched) + [r for r in first.report if r in before]
    for rel in preserved:
        assert after_first.get(rel) == before[rel], rel
    for rel in first.quarantine:
        assert before[rel] in {v for k, v in after_first.items() if k.startswith(oracle.QUARANTINE.as_posix())}
    for rel in first.delete:
        assert rel not in after_first

    for _ in range(2):
        again = oracle.apply(root)
        assert again.delete == [] and again.quarantine == []
        assert snapshot() == after_first


def test_foreign_skill_folder_is_reported_not_overwritten(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    for source in (UPGRADE / "_common", UPGRADE / "foreign-files"):
        shutil.copytree(source, root, dirs_exist_ok=True)
    skill = root / ".github" / "skills" / "devspark-specify" / "SKILL.md"
    before = skill.read_bytes()
    result = oracle.apply(root)
    assert ".github/skills/devspark-specify" in result.report
    assert skill.read_bytes() == before
