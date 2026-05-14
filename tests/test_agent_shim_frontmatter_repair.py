"""Tests for repairing malformed Copilot agent shim frontmatter quoting."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

agent_registry_spec = importlib.util.spec_from_file_location(
    "devspark_cli.agent_registry",
    str(SRC / "devspark_cli" / "agent_registry.py"),
)
agent_registry_module = importlib.util.module_from_spec(agent_registry_spec)
sys.modules["devspark_cli.agent_registry"] = agent_registry_module
assert agent_registry_spec.loader is not None
agent_registry_spec.loader.exec_module(agent_registry_module)

cli_spec = importlib.util.spec_from_file_location(
    "devspark_cli",
    str(SRC / "devspark_cli" / "__init__.py"),
    submodule_search_locations=[str(SRC / "devspark_cli")],
)
cli_module = importlib.util.module_from_spec(cli_spec)
sys.modules["devspark_cli"] = cli_module
assert cli_spec.loader is not None
cli_spec.loader.exec_module(cli_module)

from devspark_cli._template import repair_agent_shim_frontmatter


def test_repair_agent_shim_frontmatter_fixes_double_quoted_values(tmp_path: Path) -> None:
    project = tmp_path / "repo"
    agents = project / ".github" / "agents"
    agents.mkdir(parents=True)

    bad_shim = agents / "devspark.specify.agent.md"
    bad_shim.write_text(
        """---
name: ""devspark.specify""
description: ""DevSpark specify command shim""
---

## Prompt Resolution

Body text.
""",
        encoding="utf-8",
    )

    repaired = repair_agent_shim_frontmatter(project)

    assert repaired == 1
    fixed = bad_shim.read_text(encoding="utf-8")
    assert 'name: "devspark.specify"' in fixed
    assert 'description: "DevSpark specify command shim"' in fixed
    assert '""devspark.specify""' not in fixed


def test_repair_agent_shim_frontmatter_noop_when_files_are_valid(tmp_path: Path) -> None:
    project = tmp_path / "repo"
    agents = project / ".github" / "agents"
    agents.mkdir(parents=True)

    good_shim = agents / "devspark.plan.agent.md"
    original = """---
name: "devspark.plan"
description: "DevSpark plan command shim"
---

Body.
"""
    good_shim.write_text(original, encoding="utf-8")

    repaired = repair_agent_shim_frontmatter(project)

    assert repaired == 0
    assert good_shim.read_text(encoding="utf-8") == original
