"""
DevSpark Registry — Pydantic v2 models and validation for devspark.json.

Handles loading, validating, and querying the authoritative repository registry.
Includes app-local manifest (app.json) loading and merge support.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Profile model
# ---------------------------------------------------------------------------

class Profile(BaseModel):
    """A reusable rule bundle applied to a class of applications."""

    description: str = ""
    tags: dict[str, str] = Field(default_factory=dict)
    rules: list[str] = Field(default_factory=list)
    hints: dict[str, str] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# App-local manifest model (app.json — subset mirror)
# ---------------------------------------------------------------------------

class AppManifest(BaseModel):
    """
    Optional app-local manifest at {app.path}/app.json.

    Contains only override content: tags, hints, local rules.
    Identity fields (id, path, kind, owner, etc.) are ignored if present.
    """

    tags: dict[str, str] = Field(default_factory=dict)
    hints: dict[str, str] = Field(default_factory=dict)
    rules: list[str] = Field(default_factory=list)


# Identity fields that must not appear in app.json
_APP_JSON_IDENTITY_FIELDS = {
    "id", "name", "path", "kind", "purpose", "runtime", "owner",
    "criticality", "deployable", "inherits", "dependsOn", "platforms",
}


def load_app_manifest(
    app_path: Path,
    repo_root: Path,
) -> tuple[AppManifest | None, list[str]]:
    """
    Load and validate an app-local manifest from {app_path}/app.json.

    Returns (manifest, warnings). If the file does not exist, returns (None, []).
    Identity fields present in app.json produce warnings but are ignored.
    """
    manifest_path = repo_root / app_path / "app.json"
    warnings: list[str] = []

    if not manifest_path.is_file():
        return None, warnings

    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        warnings.append(f"Failed to parse {manifest_path}: {exc}")
        return None, warnings

    if not isinstance(raw, dict):
        warnings.append(f"{manifest_path}: expected JSON object, got {type(raw).__name__}")
        return None, warnings

    # Warn on identity fields
    found_identity = _APP_JSON_IDENTITY_FIELDS & raw.keys()
    if found_identity:
        warnings.append(
            f"{manifest_path}: identity fields ignored in app.json: "
            f"{', '.join(sorted(found_identity))}"
        )

    # Extract only allowed fields
    manifest = AppManifest(
        tags=raw.get("tags", {}),
        hints=raw.get("hints", {}),
        rules=raw.get("rules", []),
    )
    return manifest, warnings


# ---------------------------------------------------------------------------
# Application definition model
# ---------------------------------------------------------------------------

class AppDefinition(BaseModel):
    """A registered application in the repository."""

    id: str
    name: str = ""
    path: str
    kind: str = ""
    purpose: str = ""
    runtime: str = ""
    owner: str = ""
    criticality: str = "medium"
    deployable: bool = True
    inherits: list[str] = Field(default_factory=list)
    dependsOn: list[str] = Field(default_factory=list)  # noqa: N815
    tags: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    overrides: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v:
            raise ValueError("Application id must not be empty")
        if v != v.lower():
            raise ValueError(f"Application id must be lowercase: {v!r}")
        if not all(c.isalnum() or c in "-_" for c in v):
            raise ValueError(
                f"Application id must be path-safe (alphanumeric, dash, underscore): {v!r}"
            )
        return v


# ---------------------------------------------------------------------------
# Registry model
# ---------------------------------------------------------------------------

class DevSparkRegistry(BaseModel):
    """Top-level registry model for .documentation/devspark.json."""

    version: int = 1
    mode: str = "multi-app"
    profiles: dict[str, Profile] = Field(default_factory=dict)
    apps: list[AppDefinition] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_registry(self) -> "DevSparkRegistry":
        errors: list[str] = []

        # --- Unique IDs ---
        seen_ids: set[str] = set()
        for app in self.apps:
            if app.id in seen_ids:
                errors.append(f"duplicate id: {app.id}")
            seen_ids.add(app.id)

        id_set = {app.id for app in self.apps}

        # --- Profile references ---
        for app in self.apps:
            for profile_ref in app.inherits:
                if profile_ref not in self.profiles:
                    errors.append(
                        f"app {app.id!r}: unknown profile: {profile_ref}"
                    )

        # --- Dependency references ---
        for app in self.apps:
            for dep in app.dependsOn:
                if dep not in id_set:
                    errors.append(
                        f"app {app.id!r}: unknown dependency: {dep}"
                    )

        # --- Cycle detection ---
        cycle = _detect_cycles(self.apps)
        if cycle:
            errors.append(f"cyclic dependency detected: {' -> '.join(cycle)}")

        if errors:
            raise ValueError(
                "Registry validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        return self


def _detect_cycles(apps: list[AppDefinition]) -> list[str] | None:
    """Detect cyclic dependencies using DFS. Returns the cycle path or None."""
    dep_map = {app.id: app.dependsOn for app in apps}
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {app_id: WHITE for app_id in dep_map}
    path: list[str] = []

    def dfs(node: str) -> list[str] | None:
        color[node] = GRAY
        path.append(node)
        for neighbor in dep_map.get(node, []):
            if neighbor not in color:
                continue  # unknown dep — caught by reference validation
            if color[neighbor] == GRAY:
                cycle_start = path.index(neighbor)
                return path[cycle_start:] + [neighbor]
            if color[neighbor] == WHITE:
                result = dfs(neighbor)
                if result:
                    return result
        path.pop()
        color[node] = BLACK
        return None

    for app_id in dep_map:
        if color[app_id] == WHITE:
            result = dfs(app_id)
            if result:
                return result
    return None


# ---------------------------------------------------------------------------
# Path validation (requires repo root)
# ---------------------------------------------------------------------------

def validate_paths(registry: DevSparkRegistry, repo_root: Path) -> list[str]:
    """Validate that all app paths exist as directories under repo_root."""
    errors: list[str] = []
    for app in registry.apps:
        app_dir = repo_root / app.path
        if not app_dir.is_dir():
            errors.append(f"path does not exist: {app.path}")
    return errors


# ---------------------------------------------------------------------------
# Mode detection
# ---------------------------------------------------------------------------

def detect_mode(repo_root: Path) -> str:
    """
    Detect whether the repository is single-app or multi-app.

    Returns 'multi-app' if .documentation/devspark.json exists with mode 'multi-app'.
    Returns 'single-app' otherwise.
    """
    registry_path = repo_root / ".documentation" / "devspark.json"
    if not registry_path.is_file():
        return "single-app"

    try:
        raw = json.loads(registry_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and raw.get("mode") == "multi-app":
            return "multi-app"
    except (json.JSONDecodeError, OSError):
        pass

    return "single-app"


# ---------------------------------------------------------------------------
# Registry loading
# ---------------------------------------------------------------------------

def load_registry(repo_root: Path) -> DevSparkRegistry:
    """
    Load and validate the registry from .documentation/devspark.json.

    Raises ValueError if the file is missing, malformed, or fails validation.
    """
    registry_path = repo_root / ".documentation" / "devspark.json"

    if not registry_path.is_file():
        raise ValueError(
            f"No multi-app registry found at {registry_path}. "
            "Use /devspark.add-application to create one, or operate in single-app mode."
        )

    try:
        raw = json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse {registry_path}: {exc}") from exc

    # Schema version check
    version = raw.get("version")
    if version != 1:
        raise ValueError(
            f"Unsupported registry schema version: {version}. "
            "Expected version 1. Run /devspark.upgrade for migration guidance."
        )

    # Pydantic validation
    registry = DevSparkRegistry.model_validate(raw)

    # Path validation
    path_errors = validate_paths(registry, repo_root)
    if path_errors:
        raise ValueError(
            "Registry path validation failed:\n"
            + "\n".join(f"  - {e}" for e in path_errors)
        )

    return registry


def get_app(registry: DevSparkRegistry, app_id: str) -> AppDefinition:
    """Look up an app by id. Raises ValueError if not found."""
    for app in registry.apps:
        if app.id == app_id:
            return app
    available = ", ".join(a.id for a in registry.apps)
    raise ValueError(
        f"Unknown application: {app_id!r}. Available: {available}"
    )
