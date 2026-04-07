"""
DevSpark Resolution — Constitution, prompt, script, and template resolution chains.

Implements the multi-tier resolution model with constitution weakening detection
and profile composition.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .registry import (
    AppDefinition,
    AppManifest,
    DevSparkRegistry,
    Profile,
    load_app_manifest,
)


# ---------------------------------------------------------------------------
# Constitution resolution (FR-C3)
# ---------------------------------------------------------------------------

_MANDATORY_MARKERS = re.compile(
    r"\b(NON-NEGOTIABLE|MUST|MANDATORY)\b", re.IGNORECASE
)

_WEAKENING_PATTERNS = re.compile(
    r"\b(not required|optional|may skip|does not apply|is not mandatory|"
    r"can be skipped|not necessary|no longer required|exempt from)\b",
    re.IGNORECASE,
)


def extract_mandatory_rules(constitution_text: str) -> list[str]:
    """Extract lines containing mandatory markers from a constitution."""
    mandatory: list[str] = []
    for line in constitution_text.splitlines():
        stripped = line.strip()
        if stripped and _MANDATORY_MARKERS.search(stripped):
            mandatory.append(stripped)
    return mandatory


def detect_weakening(
    repo_mandatory_rules: list[str],
    overlay_text: str,
) -> list[str]:
    """
    Detect if an overlay text weakens any mandatory repo rules.

    Returns a list of CONFLICT warnings for detected weakening.
    """
    conflicts: list[str] = []
    overlay_lines = [l.strip() for l in overlay_text.splitlines() if l.strip()]

    for line in overlay_lines:
        if _WEAKENING_PATTERNS.search(line):
            conflicts.append(
                f"CONFLICT: app constitution may weaken mandatory rule: {line!r}"
            )

    return conflicts


def detect_app_json_weakening(
    repo_root: Path,
    app: AppDefinition,
    manifest: "AppManifest",
) -> list[str]:
    """
    Check if app.json rules weaken mandatory repo-wide rules (T015c).

    Uses the same keyword-based detection as constitution overlays.
    """
    repo_constitution_path = repo_root / ".documentation" / "memory" / "constitution.md"
    if not repo_constitution_path.is_file():
        return []

    repo_text = repo_constitution_path.read_text(encoding="utf-8")
    mandatory_rules = extract_mandatory_rules(repo_text)

    conflicts: list[str] = []
    for rule in manifest.rules:
        if _WEAKENING_PATTERNS.search(rule):
            conflicts.append(
                f"CONFLICT: app.json rule for {app.id!r} may weaken mandatory rule: {rule!r}"
            )

    return conflicts


def resolve_constitution(
    repo_root: Path,
    app: AppDefinition | None = None,
) -> tuple[str, list[str]]:
    """
    Resolve the effective constitution.

    1. Load repo constitution from .documentation/memory/constitution.md
    2. If app is provided, overlay app constitution from {app.path}/.documentation/memory/constitution.md
    3. Run weakening detection on the overlay

    Returns (effective_constitution_text, warnings).
    """
    warnings: list[str] = []

    # Load repo constitution
    repo_constitution_path = repo_root / ".documentation" / "memory" / "constitution.md"
    if not repo_constitution_path.is_file():
        raise ValueError(
            f"Repository constitution required but not found at {repo_constitution_path}"
        )
    repo_text = repo_constitution_path.read_text(encoding="utf-8")

    if app is None:
        return repo_text, warnings

    # Load app constitution overlay
    app_constitution_path = (
        repo_root / app.path / ".documentation" / "memory" / "constitution.md"
    )
    if not app_constitution_path.is_file():
        # No app overlay — repo constitution is the full effective constitution
        return repo_text, warnings

    app_text = app_constitution_path.read_text(encoding="utf-8")

    # Weakening detection
    mandatory_rules = extract_mandatory_rules(repo_text)
    conflicts = detect_weakening(mandatory_rules, app_text)
    warnings.extend(conflicts)

    # Compose: repo constitution + app overlay
    effective = (
        repo_text.rstrip()
        + "\n\n---\n\n"
        + f"## Application Overlay: {app.id}\n\n"
        + app_text
    )

    return effective, warnings


# ---------------------------------------------------------------------------
# File-based resolution chains (FR-C4, FR-C5, FR-C6)
# ---------------------------------------------------------------------------

def resolve_file(
    filename: str,
    chain: list[Path],
) -> Path | None:
    """
    Resolve a file through a priority chain of directories.

    Returns the first path where filename exists, or None.
    Uses exact filename matching only — no glob patterns.
    """
    for directory in chain:
        candidate = directory / filename
        if candidate.is_file():
            return candidate
    return None


def build_prompt_chain(
    repo_root: Path,
    app: AppDefinition | None = None,
    git_user: str | None = None,
) -> list[Path]:
    """
    Build the prompt resolution chain (FR-C4):

    1. App team override: {app.path}/.documentation/commands/
    2. Repo user override: .documentation/{git-user}/commands/
    3. Repo team override: .documentation/commands/
    4. Stock DevSpark default: .devspark/defaults/commands/
    """
    chain: list[Path] = []

    if app is not None:
        chain.append(repo_root / app.path / ".documentation" / "commands")

    if git_user:
        chain.append(repo_root / ".documentation" / git_user / "commands")

    chain.append(repo_root / ".documentation" / "commands")
    chain.append(repo_root / ".devspark" / "defaults" / "commands")

    return chain


def build_script_chain(
    repo_root: Path,
    app: AppDefinition | None = None,
) -> list[Path]:
    """
    Build the script resolution chain (FR-C5):

    1. App team override: {app.path}/.documentation/scripts/
    2. Repo team override: .documentation/scripts/
    3. Stock DevSpark default: .devspark/scripts/
    """
    chain: list[Path] = []

    if app is not None:
        chain.append(repo_root / app.path / ".documentation" / "scripts")

    chain.append(repo_root / ".documentation" / "scripts")
    chain.append(repo_root / ".devspark" / "scripts")

    return chain


def build_template_chain(
    repo_root: Path,
    app: AppDefinition | None = None,
) -> list[Path]:
    """
    Build the template resolution chain (FR-C6):

    1. App team override: {app.path}/.documentation/templates/
    2. Repo team override: .documentation/templates/
    3. Stock DevSpark default: .devspark/templates/
    """
    chain: list[Path] = []

    if app is not None:
        chain.append(repo_root / app.path / ".documentation" / "templates")

    chain.append(repo_root / ".documentation" / "templates")
    chain.append(repo_root / ".devspark" / "templates")

    return chain


# ---------------------------------------------------------------------------
# Profile composition (FR-E2)
# ---------------------------------------------------------------------------

@dataclass
class EffectiveProfile:
    """The resolved effective profile after composition."""

    tags: dict[str, str]
    rules: list[str]
    hints: dict[str, str]

    def __init__(self) -> None:
        self.tags = {}
        self.rules = []
        self.hints = {}


def compose_profiles(
    registry: DevSparkRegistry,
    app: AppDefinition,
    app_manifest: AppManifest | None = None,
) -> tuple[EffectiveProfile, list[str]]:
    """
    Compose the effective profile for an application.

    Composition order:
    1. Inherited profiles in declaration order (tags: LWW, rules: additive, hints: LWW)
    2. App registry-level overrides
    3. App-local manifest (app.json) if present

    Returns (effective_profile, warnings).
    """
    warnings: list[str] = []
    effective = EffectiveProfile()

    # Step 1: Compose inherited profiles
    for profile_name in app.inherits:
        profile = registry.profiles.get(profile_name)
        if profile is None:
            # Should have been caught by registry validation, but be safe
            warnings.append(f"Profile {profile_name!r} not found during composition")
            continue

        # Tags: last-writer-wins per key
        effective.tags.update(profile.tags)

        # Rules: additive — never removed
        for rule in profile.rules:
            if rule not in effective.rules:
                effective.rules.append(rule)

        # Hints: last-writer-wins per key
        effective.hints.update(profile.hints)

    # Step 2: Apply app registry-level overrides
    overrides = app.overrides
    if overrides:
        if "tags" in overrides and isinstance(overrides["tags"], dict):
            effective.tags.update(overrides["tags"])
        if "rules" in overrides and isinstance(overrides["rules"], list):
            for rule in overrides["rules"]:
                if rule not in effective.rules:
                    effective.rules.append(rule)
        if "hints" in overrides and isinstance(overrides["hints"], dict):
            effective.hints.update(overrides["hints"])

    # Step 3: Apply app-local manifest (app.json)
    if app_manifest is not None:
        effective.tags.update(app_manifest.tags)
        for rule in app_manifest.rules:
            if rule not in effective.rules:
                effective.rules.append(rule)
        effective.hints.update(app_manifest.hints)

    return effective, warnings
