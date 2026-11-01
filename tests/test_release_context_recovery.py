# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Release context is derived from the durable Git delta, never recovered plans."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from tests.bash_twin import BASH_EXE
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_scripts(repo: Path) -> None:
    for relative in (
        "scripts/release-context.py",
        "scripts/bash/release-context.sh",
        "scripts/powershell/release-context.ps1",
    ):
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


def context(command: list[str], repo: Path) -> dict[str, object]:
    return json.loads(run(command, repo).stdout)


def test_release_context_uses_only_durable_delta() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        repo = Path(temporary)
        copy_scripts(repo)
        run(["git", "init"], repo)
        run(["git", "config", "user.name", "Test User"], repo)
        run(["git", "config", "user.email", "test@test.invalid"], repo)
        write(repo / "pyproject.toml", '[project]\nname = "sample"\nversion = "1.0.0"\n')
        write(repo / "src" / "app.py", "VALUE = 1\n")
        write(repo / ".archive" / "old" / ".devspark.work" / "specs" / "001-old" / "tasks.md", "- [x] old\n")
        run(["git", "add", "."], repo)
        run(["git", "commit", "-m", "baseline"], repo)
        run(["git", "tag", "v1.0.0"], repo)

        write(repo / "src" / "app.py", "VALUE = 2\n")
        write(repo / "tests" / "test_app.py", "def test_value():\n    assert True\n")
        write(repo / ".knowledge" / "architecture" / "app.md", "# App\n")
        run(["git", "add", "."], repo)
        run(["git", "commit", "-m", "change behavior"], repo)

        powershell = context(
            ["pwsh", "-NoProfile", "-File", "scripts/powershell/release-context.ps1", "-Json"], repo
        )
        assert powershell["LAST_TAG"] == "v1.0.0"
        assert powershell["SOURCE_CHANGED"] == ["src/app.py"]
        assert powershell["TESTS_CHANGED"] == ["tests/test_app.py"]
        assert powershell["KNOWLEDGE_CHANGED"] == [".knowledge/architecture/app.md"]
        assert powershell["PLANNING_LEAKS"] == []
        for removed in ("COMPLETED_SPECS", "RECOVERED_COMPLETED_SPECS", "ARCHIVE_RECOVERY_USED", "CONTRIBUTORS"):
            assert removed not in powershell

        if BASH_EXE:
            bash = context([BASH_EXE, "scripts/bash/release-context.sh", "--json"], repo)
            for field in (
                "LAST_TAG",
                "RELEASE_FROM",
                "RELEASE_TO",
                "BASE_SHA",
                "HEAD_SHA",
                "CHANGED_FILES",
                "SOURCE_CHANGED",
                "TESTS_CHANGED",
                "KNOWLEDGE_CHANGED",
                "PLANNING_LEAKS",
            ):
                assert bash[field] == powershell[field]


def test_release_context_classifies_archive_eligibility() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        repo = Path(temporary)
        copy_scripts(repo)
        run(["git", "init"], repo)
        run(["git", "config", "user.name", "Test User"], repo)
        run(["git", "config", "user.email", "test@test.invalid"], repo)
        write(repo / "pyproject.toml", '[project]\nname = "sample"\nversion = "1.0.0"\n')

        specs = repo / ".devspark.work" / "specs"
        write(
            specs / "010-done" / "spec.md",
            "# Done\n\n**Status**: Complete\n",
        )
        write(
            specs / "010-done" / "tasks.md",
            "- [x] T001 Ship it code_ref: src/app.py | knowledge_ref: .knowledge/architecture/app.md\n",
        )
        write(
            specs / "011-legacy-pending-linkage" / "spec.md",
            "# Legacy\n\n**Status**: Complete\n",
        )
        write(
            specs / "011-legacy-pending-linkage" / "tasks.md",
            "- [x] T001 Ship it code_ref: pending | knowledge_ref: .knowledge/architecture/app.md\n",
        )
        write(specs / "012-in-flight" / "spec.md", "# In flight\n\n**Status**: Draft\n")

        write(
            repo / ".devspark.work" / "quickfixes" / "QF-2026-001.md",
            "# QF-2026-001\n\n**Status**: Complete\n\ncode_ref: src/app.py\nknowledge_ref: n/a - no durable behavior change\n",
        )

        run(["git", "add", "."], repo)
        run(["git", "commit", "-m", "baseline"], repo)

        payload = context(["python", "scripts/release-context.py", "--json"], repo)

        eligible = set(payload["ARCHIVE_ELIGIBLE"])
        assert ".devspark.work/specs/010-done" in eligible
        assert ".devspark.work/quickfixes/QF-2026-001.md" in eligible
        assert ".devspark.work/specs/011-legacy-pending-linkage" in eligible
        assert ".devspark.work/specs/012-in-flight" not in eligible

        blocked = {item["path"]: item for item in payload["ARCHIVE_BLOCKED"]}
        assert "not marked Complete" in "; ".join(
            blocked[".devspark.work/specs/012-in-flight"]["blockers"]
        )


