# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Golden characterization of the legacy 8.x managed entry-point forms.

The captured forms (the unchanged generator output at the branch base and at tag v8.2.0), the
quickstart-authored forms, edited variants generated at run time, foreign files and skill folders
are classified by the test-only retirement oracle. The suite is data-driven: adding a captured file
adds a case. CRLF variants are generated at run time because fixtures are stored with LF endings.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

import tests.legacy_retirement_oracle as oracle


ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "legacy-8x"
CAPTURE_SETS = ("branch-base", "v8.2.0")
CAPTURE_AGENTS = ("copilot", "claude", "gemini")
EXTRA = "Always answer in French."


def _text(path: Path) -> str:
    return path.read_bytes().decode("utf-8").replace("\r\n", "\n")


def _collect(*parts: str) -> list[tuple[str, Path, str]]:
    base = FIXTURES.joinpath(*parts)
    return [(f"{'/'.join(parts)}:{p.relative_to(base).as_posix()}", p, p.relative_to(base).as_posix())
            for p in sorted(base.rglob("*")) if p.is_file()]


def _captured() -> list[tuple[str, Path, str]]:
    found: list[tuple[str, Path, str]] = []
    for tag in CAPTURE_SETS:
        for agent in CAPTURE_AGENTS:
            found += _collect(tag, agent)
    return found


def _quickstart() -> list[tuple[str, Path, str]]:
    found: list[tuple[str, Path, str]] = []
    for agent_dir in sorted(p for p in (FIXTURES / "quickstart").iterdir() if p.is_dir()):
        found += _collect("quickstart", agent_dir.name)
    return found


CAPTURED = _captured()
QUICKSTART = _quickstart()
UNMODIFIED = CAPTURED + QUICKSTART
IDS = [item[0] for item in UNMODIFIED]


def _command(rel: str) -> str:
    return re.match(r"devspark\.([a-z0-9-]+)\.", rel.rsplit("/", 1)[-1]).group(1)


