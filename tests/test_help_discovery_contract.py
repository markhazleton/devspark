"""CLI help discovery contract test (T047)."""

from __future__ import annotations

from typer.testing import CliRunner

from devspark_cli import build_app


runner = CliRunner()


def _invoke(*args):
    app = build_app()
    return runner.invoke(app, list(args))


def test_default_help_lists_aliases_first():
    res = _invoke("help")
    assert res.exit_code == 0, res.output
    out = res.output
    aliases_idx = out.find("Aliases (recommended entrypoints):")
    workflows_idx = out.find("Workflows:")
    atomic_idx = out.find("Atomic prompts:")
    assert aliases_idx >= 0 and workflows_idx > aliases_idx
    # Atomic prompts come after workflows.
    if atomic_idx >= 0:
        assert atomic_idx > workflows_idx


def test_default_help_hides_unexposed_prompts():
    res = _invoke("help")
    # Legacy shims are exposed: false; they should not appear by default.
    assert "implement " not in res.output or "(expert)" not in res.output


def test_all_flag_includes_hidden_prompts():
    res = _invoke("help", "--all")
    assert res.exit_code == 0
    # legacy `implement` shim has audience=expert; must appear with --all.
    assert "implement" in res.output


def test_category_filter():
    res = _invoke("help", "--all", "--category", "improvement")
    assert res.exit_code == 0
    assert "improvement" in res.output
    # Other categories should not appear under the atomic prompts heading.
    assert "[legacy-command]" not in res.output


def test_audience_filter():
    res = _invoke("help", "--all", "--audience", "intermediate")
    assert res.exit_code == 0
    # capture-context is intermediate.
    assert "capture-context" in res.output
