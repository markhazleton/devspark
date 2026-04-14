"""Adapter protocol and shared response types."""

from __future__ import annotations

from dataclasses import dataclass
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