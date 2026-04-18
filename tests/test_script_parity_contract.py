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
    bash_archive = _read('scripts/bash/archive-context.sh')
    ps_archive = _read('scripts/powershell/archive-context.ps1')
    bash_release_context = _read('scripts/bash/release-context.sh')
    ps_release_context = _read('scripts/powershell/release-context.ps1')
    bash_release_history = _read('scripts/bash/release-history-context.sh')
    ps_release_history = _read('scripts/powershell/release-history-context.ps1')

    assert 'get_markdown_frontmatter()' in bash_common
    assert 'get_markdown_frontmatter_value()' in bash_common
    assert 'function Get-MarkdownFrontmatter' in ps_common
    assert 'function Get-MarkdownFrontmatterValue' in ps_common

    assert 'SHARED_CONTEXT_START="<!-- DEVSPARK SHARED CONTEXT:START -->"' in bash_update
    assert "$SHARED_CONTEXT_START = '<!-- DEVSPARK SHARED CONTEXT:START -->'" in ps_update
    assert 'agents-registry.json' in bash_update
    assert 'agents-registry.json' in ps_update

    for token in ('gate_acknowledgements', 'quickfix_record', 'required_gates', 'recommended_next_step'):
        assert token in bash_create_pr
        assert token in ps_create_pr

    assert 'harvest.sh' in bash_archive
    assert '--scope=docs' in bash_archive
    assert 'jq' not in bash_archive
    assert 'harvest.ps1' in ps_archive
    assert '-Scope docs' in ps_archive

    assert 'release-history-context.sh' in bash_release_context
    assert 'ARCHIVE_RECOVERY_USED' in bash_release_context
    assert 'RELEASE_FROM' in bash_release_context
    assert 'MERGED_PR_COUNT' in bash_release_context
    assert 'PR_REVIEW_SUMMARY' in bash_release_context
    assert 'release-history-context.ps1' in ps_release_context
    assert 'ARCHIVE_RECOVERY_USED' in ps_release_context
    assert 'RELEASE_FROM' in ps_release_context
    assert 'MERGED_PR_COUNT' in ps_release_context
    assert 'PR_REVIEW_SUMMARY' in ps_release_context

    assert 'RECOVERED_SPECS' in bash_release_history
    assert 'RECOVERED_QUICKFIXES' in bash_release_history
    assert 'MERGED_PR_NUMBERS' in bash_release_history
    assert 'PR_REVIEW_SUMMARY' in bash_release_history
    assert 'RECOVERED_SPECS' in ps_release_history
    assert 'RECOVERED_QUICKFIXES' in ps_release_history
    assert 'MERGED_PR_NUMBERS' in ps_release_history
    assert 'PR_REVIEW_SUMMARY' in ps_release_history

    # T064: run-workflow.* and generate-atomic-shims.* parity
    bash_run = _read('scripts/bash/run-workflow.sh')
    ps_run = _read('scripts/powershell/run-workflow.ps1')
    assert 'python -m devspark_cli run' in bash_run
    assert 'python -m devspark_cli run' in ps_run

    bash_shims = _read('scripts/bash/generate-atomic-shims.sh')
    ps_shims = _read('scripts/powershell/generate-atomic-shims.ps1')
    assert '--check' in bash_shims
    assert '$Check' in ps_shims or '-Check' in ps_shims
    for token in ('audience: expert', 'exposed: false', 'category: legacy-command'):
        assert token in bash_shims, f'bash generate-atomic-shims missing {token!r}'
        assert token in ps_shims, f'ps generate-atomic-shims missing {token!r}'

    print('Script parity contract validated.')


if __name__ == '__main__':
    main()