"""Contract coverage for the current-truth lifecycle and archive ownership model."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_implement_leaves_work_products_for_release() -> None:
    implement = _read("templates/commands/implement.md")
    assert "Implement never archives anything" in implement
    assert "/devspark-release` is the sole command that later sweeps" in implement


def test_release_owns_routine_work_product_sweep() -> None:
    release = _read("templates/commands/release.md")
    assert "the **sole** command" in release
    assert "archive-eligible specs/quickfixes" in release


def test_governance_commands_can_archive_governance_proposals() -> None:
    constitution = _read(".knowledge/governance/constitution.md")
    philosophy = _read(".knowledge/governance/devspark-philosophy.md")
    for command in ("/devspark-release", "/devspark-constitution", "/devspark-evolve-constitution"):
        assert command in constitution
        assert command in philosophy


def test_published_codex_guidance_matches_archive_ownership() -> None:
    guidance = _read("site/src/get-started/devspark-and-codex.md")
    assert "leaves the" in guidance
    assert "`/devspark-release`" in guidance
    assert "implement` changes code, tests, and current knowledge, verifies them, and archives" not in guidance