# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for spec Product Owner TLDR requirement and script hardening.

Run with: python tests/test_spec_hardening_contract.py
"""

from __future__ import annotations

from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import tempfile

import pytest


ROOT = Path(__file__).resolve().parent.parent


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _assert_ordered(body: str, headings: list[str], label: str) -> None:
    positions = []
    search_from = 0
    for heading in headings:
        idx = body.find(heading, search_from)
        assert idx != -1, f"{label} missing required heading {heading!r} (in order)"
        positions.append((heading, idx))
        search_from = idx + len(heading)
    for (prev_heading, prev_idx), (next_heading, next_idx) in zip(positions, positions[1:]):
        assert prev_idx < next_idx, (
            f"{label} heading order violation: {prev_heading!r} must precede {next_heading!r}"
        )


def _validate_tldr() -> None:
    spec_template = _read("templates/spec-template.md")
    quick_template = _read("templates/quick-spec-template.md")
    contract = _read("templates/spec-validation-contract.md")
    skill = _read("templates/skills/write-spec/SKILL.md")
    skill_ref = _read("templates/skills/write-spec/references/spec-template.md")

    # Product Owner TLDR must be present in both templates, above the first content section.
    assert "## Product Owner TLDR" in spec_template, "full spec template missing Product Owner TLDR"
    assert "## Product Owner TLDR" in quick_template, "quick spec template missing Product Owner TLDR"

    _assert_ordered(
        spec_template,
        ["## Product Owner TLDR", "## Rationale Summary"],
        "full spec template",
    )
    _assert_ordered(
        quick_template,
        ["## Product Owner TLDR", "## Intent"],
        "quick spec template",
    )

    # Validation contract must require Product Owner TLDR first in both route structures.
    _assert_ordered(
        contract,
        [
            "### Quick Spec Required Structure",
            "`## Product Owner TLDR`",
            "`## Intent`",
        ],
        "quick spec required structure",
    )
    _assert_ordered(
        contract,
        [
            "### Full Spec Required Structure",
            "`## Product Owner TLDR`",
            "`## Rationale Summary`",
        ],
        "full spec required structure",
    )

    # Skill guidance must instruct drafting and requiring the TLDR.
    assert "Product Owner TLDR" in skill, "write-spec SKILL.md missing Product Owner TLDR guidance"
    assert "Product Owner TLDR" in skill_ref, "write-spec reference missing Product Owner TLDR section"


def _validate_template_fallback() -> None:
    ps_common = _read("scripts/powershell/common.ps1")
    bash_common = _read("scripts/bash/common.sh")

    assert "function Resolve-TemplatePath" in ps_common, "PowerShell common.ps1 missing Resolve-TemplatePath"
    assert "resolve_template_path()" in bash_common, "bash common.sh missing resolve_template_path"

    # Both resolvers must consult the full override -> installed -> source fallback chain.
    for common, token in (
        (ps_common, ".devspark.work/templates/$TemplateName"),
        (ps_common, ".devspark/templates/$TemplateName"),
        (ps_common, "templates/$TemplateName"),
        (bash_common, ".devspark.work/templates/$template_name"),
        (bash_common, ".devspark/templates/$template_name"),
        (bash_common, "templates/$template_name"),
    ):
        assert token in common, f"template resolver missing fallback path {token!r}"

    ps_create = _read("scripts/powershell/create-new-feature.ps1")
    bash_create = _read("scripts/bash/create-new-feature.sh")
    ps_plan = _read("scripts/powershell/setup-plan.ps1")
    bash_plan = _read("scripts/bash/setup-plan.sh")
    ps_new_branch = _read("scripts/powershell/new-branch.ps1")
    bash_new_branch = _read("scripts/bash/new-branch.sh")

    # create-new-feature.* is now a thin shim that delegates spec.md
    # scaffolding to new-branch.*, which is where the override -> installed ->
    # source template-fallback chain actually runs.
    assert "Resolve-TemplatePath -RepoRoot $repoRoot -TemplateName $templateName" in ps_new_branch
    assert 'resolve_template_path "$REPO_ROOT" "$TEMPLATE_NAME"' in bash_new_branch
    assert "Resolve-TemplatePath -RepoRoot $paths.REPO_ROOT -TemplateName 'plan-template.md'" in ps_plan
    assert 'resolve_template_path "$REPO_ROOT" "plan-template.md"' in bash_plan
    assert '"$SCRIPT_DIR/new-branch.ps1"' in ps_create or 'new-branch.ps1' in ps_create
    assert 'new-branch.sh' in bash_create


def _validate_branch_failfast() -> None:
    ps_create = _read("scripts/powershell/create-new-feature.ps1")
    bash_create = _read("scripts/bash/create-new-feature.sh")

    # create-new-feature.ps1 delegates branch creation to new-branch.ps1 and
    # must fail fast (propagating its exit code) rather than writing a spec
    # after a failed branch creation.
    assert "if ($exitCode -ne 0) {" in ps_create, "PowerShell create-new-feature missing exit-code check"
    assert "exit $exitCode" in ps_create

    # Bash must exit non-zero when branch creation fails (unified-delegation
    # path and the legacy multi-app fallback path both fail closed).
    assert "Aborting before writing spec" in bash_create
    assert "exit 1" in bash_create
    assert "NEW_BRANCH_EXIT" in bash_create and "exit $NEW_BRANCH_EXIT" in bash_create


def _validate_metric_accuracy() -> None:
    ps_create = _read("scripts/powershell/create-new-feature.ps1")
    bash_create = _read("scripts/bash/create-new-feature.sh")

    # The script must not fabricate a route classification it cannot know.
    assert "classification = 'full-spec'" not in ps_create, (
        "PowerShell create-new-feature must not hardcode classification metric"
    )
    assert '"classification":"full-spec"' not in bash_create, (
        "bash create-new-feature must not hardcode classification metric"
    )


def test_rationale_and_task_artifacts_do_not_copy_upstream_prose() -> None:
    spec = _read("templates/spec-template.md")
    plan = " ".join(_read("templates/plan-template.md").split())
    tasks = _read("templates/tasks-template.md")
    task_command = _read("templates/commands/tasks.md")
    checklist = _read("templates/commands/checklist.md")
    validation = _read("templates/spec-validation-contract.md")
    assurance = _read("templates/assurance-contract.md")

    assert "Consequential scope or behavior decisions and why" in spec
    assert "concise decision record" in spec
    assert "Do not accumulate research notes" in spec
    assert "Point to `research.md`" in plan
    assert "Plan-owned decisions" in plan
    assert "do not copy a generic repository tree" in plan
    assert "## Rationale Summary" not in tasks
    assert "Describe only the implementation or verification delta" in tasks
    assert "Cite requirement and acceptance IDs instead of paraphrasing their text" in tasks
    assert "Do not paraphrase requirements, acceptance scenarios, rationale" in task_command
    assert "do not restate the task list" in task_command
    assert "not document length or repeated rationale" in checklist
    assert "Item count follows the actual gaps, not a target size" in checklist
    assert "superseded alternatives, roadmap ideas" in validation
    assert "Tasks remain a" in assurance and "do not repeat rationale" in assurance


def test_authoring_rechecks_changed_requirements_against_complete_constitution_clauses() -> None:
    specify = _read("templates/commands/specify.md")
    clarify = _read("templates/commands/clarify.md")

    assert "When introducing or materially changing a requirement" in specify
    assert "complete applicable MUST/SHOULD text, including scope and embedded exceptions" in specify
    assert "Recheck changed requirements only, not settled unchanged content" in specify
    assert "surface it for owner resolution before marking the spec ready or handing off to Plan" in specify

    assert "When an accepted answer materially changes a requirement" in clarify
    assert "complete applicable MUST/SHOULD text, including embedded scope and exceptions" in clarify
    assert "Do not repeat the check for unchanged requirements" in clarify
    assert "Cite both sides of any conflict" in clarify


_TEMPLATE_BASE: Path | None = None
_TEMP_ROOT: tempfile.TemporaryDirectory | None = None


def _get_template_base() -> Path:
    global _TEMPLATE_BASE, _TEMP_ROOT
    if _TEMPLATE_BASE is None:
        _TEMP_ROOT = tempfile.TemporaryDirectory()
        _TEMPLATE_BASE = Path(_TEMP_ROOT.name) / "repo"
        feature = _TEMPLATE_BASE / ".devspark.work/specs/001-synthetic"
        feature.mkdir(parents=True)
        template = _TEMPLATE_BASE / "templates/plan-template.md"
        template.parent.mkdir()
        template.write_bytes(b"# Template\n")
        subprocess.run(["git", "init", "-q", "-b", "001-synthetic", str(_TEMPLATE_BASE)], check=True, timeout=15, stdin=subprocess.DEVNULL)
    return _TEMPLATE_BASE


@pytest.mark.parametrize("shell", ["pwsh", "bash"])
@pytest.mark.parametrize("existing", [None, b"", b"# Template\n", b"# Authored\r\nKeep this.\r\n", b"\xef\xbb\xbf# Authored\r\n"])
def test_setup_plan_preserves_bytes_until_explicit_reset(tmp_path, shell, existing):
    executable = shutil.which("pwsh") if shell == "pwsh" else (
        "C:/Program Files/Git/bin/bash.exe" if os.name == "nt" else shutil.which("bash")
    )
    if not executable or not Path(executable).exists():
        pytest.skip(f"{shell} unavailable")
    repo = tmp_path / "repo"
    shutil.copytree(_get_template_base(), repo)
    plan = repo / ".devspark.work/specs/001-synthetic/plan.md"
    template = repo / "templates/plan-template.md"
    if existing is not None:
        plan.write_bytes(existing)
    env = {**os.environ, "DEVSPARK_FEATURE": "001-synthetic"}
    script = ROOT / "scripts" / ("powershell/setup-plan.ps1" if shell == "pwsh" else "bash/setup-plan.sh")
    command = [executable, "-NoProfile", "-File", str(script), "-Json"] if shell == "pwsh" else [executable, str(script), "--json"]

    def invoke(reset=False):
        result = subprocess.run(command + (["-Reset" if shell == "pwsh" else "--reset"] if reset else []),
                                cwd=repo, env=env, capture_output=True, text=True, check=True,
                                timeout=20, stdin=subprocess.DEVNULL)
        return json.loads(result.stdout[result.stdout.index("{"):])

    first = invoke()
    assert plan.read_bytes() == (template.read_bytes() if existing is None else existing)
    assert first["PLAN_EXISTS"] is (existing is not None)
    assert first["PLAN_MODE"] == ("create" if existing is None else "revise")
    assert {"FEATURE_SPEC", "IMPL_PLAN", "SPECS_DIR", "BRANCH", "HAS_GIT"} <= first.keys()
    preserved = plan.read_bytes()
    assert invoke()["PLAN_MODE"] == "revise"
    assert plan.read_bytes() == preserved
    assert invoke(reset=True)["PLAN_MODE"] == "reset"
    assert plan.read_bytes() == template.read_bytes()


def test_delta_oriented_guidance_and_release_separation() -> None:
    specify = _read("templates/commands/specify.md")
    plan = _read("templates/commands/plan.md")
    verify = _read("templates/commands/verify.md")
    closeout = _read("templates/commands/closeout.md")
    tasks = _read("templates/commands/tasks.md")
    tasks_template = _read("templates/tasks-template.md")
    preamble = _read("templates/command-preamble-contract.md")

    # Delta-oriented guidance
    assert "A DevSpark specification is not a blueprint for software" in preamble
    assert "bounded hypothesis about the" in preamble
    assert "next valuable change to working software" in preamble
    assert "make sure the new state remains a good place from which to change again" in preamble
    assert "A DevSpark specification is not a blueprint for software" in specify
    assert "Describe the bounded delta" in specify
    assert "Smallest responsible change" in plan
    assert "Keep software changeable" in plan or "easy to change again" in plan
    assert "Avoid speculative abstractions" in plan
    assert "Delta verification" in verify or "validate the intended delta" in verify

    # Specification/Release separation
    assert "A specification delivers a releasable change" in preamble
    assert "packages and distributes completed" in preamble
    assert "Tasks MUST NOT include publishing or deploying a release" in tasks
    assert "specification delivers a releasable change, not the product release itself" in tasks_template
    assert "Specification/Release Separation" in closeout


def test_engineering_judgment_hardening() -> None:
    plan = _flat(_read("templates/commands/plan.md"))
    plan_template = _flat(_read("templates/plan-template.md"))
    implement = _flat(_read("templates/commands/implement.md"))
    pr_review = _flat(_read("templates/commands/pr-review.md"))

    # Plan seam selection
    assert "Choose the right integration boundary" in plan
    assert "ownership, orchestration, and finalization boundaries" in plan
    assert "Prefer reusing an appropriate existing seam" in plan
    assert "A centralized hook is not always better" in plan
    assert "When a behavior could be integrated at an existing seam" in plan_template
    assert "repeated integration across call sites is chosen" in plan_template

    # Implement simplification without weakening contract
    assert "Simplifying implementation without weakening the contract" in implement
    assert "approved behavioral intent from incidental implementation mechanics" in implement
    assert "simplification MUST NOT silently weaken guarantees in pursuit of fewer lines" in implement
    assert "remove an approved validation rule, change failure propagation or exception behavior" in implement

    # PR Review accidental complexity
    assert "Accidental Complexity & Duplication Review" in pr_review
    assert "Repeated wiring" in pr_review
    assert "Redundant processing" in pr_review
    assert "A smaller implementation that drops validation guarantees or changes exception behavior is NOT equivalent" in pr_review
    assert "Line count, file count, or abstraction count are NEVER automatic failure conditions" in pr_review


def main() -> None:
    _validate_tldr()
    _validate_template_fallback()
    _validate_branch_failfast()
    _validate_metric_accuracy()
    test_delta_oriented_guidance_and_release_separation()
    test_engineering_judgment_hardening()
    print("Spec hardening contract validated.")


if __name__ == "__main__":
    main()
