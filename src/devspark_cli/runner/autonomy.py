"""DevSpark workflow runner — autonomy enforcer.

Captures a per-step working-tree baseline (HEAD commit + tracked file diff
checksum), evaluates the diff after step execution against the workflow's
guardrail policy, and either:

  - returns {"action": "ok"}        when within bounds
  - returns {"action": "pause", "rule": ...}   when policy says downgrade
  - returns {"action": "block", "rule": ...}   when policy says hard-block

Guardrail keys (from contracts/workflow-schema.md):

  max_files_changed:        int
  restricted_paths:         list[str glob]
  max_total_lines_changed:  int

The enforcer is invoked by `WorkflowRunner.before_step` / `after_step`.
For autonomous runs it returns "block"; for assisted runs it returns "pause".
"""

from __future__ import annotations

import fnmatch
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class _Baseline:
    head: str = ""
    tracked: dict[str, str] = field(default_factory=dict)


class AutonomyEnforcer:
    def __init__(self, repo_root: Path, guardrails: dict[str, Any]) -> None:
        self.repo_root = repo_root
        self.guardrails = guardrails or {}
        self._baselines: dict[str, _Baseline] = {}

    # -------------------------------------------------- pre-step hook
    def before_step(self, run, step) -> None:
        # Skip the (potentially expensive) baseline capture entirely when
        # there are no guardrails to enforce. Mirrors the early-return in
        # ``after_step`` and keeps step latency low on guardrail-free runs.
        if not self.guardrails:
            return
        baseline = _Baseline()
        baseline.head = self._git("rev-parse", "HEAD") or ""
        files = (self._git("ls-files") or "").splitlines()
        for f in files:
            baseline.tracked[f] = self._hash_file(self.repo_root / f)
        self._baselines[step.id] = baseline

    # -------------------------------------------------- post-step hook
    def after_step(self, run, step) -> dict[str, Any]:
        if not self.guardrails:
            return {"action": "ok"}

        baseline = self._baselines.get(step.id)
        if baseline is None:
            return {"action": "ok"}

        # Compute delta against baseline.
        current_files = (self._git("ls-files") or "").splitlines()
        changed: list[str] = []
        for f in current_files:
            now = self._hash_file(self.repo_root / f)
            before = baseline.tracked.get(f)
            if before != now:
                changed.append(f)
        # Track deletions
        for f in baseline.tracked:
            if f not in current_files:
                changed.append(f)

        # Restricted paths (glob match)
        restricted = self.guardrails.get("restricted_paths") or []
        for path in changed:
            for pattern in restricted:
                if fnmatch.fnmatch(path, pattern):
                    return self._decision(run, f"restricted_paths: {path} matched {pattern}")

        # Max files
        max_files = self.guardrails.get("max_files_changed")
        if isinstance(max_files, int) and len(changed) > max_files:
            return self._decision(
                run,
                f"max_files_changed: {len(changed)} > {max_files}",
            )

        # Max total lines (best-effort via git diff --numstat)
        max_lines = self.guardrails.get("max_total_lines_changed")
        if isinstance(max_lines, int) and changed:
            numstat = self._git("diff", "--numstat", baseline.head) or ""
            total = 0
            for row in numstat.splitlines():
                parts = row.split("\t")
                if len(parts) >= 2:
                    try:
                        total += int(parts[0]) + int(parts[1])
                    except ValueError:
                        continue
            if total > max_lines:
                return self._decision(
                    run,
                    f"max_total_lines_changed: {total} > {max_lines}",
                )

        return {"action": "ok"}

    def _decision(self, run, rule: str) -> dict[str, Any]:
        if run.autonomy_level == "autonomous":
            return {"action": "block", "rule": rule}
        return {"action": "pause", "rule": rule}

    # -------------------------------------------------- helpers
    def _git(self, *args: str) -> str | None:
        try:
            r = subprocess.run(
                ["git", *args],
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            return None
        if r.returncode != 0:
            return None
        return r.stdout

    @staticmethod
    def _hash_file(path: Path) -> str:
        if not path.is_file():
            return ""
        import hashlib

        h = hashlib.sha1()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
