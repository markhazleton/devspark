"""No-op harness adapter."""

from __future__ import annotations

from ..spec_models import StepSpec
from .base import AgentResponse, ProbeResult, apply_context_budget, load_prompt_text


class NoopAdapter:
    name = "noop"
    description = "Always available (no AI required)"

    def is_available(self) -> tuple[bool, str | None]:
        return True, None

    def probe(self) -> ProbeResult:
        return ProbeResult(
            can_read=True,
            can_write=False,
            is_interactive=False,
            ready=True,
            diagnostics=["Noop adapter does not execute write operations."],
        )

    def execute(self, step: StepSpec, context, telemetry, prompt_text: str | None = None) -> AgentResponse:
        effective_prompt = load_prompt_text(step, prompt_text)
        effective_prompt = apply_context_budget(effective_prompt, step, context, telemetry)
        preview = effective_prompt[:200] if effective_prompt else f"noop:{step.id}"
        telemetry.emit(
            "harness.tool.called",
            context.run_id,
            step_id=step.id,
            tool=self.name,
            command_preview=preview,
        )
        return AgentResponse(output_text="", prompt_text=effective_prompt, command_preview=preview)