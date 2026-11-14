# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for the PowerShell 7 floor of the helper scripts.

The scripts use PowerShell 7 syntax and behavior. A `#requires` directive turns an unsupported
host into one readable version error instead of a parse error somewhere in the file.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = sorted((ROOT / "scripts" / "powershell").glob("*.ps1"))
FLOOR = re.compile(r"^#requires\s+-Version\s+7(?:\.\d+)?\s*$", re.IGNORECASE)
HEADER_LINES = 6


def test_every_powershell_helper_declares_the_seven_floor_in_its_header():
    assert SCRIPTS, "no PowerShell helpers found"
    missing = [
        script.name
        for script in SCRIPTS
        if not any(FLOOR.match(line) for line in script.read_text(encoding="utf-8").splitlines()[:HEADER_LINES])
    ]
    assert not missing, f"scripts without '#requires -Version 7.0' in their first {HEADER_LINES} lines: {missing}"


def _windows_powershell() -> str | None:
    executable = shutil.which("powershell") if sys.platform == "win32" else None
    if executable is None:
        return None
    version = subprocess.run(
        [executable, "-NoProfile", "-Command", "$PSVersionTable.PSVersion.Major"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return executable if version.stdout.strip() == "5" else None


WINDOWS_POWERSHELL = _windows_powershell()


@pytest.mark.skipif(WINDOWS_POWERSHELL is None, reason="Windows PowerShell 5.1 is not available")
def test_windows_powershell_stops_with_a_version_error_not_a_parse_error():
    # common.ps1 uses the `??` operator, which Windows PowerShell cannot parse.
    result = subprocess.run(
        [WINDOWS_POWERSHELL, "-NoProfile", "-File", str(ROOT / "scripts" / "powershell" / "common.ps1")],
        capture_output=True,
        text=True,
        timeout=60,
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "#requires" in output
    assert "Unexpected token" not in output
