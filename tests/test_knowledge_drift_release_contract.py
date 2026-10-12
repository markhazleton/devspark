from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SELF_TEST = ROOT / "templates" / "knowledge-drift" / "self-test"
RELEASE_PACKAGER = ROOT / "eng" / "release" / "create-release-packages.sh"


def _manifest_controls() -> list[dict[str, str]]:
    manifest = yaml.safe_load((SELF_TEST / "claims.yaml").read_text(encoding="utf-8"))
    return manifest["controls"]


def test_every_runtime_control_and_reference_is_installed() -> None:
    controls = _manifest_controls()
    assert {control["name"] for control in controls} == {
        "known-changed",
        "known-unchanged",
        "invalid-canonicalization",
    }
    for control in controls:
        for field in ("source", "baseline"):
            referenced = SELF_TEST / control[field]
            assert referenced.is_file(), f"missing runtime control {control[field]}"


def test_release_packager_includes_runtime_controls() -> None:
    packager = RELEASE_PACKAGER.read_text(encoding="utf-8")
    assert 'copy_relative_files templates "$DEVSPARK_DIR"' in packager
    assert "knowledge-drift/self-test" not in packager


def test_corruption_variants_are_test_only() -> None:
    corruption_root = ROOT / "tests" / "fixtures" / "knowledge-drift" / "corruptions"
    assert corruption_root.is_dir()
    assert not (ROOT / "templates" / "knowledge-drift" / "corruptions").exists()
