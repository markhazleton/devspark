# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract test: after Update or Repair, `.devspark/` holds exactly what the manifest lists.

Quickstart Step 9.5 prunes in two passes: root entries not in `manifest.devspark_root`, then every
file under `.devspark/defaults/`, `templates/` and `scripts/` whose path is not a `dest` in
`manifest.install`. These tests run the Bash and PowerShell code from each quickstart against a
synthetic install, so the published procedure itself is what is verified.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.consumer_skill_helpers import bash_path

ROOT = Path(__file__).resolve().parent.parent
QUICKSTARTS = sorted((ROOT / "quickstart").glob("devspark_quickstart_*.md"))
STAMP = "VERSION"
TIMEOUT = 120

CANONICAL = [
    ".devspark/defaults/commands/devspark.specify.md",
    ".devspark/templates/spec-template.md",
    ".devspark/templates/skills/write-spec/SKILL.md",
    ".devspark/scripts/bash/common.sh",
    ".devspark/scripts/powershell/common.ps1",
]
STALE = [
    ".devspark/defaults/commands/devspark.retired.md",
    ".devspark/templates/old-template.md",
    ".devspark/scripts/bash/create-new-feature.sh",
    ".devspark/scripts/powershell/create-new-feature.ps1",
    ".devspark/scripts/legacy/only-file.py",
]
REPO_OWNED = [
    ".devspark.work/commands/devspark.specify.md",
    ".devspark.work/scripts/bash/create-new-feature.sh",
    ".knowledge/governance/constitution.md",
    ".archive/2026-01-01/note.md",
]


def _step_95(quickstart: Path) -> str:
    text = quickstart.read_text(encoding="utf-8")
    match = re.search(r"^## Step 9\.5:.*?(?=^## Step 10)", text, flags=re.MULTILINE | re.DOTALL)
    assert match, f"{quickstart.name}: Step 9.5 not found"
    return match.group(0)


def _blocks(section: str, language: str) -> list[str]:
    return re.findall(rf"^```{language}\n(.*?)^```", section, flags=re.MULTILINE | re.DOTALL)


def _install(repo: Path, install: list[str]) -> Path:
    for rel in CANONICAL + STALE + REPO_OWNED + [f".devspark/{STAMP}", ".devspark/aliases/old.md"]:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n", encoding="utf-8")
    manifest = {
        "devspark_root": [STAMP, "defaults", "templates", "scripts"],
        "install": [{"source": d, "dest": d, "category": "template"} for d in install],
    }
    path = repo / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _files(repo: Path) -> set[str]:
    return {p.relative_to(repo).as_posix() for p in repo.rglob("*") if p.is_file()} - {"manifest.json", "prune.sh", "prune.ps1", "dests.txt"}


def _run(shell: str, quickstart: Path, repo: Path, manifest: Path) -> str:
    section = _step_95(quickstart)
    if shell == "bash":
        bash, jq = bash_path(), shutil.which("jq")
        if bash is None or jq is None:
            pytest.skip("bash and jq are required")
        body = "\n".join(_blocks(section, "bash"))
        body = body.replace("/tmp/devspark-manifest.json", manifest.as_posix()).replace("/tmp/devspark-dests.txt", "dests.txt")
        script = repo / "prune.sh"
        script.write_bytes(("set -euo pipefail\n" + body).encode("utf-8"))
        args = [bash, str(script)]
    else:
        pwsh = shutil.which("pwsh")
        if pwsh is None:
            pytest.skip("pwsh is required")
        body = "\n".join(_blocks(section, "powershell"))
        script = repo / "prune.ps1"
        script.write_text(
            "$ErrorActionPreference = 'Stop'\n"
            f"$manifest = Get-Content -Raw -LiteralPath '{manifest}' | ConvertFrom-Json\n" + body,
            encoding="utf-8",
        )
        args = [pwsh, "-NoProfile", "-NonInteractive", "-File", str(script)]
    result = subprocess.run(args, cwd=repo, capture_output=True, text=True, encoding="utf-8", timeout=TIMEOUT)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def test_every_quickstart_publishes_the_same_step_95() -> None:
    assert len(QUICKSTARTS) == 6
    sections = {q.name: _step_95(q) for q in QUICKSTARTS}
    assert len(set(sections.values())) == 1, sorted(sections)
    section = next(iter(sections.values()))
    assert len(_blocks(section, "bash")) == 2 and len(_blocks(section, "powershell")) == 2
    assert "manifest.install" in section and "Never prune against an empty list" in section


@pytest.mark.parametrize("quickstart", QUICKSTARTS, ids=lambda p: p.stem.removeprefix("devspark_quickstart_"))
def test_bash_manifest_loops_strip_carriage_returns(quickstart: Path) -> None:
    # A Windows jq ends lines with CRLF; `read` keeps the CR, so a dest would gain a trailing "\r".
    lines = quickstart.read_text(encoding="utf-8").splitlines()
    loops = [line for line in lines if "/tmp/devspark-manifest.json" in line and ("@tsv'" in line or "done < <(jq" in line)]
    assert len(loops) == 2, loops
    assert all("tr -d '\\r'" in line for line in loops), loops


@pytest.mark.parametrize("shell", ["bash", "pwsh"])
@pytest.mark.parametrize("quickstart", QUICKSTARTS, ids=lambda p: p.stem.removeprefix("devspark_quickstart_"))
def test_prune_leaves_exactly_the_manifest_in_devspark(tmp_path: Path, quickstart: Path, shell: str) -> None:
    manifest = _install(tmp_path, CANONICAL)

    _run(shell, quickstart, tmp_path, manifest)

    devspark = {f for f in _files(tmp_path) if f.startswith(".devspark/")}
    assert devspark == set(CANONICAL) | {f".devspark/{STAMP}"}
    assert {f for f in _files(tmp_path) if not f.startswith(".devspark/")} == set(REPO_OWNED)
    assert not (tmp_path / ".devspark/scripts/legacy").exists(), "empty directories must be removed"
    assert not (tmp_path / ".devspark/aliases").exists(), "non-canonical root entries must be removed"


@pytest.mark.parametrize("shell", ["bash", "pwsh"])
def test_prune_never_runs_pass_2_against_an_empty_install_list(tmp_path: Path, shell: str) -> None:
    manifest = _install(tmp_path, [])

    output = _run(shell, QUICKSTARTS[0], tmp_path, manifest)

    assert "Skipping Pass 2" in output
    for rel in CANONICAL + STALE + REPO_OWNED:
        assert (tmp_path / rel).is_file(), rel
