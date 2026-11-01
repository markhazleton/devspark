# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests guarding lifecycle parity across quickfix / quick-spec / full-spec routes.

Prevents regression of the class of bug where a downstream command (critic,
analyze, verify, implement, next) silently only works for full-spec because a
shared script unconditionally requires plan.md/tasks.md, or because the
command's own prose never learned to resolve/degrade for the lighter routes.

Run with: python tests/test_lifecycle_parity_contract.py
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def _validate_prereq_scripts_dont_hard_require_plan() -> None:
    bash_script = _read("scripts/bash/check-prerequisites.sh")
    ps_script = _read("scripts/powershell/check-prerequisites.ps1")

    # plan.md must only be required behind an opt-in flag, mirroring the
    # existing tasks.md/--require-tasks pattern -- never unconditional.
    assert "--require-plan" in bash_script, "check-prerequisites.sh missing --require-plan flag"
    assert "-RequirePlan" in ps_script, "check-prerequisites.ps1 missing -RequirePlan switch"
    assert (
        'if $REQUIRE_PLAN && [[ ! -f "$IMPL_PLAN" && ! "$CURRENT_BRANCH" =~ ^[0-9]{3}-work- ]]; then'
        in bash_script
    ), "check-prerequisites.sh must gate the plan.md check on REQUIRE_PLAN and exempt work branches"
    assert (
        "if ($RequirePlan -and -not (Test-Path $paths.IMPL_PLAN -PathType Leaf)"
        " -and $paths.CURRENT_BRANCH -notmatch '^\\d{3}-work-') {" in ps_script
    ), "check-prerequisites.ps1 must gate the plan.md check on -RequirePlan and exempt work branches"

    # Commands that only quick-spec/quickfix ever run (critic, analyze, verify,
    # implement) must NOT pass --require-plan/-RequirePlan -- otherwise their
    # own documented degradation logic is unreachable. Analyze and Critic also
    # degrade without tasks.md, so neither may hard-require it.
    for cmd in ("critic.md", "analyze.md", "verify.md", "implement.md"):
        body = _read(f"templates/commands/{cmd}")
        assert "--require-plan" not in body, f"{cmd} must not hard-require plan.md (breaks quick-spec/quickfix)"
        assert "-RequirePlan" not in body, f"{cmd} must not hard-require plan.md (breaks quick-spec/quickfix)"
    for cmd in ("critic.md", "analyze.md"):
        body = _read(f"templates/commands/{cmd}")
        assert "--require-tasks" not in body, f"{cmd} must not hard-require tasks.md (breaks its degradation tiers)"
        assert "-RequireTasks" not in body, f"{cmd} must not hard-require tasks.md (breaks its degradation tiers)"

    # Legacy task generation still fails fast without a plan; work branches are exempt in the scripts.
    tasks = _read("templates/commands/tasks.md")
    assert "--require-plan" in tasks
    assert "-RequirePlan" in tasks

    # Exporting temporary task plans into a durable issue tracker is disabled.
    task_export = _read("templates/commands/taskstoissues.md")
    assert "Deprecated Behavior" in task_export
    assert "no longer performs writes" in task_export
    assert "issue_write" not in task_export


def _validate_quickfix_feature_spec_resolution() -> None:
    bash_common = _read("scripts/bash/common.sh")
    ps_common = _read("scripts/powershell/common.ps1")

    # FEATURE_SPEC must resolve to the quickfix record file, not a nonexistent
    # spec.md, when FEATURE_DIR resolves to the quickfixes directory.
    assert "feature_spec=\"$feature_dir/$current_branch.md\"" in bash_common, (
        "common.sh get_feature_paths must resolve FEATURE_SPEC to the quickfix record file"
    )
    assert "$featureSpec = Join-Path $featureDir \"$currentBranch.md\"" in ps_common, (
        "common.ps1 Get-FeaturePathsEnv must resolve FEATURE_SPEC to the quickfix record file"
    )


