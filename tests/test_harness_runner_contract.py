"""Contract validation for the harness runtime CLI.

Run with: python tests/test_harness_runner_contract.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from typer.testing import CliRunner


ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from devspark_cli import app


RUNNER = CliRunner()


def _latest_run_dir(runs_root: Path) -> Path:
    candidates = [path for path in runs_root.iterdir() if path.is_dir()]
    assert candidates, "expected at least one run directory"
    return max(candidates, key=lambda item: item.stat().st_mtime)


def _prepare_repo(temp_root: Path) -> Path:
    repo = temp_root / "repo"
    repo.mkdir()
    for rel_path in (
        Path("sample.harness.yaml"),
        Path(".devspark/schemas/harness.schema.json"),
        Path(".documentation/specs/002-harness-runtime/spec.md"),
        Path(".documentation/specs/002-harness-runtime/contracts/cli-commands.md"),
        Path(".documentation/specs/002-harness-runtime/contracts/harness-spec-yaml.md"),
        Path(".documentation/memory/constitution.md"),
        Path(".gitignore"),
    ):
        target = repo / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel_path, target)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "DevSpark Test"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "devspark@example.com"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "Initial harness fixture"], cwd=repo, check=True, capture_output=True, text=True)
    return repo


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo = _prepare_repo(Path(temp_dir))
        before_gitignore = (repo / ".gitignore").read_text(encoding="utf-8")
        previous_cwd = Path.cwd()

        try:
            os.chdir(repo)

            start = time.perf_counter()
            result = RUNNER.invoke(app, ["harness", "run", "sample.harness.yaml", "--adapter", "noop"], catch_exceptions=False)
            duration = time.perf_counter() - start
            assert result.exit_code == 0, result.output
            assert duration < 5, duration

            runs_root = repo / ".documentation" / "devspark" / "runs"
            run_dir = _latest_run_dir(runs_root)
            result_json = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
            assert result_json["status"] == "complete"
            assert (run_dir / "events.jsonl").is_file()
            assert (run_dir / "context.json").is_file()
            assert (run_dir / "spec.resolved.yaml").is_file()
            assert (run_dir / "steps" / "specify" / "prompt.md").is_file()
            assert (run_dir / "steps" / "human-review" / "prompt.md").is_file()

            dry_run = RUNNER.invoke(app, ["harness", "run", "sample.harness.yaml", "--dry-run"], catch_exceptions=False)
            assert dry_run.exit_code == 0, dry_run.output
            dry_run_dir = _latest_run_dir(runs_root)
            dry_result = json.loads((dry_run_dir / "result.json").read_text(encoding="utf-8"))
            assert all(step["status"] == "skipped_dry_run" for step in dry_result["steps"])

            no_tty = RUNNER.invoke(app, ["harness", "run", "sample.harness.yaml"], catch_exceptions=False, env={"TERM": "dumb"})
            assert no_tty.exit_code == 1, no_tty.output
            blocked_run_dir = _latest_run_dir(runs_root)
            blocked_result = json.loads((blocked_run_dir / "result.json").read_text(encoding="utf-8"))
            assert blocked_result["status"] == "failed"
            blocked_events = (blocked_run_dir / "events.jsonl").read_text(encoding="utf-8")
            assert "harness.policy.blocked" in blocked_events
            assert "manual_gate_requires_tty" in blocked_events

            trace = RUNNER.invoke(app, ["harness", "trace", "latest", "--run-dir", str(runs_root)], catch_exceptions=False)
            assert trace.exit_code == 0, trace.output

            help_result = RUNNER.invoke(app, ["harness", "run", "--help"], catch_exceptions=False)
            assert help_result.exit_code == 0
            assert "Exit codes: 0 complete, 1 failed, 2 aborted, 3 validation error." in help_result.output

            init_help = RUNNER.invoke(app, ["init", "--help"], catch_exceptions=False)
            version_help = RUNNER.invoke(app, ["version"], catch_exceptions=False)
            upgrade_help = RUNNER.invoke(app, ["upgrade", "--help"], catch_exceptions=False)
            assert init_help.exit_code == 0
            assert version_help.exit_code == 0
            assert upgrade_help.exit_code == 0

            after_gitignore = (repo / ".gitignore").read_text(encoding="utf-8")
            assert before_gitignore == after_gitignore
        finally:
            os.chdir(previous_cwd)

    print("Harness runner contract validated.")


if __name__ == "__main__":
    main()