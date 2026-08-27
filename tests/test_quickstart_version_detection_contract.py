"""Contracts for quickstart latest-version detection."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_quickstarts_use_github_releases_for_latest_version() -> None:
    for path in sorted((ROOT / "quickstart").glob("devspark_quickstart_*.md")):
        text = path.read_text(encoding="utf-8")
        assert "https://api.github.com/repos/markhazleton/devspark/releases/latest" in text, (
            f"{path.name} must use GitHub Releases as the primary latest-version source."
        )
        changelog_pos = text.find("https://raw.githubusercontent.com/markhazleton/devspark/main/CHANGELOG.md")
        releases_pos = text.find("https://api.github.com/repos/markhazleton/devspark/releases/latest")
        assert releases_pos != -1
        assert changelog_pos == -1 or releases_pos < changelog_pos, (
            f"{path.name} must treat CHANGELOG latest-version parsing as a fallback."
        )


def test_living_docs_name_current_release_explicitly() -> None:
    current_release_line = (
        "[v2.8.0](https://github.com/markhazleton/devspark/releases/tag/v2.8.0)"
    )
    for rel_path in (
        "README.md",
        ".documentation/README.md",
        ".documentation/about.md",
        ".documentation/index.md",
        ".documentation/installation.md",
        ".documentation/quickstart.md",
        ".documentation/upgrade.md",
    ):
        text = (ROOT / rel_path).read_text(encoding="utf-8")
        assert current_release_line in text, f"{rel_path} must explicitly name v2.8.0"


def test_living_docs_use_v280_command_counts() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    docs_index = (ROOT / ".documentation" / "index.md").read_text(encoding="utf-8")
    templates_readme = (ROOT / "templates" / "README.md").read_text(encoding="utf-8")

    assert "30 stock command prompts" in readme
    assert "30 stock command prompt files" in readme
    assert "30 stock command prompts" in docs_index
    assert "As of v2.8.0, the collection includes 29 active commands plus 1 deprecated compatibility alias." in templates_readme


def test_upgrade_prompts_use_releases_api_for_latest_version() -> None:
    releases_api = "https://api.github.com/repos/markhazleton/devspark/releases/latest"
    for rel_path in (
        "templates/commands/upgrade.md",
        "templates/commands/site-audit.md",
    ):
        text = (ROOT / rel_path).read_text(encoding="utf-8")
        releases_pos = text.find(releases_api)
        changelog_pos = text.find("Fallback if the Releases API is unreachable")
        assert releases_pos != -1, f"{rel_path} must use GitHub Releases API"
        assert changelog_pos == -1 or releases_pos < changelog_pos, (
            f"{rel_path} must treat CHANGELOG parsing as a fallback."
        )
