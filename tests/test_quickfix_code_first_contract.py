"""Quickfix entry contracts and an offline, already-implemented diff exercise.

Prompt assertions guard the instructions, not an AI runtime's compliance. The executable
example supplies real diff/test evidence for a manual walkthrough of those instructions.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.consumer_skill_helpers import bash_path

ROOT = Path(__file__).resolve().parents[1]
QUICKFIX = ROOT / "templates" / "commands" / "quickfix.md"


def test_engineering_philosophy_has_one_existing_published_home() -> None:
    philosophy = (ROOT / "site" / "src" / "why" / "philosophy.md").read_text(encoding="utf-8")
    manifesto = " ".join(philosophy.replace("*", "").split())
    for principle in (
        "helps developers use intelligent tools to create trustworthy, maintainable software",
        "regardless of how their development journey begins",
        "AI amplifies engineering judgment; it does not replace software engineering.",
        "Code First, Model First, exploratory development, defect investigation, and formal specification can all be appropriate.",
        "methodology-independent, but engineering-discipline-dependent.",
        "Stop measuring process compliance as a proxy for software quality.",
        "The Delta is the unit of engineering value, not the workflow used to produce it.",
        "Validate the blast radius, not the entire universe.",
        "Confidence comes from credible evidence, not declarations of compliance.",
    ):
        assert principle in manifesto
    assert "DevSpark protects three enduring engineering assets:" in manifesto
    for asset in ("Code:", "Tests:", "Durable Knowledge:"):
        assert asset in manifesto
    assert "site/src/why/philosophy.md#our-vision" in (ROOT / "README.md").read_text(encoding="utf-8")


def test_code_first_inspects_all_diff_surfaces_and_establishes_intent() -> None:
    prompt = QUICKFIX.read_text(encoding="utf-8")
    entry = prompt.split("### Code First Entry:", 1)[1].split("### 3.", 1)[0]
    for instruction in (
        "git status --short", "git diff --no-ext-diff", "git diff --cached --no-ext-diff",
        "<base>...HEAD", "untracked files", "callers, and tests", "ownership is ambiguous",
        "inferred intent", "unknown\n   root cause", "important intent",
        "boundary cases", "regressions", "regression/edge-case coverage",
    ):
        assert instruction in entry
    assert "all dirty files as this change" in entry


def test_code_first_preserves_chronology_and_proportionate_knowledge() -> None:
    prompt = QUICKFIX.read_text(encoding="utf-8")
    for instruction in (
        "implementation preceded this review", "never backdate", "actual\n   timestamps",
        "create Knowledge only for lasting engineering value",
        "knowledge_ref: n/a", "Reuse a matching existing record",
        "Validate already-done\n   items instead of reimplementing them",
        "Do not request fictional `spec.md`, `plan.md`, or `tasks.md`",
        "unrelated changes are already staged, leave the index untouched",
    ):
        assert instruction in prompt


def test_failures_and_material_risk_cannot_be_reported_as_passing() -> None:
    prompt = QUICKFIX.read_text(encoding="utf-8")
    for instruction in (
        "independent assurance, organizational requirements, and authorization",
        "A failing required check prevents a passing result and finalization",
        "not-run and blocked checks\n   remain unproven",
        "An acknowledgement does not satisfy an unmet mandatory requirement",
        "Never print the sample PASS or a completed claim by default",
        "distinguishing Quickfix's own review from any independent review",
        "do not finalize until applicable requirements pass",
    ):
        assert instruction in prompt
    assert "ask whether to continue anyway" not in prompt


def test_traditional_entry_still_hands_off_without_claiming_verification() -> None:
    prompt = QUICKFIX.read_text(encoding="utf-8")
    for instruction in (
        "### 3. Validate Scope", "### 4. Load Constitution (Targeted)",
        "### 7. Confirm, Then Create the Quickfix Branch", "Wait for an explicit yes",
        "### 8. Generate Quickfix Record", "### 9. Commit Quickfix Record",
        "For traditional entry, creation is not verification",
        "recommended_next_step: implement", "/devspark-quickfix complete {NEXT_ID}",
    ):
        assert instruction in prompt
    implement = (ROOT / "templates" / "commands" / "implement.md").read_text(encoding="utf-8")
    assert "record, no `spec.md`" in implement
    assert "Run all required verification and refuse finalization on any failure" in implement


def _run(repo: Path, *command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, cwd=repo, capture_output=True, text=True, encoding="utf-8",
        input="", timeout=20,
    )


@pytest.fixture(scope="module")
def exploratory_change(tmp_path_factory: pytest.TempPathFactory) -> Path:
    repo = tmp_path_factory.mktemp("code-first-example")
    for command in (
        ("git", "init", "--initial-branch=main"),
        ("git", "config", "user.name", "Test User"),
        ("git", "config", "user.email", "user@example.com"),
    ):
        result = _run(repo, *command)
        assert result.returncode == 0, result.stderr
    constitution = repo / ".knowledge" / "governance" / "constitution.md"
    constitution.parent.mkdir(parents=True)
    constitution.write_text(
        "# Synthetic Constitution\n\n"
        "- Changed behavior must have passing regression tests.\n"
        "- Failed checks must not be reported as passing.\n",
        encoding="utf-8",
    )
    (repo / "file_kind.py").write_text(
        "from pathlib import Path\n\n"
        "def is_markdown(path):\n"
        '    return Path(path).suffix == ".md"\n', encoding="utf-8",
    )
    (repo / "test_file_kind.py").write_text(
        "import unittest\nfrom file_kind import is_markdown\n\n"
        "class FileKindTests(unittest.TestCase):\n"
        "    def test_existing_behavior(self):\n"
        '        self.assertTrue(is_markdown("guide.md"))\n'
        '        self.assertFalse(is_markdown("guide.txt"))\n', encoding="utf-8",
    )
    for command in (("git", "add", "."), ("git", "commit", "-m", "Synthetic baseline")):
        result = _run(repo, *command)
        assert result.returncode == 0, result.stderr
    # The developer's exploratory implementation exists before Quickfix review.
    source = repo / "file_kind.py"
    source.write_text(source.read_text(encoding="utf-8").replace(".suffix ==", ".suffix.lower() =="), encoding="utf-8")
    return repo


def test_existing_diff_walkthrough_and_real_failure_evidence(exploratory_change: Path) -> None:
    repo = exploratory_change
    diff = _run(repo, "git", "--no-pager", "diff", "--no-ext-diff")
    assert diff.returncode == 0, diff.stderr
    assert '+    return Path(path).suffix.lower() == ".md"' in diff.stdout
    original = _run(repo, sys.executable, "-m", "unittest", "-v")
    assert original.returncode == 0, original.stderr

    # Inspection identifies absent uppercase/compound-suffix coverage.
    tests = repo / "test_file_kind.py"
    tests.write_text(
        tests.read_text(encoding="utf-8")
        + "\n    def test_case_and_suffix_boundaries(self):\n"
        '        self.assertTrue(is_markdown("guide.MD"))\n'
        '        self.assertTrue(is_markdown("guide.Md"))\n'
        '        self.assertFalse(is_markdown("guide.md.txt"))\n'
        '        self.assertFalse(is_markdown("guide"))\n',
        encoding="utf-8",
    )
    verified = _run(repo, sys.executable, "-B", "-m", "unittest", "-v")
    assert verified.returncode == 0, verified.stderr
    source = repo / "file_kind.py"
    implemented = source.read_text(encoding="utf-8")
    try:
        source.write_text(implemented.replace(".suffix.lower()", ".suffix"), encoding="utf-8")
        # Avoid a same-size, same-second bytecode cache hiding the seeded regression.
        for cached in (repo / "__pycache__").glob("file_kind.*.pyc"):
            cached.unlink()
        failed = _run(repo, sys.executable, "-B", "-m", "unittest", "-v")
        assert failed.returncode != 0
        assert "FAIL: test_case_and_suffix_boundaries" in failed.stderr
    finally:
        source.write_text(implemented, encoding="utf-8")
    restored = _run(repo, sys.executable, "-B", "-m", "unittest", "-v")
    assert restored.returncode == 0, restored.stderr
    assert not (repo / ".devspark.work" / "specs").exists()
    assert list((repo / ".knowledge").rglob("*.md")) == [
        repo / ".knowledge" / "governance" / "constitution.md"
    ]
    print(
        "\nCode First walkthrough evidence (not an automated AI-agent evaluation):\n"
        + diff.stdout
        + "\nIntent: recognize Markdown extensions case-insensitively; reject other suffixes.\n"
        + "Knowledge: no existing owner or lasting architectural/operational claim changes; no document needed.\n"
        + "Chronology: implementation existed before review; missing boundary tests added during review.\n"
        + "Original tests:\n" + original.stderr
        + "Added validation:\n" + verified.stderr
        + "Seeded regression (must not pass):\n" + failed.stderr
        + "Restored implementation:\n" + restored.stderr
    )


@pytest.mark.parametrize("shell", ["pwsh", "bash"])
def test_traditional_context_still_accepts_a_request_without_code(
    shell: str, tmp_path: Path,
) -> None:
    executable = shutil.which("pwsh") if shell == "pwsh" else bash_path()
    if executable is None:
        pytest.skip(f"{shell} unavailable")
    initialized = _run(tmp_path, "git", "init", "--initial-branch=main")
    assert initialized.returncode == 0, initialized.stderr
    constitution = tmp_path / ".knowledge" / "governance" / "constitution.md"
    constitution.parent.mkdir(parents=True)
    constitution.write_text("# Synthetic Constitution\n", encoding="utf-8")
    if shell == "pwsh":
        command = (
            executable, "-NoProfile", "-File",
            str(ROOT / "scripts" / "powershell" / "quickfix-context.ps1"),
            "fix markdown extension", "-Json",
        )
    else:
        command = (
            executable, str(ROOT / "scripts" / "bash" / "quickfix-context.sh"),
            "fix markdown extension", "--json",
        )
    result = _run(tmp_path, *command)
    assert result.returncode == 0, result.stdout + result.stderr
    context = json.loads(result.stdout)
    assert context["ACTION"] == "create"
    assert context["CLASSIFICATION"] == "bug-fix"
    assert context["CONSTITUTION_EXISTS"] in (True, "true")
    assert context["CURRENT_BRANCH"] == "main"
    assert not (tmp_path / ".devspark.work").exists()
    assert _run(tmp_path, "git", "diff", "--no-ext-diff").stdout == ""
