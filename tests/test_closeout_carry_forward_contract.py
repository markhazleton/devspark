# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Closeout decisions are read, carried forward, and invalidated only by real change.

Behavioral reference: a lifecycle was complete, its closeout held a human-accepted limitation, and
an optional Verify with no declared mode replaced ``closeout.md`` with ``not-complete``. The fix is
in the command and contract text, which the first group of tests pins. The second group runs
``judge.py lifecycle`` over synthetic bundles: a preserved decision keeps the lifecycle passing,
and each legitimate invalidation (reopened work, invalidated evidence, a real defect, an unmet
mandatory obligation on an old spec) still blocks.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "templates" / "closeout-contract.md"
VERIFY = ROOT / "templates" / "commands" / "verify.md"
CLOSEOUT = ROOT / "templates" / "commands" / "closeout.md"
BUNDLES = ROOT / "tests" / "fixtures" / "closeout-carry-forward"
JUDGE = ROOT / "scripts" / "judge.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _flat(path: Path) -> str:
    return " ".join(_read(path).replace("**", "").split())


# --- command and contract text --------------------------------------------------------------


def test_contract_defines_prior_decision_handling_without_new_machinery() -> None:
    text = _flat(CONTRACT)

    assert "## 7.1 Prior Decisions" in _read(CONTRACT)
    assert "reading the prior `closeout.md` before anything replaces it" in text
    assert "No new artifact, gate, or state file is involved" in text
    assert "verbatim and within its original scope" in text
    assert "a missing `accepted_by` is never filled in by the agent, a standing instruction, or inference" in text


def test_contract_lists_every_legitimate_invalidation() -> None:
    text = _flat(CONTRACT)

    for trigger in (
        "Inputs changed materially",
        "The work changed",
        "The evidence it rested on is no longer valid",
        "A real defect appeared",
        "A mandatory obligation is unmet",
    ):
        assert trigger in text, trigger
    assert "nothing here preserves a prior `complete` as such" in text
    assert "Stale evidence is never silently current" in text


def test_unchanged_optional_check_leaves_closeout_untouched() -> None:
    contract = _flat(CONTRACT)
    verify = _flat(VERIFY)
    closeout = _flat(CLOSEOUT)

    assert "leaves `closeout.md` untouched" in contract
    assert "does not create a closeout artifact merely to represent a check that supplied no evidence" in contract
    assert "leave `closeout.md` as it is" in verify
    assert "A run with no declared mode supplies no new evidence" in verify
    assert "leave `closeout.md` untouched rather than re-stamping it" in closeout


def test_verify_and_closeout_read_the_prior_closeout_before_replacing_it() -> None:
    for path in (VERIFY, CLOSEOUT):
        text = _flat(path)
        assert "prior `gates/closeout.md`" in text, path.name
        assert "Replace any prior `closeout.md`" not in text, path.name
        assert "verbatim" in text and "Never write an `accepted_by` the human did not give" in text, path.name


def test_pre_contract_specs_are_neither_reclassified_nor_waived() -> None:
    text = _flat(CONTRACT)

    assert "An unannotated criterion is still read as a `requirement`" in text
    assert "never relabeled `target`, `hypothesis`, or `accepted`" in text
    assert "a current mandatory obligation is never waived because the spec predates it" in text
    assert "A missing `evaluated_commit` falls back to `generated`" in text
    assert "not fabricated, back-dated, or reconstructed" in text


def test_the_anti_laundering_and_blocking_rules_remain() -> None:
    for path in (CONTRACT, VERIFY, CLOSEOUT):
        text = _read(path)
        assert "Blocking Defect" in text or "blocking-defect" in text, path.name
    assert "Classification is not a dodge" in _read(VERIFY)
    assert "MUST NOT be reclassified as a `hypothesis` or a `target`" in _read(CONTRACT)


# --- lifecycle behaviour over synthetic bundles --------------------------------------------------


def _lifecycle(tmp_path: Path, bundle: str) -> dict:
    feature = tmp_path / "feature"
    shutil.copytree(BUNDLES / bundle, feature)
    proc = subprocess.run(
        [sys.executable, str(JUDGE), "lifecycle", "--repo-root", str(tmp_path), "--feature-dir", str(feature)],
        cwd=tmp_path, capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL,
    )
    payload = json.loads(proc.stdout)
    assert proc.returncode == (0 if payload["status"] == "pass" else 1), proc.stdout
    return payload


def _codes(payload: dict) -> list[str]:
    return [failure["code"] for failure in payload["failures"]]


@pytest.mark.parametrize("bundle", ["preserved-accepted-limitation", "preserved-pre-contract-shape"])
def test_preserved_decision_keeps_the_lifecycle_passing(tmp_path: Path, bundle: str) -> None:
    payload = _lifecycle(tmp_path, bundle)

    assert payload["status"] == "pass", payload
    assert payload["failures"] == []


@pytest.mark.parametrize(
    ("bundle", "expected"),
    [
        ("invalidated-reopened-work", ["incomplete-tasks"]),
        ("invalidated-evidence", ["verify-not-passed"]),
        ("real-blocking-defect", ["closeout-not-complete"]),
        ("legacy-requirement-not-waived", ["verify-not-passed", "closeout-missing"]),
    ],
)
def test_legitimate_invalidation_still_blocks(tmp_path: Path, bundle: str, expected: list[str]) -> None:
    payload = _lifecycle(tmp_path, bundle)

    assert payload["status"] == "fail"
    assert _codes(payload) == expected


def test_spec_129_sequence_does_not_manufacture_an_incomplete_lifecycle(tmp_path: Path) -> None:
    # Before: the prior complete closeout with its accepted limitation stands.
    assert _lifecycle(tmp_path, "preserved-accepted-limitation")["status"] == "pass"

    # The retired behavior: an optional Verify replaced the artifact from "no evidence".
    shutil.rmtree(tmp_path / "feature")
    broken = tmp_path / "broken"
    shutil.copytree(BUNDLES / "preserved-accepted-limitation", broken)
    closeout = broken / "gates" / "closeout.md"
    closeout.write_text(
        _read(closeout).replace("decision: complete", "decision: not-complete"), encoding="utf-8"
    )
    proc = subprocess.run(
        [sys.executable, str(JUDGE), "lifecycle", "--repo-root", str(tmp_path), "--feature-dir", str(broken)],
        cwd=tmp_path, capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL,
    )
    assert _codes(json.loads(proc.stdout)) == ["closeout-not-complete"]
    # The commands now forbid that rewrite: no new evidence and nothing changed means untouched.
    assert "leave `closeout.md` as it is" in _flat(VERIFY)
