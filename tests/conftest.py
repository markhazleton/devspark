# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Session-scoped fixtures that build release packages and the install index once per run."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path

import pytest

from tests.consumer_skill_helpers import ROOT, bash_path

BUILD_AGENTS = ("copilot", "claude", "gemini")
BUILD_TIMEOUT = 600
INDEX_TIMEOUT = 120


@dataclass
class PackageBuild:
    work: Path
    zips: dict[str, Path]
    dirs: dict[str, Path]


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
    """Local Copilot, md (claude) and toml (gemini) packages built from a copy of the tree."""
    bash = bash_path()
    if bash is None:
        pytest.skip("bash not available")
    work = tmp_path_factory.mktemp("package-build") / "repo"
    _copy_inputs(work, with_eng=True)
    env = {**os.environ, "AGENTS": ",".join(BUILD_AGENTS), "SCRIPTS": "sh"}
    result = subprocess.run(
        [bash, "eng/release/create-release-packages.sh", "v9.0.0"],
        cwd=work, env=env, capture_output=True, text=True, encoding="utf-8", timeout=BUILD_TIMEOUT,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    out = work / ".genreleases"
    zips = {a: out / f"devspark-template-{a}-sh-v9.0.0.zip" for a in BUILD_AGENTS}
    dirs = {a: out / f"sdd-{a}-package-sh" for a in BUILD_AGENTS}
    for path in (*zips.values(), *dirs.values()):
        assert path.exists(), path
    return PackageBuild(work, zips, dirs)


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
