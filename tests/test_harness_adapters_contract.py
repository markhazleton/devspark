"""Contract validation for real harness adapters and app-scope resolution.

Run with: python tests/test_harness_adapters_contract.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from devspark_cli.harness.adapters import get_registered_adapters
from devspark_cli.harness.runner import HarnessRunner
from devspark_cli.harness.spec_loader import HarnessSpecError
from devspark_cli.harness.spec_models import RunContext, StepSpec
from devspark_cli.registry import get_app, load_registry
from devspark_cli.scope import resolve_doc_root, resolve_scope


class DummyTelemetry:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict]] = []

    def emit(self, event: str, run_id: str, **payload) -> None:
        self.events.append((event, {"run_id": run_id, **payload}))


def _make_step(prompt_path: Path) -> StepSpec:
    return StepSpec.model_validate(
        {
            "id": "agent-step",
            "type": "agent_task",
            "prompt_file": str(prompt_path),
        }
    )


def _write_registry(repo: Path) -> None:
    doc_root = repo / ".documentation"
    doc_root.mkdir(parents=True, exist_ok=True)
    registry = {
        "version": 1,
        "mode": "multi-app",
        "apps": [
            {"id": "todo", "path": "apps/todo"},
            {"id": "api", "path": "apps/api"},
        ],
    }
    (doc_root / "devspark.json").write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    for app_id in ("todo", "api"):
        (repo / "apps" / app_id / ".documentation").mkdir(parents=True, exist_ok=True)


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo = Path(temp_dir)
        prompt_dir = repo / "prompts"
        prompt_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = prompt_dir / "agent.md"
        prompt_text = "Generate a concise implementation summary.\n" * 2000
        prompt_path.write_text(prompt_text, encoding="utf-8")

        context = RunContext(
            run_id="run_adapter_contract",
            repo_root=str(repo),
            spec_path=str(repo / "sample.harness.yaml"),
            doc_root=str(repo / ".documentation"),
            adapter="noop",
            dry_run=False,
        )

        expected_commands = {
            "claude_code": "claude",
            "copilot": "copilot",
            "cursor": "cursor-agent",
        }

        for adapter_name, executable in expected_commands.items():
            adapter = get_registered_adapters()[adapter_name]
            with patch("shutil.which", return_value=None):
                available, reason = adapter.is_available()
            assert not available
            assert executable in (reason or "")

            telemetry = DummyTelemetry()
            captured: dict[str, object] = {}

            def fake_run(command, cwd, input, capture_output, text, check):
                captured["command"] = command
                captured["cwd"] = cwd
                captured["input"] = input
                return subprocess.CompletedProcess(command, 0, stdout=f"{adapter_name} output", stderr="")

            with patch("shutil.which", return_value=f"/tmp/{executable}"), patch("subprocess.run", side_effect=fake_run):
                response = adapter.execute(_make_step(prompt_path), context, telemetry)

            assert captured["command"] == [executable, "--print"]
            assert captured["cwd"] == context.repo_root
            assert captured["input"] == prompt_text
            assert response.output_text == f"{adapter_name} output"
            assert response.prompt_text == prompt_text
            assert any(event == "harness.tool.called" for event, _ in telemetry.events)

        _write_registry(repo)
        harness_spec = repo / "app-scope.harness.yaml"
        harness_spec.write_text(
            """apiVersion: devspark.ai/v1
kind: HarnessSpec
name: app-scope-test
scope:
  type: app
  app: todo
steps:
  - id: scoped-step
    type: agent_task
    prompt_file: prompts/agent.md
""",
            encoding="utf-8",
        )

        runner = HarnessRunner(harness_spec, adapter_override="noop", repo_root=repo)
        run = runner.execute()
        registry = load_registry(repo)
        scope_ctx = resolve_scope(registry, "todo", False, repo)
        expected_doc_root = resolve_doc_root(get_app(registry, "todo"), repo).resolve()
        assert not scope_ctx.errors
        assert Path(run.context.doc_root) == expected_doc_root
        assert run.status == "complete"

        missing_app_spec = repo / "missing-app.harness.yaml"
        missing_app_spec.write_text(
            """apiVersion: devspark.ai/v1
kind: HarnessSpec
name: missing-app
scope:
  type: app
  app: missing
steps:
  - id: scoped-step
    type: agent_task
    prompt_file: prompts/agent.md
""",
            encoding="utf-8",
        )
        try:
            HarnessRunner(missing_app_spec, adapter_override="noop", repo_root=repo).resolve_context()
        except HarnessSpecError as exc:
            assert "Unknown application" in str(exc)
        else:
            raise AssertionError("Expected unknown app scope to fail")

        ambiguity = resolve_scope(registry, None, False, repo)
        assert ambiguity.errors
        assert "Multiple apps registered" in ambiguity.errors[0]

        invalid_registry_spec = repo / "invalid-registry.harness.yaml"
        invalid_registry_spec.write_text(
            """apiVersion: devspark.ai/v1
kind: HarnessSpec
name: invalid-registry
scope:
  type: app
  app: todo
steps:
  - id: scoped-step
    type: agent_task
    prompt_file: prompts/agent.md
""",
            encoding="utf-8",
        )
        (repo / ".documentation" / "devspark.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "mode": "multi-app",
                    "apps": [{"id": "todo", "path": "apps/missing"}],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        try:
            HarnessRunner(invalid_registry_spec, adapter_override="noop", repo_root=repo).resolve_context()
        except HarnessSpecError as exc:
            assert "Registry path validation failed" in str(exc)
        else:
            raise AssertionError("Expected invalid registry to fail explicitly")

    print("Harness adapter contract validated.")


if __name__ == "__main__":
    main()