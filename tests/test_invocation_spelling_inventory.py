# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Inventory of dotted `devspark.<command>` occurrences on current-version surfaces.

Classifier rules (deterministic, applied in this order to every occurrence of a dotted spelling
followed by a known command name or a `<command>` / `{command}` placeholder):

1. `@devspark.<cmd>` is always actionable, whatever surrounds it.
2. filename: the occurrence is followed by a file extension (`.md`, `.agent.md`, `.prompt.md`,
   `.toml`, `.json`, `.sh`, `.ps1`, `.py`, `.yml`, `.yaml`).
3. path: the occurrence is glued to a preceding path segment (`commands/devspark.specify`).
   A slash preceded by whitespace, a quote, a backtick, a bracket or the line start is an
   invocation, not a path.
4. metadata key: the line is a YAML key from `METADATA_KEYS` whose value is the dotted name.
5. script name: the occurrence is the stem of a file under `scripts/` named after it.
   A `devspark.<placeholder>` that is not an invocation (no leading slash) is a name pattern for a
   file or key, such as the 8.x entry point names the upgrade recognizes, and is retained.
6. historical record: the file is the changelog, the release notes page, or lives under an archive
   directory.
7. documented 8.x note: the line, or the nearest preceding heading, names 8.x, the dotted form, or an
   upgrade from 8.x.
8. otherwise the occurrence is actionable and must be respelled `devspark-<cmd>`.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

import yaml

from tests.consumer_skill_helpers import ROOT, commands

SURFACE_GLOBS = (
    "templates/**/*.md",
    "scripts/**/*.sh",
    "scripts/**/*.ps1",
    "scripts/**/*.py",
    "scripts/README.md",
    "quickstart/*.md",
    "README.md",
    "AGENTS.md",
    "site/src/**/*.md",
    "examples/**/*.md",
    ".knowledge/**/*.md",
    "CONTRIBUTING.md",
    ".github/ISSUE_TEMPLATE/*.md",
    ".github/agents/*.md",
    ".github/skills/**/SKILL.md",
    "eng/**/*.md",
    "eng/**/*.sh",
    "eng/**/*.ps1",
)
FILE_EXTENSIONS = r"(?:agent\.md|prompt\.md|md|toml|json|sh|ps1|py|yml|yaml)"
METADATA_KEYS = ("legacy_command", "legacy_name", "mode", "name", "replaces")
NOTE_WORDS = re.compile(r"8\.x|\b8\.\d|\bdotted\b|upgrading from|before 9", re.IGNORECASE)
HEADING = re.compile(r"^#{1,6}\s+(.*)$")
NEXT_STEPS = re.compile(r"^(#{2,4})\s+.*next steps?\b", re.IGNORECASE | re.MULTILINE)
BOTH_FORMATS = re.compile(
    r"(both\s+(the\s+)?(dotted|hyphen\w*|spellings?)|"
    r"dotted[^.\n]*\b(still|also|continues?)\b[^.\n]*\b(work|accepted|supported|valid)|"
    r"(either|any)\s+spelling[^.\n]*(work|accepted|supported|valid))",
    re.IGNORECASE,
)
NEGATED = re.compile(r"\b(no longer|not|never|cannot|without|stops?)\b", re.IGNORECASE)


def _occurrence_pattern() -> re.Pattern[str]:
    names = "|".join(sorted(map(re.escape, commands()), key=len, reverse=True))
    return re.compile(rf"(?P<at>@?)devspark\.(?P<name>{names}|<[^>\s]+>|\{{[^}}\s]+\}}|\*)(?![\w-])")


OCCURRENCE = _occurrence_pattern()


