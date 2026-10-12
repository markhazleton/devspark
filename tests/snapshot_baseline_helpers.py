# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Test-only capture helper for the behavior-neutral snapshot baseline.

Never shipped. It records, per stock command, a hash of the command body after spelling
normalization, and the lifecycle outputs (``judge.py lifecycle`` plus both ``next-context`` twins)
for the synthetic gate bundles. The baseline JSON files under ``tests/fixtures/snapshot-baseline/``
were captured once from the unchanged tree; the neutral-snapshot test recomputes the same values and
compares them.

Spelling normalization is deliberately narrow: only a stock command name written with a hyphen
(``devspark-<cmd>``, with or without a leading slash, including the ``{command}`` placeholder) is
rewritten to the dotted form (``devspark.<cmd>``), so the later respelling of invocations does not
read as a content change. Line endings are normalized to LF.
Nothing else is rewritten: prose, paths such as ``devspark.<cmd>.md``, unknown command names and
longer hyphenated names (for example ``/devspark-next-context``) are left byte-for-byte alone.

Regenerate with: ``PYTHONPATH=src python tests/snapshot_baseline_helpers.py`` (run from the unchanged
tree; a deliberate behavior change is recorded as a named delta in the test instead).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
COMMANDS = ROOT / "templates" / "commands"
BUNDLES = ROOT / "tests" / "fixtures" / "stage-evidence"
BASELINE = ROOT / "tests" / "fixtures" / "snapshot-baseline"
JUDGE = ROOT / "scripts" / "judge.py"
PS_SCRIPT = ROOT / "scripts" / "powershell" / "next-context.ps1"
SH_SCRIPT = ROOT / "scripts" / "bash" / "next-context.sh"
GIT_BASH = Path(r"C:\Program Files\Git\bin\bash.exe")
FEATURE = "001-demo"
NEXT_FIELDS = (
    "STATE",
    "RECOMMENDED_COMMAND",
    "VERIFY_REQUIRED",
    "VERIFY_PASSED",
    "CLOSEOUT_DECISION",
    "TASKS_COMPLETE",
)


def stock_commands() -> list[str]:
    return sorted(p.stem for p in COMMANDS.glob("*.md"))


def normalize_spelling(text: str) -> str:
    """Rewrite ``devspark-<stock command>`` invocations to ``devspark.<stock command>``."""
    names = "|".join(re.escape(name) for name in sorted(stock_commands(), key=len, reverse=True))
    pattern = re.compile(rf"(?<![A-Za-z0-9_./-])(/?)devspark-({names}|\{{command\}})(?![A-Za-z0-9_-])")
    return pattern.sub(r"\1devspark.\2", text.replace("\r\n", "\n"))


def command_hashes() -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(COMMANDS.glob("*.md")):
        body = normalize_spelling(path.read_bytes().decode("utf-8"))
        result[path.stem] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return result


def bundles() -> list[str]:
    return sorted(p.name for p in BUNDLES.iterdir() if p.is_dir())


def _bash() -> str | None:
    if os.name == "nt":
        return str(GIT_BASH) if GIT_BASH.exists() and shutil.which("jq") else None
    return shutil.which("bash") if shutil.which("jq") else None


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, timeout=60, stdin=subprocess.DEVNULL)


def make_repo(base: Path, bundle: str) -> Path:
    repo = base / "r"
    (repo / ".knowledge" / "governance").mkdir(parents=True)
    (repo / ".knowledge" / "governance" / "constitution.md").write_text("# C\n", encoding="utf-8")
    shutil.copytree(BUNDLES / bundle, repo / ".devspark.work" / "specs" / FEATURE)
    _git(repo, "init", "-q", "-b", FEATURE)
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "T")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Synthetic bundle")
    return repo


def judge_lifecycle(repo: Path) -> dict:
    feature = repo / ".devspark.work" / "specs" / FEATURE
    proc = subprocess.run(
        [sys.executable, str(JUDGE), "lifecycle", "--feature-dir", str(feature)],
        cwd=repo, capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL,
    )
    return _normalized(json.loads(proc.stdout))


def next_context(shell: str, repo: Path) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "DEVSPARK_FEATURE"}
    stubs = repo.parent / "host-stubs"
    stubs.mkdir(exist_ok=True)
    for command in ("gh", "az"):
        (stubs / command).write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        (stubs / command).chmod(0o755)
        (stubs / f"{command}.cmd").write_text("@exit /b 1\n", encoding="utf-8")
    env["PATH"] = str(stubs) + os.pathsep + str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    cmd = ["pwsh", "-NoProfile", "-File", str(PS_SCRIPT), "-Json"] if shell == "pwsh" else [_bash(), str(SH_SCRIPT), "--json"]
    proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, timeout=120, stdin=subprocess.DEVNULL, env=env)
    payload = json.loads(proc.stdout)
    return _normalized({key: payload.get(key) for key in NEXT_FIELDS})


def _normalized(value):
    if isinstance(value, str):
        return normalize_spelling(value)
    if isinstance(value, list):
        return [_normalized(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalized(item) for key, item in value.items()}
    return value


def lifecycle_outputs(base: Path) -> dict[str, dict]:
    """Per bundle: the lifecycle verdict and both next-context twins on a fresh synthetic repo."""
    result: dict[str, dict] = {}
    for index, bundle in enumerate(bundles()):
        workdir = base / f"b{index}"
        workdir.mkdir()
        repo = make_repo(workdir, bundle)
        result[bundle] = {
            "judge_lifecycle": judge_lifecycle(repo),
            "next_context_pwsh": next_context("pwsh", repo),
            "next_context_bash": next_context("bash", repo),
        }
    return result


def capture(base: Path) -> dict[str, dict]:
    return {"command-bodies": command_hashes(), "lifecycle-outputs": lifecycle_outputs(base)}


def write_baseline() -> None:
    BASELINE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT / ".tmp-capture" if (ROOT / ".tmp-capture").exists() else None) as work:
        data = capture(Path(work))
    for name, value in data.items():
        (BASELINE / f"{name}.json").write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_baseline()
