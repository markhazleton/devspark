"""The developer-facing command surface describes one flow.

Prompt-wording and documentation checks only. They assert what the command prompts, handoffs,
script messages and public pages tell a developer; the routing itself is covered by the
``next-context`` tests in ``test_next_context_resolution_contract.py``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
COMMANDS = ROOT / "templates" / "commands"
SITE = ROOT / "site" / "src"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontmatter(name: str) -> dict:
    return yaml.safe_load(_read(COMMANDS / name).split("---", 2)[1])


def _handoffs(name: str) -> list[dict]:
    return _frontmatter(name).get("handoffs") or []


def test_clarify_on_a_work_branch_asks_in_conversation_and_writes_no_spec():
    text = _read(COMMANDS / "clarify.md")
    paragraph = text.split("**Work branch.**", 1)[1].split("\n\n", 1)[0]

    assert "do not create `spec.md`" in paragraph
    assert "do not write `## Clarifications` into `work.md`" in paragraph
    assert "do not send the developer to `/devspark-specify`" in paragraph
    assert "return to `/devspark-implement`" in paragraph
    assert _handoffs("clarify.md")[0]["agent"] == "devspark-implement"


def test_checklist_on_a_work_branch_writes_no_gate_and_does_not_chain_into_analyze():
    section = _read(COMMANDS / "checklist.md").split("## Work Branch", 1)[1].split("\n## ", 1)[0]

    assert "no `gates/checklist.md`" in section
    assert "return to `/devspark-implement`" in section
    assert [h["agent"] for h in _handoffs("checklist.md")] == ["devspark-implement"]


def test_quickfix_is_an_optional_entry_not_a_route_decision():
    position = _read(COMMANDS / "quickfix.md").split("## Workflow Position", 1)[1].split("\n\n", 2)[1]

    assert position.startswith("Optional entry for a defect you have already diagnosed")
    assert "never routes to this command" in position


@pytest.mark.parametrize(
    ("name", "phrase"),
    [
        ("plan.md", "Optional"),
        ("analyze.md", "On demand for one specific"),
        ("critic.md", "On demand for one specific"),
        ("clarify.md", "For an existing specification"),
        ("checklist.md", "For an existing specification"),
    ],
)
def test_descriptions_say_when_a_non_essential_skill_applies(name: str, phrase: str):
    assert _frontmatter(name)["description"].startswith(phrase)


def test_handoffs_never_ask_specify_for_a_specification_bundle():
    for path in sorted(COMMANDS.glob("*.md")):
        for handoff in _handoffs(path.name):
            if handoff["agent"] != "devspark-specify":
                continue
            wording = f"{handoff['label']} {handoff.get('prompt', '')}".lower()
            assert "spec" not in wording.replace("specify", ""), f"{path.name}: {handoff['label']}"


def test_review_handoffs_reach_the_command_they_name():
    assert _handoffs("pr-review.md")[0]["agent"] == "devspark-address-pr-review"
    critic = {h["agent"]: h for h in _handoffs("critic.md")}
    assert "devspark-specify" not in critic
    assert "existing" in critic["devspark-clarify"]["label"].lower()


def test_nothing_routes_new_work_to_the_legacy_quickfix_entry():
    offering = [p.name for p in sorted(COMMANDS.glob("*.md")) if p.name != "quickfix.md"
                and any(h["agent"] == "devspark-quickfix" for h in _handoffs(p.name))]
    assert offering == []
    assert "`/devspark-quickfix`" not in _read(COMMANDS / "next.md")
    for script in ("scripts/powershell/next-context.ps1", "scripts/bash/next-context.sh"):
        assert "/devspark-quickfix" not in _read(ROOT / script), script


def test_critic_ignores_spec_frontmatter_on_a_work_branch():
    rule = next(p for p in _read(COMMANDS / "critic.md").split("\n\n") if p.startswith("Read YAML frontmatter"))
    assert "On a work branch none of this applies" in rule
    assert "incidental" in rule


@pytest.mark.parametrize(
    "script",
    [
        "scripts/powershell/next-context.ps1",
        "scripts/bash/next-context.sh",
        "scripts/powershell/create-pr.ps1",
        "scripts/bash/create-pr.sh",
    ],
)
def test_script_messages_use_the_hyphenated_slash_command(script: str):
    messages = [line for line in _read(ROOT / script).splitlines() if not line.lstrip().startswith("#")]

    assert not [line for line in messages if re.search(r"""(?:^|[\s'"(`])/devspark\.[a-z]""", line)]
    assert "it will route you" not in "\n".join(messages)


def test_the_home_explorer_starts_on_one_flow():
    script = _read(ROOT / "site" / "templates" / "devspark" / "public" / "main.js")
    ids = re.findall(r'^\s+id: "([a-z-]+)",', script, flags=re.MULTILINE)

    assert ids == ["work", "quickfix", "legacy"]
    assert "DEVSPARK_FLOW_ROUTES[0]" in script


@pytest.mark.parametrize(
    "page",
    [
        "index.md",
        "get-started/quickstart.md",
        "get-started/how-it-works.md",
        "get-started/devspark-and-codex.md",
        "guides/troubleshooting-usage.md",
    ],
)
def test_current_pages_do_not_ask_for_a_route_choice(page: str):
    text = _read(SITE / page).lower()

    for phrase in ("recommends a route", "choose the fix size", "find your route", "full-spec gates"):
        assert phrase not in text, f"{page}: {phrase}"


def test_the_skill_catalog_makes_the_normal_path_obvious():
    catalog = _read(SITE / "guides" / "prompt-lifecycle-mapping.md")
    glance = catalog.split("## At a glance", 1)[1].split("## Invocation format", 1)[0]
    normal = glance.split("### Normal path", 1)[1].split("### ", 1)[0]
    legacy = glance.split("### Existing v9.3 specifications", 1)[1].split("### ", 1)[0]

    for command in ("specify", "next", "implement", "verify", "create-pr"):
        assert f"`/devspark-{command}`" in normal
    for command in ("plan", "tasks", "analyze", "critic", "clarify", "checklist", "planning-review"):
        assert f"`/devspark-{command}`" not in normal
    for command in ("clarify", "checklist", "planning-review"):
        assert f"`/devspark-{command}`" in legacy
