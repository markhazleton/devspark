"""Contract validation for hands-off lifecycle behavior.

Run with: python tests/test_hands_off_lifecycle_contract.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
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
    for dest_rel_path, source_rel_path in (
        (Path("sample.harness.yaml"), Path("sample.harness.yaml")),
        (Path(".devspark/schemas/harness.schema.json"), Path(".devspark/schemas/harness.schema.json")),
        # sample.harness.yaml hardcodes these as .documentation/specs/002-harness-runtime/ paths,
        # but the source spec was archived to releases/v2.5.0/ when that release shipped.
        (
            Path(".documentation/specs/002-harness-runtime/spec.md"),
            Path(".documentation/releases/v2.5.0/specs/002-harness-runtime/spec.md"),
        ),
        (
            Path(".documentation/specs/002-harness-runtime/contracts/cli-commands.md"),
            Path(".documentation/releases/v2.5.0/specs/002-harness-runtime/contracts/cli-commands.md"),
        ),
        (
            Path(".documentation/specs/002-harness-runtime/contracts/harness-spec-yaml.md"),
            Path(".documentation/releases/v2.5.0/specs/002-harness-runtime/contracts/harness-spec-yaml.md"),
        ),
        (Path(".documentation/memory/constitution.md"), Path(".documentation/memory/constitution.md")),
    ):
        target = repo / dest_rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / source_rel_path, target)

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "DevSpark Test"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "devspark@example.com"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=repo, check=True, capture_output=True, text=True)
    return repo


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo = _prepare_repo(Path(temp_dir))
        previous_cwd = Path.cwd()
        try:
            os.chdir(repo)
            result = RUNNER.invoke(
                app,
                ["harness", "run", "sample.harness.yaml", "--hands-off", "--adapter", "manual"],
                catch_exceptions=False,
                env={"TERM": "dumb"},
            )
            assert result.exit_code == 1, result.output

            runs_root = repo / ".documentation" / "devspark" / "runs"
            run_dir = _latest_run_dir(runs_root)
            payload = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
            assert payload["context"]["hands_off"] is True
            assert payload["failure_reason_code"] is not None

            events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
            assert "write_incompatible_adapter" in events

            decision = json.loads((run_dir / "decision-packet.json").read_text(encoding="utf-8"))
            assert decision["create_pr_ready"] is False
        finally:
            os.chdir(previous_cwd)

    print("Hands-off lifecycle contract validated.")


if __name__ == "__main__":
    main()
