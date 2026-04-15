"""No-op harness adapter."""

from __future__ import annotations

from ..spec_models import StepSpec
from .base import AgentResponse, load_prompt_text


class NoopAdapter:
    name = "noop"
    description = "Always available (no AI required)"

    def is_available(self) -> tuple[bool, str | None]:
        return True, None

    def execute(self, step: StepSpec, context, telemetry, prompt_text: str | None = None) -> AgentResponse:
        effective_prompt = load_prompt_text(step, prompt_text)
        preview = effective_prompt[:200] if effective_prompt else f"noop:{step.id}"
        telemetry.emit(
            "harness.tool.called",
            context.run_id,
            step_id=step.id,
            tool=self.name,
            command_preview=preview,
        )
        return AgentResponse(output_text="", prompt_text=effective_prompt, command_preview=preview)