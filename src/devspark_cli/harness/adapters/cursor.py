"""Cursor harness adapter."""

from __future__ import annotations

from .base import CommandLineAdapter


class CursorAdapter(CommandLineAdapter):
    name = "cursor"
    description = "Cursor agent CLI"
    executable = "cursor-agent"