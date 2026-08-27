"""Contracts for refreshing an already-published release from workflow dispatch."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_workflow_dispatch_can_refresh_existing_release_assets() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    refresh_condition = (
        "steps.check_release.outputs.exists == 'false' || "
        "github.event_name == 'workflow_dispatch'"
    )

    assert refresh_condition in workflow
    assert workflow.count(refresh_condition) == 3


def test_publish_scripts_clobber_existing_release_assets() -> None:
    bash_publish = (ROOT / ".github" / "workflows" / "scripts" / "create-github-release.sh").read_text(
        encoding="utf-8"
    )
    ps_publish = (ROOT / ".github" / "workflows" / "scripts" / "create-github-release.ps1").read_text(
        encoding="utf-8"
    )

    assert 'gh release view "$VERSION"' in bash_publish
    assert 'gh release upload "$VERSION"' in bash_publish
    assert "--clobber" in bash_publish
    assert 'gh release edit "$VERSION"' in bash_publish

    assert "gh release view $Version" in ps_publish
    assert "gh release upload $Version" in ps_publish
    assert "--clobber" in ps_publish
    assert "gh release edit $Version" in ps_publish
