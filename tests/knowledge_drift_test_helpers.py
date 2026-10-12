# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Shared, offline, bounded helpers for the knowledge-drift-detection test suite.

Every helper here is deliberately small and deterministic: no network access, no
implicit timeouts, and no reliance on the real repository's Git history. Tests
that need a Git-backed scope build one with `init_git_repo`/`commit_all` instead
of inspecting this repository's own history.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

DEFAULT_TIMEOUT_SECONDS = 30


def run_bounded(
    args: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess with an explicit timeout (Constitution IX: no unbounded runs)."""
    return subprocess.run(
        args,
        text=True,
        capture_output=True,
        cwd=cwd,
        env=env,
        timeout=timeout,
    )


def parse_json_report(path: Path) -> dict[str, Any]:
    """Load and parse a machine-readable drift/report JSON file, failing loudly on absence."""
    if not path.exists():
        raise AssertionError(f"expected report file at {path}, none was written")
    return json.loads(path.read_text(encoding="utf-8"))


def init_git_repo(root: Path, *, user_name: str = "Test User", user_email: str = "test@example.com") -> None:
    """Initialize a minimal, deterministic local Git repository at `root`."""
    run_bounded(["git", "init", "--quiet"], cwd=root)
    run_bounded(["git", "config", "user.name", user_name], cwd=root)
    run_bounded(["git", "config", "user.email", user_email], cwd=root)
    # Keep test repos independent of any real global Git config that could
    # change default branch naming or signing behavior.
    run_bounded(["git", "config", "commit.gpgsign", "false"], cwd=root)
    run_bounded(["git", "config", "init.defaultBranch", "main"], cwd=root)


def commit_all(root: Path, message: str) -> str:
    """Stage and commit every change in `root`, returning the new commit SHA."""
    run_bounded(["git", "add", "-A"], cwd=root)
    run_bounded(["git", "commit", "--quiet", "--message", message], cwd=root)
    result = run_bounded(["git", "rev-parse", "HEAD"], cwd=root)
    return result.stdout.strip()


def write_file(path: Path, content: str) -> None:
    """Write `content` to `path`, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
