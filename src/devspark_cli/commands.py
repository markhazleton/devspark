"""
DevSpark Commands — add-application, list-applications, validate-registry.

CLI-level command implementations for multi-app registry management.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .registry import (
    AppDefinition,
    DevSparkRegistry,
    Profile,
    get_app,
    load_app_manifest,
    load_registry,
    validate_paths,
)
from .resolution import (
    detect_app_json_weakening,
    detect_weakening,
    extract_mandatory_rules,
    validate_profiles_across_apps,
)


# ---------------------------------------------------------------------------
# Standard scaffolding directories
# ---------------------------------------------------------------------------

_SCAFFOLD_DIRS = [
    "memory",
    "commands",
    "scripts",
    "templates",
    "specs",
]


# ---------------------------------------------------------------------------
# Multi-app registry creation helpers
# ---------------------------------------------------------------------------

def add_application(
    repo_root: Path,
    app_id: str,
    name: str,
    path: str,
    kind: str,
    purpose: str = "",
    runtime: str = "",
    owner: str = "",
    criticality: str = "medium",
    deployable: bool = True,
    inherits: list[str] | None = None,
    depends_on: list[str] | None = None,
    tags: list[str] | None = None,
    platforms: list[str] | None = None,
) -> dict[str, Any]:
    """
    Add a new application to the registry and scaffold its documentation.

    Returns a result dict with 'success', 'entry', 'scaffolded', and 'errors'.
    """
    registry_path = repo_root / ".documentation" / "devspark.json"
    inherits = inherits or []
    depends_on = depends_on or []
    tags = tags or []
    platforms = platforms or []

    # Load or create registry
    if registry_path.is_file():
        raw = json.loads(registry_path.read_text(encoding="utf-8"))
    else:
        raw = {
            "version": 1,
            "mode": "multi-app",
            "profiles": {},
            "apps": [],
        }

    # Check duplicate ID
    existing_ids = {a["id"] for a in raw.get("apps", [])}
    if app_id in existing_ids:
        return {
            "success": False,
            "errors": [f"duplicate id: {app_id}"],
            "entry": None,
            "scaffolded": [],
        }

    # Build entry
    entry = {
        "id": app_id,
        "name": name,
        "path": path,
        "kind": kind,
        "purpose": purpose,
        "runtime": runtime,
        "owner": owner,
        "criticality": criticality,
        "deployable": deployable,
        "inherits": inherits,
        "dependsOn": depends_on,
        "tags": tags,
        "platforms": platforms,
        "overrides": {},
    }

    # Validate profile references
    profile_keys = set(raw.get("profiles", {}).keys())
    bad_profiles = [p for p in inherits if p not in profile_keys]
    if bad_profiles:
        return {
            "success": False,
            "errors": [f"unknown profile(s): {', '.join(bad_profiles)}"],
            "entry": None,
            "scaffolded": [],
        }

    # Validate dependency references
    all_ids = existing_ids | {app_id}
    bad_deps = [d for d in depends_on if d not in all_ids]
    if bad_deps:
        return {
            "success": False,
            "errors": [f"unknown dependency(ies): {', '.join(bad_deps)}"],
            "entry": None,
            "scaffolded": [],
        }

    # Add to registry
    raw["apps"].append(entry)

    # Validate full registry
    try:
        DevSparkRegistry.model_validate(raw)
    except Exception as exc:
        return {
            "success": False,
            "errors": [str(exc)],
            "entry": None,
            "scaffolded": [],
        }

    # Write registry
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(raw, indent=2) + "\n", encoding="utf-8"
    )

    # Scaffold documentation directories (always)
    app_doc_root = repo_root / path / ".documentation"
    scaffolded: list[str] = []
    for subdir in _SCAFFOLD_DIRS:
        d = app_doc_root / subdir
        d.mkdir(parents=True, exist_ok=True)
        scaffolded.append(str(d.relative_to(repo_root)))

    return {
        "success": True,
        "entry": entry,
        "scaffolded": scaffolded,
        "errors": [],
    }


# ---------------------------------------------------------------------------
# Multi-app registry inspection helpers
# ---------------------------------------------------------------------------

def list_applications(repo_root: Path) -> dict[str, Any]:
    """
    List all registered applications.

    Returns a result dict with 'mode', 'apps', 'profiles', and 'errors'.
    """
    registry_path = repo_root / ".documentation" / "devspark.json"

    if not registry_path.is_file():
        return {
            "mode": "single-app",
            "apps": [],
            "profiles": [],
            "message": "No multi-app registry configured. Repository operates in single-app mode.",
            "errors": [],
        }

    try:
        registry = load_registry(repo_root)
    except ValueError as exc:
        return {
            "mode": "error",
            "apps": [],
            "profiles": [],
            "message": str(exc),
            "errors": [str(exc)],
        }

    apps = []
    for app in registry.apps:
        doc_root = f"{app.path}/.documentation"
        apps.append({
            "id": app.id,
            "name": app.name,
            "path": app.path,
            "kind": app.kind,
            "owner": app.owner,
            "criticality": app.criticality,
            "deployable": app.deployable,
            "inherits": app.inherits,
            "dependsOn": app.dependsOn,
            "doc_root": doc_root,
        })

    profiles = []
    for name, profile in registry.profiles.items():
        profiles.append({
            "name": name,
            "description": profile.description,
            "rule_count": len(profile.rules),
        })

    return {
        "mode": "multi-app",
        "apps": apps,
        "profiles": profiles,
        "message": f"{len(apps)} applications, {len(profiles)} profiles",
        "errors": [],
    }


# ---------------------------------------------------------------------------
# Multi-app registry validation helpers
# ---------------------------------------------------------------------------

def validate_registry(repo_root: Path) -> dict[str, Any]:
    """
    Validate the registry, app.json files, and constitutions.

    Returns a result dict with 'valid', 'errors', 'warnings', and 'summary'.
    """
    errors: list[str] = []
    warnings: list[str] = []

    registry_path = repo_root / ".documentation" / "devspark.json"

    if not registry_path.is_file():
        return {
            "valid": False,
            "errors": ["No multi-app registry found"],
            "warnings": [],
            "summary": {"apps": 0, "profiles": 0},
        }

    # Schema and reference validation
    try:
        registry = load_registry(repo_root)
    except ValueError as exc:
        return {
            "valid": False,
            "errors": [str(exc)],
            "warnings": [],
            "summary": {"apps": 0, "profiles": 0},
        }

    # App.json validation
    for app in registry.apps:
        manifest, mw = load_app_manifest(Path(app.path), repo_root)
        warnings.extend(mw)

        if manifest is not None:
            # Weakening detection on app.json rules
            conflicts = detect_app_json_weakening(repo_root, app, manifest)
            warnings.extend(conflicts)

    # Profile validation across apps
    profile_warnings = validate_profiles_across_apps(registry, repo_root)
    warnings.extend(profile_warnings)

    # Constitution validation
    repo_const = repo_root / ".documentation" / "memory" / "constitution.md"
    if not repo_const.is_file():
        errors.append("Repository constitution not found")
    else:
        repo_text = repo_const.read_text(encoding="utf-8")
        mandatory_rules = extract_mandatory_rules(repo_text)

        for app in registry.apps:
            app_const = repo_root / app.path / ".documentation" / "memory" / "constitution.md"
            if app_const.is_file():
                app_text = app_const.read_text(encoding="utf-8")
                conflicts = detect_weakening(mandatory_rules, app_text)
                warnings.extend(conflicts)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "apps": len(registry.apps),
            "profiles": len(registry.profiles),
        },
    }
