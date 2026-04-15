"""Contract validation for the standalone harness validation engine.

Run with: python tests/test_harness_validation_contract.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from devspark_cli.harness.runner import HarnessRunner
from devspark_cli.harness.spec_models import RetryPolicy, RunContext, StepSpec, ValidationRule
from devspark_cli.harness.validation import ValidationEngine


def main() -> None:
    engine = ValidationEngine()
    with tempfile.TemporaryDirectory() as temp_dir:
        repo = Path(temp_dir)
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.name", "DevSpark Test"], cwd=repo, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "devspark@example.com"], cwd=repo, check=True, capture_output=True, text=True)

        target = repo / "target.txt"
        target.write_text("alpha beta gamma", encoding="utf-8")
        schema = repo / "schema.json"
        schema.write_text(json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object", "required": ["apiVersion"]}), encoding="utf-8")
        yaml_target = repo / "payload.yaml"
        yaml_target.write_text("apiVersion: devspark.ai/v1\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
        subprocess.run(["git", "commit", "-m", "fixture"], cwd=repo, check=True, capture_output=True, text=True)

        context = RunContext(run_id="run_test", repo_root=str(repo), spec_path=str(repo / "sample.yaml"), doc_root=str(repo / ".documentation"), adapter="noop", dry_run=False)
        step_dir = repo / "step"
        step_dir.mkdir()

        rules = [
            ValidationRule(id="always", type="always.pass", severity="warning"),
            ValidationRule(id="exists", type="file.exists", severity="error", path=str(target)),
            ValidationRule(id="contains", type="file.contains", severity="error", path=str(target), contains="beta"),
            ValidationRule(id="command", type="command.exit_code", severity="error", command="git --version"),
            ValidationRule(id="schema", type="json.schema", severity="error", schema_file=str(schema), target_file=str(yaml_target)),
          ValidationRule(id="clean", type="git.clean", severity="warning", path="target.txt"),
            ValidationRule(id="regex", type="regex.match", severity="error", path=str(target), pattern="alpha\\sbeta"),
        ]
        findings = [engine.evaluate(rule, context, step_dir) for rule in rules]
        assert all(finding.status == "passed" for finding in findings), findings
        assert (step_dir / "stdout.txt").is_file()

        bad_warning = ValidationRule(id="warn-miss", type="file.contains", severity="warning", path=str(target), contains="delta")
        bad_error = ValidationRule(id="err-miss", type="file.contains", severity="error", path=str(target), contains="delta")
        assert engine.evaluate(bad_warning, context, step_dir).status == "failed"
        assert engine.evaluate(bad_error, context, step_dir).status == "failed"

        prompts = repo / "prompts"
        prompts.mkdir()
        (prompts / "base.md").write_text("Base prompt", encoding="utf-8")
        (prompts / "repair.md").write_text("Repair instructions", encoding="utf-8")
        harness = repo / "retry.harness.yaml"
        harness.write_text(
            """apiVersion: devspark.ai/v1
kind: HarnessSpec
name: retry-test
steps:
  - id: retry-step
    type: agent_task
    prompt_file: prompts/base.md
    retry:
      maxAttempts: 2
      backoff: none
      retryOn:
        - validation_fail
      repairPrompt: prompts/repair.md
    validation:
      - id: missing-output
        type: file.exists
        severity: error
        path: missing.txt
""",
            encoding="utf-8",
        )
        runner = HarnessRunner(harness, adapter_override="noop", repo_root=repo)
        run = runner.execute()
        assert run.status == "failed"
        retry_prompt = (runner.run_dir / "steps" / "retry-step" / "prompt.md").read_text(encoding="utf-8")
        assert "Repair instructions" in retry_prompt
        assert "## Validation Errors" in retry_prompt

        original_isatty = sys.stdout.isatty
        import readchar
        original_readkey = readchar.readkey
        try:
            sys.stdout.isatty = lambda: True
            readchar.readkey = lambda: "y"
            gated = repo / "gated.harness.yaml"
            gated.write_text(
                """apiVersion: devspark.ai/v1
kind: HarnessSpec
name: gated-test
steps:
  - id: gated-step
    type: agent_task
    prompt_file: prompts/base.md
    retry:
      maxAttempts: 2
      backoff: none
      retryOn:
        - validation_fail
      requireHumanAfter: 1
      repairPrompt: prompts/repair.md
    validation:
      - id: missing-output
        type: file.exists
        severity: error
        path: missing.txt
""",
                encoding="utf-8",
            )
            gated_runner = HarnessRunner(gated, adapter_override="noop", repo_root=repo)
            gated_runner.execute()
            gated_prompt = (gated_runner.run_dir / "steps" / "gated-step" / "prompt.md").read_text(encoding="utf-8")
            assert "## Validation Errors" in gated_prompt
        finally:
            sys.stdout.isatty = original_isatty
            readchar.readkey = original_readkey

    print("Harness validation contract validated.")


if __name__ == "__main__":
    main()