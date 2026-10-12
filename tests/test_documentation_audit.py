# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Current-state documentation audit for the repository and docs site.

Run with: python tests/test_documentation_audit.py
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

SCOPE_PATHS = [
    ROOT / "README.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "SUPPORT.md",
    ROOT / "CHANGELOG.md",
    ROOT / "CLAUDE.md",
]
SCOPE_DIRS = [
    ROOT / "site" / "src",
    ROOT / "quickstart",
    ROOT / "templates",
    ROOT / "examples",
]

EXCLUDED_PARTS = {
    ".archive",
    "tests",
    ".claude",
    ".github/agents",
    ".github/prompts",
}

FORBIDDEN_PHRASES = [
    "All canonical prompts live in `.devspark.work/commands/`",
    "Canonical prompts live in `.devspark.work/commands/` as a single source of truth.",
    "24 slash-command prompt files (the product)",
    "It provides 24 prompt templates",
    "redirect to shared canonical prompts",
]

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def iter_scope_files() -> list[Path]:
    files: list[Path] = []
    for path in SCOPE_PATHS:
        if path.exists():
            files.append(path)
    for directory in SCOPE_DIRS:
        if not directory.exists():
            continue
        for path in directory.rglob("*.md"):
            relative = path.relative_to(ROOT).as_posix()
            if any(part in relative for part in EXCLUDED_PARTS):
                continue
            files.append(path)
    return sorted(set(files))


def check_forbidden_phrases(files: list[Path]) -> None:
    problems: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for phrase in FORBIDDEN_PHRASES:
            if phrase in text:
                problems.append(f"{path.relative_to(ROOT).as_posix()}: contains forbidden phrase: {phrase}")
    assert not problems, "\n".join(problems)


def check_internal_links(files: list[Path]) -> None:
    problems: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            raw_target = match.group(1).strip()
            if not raw_target or raw_target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if "{" in raw_target or "}" in raw_target:
                continue
            target = raw_target.split("#", 1)[0]
            if not target:
                continue
            target_path = (path.parent / target).resolve()
            if not target_path.exists():
                problems.append(
                    f"{path.relative_to(ROOT).as_posix()}: broken relative link -> {raw_target}"
                )
    assert not problems, "\n".join(problems)


def test_site_skills_use_canonical_invocations() -> None:
    commands = {path.stem for path in (ROOT / "templates" / "commands").glob("*.md")}
    canonical = {f"/devspark-{command}" for command in commands}
    dotted_name = re.compile(
        r"(?<![\w./-])/?devspark\.(?:" + "|".join(sorted(commands)) + r"|\*)(?![\w.-])"
    )
    site = ROOT / "site"
    text_extensions = {".md", ".yml", ".json", ".js", ".css", ".html", ".tmpl", ".svg"}
    sources = sorted(
        path
        for directory in (site / "src", site / "templates")
        for path in directory.rglob("*")
        if path.is_file() and path.suffix in text_extensions
    )
    flow = site / "templates" / "devspark" / "public" / "main.js"
    problems: list[str] = []
    for path in sources:
        text = path.read_text(encoding="utf-8")
        label = path.relative_to(ROOT).as_posix()
        if dotted_name.search(text) or re.search(r"(?<![\w./-])/devspark\.[a-z*<]", text):
            problems.append(f"{label}: dotted skill name")
        if "Command Catalog" in text:
            problems.append(f"{label}: obsolete catalog label")
        for command in re.findall(r"(?<![\w./-])/devspark-([a-z][a-z-]*)", text):
            if command not in commands:
                problems.append(f"{label}: unknown skill /devspark-{command}")

    catalog = (site / "src" / "guides" / "prompt-lifecycle-mapping.md").read_text(encoding="utf-8")
    assert catalog.startswith("# Skill Catalog\n")
    assert "Every `/devspark-*` skill in one place." in catalog
    assert set(re.findall(r"/devspark-([a-z][a-z-]*)", catalog)) == commands
    for label in re.findall(r"`([^`]+)`|\*\*([^*]+)\*\*", catalog):
        name = label[0] or label[1]
        if name in commands:
            problems.append(f"Skill Catalog: short skill name {name}")

    flow_text = flow.read_text(encoding="utf-8")
    steps = re.findall(r'\{ cmd: "([^"]+)", tag: "(?:req|rec|opt)"', flow_text)
    assert steps, "Route explorer has no skill steps"
    for step in steps:
        if step not in canonical:
            problems.append(f"Route explorer: noncanonical skill {step}")
    assert not problems, "\n".join(problems)


def test_site_defines_distinct_skill_terminology() -> None:
    site = ROOT / "site" / "src"
    catalog = (site / "guides" / "prompt-lifecycle-mapping.md").read_text(encoding="utf-8")
    assert "## Terminology\n" in catalog
    for term in ("Skill", "Slash command", "Agent", "Prompt"):
        assert f"| **{term}** |" in catalog
    for path in (
        site / "index.md",
        site / "get-started" / "quickstart.md",
        site / "get-started" / "how-it-works.md",
        site / "why" / "faq.md",
    ):
        assert "prompt-lifecycle-mapping.md#terminology" in path.read_text(encoding="utf-8")

    outdated_terms = ("DevSpark commands", "DevSpark command ", "command catalog", "command prompts")
    for path in site.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for term in outdated_terms:
            assert term not in text, f"{path.relative_to(ROOT)}: ambiguous terminology {term}"

    codex = (site / "get-started" / "devspark-and-codex.md").read_text(encoding="utf-8")
    assert "does not mean it is installed as a native Codex skill" in codex
    assert "Use skills for specialist execution patterns" not in codex
    releases = (site / "releases.md").read_text(encoding="utf-8")
    assert "Prompt and agent files are no longer distributed." not in releases


def main() -> None:
    files = iter_scope_files()
    assert files, "No documentation files found for audit scope"
    check_forbidden_phrases(files)
    check_internal_links(files)
    test_site_skills_use_canonical_invocations()
    test_site_defines_distinct_skill_terminology()
    print(f"Documentation audit validated for {len(files)} files.")


if __name__ == "__main__":
    main()