def test_knowledge_build_status_uses_the_index_builder() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        repo = Path(temporary)
        copy_scripts(repo)
        shutil.copy2(ROOT / "scripts/build_knowledge_index.py", repo / "scripts/build_knowledge_index.py")
        run(["git", "init"], repo)
        run(["git", "config", "user.name", "Test User"], repo)
        run(["git", "config", "user.email", "test@test.invalid"], repo)
        write(repo / "pyproject.toml", '[project]\nname = "sample"\nversion = "1.0.0"\n')
        write(
            repo / ".knowledge" / "architecture" / "app.md",
            "---\nid: app\ntype: architecture\ntitle: App\n---\n\n# App\n\nCurrent behavior.\n",
        )
        write(repo / ".knowledge" / "index.json", '{"nodes": []}\n')
        run(["git", "add", "."], repo)
        run(["git", "commit", "-m", "baseline"], repo)

        payload = context(["python", "scripts/release-context.py", "--json"], repo)
        assert payload["KNOWLEDGE_BUILDS"] is True, (
            "a stale derived index must not matter when the Knowledge builds"
        )
        assert "KNOWLEDGE_INDEX_CURRENT" not in payload


def test_knowledge_build_status_prefers_the_devspark_managed_engine() -> None:
    """When both a legacy repo-root copy and the framework-managed `.devspark/scripts/` copy of
    the index builder exist, the framework-managed copy is always the one used -- a repository
    must never get a different answer depending on which copy a caller happens to find first."""
    with tempfile.TemporaryDirectory() as temporary:
        repo = Path(temporary)
        copy_scripts(repo)
        # A broken/divergent legacy root copy -- if this were ever consulted, the check would
        # exit 2 and the status would be None rather than True.
        write(
            repo / "scripts" / "build_knowledge_index.py",
            "import sys\nsys.exit(2)\n",
        )
        devspark_engine = repo / ".devspark" / "scripts" / "build_knowledge_index.py"
        devspark_engine.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "scripts/build_knowledge_index.py", devspark_engine)
        run(["git", "init"], repo)
        run(["git", "config", "user.name", "Test User"], repo)
        run(["git", "config", "user.email", "test@test.invalid"], repo)
        write(repo / "pyproject.toml", '[project]\nname = "sample"\nversion = "1.0.0"\n')
        write(
            repo / ".knowledge" / "architecture" / "app.md",
            "---\nid: app\ntype: architecture\ntitle: App\n---\n\n# App\n\nCurrent behavior.\n",
        )
        run(["git", "add", "."], repo)
        run(["git", "commit", "-m", "baseline"], repo)

        payload = context(["python", "scripts/release-context.py", "--json"], repo)
        assert payload["KNOWLEDGE_BUILDS"] is True, (
            "the real .devspark/scripts/build_knowledge_index.py must be used, "
            "not the broken repo-root copy"
        )