def classify(line: str, match: re.Match[str], file: Path | str, heading: str = "") -> str:
    """Return `actionable` or the retained class of one dotted occurrence."""
    path = Path(file).as_posix()
    if match.group("at"):
        return "actionable"
    after = line[match.end() :]
    if re.match(rf"\.{FILE_EXTENSIONS}\b", after):
        return "filename"
    before = line[: match.start()]
    if re.search(r"[\w}\].~*-][/\\]$", before) or re.search(r"<(?!/?(?:code|a|em|strong|b|i|span|p|li|kbd)\b)[^<>]*>[/\\]$", before) or before.endswith("."):
        return "path"
    key = re.match(r"\s*(?:-\s+)?([A-Za-z_]+)\s*:", before)
    if key and key.group(1) in METADATA_KEYS and before.rstrip().endswith(":"):
        return "metadata-key"
    if match.group("name").startswith("<") and not before.endswith("/"):
        return "name-placeholder"
    if path.startswith("scripts/") and match.group("name") in Path(path).stem:
        return "script-name"
    if Path(path).name == "CHANGELOG.md" or path == "site/src/releases.md":
        return "historical-record"
    if path.startswith(".archive/") or "/.archive/" in path:
        return "historical-record"
    if NOTE_WORDS.search(line) or NOTE_WORDS.search(heading):
        return "documented-8x-note"
    return "actionable"


def surface_files() -> list[Path]:
    seen: dict[Path, None] = {}
    for pattern in SURFACE_GLOBS:
        for path in sorted(ROOT.glob(pattern)):
            if path.is_file() and "__pycache__" not in path.parts and "_site" not in path.parts:
                seen[path] = None
    return list(seen)


def occurrences(files: list[Path] | None = None) -> Iterator[tuple[str, int, str, str]]:
    """Yield (relative path, line number, class, text) for every dotted occurrence."""
    for path in files or surface_files():
        relative = path.relative_to(ROOT).as_posix()
        heading = ""
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            title = HEADING.match(line)
            if title and path.suffix == ".md":
                heading = title.group(1)
            for match in OCCURRENCE.finditer(line):
                yield relative, number, classify(line, match, relative, heading), line.strip()


def _classes(line: str, file: str = "templates/commands/x.md", heading: str = "") -> list[str]:
    return [classify(line, m, file, heading) for m in OCCURRENCE.finditer(line)]


def test_classifier_marks_actionable_invocations() -> None:
    assert _classes("Run `/devspark.specify` next.") == ["actionable"]
    assert _classes("then /devspark.plan, then /devspark.tasks") == ["actionable", "actionable"]
    assert _classes("  agent: devspark.plan") == ["actionable"]
    assert _classes("see @devspark.next for more", heading="Upgrading from 8.x") == ["actionable"]


def test_classifier_retains_filenames_paths_keys_scripts_history_and_8x_notes() -> None:
    assert _classes("copy devspark.specify.md here") == ["filename"]
    assert _classes("`.github/agents/devspark.next.agent.md`") == ["filename"]
    assert _classes("`.devspark.work/commands/devspark.specify`") == ["path"]
    assert _classes("a `name` must equal `devspark.<cmd>` for the file") == ["name-placeholder"]
    assert _classes("<code>/devspark.implement</code>") == ["actionable"]
    assert _classes("see `<root>/devspark.specify`") == ["path"]
    assert _classes("run `/devspark.{command}` now") == ["actionable"]
    assert _classes("legacy_command: devspark.specify") == ["metadata-key"]
    assert _classes("echo devspark.next", file="scripts/bash/devspark.next.sh") == ["script-name"]
    assert _classes("Run /devspark.plan", file="CHANGELOG.md") == ["historical-record"]
    assert _classes("8.x used /devspark.plan") == ["documented-8x-note"]
    assert _classes("Run /devspark.plan", heading="Upgrading from 8.x") == ["documented-8x-note"]
    assert _classes("the file devspark.{command}.md") == ["filename"]


def test_classifier_flags_wildcard_invocations_but_not_wildcard_paths_or_filenames() -> None:
    assert _classes("every `/devspark.*` command it installs") == ["actionable"]
    assert _classes("`.devspark/defaults/commands/devspark.*.md`") == ["filename"]
    assert _classes("`.github/agents/devspark.*` entry point") == ["path"]


