"""Pre-run gate checks for the workflow runner (git state, governance approval)."""

from __future__ import annotations

import glob
import json
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .runner.loader import Workflow


def git_dirty(repo_root: Path) -> bool:
    """Return True when `git status --porcelain` reports any change."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return False
    return bool(result.stdout.strip())


def branch_synced_with_main(repo_root: Path) -> bool:
    """Return True when the current branch is not behind origin/main."""
    try:
        result = subprocess.run(
            ["git", "rev-list", "--left-right", "--count", "origin/main...HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return True
    if result.returncode != 0:
        return True
    parts = (result.stdout or "").strip().split()
    if len(parts) != 2:
        return True
    try:
        behind = int(parts[0])
    except ValueError:
        return True
    return behind == 0


def latest_harness_result(repo_root: Path) -> dict[str, Any] | None:
    """Return the result.json from the most recently modified harness run, or None."""
    runs_root = repo_root / ".documentation" / "devspark" / "runs"
    if not runs_root.is_dir():
        return None
    candidates = [
        path for path in runs_root.iterdir()
        if path.is_dir() and (path / "result.json").is_file()
    ]
    if not candidates:
        return None
    latest = max(candidates, key=lambda item: item.stat().st_mtime)
    try:
        return json.loads((latest / "result.json").read_text(encoding="utf-8"))
    except Exception:
        return None


def is_delivery_gate_target(workflow_id: str) -> bool:
    lowered = workflow_id.lower()
    return "create-pr" in lowered or "pr-review" in lowered


def get_governance_approval_status(repo_root: Path) -> dict[str, Any] | None:
    """Return approval record if a governance-approval gate file is found, else None."""
    patterns = [
        str(repo_root / ".documentation" / "specs" / "*/gates" / "governance-approval.md"),
        str(repo_root / ".documentation" / "specs" / "*/governance-approval.md"),
    ]
    for pattern in patterns:
        for match in glob.glob(pattern):
            try:
                content = Path(match).read_text(encoding="utf-8")
                if "Approver Name:" in content and "Decision:" in content:
                    for line in content.split("\n"):
                        if "Decision:" in line:
                            decision = line.split("Decision:")[-1].strip()
                            if "approved" in decision.lower():
                                return {"approved": True, "path": match, "decision": decision}
            except (OSError, UnicodeDecodeError):
                continue
    return None


def requires_governance_approval(wf: "Workflow") -> bool:
    """Return True only when the workflow YAML explicitly sets governance_required: true."""
    return bool(wf.governance_required)
