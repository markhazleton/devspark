"""
T069 — PR Scope Validation scenario tests.

Tests the five scenarios specified in the task definition.
Run with: python tests/test_pr_scope_validation.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src is importable without going through __init__.py
import importlib.util

_src = str(Path(__file__).resolve().parent.parent / "src")
sys.path.insert(0, _src)

for _mod in ["registry", "scope", "resolution", "inference"]:
    _spec = importlib.util.spec_from_file_location(
        f"devspark_cli.{_mod}",
        f"{_src}/devspark_cli/{_mod}.py",
        submodule_search_locations=[],
    )
    _m = importlib.util.module_from_spec(_spec)
    sys.modules[f"devspark_cli.{_mod}"] = _m

for _mod in ["registry", "scope", "resolution", "inference"]:
    _spec = importlib.util.spec_from_file_location(
        f"devspark_cli.{_mod}",
        f"{_src}/devspark_cli/{_mod}.py",
    )
    _spec.loader.exec_module(sys.modules[f"devspark_cli.{_mod}"])

from devspark_cli.registry import AppDefinition, DevSparkRegistry
from devspark_cli.scope import PRScopeDeclaration, validate_pr_scope


def _build_registry() -> DevSparkRegistry:
    """Build a minimal multi-app registry for testing."""
    return DevSparkRegistry(
        version=1,
        mode="multi-app",
        apps=[
            AppDefinition(id="admin-web", path="apps/admin-web", kind="frontend"),
            AppDefinition(id="admin-api", path="apps/admin-api", kind="backend"),
            AppDefinition(id="shared-auth", path="libs/shared-auth", kind="library"),
        ],
    )


REPO_ROOT = Path("/tmp/fake-repo")


def run_scenarios() -> None:
    registry = _build_registry()
    results: list[tuple[str, bool]] = []

    # P1: single-app admin-web, changes only in apps/admin-web/ -> PASS
    decl = PRScopeDeclaration(mode="single-app", primary_app="admin-web")
    passed, msgs = validate_pr_scope(
        decl,
        ["apps/admin-web/src/index.ts", "apps/admin-web/package.json"],
        registry,
        REPO_ROOT,
    )
    results.append(("P1: single-app, own files only", passed is True))

    # P2: single-app admin-web, changes in apps/admin-web/ + .github/ -> PASS (shared)
    decl = PRScopeDeclaration(mode="single-app", primary_app="admin-web")
    passed, msgs = validate_pr_scope(
        decl,
        ["apps/admin-web/src/app.ts", ".github/workflows/ci.yml"],
        registry,
        REPO_ROOT,
    )
    results.append(("P2: single-app + shared .github/ path", passed is True))

    # P3: single-app admin-web, changes in apps/admin-web/ + apps/admin-api/ -> FAIL
    decl = PRScopeDeclaration(mode="single-app", primary_app="admin-web")
    passed, msgs = validate_pr_scope(
        decl,
        ["apps/admin-web/src/app.ts", "apps/admin-api/src/server.ts"],
        registry,
        REPO_ROOT,
    )
    results.append(("P3: single-app scope mismatch (touches another app)", passed is False))

    # P4: cross-app primary=admin-web affected=[admin-api], both paths -> PASS
    decl = PRScopeDeclaration(
        mode="cross-app",
        primary_app="admin-web",
        affected_apps=["admin-api"],
    )
    passed, msgs = validate_pr_scope(
        decl,
        ["apps/admin-web/src/app.ts", "apps/admin-api/src/handler.ts"],
        registry,
        REPO_ROOT,
    )
    results.append(("P4: cross-app, both declared", passed is True))

    # P5: repo-scope, libs/shared-auth changes -> PASS
    decl = PRScopeDeclaration(mode="repo-scope", reason="infrastructure change")
    passed, msgs = validate_pr_scope(
        decl,
        ["libs/shared-auth/src/auth.ts", "libs/shared-auth/package.json"],
        registry,
        REPO_ROOT,
    )
    results.append(("P5: repo-scope allows everything", passed is True))

    # Print results
    all_passed = True
    for label, ok in results:
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_passed = False
        print(f"  [{status}] {label}")

    print()
    if all_passed:
        print("All 5 scenarios passed.")
    else:
        print("SOME SCENARIOS FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    run_scenarios()
