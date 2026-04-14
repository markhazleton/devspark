"""Static validation for persisted gate artifact contract text."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def main() -> None:
    analyze = _read("templates/commands/analyze.md")
    critic = _read("templates/commands/critic.md")
    checklist = _read("templates/commands/checklist.md")
    create_pr = _read("templates/commands/create-pr.md")
    specify = _read("templates/commands/specify.md")
    clarify = _read("templates/commands/clarify.md")
    tasks_template = _read("templates/tasks-template.md")
    plan_template = _read("templates/plan-template.md")
    spec_validation_contract = _read("templates/spec-validation-contract.md")

    assert "FEATURE_DIR/gates/analyze.md" in analyze
    assert "FEATURE_DIR/gates/critic.md" in critic
    assert "FEATURE_DIR/gates/checklist.md" in checklist
    assert "Gate Acknowledgements" in create_pr
    assert "quickfix record" in create_pr.lower()
    assert "shared specification validation contract" in specify.lower()
    assert "spec-validation-contract.md" in specify
    assert "shared specification validation contract" in clarify.lower()
    assert "spec-validation-contract.md" in clarify
    assert "## 1. Frontmatter Contract" in spec_validation_contract
    assert "## 3. Required Sections By Route" in spec_validation_contract
    assert "## 5. Clarification Session Rules" in spec_validation_contract
    assert "## Gate Acknowledgements" in tasks_template
    assert "gates/" in plan_template

    print("Prompt gate contract validated.")


if __name__ == "__main__":
    main()