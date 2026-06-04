#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "rich",
#     "platformdirs",
#     "readchar",
#     "httpx",
# ]
# ///
"""
DevSpark CLI — Scaffold projects with AI development lifecycle prompts

Usage:
    uvx devspark-cli.py init <project-name>
    uvx devspark-cli.py init .
    uvx devspark-cli.py init --here

Or install globally:
    uv tool install --from devspark-cli.py devspark-cli
    devspark init <project-name>
    devspark init .
    devspark init --here
"""

# Re-export the public API surface used by callers and tests.
from ._app import app  # noqa: F401

# Import command modules so their @app.command() decorators register with `app`.
from .commands import init as _cmd_init  # noqa: F401
from .commands import upgrade as _cmd_upgrade  # noqa: F401
from .commands import lifecycle as _cmd_lifecycle  # noqa: F401

# Re-export upgrade helpers so existing code/tests that access them via the
# top-level devspark_cli namespace continue to work (backward-compatible API).
from ._upgrade_helpers import read_version_stamp, write_version_stamp  # noqa: F401
from .commands.upgrade import (  # noqa: F401
    collect_legacy_artifacts,
    collect_pre_separation_framework_artifacts,
    collect_script_override_summaries,
    collect_structural_override_warnings,
    needs_migration,
    render_upgrade_analysis,
    run_migration_script,
)


def build_app():
    """Construct (and return) the Typer app with all subcommands registered.

    Tests use this to invoke the CLI without triggering ``app()``.
    Idempotent: repeated calls do not re-register commands.
    """
    if getattr(app, "_devspark_run_commands_registered", False):
        return app
    from .run_commands import register as _register_run_commands
    _register_run_commands(app)
    app._devspark_run_commands_registered = True  # type: ignore[attr-defined]
    return app


def main():
    build_app()
    app()


if __name__ == "__main__":
    main()
