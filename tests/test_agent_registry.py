"""Basic validation for the shared agent registry."""

from __future__ import annotations

import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location(
    "devspark_cli.agent_registry",
    str(ROOT / "src" / "devspark_cli" / "agent_registry.py"),
)
module = importlib.util.module_from_spec(spec)
sys.modules["devspark_cli.agent_registry"] = module
assert spec.loader is not None
spec.loader.exec_module(module)

AGENT_CONFIG = module.AGENT_CONFIG
REGISTRY_PATH = module.REGISTRY_PATH
load_agent_registry = module.load_agent_registry


def main() -> None:
    registry = load_agent_registry()
    assert REGISTRY_PATH.is_file(), f"Registry file missing: {REGISTRY_PATH}"
    assert registry, "Registry should contain at least one agent"
    assert "copilot" in AGENT_CONFIG, "copilot must be present in shared registry"
    assert "claude" in AGENT_CONFIG, "claude must be present in shared registry"

    for agent in registry:
        assert agent["key"] == agent["key"].strip(), f"Agent key has unexpected whitespace: {agent['key']!r}"
        assert agent["context_file"], f"Missing context_file for {agent['key']}"
        release = agent.get("release", {})
        assert release.get("commands_dir"), f"Missing release.commands_dir for {agent['key']}"
        assert release.get("extension"), f"Missing release.extension for {agent['key']}"
        assert release.get("arg_format"), f"Missing release.arg_format for {agent['key']}"

    print(f"Validated {len(registry)} agents from {REGISTRY_PATH.name}.")


if __name__ == "__main__":
    main()