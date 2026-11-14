# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""A formal release archives completed work from the active workspace, safely and repeatably."""

from __future__ import annotations

import hashlib
import json
import os
import runpy
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.consumer_skill_helpers import bash_path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = (
    "scripts/release-archive.py",
    "scripts/release-context.py",
    "scripts/bash/release-archive.sh",
    "scripts/powershell/release-archive.ps1",
)
DATE = "2026-11-01"
VERSION = "1.1.0"
WORK = ".devspark.work"
TIMEOUT = 120

COMPLETE_TASKS = "- [x] T001 Ship it code_ref: src/app.py | knowledge_ref: .knowledge/architecture/app.md\n"
LEGEND = "Legend: (code_ref: pending | knowledge_ref: pending) until each task closes.\n"


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True, timeout=TIMEOUT
    )
    return result.stdout


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree(base: Path) -> dict[str, str]:
    return {p.relative_to(base).as_posix(): digest(p) for p in sorted(base.rglob("*")) if p.is_file()}


def commit(repo: Path, message: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)


def complete_spec(repo: Path, name: str) -> None:
    base = repo / WORK / "specs" / name
    write(base / "spec.md", f"# {name}\n\n**Status**: Complete\n\n{LEGEND}")
    write(base / "plan.md", "# Plan\n")
    write(base / "tasks.md", COMPLETE_TASKS)
    write(base / "research.md", "# Research\n")
    write(base / "checklists" / "requirements.md", "- [x] CHK001 reviewed\n")
    write(base / "gates" / "verify.md", "---\nstatus: pass\n---\n")
    write(base / "contracts" / "shape.json", '{"shape": 1}\n')


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    for relative in SCRIPTS:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.name", "Test User")
    git(root, "config", "user.email", "test@test.invalid")
    git(root, "config", "core.autocrlf", "false")
    write(root / "src" / "app.py", "VALUE = 1\n")
    write(root / WORK / "devspark.json", '{"version": 1}\n')
    write(root / WORK / "README.md", "# Work\n")
    write(root / WORK / "commands" / "devspark.custom.md", "# Override\n")
    write(root / WORK / "intake" / "plan-a.md", "# Backlog\n")
    write(root / WORK / "specs" / ".gitkeep", "")
    commit(root, "baseline")
    git(root, "tag", "v1.0.0")

    complete_spec(root, "001-shipped")
    write(root / WORK / "quickfixes" / "QF-2026-001.md", "# QF\n\n**Status**: Complete\n\ncode_ref: src/app.py\nknowledge_ref: n/a - no durable behavior change\n")
    write(root / WORK / "pr-review" / "pr-1.md", "# Review\n")
    write(root / WORK / "specs" / "002-active" / "spec.md", "# Active\n\n**Status**: In Progress\n")
    write(root / WORK / "specs" / "002-active" / "tasks.md", "- [ ] T001 Pending code_ref: pending | knowledge_ref: pending\n")
    write(root / "docs" / "notes.md", "Older note.\n")
    commit(root, "release work")
    git(root, "branch", "002-active")
    return root


