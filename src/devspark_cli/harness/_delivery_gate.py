"""Delivery-gate pass/fail logic for the DevSpark harness runtime."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .spec_models import (
    DeliveryCheckResult,
    REASON_CODE_CREATE_PR_BLOCKED,
    REASON_CODE_DELIVERY_UNMET,
    Run,
)


def collect_delivery_checks(repo_root: Path) -> list[DeliveryCheckResult]:
    """Run git-based delivery checks and return structured results."""
    changed: set[str] = set()
    try:
        commands = [
            ["git", "diff", "origin/main...HEAD", "--name-only", "--", "src/", "test/"],
            ["git", "diff", "--cached", "--name-only", "--", "src/", "test/"],
            ["git", "diff", "--name-only", "--", "src/", "test/"],
        ]
        for command in commands:
            completed = subprocess.run(
                command,
                cwd=repo_root,
                text=True,
                errors="replace",
                capture_output=True,
                check=False,
                timeout=30,
            )
            if completed.returncode == 0:
                for line in (completed.stdout or "").splitlines():
                    value = line.strip()
                    if value:
                        changed.add(value.replace("\\", "/"))

        status_completed = subprocess.run(
            ["git", "status", "--porcelain", "--", "src/", "test/"],
            cwd=repo_root,
            text=True,
            errors="replace",
            capture_output=True,
            check=False,
            timeout=30,
        )
        if status_completed.returncode == 0:
            for line in (status_completed.stdout or "").splitlines():
                candidate = line[3:].strip() if len(line) > 3 else ""
                if candidate:
                    changed.add(candidate.replace("\\", "/"))
    except Exception:
        changed = set()

    checks: list[DeliveryCheckResult] = []
    checks.append(
        DeliveryCheckResult(
            check_id="default-src-test-changed-count",
            check_type="git.changed_count",
            required=True,
            status="pass" if len(changed) >= 1 else "fail",
            details={"base_ref": "origin/main", "count": len(changed)},
        )
    )
    checks.append(
        DeliveryCheckResult(
            check_id="default-src-test-path-match",
            check_type="git.changed_path_match",
            required=True,
            status="pass" if any(path.startswith("src/") or path.startswith("test/") for path in changed) else "fail",
            details={"base_ref": "origin/main", "matched_paths": sorted(changed)[:20]},
        )
    )
    return checks


def write_no_change_explainer(run_dir: Path | None, checks: list[DeliveryCheckResult]) -> None:
    """Write a markdown explainer when delivery evidence requirements are not met."""
    if run_dir is None:
        return
    failed = [check for check in checks if check.required and check.status == "fail"]
    if not failed:
        return
    lines = [
        "# Delivery Status Unmet",
        "",
        "Workflow execution completed but delivery evidence requirements were not met.",
        "",
        "## Failed Checks",
    ]
    for check in failed:
        lines.append(f"- {check.check_id}: {check.details}")
    lines.append("")
    lines.append("## Next Actions")
    lines.append("- Ensure at least one file changes under src/ or test/.")
    lines.append("- Re-run harness after implementation changes are present.")
    (run_dir / "no-change-explainer.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def evaluate_delivery_gate(run: Run, run_dir: Path | None, repo_root: Path) -> None:
    """Collect delivery checks and set delivery-related run fields in-place."""
    run.delivery_checks = collect_delivery_checks(repo_root)
    required_failed = [c for c in run.delivery_checks if c.required and c.status == "fail"]
    run.delivery_status = "met" if not required_failed else "unmet"
    run.create_pr_ready = run.workflow_status == "complete" and run.delivery_status == "met"
    if run.delivery_status == "unmet":
        run.failure_reason_code = REASON_CODE_DELIVERY_UNMET
        write_no_change_explainer(run_dir, run.delivery_checks)
    elif not run.create_pr_ready:
        run.failure_reason_code = REASON_CODE_CREATE_PR_BLOCKED
