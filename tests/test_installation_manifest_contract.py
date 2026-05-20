"""Contract validation for agent-specific installation manifest checks."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from devspark_cli._template import validate_installation_manifest


def _write_command(repo: Path, name: str) -> None:
    command_dir = repo / ".devspark" / "defaults" / "commands"
    command_dir.mkdir(parents=True, exist_ok=True)
    (command_dir / f"devspark.{name}.md").write_text(f"# {name}\n", encoding="utf-8")


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo = Path(temp_dir)
        _write_command(repo, "specify")
        _write_command(repo, "plan")

        copilot_dir = repo / ".github" / "agents"
        copilot_dir.mkdir(parents=True, exist_ok=True)
        (copilot_dir / "devspark.specify.agent.md").write_text("# specify\n", encoding="utf-8")
        (copilot_dir / "devspark.plan.agent.md").write_text("# plan\n", encoding="utf-8")

        codex_dir = repo / ".codex" / "prompts"
        codex_dir.mkdir(parents=True, exist_ok=True)
        (codex_dir / "devspark.specify.md").write_text("# specify\n", encoding="utf-8")
        (codex_dir / "devspark.plan.md").write_text("# plan\n", encoding="utf-8")

        copilot = validate_installation_manifest(repo, "copilot")
        assert copilot["valid"]
        assert copilot["shim_count"] == 2
        assert copilot["shim_dir"].endswith(".github\\agents") or copilot["shim_dir"].endswith(".github/agents")

        codex = validate_installation_manifest(repo, "codex")
        assert codex["valid"]
        assert codex["shim_count"] == 2
        assert codex["shim_dir"].endswith(".codex\\prompts") or codex["shim_dir"].endswith(".codex/prompts")

        (codex_dir / "devspark.plan.md").unlink()
        codex_missing = validate_installation_manifest(repo, "codex")
        assert not codex_missing["valid"]
        assert codex_missing["missing_shims"] == ["plan"]

    print("Installation manifest contract validated.")


if __name__ == "__main__":
    main()
