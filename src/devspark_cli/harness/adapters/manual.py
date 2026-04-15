"""Manual harness adapter for copy/paste workflows."""

from __future__ import annotations

import sys

import readchar
from rich.console import Console
from rich.panel import Panel

from ..spec_models import StepSpec
from .base import AgentResponse, load_prompt_text


class ManualAdapter:
    name = "manual"
    description = "Copy/paste workflow for IDE agents"

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console(stderr=True)

    def is_available(self) -> tuple[bool, str | None]:
        return True, None

    def execute(self, step: StepSpec, context, telemetry, prompt_text: str | None = None) -> AgentResponse:
        if not sys.stdout.isatty():
            reason = "manual_gate_requires_tty"
            telemetry.emit(
                "harness.policy.blocked",
                context.run_id,
                step_id=step.id,
                reason=reason,
            )
            raise RuntimeError(reason)

        effective_prompt = load_prompt_text(step, prompt_text)
        preview = effective_prompt[:200] if effective_prompt else f"manual:{step.id}"
        telemetry.emit(
            "harness.tool.called",
            context.run_id,
            step_id=step.id,
            tool=self.name,
            command_preview=preview,
        )
        self.console.print(Panel(effective_prompt or f"Complete step {step.id} and press any key.", title=f"Manual Step: {step.name or step.id}"))
        self.console.print("Press any key when the step is complete.")
        readchar.readkey()
        return AgentResponse(output_text="manual-confirmed", prompt_text=effective_prompt, command_preview=preview)