from __future__ import annotations

import json
import subprocess
from pathlib import Path

from devspark_cli.harness.runner import HarnessRunner


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _write_harness(repo: Path) -> Path:
    harness = repo / "delivery.harness.yaml"
    prompts = repo / "prompts"
    prompts.mkdir(exist_ok=True)
    (prompts / "base.md").write_text("Implement changes", encoding="utf-8")
    harness.write_text(
        """apiVersion: devspark.ai/v1
kind: HarnessSpec
name: delivery-contract
steps:
  - id: implement
    type: agent_task
    prompt_file: prompts/base.md
    validation:
      - id: always
        type: always.pass
        severity: warning
""",
        encoding="utf-8",
    )
    return harness


def test_delivery_status_unmet_without_src_or_test_changes(tmp_path: Path) -> None:
    repo = tmp_path
    _git(repo, "init")
    _git(repo, "config", "user.email", "devspark@example.com")
    _git(repo, "config", "user.name", "DevSpark Test")

    harness = _write_harness(repo)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "init")

    runner = HarnessRunner(harness, adapter_override="noop", repo_root=repo)
    run = runner.execute()

    assert run.workflow_status == "complete"
    assert run.delivery_status == "unmet"
    assert run.create_pr_ready is False
    assert run.failure_reason_code == "delivery_status_unmet"

    assert runner.run_dir is not None
    explainer = runner.run_dir / "no-change-explainer.md"
    assert explainer.is_file()


def test_delivery_status_met_with_src_changes(tmp_path: Path) -> None:
    repo = tmp_path
    _git(repo, "init")
    _git(repo, "config", "user.email", "devspark@example.com")
    _git(repo, "config", "user.name", "DevSpark Test")

    harness = _write_harness(repo)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "init")

    src = repo / "src"
    src.mkdir(exist_ok=True)
    (src / "module.py").write_text("value = 1\n", encoding="utf-8")

    runner = HarnessRunner(harness, adapter_override="noop", repo_root=repo)
    run = runner.execute()

    assert run.workflow_status == "complete"
    assert run.delivery_status == "met"
    assert run.create_pr_ready is True

    assert runner.run_dir is not None
    result = json.loads((runner.run_dir / "result.json").read_text(encoding="utf-8"))
    assert result["delivery_status"] == "met"
    assert result["create_pr_ready"] is True
