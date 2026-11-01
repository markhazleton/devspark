# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import jsonschema
import pytest
from tests.bash_twin import BASH_EXE, to_bash_path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = json.loads((ROOT / "tests/fixtures/taxonomy-golden-corpus.json").read_text(encoding="utf-8"))
HAS_PWSH = shutil.which("pwsh") is not None
HAS_BASH = BASH_EXE is not None


def _wsl_path(path: Path) -> str:
    return to_bash_path(path)


def _powershell_taxon(repo: Path, path: str, content: str = "") -> str:
    command = (
        f". '{ROOT / 'scripts/powershell/common.ps1'}'; "
        f"Resolve-DocTaxon -RepoRoot '{repo}' -RelativePath '{path}' "
        f"-Content '{content.replace(chr(39), chr(39) * 2)}'"
    )
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-Command", command],
        text=True,
        capture_output=True,
        cwd=ROOT,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _bash_taxon(repo: Path, path: str, content: str = "") -> str:
    common = _wsl_path(ROOT / "scripts/bash/common.sh")
    command = (
        f"source '{common}'; resolve_doc_taxon '{_wsl_path(repo)}' "
        f"'{path}' '{content}'"
    )
    result = subprocess.run(
        [BASH_EXE, "-lc", command], text=True, capture_output=True, cwd=ROOT, timeout=60
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def test_knowledge_schema_accepts_only_current_truth() -> None:
    schema = json.loads(
        (ROOT / "templates/schemas/knowledge-node.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.validate(
        {
            "id": "authentication",
            "type": "architecture",
            "title": "Authentication",
            "links": {"references": ["identity-provider"]},
            "appliesTo": ["src/auth/**"],
        },
        schema,
    )
    for invalid in (
        {"id": "old", "type": "historical-record", "title": "Old"},
        {"id": "decision", "type": "architecture", "title": "Decision", "status": "superseded"},
        {"id": "plan", "type": "architecture", "title": "Plan", "supersedes": "old"},
    ):
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(invalid, schema)


def test_registry_schema_rejects_retention() -> None:
    """No mapping supports timed/counted retention anymore — release moves every categorized
    `.devspark.work/` artifact into the release archive unconditionally, so a `retention` property
    (keepCount/maxAgeDays) is rejected for any mapping, knowledge or work-product alike."""
    schema = json.loads(
        (ROOT / "templates/schemas/taxonomy-registry.schema.json").read_text(encoding="utf-8")
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            {
                "mappings": [
                    {
                        "pathPattern": ".knowledge/runbooks/**",
                        "nodeType": "operations-runbook",
                        "retention": {"keepCount": 5},
                    }
                ]
            },
            schema,
        )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            {
                "mappings": [
                    {
                        "pathPattern": ".devspark.work/audit/**",
                        "workProductType": "audit",
                        "retention": {"maxAgeDays": 60},
                    }
                ]
            },
            schema,
        )


@pytest.mark.skipif(not HAS_PWSH, reason="pwsh not available")
@pytest.mark.skipif(not HAS_BASH, reason="bash not available")
def test_no_config_matches_golden_corpus_in_both_languages(tmp_path: Path) -> None:
    for item in CORPUS:
        assert _powershell_taxon(tmp_path, item["path"], item["content"]) == item["taxon"]
        assert _bash_taxon(tmp_path, item["path"], item["content"]) == item["taxon"]


@pytest.mark.skipif(not HAS_PWSH, reason="pwsh not available")
@pytest.mark.skipif(not HAS_BASH, reason="bash not available")
def test_registry_precedes_defaults_and_catch_all_never_blank(tmp_path: Path) -> None:
    knowledge = tmp_path / ".knowledge"
    knowledge.mkdir()
    (knowledge / "taxonomy-registry.json").write_text(
        json.dumps(
            {
                "mappings": [
                    {
                        "pathPattern": ".documentation/decisions/**",
                        "nodeType": "governance",
                    },
                    {
                        "pathPattern": ".knowledge/custom/**",
                        "nodeType": "architecture",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    cases = {
        ".documentation/decisions/example.md": "GOVERNANCE",
        ".knowledge/custom/example.md": "ARCHITECTURE",
        ".knowledge/reference/example.md": "REFERENCE_DATA",
        "unknown/example.md": "AUTHORITATIVE_REFERENCE",
    }
    for path, expected in cases.items():
        assert _powershell_taxon(tmp_path, path) == expected
        assert _bash_taxon(tmp_path, path) == expected
