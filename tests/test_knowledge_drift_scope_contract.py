from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

from tests.knowledge_drift_test_helpers import commit_all, init_git_repo, parse_json_report, run_bounded, write_file

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "scripts" / "build_knowledge_index.py"
SELF_TEST = ROOT / "templates" / "knowledge-drift" / "self-test"


def _prepared_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "templates" / "knowledge-drift").mkdir(parents=True)
    shutil.copytree(SELF_TEST, repo / "templates" / "knowledge-drift" / "self-test")
    (repo / ".knowledge").mkdir()
    init_git_repo(repo)
    commit_all(repo, "initial commit")
    return repo


def _run(repo: Path, report: Path, *, base: str, head: str) -> tuple[int, dict]:
    result = run_bounded(
        [
            sys.executable,
            str(ENGINE),
            "--repo-root",
            str(repo),
            "--detect-drift",
            "--base",
            base,
            "--head",
            head,
            "--report-output",
            str(report),
        ],
        cwd=ROOT,
    )
    return result.returncode, parse_json_report(report)


def test_unrelated_change_produces_silence(tmp_path: Path) -> None:
    repo = _prepared_git_repo(tmp_path)
    base = run_bounded(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    write_file(repo / "docs" / "unrelated.md", "unrelated change\n")
    head = commit_all(repo, "unrelated change")

    code, report = _run(repo, tmp_path / "report.json", base=base, head=head)

    assert code == 0, report
    assert report["findings"] == []
    assert report["mode"] == "routine"


def test_missing_ref_is_an_input_error_with_no_findings(tmp_path: Path) -> None:
    repo = _prepared_git_repo(tmp_path)
    head = run_bounded(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()

    code, report = _run(repo, tmp_path / "report.json", base="deadbeefdeadbeefdeadbeefdeadbeefdeadbeef", head=head)

    assert code == 2
    assert report["status"] == "error"
    assert report["findings"] == []
    assert "does not resolve" in str(report["errors"])


def test_diverged_branches_use_merge_base_not_direct_ancestry(tmp_path: Path) -> None:
    repo = _prepared_git_repo(tmp_path)
    common = run_bounded(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()

    run_bounded(["git", "checkout", "-b", "branch-a"], cwd=repo)
    write_file(repo / "a.txt", "a\n")
    branch_a = commit_all(repo, "branch a change")

    run_bounded(["git", "checkout", common], cwd=repo)
    run_bounded(["git", "checkout", "-b", "branch-b"], cwd=repo)
    write_file(repo / "b.txt", "b\n")
    branch_b = commit_all(repo, "branch b change")

    code, report = _run(repo, tmp_path / "report.json", base=branch_a, head=branch_b)

    assert code == 0, report
    assert report["status"] == "ok"


def test_scope_includes_added_and_deleted_paths(tmp_path: Path) -> None:
    repo = _prepared_git_repo(tmp_path)
    engine = importlib.util.spec_from_file_location("build_knowledge_index", ENGINE)
    assert engine and engine.loader
    module = importlib.util.module_from_spec(engine)
    engine.loader.exec_module(module)
    base = run_bounded(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()

    write_file(repo / "added.txt", "added\n")
    head = commit_all(repo, "add path")
    assert module.resolve_routine_scope(repo, base, head) == {"added.txt"}

    write_file(repo / "deleted.txt", "deleted\n")
    before_delete = commit_all(repo, "add deletion candidate")
    (repo / "deleted.txt").unlink()
    after_delete = commit_all(repo, "delete path")
    assert module.resolve_routine_scope(repo, before_delete, after_delete) == {"deleted.txt"}


def test_scope_reports_both_sides_of_a_rename(tmp_path: Path) -> None:
    repo = _prepared_git_repo(tmp_path)
    spec = importlib.util.spec_from_file_location("build_knowledge_index", ENGINE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    write_file(repo / "before.txt", "line one\nline two\n")
    base = commit_all(repo, "add rename candidate")
    (repo / "before.txt").rename(repo / "after.txt")
    head = commit_all(repo, "rename path")

    assert module.resolve_routine_scope(repo, base, head) == {"before.txt", "after.txt"}


def test_scope_requires_explicit_base_and_head(tmp_path: Path) -> None:
    repo = _prepared_git_repo(tmp_path)
    report_path = tmp_path / "report.json"
    result = run_bounded(
        [
            sys.executable,
            str(ENGINE),
            "--repo-root",
            str(repo),
            "--detect-drift",
            "--report-output",
            str(report_path),
        ],
        cwd=ROOT,
    )

    report = parse_json_report(report_path)
    assert result.returncode == 2
    assert report["status"] == "error"
    assert report["findings"] == []
    assert "base" in str(report["errors"]).lower()


def test_full_inventory_does_not_require_git(tmp_path: Path) -> None:
    repo = _prepared_git_repo(tmp_path)
    report_path = tmp_path / "report.json"
    result = run_bounded(
        [
            sys.executable,
            str(ENGINE),
            "--repo-root",
            str(repo),
            "--detect-drift",
            "--full-inventory",
            "--report-output",
            str(report_path),
        ],
        cwd=ROOT,
    )

    report = parse_json_report(report_path)
    assert result.returncode == 0, report
    assert report["mode"] == "full-inventory"
    assert report["status"] == "ok"


def test_shallow_scope_without_merge_base_fails_closed(tmp_path: Path) -> None:
    source = _prepared_git_repo(tmp_path / "source")
    common = run_bounded(["git", "rev-parse", "HEAD"], cwd=source).stdout.strip()
    run_bounded(["git", "checkout", "-b", "branch-a"], cwd=source)
    write_file(source / "a.txt", "a\n")
    commit_all(source, "branch a")
    run_bounded(["git", "checkout", common], cwd=source)
    run_bounded(["git", "checkout", "-b", "branch-b"], cwd=source)
    write_file(source / "b.txt", "b\n")
    commit_all(source, "branch b")

    clone = tmp_path / "shallow"
    result = run_bounded(
        [
            "git",
            "clone",
            "--quiet",
            "--no-local",
            "--depth",
            "1",
            "--no-single-branch",
            str(source),
            str(clone),
        ],
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr
    report_path = tmp_path / "shallow.json"
    detection = run_bounded(
        [
            sys.executable,
            str(ENGINE),
            "--repo-root",
            str(clone),
            "--detect-drift",
            "--base",
            "origin/branch-a",
            "--head",
            "origin/branch-b",
            "--report-output",
            str(report_path),
        ],
        cwd=ROOT,
    )

    report = parse_json_report(report_path)
    assert detection.returncode == 2
    assert report["findings"] == []
    assert "merge base" in str(report["errors"]).lower()
