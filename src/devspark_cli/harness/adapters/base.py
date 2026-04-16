"""Adapter protocol and shared response types."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex
import shutil
import subprocess
from typing import Protocol

from ..spec_models import StepSpec

_PLAN_MODE_PREFIX = (
    "PLAN MODE — do NOT write, create, or modify any files. "
    "Describe what you would do instead.\n\n"
)


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


def apply_context_budget(text: str, step: StepSpec, context, telemetry) -> str:
    """Truncate prompt text to step.context_budget characters and emit a policy event if truncated."""
    if step.context_budget is None or len(text) <= step.context_budget:
        return text
    telemetry.emit(
        "harness.policy.blocked",
        context.run_id,
        step_id=step.id,
        reason="context_budget_exceeded",
    )
    return text[: step.context_budget]


class CommandLineAdapter:
    """Base adapter for agent CLIs that accept a prompt as a terminal argument."""

    name = ""
    description = ""
    executable = ""

    def is_available(self) -> tuple[bool, str | None]:
        if shutil.which(self.executable) is not None:
            return True, None
        return False, f"Missing required CLI '{self.executable}' for adapter '{self.name}'"

    def build_command(self) -> list[str]:
        return [self.executable, "--print"]

    def execute(self, step: StepSpec, context, telemetry, prompt_text: str | None = None) -> AgentResponse:
        effective_prompt = load_prompt_text(step, prompt_text)
        # Phase 2: prepend plan-mode instruction so the model does not write files
        execution_mode = getattr(context, "execution_mode", "act")
        if execution_mode == "plan":
            effective_prompt = _PLAN_MODE_PREFIX + effective_prompt
        effective_prompt = apply_context_budget(effective_prompt, step, context, telemetry)
        command = self.build_command()
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
            input=effective_prompt,
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


class CommandLineAdapter:
    """Base adapter for agent CLIs that accept a prompt as a terminal argument."""

    name = ""
    description = ""
    executable = ""

    def is_available(self) -> tuple[bool, str | None]:
        if shutil.which(self.executable) is not None:
            return True, None
        return False, f"Missing required CLI '{self.executable}' for adapter '{self.name}'"

    def build_command(self) -> list[str]:
        return [self.executable, "--print"]

    def execute(self, step: StepSpec, context, telemetry, prompt_text: str | None = None) -> AgentResponse:
        effective_prompt = load_prompt_text(step, prompt_text)
        command = self.build_command()
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
            input=effective_prompt,
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