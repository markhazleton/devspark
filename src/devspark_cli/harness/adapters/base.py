"""Adapter protocol and shared response types."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex
import shutil
import subprocess
from typing import Protocol

from ..spec_models import StepSpec


@dataclass(slots=True)
class AgentResponse:
    output_text: str = ""
    prompt_text: str = ""
    command_preview: str = ""


class AgentAdapter(Protocol):
    name: str

    def is_available(self) -> tuple[bool, str | None]:
        ...

    def execute(self, step: StepSpec, context, telemetry, prompt_text: str | None = None) -> AgentResponse:
        ...


def load_prompt_text(step: StepSpec, prompt_text: str | None = None) -> str:
    """Load the effective prompt text for an adapter step."""

    if prompt_text is not None:
        return prompt_text
    if not step.prompt_file:
        return ""
    return Path(step.prompt_file).read_text(encoding="utf-8")


class CommandLineAdapter:
    """Base adapter for agent CLIs that accept a prompt as a terminal argument."""

    name = ""
    description = ""
    executable = ""

    def is_available(self) -> tuple[bool, str | None]:
        if shutil.which(self.executable) is not None:
            return True, None
        return False, f"Missing required CLI '{self.executable}' for adapter '{self.name}'"

    def build_command(self, prompt_text: str) -> list[str]:
        return [self.executable, "--print", prompt_text]

    def execute(self, step: StepSpec, context, telemetry, prompt_text: str | None = None) -> AgentResponse:
        effective_prompt = load_prompt_text(step, prompt_text)
        command = self.build_command(effective_prompt)
        preview = shlex.join(command)
        telemetry.emit(
            "harness.tool.called",
            context.run_id,
            step_id=step.id,
            tool=self.name,
            command_preview=preview,
        )
        completed = subprocess.run(
            command,
            cwd=context.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            error_text = (completed.stderr or completed.stdout or "CLI execution failed").strip()
            raise RuntimeError(f"{self.name} exited with code {completed.returncode}: {error_text}")
        return AgentResponse(
            output_text=completed.stdout,
            prompt_text=effective_prompt,
            command_preview=preview,
        )