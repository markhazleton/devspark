"""Harness adapter package."""

from __future__ import annotations

from .base import AgentAdapter, ProbeResult
from .claude_code import ClaudeCodeAdapter
from .copilot import CopilotAdapter
from .cursor import CursorAdapter
from .manual import ManualAdapter
from .noop import NoopAdapter
from ..spec_models import AdapterCapabilityProfile


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


def probe_adapter(name: str) -> AdapterCapabilityProfile:
	"""Return normalized adapter capability profile used by adapter doctor."""

	adapters = get_registered_adapters()
	adapter = adapters.get(name)
	if adapter is None:
		return AdapterCapabilityProfile(
			adapter=name,
			state="unavailable",
			is_available=False,
			can_execute_read_only=False,
			can_execute_write=False,
			requires_write_approval=False,
			remediation_guidance="Select one of the built-in adapters.",
			diagnostics=[f"Unknown adapter: {name}"],
		)

	probe: ProbeResult = adapter.probe() if hasattr(adapter, "probe") else ProbeResult()
	if probe.ready and probe.can_write:
		state = "ready"
		guidance = "Adapter is ready for hands-off lifecycle execution."
	elif probe.ready and probe.can_read and probe.is_interactive:
		state = "write_approval_required"
		guidance = "Use interactive mode, or switch to a non-interactive write-capable adapter."
	elif probe.ready and probe.can_read and not probe.can_write:
		state = "write_incompatible"
		guidance = "Adapter supports read-only checks only; use a write-capable adapter for implement/create-pr/pr-review."
	else:
		state = "unavailable"
		guidance = "Install or configure the adapter CLI, then retry adapter doctor."

	return AdapterCapabilityProfile(
		adapter=name,
		state=state,
		is_available=probe.ready,
		can_execute_read_only=probe.can_read,
		can_execute_write=probe.can_write,
		requires_write_approval=probe.is_interactive,
		remediation_guidance=guidance,
		diagnostics=probe.diagnostics or [],
	)
