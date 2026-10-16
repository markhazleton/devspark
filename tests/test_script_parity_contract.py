# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Validation for changed Bash/PowerShell script-pair contract parity.

Run with: python tests/test_script_parity_contract.py
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding='utf-8')


def main() -> None:
    bash_common = _read('scripts/bash/common.sh')
    ps_common = _read('scripts/powershell/common.ps1')
    bash_update = _read('scripts/bash/update-agent-context.sh')
    ps_update = _read('scripts/powershell/update-agent-context.ps1')
    bash_create_pr = _read('scripts/bash/create-pr.sh')
    ps_create_pr = _read('scripts/powershell/create-pr.ps1')
    bash_release_context = _read('scripts/bash/release-context.sh')
    ps_release_context = _read('scripts/powershell/release-context.ps1')
    release_engine = _read('scripts/release-context.py')
    bash_address_pr_review = _read('scripts/bash/address-pr-review.sh')
    ps_address_pr_review = _read('scripts/powershell/address-pr-review.ps1')
    bash_pr_context = _read('scripts/bash/get-pr-context.sh')
    ps_pr_context = _read('scripts/powershell/get-pr-context.ps1')

    assert 'get_markdown_frontmatter()' in bash_common
    assert 'get_markdown_frontmatter_value()' in bash_common
    assert 'function Get-MarkdownFrontmatter' in ps_common
    assert 'function Get-MarkdownFrontmatterValue' in ps_common

    assert 'DEVSPARK_METRICS_ENABLED:-false' in bash_common
    assert "$env:DEVSPARK_METRICS_ENABLED -ne 'true'" in ps_common

    assert 'SHARED_CONTEXT_START="<!-- DEVSPARK SHARED CONTEXT:START -->"' in bash_update
    assert "$SHARED_CONTEXT_START = '<!-- DEVSPARK SHARED CONTEXT:START -->'" in ps_update
    assert 'agents-registry.json' in bash_update
    assert 'agents-registry.json' in ps_update

    for token in ('gate_acknowledgements', 'quickfix_record', 'required_gates', 'recommended_next_step'):
        assert token in bash_create_pr
        assert token in ps_create_pr

    assert '../release-context.py' in bash_release_context
    assert "'release-context.py'" in ps_release_context
    assert '../release-archive.py' in _read('scripts/bash/release-archive.sh')
    assert "'release-archive.py'" in _read('scripts/powershell/release-archive.ps1')
    for token in ('RELEASE_FROM', 'CHANGED_FILES', 'KNOWLEDGE_CHANGED', 'PLANNING_LEAKS'):
        assert token in release_engine
    for removed in ('RECOVERED_SPECS', 'RECOVERED_QUICKFIXES', 'ARCHIVE_RECOVERY_USED'):
        assert removed not in release_engine

    for token in ('Code commit gate failed', 'Review commit gate failed'):
        assert token in bash_address_pr_review
        assert token in ps_address_pr_review

    for token in ('.knowledge/governance/constitution.md', '.devspark.work/specs/', '.devspark.work/pr-review'):
        assert token in bash_pr_context, f'bash get-pr-context missing {token!r}'
    for token in ('.knowledge\\governance\\constitution.md', '.devspark.work\\specs\\', '.devspark.work\\pr-review'):
        assert token in ps_pr_context, f'PowerShell get-pr-context missing {token!r}'

    # commit-audit.* parity: anonymized contributor roles and JSON contract
    bash_commit_audit = _read('scripts/bash/commit-audit.sh')
    ps_commit_audit = _read('scripts/powershell/commit-audit.ps1')
    for token in ('author_role', 'report_path', 'monthly_velocity', 'Contributor'):
        assert token in bash_commit_audit, f'bash commit-audit missing {token!r}'
        assert token in ps_commit_audit, f'ps commit-audit missing {token!r}'

    bash_shims = _read('scripts/bash/generate-atomic-shims.sh')
    ps_shims = _read('scripts/powershell/generate-atomic-shims.ps1')
    assert '--check' in bash_shims
    assert '$Check' in ps_shims or '-Check' in ps_shims
    for token in ('disable-model-invocation: true', 'user-invocable: true', '.github/skills',
                  'templates/consumer-skills', 'eng/skills/source-stop',
                  'missing source-only stop body', 'Orphaned skill entry point'):
        assert token in bash_shims, f'bash generate-atomic-shims missing {token!r}'
        assert token in ps_shims, f'ps generate-atomic-shims missing {token!r}'
    for token in ('audience: expert', 'category: legacy-command', 'templates/prompts', '.github/agents'):
        assert token not in bash_shims, f'bash generate-atomic-shims still carries {token!r}'
        assert token not in ps_shims, f'ps generate-atomic-shims still carries {token!r}'

    # workitem.* parity: the vocabulary a caller depends on must be spelled the same
    # in both shells. Flag syntax stays shell-idiomatic, but every operation name, every
    # machine-readable code, and every response key must be literally identical -- a caller
    # branching on them cannot know which shell produced the line it is reading.
    bash_workitem = _read('scripts/bash/workitem.sh')
    ps_workitem = _read('scripts/powershell/workitem.ps1')

    for operation in (
        'check', 'read', 'propose-update', 'apply-update', 'comment',
        'propose-create', 'apply-create', 'verify-link',
    ):
        assert operation in bash_workitem, f'bash workitem.sh missing operation {operation!r}'
        assert operation in ps_workitem, f'ps workitem.ps1 missing operation {operation!r}'

    for code in (
        'context_unresolved', 'cli_missing', 'extension_missing',
        'auth_failed', 'item_unresolvable', 'type_unsupported',
    ):
        assert code in bash_workitem, f'bash workitem.sh missing error code {code!r}'
        assert code in ps_workitem, f'ps workitem.ps1 missing error code {code!r}'

    for code in (
        'area_mismatch', 'story_points_unsupported', 'iteration_missing',
        'content_truncated', 'fixture_mode',
    ):
        assert code in bash_workitem, f'bash workitem.sh missing warning code {code!r}'
        assert code in ps_workitem, f'ps workitem.ps1 missing warning code {code!r}'

    # The confirmation and revision flags gate every write, so a divergence in either
    # name is the difference between a guarded write and an unguarded one.
    assert '--confirmed' in bash_workitem
    assert '$Confirmed' in ps_workitem
    assert '--rev' in bash_workitem
    assert '$Rev' in ps_workitem
    assert 'stale_revision' in bash_workitem
    assert 'stale_revision' in ps_workitem

    # The argument surface the contract declares. Flag spelling is per-shell, but a name
    # present in one shell and absent in the other is a caller who cannot switch platforms.
    for bash_flag, ps_param in (
        ('--url', '$Url'),
        ('--field', '$Field'),
        ('--value', '$Value'),
        ('--text', '$Text'),
        ('--type', '$Type'),
        ('--title', '$Title'),
        ('--reference', '$Reference'),
    ):
        assert bash_flag in bash_workitem, f'bash workitem.sh missing {bash_flag!r}'
        assert ps_param in ps_workitem, f'ps workitem.ps1 missing {ps_param!r}'

    # §VI Platform Parity (MUST): every .sh must have a matching .ps1 and vice versa
    bash_dir = ROOT / 'scripts' / 'bash'
    ps_dir = ROOT / 'scripts' / 'powershell'
    bash_stems = {p.stem for p in bash_dir.glob('*.sh')}
    ps_stems = {p.stem for p in ps_dir.glob('*.ps1')}
    bash_only = bash_stems - ps_stems
    ps_only = ps_stems - bash_stems
    assert not bash_only, (
        f'Constitution §VI violation — Bash scripts have no PowerShell counterpart: {sorted(bash_only)}'
    )
    assert not ps_only, (
        f'Constitution §VI violation — PowerShell scripts have no Bash counterpart: {sorted(ps_only)}'
    )

    # new-branch.* parity: identical
    # options/output-contract surface across both shells, even though the flag
    # syntax itself is per-shell-idiomatic (PowerShell -Type vs Bash --type).
    bash_new_branch = _read('scripts/bash/new-branch.sh')
    ps_new_branch = _read('scripts/powershell/new-branch.ps1')

    bash_new_branch_flags = ('--type', '--short-name', '--number', '--json', '--dry-run', '--yes', '--help')
    ps_new_branch_flags = ('$Type', '$ShortName', '$Number', '$Json', '$DryRun', '$Yes', '$Help')
    for flag in bash_new_branch_flags:
        assert flag in bash_new_branch, f'bash new-branch.sh missing flag {flag!r}'
    for flag in ps_new_branch_flags:
        assert flag in ps_new_branch, f'ps new-branch.ps1 missing param {flag!r}'

    for json_field in ('BRANCH_NAME', 'NUMBER', 'TYPE', 'ARTIFACT_PATH', 'HAS_GIT', 'SWITCHED'):
        assert json_field in bash_new_branch, f'bash new-branch.sh missing JSON field {json_field!r}'
        assert json_field in ps_new_branch, f'ps new-branch.ps1 missing JSON field {json_field!r}'

    # Exit codes: 0 ok | 1 usage/type/invalid-ref | 2 collision | 3 empty slug
    assert 'die() {' in bash_new_branch or 'die ' in bash_new_branch
    assert 'Exit-WithError' in ps_new_branch
    assert 'check-ref-format' in bash_new_branch
    assert 'check-ref-format' in ps_new_branch
    assert 'refusing to switch branches without confirmation' in bash_new_branch
    assert 'refusing to switch branches without confirmation' in ps_new_branch

    # check-planning-references.* parity: the deterministic backstop for command-preamble-
    # contract.md §0's one-way traceability rule. Same JSON keys, same finding vocabulary, same
    # flag surface across both shells -- a caller (implement.md, CI) must not have to special-case
    # which shell produced the result.
    bash_check_refs = _read('scripts/bash/check-planning-references.sh')
    ps_check_refs = _read('scripts/powershell/check-planning-references.ps1')

    for token in (
        'branch_findings', 'id_findings', 'linkage_findings', 'PLANNING-REF', 'LINKAGE-GAP',
    ):
        assert token in bash_check_refs, f'bash check-planning-references.sh missing {token!r}'
        assert token in ps_check_refs, f'ps check-planning-references.ps1 missing {token!r}'

    for bash_flag, ps_param in (
        ('--repo-root', '$RepoRoot'),
        ('--branch', '$Branch'),
        ('--include-tests', '$IncludeTests'),
        ('--json', '$Json'),
    ):
        assert bash_flag in bash_check_refs, f'bash check-planning-references.sh missing {bash_flag!r}'
        assert ps_param in ps_check_refs, f'ps check-planning-references.ps1 missing {ps_param!r}'

    bash_drift = _read('scripts/bash/generate-knowledge-index.sh')
    ps_drift = _read('scripts/powershell/generate-knowledge-index.ps1')
    for bash_flag, ps_param in (
        ('--detect-drift', '$DetectDrift'),
        ('--full-inventory', '$FullInventory'),
        ('--base', '$Base'),
        ('--head', '$Head'),
        ('--report-output', '$ReportOutput'),
        ('--currency-report', '$CurrencyReport'),
        ('--currency-days', '$CurrencyDays'),
        ('--prune-baselines', '$PruneBaselines'),
    ):
        assert bash_flag in bash_drift, f'bash drift wrapper missing {bash_flag!r}'
        assert ps_param in ps_drift, f'PowerShell drift wrapper missing {ps_param!r}'

    print('Script parity contract validated.')


if __name__ == '__main__':
    main()
