"""Shared DevSpark agent registry loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_REPO_REGISTRY_PATH = Path(__file__).resolve().parents[2] / "agents-registry.json"
_PACKAGE_REGISTRY_PATH = Path(__file__).with_name("agents-registry.json")
REGISTRY_PATH = _REPO_REGISTRY_PATH if _REPO_REGISTRY_PATH.is_file() else _PACKAGE_REGISTRY_PATH


def load_agent_registry(path: Path | None = None) -> list[dict[str, Any]]:
    """Load the static agent registry from the repository root."""
    registry_path = path or REGISTRY_PATH
    raw = json.loads(registry_path.read_text(encoding="utf-8"))
    agents = raw.get("agents")
    if not isinstance(agents, list) or not agents:
        raise ValueError(f"Invalid agent registry at {registry_path}")
    return agents


def load_agent_config(path: Path | None = None) -> dict[str, dict[str, Any]]:
    """Return agent registry keyed by agent key for CLI/runtime lookups."""
    config: dict[str, dict[str, Any]] = {}
    for agent in load_agent_registry(path):
        key = agent.get("key")
        if not isinstance(key, str) or not key:
            raise ValueError("Agent registry entries require a non-empty 'key'")
        config[key] = agent
    return config


AGENT_CONFIG = load_agent_config()