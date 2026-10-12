# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Validation for registry-driven release packaging contracts.

Run with: python tests/test_release_registry_contract.py
"""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parent.parent
SHIM_KEYS = ("commands_dir", "extension", "arg_format", "prompt_dir")


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def main() -> None:
    bash_release = _read('eng/release/create-release-packages.sh')
    ps_release = _read('eng/release/create-release-packages.ps1')
    registry = _read('agents-registry.json')

    assert '"version": 1' in registry
    assert 'AGENT_REGISTRY_FILE="agents-registry.json"' in bash_release
    assert '$AgentRegistryFile = "agents-registry.json"' in ps_release
    assert 'get_registered_agents()' in bash_release
    assert 'Get-RegisteredAgents' in ps_release
    assert "jq -r '.agents[].key' \"$AGENT_REGISTRY_FILE\" | tr -d '\\r'" in bash_release
    assert "| tr -d '\\r'" in bash_release
    for release_script in (bash_release, ps_release):
        assert '.devspark.work/{git-user}/commands/' in release_script
        assert '.documentation/{git-user}/commands/' not in release_script

    print('Release registry contract validated.')


def _registry() -> dict:
    return json.loads(_read('agents-registry.json'))


def _schema() -> dict:
    return json.loads(_read('templates/agents-registry.schema.json'))


def _agent(registry: dict, key: str) -> dict:
    return next(a for a in registry['agents'] if a['key'] == key)


def _skills_form_registry() -> dict:
    registry = copy.deepcopy(_registry())
    release = _agent(registry, 'copilot')['release']
    for key in SHIM_KEYS:
        release.pop(key, None)
    release['skills_dir'] = '.github/skills'
    return registry


def _run_validator(tmp_path: Path, registry: dict) -> subprocess.CompletedProcess[str]:
    repo = tmp_path / 'repo'
    (repo / 'eng' / 'release').mkdir(parents=True)
    (repo / 'templates').mkdir()
    shutil.copy(ROOT / 'eng' / 'release' / 'validate_agents_registry.py', repo / 'eng' / 'release')
    shutil.copy(ROOT / 'templates' / 'agents-registry.schema.json', repo / 'templates')
    (repo / 'agents-registry.json').write_text(json.dumps(registry), encoding='utf-8')
    return subprocess.run(
        [sys.executable, str(repo / 'eng' / 'release' / 'validate_agents_registry.py')],
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_shim_form_registry_validates_against_the_schema() -> None:
    errors = list(Draft7Validator(_schema()).iter_errors(_registry()))
    assert errors == []


def test_shim_form_registry_passes_the_validator(tmp_path: Path) -> None:
    result = _run_validator(tmp_path, _registry())
    assert result.returncode == 0, result.stdout + result.stderr


def test_every_non_copilot_agent_keeps_the_shim_form() -> None:
    for agent in _registry()['agents']:
        if agent['key'] == 'copilot':
            continue
        release = agent['release']
        assert release.get('commands_dir') and release.get('extension') and release.get('arg_format'), agent['key']
        assert 'skills_dir' not in release, agent['key']


def test_copilot_registry_entry_uses_skills_form() -> None:
    release = _agent(_registry(), 'copilot')['release']
    assert release['skills_dir'] == '.github/skills'
    assert [k for k in SHIM_KEYS if k in release] == []
    assert any(f['destination'] == '.vscode/settings.json' for f in release['support_files'])


def test_schema_accepts_exactly_the_shim_form_or_the_skills_form() -> None:
    release = _schema()['$defs']['release']
    forms = release.get('oneOf')
    assert forms and len(forms) == 2
    required = [set(f.get('required', [])) for f in forms]
    assert {'commands_dir', 'extension', 'arg_format'} in required
    assert {'skills_dir'} in required


def test_skills_form_registry_validates_against_the_schema() -> None:
    errors = list(Draft7Validator(_schema()).iter_errors(_skills_form_registry()))
    assert errors == []


def test_skills_form_registry_passes_the_validator(tmp_path: Path) -> None:
    result = _run_validator(tmp_path, _skills_form_registry())
    assert result.returncode == 0, result.stdout + result.stderr


def test_schema_rejects_a_release_mixing_both_forms() -> None:
    mixed = _skills_form_registry()
    release = _agent(mixed, 'copilot')['release']
    release.update({'commands_dir': '.github/agents', 'extension': 'agent.md', 'arg_format': '$ARGUMENTS'})
    validator = Draft7Validator(_schema())
    assert list(validator.iter_errors(_skills_form_registry())) == []
    assert list(validator.iter_errors(mixed))


def test_vscode_settings_keeps_terminal_autoapprove_and_json_schemas() -> None:
    settings = json.loads(_read('templates/vscode-settings.json'))
    assert '.devspark.work/scripts/bash/' in settings['chat.tools.terminal.autoApprove']
    assert settings['json.schemas']


def test_vscode_settings_has_no_managed_prompt_recommendations() -> None:
    settings = json.loads(_read('templates/vscode-settings.json'))
    assert 'chat.promptFilesRecommendations' not in settings


if __name__ == '__main__':
    main()
