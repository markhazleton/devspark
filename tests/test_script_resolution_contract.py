"""Validation that all stock command templates with {SCRIPT} in their body
include the 2-tier script resolution instruction.

This enforces the fix for the issue where .documentation/scripts/ overrides
were silently ignored because stock templates hardcoded .devspark/scripts/ paths.

Run with: python tests/test_script_resolution_contract.py
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
COMMANDS_DIR = ROOT / "templates" / "commands"

RESOLUTION_MARKER = "2-tier override check"


def _get_templates_with_script() -> list[Path]:
    """Return all command template files that reference {SCRIPT} in their body."""
    templates = []
    for path in sorted(COMMANDS_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        # Strip frontmatter (between first two '---' lines)
        parts = content.split("---", 2)
        body = parts[2] if len(parts) >= 3 else content
        if "{SCRIPT}" in body or "{AGENT_SCRIPT}" in body:
            templates.append(path)
    return templates


def main() -> None:
    templates_with_script = _get_templates_with_script()
    assert templates_with_script, "Expected to find command templates that use {SCRIPT}"

    missing = []
    for path in templates_with_script:
        content = path.read_text(encoding="utf-8")
        if RESOLUTION_MARKER not in content:
            missing.append(path.name)

    if missing:
        raise AssertionError(
            f"The following command templates use {{SCRIPT}} but are missing the "
            f"2-tier script resolution instruction:\n"
            + "\n".join(f"  - templates/commands/{name}" for name in missing)
        )

    print(
        f"Script resolution contract validated: "
        f"{len(templates_with_script)} templates all contain resolution instruction."
    )


if __name__ == "__main__":
    main()
