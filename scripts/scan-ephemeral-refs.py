"""Scan code comments for references to ephemeral DevSpark artifacts.

One deterministic check: permanent code must never track specs, requirements,
tasks, plans, proposals, or archive paths in comments. Only comments are
scanned; string literals and Markdown are out of scope. Read-only.

Scope (exactly one):
  --base <ref> [--head <ref>]   files changed between two Git refs
  --full-inventory              every tracked file

Exit codes: 0 clean, 1 findings, 2 usage or Git error.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HASH_COMMENT = {
    ".py", ".pyi", ".sh", ".bash", ".zsh", ".ps1", ".psm1", ".rb", ".pl", ".r",
    ".yaml", ".yml", ".toml", ".cfg", ".ini", ".tf", ".dockerfile",
}
SLASH_COMMENT = {
    ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".cs", ".java", ".kt", ".kts",
    ".go", ".rs", ".c", ".h", ".cc", ".cpp", ".hpp", ".swift", ".scala", ".php",
    ".dart", ".css", ".scss", ".less", ".groovy", ".fs",
}
MARKUP_COMMENT = {".xml", ".html", ".htm", ".xaml", ".csproj", ".fsproj", ".vbproj", ".props", ".targets", ".vue", ".svelte"}
SQL_COMMENT = {".sql"}

EXCLUDED_PREFIXES = (".git/", ".devspark.work/", ".archive/", ".knowledge/", "node_modules/")

PATTERNS = (
    ("task-id", re.compile(r"\bT\d{3,4}\b")),
    ("requirement-id", re.compile(r"\b(?:FR|NFR|SC|US)-\d{2,4}\b")),
    ("proposal-id", re.compile(r"\bCAP-\d{4}-\d{3}\b")),
    ("work-package-path", re.compile(r"\.devspark\.work/(?:specs|quickfixes|pr-reviews|release-candidates)/[\w.-]+")),
    ("spec-path", re.compile(r"\bspecs/\d{3}-[a-z0-9][\w-]*")),
    ("spec-id", re.compile(r"\b(?:spec|feature|quickfix|plan)[\s:#]+\d{3}(?:-[a-z0-9]+)+\b", re.IGNORECASE)),
    ("archive-path", re.compile(r"\.archive/\d{4}-\d{2}-\d{2}")),
)


def comment_kind(path: str) -> str | None:
    name = Path(path).name.lower()
    suffix = Path(path).suffix.lower()
    if name in {"dockerfile", "makefile"}:
        return "hash"
    if suffix in HASH_COMMENT:
        return "hash"
    if suffix in SLASH_COMMENT:
        return "slash"
    if suffix in MARKUP_COMMENT:
        return "markup"
    if suffix in SQL_COMMENT:
        return "sql"
    return None


def strip_strings(line: str) -> str:
    """Blank out quoted string contents so markers inside strings are ignored."""
    return re.sub(r"(\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')", lambda m: " " * len(m.group(0)), line)


def blank_triple_quoted(text: str) -> str:
    """Blank Python triple-quoted strings, keeping line numbers intact."""
    return re.sub(
        r'("""|\'\'\')(?:.|\n)*?\1',
        lambda m: re.sub(r"[^\n]", " ", m.group(0)),
        text,
    )


def comments(text: str, kind: str, powershell: bool) -> list[tuple[int, str]]:
    """Return (line number, comment text) pairs for one file."""
    found: list[tuple[int, str]] = []
    in_block = False
    block_open, block_close = {
        "slash": ("/*", "*/"),
        "markup": ("<!--", "-->"),
        "hash": ("<#", "#>") if powershell else (None, None),
        "sql": ("/*", "*/"),
    }[kind]
    line_marker = {"hash": "#", "slash": "//", "sql": "--", "markup": None}[kind]

    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw
        if in_block:
            end = line.find(block_close)
            if end == -1:
                found.append((number, line))
                continue
            found.append((number, line[:end]))
            line = line[end + len(block_close):]
            in_block = False
        scrubbed = strip_strings(line)
        if block_open:
            start = scrubbed.find(block_open)
            if start != -1:
                end = scrubbed.find(block_close, start + len(block_open))
                if end == -1:
                    found.append((number, line[start + len(block_open):]))
                    in_block = True
                    continue
                found.append((number, line[start + len(block_open):end]))
                scrubbed = scrubbed[:start] + " " * (end + len(block_close) - start) + scrubbed[end + len(block_close):]
        if line_marker:
            index = scrubbed.find(line_marker)
            if index != -1:
                found.append((number, line[index + len(line_marker):]))
    return found


def git_lines(root: Path, *args: str) -> list[str]:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def scoped_files(root: Path, base: str | None, head: str | None, full_inventory: bool) -> list[str]:
    if full_inventory:
        files = git_lines(root, "ls-files")
    else:
        files = git_lines(root, "diff", "--name-only", "--diff-filter=ACMR", f"{base}...{head or 'HEAD'}")
    return sorted(
        path for path in files
        if not path.startswith(EXCLUDED_PREFIXES) and comment_kind(path) and (root / path).is_file()
    )


def scan(root: Path, files: list[str]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for path in files:
        try:
            text = (root / path).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        kind = comment_kind(path)
        assert kind is not None
        if Path(path).suffix.lower() in {".py", ".pyi"}:
            text = blank_triple_quoted(text)
        for number, comment in comments(text, kind, Path(path).suffix.lower() in {".ps1", ".psm1"}):
            spans: list[tuple[int, int]] = []
            for name, pattern in PATTERNS:
                for match in pattern.finditer(comment):
                    # Report each span once, under the most specific (earliest) pattern.
                    if any(start <= match.start() and match.end() <= end for start, end in spans):
                        continue
                    spans.append(match.span())
                    findings.append(
                        {"path": path, "line": number, "kind": name, "match": match.group(0), "comment": comment.strip()}
                    )
    return findings


def discover_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    configured = os.environ.get("DEVSPARK_REPO_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    try:
        return Path(git_lines(Path.cwd(), "rev-parse", "--show-toplevel")[0]).resolve()
    except (RuntimeError, IndexError):
        return Path.cwd().resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", help="repository root (defaults to the Git top level)")
    parser.add_argument("--base", help="scope: base Git ref")
    parser.add_argument("--head", help="scope: head Git ref (default HEAD)")
    parser.add_argument("--full-inventory", action="store_true", help="scope: every tracked file")
    args = parser.parse_args(argv)
    if args.full_inventory == bool(args.base):
        print("Choose exactly one scope: --base <ref> [--head <ref>] or --full-inventory.", file=sys.stderr)
        return 2
    root = discover_root(args.root)
    try:
        files = scoped_files(root, args.base, args.head, args.full_inventory)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    findings = scan(root, files)
    print(
        json.dumps(
            {
                "scope": "full-inventory" if args.full_inventory else {"base": args.base, "head": args.head or "HEAD"},
                "files_scanned": len(files),
                "findings": findings,
            },
            indent=2,
        )
    )
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
