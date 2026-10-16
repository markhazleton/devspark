"""Git fixture snapshots must not race with automatic background maintenance."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("key", ["maintenance.auto", "gc.auto"])
@pytest.mark.parametrize("nested", [False, True], ids=["git-child", "python-grandchild"])
def test_auto_maintenance_is_disabled_in_test_subprocesses(tmp_path: Path, key: str, nested: bool) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, capture_output=True, timeout=10)
    subprocess.run(
        ["git", "config", "--local", key, "1"], cwd=tmp_path, check=True, capture_output=True, timeout=10
    )
    command = ["git", "config", "--get", key]
    if nested:
        command = [
            sys.executable,
            "-c",
            "import subprocess, sys; sys.exit(subprocess.call(sys.argv[1:]))",
            *command,
        ]
    result = subprocess.run(command, cwd=tmp_path, check=True, capture_output=True, text=True, timeout=10)

    assert result.stdout.strip() == "0"
