"""Validation for registry-driven release packaging contracts.

Run with: python tests/test_release_registry_contract.py
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def main() -> None:
    bash_release = _read('.github/workflows/scripts/create-release-packages.sh')
    ps_release = _read('.github/workflows/scripts/create-release-packages.ps1')
    bash_publish = _read('.github/workflows/scripts/create-github-release.sh')
    ps_publish = _read('.github/workflows/scripts/create-github-release.ps1')
    registry = _read('agents-registry.json')

    assert '"version": 1' in registry
    assert 'AGENT_REGISTRY_FILE="agents-registry.json"' in bash_release
    assert 'echo "version: ${NEW_VERSION#v}"' in bash_release
    assert 'RELEASE_DATE=$(date +%F)' in bash_release
    assert '> "$DEVSPARK_DIR/VERSION"' in bash_release
    assert '$AgentRegistryFile = "agents-registry.json"' in ps_release
    assert '$versionNoV = $Version -replace' in ps_release
    assert "$installedDate = Get-Date -Format 'yyyy-MM-dd'" in ps_release
    assert 'Join-Path $devsparkDir "VERSION"' in ps_release
    assert 'get_registered_agents()' in bash_release
    assert 'Get-RegisteredAgents' in ps_release
    assert 'AGENT_REGISTRY_FILE="agents-registry.json"' in bash_publish
    assert 'gh release upload "$VERSION"' in bash_publish
    assert '--clobber' in bash_publish
    assert 'gh release edit "$VERSION"' in bash_publish
    assert "$AgentRegistryFile = 'agents-registry.json'" in ps_publish
    assert 'gh release upload $Version' in ps_publish
    assert '--clobber' in ps_publish
    assert 'gh release edit $Version' in ps_publish
    assert '.agents[].key' in bash_publish
    assert 'ConvertFrom-Json' in ps_publish

    print('Release registry contract validated.')


if __name__ == '__main__':
    main()
