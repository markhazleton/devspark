"""Resolve the Bash that runs the Bash twin scripts in tests, and the path form it understands.

On Windows, Git Bash is preferred. A bare ``bash`` there resolves to the WSL launcher in System32
before PATH is searched, and that launcher fails when no Linux distribution is installed, as on
CI runners. WSL is used only when Git Bash is absent, and only then are paths rewritten to /mnt.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

GIT_BASH = Path(r"C:\Program Files\Git\bin\bash.exe")


def _resolve() -> str | None:
    if os.name == "nt" and GIT_BASH.exists():
        return str(GIT_BASH)
    return shutil.which("bash")


BASH_EXE = _resolve()
IS_WSL = bool(BASH_EXE) and os.name == "nt" and BASH_EXE.lower().endswith(r"system32\bash.exe")


def to_bash_path(path: Path) -> str:
    """Return ``path`` in the form BASH_EXE accepts: /mnt/<drive>/... for WSL, forward slashes otherwise."""
    value = path.as_posix()
    if IS_WSL and len(value) > 1 and value[1] == ":":
        return f"/mnt/{value[0].lower()}{value[2:]}"
    return value
