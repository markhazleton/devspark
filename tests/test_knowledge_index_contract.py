# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from tests.bash_twin import BASH_EXE, to_bash_path

ROOT = Path(__file__).resolve().parent.parent
HAS_PWSH = shutil.which("pwsh") is not None
HAS_BASH = BASH_EXE is not None
FIXED_TIME = "2026-01-01T00:00:00Z"


def _wsl_path(path: Path) -> str:
    return to_bash_path(path)


def _node(path: Path, node_id: str = "authentication", node_type: str = "architecture") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            (
                "---",
                f"id: {node_id}",
                f"type: {node_type}",
                "title: Authentication",
                "links:",
                "  references:",
                "    - identity-provider",
                "appliesTo:",
                "  - src/auth/**",
                "---",
                "",
                "# Authentication",
                "",
                "Current authentication behavior.",
                "",
            )
        ),
        encoding="utf-8",
    )


def _run_ps(repo: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ | {"DEVSPARK_GENERATED_AT": FIXED_TIME}
    return subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(ROOT / "scripts/powershell/generate-knowledge-index.ps1"),
            "-RepoRoot",
            str(repo),
            "-Stdout",
            "-GeneratedAt",
            FIXED_TIME,
        ],
        text=True,
        capture_output=True,
        env=env,
        cwd=ROOT,
    )


def _run_bash(repo: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ | {"DEVSPARK_GENERATED_AT": FIXED_TIME}
    return subprocess.run(
        [
            BASH_EXE,
            _wsl_path(ROOT / "scripts/bash/generate-knowledge-index.sh"),
            "--repo-root",
            _wsl_path(repo),
            "--stdout",
            "--generated-at",
            FIXED_TIME,
        ],
        text=True,
        capture_output=True,
        env=env,
        cwd=ROOT,
    )


@pytest.mark.skipif(not HAS_PWSH or not HAS_BASH, reason="PowerShell and Bash required")
def test_generators_emit_identical_complete_index(tmp_path: Path) -> None:
    _node(tmp_path / ".knowledge/architecture/authentication.md")
    untyped = tmp_path / ".knowledge/reference/codes.md"
    untyped.parent.mkdir(parents=True)
    untyped.write_text("# Codes\n\nCurrent code reference.\n", encoding="utf-8")
    ephemeral = tmp_path / ".devspark.work/specs/example/knowledge/fr-001.md"
    ephemeral.parent.mkdir(parents=True)
    ephemeral.write_text("# Temporary requirement\n", encoding="utf-8")

    ps = _run_ps(tmp_path)
    bash = _run_bash(tmp_path)
    assert ps.returncode == 0, ps.stderr
    assert bash.returncode == 0, bash.stderr
    assert json.loads(ps.stdout) == json.loads(bash.stdout)

    index = json.loads(ps.stdout)
    assert [node["id"] for node in index["nodes"]] == ["authentication", "reference-codes"]
    assert index["nodes"][1]["type"] == "reference-data"
    assert index["edges"] == [
        {"from": "authentication", "to": "identity-provider", "rel": "references"}
    ]
    assert [root["path"] for root in index["roots"]] == [
        ".devspark/",
        ".devspark.work/",
        ".knowledge/",
        ".archive/",
    ]
    assert all(".devspark.work" not in node["path"] for node in index["nodes"])


@pytest.mark.skipif(not HAS_PWSH or not HAS_BASH, reason="PowerShell and Bash required")
@pytest.mark.parametrize(
    ("frontmatter", "body"),
    [
        ("status: superseded", "Current text."),
        ("type: historical-record", "Current text."),
        ("type: architecture\nlinks:\n  supersedes:\n    - old", "Current text."),
    ],
)
def test_generators_reject_noncurrent_knowledge(
    tmp_path: Path, frontmatter: str, body: str
) -> None:
    path = tmp_path / ".knowledge/example.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        f"---\nid: example\ntitle: Example\n{frontmatter}\n---\n\n# Example\n\n{body}\n",
        encoding="utf-8",
    )
    ps = _run_ps(tmp_path)
    bash = _run_bash(tmp_path)
    assert ps.returncode != 0
    assert bash.returncode != 0


@pytest.mark.skipif(not HAS_PWSH or not HAS_BASH, reason="PowerShell and Bash required")
def test_generators_accept_current_body_prose_using_lifecycle_words(tmp_path: Path) -> None:
    path = tmp_path / ".knowledge/example.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "---\nid: example\ntitle: Example\ntype: architecture\n---\n\n"
        "# Example\n\n"
        'Marks the prior version `status: superseded` as part of an ongoing scheme. '
        "The legacy field is no longer read (superseded by `new_field`); do not build "
        "new logic on it. The intent node is replaced by the in-process engine.\n",
        encoding="utf-8",
    )
    ps = _run_ps(tmp_path)
    bash = _run_bash(tmp_path)
    assert ps.returncode == 0, ps.stderr
    assert bash.returncode == 0, bash.stderr


