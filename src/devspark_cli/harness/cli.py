"""Typer commands for the DevSpark harness runtime."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .config import load_adapter_default, save_adapter_default
from .runner import HarnessRunner, run_status_to_exit_code
from .spec_loader import HarnessSpecError, load_harness_spec


console = Console()
harness_app = typer.Typer(help="Run, validate, and inspect DevSpark harness workflows.", add_completion=False)
adapter_app = typer.Typer(help="List and configure harness execution adapters.", add_completion=False)


def _is_tty() -> bool:
    return console.is_terminal


def _print_run_summary(run, run_dir: Path) -> None:
    if _is_tty():
        console.print(f"DevSpark Harness: {run.harness_name}")
        console.print(f"Run ID: {run.run_id}")
        console.print(f"Adapter: {run.context.adapter} | Scope: {run.scope.type}")
        for step in run.steps:
            status_symbol = {"passed": "✓", "failed": "✗", "skipped_dry_run": "-", "aborted": "!"}.get(step.status, "?")
            console.print(f"  {status_symbol}  {step.step_id:<16} [{step.adapter}] {step.duration_ms / 1000:.1f}s")
        console.print(f"Artifacts: {run_dir}")
        return

    print(f"run_{run.status} {run.run_id} {run.harness_name}")
    for step in run.steps:
        detail = step.validation_findings[0].message if step.validation_findings and step.status == "failed" else ""
        print(f"step_{'pass' if step.status == 'passed' else 'fail' if step.status == 'failed' else step.status} {step.step_id} {step.adapter} {step.duration_ms / 1000:.1f}s {detail}".rstrip())


@harness_app.command("run")
def run_command(
    spec_file: Path = typer.Argument(..., exists=True, readable=True, help="Path to a harness YAML or JSON file."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate and resolve the spec but skip all step execution."),
    adapter: str | None = typer.Option(None, "--adapter", help="Override the adapter for all executable steps."),
    adapter_default: bool = typer.Option(False, "--adapter-default", help="Use the adapter stored in user config."),
) -> None:
    """Execute a harness spec.

    Exit codes: 0 complete, 1 failed, 2 aborted, 3 validation error.
    """

    try:
        runner = HarnessRunner(spec_file, adapter_override=adapter, use_adapter_default=adapter_default, dry_run=dry_run)
        run = runner.execute()
    except HarnessSpecError as exc:
        console.print(str(exc))
        raise typer.Exit(3)

    assert runner.run_dir is not None
    _print_run_summary(run, runner.run_dir)
    raise typer.Exit(run_status_to_exit_code(run.status))


@harness_app.command("validate")
def validate_command(spec_file: Path = typer.Argument(..., exists=True, readable=True, help="Path to a harness YAML or JSON file.")) -> None:
    """Validate a harness spec without executing it."""

    started = time.perf_counter()
    try:
        spec = load_harness_spec(spec_file)
    except HarnessSpecError as exc:
        if _is_tty():
            console.print(f"Validating: {spec_file}")
            console.print(str(exc))
            console.print("Spec invalid — 1 error")
        else:
            print(f"validate_err {exc}")
            print("spec_invalid 1 error")
        raise typer.Exit(1)

    duration = time.perf_counter() - started
    if _is_tty():
        console.print(f"Validating: {spec_file}")
        console.print(f"  ✓  apiVersion: {spec.apiVersion}")
        console.print(f"  ✓  kind: {spec.kind}")
        console.print(f"  ✓  {len(spec.steps)} steps — all IDs unique")
        console.print(f"Spec valid ({duration:.3f}s)")
    else:
        print("validate_ok apiVersion")
        print("validate_ok kind")
        print("validate_ok step_ids")
        print(f"spec_valid {duration:.3f}s")
    raise typer.Exit(0)


def _resolve_latest_run(run_root: Path) -> Path | None:
    candidates = [path for path in run_root.iterdir() if path.is_dir()] if run_root.is_dir() else []
    if not candidates:
        return None
    return max(candidates, key=lambda item: item.stat().st_mtime)


@harness_app.command("trace")
def trace_command(run_id: str = typer.Argument(..., help="Run id or 'latest'."), run_dir: Path = typer.Option(Path(".documentation/devspark/runs"), "--run-dir", help="Root run directory.")) -> None:
    """Render a harness event stream."""

    target_dir = _resolve_latest_run(run_dir) if run_id == "latest" else run_dir / run_id
    if target_dir is None or not target_dir.is_dir():
        console.print("No runs found" if run_id == "latest" else f"Run not found: {run_id}")
        raise typer.Exit(1)

    events_path = target_dir / "events.jsonl"
    if not events_path.is_file():
        console.print(f"Missing event log: {events_path}")
        raise typer.Exit(1)

    records = []
    for line in events_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        records.append(json.loads(line))

    result_path = target_dir / "result.json"
    summary = json.loads(result_path.read_text(encoding="utf-8")) if result_path.is_file() else {}

    if _is_tty():
        table = Table(title=f"Run: {target_dir.name}")
        table.add_column("Timestamp")
        table.add_column("Step ID")
        table.add_column("Attempt")
        table.add_column("Status")
        table.add_column("Duration ms")
        for record in records:
            status = record.get("status") or record["event"].split(".")[-1]
            table.add_row(
                record.get("ts", ""),
                record.get("step_id", "-"),
                str(record.get("attempt", "-")),
                str(status),
                str(record.get("duration_ms", "-")),
            )
        console.print(table)
        findings = [record for record in records if record.get("event") == "harness.step.validation"]
        if findings:
            console.print("Validation findings:")
            for finding in findings:
                console.print(
                    f"  {finding['step_id']}  {finding['rule_id']}  {finding['status']}  ({finding['rule_type']})"
                )
        if summary:
            console.print(f"Status: {summary.get('status', 'unknown')}")
    else:
        for record in records:
            status = record.get("status") or record["event"].split(".")[-1]
            print("\t".join([record.get("ts", ""), record.get("step_id", "-"), str(record.get("attempt", "-")), str(status), str(record.get("duration_ms", "-"))]))
    raise typer.Exit(0)


@adapter_app.command("list")
def list_adapters() -> None:
    """List built-in adapters and availability."""

    default_adapter = load_adapter_default() or "noop"
    known = [
        ("noop", True, "Always available (no AI required)"),
        ("manual", True, "Always available (copy/paste for IDE agents)"),
        ("claude_code", shutil.which("claude") is not None, "Requires claude CLI"),
        ("copilot", shutil.which("gh") is not None, "Requires gh CLI with Copilot extension"),
        ("cursor", shutil.which("cursor") is not None, "Requires Cursor IDE"),
    ]
    if _is_tty():
        console.print("Available adapters:")
        for name, available, reason in known:
            symbol = "✓" if available else "✗"
            console.print(f"  {symbol}  {name:<11} {reason}")
        console.print(f"Default adapter: {default_adapter}")
    else:
        for name, available, reason in known:
            state = "available" if available else "unavailable"
            print(f"adapter {name} {state} {reason}")
        print(f"default_adapter {default_adapter}")
    raise typer.Exit(0)


@adapter_app.command("default")
def set_default_adapter(name: str = typer.Argument(..., help="Adapter name.")) -> None:
    """Persist the default adapter used by harness runs."""

    if name not in {"noop", "manual", "claude_code", "copilot", "cursor"}:
        console.print(f"Unknown adapter: {name}")
        raise typer.Exit(1)
    path = save_adapter_default(name)
    console.print(f"Default adapter set to {name} ({path})")
    raise typer.Exit(0)