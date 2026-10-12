# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
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
    preamble = _read("templates/command-preamble-contract.md")
    implement = _read("templates/commands/implement.md")
    tasks = _read("templates/commands/tasks.md")
    quickfix = _read("templates/commands/quickfix.md")
    tasks_template = _read("templates/tasks-template.md")
    explain = _read("templates/commands/explain.md")
    analyze = _read("templates/commands/analyze.md")

    assert "FEATURE_DIR/gates/analyze.md" in analyze
    assert "FEATURE_DIR/gates/critic.md" in critic
    assert "FEATURE_DIR/gates/checklist.md" in checklist
    assert "Gate Acknowledgements" in create_pr
    assert "quickfix record" in create_pr.lower()
    assert "advisory-only noise" in create_pr.lower()
    assert "test signal wording" in create_pr.lower()
    assert "shared specification validation contract" in specify.lower()
    assert "spec-validation-contract.md" in specify
    assert "shared specification validation contract" in clarify.lower()
    assert "spec-validation-contract.md" in clarify
    assert "## 1. Frontmatter Contract" in spec_validation_contract
    assert "## 3. Required Sections By Route" in spec_validation_contract
    assert "## 5. Clarification Session Rules" in spec_validation_contract
    assert "## Gate Acknowledgements" in tasks_template
    assert "gates/" in plan_template

    assert "Traceability is strictly one-directional" in preamble
    assert "code_ref` may\n  name both production and test files" in preamble
    assert "Every implementation task or checklist item that changes behavior MUST record all affected" in preamble
    assert "A durable `.knowledge/` node's `source_of_truth` or evidence" in preamble
    assert "code_ref` includes all production and test files" in implement
    assert "every affected production-code path, test path, and current `.knowledge/` path" in implement
    assert "neither durable output may point back" in tasks
    assert "code_ref` MUST list every affected production-code and test file" in tasks
    assert "never reference the temporary quickfix record from a durable file" in quickfix
    assert "Every generated task ends with `(code_ref: pending | knowledge_ref: pending)`" in tasks_template
    assert "ask targeted clarification questions before proposing a durable update" in explain
    assert "Explain is read-only by default" in explain
    assert "never combine two actions, or an action and a trace save, into one" in explain
    assert "only when the developer asked for one and a concrete remediation exists" in explain
    assert "never put a spec, plan, task, quickfix" in explain
    assert "never from durable `.knowledge/` documents" in analyze

    print("Prompt gate contract validated.")


if __name__ == "__main__":
    main()