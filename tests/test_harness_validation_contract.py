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

        # Phase 1: ArtifactDelta tracking — noop adapter produces correct delta
        output_file = repo / "tracked_output.txt"
        delta_harness = repo / "delta.harness.yaml"
        delta_harness.write_text(
            f"""apiVersion: devspark.ai/v1
kind: HarnessSpec
name: delta-test
steps:
  - id: delta-step
    type: agent_task
    prompt_file: prompts/base.md
    outputs:
      - {output_file}
""",
            encoding="utf-8",
        )
        # File does not exist before — noop won't create it — delta should be empty
        delta_runner = HarnessRunner(delta_harness, adapter_override="noop", repo_root=repo)
        delta_run = delta_runner.execute()
        step_result = delta_run.steps[0]
        assert step_result.artifacts.created == []
        assert step_result.artifacts.modified == []
        assert step_result.artifacts.deleted == []
        # harness.step.artifacts event should appear in events.jsonl
        events_text = (delta_runner.run_dir / "events.jsonl").read_text(encoding="utf-8")
        assert "harness.step.artifacts" in events_text

        # Pre-create the file, then run — still empty delta since noop doesn't modify it
        output_file.write_text("original", encoding="utf-8")
        delta_run2 = HarnessRunner(delta_harness, adapter_override="noop", repo_root=repo).execute()
        assert delta_run2.steps[0].artifacts.created == []
        assert delta_run2.steps[0].artifacts.modified == []

        # Phase 2: Plan mode — execution_mode stored in context.json, command.exit_code skipped
        plan_harness = repo / "plan.harness.yaml"
        plan_harness.write_text(
            """apiVersion: devspark.ai/v1
kind: HarnessSpec
name: plan-test
steps:
  - id: plan-step
    type: validation
    validation:
      - id: cmd-check
        type: command.exit_code
        severity: error
        command: git --version
      - id: always-ok
        type: always.pass
        severity: warning
""",
            encoding="utf-8",
        )
        plan_runner = HarnessRunner(plan_harness, adapter_override="noop", repo_root=repo, execution_mode="plan")
        plan_run = plan_runner.execute()
        context_json = json.loads((plan_runner.run_dir / "context.json").read_text(encoding="utf-8"))
        assert context_json["execution_mode"] == "plan"
        cmd_findings = [f for f in plan_run.steps[0].validation_findings if f.rule_id == "cmd-check"]
        assert cmd_findings[0].status == "skipped"

        # Phase 3: Disabled rule (enabled=false) is skipped
        disabled_harness = repo / "disabled.harness.yaml"
        disabled_harness.write_text(
            """apiVersion: devspark.ai/v1
kind: HarnessSpec
name: disabled-test
steps:
  - id: disabled-step
    type: validation
    validation:
      - id: this-fails
        type: file.exists
        severity: error
        path: absolutely_missing_file_xyz.txt
        enabled: false
      - id: this-passes
        type: always.pass
        severity: warning
""",
            encoding="utf-8",
        )
        disabled_run = HarnessRunner(disabled_harness, adapter_override="noop", repo_root=repo).execute()
        assert disabled_run.status == "complete"
        disabled_findings = {f.rule_id: f for f in disabled_run.steps[0].validation_findings}
        assert disabled_findings["this-fails"].status == "skipped"
        assert disabled_findings["this-passes"].status == "passed"

        # Phase 3: llm.rubric skipped when deterministic error-severity rule fails
        rubric_harness = repo / "rubric.harness.yaml"
        rubric_harness.write_text(
            """apiVersion: devspark.ai/v1
kind: HarnessSpec
name: rubric-skip-test
steps:
  - id: rubric-step
    type: validation
    validation:
      - id: det-fail
        type: file.exists
        severity: error
        path: absolutely_missing_rubric_input.txt
      - id: rubric-check
        type: llm.rubric
        severity: warning
        rubric: Does the output contain a summary?
        grader_command: echo 4
""",
            encoding="utf-8",
        )
        rubric_run = HarnessRunner(rubric_harness, adapter_override="noop", repo_root=repo).execute()
        rubric_findings = {f.rule_id: f for f in rubric_run.steps[0].validation_findings}
        assert rubric_findings["det-fail"].status == "failed"
        assert rubric_findings["rubric-check"].status == "skipped"

        # Phase 3: llm.rubric passes when grader outputs a score >= threshold
        output_for_rubric = repo / "rubric_output.txt"
        output_for_rubric.write_text("Great implementation with a summary.", encoding="utf-8")
        rubric_pass_harness = repo / "rubric_pass.harness.yaml"
        rubric_pass_harness.write_text(
            f"""apiVersion: devspark.ai/v1
kind: HarnessSpec
name: rubric-pass-test
steps:
  - id: rubric-pass-step
    type: agent_task
    prompt_file: prompts/base.md
""",
            encoding="utf-8",
        )
        # Create a mock grader that outputs "4" (above default threshold of 3)
        mock_grader = repo / "mock_grader.py"
        mock_grader.write_text("import sys; print('4'); sys.exit(0)\n", encoding="utf-8")

        rubric_inline_harness = repo / "rubric_inline.harness.yaml"
        rubric_inline_harness.write_text(
            f"""apiVersion: devspark.ai/v1
kind: HarnessSpec
name: rubric-inline-test
steps:
  - id: rubric-inline-step
    type: validation
    validation:
      - id: rubric-inline
        type: llm.rubric
        severity: warning
        rubric: Does the output contain a summary?
        grader_command: python {mock_grader} --
        pass_threshold: 3
""",
            encoding="utf-8",
        )
        # Write a fake output.txt so the engine can find it
        rubric_step_dir = repo / "steps" / "rubric-inline-step"
        rubric_step_dir.mkdir(parents=True, exist_ok=True)
        (rubric_step_dir / "output.txt").write_text("Summary: This implementation works.", encoding="utf-8")

        rubric_engine = ValidationEngine()
        rubric_rule_pass = ValidationRule(
            id="rubric-test", type="llm.rubric", severity="warning",
            rubric="Does the output contain a summary?",
            grader_command=f"python {mock_grader} --",
            pass_threshold=3,
        )
        rubric_ctx = RunContext(
            run_id="r_test", repo_root=str(repo), spec_path=str(repo / "h.yaml"),
            doc_root=str(repo / ".documentation"), adapter="noop", dry_run=False,
        )
        rubric_finding = rubric_engine.evaluate(rubric_rule_pass, rubric_ctx, rubric_step_dir)
        assert rubric_finding.status == "passed", rubric_finding.message
        assert (rubric_step_dir / "rubric_result.txt").is_file()

        # Score below threshold should fail
        mock_grader_low = repo / "mock_grader_low.py"
        mock_grader_low.write_text("import sys; print('1'); sys.exit(0)\n", encoding="utf-8")
        rubric_rule_fail = ValidationRule(
            id="rubric-fail", type="llm.rubric", severity="warning",
            rubric="Does the output contain a summary?",
            grader_command=f"python {mock_grader_low} --",
            pass_threshold=3,
        )
        rubric_finding_fail = rubric_engine.evaluate(rubric_rule_fail, rubric_ctx, rubric_step_dir)
        assert rubric_finding_fail.status == "failed"

        # Phase 5: context_budget truncates prompt
        from devspark_cli.harness.adapters.base import apply_context_budget

        class _FakeTelemetry:
            def __init__(self):
                self.events = []
            def emit(self, event, run_id, **kw):
                self.events.append(event)

        class _FakeContext:
            run_id = "r_budget"

        budget_step = StepSpec.model_validate(
            {"id": "budget-step", "type": "agent_task", "prompt_file": str(repo / "prompts" / "base.md"), "context_budget": 10}
        )
        long_text = "A" * 200
        fake_tel = _FakeTelemetry()
        truncated = apply_context_budget(long_text, budget_step, _FakeContext(), fake_tel)
        assert len(truncated) == 10
        assert "harness.policy.blocked" in fake_tel.events

        # No truncation when under budget
        short_text = "Hi"
        fake_tel2 = _FakeTelemetry()
        not_truncated = apply_context_budget(short_text, budget_step, _FakeContext(), fake_tel2)
        assert not_truncated == "Hi"
        assert "harness.policy.blocked" not in fake_tel2.events

    print("Harness validation contract validated.")


if __name__ == "__main__":
    main()