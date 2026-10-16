# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Pytest wrapper that executes every main()-style contract script.

Several tests/test_*_contract.py files are standalone scripts (a bare
``main()`` guarded by ``__name__ == "__main__"`` with no ``def test_``
functions). Pytest collects those files but runs nothing in them, so
their assertions were silently skipped by the CI test gate. This wrapper
runs each one in a subprocess and fails if any exits non-zero.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

CONTRACT_SCRIPTS = sorted(
    path
    for path in (ROOT / "tests").glob("test_*_contract.py")
    if "def test_" not in path.read_text(encoding="utf-8")
)


def test_contract_scripts_discovered() -> None:
    assert CONTRACT_SCRIPTS, "expected at least one main()-style contract script"


@pytest.mark.parametrize("script", CONTRACT_SCRIPTS, ids=lambda p: p.stem)
def test_contract_script(script: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        timeout=300,
    )
    assert result.returncode == 0, (
        f"{script.name} failed (exit {result.returncode})\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