@pytest.mark.skipif(not HAS_PWSH or not HAS_BASH, reason="PowerShell and Bash required")
@pytest.mark.parametrize(
    "applies_to_path",
    [".devspark.work/specs/001-foo/plan.md", ".archive/2026-01-01/specs/001-foo/plan.md"],
)
def test_generators_reject_appliesto_into_forbidden_roots(
    tmp_path: Path, applies_to_path: str
) -> None:
    path = tmp_path / ".knowledge/example.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "---\nid: example\ntitle: Example\ntype: architecture\nappliesTo:\n"
        f"  - {applies_to_path}\n---\n\n# Example\n\nCurrent behavior.\n",
        encoding="utf-8",
    )
    ps = _run_ps(tmp_path)
    bash = _run_bash(tmp_path)
    assert ps.returncode != 0
    assert bash.returncode != 0
    assert ".devspark.work/ or .archive/" in ps.stderr
    assert ".devspark.work/ or .archive/" in bash.stderr


def _init_git_repo_with_commit(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True)


def _entity(repo: Path, *, last_verified: str = "2000-01-01") -> None:
    entity_dir = repo / ".knowledge" / "entities" / "widget"
    entity_dir.mkdir(parents=True)
    (entity_dir / "_entity.yaml").write_text(
        "id: widget\ntype: subsystem\nowner: team-x\n", encoding="utf-8"
    )
    (entity_dir / "architecture.md").write_text(
        "\n".join(
            (
                "---",
                "type: entity-layer",
                "layer: architecture",
                "title: Widget Architecture",
                f"last_verified: {last_verified}",
                "source_of_truth:",
                "  - src/widget.py",
                "---",
                "",
                "# Widget Architecture",
                "",
                "Current behavior.",
                "",
            )
        ),
        encoding="utf-8",
    )
    source = repo / "src" / "widget.py"
    source.parent.mkdir(parents=True)
    source.write_text("value = 1\n", encoding="utf-8")


@pytest.mark.skipif(not HAS_PWSH or not HAS_BASH, reason="PowerShell and Bash required")
def test_generators_preserve_legacy_stale_entities_and_fail_on_stale_without_opt_in(
    tmp_path: Path,
) -> None:
    """Pins FR-012: object-claim/drift support installed alongside the wrappers must not change
    the no-opt-in legacy `stale_entities` reporting or `--fail-on-stale` blocking behavior."""
    _entity(tmp_path, last_verified="2000-01-01")
    _init_git_repo_with_commit(tmp_path)

    ps_default = _run_ps(tmp_path)
    bash_default = _run_bash(tmp_path)
    assert ps_default.returncode == 0, ps_default.stderr
    assert bash_default.returncode == 0, bash_default.stderr
    ps_index = json.loads(ps_default.stdout)
    bash_index = json.loads(bash_default.stdout)
    assert ps_index["stale_entities"], "stale entity must still be reported by default"
    assert ps_index["stale_entities"] == bash_index["stale_entities"]
    assert "STALE:" in ps_default.stderr
    assert "STALE:" in bash_default.stderr

    ps_strict = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(ROOT / "scripts/powershell/generate-knowledge-index.ps1"),
            "-RepoRoot",
            str(tmp_path),
            "-Stdout",
            "-FailOnStale",
            "-GeneratedAt",
            FIXED_TIME,
        ],
        text=True,
        capture_output=True,
        cwd=ROOT,
    )
    bash_strict = subprocess.run(
        [
            BASH_EXE,
            _wsl_path(ROOT / "scripts/bash/generate-knowledge-index.sh"),
            "--repo-root",
            _wsl_path(tmp_path),
            "--stdout",
            "--fail-on-stale",
            "--generated-at",
            FIXED_TIME,
        ],
        text=True,
        capture_output=True,
        cwd=ROOT,
    )
    assert ps_strict.returncode == 1
    assert bash_strict.returncode == 1
    assert "last_verified" in ps_strict.stderr
    assert "last_verified" in bash_strict.stderr


@pytest.mark.skipif(not HAS_PWSH or not HAS_BASH, reason="PowerShell and Bash required")
def test_generators_forward_detect_drift_full_inventory_identically(tmp_path: Path) -> None:
    self_test_src = ROOT / "templates" / "knowledge-drift" / "self-test"
    (tmp_path / "templates" / "knowledge-drift").mkdir(parents=True)
    shutil.copytree(self_test_src, tmp_path / "templates" / "knowledge-drift" / "self-test")
    (tmp_path / ".knowledge").mkdir()

    ps_report = tmp_path / "ps-report.json"
    bash_report = tmp_path / "bash-report.json"
    ps_result = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(ROOT / "scripts/powershell/generate-knowledge-index.ps1"),
            "-RepoRoot",
            str(tmp_path),
            "-DetectDrift",
            "-FullInventory",
            "-ReportOutput",
            str(ps_report),
        ],
        text=True,
        capture_output=True,
        cwd=ROOT,
    )
    bash_result = subprocess.run(
        [
            BASH_EXE,
            _wsl_path(ROOT / "scripts/bash/generate-knowledge-index.sh"),
            "--repo-root",
            _wsl_path(tmp_path),
            "--detect-drift",
            "--full-inventory",
            "--report-output",
            _wsl_path(bash_report),
        ],
        text=True,
        capture_output=True,
        cwd=ROOT,
    )

    assert ps_result.returncode == 0, ps_result.stderr
    assert bash_result.returncode == 0, bash_result.stderr
    assert json.loads(ps_report.read_text(encoding="utf-8"))["status"] == "ok"
    assert json.loads(bash_report.read_text(encoding="utf-8"))["status"] == "ok"
