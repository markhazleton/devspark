# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Drift guard for the split command preamble contract.

The core binds every command; modules bind only the commands named in the
core's module table. A command that cites a section must load the module that
owns it, and every listed consumer must load its module even without a citation.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "templates" / "command-preamble-contract.md"
MODULES_DIR = ROOT / "templates" / "preamble"
COMMANDS = ROOT / "templates" / "commands"

CORE_SECTIONS = {"0", "1", "2", "3", "4", "5", "6", "8", "13", "14"}
MODULE_SECTIONS = {
    "finding-fix": {"9", "9.1", "9.2"},
    "convergence": {"10"},
    "orchestration": {"11"},
    "provenance": {"12"},
    "configuration": {"7"},
}
SECTION_OWNER = {section: module for module, sections in MODULE_SECTIONS.items() for section in sections}

# Obligations that must keep loading their safety/scope text whatever a prompt cites.
MANDATORY_CORE_COMMANDS = ("plan", "tasks", "implement", "specify", "analyze", "critic")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _module_table() -> dict[str, list[str]]:
    match = re.search(r"```yaml\s*\npreamble_modules:\n(.*?)```", _text(CORE), re.S)
    assert match, "the core must carry a machine-readable preamble_modules block"
    parsed = yaml.safe_load("preamble_modules:\n" + match.group(1))["preamble_modules"]
    return {name: list(consumers) for name, consumers in parsed.items()}


def _declared_modules(command_text: str) -> set[str]:
    match = re.search(r"Preamble\s+modules:\s*((?:`[a-z-]+`(?:,\s*)?)+)", command_text)
    return set(re.findall(r"`([a-z-]+)`", match.group(1))) if match else set()


def _cited_sections(command_text: str) -> set[str]:
    cited: set[str] = set()
    for line in command_text.splitlines():
        if "preamble" in line.lower():
            cited.update(re.findall(r"\u00a7\s?(\d+(?:\.\d+)?)", line))
    return cited


def _commands() -> list[Path]:
    return sorted(COMMANDS.glob("*.md"), key=lambda p: p.as_posix())


def test_every_module_exists_and_owns_exactly_its_sections() -> None:
    table = _module_table()
    assert set(table) == set(MODULE_SECTIONS)
    for module, sections in MODULE_SECTIONS.items():
        body = _text(MODULES_DIR / f"{module}.md")
        headings = set(re.findall(r"^#{2,3} (\d+(?:\.\d+)?)[. ]", body, re.M))
        assert headings == sections, (module, headings)


def test_the_core_keeps_its_sections_and_does_not_restate_module_sections() -> None:
    core = _text(CORE)
    headings = set(re.findall(r"^## (\d+)\. ", core, re.M))
    assert headings == CORE_SECTIONS
    for section in SECTION_OWNER:
        assert not re.search(rf"^#{{2,3}} {re.escape(section)}[. ]", core, re.M), section


def test_every_listed_consumer_loads_its_module() -> None:
    missing = []
    for module, consumers in _module_table().items():
        for name in consumers:
            path = COMMANDS / f"{name}.md"
            assert path.is_file(), f"{module} lists unknown command {name}"
            if module not in _declared_modules(_text(path)):
                missing.append((module, name))
    assert not missing, missing


def test_a_command_never_loads_a_module_it_is_not_listed_for() -> None:
    table = _module_table()
    stray = []
    for path in _commands():
        for module in _declared_modules(_text(path)):
            if module not in table:
                stray.append((path.stem, module, "unknown module"))
            elif path.stem not in table[module]:
                stray.append((path.stem, module, "not a listed consumer"))
    assert not stray, stray


def test_a_command_citing_a_section_loads_the_module_that_owns_it() -> None:
    offenders = []
    for path in _commands():
        text = _text(path)
        declared = _declared_modules(text)
        for section in _cited_sections(text):
            if section in CORE_SECTIONS:
                continue
            owner = SECTION_OWNER.get(section)
            if owner is None:
                offenders.append((path.stem, section, "unknown section"))
            elif owner not in declared:
                offenders.append((path.stem, section, f"needs {owner}"))
    assert not offenders, offenders


@pytest.mark.parametrize("command", MANDATORY_CORE_COMMANDS)
def test_planning_and_gate_commands_still_load_the_core(command: str) -> None:
    text = _text(COMMANDS / f"{command}.md")
    assert "shared preamble contract core at" in text
    assert "command-preamble-contract.md" in text


def test_the_core_keeps_the_universal_safety_scope_and_authority_rules() -> None:
    core = _text(CORE)
    for phrase in (
        "MUST NOT contain\n  spec, task, quickfix, feature, or requirement identifiers",
        "No DevSpark command reads, lists, enumerates, or globs `.archive/`",
        "Branch Safety (non-negotiable)",
        "required even under `--auto`",
        "Minimum Sufficient Change",
        "Complexity is a cost that requires justification.",
    ):
        assert phrase in core, phrase


def test_same_context_reuse_is_limited_to_full_unchanged_content_and_keeps_independent_checks() -> None:
    core = _text(CORE)
    section = core.split("## 14. Reusing Already-Loaded Artifacts", 1)[1]
    assert "full, unchanged" in section
    assert "Never reuse a summary, an excerpt, or a copy from another session or a cache" in section
    assert "still evaluates the artifact itself and never adopts another command's conclusion" in section
    assert "reloads it before relying on it again" in section


@pytest.mark.parametrize("command", ["plan", "tasks", "next", "analyze", "critic"])
def test_loaded_shared_bytes_are_smaller_than_the_whole_contract(command: str) -> None:
    modules_total = sum(len(_text(MODULES_DIR / f"{m}.md").encode()) for m in MODULE_SECTIONS)
    core = len(_text(CORE).encode())
    loaded = core + sum(
        len(_text(MODULES_DIR / f"{m}.md").encode()) for m in _declared_modules(_text(COMMANDS / f"{command}.md"))
    )
    assert loaded < core + modules_total
