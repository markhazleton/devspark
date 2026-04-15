"""GitHub Copilot harness adapter."""

from __future__ import annotations

from .base import CommandLineAdapter


class CopilotAdapter(CommandLineAdapter):
    name = "copilot"
    description = "GitHub Copilot CLI"
    executable = "copilot"