"""
DevSpark Scope — Scope object, documentation root resolution, and dependency reporting.

Handles repo-scope vs app-scope resolution, inverse dependency lookup,
and scope report generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .registry import AppDefinition, DevSparkRegistry


# ---------------------------------------------------------------------------
# Scope types
# ---------------------------------------------------------------------------

SCOPE_REPO = "repo"
SCOPE_SINGLE_APP = "single-app"
SCOPE_CROSS_APP = "cross-app"


# ---------------------------------------------------------------------------
# Scope object
# ---------------------------------------------------------------------------

@dataclass
class ScopeContext:
    """
    The resolved execution scope for a DevSpark workflow.

    Populated by scope resolution and used by all downstream workflow steps.
    """

    scope_type: str = SCOPE_REPO
    primary_app: Optional[str] = None
    affected_apps: list[str] = field(default_factory=list)
    declared_downstream: list[str] = field(default_factory=list)
    inferred_downstream: list[str] = field(default_factory=list)
    doc_root: str = ".documentation"
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Render a human-readable scope summary."""
        lines = [
            f"scope: {self.scope_type}",
            f"doc-root: {self.doc_root}",
        ]
        if self.primary_app:
            lines.append(f"app: {self.primary_app}")
        if self.affected_apps:
            lines.append(f"affected-apps: {', '.join(self.affected_apps)}")
        if self.declared_downstream:
            lines.append(
                f"declared-downstream: {', '.join(self.declared_downstream)}"
            )
        if self.inferred_downstream:
            lines.append(
                f"inferred-downstream: {', '.join(self.inferred_downstream)}"
            )
        if self.warnings:
            lines.append(f"warnings: {'; '.join(self.warnings)}")
        if self.errors:
            lines.append(f"errors: {'; '.join(self.errors)}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Documentation root resolution
# ---------------------------------------------------------------------------

def resolve_doc_root(
    app: AppDefinition | None,
    repo_root: Path,
) -> Path:
    """
    Resolve the documentation root.

    - If app is provided, returns {repo_root}/{app.path}/.documentation/
    - If app is None (repo scope), returns {repo_root}/.documentation/
    """
    if app is not None:
        return repo_root / app.path / ".documentation"
    return repo_root / ".documentation"


# ---------------------------------------------------------------------------
# Inverse dependency lookup
# ---------------------------------------------------------------------------

def build_downstream_map(
    registry: DevSparkRegistry,
) -> dict[str, list[str]]:
    """
    Build an inverse dependency map: for each app, which apps depend on it.

    dependsOn points upstream (consumer → provider), so the inverse gives
    us downstream consumers of each provider.
    """
    downstream: dict[str, list[str]] = {app.id: [] for app in registry.apps}

    for app in registry.apps:
        for dep in app.dependsOn:
            if dep in downstream:
                downstream[dep].append(app.id)

    return downstream


def get_direct_downstream(
    registry: DevSparkRegistry,
    app_id: str,
) -> list[str]:
    """Get direct downstream consumers of the given app."""
    downstream_map = build_downstream_map(registry)
    return sorted(downstream_map.get(app_id, []))


# ---------------------------------------------------------------------------
# Scope resolution
# ---------------------------------------------------------------------------

def resolve_scope(
    registry: DevSparkRegistry | None,
    app_id: str | None,
    repo_scope: bool,
    repo_root: Path,
) -> ScopeContext:
    """
    Resolve the execution scope for a DevSpark workflow.

    Rules:
    - No registry → single-app mode (repo scope)
    - --app specified → single-app scope for that app
    - --repo-scope specified → repo scope
    - Neither --app nor --repo-scope with multiple apps → error
    """
    ctx = ScopeContext()

    # No registry → single-app mode
    if registry is None:
        if app_id:
            ctx.errors.append("No multi-app registry found. Cannot use --app.")
            return ctx
        ctx.scope_type = SCOPE_REPO
        ctx.doc_root = ".documentation"
        return ctx

    # Explicit repo scope
    if repo_scope:
        ctx.scope_type = SCOPE_REPO
        ctx.doc_root = ".documentation"
        return ctx

    # Explicit app scope
    if app_id:
        # Verify app exists
        app_ids = {a.id for a in registry.apps}
        if app_id not in app_ids:
            available = ", ".join(sorted(app_ids))
            ctx.errors.append(
                f"Unknown application: {app_id!r}. Available: {available}"
            )
            return ctx

        app = next(a for a in registry.apps if a.id == app_id)
        ctx.scope_type = SCOPE_SINGLE_APP
        ctx.primary_app = app_id
        ctx.doc_root = f"{app.path}/.documentation"
        ctx.declared_downstream = get_direct_downstream(registry, app_id)
        return ctx

    # Ambiguous: multiple apps, no explicit scope
    if len(registry.apps) > 1:
        ctx.errors.append(
            "Multiple apps registered; specify --app <id> or use --repo-scope. "
            f"Available: {', '.join(a.id for a in registry.apps)}"
        )
        return ctx

    # Single app in registry — use it
    app = registry.apps[0]
    ctx.scope_type = SCOPE_SINGLE_APP
    ctx.primary_app = app.id
    ctx.doc_root = f"{app.path}/.documentation"
    ctx.declared_downstream = get_direct_downstream(registry, app.id)
    return ctx


# ---------------------------------------------------------------------------
# Scope report generation (T038)
# ---------------------------------------------------------------------------

def generate_scope_report(
    ctx: ScopeContext,
    registry: DevSparkRegistry | None = None,
    inferred: list[tuple[str, str]] | None = None,
) -> str:
    """
    Generate a structured scope report for workflow output.

    Includes declared scope, detected scope, mismatches, declared downstream
    impact list, and inferred downstream impact list.
    """
    lines = [
        "## DevSpark Scope Report",
        "",
        f"**Scope type**: {ctx.scope_type}",
        f"**Documentation root**: {ctx.doc_root}",
    ]

    if ctx.primary_app:
        lines.append(f"**Primary application**: {ctx.primary_app}")

    if ctx.affected_apps:
        lines.append(f"**Affected applications**: {', '.join(ctx.affected_apps)}")

    # Declared dependencies
    if ctx.declared_downstream:
        lines.append("")
        lines.append("### Declared downstream dependencies")
        for dep in ctx.declared_downstream:
            lines.append(f"- {dep}")

    # Inferred dependencies
    if inferred:
        lines.append("")
        lines.append("### Inferred downstream dependencies")
        for dep_id, evidence in inferred:
            lines.append(f"- {dep_id} *(inferred: {evidence})*")

    # Warnings
    if ctx.warnings:
        lines.append("")
        lines.append("### Warnings")
        for warning in ctx.warnings:
            lines.append(f"- {warning}")

    # Errors
    if ctx.errors:
        lines.append("")
        lines.append("### Errors")
        for error in ctx.errors:
            lines.append(f"- {error}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# PR Scope Validation (Phase 9 — T062–T065)
# ---------------------------------------------------------------------------

@dataclass
class PRScopeDeclaration:
    """
    Declares the intended scope of a pull request.

    mode: "single-app" | "cross-app" | "repo-scope"
    primary_app: The primary app being changed (required for single-app/cross-app).
    affected_apps: All apps touched by this PR (used by cross-app mode).
    reason: Human-readable explanation of why this scope was chosen.
    """

    mode: str
    primary_app: Optional[str] = None
    affected_apps: list[str] = field(default_factory=list)
    reason: str = ""


# Shared repository paths that any PR mode may touch without triggering
# a scope mismatch.
APPROVED_SHARED_PATHS: list[str] = [
    ".documentation/",
    ".github/",
    ".devspark/",
]

# Root-level config file extensions that are always considered shared.
_ROOT_CONFIG_EXTENSIONS: set[str] = {
    ".md", ".json", ".yaml", ".yml", ".toml", ".cfg",
}


def is_approved_shared_path(
    path: str,
    repo_root: Path,
    registry: DevSparkRegistry,
) -> bool:
    """
    Return True if *path* is a recognised shared/repo-level path.

    A path is shared when it:
    - Starts with one of APPROVED_SHARED_PATHS prefixes.
    - Is a root-level config file (no directory separator beyond the filename)
      with an approved extension.
    - Starts with a CI-config directory (e.g. .github/, .gitlab-ci/, .circleci/).
    """
    # Normalise to forward slash for consistent matching.
    normalised = path.replace("\\", "/")

    # Check explicit shared prefixes.
    for prefix in APPROVED_SHARED_PATHS:
        if normalised.startswith(prefix):
            return True

    # Root-level config files (no nested directory).
    if "/" not in normalised:
        suffix = Path(normalised).suffix
        if suffix in _ROOT_CONFIG_EXTENSIONS:
            return True

    return False


def analyze_changed_paths(
    changed_paths: list[str],
    registry: DevSparkRegistry,
) -> dict[str, list[str]]:
    """
    Map each changed path to the app it belongs to.

    Returns a dict keyed by app id (for paths inside an app.path prefix)
    plus a ``"_shared"`` key for paths that don't fall under any app.
    """
    result: dict[str, list[str]] = {"_shared": []}

    # Build a lookup sorted longest-prefix-first so nested apps match correctly.
    app_prefixes: list[tuple[str, str]] = sorted(
        [(a.path.rstrip("/") + "/", a.id) for a in registry.apps],
        key=lambda t: len(t[0]),
        reverse=True,
    )

    for p in changed_paths:
        normalised = p.replace("\\", "/")
        matched = False
        for prefix, app_id in app_prefixes:
            if normalised.startswith(prefix):
                result.setdefault(app_id, []).append(p)
                matched = True
                break
        if not matched:
            result["_shared"].append(p)

    return result


def validate_pr_scope(
    declaration: PRScopeDeclaration,
    changed_paths: list[str],
    registry: DevSparkRegistry,
    repo_root: Path,
) -> tuple[bool, list[str]]:
    """
    Validate that the actual changed paths honour the declared PR scope.

    Returns ``(passed, messages)`` where *messages* lists any violations.
    """
    messages: list[str] = []
    path_map = analyze_changed_paths(changed_paths, registry)

    if declaration.mode == "repo-scope":
        return True, ["repo-scope: all paths allowed"]

    if declaration.mode == "single-app":
        primary = declaration.primary_app
        if not primary:
            return False, ["single-app mode requires primary_app"]

        for app_id, paths in path_map.items():
            if app_id == "_shared":
                # Check each shared path is actually approved.
                for sp in paths:
                    if not is_approved_shared_path(sp, repo_root, registry):
                        messages.append(
                            f"scope mismatch: '{sp}' is not an approved shared path"
                        )
                continue
            if app_id != primary:
                messages.append(
                    f"scope mismatch: files touch app '{app_id}' but PR "
                    f"is declared single-app for '{primary}'"
                )

        passed = len(messages) == 0
        return passed, messages if messages else [
            f"single-app scope OK: all changes within '{primary}' + shared paths"
        ]

    if declaration.mode == "cross-app":
        declared_set = set(declaration.affected_apps)
        if declaration.primary_app:
            declared_set.add(declaration.primary_app)

        for app_id, paths in path_map.items():
            if app_id == "_shared":
                for sp in paths:
                    if not is_approved_shared_path(sp, repo_root, registry):
                        messages.append(
                            f"scope mismatch: '{sp}' is not an approved shared path"
                        )
                continue
            if app_id not in declared_set:
                messages.append(
                    f"scope mismatch: files touch app '{app_id}' which is "
                    f"not in declared affected_apps {sorted(declared_set)}"
                )

        passed = len(messages) == 0
        return passed, messages if messages else [
            f"cross-app scope OK: changes within declared apps"
            f" {sorted(declared_set)} + shared paths"
        ]

    return False, [f"unknown PR scope mode: {declaration.mode!r}"]
