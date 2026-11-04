# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""An optional roadmap: absent means inert, present means structurally checked, repaired only inside its root."""

from __future__ import annotations

import hashlib
import json
import os
import runpy
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tests.consumer_skill_helpers import bash_path

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "roadmap-check.py"
WORK = ".devspark.work"
ROADMAP = f"{WORK}/roadmap"
DATE = "2026-11-01"
VERSION = "1.1.0"
TIMEOUT = 120
RELEASE_SCRIPTS = (
    "scripts/release-archive.py",
    "scripts/release-context.py",
    "scripts/roadmap-check.py",
)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True, timeout=TIMEOUT).stdout


def write(path: Path, content: str, newline: str = "\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline=newline)


def tree(base: Path, skip: tuple[str, ...] = (".git",)) -> dict[str, str]:
    found = {}
    for path in sorted(base.rglob("*")):
        relative = path.relative_to(base).as_posix()
        if path.is_file() and not any(relative == s or relative.startswith(f"{s}/") for s in skip):
            found[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


def commit(repo: Path, message: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)


def prospective(root: Path, identity: str, slug: str, status: str = "proposed", folder: str = "specs", body: str = "", **meta: object) -> Path:
    lines = [f"id: {identity}", f"title: {slug.replace('-', ' ').title()}", f"status: {status}"]
    lines += [f"{key}: {json.dumps(value)}" for key, value in meta.items()]
    path = root / folder / f"{identity}-{slug}.md"
    write(path, "---\n" + "\n".join(lines) + f"\n---\n\n# {identity}\n\n## Outcome\n\nA shippable outcome.\n{body}")
    return path


def new_repo(base: Path) -> Path:
    repo = base / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.name", "Test User")
    git(repo, "config", "user.email", "test@test.invalid")
    git(repo, "config", "core.autocrlf", "false")
    write(repo / "src" / "app.py", "VALUE = 1\n")
    write(repo / WORK / "devspark.json", '{"version": 1}\n')
    commit(repo, "baseline")
    return repo


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return new_repo(tmp_path)


def check(repo: Path, *args: str) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, str(CHECKER), *args, "--repo-root", str(repo), "--json"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode in (0, 1, 2), result.stderr
    return result.returncode, json.loads(result.stdout)


def codes(payload: dict, severity: str | None = None) -> set[str]:
    return {f["code"] for f in payload["FINDINGS"] if severity is None or f["severity"] == severity}


# Absent roadmap ------------------------------------------------------------------------------------


def test_absent_roadmap_is_inert_and_writes_nothing(repo: Path) -> None:
    before = tree(repo)

    for command in ("check", "repair"):
        code, payload = check(repo, command)
        assert code == 0
        assert payload["PRESENT"] is False and payload["OK"] is True
        assert payload["ITEMS"] == [] and payload["FINDINGS"] == [] and payload["UNBLOCKED"] == []
        assert payload["ROOT_SOURCE"] == "default" and payload["EXTERNAL"] is False
    _, repair = check(repo, "repair", "--apply")

    assert repair["REPAIRS"] == [] and repair["APPLIED"] is False
    assert tree(repo) == before
    assert not (repo / ROADMAP).exists()


# Location ------------------------------------------------------------------------------------------


def test_default_location_reports_items_unblocked_work_and_next_id(repo: Path) -> None:
    root = repo / ROADMAP
    write(root / "roadmap.md", "# Roadmap\n\n- [Base](specs/complete/ps-001-base.md)\n- [Next](specs/ps-002-next.md)\n")
    prospective(root, "ps-001", "base", "complete", folder="specs/complete", delivery=["main"])
    prospective(root, "ps-002", "next", "ready", depends_on=["ps-001"])
    prospective(root, "ps-003", "later", depends_on=["ps-002"])

    code, payload = check(repo, "check")

    assert code == 0 and payload["OK"] is True and payload["FINDINGS"] == []
    assert payload["PRESENT"] is True and payload["ROOT_SOURCE"] == "default"
    assert [item["id"] for item in payload["ITEMS"]] == ["ps-001", "ps-002", "ps-003"]
    assert payload["UNBLOCKED"] == ["ps-002"]
    assert payload["NEXT_ID"] == "ps-004"


def test_next_id_never_reuses_an_archived_id_recorded_in_roadmap_history(repo: Path) -> None:
    root = repo / ROADMAP
    write(root / "roadmap.md", "# Roadmap\n\n## Delivered\n\n- ps-007 Reports — delivered in 1.0.0\n")
    prospective(root, "ps-002", "next")

    _, payload = check(repo, "check")

    assert payload["NEXT_ID"] == "ps-008"


@pytest.mark.parametrize("relative", [True, False])
def test_configured_external_root_is_used_without_discovery(repo: Path, tmp_path: Path, relative: bool) -> None:
    planning = tmp_path / "planning" / "roadmap"
    prospective(planning, "ps-001", "external")
    configured = "../planning/roadmap" if relative else planning.as_posix()
    write(repo / WORK / "devspark.json", json.dumps({"version": 1, "roadmap": {"root": configured}}))

    code, payload = check(repo, "check")

    assert code == 0
    assert payload["ROOT_SOURCE"] == "config" and payload["EXTERNAL"] is True
    assert Path(payload["ROADMAP_ROOT"]) == planning.resolve()
    assert [item["id"] for item in payload["ITEMS"]] == ["ps-001"]


def test_explicit_root_argument_wins_over_configuration(repo: Path, tmp_path: Path) -> None:
    write(repo / WORK / "devspark.json", json.dumps({"roadmap": {"root": "planning/configured"}}))
    chosen = tmp_path / "chosen"
    prospective(chosen, "ps-001", "chosen")

    _, payload = check(repo, "check", "--root", str(chosen))

    assert payload["ROOT_SOURCE"] == "argument" and payload["EXTERNAL"] is True
    assert [item["id"] for item in payload["ITEMS"]] == ["ps-001"]


@pytest.mark.parametrize("root", [".", ".."])
def test_repository_root_or_above_is_refused(repo: Path, root: str) -> None:
    before = tree(repo)

    code, payload = check(repo, "repair", "--apply", "--root", root)

    assert code == 2 and payload["OK"] is False and "dedicated planning directory" in payload["ERROR"]
    assert tree(repo) == before


def test_non_string_configured_root_is_a_usage_error(repo: Path) -> None:
    write(repo / WORK / "devspark.json", json.dumps({"roadmap": {"root": 5}}))

    code, payload = check(repo, "check")

    assert code == 2 and "roadmap.root" in payload["ERROR"]


def test_unreadable_configuration_falls_back_to_the_default_root(repo: Path) -> None:
    write(repo / WORK / "devspark.json", "{ not json")

    code, payload = check(repo, "check")

    assert code == 0 and payload["ROOT_SOURCE"] == "default" and payload["PRESENT"] is False


# Structural findings --------------------------------------------------------------------------------


def test_structural_errors_are_reported(repo: Path) -> None:
    root = repo / ROADMAP
    prospective(root, "ps-001", "one", depends_on=["ps-099"])
    write(root / "specs" / "ps-001-copy.md", "---\nid: ps-001\ntitle: Copy\nstatus: proposed\n---\n")
    prospective(root, "ps-002", "two", depends_on=["ps-003"])
    prospective(root, "ps-003", "three", depends_on=["ps-002"])
    prospective(root, "ps-004", "four", depends_on=["ps-004"])
    prospective(root, "ps-005", "five", status="someday")
    write(root / "specs" / "ps-006-named.md", "---\nid: ps-060\ntitle: Wrong\nstatus: proposed\n---\n")
    write(root / "specs" / "ps-007-bad.md", "---\nid: [unclosed\n---\n")
    write(root / "specs" / "ps-008-none.md", "# no frontmatter\n")
    write(root / "specs" / "ps-009-missing.md", "---\nid: ps-009\nstatus: proposed\n---\n")
    write(root / "specs" / "item-x.md", "---\nid: item-x\ntitle: X\nstatus: proposed\n---\n")

    code, payload = check(repo, "check")

    assert code == 1 and payload["OK"] is False
    assert {
        "duplicate-id",
        "missing-dependency",
        "dependency-cycle",
        "invalid-status",
        "id-filename-mismatch",
        "malformed-metadata",
        "missing-field",
        "invalid-id",
    } <= codes(payload, "error")
    cycles = [f["message"] for f in payload["FINDINGS"] if f["code"] == "dependency-cycle"]
    assert any("ps-002 -> ps-003 -> ps-002" in m for m in cycles)
    assert any("ps-004 depends on itself" in m for m in cycles)


def test_warnings_alone_keep_the_roadmap_ok(repo: Path) -> None:
    root = repo / ROADMAP
    prospective(root, "ps-001", "dropped", "dropped", folder="specs/complete")
    prospective(root, "ps-002", "after", depends_on=["ps-001"], owner="someone")

    code, payload = check(repo, "check")

    assert code == 0 and payload["OK"] is True
    assert codes(payload) == {"unsupported-field", "depends-on-dropped"}
    assert codes(payload, "error") == set()


def test_tracking_disagreements_are_warnings_backed_by_git_evidence(repo: Path) -> None:
    head = git(repo, "rev-parse", "HEAD").strip()
    root = repo / ROADMAP
    prospective(root, "ps-001", "no-evidence", "complete", folder="specs/complete")
    prospective(root, "ps-002", "behind", "ready", delivery=["feature/behind"])
    prospective(root, "ps-003", "unknown", "complete", folder="specs/complete", delivery=["deadbeef1234567"])
    prospective(root, "ps-004", "real", "complete", folder="specs/complete", delivery=[head])

    code, payload = check(repo, "check")

    assert code == 0
    by_path = {(f["path"], f["code"]) for f in payload["FINDINGS"]}
    assert by_path == {
        ("specs/complete/ps-001-no-evidence.md", "complete-without-delivery"),
        ("specs/ps-002-behind.md", "status-behind-delivery"),
        ("specs/complete/ps-003-unknown.md", "unresolved-delivery-ref"),
    }
    assert all(f["severity"] == "warning" for f in payload["FINDINGS"])


# Repair ----------------------------------------------------------------------------------------------


def misplaced_roadmap(repo: Path) -> Path:
    root = repo / ROADMAP
    write(root / "roadmap.md", "# Roadmap\n\n- [Base](specs/ps-001-base.md)\n- [Next](specs/ps-002-next.md#outcome)\n")
    prospective(root, "ps-001", "base", "complete", delivery=["main"], body="\nFollowed by [next](ps-002-next.md).\n")
    path = prospective(root, "ps-002", "next", "ready", depends_on=["ps-001"])
    crlf = path.read_text(encoding="utf-8").replace("\n", "\r\n") + "Builds on [base](ps-001-base.md#outcome).\r\n"
    path.write_bytes(crlf.encode("utf-8"))
    return root


def test_repair_without_apply_plans_and_writes_nothing(repo: Path) -> None:
    misplaced_roadmap(repo)
    before = tree(repo)

    code, payload = check(repo, "repair")

    assert code == 1 and payload["APPLIED"] is False
    assert {"action": "move", "from": "specs/ps-001-base.md", "to": "specs/complete/ps-001-base.md"} in payload["REPAIRS"]
    assert {r["file"] for r in payload["REPAIRS"] if r["action"] == "relink"} == {
        "roadmap.md",
        "specs/complete/ps-001-base.md",
        "specs/ps-002-next.md",
    }
    assert tree(repo) == before


def test_repair_apply_moves_relinks_and_touches_nothing_outside_the_root(repo: Path) -> None:
    root = misplaced_roadmap(repo)
    write(repo / "src" / "app.py", "VALUE = 2  # uncommitted developer change\n")
    outside_before = tree(repo, skip=(".git", ROADMAP))
    status_before = git(repo, "status", "--porcelain", "--", "src")
    staged_before = git(repo, "diff", "--cached", "--name-only")
    original = (root / "specs" / "ps-001-base.md").read_text(encoding="utf-8")

    code, payload = check(repo, "repair", "--apply")

    assert code == 0 and payload["APPLIED"] is True and payload["OK"] is True and payload["FINDINGS"] == []
    moved = root / "specs" / "complete" / "ps-001-base.md"
    assert not (root / "specs" / "ps-001-base.md").exists()
    assert moved.read_text(encoding="utf-8") == original.replace("(ps-002-next.md)", "(../ps-002-next.md)")
    assert "(specs/complete/ps-001-base.md)" in (root / "roadmap.md").read_text(encoding="utf-8")
    assert "(specs/ps-002-next.md#outcome)" in (root / "roadmap.md").read_text(encoding="utf-8")
    raw = (root / "specs" / "ps-002-next.md").read_bytes().decode("utf-8")
    assert "(complete/ps-001-base.md#outcome)" in raw and "\r\n" in raw and "\n" not in raw.replace("\r\n", "")
    assert [item["status"] for item in payload["ITEMS"]] == ["complete", "ready"]
    assert tree(repo, skip=(".git", ROADMAP)) == outside_before
    assert git(repo, "status", "--porcelain", "--", "src") == status_before
    assert git(repo, "diff", "--cached", "--name-only") == staged_before

    code, again = check(repo, "repair", "--apply")
    assert code == 0 and again["REPAIRS"] == [] and again["APPLIED"] is False


def test_repair_refuses_to_overwrite_an_existing_destination(repo: Path) -> None:
    root = repo / ROADMAP
    prospective(root, "ps-001", "base", "complete", delivery=["main"])
    write(root / "specs" / "complete" / "ps-001-base.md", "# not a prospective spec\n")
    before = tree(repo)

    code, payload = check(repo, "repair", "--apply")

    assert code == 1 and payload["APPLIED"] is False
    assert payload["REFUSED"] and "already exists" in payload["REFUSED"][0]
    assert tree(repo) == before


def test_repair_never_changes_status_or_unrepairable_findings(repo: Path) -> None:
    root = repo / ROADMAP
    path = prospective(root, "ps-001", "base", "ready", depends_on=["ps-404"], delivery=["main"])
    before = tree(repo)

    _, payload = check(repo, "repair", "--apply")

    assert payload["REPAIRS"] == [] and payload["APPLIED"] is False
    assert {"missing-dependency", "status-behind-delivery"} <= codes(payload)
    assert tree(repo) == before and "status: ready" in path.read_text(encoding="utf-8")


# Write boundary --------------------------------------------------------------------------------------


def symlink_or_skip(link: Path, target: Path) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("this platform does not allow creating symbolic links")


@pytest.mark.parametrize(
    "root", [".git/roadmap", ".archive/roadmap", ".knowledge/roadmap", ".devspark/roadmap", f"{WORK}/specs/roadmap", f"{WORK}/audit/roadmap"]
)
def test_roots_inside_protected_areas_are_refused(repo: Path, root: str) -> None:
    before = tree(repo)

    code, payload = check(repo, "repair", "--apply", "--root", root)

    assert code == 2 and "never write" in payload["ERROR"]
    assert tree(repo) == before


def test_symlinked_items_are_unsafe_and_never_read_or_written(repo: Path, tmp_path: Path) -> None:
    root = repo / ROADMAP
    outside = tmp_path / "elsewhere" / "ps-009-escape.md"
    write(outside, "---\nid: ps-009\ntitle: Escape\nstatus: complete\n---\n\nOutside the root.\n")
    prospective(root, "ps-001", "base")
    symlink_or_skip(root / "specs" / "ps-009-escape.md", outside)
    before = outside.read_bytes()

    code, payload = check(repo, "repair", "--apply")

    assert code == 1 and "unsafe-path" in codes(payload, "error")
    assert [item["id"] for item in payload["ITEMS"]] == ["ps-001"]
    assert payload["REPAIRS"] == [] and payload["APPLIED"] is False
    assert outside.read_bytes() == before and (root / "specs" / "ps-009-escape.md").is_symlink()


def test_links_into_the_release_archive_are_history_not_broken_links(repo: Path) -> None:
    root = repo / ROADMAP
    write(root / "roadmap.md", "# Roadmap\n\n- [ps-001 Base](../../.archive/2026-01-01/roadmap/specs/complete/ps-001-base.md#outcome)\n")
    prospective(root, "ps-002", "next")

    code, payload = check(repo, "check")

    assert code == 0 and "broken-link" not in codes(payload)


@pytest.mark.parametrize("content", [None, "# unreadable status\n", "---\nstatus: complete\n---\n"])
def test_archive_links_without_live_status_never_unblock_a_dependency(repo: Path, content: str | None) -> None:
    root = repo / ROADMAP
    archived = repo / ".archive" / DATE / "roadmap/specs/complete/ps-001-base.md"
    target = Path(os.path.relpath(archived, root)).as_posix()
    write(root / "roadmap.md", f"# Roadmap\n\n- [Base]({target})\n")
    prospective(root, "ps-002", "next", "ready", depends_on=["ps-001"])
    if content is not None:
        write(archived, content)

    code, payload = check(repo, "check")

    assert code == 0 and payload["ARCHIVED"] == {"ps-001": "unknown"}
    assert payload["UNBLOCKED"] == [] and "unknown-dependency-status" in codes(payload)
    assert payload["NEXT_ID"] == "ps-003"
    assert check(repo, "locate", "ps-002")[1]["DEPENDENCIES"] == {"ps-001": "unknown"}


def test_live_delivered_status_is_used_without_opening_archived_files(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = repo / ROADMAP
    archived = repo / ".archive" / DATE / "roadmap/specs/complete/ps-001-base.md"
    target = Path(os.path.relpath(archived, root)).as_posix()
    write(archived, "---\nstatus: dropped\n---\n")
    write(root / "roadmap.md", f"# Roadmap\n\n## Delivered\n\n- [Base]({target}) — complete; archived with release {VERSION}\n")
    prospective(root, "ps-002", "next", "ready", depends_on=["ps-001"])
    engine = runpy.run_path(str(CHECKER))
    original_open = Path.open

    def no_archive_open(path: Path, *args, **kwargs):
        assert repo / ".archive" not in path.parents, f"checker opened archived content: {path}"
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", no_archive_open)
    payload = engine["Roadmap"](repo, root, "default").payload("check")

    assert payload["ARCHIVED"] == {"ps-001": "complete"} and payload["UNBLOCKED"] == ["ps-002"]
    assert payload["FINDINGS"] == []


def test_conflicting_live_archive_statuses_do_not_satisfy_dependencies(repo: Path) -> None:
    root = repo / ROADMAP
    target = f"../../.archive/{DATE}/roadmap/specs/complete/ps-001-base.md"
    write(root / "roadmap.md", "# Roadmap\n\n## Delivered\n\n" + "".join(
        f"- [Base]({target}) — {status}; archived with release {VERSION}\n" for status in ("complete", "dropped")
    ))
    prospective(root, "ps-002", "next", "ready", depends_on=["ps-001"])

    code, payload = check(repo, "check")

    assert code == 1 and payload["ARCHIVED"] == {"ps-001": "unknown"} and payload["UNBLOCKED"] == []
    assert "conflicting-archived-status" in codes(payload)


def test_roadmap_operations_never_touch_code_tests_knowledge_or_delivery_specs(repo: Path) -> None:
    write(repo / "tests" / "test_app.py", "def test_value():\n    assert True\n")
    write(repo / ".knowledge" / "decisions" / "adr-001.md", "# ADR 001\n")
    write(repo / WORK / "specs" / "001-feature" / "spec.md", "# Spec\n\n**Status**: Draft\n")
    commit(repo, "application baseline")
    misplaced_roadmap(repo)
    write(repo / "tests" / "test_app.py", "def test_value():\n    assert True  # uncommitted edit\n")
    outside_before = tree(repo, skip=(".git", ROADMAP))
    status_before = git(repo, "status", "--porcelain", "--", ":!" + ROADMAP)

    for args in (("check",), ("locate", "ps-002"), ("repair",), ("repair", "--apply"), ("check",)):
        check(repo, *args)

    assert tree(repo, skip=(".git", ROADMAP)) == outside_before
    assert git(repo, "status", "--porcelain", "--", ":!" + ROADMAP) == status_before
    assert git(repo, "diff", "--cached", "--name-only") == ""


# Locate ----------------------------------------------------------------------------------------------


def test_locate_reports_the_item_and_its_dependency_status(repo: Path) -> None:
    root = repo / ROADMAP
    prospective(root, "ps-001", "base", "complete", folder="specs/complete", delivery=["main"])
    prospective(root, "ps-002", "middle", "active", delivery=["feature/middle"])
    prospective(root, "ps-003", "next", "ready", depends_on=["ps-001", "ps-002"])

    for reference in ("ps-003", "PS-003", f"{ROADMAP}/specs/ps-003-next.md"):
        code, payload = check(repo, "locate", reference)
        assert code == 0
        assert payload["ITEM"]["path"] == "specs/ps-003-next.md"
        assert payload["DEPENDENCIES"] == {"ps-001": "complete", "ps-002": "active"}

    code, missing = check(repo, "locate", "ps-099")
    assert code == 1 and missing["ITEM"] is None and "not found" in missing["ERROR"]


# Wrappers --------------------------------------------------------------------------------------------


def test_powershell_wrapper_matches_the_engine(repo: Path) -> None:
    pwsh = shutil.which("pwsh")
    if not pwsh:
        pytest.skip("pwsh is not installed")
    prospective(repo / ROADMAP, "ps-001", "base")
    _, direct = check(repo, "check")

    declared = declared_check("ps")
    result = subprocess.run(
        [pwsh, "-NoProfile", "-File", *declared, "--repo-root", str(repo)],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == direct


def test_bash_wrapper_matches_the_engine(repo: Path) -> None:
    bash = bash_path()
    if not bash:
        pytest.skip("bash is not installed")
    probe = subprocess.run([bash, "-c", "command -v python3 && python3 -c 'import yaml'"], capture_output=True, text=True, timeout=TIMEOUT)
    if probe.returncode != 0:
        pytest.skip("this bash has no python3 with PyYAML")
    prospective(repo / ROADMAP, "ps-001", "base")
    _, direct = check(repo, "check")

    result = subprocess.run([bash, *declared_check("sh")], cwd=repo, capture_output=True, text=True, timeout=TIMEOUT)

    assert result.returncode == 0, result.stderr
    assert {k: v for k, v in json.loads(result.stdout).items() if k not in ("REPO_ROOT", "ROADMAP_ROOT")} == {
        k: v for k, v in direct.items() if k not in ("REPO_ROOT", "ROADMAP_ROOT")
    }


# Release archival ------------------------------------------------------------------------------------


@pytest.fixture
def release_repo(tmp_path: Path) -> Path:
    repo = new_repo(tmp_path)
    for relative in RELEASE_SCRIPTS:
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    commit(repo, "scripts")
    git(repo, "tag", "v1.0.0")
    return repo


def release(repo: Path, *args: str, version: str = VERSION, date: str = DATE) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, "scripts/release-archive.py", *args, "--version", version, "--date", date, "--json"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode in (0, 1, 2), result.stderr
    return result.returncode, json.loads(result.stdout)


def resolved_roadmap(repo: Path) -> Path:
    root = repo / ROADMAP
    write(root / "roadmap.md", "# Roadmap\n\n- [Next](specs/ps-002-next.md)\n\n## Delivered\n\n- ps-001 Base\n")
    prospective(root, "ps-001", "base", "complete", folder="specs/complete", delivery=["main"])
    prospective(root, "ps-002", "next", "ready", depends_on=["ps-001"])
    commit(repo, "roadmap")
    return root


def test_release_without_a_roadmap_reports_no_roadmap_work(release_repo: Path) -> None:
    _, payload = release(release_repo, "plan")

    assert payload["ROADMAP_COMPLETED"] == [] and payload["ROADMAP_INCLUDED"] is False
    assert payload["ROADMAP_ROOT"] == "" and payload["ROADMAP_ERROR"] == "" and payload["ROADMAP_RELINK"] == []


def test_release_reports_resolved_items_but_archives_them_only_when_asked(release_repo: Path) -> None:
    root = resolved_roadmap(release_repo)
    staged = f"{ROADMAP}/specs/complete/ps-001-base.md"

    _, plan = release(release_repo, "plan")
    code, applied = release(release_repo, "apply")

    assert plan["ROADMAP_COMPLETED"] == [staged]
    assert not any(item["path"].startswith(ROADMAP) for item in plan["NEEDS_DECISION"])
    assert staged not in {item["original"] for item in plan["TO_ARCHIVE"]}
    assert code == 0 and (root / "specs" / "complete" / "ps-001-base.md").is_file()
    assert staged not in {item["original"] for item in applied["TO_ARCHIVE"]}


def test_release_archives_resolved_items_when_included(release_repo: Path) -> None:
    root = resolved_roadmap(release_repo)
    staged = root / "specs" / "complete" / "ps-001-base.md"
    content = staged.read_bytes()

    _, plan = release(release_repo, "plan", "--include-roadmap")
    code, applied = release(release_repo, "apply", "--include-roadmap")
    validate_code, validated = release(release_repo, "validate")

    assert plan["ROADMAP_INCLUDED"] is True
    assert f"{ROADMAP}/specs/complete/ps-001-base.md" in {item["original"] for item in plan["TO_ARCHIVE"]}
    assert code == 0 and applied["OK"] is True
    archived = release_repo / ".archive" / DATE / "roadmap" / "specs" / "complete" / "ps-001-base.md"
    assert archived.read_bytes() == content and not staged.exists()
    assert (root / "roadmap.md").is_file() and (root / "specs" / "ps-002-next.md").is_file()
    assert validate_code == 0 and validated["OK"] is True


def test_release_leaves_an_unclean_staged_item_for_a_decision(release_repo: Path) -> None:
    root = resolved_roadmap(release_repo)
    prospective(root, "ps-003", "wip", "active", folder="specs/complete", delivery=["feature/wip"])
    write(root / "specs" / "complete" / "notes.md", "# not a prospective spec\n")
    commit(release_repo, "unclean staging")

    _, applied = release(release_repo, "apply", "--include-roadmap")

    undecided = {item["path"] for item in applied["NEEDS_DECISION"]}
    assert {f"{ROADMAP}/specs/complete/ps-003-wip.md", f"{ROADMAP}/specs/complete/notes.md"} <= undecided
    assert (root / "specs" / "complete" / "ps-003-wip.md").is_file()
    assert (root / "specs" / "complete" / "notes.md").is_file()


def test_release_never_archives_an_untracked_roadmap_item(release_repo: Path) -> None:
    root = resolved_roadmap(release_repo)
    prospective(root, "ps-004", "untracked", "dropped", folder="specs/complete")

    _, applied = release(release_repo, "apply", "--include-roadmap")

    assert f"{ROADMAP}/specs/complete/ps-004-untracked.md" in {item["path"] for item in applied["NEEDS_DECISION"]}
    assert (root / "specs" / "complete" / "ps-004-untracked.md").is_file()


ARCHIVED_BASE = f".archive/{DATE}/roadmap/specs/complete/ps-001-base.md"
NARRATIVE = (
    "# Roadmap\n\n## Direction\n\nKeep releases small and reversible.\n\n## Themes\n\n"
    "- [ps-001 Base](specs/complete/ps-001-base.md#outcome) laid the foundation.\n"
    "- [ps-002 Next](specs/ps-002-next.md) builds on it.\n- [Guide](https://example.com/guide)\n\n"
    "## Decisions\n\n- Base first, because everything depends on it.\n"
)


def linked_roadmap(repo: Path, root: Path) -> None:
    write(root / "roadmap.md", NARRATIVE)
    prospective(root, "ps-001", "base", "complete", folder="specs/complete", delivery=["main"])
    path = prospective(root, "ps-002", "next", "ready", depends_on=["ps-001"])
    crlf = path.read_text(encoding="utf-8").replace("\n", "\r\n") + "Builds on [base](complete/ps-001-base.md).\r\n"
    path.write_bytes(crlf.encode("utf-8"))
    commit(repo, "linked roadmap")


def test_release_archival_relinks_roadmap_links_and_preserves_everything_else(release_repo: Path) -> None:
    root = release_repo / ROADMAP
    linked_roadmap(release_repo, root)
    next_before = (root / "specs" / "ps-002-next.md").read_bytes().decode("utf-8")

    _, plan = release(release_repo, "plan", "--include-roadmap")
    code, applied = release(release_repo, "apply", "--include-roadmap")

    assert plan["ROADMAP_RELINK"] == [f"{ROADMAP}/roadmap.md", f"{ROADMAP}/specs/ps-002-next.md"]
    assert code == 0 and applied["OK"] is True
    assert applied["ROADMAP_RELINKED"] == plan["ROADMAP_RELINK"]
    overview = (root / "roadmap.md").read_text(encoding="utf-8")
    to_overview = os.path.relpath(release_repo / ARCHIVED_BASE, root).replace(os.sep, "/")
    expected = NARRATIVE.replace("(specs/complete/ps-001-base.md#outcome)", f"({to_overview}#outcome)")
    assert overview == expected + f"\n## Delivered\n\n- [ps-001-base]({to_overview}) — complete; archived with release {VERSION}\n"
    raw = (root / "specs" / "ps-002-next.md").read_bytes().decode("utf-8")
    to_next = os.path.relpath(release_repo / ARCHIVED_BASE, root / "specs").replace(os.sep, "/")
    assert raw == next_before.replace("(complete/ps-001-base.md)", f"({to_next})")
    assert (root / "specs" / to_next).resolve() == (release_repo / ARCHIVED_BASE).resolve()
    assert (release_repo / ARCHIVED_BASE).is_file()
    staged = git(release_repo, "diff", "--cached", "--name-only").split()
    assert {f"{ROADMAP}/roadmap.md", f"{ROADMAP}/specs/ps-002-next.md", ARCHIVED_BASE} <= set(staged)

    checked_code, checked = check(release_repo, "check")
    assert checked_code == 0 and checked["FINDINGS"] == []
    assert checked["ARCHIVED"] == {"ps-001": "complete"} and checked["UNBLOCKED"] == ["ps-002"] and checked["NEXT_ID"] == "ps-003"
    validate_code, validated = release(release_repo, "validate")
    assert validate_code == 0 and validated["STALE_REFERENCES"] == []

    after = tree(release_repo)
    rerun_code, rerun = release(release_repo, "apply", "--include-roadmap")
    assert rerun_code == 0 and rerun["ROADMAP_RELINKED"] == [] and tree(release_repo) == after


def test_release_records_an_unlinked_archived_item_so_its_id_stays_traceable(release_repo: Path) -> None:
    root = resolved_roadmap(release_repo)
    before = (root / "roadmap.md").read_text(encoding="utf-8")

    code, applied = release(release_repo, "apply", "--include-roadmap")

    assert code == 0 and applied["ROADMAP_RELINKED"] == [f"{ROADMAP}/roadmap.md"]
    to_archive = os.path.relpath(release_repo / ARCHIVED_BASE, root).replace(os.sep, "/")
    assert (root / "roadmap.md").read_text(encoding="utf-8") == before + f"- [ps-001-base]({to_archive}) — complete; archived with release {VERSION}\n"
    _, checked = check(release_repo, "check")
    assert checked["OK"] is True and checked["ARCHIVED"] == {"ps-001": "complete"} and checked["UNBLOCKED"] == ["ps-002"]
    _, located = check(release_repo, "locate", "ps-002")
    assert located["DEPENDENCIES"] == {"ps-001": "complete"}

    after = tree(release_repo)
    assert release(release_repo, "apply", "--include-roadmap")[1]["ROADMAP_RELINKED"] == [] and tree(release_repo) == after


def test_an_archived_dropped_item_is_recorded_as_dropped_and_never_satisfies_a_dependency(release_repo: Path) -> None:
    root = release_repo / ROADMAP
    write(root / "roadmap.md", "# Roadmap\n\n- [Next](specs/ps-002-next.md)\n")
    prospective(root, "ps-001", "base", "dropped", folder="specs/complete")
    prospective(root, "ps-002", "next", "proposed", depends_on=["ps-001"])
    commit(release_repo, "roadmap")

    code, applied = release(release_repo, "apply", "--include-roadmap")

    assert code == 0 and applied["OK"] is True
    to_archive = os.path.relpath(release_repo / ARCHIVED_BASE, root).replace(os.sep, "/")
    assert f"- [ps-001-base]({to_archive}) — dropped; archived with release {VERSION}\n" in (root / "roadmap.md").read_text(encoding="utf-8")
    _, checked = check(release_repo, "check")
    assert checked["ARCHIVED"] == {"ps-001": "dropped"} and checked["UNBLOCKED"] == []
    assert [f["code"] for f in checked["FINDINGS"]] == ["depends-on-dropped"]
    assert check(release_repo, "locate", "ps-002")[1]["DEPENDENCIES"] == {"ps-001": "dropped"}


def test_archived_dependency_survives_archival_of_its_only_referring_spec(release_repo: Path) -> None:
    root = resolved_roadmap(release_repo)
    overview = root / "roadmap.md"
    write(overview, "# Roadmap\n\n- [Next](specs/ps-002-next.md)\n")
    next_item = root / "specs/ps-002-next.md"
    write(next_item, next_item.read_text(encoding="utf-8") + "\nBuilds on [base](complete/ps-001-base.md).\n")
    commit(release_repo, "reference base only from next")

    code, _ = release(release_repo, "apply", "--include-roadmap")
    assert code == 0
    commit(release_repo, "first archive")
    git(release_repo, "tag", f"v{VERSION}")
    content = next_item.read_text(encoding="utf-8").replace("status: ready", "status: complete\ndelivery: [main]")
    write(next_item, content)
    assert check(release_repo, "repair", "--apply")[0] == 0
    prospective(root, "ps-003", "third", "ready", depends_on=["ps-001"])
    commit(release_repo, "finish next and plan third")

    code, _ = release(release_repo, "apply", "--include-roadmap", version="1.2.0", date="2026-11-02")
    checked_code, checked = check(release_repo, "check")

    assert code == 0 and checked_code == 0
    assert checked["ARCHIVED"] == {"ps-001": "complete", "ps-002": "complete"}
    assert checked["UNBLOCKED"] == ["ps-003"] and checked["FINDINGS"] == []
    assert check(release_repo, "locate", "ps-003")[1]["DEPENDENCIES"] == {"ps-001": "complete"}


@pytest.mark.parametrize("status", ["complete", "dropped"])
def test_release_resumes_live_status_records_from_the_journal(release_repo: Path, status: str) -> None:
    root = release_repo / ROADMAP
    original = "# Roadmap\n\n- [Base](specs/complete/ps-001-base.md)\n"
    write(root / "roadmap.md", original)
    prospective(root, "ps-001", "base", status, folder="specs/complete", delivery=["main"])
    prospective(root, "ps-002", "next", "ready", depends_on=["ps-001"])
    commit(release_repo, "resolved roadmap")
    assert release(release_repo, "apply", "--include-roadmap")[0] == 0
    manifest = release_repo / f".archive/{DATE}/release/archive-manifest-{VERSION}.json"
    assert json.loads(manifest.read_text(encoding="utf-8"))["items"][0]["roadmap_status"] == status

    # Recreate interruption after the move, before the overview rewrite.
    write(root / "roadmap.md", original)
    code, payload = release(release_repo, "apply", "--include-roadmap")
    _, checked = check(release_repo, "check")

    assert code == 0 and payload["ROADMAP_ERROR"] == ""
    assert checked["ARCHIVED"] == {"ps-001": status}
    assert checked["UNBLOCKED"] == (["ps-002"] if status == "complete" else [])
    assert (root / "roadmap.md").read_text(encoding="utf-8").count(f"— {status}; archived") == 1


def test_release_creates_a_live_status_record_when_the_overview_is_missing(release_repo: Path) -> None:
    root = release_repo / ROADMAP
    prospective(root, "ps-007", "base", "complete", folder="specs/complete", delivery=["main"])
    commit(release_repo, "resolved item without overview")

    code, _ = release(release_repo, "apply", "--include-roadmap")
    _, checked = check(release_repo, "check")

    assert code == 0 and checked["ARCHIVED"] == {"ps-007": "complete"} and checked["NEXT_ID"] == "ps-008"
    assert (root / "roadmap.md").is_file()


@pytest.mark.parametrize("configured", ["planning/roadmap", f"{WORK}/plans"])
def test_release_archives_a_configured_internal_roadmap(release_repo: Path, configured: str) -> None:
    write(release_repo / WORK / "devspark.json", json.dumps({"version": 1, "roadmap": {"root": configured}}))
    root = release_repo / configured
    linked_roadmap(release_repo, root)

    code, applied = release(release_repo, "apply", "--include-roadmap")

    assert code == 0 and applied["OK"] is True and applied["ROADMAP_ROOT"] == configured
    assert {item["archived"] for item in applied["TO_ARCHIVE"]} == {ARCHIVED_BASE}
    assert (release_repo / ARCHIVED_BASE).is_file() and not (root / "specs" / "complete" / "ps-001-base.md").exists()
    assert applied["ROADMAP_RELINKED"] == [f"{configured}/roadmap.md", f"{configured}/specs/ps-002-next.md"]
    assert not any(item["path"].startswith(configured) for item in applied["NEEDS_DECISION"])
    assert check(release_repo, "check")[1]["OK"] is True


def test_release_never_touches_an_external_roadmap(release_repo: Path, tmp_path: Path) -> None:
    external = tmp_path / "planning" / "roadmap"
    write(external / "roadmap.md", NARRATIVE)
    prospective(external, "ps-001", "base", "complete", folder="specs/complete", delivery=["main"])
    write(release_repo / WORK / "devspark.json", json.dumps({"version": 1, "roadmap": {"root": external.as_posix()}}))
    commit(release_repo, "external roadmap")
    before = tree(external)

    code, applied = release(release_repo, "apply", "--include-roadmap")

    assert code == 0 and applied["OK"] is True and applied["ROADMAP_EXTERNAL"] is True
    assert applied["ROADMAP_COMPLETED"] == [] and applied["ROADMAP_RELINKED"] == []
    assert "planning repository" in applied["ROADMAP_NOTICE"]
    assert tree(external) == before


def test_release_defers_roadmap_archival_over_uncommitted_roadmap_changes(release_repo: Path) -> None:
    root = release_repo / ROADMAP
    linked_roadmap(release_repo, root)
    edited = NARRATIVE + "\n- Draft thought, not yet committed.\n"
    write(root / "roadmap.md", edited)

    code, applied = release(release_repo, "apply", "--include-roadmap")

    assert code == 0 and applied["OK"] is True
    deferred = {item["path"]: item["reason"] for item in applied["NEEDS_DECISION"]}
    assert "uncommitted" in deferred[f"{ROADMAP}/specs/complete/ps-001-base.md"]
    assert (root / "specs" / "complete" / "ps-001-base.md").is_file()
    assert (root / "roadmap.md").read_text(encoding="utf-8") == edited
    assert f"{ROADMAP}/roadmap.md" not in git(release_repo, "diff", "--cached", "--name-only")


def test_release_never_moves_a_symlinked_roadmap_item(release_repo: Path, tmp_path: Path) -> None:
    root = resolved_roadmap(release_repo)
    outside = tmp_path / "elsewhere" / "ps-009-escape.md"
    write(outside, "---\nid: ps-009\ntitle: Escape\nstatus: complete\ndelivery: [main]\n---\n")
    symlink_or_skip(root / "specs" / "complete" / "ps-009-escape.md", outside)
    before = outside.read_bytes()

    code, applied = release(release_repo, "apply", "--include-roadmap")

    assert code == 0
    deferred = {item["path"]: item["reason"] for item in applied["NEEDS_DECISION"]}
    assert "symbolic link" in deferred[f"{ROADMAP}/specs/complete/ps-009-escape.md"]
    assert (root / "specs" / "complete" / "ps-009-escape.md").is_symlink() and outside.read_bytes() == before


@pytest.mark.parametrize("problem", ["invalid-root", "missing-checker"])
def test_an_unusable_roadmap_never_blocks_the_release(release_repo: Path, problem: str) -> None:
    root = resolved_roadmap(release_repo)
    write(release_repo / WORK / "audit" / "report.md", "# Audit\n")
    if problem == "invalid-root":
        write(release_repo / WORK / "devspark.json", json.dumps({"version": 1, "roadmap": {"root": "."}}))
    else:
        (release_repo / "scripts" / "roadmap-check.py").unlink()
    commit(release_repo, "release work")
    before = tree(root)

    code, applied = release(release_repo, "apply", "--include-roadmap")

    assert code == 0 and applied["OK"] is True and applied["ROADMAP_ERROR"].startswith("roadmap skipped")
    assert f"{WORK}/audit/report.md" in applied["MOVED"]
    assert tree(root) == before


# Prompt surface --------------------------------------------------------------------------------------


def command(name: str) -> str:
    return " ".join((ROOT / "templates" / "commands" / f"{name}.md").read_text(encoding="utf-8").split())


def declared_check(shell: str) -> list[str]:
    raw = (ROOT / "templates/commands/roadmap.md").read_text(encoding="utf-8")
    declaration = yaml.safe_load(raw.split("---", 2)[1])["scripts"][shell]
    assert "$ARGUMENTS" not in declaration, "natural-language requests must not be CLI arguments"
    args = shlex.split(declaration)
    args[0] = (ROOT / args[0].removeprefix(".devspark/")).as_posix()
    return args


def test_roadmap_command_plans_and_never_delivers() -> None:
    raw = (ROOT / "templates" / "commands" / "roadmap.md").read_text(encoding="utf-8")
    frontmatter = raw.split("---", 2)[1]
    text = command("roadmap")

    assert "roadmap-check.sh check --json" in frontmatter and "roadmap-check.ps1 check -Json" in frontmatter
    assert "$ARGUMENTS" not in frontmatter
    assert "Extract only `--root <path>`" in text and "Keep the natural-language request out of the CLI arguments" in text
    assert "send: true" not in frontmatter
    assert "Never invoke `/devspark-specify`" in text
    assert "Write only roadmap artifacts, only inside the resolved roadmap root." in text
    assert "Never search for a nearby planning directory" in text
    assert "--apply" in text and "only after the developer authorizes it" in text


def test_specify_reads_a_prospective_spec_only_when_named() -> None:
    text = command("specify")
    section = text.split("## Prospective Spec Context", 1)[1].split(" ## ", 1)[0]

    assert "only when the developer explicitly names a Prospective Spec" in section
    assert "never search for a roadmap" in section
    assert "roadmap-check.sh locate <id> --json" in section
    assert "It is context, not a gate." in section
    assert "never in shipped code, tests, or `.knowledge/`" in section


def test_release_offers_roadmap_archival_without_blocking() -> None:
    text = command("release")

    assert "--include-roadmap" in text
    assert "never archive them without that agreement" in text
    assert "do not edit these links by hand" in text and "ROADMAP_RELINKED" in text
    assert "never read, archived, or rewritten here" in text and "never blocks a release" in text


def test_configuration_schema_declares_the_optional_roadmap_root() -> None:
    schema = json.loads((ROOT / "templates" / "devspark-config.schema.json").read_text(encoding="utf-8"))

    assert schema["properties"]["roadmap"]["properties"]["root"]["type"] == "string"
    assert "roadmap" not in schema.get("required", [])
