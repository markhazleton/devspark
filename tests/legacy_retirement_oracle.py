# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Test-only oracle for retiring legacy 8.x dotted entry points.

Never shipped. It encodes the structural recognition rule and the resulting actions so fixtures
can be classified without hashes: description text, handoffs and wording vary across 8.x releases
and quickstart output, so a managed entry point is recognised by location, name, frontmatter keys
and the exact generated body shape.

Actions: delete (unmodified managed entry point), quarantine (managed-name file that fails
recognition, moved byte-identical under the quarantine directory with a numeric suffix on
collision), report (skill folder conflict or orphan managed skill) and untouched (everything else).

Assumption: the consumer skill generated marker is a fixed path-free comment. The constant below
stands in for it; fixtures use the same constant.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from tests.consumer_skill_helpers import SKILL_MARKER


ROOT = Path(__file__).resolve().parent.parent
QUARANTINE = Path(".devspark.work") / "migration" / "8.x-entry-points"
SKILL_DIRS = (".github/skills",)
FRONTMATTER_KEYS = {"description", "handoffs", "agent", "name"}
PLACEHOLDERS = ("$ARGUMENTS", "{{input}}", "{{args}}")
PACKAGE_PLACEHOLDERS = ("$ARGUMENTS", "{{args}}")
CLOSING = "Pass the user input above to the resolved prompt."
UNTOUCHABLE_ROOTS = (".devspark.work", ".knowledge", ".archive")

DELETE = "delete"
QUARANTINE_ACTION = "quarantine"
REPORT = "report"
UNTOUCHED = "untouched"


def stock_commands(root: Path = ROOT) -> list[str]:
    return sorted(p.stem for p in (root / "templates" / "commands").glob("*.md"))


def targets(root: Path = ROOT) -> list[dict]:
    """Every (directory, extension) pair a managed entry point can live in."""
    registry = json.loads((root / "agents-registry.json").read_text(encoding="utf-8"))
    found: dict[tuple[str, str], str] = {
        (".github/agents", "agent.md"): "copilot",
        (".github/prompts", "prompt.md"): "copilot",
    }
    for agent in registry["agents"]:
        release = agent["release"]
        if "commands_dir" not in release:
            continue
        found[(release["commands_dir"], release["extension"])] = agent["key"]
        if release.get("prompt_dir"):
            found[(release["prompt_dir"], "prompt.md")] = agent["key"]
    return [{"dir": d, "ext": e, "agent": a} for (d, e), a in sorted(found.items())]


def resolution_section(cmd: str) -> str:
    return (
        "## Prompt Resolution\n\n"
        "Determine the current git user by running `git config user.name`.\n"
        "Normalize to a folder-safe slug: lowercase, replace spaces with hyphens, "
        "strip non-alphanumeric/hyphen chars.\n\n"
        "Read and execute the instructions from the **first file that exists**:\n"
        f"1. `.devspark.work/{{git-user}}/commands/devspark.{cmd}.md` (personalized override)\n"
        f"2. `.devspark.work/commands/devspark.{cmd}.md` (team customization)\n"
        f"3. `.devspark/defaults/commands/devspark.{cmd}.md` (stock default)\n"
    )


WHERE_LINE = "Where `{git-user}` is the normalized slug from step above.\n"


def package_body(cmd: str, placeholder: str) -> str:
    return (
        resolution_section(cmd) + "\n" + WHERE_LINE + "\n## User Input\n\n"
        f"```text\n{placeholder}\n```\n\n{CLOSING}\n"
    )


def quickstart_body(cmd: str, placeholder: str, *, fenced: bool = False, where: bool = False) -> str:
    holder = f"```text\n{placeholder}\n```" if fenced else placeholder
    middle = "\n" + WHERE_LINE if where else ""
    return resolution_section(cmd) + middle + f"\n## User Input\n\n{holder}\n\n{CLOSING}\n"


def companion_body(cmd: str, *, where: bool = False) -> str:
    return resolution_section(cmd) + ("\n" + WHERE_LINE if where else "")


