"""Contracts for the ephemeral-reference comment scanner (rule 5)."""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCANNER = ROOT / "scripts" / "scan-ephemeral-refs.py"
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]


def _scan(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCANNER), "--root", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def _repo(tmp_path: Path, files: dict[str, str]) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    for relative, text in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text), encoding="utf-8")
    subprocess.run([*GIT, "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run([*GIT, "commit", "-qm", "base"], cwd=tmp_path, check=True)
    return tmp_path


def test_flags_ephemeral_ids_in_comments_only(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {
            "src/auth.py": """\
                # Refresh tokens early (T014)
                LABEL = "T015 inside a string is fine"
                value = 1  # see .devspark.work/specs/001-auth/plan.md
            """,
            "src/app.ts": """\
                /* Implements FR-003 */
                const id = "CAP-2026-001"; // fine: CAP-2026-002 is in a comment, so flagged
            """,
            "scripts/run.ps1": """\
                <#
                  Added for spec 001-token-refresh
                #>
                Write-Host 'T099'
            """,
            "docs/guide.md": "Markdown is out of scope: T001\n",
            ".devspark.work/specs/001-auth/tasks.md": "- [X] T001\n",
        },
    )
    result = _scan(repo, "--full-inventory")
    assert result.returncode == 1, result.stdout + result.stderr
    found = {(item["path"], item["kind"], item["match"]) for item in json.loads(result.stdout)["findings"]}
    assert found == {
        ("src/auth.py", "task-id", "T014"),
        ("src/auth.py", "work-package-path", ".devspark.work/specs/001-auth"),
        ("src/app.ts", "requirement-id", "FR-003"),
        ("src/app.ts", "proposal-id", "CAP-2026-002"),
        ("scripts/run.ps1", "spec-id", "spec 001-token-refresh"),
    }


def test_git_scope_only_scans_changed_files(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"src/old.py": "# legacy note (T001)\n", "src/new.py": "value = 1\n"})
    (repo / "src" / "new.py").write_text("# clean comment\nvalue = 2\n", encoding="utf-8")
    subprocess.run([*GIT, "commit", "-qam", "head"], cwd=repo, check=True)
    result = _scan(repo, "--base", "HEAD~1")
    assert result.returncode == 0, result.stdout
    assert json.loads(result.stdout)["files_scanned"] == 1
    assert _scan(repo).returncode == 2, "an explicit scope is required"


def test_devspark_source_has_no_ephemeral_comment_references() -> None:
    result = _scan(ROOT, "--full-inventory")
    assert result.returncode == 0, result.stdout