def engine(repo: Path, *args: str, check: bool = True) -> tuple[int, dict[str, object]]:
    result = subprocess.run(
        [sys.executable, "scripts/release-archive.py", *args, "--json"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    if check:
        assert result.returncode in (0, 1, 2), result.stderr
    return result.returncode, json.loads(result.stdout)


def apply(repo: Path) -> tuple[int, dict[str, object]]:
    return engine(repo, "apply", "--version", VERSION, "--date", DATE)


def archived_root(repo: Path) -> Path:
    return repo / ".archive" / DATE


def test_completed_spec_moves_with_every_associated_artifact(repo: Path) -> None:
    before = tree(repo / WORK / "specs" / "001-shipped")
    assert {"spec.md", "plan.md", "tasks.md", "research.md", "checklists/requirements.md", "gates/verify.md", "contracts/shape.json"} <= set(before)

    code, payload = apply(repo)

    assert code == 0 and payload["OK"] is True
    assert not (repo / WORK / "specs" / "001-shipped").exists()
    assert tree(archived_root(repo) / "specs" / "001-shipped") == before
    renames = [line for line in git(repo, "diff", "--cached", "-M", "--name-status").splitlines() if line.startswith("R100")]
    assert len(renames) >= len(before)

    manifest = json.loads((archived_root(repo) / "release" / f"archive-manifest-{VERSION}.json").read_text(encoding="utf-8"))
    spec = next(item for item in manifest["items"] if item["original"].endswith("001-shipped"))
    assert spec["archived"] == f".archive/{DATE}/specs/001-shipped"
    assert {entry["path"]: entry["sha256"] for entry in spec["files"]} == before


def test_completed_conditional_work_note_archives_with_its_bundle(repo: Path) -> None:
    work = repo / WORK / "specs" / "003-work-complaint"
    write(work / "work.md", "# Work: Complaint behavior\n\n**Status**: Complete\n\n## Intended Outcome\nThe requested behavior works.\n")
    commit(repo, "complete bundle-free work")

    _, plan = engine(repo, "plan", "--version", VERSION, "--date", DATE)
    assert f"{WORK}/specs/003-work-complaint" in {item["original"] for item in plan["TO_ARCHIVE"]}

    code, payload = apply(repo)

    assert code == 0 and payload["OK"] is True
    assert not work.exists()
    assert (archived_root(repo) / "specs" / "003-work-complaint" / "work.md").is_file()


def test_legend_prose_does_not_block_a_completed_spec(repo: Path) -> None:
    _, payload = engine(repo, "plan", "--version", VERSION, "--date", DATE)

    originals = [item["original"] for item in payload["TO_ARCHIVE"]]
    assert f"{WORK}/specs/001-shipped" in originals


def test_passing_closeout_gate_counts_as_completion_despite_stale_status(repo: Path) -> None:
    base = repo / WORK / "specs" / "005-closed"
    write(base / "spec.md", "# Closed\n\n**Status**: Draft\n")
    write(base / "tasks.md", COMPLETE_TASKS)
    write(base / "gates" / "closeout.md", "---\nstatus: pass\ndecision: complete\n---\n")
    write(repo / WORK / "specs" / "006-failed" / "spec.md", "# Failed\n\n**Status**: Draft\n")
    write(repo / WORK / "specs" / "006-failed" / "gates" / "closeout.md", "---\nstatus: fail\ndecision: complete\n---\n")
    commit(repo, "closed spec with stale status")

    _, payload = engine(repo, "plan", "--version", VERSION, "--date", DATE)

    originals = [item["original"] for item in payload["TO_ARCHIVE"]]
    assert f"{WORK}/specs/005-closed" in originals
    assert f"{WORK}/specs/006-failed" not in originals


def test_non_spec_work_products_are_archived_when_eligible(repo: Path) -> None:
    code, payload = apply(repo)

    assert code == 0
    assert (archived_root(repo) / "quickfixes" / "QF-2026-001.md").is_file()
    assert (archived_root(repo) / "pr-review" / "pr-1.md").is_file()
    assert not (repo / WORK / "quickfixes" / "QF-2026-001.md").exists()
    assert not (repo / WORK / "pr-review" / "pr-1.md").exists()


def test_active_spec_and_operational_files_stay(repo: Path) -> None:
    active = tree(repo / WORK / "specs" / "002-active")
    operational = {
        path: digest(repo / path)
        for path in (
            f"{WORK}/devspark.json",
            f"{WORK}/README.md",
            f"{WORK}/commands/devspark.custom.md",
            f"{WORK}/intake/plan-a.md",
            f"{WORK}/specs/.gitkeep",
            "src/app.py",
            "docs/notes.md",
        )
    }

    code, payload = apply(repo)

    assert code == 0
    assert tree(repo / WORK / "specs" / "002-active") == active
    assert {path: digest(repo / path) for path in operational} == operational
    assert [item["path"] for item in payload["IN_FLIGHT"]] == [f"{WORK}/specs/002-active"]
    assert not any("002-active" in str(item) for item in payload["MOVED"])
    assert not (archived_root(repo) / "specs" / "002-active").exists()


def test_applying_twice_is_idempotent(repo: Path) -> None:
    apply(repo)
    first = tree(repo / ".archive")
    staged = git(repo, "status", "--porcelain")

    code, payload = apply(repo)

    assert code == 0 and payload["OK"] is True
    assert payload["MOVED"] == []
    assert tree(repo / ".archive") == first
    assert git(repo, "status", "--porcelain") == staged
    assert sorted(payload["ALREADY_ARCHIVED"]) == sorted(
        [f"{WORK}/pr-review/pr-1.md", f"{WORK}/quickfixes/QF-2026-001.md", f"{WORK}/specs/001-shipped"]
    )


def test_existing_archive_content_is_never_overwritten(repo: Path) -> None:
    occupied = archived_root(repo) / "specs" / "001-shipped" / "spec.md"
    write(occupied, "Earlier evidence that must survive.\n")
    source = tree(repo / WORK / "specs" / "001-shipped")

    code, payload = apply(repo)

    assert code == 2 and payload["OK"] is False
    assert payload["COLLISIONS"] and payload["COLLISIONS"][0]["archived"].endswith("001-shipped/spec.md")
    assert occupied.read_text(encoding="utf-8") == "Earlier evidence that must survive.\n"
    assert tree(repo / WORK / "specs" / "001-shipped") == source
    assert (repo / WORK / "quickfixes" / "QF-2026-001.md").is_file()
    assert not (archived_root(repo) / "release").exists()


def test_interrupted_move_resumes_from_the_journal(repo: Path) -> None:
    code, _ = apply(repo)
    assert code == 0
    archived = archived_root(repo) / "specs" / "001-shipped"
    original = repo / WORK / "specs" / "001-shipped"
    # Simulate a crash after the journal was written but before two files moved.
    for name in ("plan.md", "gates/verify.md"):
        target = original / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(archived / name), str(target))
    expected = tree(archived) | {"plan.md": digest(original / "plan.md"), "gates/verify.md": digest(original / "gates" / "verify.md")}

    _, plan = engine(repo, "plan", "--version", VERSION)
    assert [item["original"] for item in plan["RESUMING"]] == [f"{WORK}/specs/001-shipped"]

    code, payload = engine(repo, "apply", "--version", VERSION)

    assert code == 0 and payload["OK"] is True
    assert not original.exists()
    assert tree(archived) == expected


def test_journaled_file_edited_after_the_crash_is_a_collision(repo: Path) -> None:
    apply(repo)
    original = repo / WORK / "specs" / "001-shipped"
    original.mkdir(parents=True, exist_ok=True)
    shutil.move(str(archived_root(repo) / "specs" / "001-shipped" / "plan.md"), str(original / "plan.md"))
    write(original / "plan.md", "# Edited after the journal\n")

    code, payload = engine(repo, "apply", "--version", VERSION)

    assert code == 2
    assert "changed after being journaled" in payload["COLLISIONS"][0]["reason"]
    assert (original / "plan.md").read_text(encoding="utf-8") == "# Edited after the journal\n"


def test_missing_completion_evidence_is_reported_not_archived(repo: Path) -> None:
    write(repo / WORK / "specs" / "003-orphan" / "spec.md", "# Orphan\n\n**Status**: Draft\n")
    write(repo / WORK / "explain" / "topic.md", "# Saved explanation\n")
    commit(repo, "ambiguous work")

    code, payload = apply(repo)

    assert code == 0
    decisions = {item["path"]: item for item in payload["NEEDS_DECISION"]}
    assert "orphaned" in decisions[f"{WORK}/specs/003-orphan"]["reason"]
    assert decisions[f"{WORK}/specs/003-orphan"]["action"]
    assert "uncategorized" in decisions[f"{WORK}/explain"]["reason"]
    for name in ("specs/003-orphan/spec.md", "explain/topic.md"):
        assert (repo / WORK / name).is_file()


def test_legacy_unpopulated_linkage_does_not_block_archiving(repo: Path) -> None:
    write(repo / WORK / "specs" / "004-legacy" / "spec.md", "# Legacy\n\n**Status**: Complete\n")
    write(repo / WORK / "specs" / "004-legacy" / "tasks.md", "- [x] T001 Done code_ref: pending | knowledge_ref: pending\n")
    commit(repo, "legacy linkage")

    code, _ = apply(repo)

    assert code == 0
    assert (archived_root(repo) / "specs" / "004-legacy" / "spec.md").is_file()
    assert not (repo / WORK / "specs" / "004-legacy").exists()


def test_untracked_files_in_a_completed_spec_need_a_decision(repo: Path) -> None:
    write(repo / WORK / "specs" / "001-shipped" / "scratch.md", "Never committed.\n")

    code, payload = apply(repo)

    assert code == 0
    decision = next(item for item in payload["NEEDS_DECISION"] if item["path"].endswith("001-shipped"))
    assert "not tracked by Git" in decision["reason"]
    assert (repo / WORK / "specs" / "001-shipped" / "spec.md").is_file()
    assert not (archived_root(repo) / "specs" / "001-shipped").exists()


def test_dry_run_changes_nothing(repo: Path) -> None:
    snapshot = (tree(repo / WORK), git(repo, "status", "--porcelain"))

    code, payload = engine(repo, "apply", "--version", VERSION, "--date", DATE, "--dry-run")

    assert code == 0 and payload["TO_ARCHIVE"]
    assert (tree(repo / WORK), git(repo, "status", "--porcelain")) == snapshot
    assert not (repo / ".archive").exists()


def test_version_preconditions_refuse_unsafe_releases(repo: Path) -> None:
    code, payload = engine(repo, "apply", "--version", "1.0.0")
    assert code == 2 and "already exists" in payload["ERROR"]

    code, payload = engine(repo, "apply", "--version", "0.9.0")
    assert code == 2 and "not newer" in payload["ERROR"]

    code, payload = engine(repo, "apply", "--version", "next")
    assert code == 2 and "semantic version" in payload["ERROR"]

    code, payload = engine(repo, "apply")
    assert code == 2 and "--version" in payload["ERROR"]
    assert (repo / WORK / "specs" / "001-shipped").is_dir()


def test_validate_detects_tampered_archive(repo: Path) -> None:
    apply(repo)
    code, payload = engine(repo, "validate", "--version", VERSION)
    assert code == 0 and payload["OK"] is True and payload["ARCHIVED"] >= 8

    write(archived_root(repo) / "specs" / "001-shipped" / "plan.md", "# Rewritten history\n")
    code, payload = engine(repo, "validate", "--version", VERSION)

    assert code == 1
    assert any("differs from the journal" in problem for problem in payload["PROBLEMS"])


def test_stale_references_to_moved_paths_are_reported(repo: Path) -> None:
    write(repo / "docs" / "notes.md", f"See {WORK}/specs/001-shipped/plan.md for details.\n")
    commit(repo, "reference a spec")

    _, payload = engine(repo, "plan", "--version", VERSION, "--date", DATE)

    assert payload["STALE_REFERENCES"] == [
        {"file": "docs/notes.md", "line": 1, "target": f"{WORK}/specs/001-shipped"}
    ]


def test_next_development_cycle_starts_cleanly_after_archival(repo: Path) -> None:
    apply(repo)
    commit(repo, "release archive")

    write(repo / WORK / "specs" / "003-next" / "spec.md", "# Next\n\n**Status**: Draft\n")
    git(repo, "branch", "003-next")
    commit(repo, "start next cycle")
    git(repo, "tag", f"v{VERSION}")

    code, payload = engine(repo, "plan", "--version", "1.2.0", "--date", "2026-12-01")

    assert code == 0 and payload["TO_ARCHIVE"] == []
    assert sorted(item["path"] for item in payload["IN_FLIGHT"]) == [f"{WORK}/specs/002-active", f"{WORK}/specs/003-next"]
    assert payload["NEEDS_DECISION"] == []
    assert (repo / WORK / "devspark.json").is_file() and (repo / WORK / "intake" / "plan-a.md").is_file()
    assert sorted(path.name for path in (repo / WORK / "specs").iterdir()) == [".gitkeep", "002-active", "003-next"]


# Archive location ------------------------------------------------------------------------------------


@pytest.fixture
def store(tmp_path: Path) -> Path:
    folder = tmp_path / "store"
    folder.mkdir()
    return folder


def external(repo: Path, store: Path, command: str = "apply", *extra: str) -> tuple[int, dict[str, object]]:
    return engine(repo, command, "--version", VERSION, "--date", DATE, "--archive-root", str(store), *extra)


def test_the_archive_defaults_to_the_repository(repo: Path) -> None:
    _, payload = engine(repo, "plan", "--version", VERSION, "--date", DATE)

    assert payload["ARCHIVE_ROOT"] == f".archive/{DATE}"
    assert payload["ARCHIVE_EXTERNAL"] is False and payload["ARCHIVE_SOURCE"] == "default"
    assert payload["ARCHIVE_NOTICE"] == ""


def test_an_external_archive_receives_the_move(repo: Path, store: Path) -> None:
    before = tree(repo / WORK / "specs" / "001-shipped")
    dated = store.resolve() / DATE

    _, plan = external(repo, store, "plan")
    code, payload = external(repo, store)

    planned = next(item for item in plan["TO_ARCHIVE"] if item["original"].endswith("001-shipped"))
    assert planned["archived"] == f"{dated.as_posix()}/specs/001-shipped"
    assert code == 0 and payload["OK"] is True
    assert payload["ARCHIVE_EXTERNAL"] is True and payload["ARCHIVE_SOURCE"] == "argument"
    assert payload["ARCHIVE_ROOT"] == dated.as_posix() and "outside this repository" in payload["ARCHIVE_NOTICE"]
    assert tree(store / DATE / "specs" / "001-shipped") == before
    assert not (repo / WORK / "specs" / "001-shipped").exists() and not (repo / ".archive").exists()
    assert not list(store.rglob("*.partial"))

    manifest = json.loads((store / DATE / "release" / f"archive-manifest-{VERSION}.json").read_text(encoding="utf-8"))
    spec = next(item for item in manifest["items"] if item["original"].endswith("001-shipped"))
    assert manifest["location"] == "external" and manifest["archive_root"] == DATE
    assert spec["archived"] == f"{DATE}/specs/001-shipped"
    staged = git(repo, "diff", "--cached", "--name-status").splitlines()
    assert len([line for line in staged if line.startswith("D")]) >= len(before)
    assert not [line for line in staged if line.startswith(("A", "R"))]


def test_the_external_journal_stays_valid_when_the_archive_is_cloned_elsewhere(repo: Path, store: Path, tmp_path: Path) -> None:
    external(repo, store)
    code, validated = external(repo, store, "validate")
    assert code == 0 and validated["OK"] is True and validated["ARCHIVED"] >= 8

    cloned = tmp_path / "store-clone"
    store.rename(cloned)
    code, validated = external(repo, cloned, "validate")
    assert code == 0 and validated["OK"] is True

    write(cloned / DATE / "specs" / "001-shipped" / "plan.md", "# Rewritten history\n")
    code, validated = external(repo, cloned, "validate")
    assert code == 1 and any("differs from the journal" in problem for problem in validated["PROBLEMS"])


def test_the_archive_root_comes_from_devspark_json_and_the_argument_overrides_it(repo: Path, store: Path, tmp_path: Path) -> None:
    other = tmp_path / "other"
    other.mkdir()
    write(repo / WORK / "devspark.json", '{"version": 1, "archive": {"root": "../store"}}\n')
    commit(repo, "configure the archive")

    _, configured = engine(repo, "plan", "--version", VERSION, "--date", DATE)
    _, overridden = external(repo, other, "plan")

    assert (configured["ARCHIVE_SOURCE"], configured["ARCHIVE_ROOT"]) == ("config", (store.resolve() / DATE).as_posix())
    assert (overridden["ARCHIVE_SOURCE"], overridden["ARCHIVE_ROOT"]) == ("argument", (other.resolve() / DATE).as_posix())


def test_a_folder_inside_the_repository_archive_is_allowed(repo: Path) -> None:
    code, payload = engine(repo, "apply", "--version", VERSION, "--date", DATE, "--archive-root", ".archive/team-a")

    dated = repo / ".archive" / "team-a" / DATE
    assert code == 0 and payload["OK"] is True and payload["ARCHIVE_EXTERNAL"] is False
    assert payload["ARCHIVE_ROOT"] == f".archive/team-a/{DATE}"
    assert (dated / "specs" / "001-shipped" / "spec.md").is_file()
    manifest = json.loads((dated / "release" / f"archive-manifest-{VERSION}.json").read_text(encoding="utf-8"))
    spec = next(item for item in manifest["items"] if item["original"].endswith("001-shipped"))
    assert spec["archived"] == f".archive/team-a/{DATE}/specs/001-shipped"


@pytest.mark.parametrize(
    ("root", "reason"),
    [
        (".", "repository root or above"),
        ("..", "repository root or above"),
        (".devspark.work/archive", "outside .archive/"),
        (".devspark/archive", "outside .archive/"),
        (".knowledge/archive", "outside .archive/"),
        (".git/archive", "outside .archive/"),
        ("docs/archive", "outside .archive/"),
        ("../nowhere", "not an existing folder"),
        ("../file.txt", "not an existing folder"),
    ],
)
def test_unsafe_archive_roots_are_refused_before_anything_moves(repo: Path, tmp_path: Path, root: str, reason: str) -> None:
    write(tmp_path / "file.txt", "not a folder\n")
    source = tree(repo / WORK / "specs" / "001-shipped")

    code, payload = engine(repo, "apply", "--version", VERSION, "--date", DATE, "--archive-root", root)

    assert code == 2 and payload["OK"] is False and reason in payload["ERROR"]
    assert tree(repo / WORK / "specs" / "001-shipped") == source
    assert not (repo / ".archive").exists() and not (tmp_path / "nowhere").exists()


@pytest.mark.parametrize("config", ['{"archive": {"root": 5}}', '{"archive": {"root": "  "}}', '{"archive": "../store"}'])
def test_a_malformed_archive_setting_is_refused(repo: Path, config: str) -> None:
    write(repo / WORK / "devspark.json", config)
    commit(repo, "malformed archive setting")

    code, payload = engine(repo, "plan", "--version", VERSION, "--date", DATE)

    assert code == 2 and "'archive" in payload["ERROR"]


@pytest.mark.parametrize("config", ["{", '{"archive": {}}', '{"version": 1}'])
def test_an_unset_or_unreadable_archive_setting_uses_the_default(repo: Path, config: str) -> None:
    write(repo / WORK / "devspark.json", config)
    commit(repo, "no usable archive setting")

    code, payload = engine(repo, "plan", "--version", VERSION, "--date", DATE)

    assert code == 0 and payload["ARCHIVE_SOURCE"] == "default" and payload["ARCHIVE_ROOT"] == f".archive/{DATE}"


def test_an_occupied_external_destination_is_a_collision(repo: Path, store: Path) -> None:
    occupied = store / DATE / "specs" / "001-shipped" / "spec.md"
    write(occupied, "Earlier evidence that must survive.\n")
    source = tree(repo / WORK / "specs" / "001-shipped")

    code, payload = external(repo, store)

    assert code == 2 and payload["OK"] is False
    assert payload["COLLISIONS"][0]["archived"] == occupied.resolve().as_posix()
    assert occupied.read_text(encoding="utf-8") == "Earlier evidence that must survive.\n"
    assert tree(repo / WORK / "specs" / "001-shipped") == source
    assert not (store / DATE / "release").exists()


def test_an_external_move_interrupted_after_the_copy_resumes(repo: Path, store: Path) -> None:
    external(repo, store)
    archived = store / DATE / "specs" / "001-shipped"
    original = repo / WORK / "specs" / "001-shipped"
    expected = tree(archived)
    # One file crashed after its copy was published but before the original went; another died mid-copy.
    for name in ("plan.md", "gates/verify.md"):
        target = original / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(archived / name, target)
    (archived / "gates" / "verify.md").unlink()
    write(archived / "gates" / "verify.md.partial", "half a file")

    _, plan = engine(repo, "plan", "--version", VERSION, "--archive-root", str(store))
    assert [item["original"] for item in plan["RESUMING"]] == [f"{WORK}/specs/001-shipped"]

    code, payload = engine(repo, "apply", "--version", VERSION, "--archive-root", str(store))

    assert code == 0 and payload["OK"] is True
    assert not original.exists()
    assert tree(archived) == expected


def test_an_unwritable_external_archive_stops_before_anything_moves(repo: Path, store: Path) -> None:
    write(store / DATE, "a file where the dated folder belongs\n")
    source = tree(repo / WORK / "specs" / "001-shipped")

    code, payload = external(repo, store)

    assert code == 2 and "nothing was moved" in payload["ERROR"]
    assert tree(repo / WORK / "specs" / "001-shipped") == source
    assert (repo / WORK / "quickfixes" / "QF-2026-001.md").is_file()


def test_a_copy_that_does_not_match_the_plan_leaves_the_original(tmp_path: Path) -> None:
    module = runpy.run_path(str(ROOT / "scripts" / "release-archive.py"), run_name="release_archive_unit")
    source = tmp_path / "source.md"
    write(source, "content\n")
    destination = tmp_path / "store" / DATE / "source.md"

    with pytest.raises(module["ArchiveError"], match="no longer matches the plan"):
        module["relocate"](source, destination, "0" * 64, True)

    assert source.read_text(encoding="utf-8") == "content\n"
    assert not destination.exists() and not list(tmp_path.rglob("*.partial"))


def test_uncommitted_changes_defer_a_bundle_bound_for_an_external_archive(repo: Path, store: Path) -> None:
    write(repo / WORK / "specs" / "001-shipped" / "plan.md", "# Edited, not committed\n")

    code, payload = external(repo, store)

    assert code == 0
    decision = next(item for item in payload["NEEDS_DECISION"] if item["path"].endswith("001-shipped"))
    assert "uncommitted" in decision["reason"] and decision["action"]
    assert (repo / WORK / "specs" / "001-shipped" / "plan.md").read_text(encoding="utf-8") == "# Edited, not committed\n"
    assert not (store / DATE / "specs" / "001-shipped").exists()
    assert (store / DATE / "quickfixes" / "QF-2026-001.md").is_file()

    _, inside = engine(repo, "plan", "--version", VERSION, "--date", DATE)
    assert f"{WORK}/specs/001-shipped" in {item["original"] for item in inside["TO_ARCHIVE"]}


def test_a_dry_run_with_an_external_archive_writes_nothing(repo: Path, store: Path) -> None:
    snapshot = (tree(repo / WORK), git(repo, "status", "--porcelain"))

    code, payload = external(repo, store, "apply", "--dry-run")

    assert code == 0 and payload["TO_ARCHIVE"]
    assert (tree(repo / WORK), git(repo, "status", "--porcelain")) == snapshot
    assert list(store.iterdir()) == []


def test_powershell_wrapper_matches_the_engine(repo: Path, store: Path) -> None:
    pwsh = shutil.which("pwsh")
    if not pwsh:
        pytest.skip("pwsh is not installed")
    _, direct = engine(repo, "plan", "--version", VERSION, "--date", DATE, "--archive-root", str(store))
    assert direct["ARCHIVE_EXTERNAL"] is True

    result = subprocess.run(
        [pwsh, "-NoProfile", "-File", "scripts/powershell/release-archive.ps1", "plan", "--version", VERSION, "--date", DATE, "--archive-root", str(store), "-Json"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == direct


def test_bash_wrapper_matches_the_engine(repo: Path, store: Path) -> None:
    bash = bash_path()
    if not bash:
        pytest.skip("bash is not installed")
    probe = subprocess.run([bash, "-c", "command -v python3"], capture_output=True, text=True, timeout=TIMEOUT)
    if probe.returncode != 0:
        pytest.skip("this bash has no python3")
    _, direct = engine(repo, "plan", "--version", VERSION, "--date", DATE, "--archive-root", str(store))
    assert direct["ARCHIVE_EXTERNAL"] is True

    result = subprocess.run(
        [bash, "scripts/bash/release-archive.sh", "plan", "--version", VERSION, "--date", DATE, "--archive-root", str(store), "--json"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == direct
