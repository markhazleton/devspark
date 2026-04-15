"""Claude Code harness adapter."""

from __future__ import annotations

from .base import CommandLineAdapter


class ClaudeCodeAdapter(CommandLineAdapter):
    name = "claude_code"
    description = "Anthropic Claude Code CLI"
    executable = "claude"