"""
DevSpark Dependency Inference — Scan source and build files for cross-app references.

Supplements declared dependsOn entries with basic inference from:
- Source imports (*.py, *.ts, *.js, *.cs, *.java)
- Build configuration (package.json, pyproject.toml, *.csproj)

Inferred dependencies are reported separately from declared dependencies.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from .registry import AppDefinition, DevSparkRegistry


# ---------------------------------------------------------------------------
# Source file extensions to scan
# ---------------------------------------------------------------------------

_SOURCE_EXTENSIONS = {".py", ".ts", ".js", ".cs", ".java", ".tsx", ".jsx"}

# Build config filenames to scan
_BUILD_CONFIGS = {"package.json", "pyproject.toml"}

# Build config glob patterns
_BUILD_GLOBS = ["*.csproj"]


# ---------------------------------------------------------------------------
# Gitignore-aware file walking
# ---------------------------------------------------------------------------

def _should_skip(path: Path, skip_dirs: set[str]) -> bool:
    """Check if a path component matches common ignore patterns."""
    for part in path.parts:
        if part in skip_dirs:
            return True
    return False


_SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", "bin", "obj", ".next", ".nuxt",
    "coverage", ".tox", ".mypy_cache", ".pytest_cache",
}


# ---------------------------------------------------------------------------
# Source import scanning
# ---------------------------------------------------------------------------

def _scan_source_imports(
    app_dir: Path,
    other_app_paths: list[str],
) -> dict[str, list[str]]:
    """
    Scan source files in app_dir for import references to other app paths.

    Returns {other_app_id: [file_path_that_references_it, ...]}.
    """
    matches: dict[str, list[str]] = {}

    if not app_dir.is_dir():
        return matches

    for source_file in _walk_source_files(app_dir):
        try:
            content = source_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        rel_path = str(source_file.relative_to(app_dir))

        for app_path, app_id in other_app_paths:
            # Check if any line references the other app's path segment
            # Normalize path separators for matching
            path_segment = app_path.replace("\\", "/")
            # Match the path segment in import-like statements
            if path_segment in content or app_id in content:
                if app_id not in matches:
                    matches[app_id] = []
                matches[app_id].append(rel_path)
                break  # Only record each file once per app


    return matches


def _walk_source_files(directory: Path):
    """Walk directory yielding source files, skipping ignored dirs."""
    try:
        for item in directory.iterdir():
            if item.is_dir():
                if item.name not in _SKIP_DIRS and not item.name.startswith("."):
                    yield from _walk_source_files(item)
            elif item.is_file() and item.suffix in _SOURCE_EXTENSIONS:
                yield item
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Build config scanning
# ---------------------------------------------------------------------------

def _scan_build_configs(
    app_dir: Path,
    other_app_paths: list[str],
) -> dict[str, list[str]]:
    """
    Scan build configuration files for project references to other apps.

    Returns {other_app_id: [config_file, ...]}.
    """
    matches: dict[str, list[str]] = {}

    if not app_dir.is_dir():
        return matches

    # Scan known config files
    for config_name in _BUILD_CONFIGS:
        config_path = app_dir / config_name
        if config_path.is_file():
            try:
                content = config_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            for app_path, app_id in other_app_paths:
                if app_path in content or app_id in content:
                    if app_id not in matches:
                        matches[app_id] = []
                    matches[app_id].append(config_name)

    # Scan csproj files
    for pattern in _BUILD_GLOBS:
        for config_path in app_dir.glob(f"**/{pattern}"):
            if _should_skip(config_path.relative_to(app_dir), _SKIP_DIRS):
                continue
            try:
                content = config_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            rel = str(config_path.relative_to(app_dir))
            for app_path, app_id in other_app_paths:
                if app_path in content or app_id in content:
                    if app_id not in matches:
                        matches[app_id] = []
                    matches[app_id].append(rel)

    return matches


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def infer_dependencies(
    registry: DevSparkRegistry,
    app: AppDefinition,
    repo_root: Path,
) -> list[tuple[str, str]]:
    """
    Infer undeclared dependencies for an app by scanning its source and build files.

    Returns a list of (app_id, evidence_description) for inferred dependencies
    that are NOT already declared in dependsOn.

    Example: [("runtime-api-a", "from apps/admin-web/src/api-client.ts import")]
    """
    declared = set(app.dependsOn)
    app_dir = repo_root / app.path

    # Build list of other app paths to search for
    other_apps: list[tuple[str, str]] = [
        (other.path, other.id)
        for other in registry.apps
        if other.id != app.id
    ]

    inferred: list[tuple[str, str]] = []

    # Scan source imports
    source_matches = _scan_source_imports(app_dir, other_apps)
    for app_id, files in source_matches.items():
        if app_id not in declared:
            evidence = f"from {app.path}/{files[0]} import"
            inferred.append((app_id, evidence))

    # Scan build configs
    build_matches = _scan_build_configs(app_dir, other_apps)
    for app_id, files in build_matches.items():
        if app_id not in declared and app_id not in {i[0] for i in inferred}:
            evidence = f"from {app.path}/{files[0]} build config"
            inferred.append((app_id, evidence))

    return sorted(inferred, key=lambda x: x[0])
