# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Session-scoped fixtures that build release packages and the install index once per run."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import textwrap
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from tests.consumer_skill_helpers import ROOT, bash_path, copy_generation_repo, run_generator, tree_bytes

BUILD_AGENTS = ("copilot", "claude", "gemini")
BUILD_TIMEOUT = 600
INDEX_TIMEOUT = 120


@dataclass
class PackageBuild:
    work: Path
    zips: dict[str, Path]
    dirs: dict[str, Path]


_SHARED_SCOPES = {"session", "package", "module"}


@pytest.fixture(scope="session", autouse=True)
def disable_git_auto_maintenance() -> Iterator[None]:
    """Keep cached Git fixture repositories stable while they are being copied."""
    with pytest.MonkeyPatch.context() as patch:
        count = int(os.environ.get("GIT_CONFIG_COUNT", "0"))
        for index, key in enumerate(("maintenance.auto", "gc.auto"), start=count):
            patch.setenv(f"GIT_CONFIG_KEY_{index}", key)
            patch.setenv(f"GIT_CONFIG_VALUE_{index}", "0")
        patch.setenv("GIT_CONFIG_COUNT", str(count + 2))
        yield


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Keep every test of an expensive shared fixture on one xdist worker.

    Under ``--dist loadgroup`` each worker builds its own copy of a session or module
    fixture, so a fixture such as ``package_build`` would otherwise be rebuilt per worker.
    Tests that use no shared repository fixture stay ungrouped and load-balance freely.
    """
    for item in items:
        info = getattr(item, "_fixtureinfo", None)
        if info is None or item.get_closest_marker("xdist_group"):
            continue
        for name in info.names_closure:
            defs = info.name2fixturedefs.get(name)
            if not defs:
                continue
            fixturedef = defs[-1]
            module = getattr(fixturedef.func, "__module__", "") or ""
            if fixturedef.scope in _SHARED_SCOPES and module.startswith("tests"):
                if module == "tests.conftest" and name in {"package_build", "install_index"}:
                    group = "tests.conftest.distribution_artifacts"
                elif module == "tests.conftest":
                    group = f"{module}.{name}"
                else:
                    group = module
                item.add_marker(pytest.mark.xdist_group(group))
                break


def _copy_inputs(dest: Path, *, with_eng: bool) -> None:
    dest.mkdir(parents=True)
    ignore = shutil.ignore_patterns("__pycache__")
    shutil.copytree(ROOT / "templates", dest / "templates", ignore=ignore)
    shutil.copytree(ROOT / "scripts", dest / "scripts", ignore=ignore)
    shutil.copy2(ROOT / "agents-registry.json", dest / "agents-registry.json")
    if with_eng:
        shutil.copytree(ROOT / "eng" / "release", dest / "eng" / "release", ignore=ignore)


@pytest.fixture(scope="session")
def package_build(tmp_path_factory: pytest.TempPathFactory) -> PackageBuild:
    """Local Copilot, md (claude) and toml (gemini) packages built from a copy of the tree.

    Each agent builds concurrently in its own copy: the packager clears `.genreleases/` on
    start, so the copies must not share it. The packages are identical to a combined build.
    """
    bash = bash_path()
    if bash is None:
        pytest.skip("bash not available")
    base = tmp_path_factory.mktemp("package-build")
    works = {agent: base / agent for agent in BUILD_AGENTS}
    procs: dict[str, subprocess.Popen[str]] = {}
    for agent, work in works.items():
        _copy_inputs(work, with_eng=True)
        env = {**os.environ, "AGENTS": agent, "SCRIPTS": "sh"}
        procs[agent] = subprocess.Popen(
            [bash, "eng/release/create-release-packages.sh", "v9.0.0"],
            cwd=work, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
        )
    try:
        outputs = {agent: proc.communicate(timeout=BUILD_TIMEOUT)[0] for agent, proc in procs.items()}
    finally:
        for proc in procs.values():
            if proc.poll() is None:
                proc.kill()
    for agent, proc in procs.items():
        assert proc.returncode == 0, outputs[agent]
    zips = {a: works[a] / ".genreleases" / f"devspark-template-{a}-sh-v9.0.0.zip" for a in BUILD_AGENTS}
    dirs = {a: works[a] / ".genreleases" / f"sdd-{a}-package-sh" for a in BUILD_AGENTS}
    for path in (*zips.values(), *dirs.values()):
        assert path.exists(), path
    return PackageBuild(base, zips, dirs)


@dataclass
class GeneratorRun:
    repo: Path
    before: dict[str, bytes]


@pytest.fixture(scope="session")
def generated_repos(tmp_path_factory: pytest.TempPathFactory) -> dict[str, GeneratorRun]:
    """Each skill-generator twin run once on its own copy of the repository's generator inputs.

    Tests read these trees; any test that mutates one must copy it first.
    """
    runs: dict[str, GeneratorRun] = {}
    for shell, available in (("bash", bash_path() is not None), ("pwsh", shutil.which("pwsh") is not None)):
        if not available:
            continue
        repo = copy_generation_repo(tmp_path_factory.mktemp(f"generated-{shell}") / "repo")
        before = tree_bytes(repo)
        result = run_generator(shell, repo)
        assert result.returncode == 0, result.stdout + result.stderr
        runs[shell] = GeneratorRun(repo, before)
    return runs


def _extract_function(yaml_text: str, name: str) -> str:
    lines = yaml_text.replace("\r\n", "\n").split("\n")
    start = next(i for i, line in enumerate(lines) if line.strip() == f"{name}() {{")
    indent = re.match(r"\s*", lines[start]).group(0)
    end = next(i for i in range(start + 1, len(lines)) if lines[i] == indent + "}")
    return textwrap.dedent("\n".join(lines[start : end + 1]))


@dataclass
class InstallIndex:
    work: Path
    rows: list[tuple[str, str, str]]


@pytest.fixture(scope="session")
def install_index(tmp_path_factory: pytest.TempPathFactory) -> InstallIndex:
    """`build_install_index` lifted out of the pipeline file and run on a temporary copy."""
    bash = bash_path()
    if bash is None:
        pytest.skip("bash not available")
    work = tmp_path_factory.mktemp("install-index") / "repo"
    _copy_inputs(work, with_eng=False)
    function = _extract_function((ROOT / "azure-pipelines.yml").read_text(encoding="utf-8"), "build_install_index")
    script = work.parent / "index.sh"
    script.write_bytes((function + "\nbuild_install_index\n").encode("utf-8"))
    result = subprocess.run(
        [bash, str(script)], cwd=work, capture_output=True, text=True, encoding="utf-8", timeout=INDEX_TIMEOUT
    )
    assert result.returncode == 0, result.stdout + result.stderr
    rows = [tuple(line.split("\t")) for line in result.stdout.replace("\r\n", "\n").split("\n") if line]
    assert rows and all(len(r) == 3 for r in rows), result.stdout[:400]
    return InstallIndex(work, rows)
