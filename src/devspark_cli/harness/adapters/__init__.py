"""Harness adapter package."""

from __future__ import annotations

from .base import AgentAdapter, ProbeResult
from .claude_code import ClaudeCodeAdapter
from .copilot import CopilotAdapter
from .cursor import CursorAdapter
from .manual import ManualAdapter
from .noop import NoopAdapter


def get_registered_adapters() -> dict[str, AgentAdapter]:
	"""Return built-in harness adapters keyed by adapter name."""

	return {
		"noop": NoopAdapter(),
		"manual": ManualAdapter(),
		"claude_code": ClaudeCodeAdapter(),
		"copilot": CopilotAdapter(),
		"cursor": CursorAdapter(),
	}


def get_registered_adapter_names() -> list[str]:
	"""Return stable built-in adapter names."""

	return list(get_registered_adapters().keys())
