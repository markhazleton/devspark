"""DevSpark CLI subcommands for the tiered workflow engine.

Adds: `devspark run`, `devspark resume`, `devspark workflows`,
`devspark runs`, and an enriched `devspark help` view.

Registered onto the main Typer app via `register(app)` from `__init__.py`.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import typer

from .resolution import (
    build_alias_chain,
    build_atomic_prompt_chain,
    build_workflow_chain,
    resolve_alias,
    resolve_atomic_prompt,
    resolve_workflow,
)
from .runner.executor import (
    EXIT_AUTONOMY_REQUIRED,
    EXIT_RESUME_FAILED,
    WorkflowRunner,
    load_pause_state,
    runs_dir,
)
from .runner.loader import (
    Alias,
    AtomicPrompt,
    ValidationError,
    Workflow,
    parse_alias,
    parse_atomic_prompt,
    parse_workflow,
    validate_alias,
    validate_atomic_prompt,
    validate_workflow,
)


# ---------------------------------------------------------------------------
# Resolver helpers
# ---------------------------------------------------------------------------

def _repo_root() -> Path:
    return Path.cwd()


def _scan_atomic_prompts(repo_root: Path) -> dict[str, AtomicPrompt]:
    """Collect every reachable atomic prompt across the resolution chain.

    Last-writer-wins by id (later entries overwrite earlier; we walk lowest
    priority first so highest priority wins).
    """
    prompts: dict[str, AtomicPrompt] = {}
    for d in reversed(build_atomic_prompt_chain(repo_root)):
        if not d.is_dir():
            continue
        for path in sorted(d.glob("*.md")):
            try:
                prompts[path.stem] = parse_atomic_prompt(path)
            except ValidationError:
                continue
    return prompts


def _scan_workflows(repo_root: Path) -> dict[str, Workflow]:
    workflows: dict[str, Workflow] = {}
    for d in reversed(build_workflow_chain(repo_root)):
        if not d.is_dir():
            continue
        for path in sorted(d.glob("*.yaml")):
            try:
                workflows[path.stem] = parse_workflow(path)
            except ValidationError:
                continue
    return workflows


def _scan_aliases(repo_root: Path) -> dict[str, Alias]:
    aliases: dict[str, Alias] = {}
    for d in reversed(build_alias_chain(repo_root)):
        if not d.is_dir():
            continue
        for path in sorted(d.glob("*.yaml")):
            try:
                aliases[path.stem] = parse_alias(path)
            except ValidationError:
                continue
    return aliases


# ---------------------------------------------------------------------------
# Repeated-sequence detection ring buffer (FR-022 / T049)
# ---------------------------------------------------------------------------

_INVOCATION_RING: list[tuple[str, float]] = []
_RING_WINDOW_SECONDS = 30 * 60
_RING_MIN_LEN = 3


def _record_atomic_invocation(prompt_id: str, repo_root: Path) -> None:
    import time

    now = time.time()
    _INVOCATION_RING.append((prompt_id, now))
    # Trim window
    while _INVOCATION_RING and now - _INVOCATION_RING[0][1] > _RING_WINDOW_SECONDS:
        _INVOCATION_RING.pop(0)
    if len(_INVOCATION_RING) < _RING_MIN_LEN:
        return
    recent_ids = [p for p, _ in _INVOCATION_RING[-_RING_MIN_LEN:]]
    workflows = _scan_workflows(repo_root)
    for wf in workflows.values():
        wf_step_prompts = [s.prompt for s in wf.steps[:_RING_MIN_LEN]]
        if recent_ids == wf_step_prompts:
            print(
                f"Tip: try `devspark run {wf.id}` to orchestrate these steps with pause/resume support.",
                file=sys.stderr,
            )
            return


# ---------------------------------------------------------------------------
# Live invoker (T025): forward to the canonical command file via legacy_command
# ---------------------------------------------------------------------------

def _live_prompt_invoker(repo_root: Path):
    def _invoke(prompt_id: str, step, context: dict[str, Any]) -> dict[str, Any]:
        path = resolve_atomic_prompt(prompt_id, repo_root)
        if path is None:
            raise RuntimeError(f"atomic prompt {prompt_id!r} did not resolve")
        prompt = parse_atomic_prompt(path)
        validate_atomic_prompt(prompt)

        # In CLI execution we surface a structured request — the workflow
        # runner's job is orchestration, not LLM invocation. The actual prompt
        # body is delegated to the agent driving the conversation.
        target = (
            f"templates/commands/{prompt.legacy_command}.md"
            if prompt.legacy_command
            else f"templates/prompts/atomic/{prompt_id}.md"
        )
        print(
            f"[devspark] step {step.id!r} — invoke {prompt_id!r} via {target}",
            file=sys.stdout,
        )
        _record_atomic_invocation(prompt_id, repo_root)
        return {}

    return _invoke


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register(app: typer.Typer) -> None:
    """Register the run/resume/workflows/runs subcommands onto the main Typer app."""

    workflows_app = typer.Typer(help="Inspect and validate workflow definitions.")
    runs_app = typer.Typer(help="Inspect persisted workflow run state.")

    # ---------------------------------------------------------------- run
    @app.command("run")
    def run_cmd(
        target: str = typer.Argument(..., help="Alias or workflow id."),
        autonomy: str = typer.Option(
            "", "--autonomy", help="Override workflow autonomy level: assisted | autonomous."
        ),
        non_interactive: bool = typer.Option(
            False, "--non-interactive", help="Fail rather than prompt for missing inputs."
        ),
        allow_dirty: bool = typer.Option(
            False, "--allow-dirty", help="Allow start with a dirty git working tree (FR-015a)."
        ),
        hands_off: bool = typer.Option(False, "--hands-off", help="Run full lifecycle non-interactively."),
        yes: bool = typer.Option(False, "--yes", help="Skip interactive confirmations."),
    ) -> None:
        """Run a workflow by alias or workflow id."""
        repo_root = _repo_root()

        # Resolve alias -> workflow with one-step fallback (no chains)
        alias_path = resolve_alias(target, repo_root)
        workflow_id = target
        if alias_path is not None:
            try:
                a = parse_alias(alias_path)
                workflow_id = a.target_workflow
            except ValidationError as exc:
                typer.echo(f"alias invalid: {exc}", err=True)
                raise typer.Exit(code=23)

        wf_path = resolve_workflow(workflow_id, repo_root)
        if wf_path is None:
            typer.echo(f"workflow {workflow_id!r} did not resolve", err=True)
            raise typer.Exit(code=22)

        try:
            wf = parse_workflow(wf_path)
            validate_workflow(wf, resolve_prompt=lambda pid: resolve_atomic_prompt(pid, repo_root))
        except ValidationError as exc:
            typer.echo(f"workflow invalid: {exc}", err=True)
            raise typer.Exit(code=22)

        # Autonomy resolution: flag > env > workflow default
        effective_autonomy = (
            autonomy.strip()
            or os.environ.get("DEVSPARK_AUTONOMY", "").strip()
            or wf.autonomy_level
        )
        if non_interactive and not effective_autonomy:
            typer.echo(
                "autonomy required in non-interactive mode; provide one of:\n"
                "  --autonomy <assisted|autonomous>\n"
                "  DEVSPARK_AUTONOMY env var\n"
                "  .devspark/autonomy.yaml file",
                err=True,
            )
            raise typer.Exit(code=EXIT_AUTONOMY_REQUIRED)

        # Working tree guard (FR-015a)
        if not allow_dirty and _git_dirty(repo_root):
            typer.echo(
                "git working tree is dirty. Commit/stash changes or pass --allow-dirty.",
                err=True,
            )
            raise typer.Exit(code=EXIT_AUTONOMY_REQUIRED)

        if _is_delivery_gate_target(workflow_id):
            latest_result = _latest_harness_result(repo_root)
            if latest_result is not None:
                delivery_status = latest_result.get("delivery_status")
                create_pr_ready = latest_result.get("create_pr_ready")
                if delivery_status == "unmet" or create_pr_ready is False:
                    typer.echo(
                        "delivery-status gate blocked this workflow; latest harness run is not create-pr ready.",
                        err=True,
                    )
                    raise typer.Exit(code=EXIT_AUTONOMY_REQUIRED)
            if not _is_branch_synced_with_main(repo_root):
                typer.echo(
                    "branch-sync gate blocked this workflow; branch is behind origin/main.",
                    err=True,
                )
                raise typer.Exit(code=EXIT_AUTONOMY_REQUIRED)

        # Governance approval guard for cross-cutting features
        if _requires_governance_approval(workflow_id):
            approval = _get_governance_approval_status(repo_root)
            if approval is None:
                typer.echo(
                    "Governance approval required but not found. "
                    "Leadership checkpoint must be completed before this workflow can run.\n"
                    "See .documentation/specs/*/gates/governance-approval.md for approval template.",
                    err=True,
                )
                raise typer.Exit(code=EXIT_AUTONOMY_REQUIRED)

        invoker = _live_prompt_invoker(repo_root)
        telemetry = _make_telemetry(repo_root)
        enforcer = _make_enforcer(repo_root, wf, effective_autonomy)
        runner = WorkflowRunner(
            wf,
            mode="live",
            invoker=invoker,
            repo_root=repo_root,
            telemetry=telemetry,
            autonomy_enforcer=enforcer,
        )
        if hands_off:
            result = runner.run_full_lifecycle({}, autonomy_level=effective_autonomy)
        else:
            result = runner.run({}, autonomy_level=effective_autonomy)

        typer.echo(
            f"[devspark] workflow {wf.id!r} output_type={wf.output_type} "
            f"steps_run={len(result.results)} paused={result.paused}"
        )
        raise typer.Exit(code=result.exit_code)

    # ---------------------------------------------------------------- resume
    @app.command("resume")
    def resume_cmd(workflow_run_id: str = typer.Argument(...)) -> None:
        """Resume a paused workflow run by its workflow_run_id."""
        repo_root = _repo_root()
        try:
            state = load_pause_state(repo_root, workflow_run_id)
        except ValueError as exc:
            typer.echo(f"resume failed: {exc}", err=True)
            raise typer.Exit(code=EXIT_RESUME_FAILED)

        wf_path = resolve_workflow(state["workflow_id"], repo_root)
        if wf_path is None:
            typer.echo(
                f"resume failed: workflow {state['workflow_id']!r} no longer resolves",
                err=True,
            )
            raise typer.Exit(code=EXIT_RESUME_FAILED)

        try:
            wf = parse_workflow(wf_path)
            validate_workflow(wf, resolve_prompt=lambda pid: resolve_atomic_prompt(pid, repo_root))
        except ValidationError as exc:
            typer.echo(f"resume failed: {exc}", err=True)
            raise typer.Exit(code=EXIT_RESUME_FAILED)

        if wf.id != state["workflow_id"]:
            typer.echo(
                f"resume failed: persisted workflow_id {state['workflow_id']!r} "
                f"does not match resolved id {wf.id!r}",
                err=True,
            )
            raise typer.Exit(code=EXIT_RESUME_FAILED)

        invoker = _live_prompt_invoker(repo_root)
        telemetry = _make_telemetry(repo_root)
        enforcer = _make_enforcer(repo_root, wf, state.get("autonomy_level") or wf.autonomy_level)
        runner = WorkflowRunner(
            wf,
            mode="live",
            invoker=invoker,
            repo_root=repo_root,
            telemetry=telemetry,
            autonomy_enforcer=enforcer,
        )
        result = runner.run(
            state.get("context") or {},
            autonomy_level=state.get("autonomy_level") or wf.autonomy_level,
            workflow_run_id=workflow_run_id,
            start_at_step_id=state.get("next_step_id"),
        )
        typer.echo(
            f"[devspark] resumed workflow {wf.id!r} steps_run={len(result.results)} "
            f"paused={result.paused}"
        )
        raise typer.Exit(code=result.exit_code)

    # ---------------------------------------------------------------- workflows
    @workflows_app.command("list")
    def workflows_list_cmd() -> None:
        repo_root = _repo_root()
        wfs = _scan_workflows(repo_root)
        if not wfs:
            typer.echo("(no workflows found)")
            return
        for wid, wf in sorted(wfs.items()):
            typer.echo(
                f"{wid}\toutput_type={wf.output_type}\tautonomy={wf.autonomy_level}\t"
                f"{wf.description.strip()[:80]}"
            )

    @workflows_app.command("validate")
    def workflows_validate_cmd() -> None:
        repo_root = _repo_root()
        ok = True

        for wid, wf in _scan_workflows(repo_root).items():
            try:
                validate_workflow(wf, resolve_prompt=lambda pid: resolve_atomic_prompt(pid, repo_root))
                typer.echo(f"workflow {wid}: ok")
            except ValidationError as exc:
                typer.echo(f"workflow {wid}: {exc}", err=True)
                ok = False

        atomic_ids = set(_scan_atomic_prompts(repo_root).keys())
        for aid, alias in _scan_aliases(repo_root).items():
            try:
                validate_alias(
                    alias,
                    resolve_workflow=lambda wid: resolve_workflow(wid, repo_root),
                    resolve_alias_target=lambda wid: resolve_alias(wid, repo_root),
                    atomic_prompt_ids=atomic_ids,
                )
                typer.echo(f"alias {aid}: ok")
            except ValidationError as exc:
                typer.echo(f"alias {aid}: {exc}", err=True)
                ok = False

        raise typer.Exit(code=0 if ok else 22)

    app.add_typer(workflows_app, name="workflows")

    # ---------------------------------------------------------------- runs
    @runs_app.command("list")
    def runs_list_cmd() -> None:
        repo_root = _repo_root()
        target = runs_dir(repo_root)
        if not target.is_dir():
            typer.echo("(no persisted runs)")
            return
        rows = []
        for path in sorted(target.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            rows.append(
                f"{data.get('workflow_run_id', path.stem)}\t"
                f"{data.get('workflow_id', '?')}\t"
                f"next={data.get('next_step_id', '?')}\t"
                f"paused_at={data.get('paused_at', '?')}"
            )
        if not rows:
            typer.echo("(no persisted runs)")
            return
        for row in rows:
            typer.echo(row)

    app.add_typer(runs_app, name="runs")

    # ---------------------------------------------------------------- help (atomic-prompt aware)
    @app.command("help")
    def help_cmd(
        all_: bool = typer.Option(False, "--all", help="Include hidden (exposed: false) atomic prompts"),
        category: str | None = typer.Option(None, "--category", help="Filter atomic prompts by category"),
        audience: str | None = typer.Option(None, "--audience", help="Filter atomic prompts by audience"),
    ) -> None:
        """List aliases, workflows, and atomic prompts (FR-021)."""
        _print_help_view(_repo_root(), include_all=all_, category=category, audience=audience)

    @app.command("workflows-help", hidden=True)
    def _workflows_help_alias() -> None:
        """Hidden alias used by tests to enumerate help discovery."""
        _print_help_view(_repo_root(), include_all=False, category=None, audience=None)


def _print_help_view(
    repo_root: Path,
    *,
    include_all: bool,
    category: str | None,
    audience: str | None,
) -> None:
    aliases = _scan_aliases(repo_root)
    workflows = _scan_workflows(repo_root)
    prompts = _scan_atomic_prompts(repo_root)

    if aliases:
        typer.echo("Aliases (recommended entrypoints):")
        for aid, alias in sorted(aliases.items()):
            typer.echo(f"  {aid:<24} {alias.description.strip()[:80]}")
        typer.echo("")

    if workflows:
        typer.echo("Workflows:")
        for wid, wf in sorted(workflows.items()):
            typer.echo(f"  {wid:<24} {wf.description.strip()[:80]}")
        typer.echo("")

    if prompts:
        typer.echo("Atomic prompts:")
        groups: dict[str, list[AtomicPrompt]] = {}
        for p in prompts.values():
            if not include_all and not p.exposed:
                continue
            if category and p.category != category:
                continue
            if audience and p.audience != audience:
                continue
            groups.setdefault(p.category, []).append(p)
        order = {"beginner": 0, "intermediate": 1, "expert": 2}
        for cat in sorted(groups):
            typer.echo(f"  [{cat}]")
            for p in sorted(groups[cat], key=lambda x: (order.get(x.audience, 99), x.id)):
                typer.echo(f"    {p.id:<22} ({p.audience}) {p.description.strip()[:80]}")


def _git_dirty(repo_root: Path) -> bool:
    """Return True when `git status --porcelain` reports any change."""
    import subprocess

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


def _latest_harness_result(repo_root: Path) -> dict[str, Any] | None:
    runs_root = repo_root / ".documentation" / "devspark" / "runs"
    if not runs_root.is_dir():
        return None
    candidates = [path for path in runs_root.iterdir() if path.is_dir() and (path / "result.json").is_file()]
    if not candidates:
        return None
    latest = max(candidates, key=lambda item: item.stat().st_mtime)
    try:
        return json.loads((latest / "result.json").read_text(encoding="utf-8"))
    except Exception:
        return None


def _is_delivery_gate_target(workflow_id: str) -> bool:
    lowered = workflow_id.lower()
    return "create-pr" in lowered or "pr-review" in lowered


def _is_branch_synced_with_main(repo_root: Path) -> bool:
    import subprocess

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


def _get_governance_approval_status(repo_root: Path) -> dict[str, Any] | None:
    """Check for governance approval evidence in spec artifacts.
    
    Returns approval record if found, None otherwise.
    """
    # Check common feature spec locations
    spec_paths = [
        repo_root / ".documentation" / "specs" / "*/gates" / "governance-approval.md",
        repo_root / ".documentation" / "specs" / "*/governance-approval.md",
    ]
    
    for pattern_path in spec_paths:
        if "*" in str(pattern_path):
            import glob
            matches = glob.glob(str(pattern_path))
            for match in matches:
                try:
                    content = Path(match).read_text(encoding="utf-8")
                    # Check if approval record is populated
                    if "Approver Name:" in content and "Decision:" in content:
                        # Extract decision line
                        for line in content.split("\n"):
                            if "Decision:" in line:
                                decision = line.split("Decision:")[-1].strip()
                                if "approved" in decision.lower():
                                    return {"approved": True, "path": match, "decision": decision}
                except Exception:
                    continue
    
    return None


def _requires_governance_approval(workflow_id: str) -> bool:
    """Check if a workflow requires governance approval checkpoint.
    
    Workflows that modify cross-cutting runtime behavior require governance
    approval before execution begins.
    """
    lowered = workflow_id.lower()
    # Require approval for workflows marked in spec as governance-required
    # This includes harness delivery integrity and other cross-cutting features
    return "implement" in lowered and any(
        marker in lowered
        for marker in ["delivery-integrity", "harness", "governance"]
    )


def _make_telemetry(repo_root: Path):
    from .runner.telemetry import TelemetryWriter

    return TelemetryWriter(repo_root=repo_root)


def _make_enforcer(repo_root: Path, wf, autonomy_level: str):
    """Build an AutonomyEnforcer when guardrails are configured."""
    if not wf.guardrails:
        return None
    from .runner.autonomy import AutonomyEnforcer

    return AutonomyEnforcer(repo_root, wf.guardrails)
