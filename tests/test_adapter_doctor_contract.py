"""Contract validation for adapter doctor capability classification.

Run with: python tests/test_adapter_doctor_contract.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from typer.testing import CliRunner


ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from devspark_cli import app


RUNNER = CliRunner()


def main() -> None:
    result = RUNNER.invoke(app, ["adapter", "doctor"], catch_exceptions=False)
    assert result.exit_code in (0, 1), result.output

    profiles = []
    for line in result.output.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        profiles.append(json.loads(line))

    assert profiles, "expected JSON adapter-doctor output"

    by_name = {profile["adapter"]: profile for profile in profiles}

    assert by_name["noop"]["state"] == "write_incompatible"
    assert by_name["noop"]["can_execute_read_only"] is True
    assert by_name["noop"]["can_execute_write"] is False

    assert by_name["manual"]["state"] == "write_approval_required"
    assert by_name["manual"]["requires_write_approval"] is True

    unknown = RUNNER.invoke(app, ["adapter", "doctor", "--adapter", "missing"], catch_exceptions=False)
    assert unknown.exit_code == 1
    payload = json.loads(unknown.output.strip())
    assert payload["adapter"] == "missing"
    assert payload["state"] == "unavailable"

    print("Adapter doctor contract validated.")


if __name__ == "__main__":
    main()
