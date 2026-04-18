"""Validation that all stock command templates with {SCRIPT} in their body
include the 2-tier script resolution instruction.

This enforces the fix for the issue where .documentation/scripts/ overrides
were silently ignored because stock templates hardcoded .devspark/scripts/ paths.

Run with: python tests/test_script_resolution_contract.py
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
COMMANDS_DIR = ROOT / "templates" / "commands"

RESOLUTION_MARKER = "2-tier override check"


def _get_templates_with_script() -> list[Path]:
    """Return all command template files that reference {SCRIPT} in their body."""
    templates = []
    for path in sorted(COMMANDS_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        # Strip frontmatter: split on '---' with maxsplit=2.
        # A well-formed YAML front matter yields 3 parts:
        #   ["", "<frontmatter>", "<body>"]
        # Any other split count means the file lacks proper closed frontmatter;
        # fall back to searching the full content to avoid false negatives.
        parts = content.split("---", 2)
        body = parts[2] if len(parts) == 3 else content
        if "{SCRIPT}" in body or "{AGENT_SCRIPT}" in body:
            templates.append(path)
    return templates


def main() -> None:
    templates_with_script = _get_templates_with_script()
    assert templates_with_script, "Expected to find command templates that use {SCRIPT}"

    missing = []
    for path in templates_with_script:
        content = path.read_text(encoding="utf-8")
        if RESOLUTION_MARKER not in content:
            missing.append(path.name)

    if missing:
        raise AssertionError(
            f"The following command templates use {{SCRIPT}} but are missing the "
            f"2-tier script resolution instruction:\n"
            + "\n".join(f"  - templates/commands/{name}" for name in missing)
        )

    print(
        f"Script resolution contract validated: "
        f"{len(templates_with_script)} templates all contain resolution instruction."
    )


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# Tiered resolver contract (T016): atomic prompts / workflows / aliases
# resolve through the same 3-tier (personal -> team -> stock) chain as
# templates/commands/.
# ---------------------------------------------------------------------------

import shutil
import sys

# Ensure src/ on path
sys.path.insert(0, str(ROOT / "src"))

from devspark_cli.resolution import (  # noqa: E402
    build_alias_chain,
    build_atomic_prompt_chain,
    build_workflow_chain,
    resolve_alias,
    resolve_atomic_prompt,
    resolve_workflow,
)


def _populate(tmp, kind_dirs, filename, body=""):
    for d in kind_dirs:
        d.mkdir(parents=True, exist_ok=True)
    target = kind_dirs[0] / filename
    target.write_text(body, encoding="utf-8")
    return target


def test_atomic_prompt_chain_personal_overrides_team(tmp_path):
    user = "alice"
    chain = build_atomic_prompt_chain(tmp_path, app=None, git_user=user)
    # Personal layer should appear before team
    user_dir = tmp_path / ".documentation" / user / "templates" / "prompts" / "atomic"
    team_dir = tmp_path / ".documentation" / "templates" / "prompts" / "atomic"
    assert chain.index(user_dir) < chain.index(team_dir)


def test_workflow_chain_app_overrides_team(tmp_path):
    from devspark_cli.registry import AppDefinition

    app = AppDefinition(
        id="web",
        name="Web",
        path="apps/web",
        kind="web",
    )
    chain = build_workflow_chain(tmp_path, app=app)
    app_dir = tmp_path / "apps" / "web" / ".documentation" / "templates" / "workflows"
    team_dir = tmp_path / ".documentation" / "templates" / "workflows"
    assert chain.index(app_dir) < chain.index(team_dir)


def test_resolve_atomic_prompt_finds_first(tmp_path):
    team = tmp_path / ".documentation" / "templates" / "prompts" / "atomic"
    team.mkdir(parents=True)
    (team / "specify.md").write_text("team-version", encoding="utf-8")
    found = resolve_atomic_prompt("specify", tmp_path)
    assert found is not None
    assert found.read_text(encoding="utf-8") == "team-version"


def test_resolve_workflow_returns_none_when_missing(tmp_path):
    assert resolve_workflow("nope", tmp_path) is None


def test_resolve_alias_returns_none_when_missing(tmp_path):
    assert resolve_alias("nope", tmp_path) is None