def _normalize(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    return "\n".join(lines).strip("\n") + "\n"


def accepted_bodies(cmd: str) -> set[str]:
    bodies = {_normalize(package_body(cmd, p)) for p in PACKAGE_PLACEHOLDERS}
    for placeholder in PLACEHOLDERS:
        for fenced in (False, True):
            for where in (False, True):
                bodies.add(_normalize(quickstart_body(cmd, placeholder, fenced=fenced, where=where)))
    bodies.add(_normalize(companion_body(cmd)))
    bodies.add(_normalize(companion_body(cmd, where=True)))
    return bodies


def _split_markdown(text: str) -> tuple[dict | None, str] | None:
    """Return (frontmatter or None, body); None when the frontmatter is unparseable."""
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        if text.endswith("\n---"):
            end = len(text) - 4
        else:
            return None
    try:
        data = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError:
        return None
    return (data if isinstance(data, dict) else None), text[end + 5 :]


def _frontmatter_ok(front: dict, cmd: str, ext: str) -> bool:
    if set(front) - FRONTMATTER_KEYS:
        return False
    if "name" in front and front["name"] != f"devspark.{cmd}":
        return False
    if "agent" in front and front["agent"] != f"devspark.{cmd}":
        return False
    handoffs = front.get("handoffs")
    if handoffs is not None:
        if not isinstance(handoffs, list):
            return False
        for item in handoffs:
            if not isinstance(item, dict) or set(item) - {"label", "agent", "prompt", "send"}:
                return False
    return True


def _markdown_recognised(text: str, cmd: str, ext: str) -> bool:
    split = _split_markdown(text)
    if split is None:
        return False
    front, body = split
    if front is None and body.lstrip("\n").startswith("---"):
        return False
    if front is not None and not _frontmatter_ok(front, cmd, ext):
        return False
    if ext == "prompt.md" and front is not None and not body.strip():
        return front.get("agent") == f"devspark.{cmd}" and set(front) == {"agent"}
    if ext == "prompt.md" and front is not None:
        return False
    return _normalize(body) in accepted_bodies(cmd)


def _toml_recognised(text: str, cmd: str) -> bool:
    text = text.replace("\r\n", "\n")
    match = re.fullmatch(r'description = "(.*)"\n\nprompt = """\n(.*)"""\n?', text, flags=re.DOTALL)
    if not match:
        return False
    return _normalize(match.group(2)) in accepted_bodies(cmd)


def is_managed_entry_point(rel: str, text: str, root: Path = ROOT) -> bool:
    """True when the file is an unmodified managed entry point for a stock command."""
    rel = rel.replace("\\", "/")
    directory, _, name = rel.rpartition("/")
    for target in targets(root):
        if target["dir"] != directory:
            continue
        suffix = "." + target["ext"]
        match = re.fullmatch(r"devspark\.([a-z0-9-]+)" + re.escape(suffix), name)
        if not match or match.group(1) not in stock_commands(root):
            continue
        cmd = match.group(1)
        if target["ext"] == "toml":
            ok = _toml_recognised(text, cmd)
        else:
            ok = _markdown_recognised(text, cmd, target["ext"])
        if ok:
            return True
    return False


def has_managed_name(rel: str, root: Path = ROOT) -> bool:
    rel = rel.replace("\\", "/")
    directory, _, name = rel.rpartition("/")
    for target in targets(root):
        if target["dir"] != directory:
            continue
        match = re.fullmatch(r"devspark\.([a-z0-9-]+)\." + re.escape(target["ext"]), name)
        if match and match.group(1) in stock_commands(root):
            return True
    return False


@dataclass
class Plan:
    delete: list[str] = field(default_factory=list)
    quarantine: list[str] = field(default_factory=list)
    report: list[str] = field(default_factory=list)
    untouched: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, list[str]]:
        return {
            DELETE: sorted(self.delete),
            QUARANTINE_ACTION: sorted(self.quarantine),
            REPORT: sorted(self.report),
            UNTOUCHED: sorted(self.untouched),
        }


def _files(root: Path) -> list[str]:
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and ".git/" not in p.as_posix())


def _skill_findings(root: Path) -> list[str]:
    cmds = set(stock_commands())
    found: list[str] = []
    for base in SKILL_DIRS:
        skills = root / base
        if not skills.is_dir():
            continue
        for folder in sorted(p for p in skills.iterdir() if p.is_dir() and p.name.startswith("devspark-")):
            cmd = folder.name.removeprefix("devspark-")
            skill = folder / "SKILL.md"
            marked = skill.is_file() and SKILL_MARKER in skill.read_text(encoding="utf-8")
            if marked and cmd not in cmds:
                found.append(f"{base}/{folder.name}")
            elif not marked and cmd in cmds:
                found.append(f"{base}/{folder.name}")
    return found


def plan(root: Path) -> Plan:
    result = Plan()
    reported = _skill_findings(root)
    result.report.extend(reported)
    for rel in _files(root):
        parts = rel.split("/")
        if parts[0] in UNTOUCHABLE_ROOTS:
            result.untouched.append(rel)
        elif any(rel.startswith(f"{base}/devspark-") for base in SKILL_DIRS):
            if "/".join(parts[:3]) not in reported:
                result.untouched.append(rel)
        elif has_managed_name(rel):
            text = (root / rel).read_text(encoding="utf-8", errors="surrogateescape")
            (result.delete if is_managed_entry_point(rel, text) else result.quarantine).append(rel)
        else:
            result.untouched.append(rel)
    return result


def _free_name(directory: Path, name: str) -> Path:
    candidate = directory / name
    index = 1
    while candidate.exists():
        index += 1
        candidate = directory / f"{name}.{index}"
    return candidate


def apply(root: Path) -> Plan:
    """Carry out the plan; a second call finds nothing left to do."""
    current = plan(root)
    for rel in current.delete:
        (root / rel).unlink()
    if current.quarantine:
        target_dir = root / QUARANTINE
        target_dir.mkdir(parents=True, exist_ok=True)
        for rel in current.quarantine:
            destination = _free_name(target_dir, Path(rel).name)
            shutil.move(str(root / rel), str(destination))
    return current
