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
    ROOT / ".documentation",
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
    ".documentation/devspark/runs",
}

FORBIDDEN_PHRASES = [
    "All canonical prompts live in `.documentation/commands/`",
    "Canonical prompts live in `.documentation/commands/` as a single source of truth.",
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


def main() -> None:
    files = iter_scope_files()
    assert files, "No documentation files found for audit scope"
    check_forbidden_phrases(files)
    check_internal_links(files)
    print(f"Documentation audit validated for {len(files)} files.")


if __name__ == "__main__":
    main()