def _validate_critic_analyze_quickfix_tier() -> None:
    critic = _read("templates/commands/critic.md")
    analyze = _read("templates/commands/analyze.md")

    for body, label in ((critic, "critic.md"), (analyze, "analyze.md")):
        assert "QUICKFIX-ONLY" in body, f"{label} missing the QUICKFIX-ONLY degradation tier"
        assert "quickfix record" in body, f"{label} must describe resolving a quickfix record"


def _validate_implement_route_awareness() -> None:
    implement = _read("templates/commands/implement.md")

    assert "Quick-Spec Route" in implement, "implement.md missing the Quick-Spec Route"
    assert "Quickfix Route" in implement, "implement.md missing the Quickfix Route"
    assert "## Action Plan" in implement, "implement.md Quick-Spec Route must reference the spec's Action Plan"
    assert "## Validation Checklist" in implement, (
        "implement.md Quickfix Route must reference the quickfix record's Validation Checklist"
    )


def _validate_quick_spec_next_step() -> None:
    quick_template = _read("templates/quick-spec-template.md")
    create_pr = _read("templates/commands/create-pr.md")

    assert "recommended_next_step: implement" in quick_template, (
        "quick-spec-template.md must point recommended_next_step at implement, "
        "not the heavy plan.md workflow its own contract never uses"
    )
    assert "Missing planning records are normal" in create_pr
    assert "route back to `/devspark-implement`" in create_pr


def _validate_next_state_machine_route_aware() -> None:
    bash_ctx = _read("scripts/bash/next-context.sh")
    ps_ctx = _read("scripts/powershell/next-context.ps1")
    next_cmd = _read("templates/commands/next.md")

    assert "quickspec-needs-implement" in bash_ctx, "next-context.sh missing quickspec-needs-implement state"
    assert "quickspec-needs-implement" in ps_ctx, "next-context.ps1 missing quickspec-needs-implement state"
    assert "quickspec-needs-implement" in next_cmd, "next.md STATE list missing quickspec-needs-implement"


def _validate_universal_work_route() -> None:
    bash_branch = _read("scripts/bash/new-branch.sh")
    ps_branch = _read("scripts/powershell/new-branch.ps1")
    bash_common = _read("scripts/bash/common.sh")
    ps_common = _read("scripts/powershell/common.ps1")
    bash_next = _read("scripts/bash/next-context.sh")
    ps_next = _read("scripts/powershell/next-context.ps1")
    specify = _read("templates/commands/specify.md")
    implement = _read("templates/commands/implement.md")

    assert 'fix|work) ;;' in bash_branch and "@('fix', 'work')" in ps_branch
    assert 'if [[ "$TYPE" == "fix" ]]; then' in bash_branch
    assert "if ($Type -eq 'fix')" in ps_branch
    assert "^\\d{3}-work-" in ps_common and "^[0-9]{3}-work-" in bash_common
    assert "WORK_RECORD_EXISTS" in bash_next and "work-in-progress" in bash_next
    assert "$workRecordExists" in ps_next and "work-in-progress" in ps_next
    assert "WORK_COMPLETE" in bash_next and "WORK_COMPLETE" in ps_next
    assert "--type work --json --yes" in specify and "-Type work -Json -Yes" in specify
    assert "## Work Route (no planning bundle)" in implement
    assert "Perform assurance discovery as part of understanding" in specify
    assert "No Plan, Tasks, checklist, specification, or review artifact" in specify


def main() -> None:
    _validate_prereq_scripts_dont_hard_require_plan()
    _validate_quickfix_feature_spec_resolution()
    _validate_critic_analyze_quickfix_tier()
    _validate_implement_route_awareness()
    _validate_quick_spec_next_step()
    _validate_next_state_machine_route_aware()
    _validate_universal_work_route()
    print("Lifecycle parity contract validated.")


if __name__ == "__main__":
    main()