def _variants(rel: str, text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    if rel.endswith(".toml"):
        out["added-paragraph"] = text.rstrip("\n")[:-3] + f"\n{EXTRA}\n\"\"\"\n"
        return out
    out["added-paragraph"] = text.rstrip("\n") + f"\n\n{EXTRA}\n"
    for label, line in (("foreign-name", "name: devspark.other-command"), ("unknown-key", "model: demo-model")):
        if text.startswith("---\n"):
            body = re.sub(r"^name: .*\n", "", text[4:], count=1, flags=re.MULTILINE) if label == "foreign-name" else text[4:]
            out[label] = f"---\n{line}\n{body}"
        else:
            out[label] = f"---\n{line}\n---\n{text}"
    return out


def _tree(tmp_path: Path, *sources: Path) -> Path:
    root = tmp_path / "tree"
    root.mkdir()
    for source in sources:
        shutil.copytree(source, root, dirs_exist_ok=True)
    return root


def test_captured_forms_cover_both_tags_with_and_without_handoffs():
    names = {item[0].split(":")[0].split("/")[0] for item in CAPTURED}
    assert names == set(CAPTURE_SETS)
    with_handoffs = [i for i in CAPTURED if i[1].suffix == ".md" and "handoffs:" in _text(i[1])]
    without = [i for i in CAPTURED if i[1].suffix == ".md" and "handoffs:" not in _text(i[1])]
    assert with_handoffs and without
    assert {Path(i[2]).suffix for i in CAPTURED} == {".md", ".toml"}
    assert any(i[2].endswith(".agent.md") for i in CAPTURED) and any(i[2].endswith(".prompt.md") for i in CAPTURED)


@pytest.mark.parametrize("label,path,rel", UNMODIFIED, ids=IDS)
def test_unmodified_form_is_recognised_in_lf_and_crlf(label, path, rel):
    text = _text(path)
    assert oracle.is_managed_entry_point(rel, text)
    assert oracle.is_managed_entry_point(rel, text.replace("\n", "\r\n"))


@pytest.mark.parametrize("label,path,rel", [c for c in CAPTURED if not c[2].endswith(".prompt.md")], ids=[c[0] for c in CAPTURED if not c[2].endswith(".prompt.md")])
def test_captured_body_is_the_package_form(label, path, rel):
    text = _text(path)
    cmd = _command(rel)
    body = re.sub(r'^description = ".*"\n\nprompt = """\n(.*)"""\n?$', r"\1", text, flags=re.DOTALL) if rel.endswith(".toml") \
        else text.split("\n---\n", 1)[1] if text.startswith("---\n") else text
    assert oracle._normalize(body) in {oracle._normalize(oracle.package_body(cmd, p)) for p in oracle.PACKAGE_PLACEHOLDERS}


@pytest.mark.parametrize("label,path,rel", [c for c in CAPTURED if c[2].endswith(".prompt.md")], ids=[c[0] for c in CAPTURED if c[2].endswith(".prompt.md")])
def test_copilot_prompt_companion_form(label, path, rel):
    assert _text(path) == f"---\nagent: devspark.{_command(rel)}\n---\n"


@pytest.mark.parametrize("label,path,rel", UNMODIFIED, ids=IDS)
def test_edited_variants_are_not_recognised(label, path, rel):
    variants = _variants(rel, _text(path))
    assert variants
    for name, edited in variants.items():
        assert not oracle.is_managed_entry_point(rel, edited), name
        assert not oracle.is_managed_entry_point(rel, edited.replace("\n", "\r\n")), name


def test_a_rendered_form_is_recognised_for_every_stock_command_and_agent():
    commands = oracle.stock_commands()
    assert len(commands) >= 38
    for target in oracle.targets():
        for cmd in commands:
            rel = f"{target['dir']}/devspark.{cmd}.{target['ext']}"
            if target["ext"] == "toml":
                text = f'description = "x"\n\nprompt = """\n{oracle.package_body(cmd, "{{args}}")}"""\n'
            elif target["ext"] == "prompt.md":
                text = oracle.companion_body(cmd)
            else:
                text = oracle.package_body(cmd, "$ARGUMENTS")
            assert oracle.is_managed_entry_point(rel, text), rel
            assert not oracle.is_managed_entry_point(rel, text + f"\n{EXTRA}\n"), rel


def test_quickstart_fixtures_match_the_rendered_quickstart_shapes():
    by_name = {item[0]: _text(item[1]) for item in QUICKSTART}
    for label, text in by_name.items():
        body = text.split("\n---\n", 1)[1] if text.startswith("---\n") else text
        body = re.sub(r'^description = ".*"\n\nprompt = """\n(.*)"""\n?$', r"\1", body, flags=re.DOTALL)
        assert oracle._normalize(body) in oracle.accepted_bodies("specify"), label
    placeholders = {re.search(r"## User Input\n\n(?:```text\n)?(\S+)\n", t).group(1) for t in by_name.values()}
    assert placeholders == {"{{input}}", "$ARGUMENTS", "{{args}}"}
    assert any(t.startswith("---\nname: devspark.specify\n") for t in by_name.values())
    assert any(not t.startswith("---") and "{{input}}" in t for t in by_name.values())


def test_foreign_files_and_skills_are_left_alone_or_reported(tmp_path):
    plan = oracle.plan(_tree(tmp_path, FIXTURES / "foreign"))
    assert plan.delete == [] and plan.quarantine == []
    assert sorted(plan.report) == [".github/skills/devspark-retired-demo", ".github/skills/devspark-specify"]
    assert ".github/agents/devspark.custom-audit.agent.md" in plan.untouched
    assert ".github/skills/devspark-next/SKILL.md" in plan.untouched
    assert ".github/skills/team-helper/SKILL.md" in plan.untouched
    assert ".github/copilot-instructions.md" in plan.untouched


def _seed_existing(root: Path) -> dict[str, bytes]:
    existing = {
        ".devspark.work/commands/devspark.specify.md": b"# Team customization\n",
        ".devspark.work/notes/keep.md": b"Keep me.\n",
        ".knowledge/guides/overview.md": b"# Overview\n",
        ".archive/2026-01-01/old.md": b"old\n",
    }
    for rel, data in existing.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return existing


def test_apply_deletes_quarantines_reports_and_is_idempotent(tmp_path):
    root = _tree(tmp_path, FIXTURES / "branch-base" / "copilot", FIXTURES / "quickstart" / "claude", FIXTURES / "foreign")
    existing = _seed_existing(root)
    edited_rel = ".github/agents/devspark.next.agent.md"
    edited_text = _text(root / edited_rel) + f"\n{EXTRA}\n"
    (root / edited_rel).write_bytes(edited_text.replace("\n", "\r\n").encode("utf-8"))
    edited_bytes = (root / edited_rel).read_bytes()
    foreign = {p.relative_to(FIXTURES / "foreign").as_posix(): p.read_bytes()
               for p in (FIXTURES / "foreign").rglob("*") if p.is_file()}
    collision = root / oracle.QUARANTINE / "devspark.next.agent.md"
    collision.parent.mkdir(parents=True, exist_ok=True)
    collision.write_bytes(b"earlier quarantine\n")
    existing[collision.relative_to(root).as_posix()] = b"earlier quarantine\n"

    expected_deleted = sorted(
        p.relative_to(root).as_posix() for p in root.rglob("devspark.*") if p.is_file() and p.relative_to(root).as_posix() != edited_rel
        and oracle.has_managed_name(p.relative_to(root).as_posix())
    )
    first = oracle.apply(root).as_dict()
    assert first[oracle.QUARANTINE_ACTION] == [edited_rel]
    assert first[oracle.DELETE] == expected_deleted and first[oracle.DELETE]
    assert sorted(first[oracle.REPORT]) == [".github/skills/devspark-retired-demo", ".github/skills/devspark-specify"]

    assert (root / oracle.QUARANTINE / "devspark.next.agent.md").read_bytes() == b"earlier quarantine\n"
    assert (root / oracle.QUARANTINE / "devspark.next.agent.md.2").read_bytes() == edited_bytes
    assert not (root / edited_rel).exists()
    for rel, data in {**existing, **foreign}.items():
        assert (root / rel).read_bytes() == data, rel

    snapshot = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    for _ in range(2):
        again = oracle.apply(root).as_dict()
        assert again[oracle.DELETE] == [] and again[oracle.QUARANTINE_ACTION] == []
        assert {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()} == snapshot


def test_an_interrupted_run_is_recomputed_from_what_remains(tmp_path):
    root = _tree(tmp_path, FIXTURES / "branch-base" / "claude")
    files = sorted((root / ".claude" / "commands").glob("devspark.*.md"))
    assert len(files) >= 4
    files[0].unlink()
    files[1].unlink()
    plan = oracle.plan(root)
    assert sorted(plan.delete) == sorted(f".claude/commands/{p.name}" for p in files[2:])
    oracle.apply(root)
    assert not list((root / ".claude" / "commands").glob("devspark.*"))
    assert oracle.plan(root).as_dict() == {"delete": [], "quarantine": [], "report": [], "untouched": []}


UPGRADE = FIXTURES.parent / "upgrade"
UPGRADE_TREES = {
    "plain-copilot": (4, 0, 0),
    "quickstart-shim": (3, 0, 0),
    "customized": (2, 0, 0),
    "edited-shim": (3, 1, 0),
    "interrupted": (2, 0, 0),
    "foreign-files": (1, 0, 2),
    "md-agent": (2, 0, 0),
    "toml-agent": (2, 0, 0),
}


def test_every_upgrade_tree_has_an_expected_outcome():
    present = {p.name for p in UPGRADE.iterdir() if p.is_dir() and p.name != "_common"}
    assert present == set(UPGRADE_TREES)


@pytest.mark.parametrize("name", sorted(UPGRADE_TREES))
def test_upgrade_tree_is_retired_without_touching_user_content(tmp_path, name):
    root = _tree(tmp_path, UPGRADE / "_common", UPGRADE / name)
    before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    deletes, quarantines, reports = UPGRADE_TREES[name]
    result = oracle.apply(root).as_dict()
    assert (len(result["delete"]), len(result["quarantine"]), len(result["report"])) == (deletes, quarantines, reports)
    for rel in result["untouched"] + result["report"]:
        if (root / rel).is_file():
            assert (root / rel).read_bytes() == before[rel], rel
    for rel, data in before.items():
        if rel.startswith((".devspark/", ".devspark.work/", ".knowledge/", ".archive/")):
            assert (root / rel).read_bytes() == data, rel
    assert oracle.apply(root).as_dict()["delete"] == []
    assert oracle.plan(root).quarantine == []