def test_quickstart_preview_prints_the_stock_prompt_not_the_skill_shim() -> None:
    for guide in sorted((ROOT / "quickstart").glob("devspark_quickstart_*.md")):
        text = guide.read_text(encoding="utf-8")
        assert "-like '*devspark-specify*'" not in text, guide.name
        assert 'test("devspark-specify")' not in text, guide.name
        assert "$_.category -eq 'command'" in text, guide.name
        assert '.category=="command"' in text, guide.name


def test_classifier_ignores_non_command_dotted_names() -> None:
    assert _classes("`.devspark.work/specs` and devspark.json and VERSION") == []


def test_classifier_is_deterministic() -> None:
    line = "Run /devspark.plan then devspark.tasks.md"
    assert _classes(line) == _classes(line) == ["actionable", "filename"]


def test_the_surface_set_covers_the_current_version_documents() -> None:
    files = {p.relative_to(ROOT).as_posix() for p in surface_files()}
    for required in ("README.md", "AGENTS.md", "templates/commands/specify.md", "quickstart/devspark_quickstart_copilot.md"):
        assert required in files, required
    assert any(f.startswith(".knowledge/") for f in files)
    assert any(f.startswith("site/src/") for f in files)


def test_there_are_no_unclassified_actionable_dotted_invocations() -> None:
    actionable = [f"{p}:{n}: {t[:90]}" for p, n, c, t in occurrences() if c == "actionable"]
    assert not actionable, f"{len(actionable)} actionable dotted invocations, first: {actionable[:5]}"


def test_no_at_prefixed_dotted_form_remains() -> None:
    found = [f"{p}:{n}" for p, n, _, t in occurrences() if "@devspark." in t]
    assert not found, found[:5]


def _handoff_agents(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\r?\n(.*?)\r?\n---", text, re.DOTALL)
    if not match:
        return []
    data = yaml.safe_load(match.group(1)) or {}
    return [str(h["agent"]) for h in data.get("handoffs", []) or [] if isinstance(h, dict) and "agent" in h]


def test_handoff_targets_exist_in_every_handoff_bearing_template() -> None:
    assert any(_handoff_agents(p) for p in (ROOT / "templates" / "commands").glob("*.md"))


def test_handoff_agent_values_are_hyphenated_command_names() -> None:
    bad = []
    known = set(commands())
    for path in sorted((ROOT / "templates" / "commands").glob("*.md")):
        for agent in _handoff_agents(path):
            if agent.removeprefix("devspark-") not in known or not agent.startswith("devspark-"):
                bad.append(f"{path.name}: {agent}")
    assert not bad, bad[:5]


def _final_next_steps(text: str) -> str | None:
    headings = list(re.finditer(r"^(#{1,6})\s+.*$", text, re.MULTILINE))
    last = None
    for index, heading in enumerate(headings):
        if NEXT_STEPS.match(heading.group(0)):
            level = len(heading.group(1))
            end = next((h.start() for h in headings[index + 1 :] if len(h.group(1)) <= level), len(text))
            last = text[heading.start() : end]
    return last


def test_some_commands_carry_a_next_steps_section() -> None:
    sections = [_final_next_steps(p.read_text(encoding="utf-8")) for p in (ROOT / "templates" / "commands").glob("*.md")]
    assert any(sections)


def test_each_final_next_steps_section_names_a_hyphenated_command() -> None:
    names = "|".join(sorted(map(re.escape, commands()), key=len, reverse=True))
    missing = []
    for path in sorted((ROOT / "templates" / "commands").glob("*.md")):
        section = _final_next_steps(path.read_text(encoding="utf-8"))
        if section is None:
            continue
        if not re.search(rf"/devspark-(?:{names})\b", section) or re.search(rf"(?<![\w.])/devspark\.(?:{names})\b", section):
            missing.append(path.name)
    assert not missing, missing


def test_no_surface_claims_that_both_spellings_work() -> None:
    offenders = []
    for path in surface_files():
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if BOTH_FORMATS.search(line) and not NEGATED.search(line):
                offenders.append(f"{path.relative_to(ROOT).as_posix()}:{number}")
    assert not offenders, offenders[:5]
