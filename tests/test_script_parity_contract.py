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

    print('Script parity contract validated.')


if __name__ == '__main__':
    main()