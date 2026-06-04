"""OpenAI Codex CLI harness adapter."""

from __future__ import annotations

from .base import CommandLineAdapter


class CodexAdapter(CommandLineAdapter):
    name = "codex"
    description = "OpenAI Codex CLI"
    executable = "codex"

    def build_command(self) -> list[str]:
        return [self.executable, "exec", "--sandbox", "workspace-write", "-"]
