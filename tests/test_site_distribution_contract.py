"""Public installation must resolve every manifest path and preserve old docs URLs."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("site_distribution", ROOT / "eng/site/build-distribution.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def write(root, relative, content):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_public_install_tree_and_legacy_routes(tmp_path):
    write(tmp_path, "pyproject.toml", '[project]\nversion = "9.0.0"\n')
    write(tmp_path, "templates/commands/specify.md", "# Specify")
    write(tmp_path, "templates/skills/example/SKILL.md", "# Example")
    write(tmp_path, "templates/consumer-skills/devspark-specify/SKILL.md", "# Specify skill")
    write(tmp_path, "scripts/bash/common.sh", "# common")
    write(tmp_path, "scripts/__pycache__/common.pyc", "local-only")
    write(tmp_path, "quickstart/devspark_quickstart_codex.md", "# Quickstart")
    write(tmp_path, "agents-registry.json", '{"agents": []}')
    write(tmp_path, ".knowledge/governance/constitution.md", "# Constitution")
    write(tmp_path, ".genreleases/devspark-template-codex-ps-v9.0.0.zip", "archive fixture")
    write(tmp_path, "site/_site/index.html", "<h1>DevSpark</h1>")
    write(tmp_path, "site/_site/raw/templates/prompts/atomic/retired.md", "obsolete")
    write(tmp_path, "staticwebapp.config.json", json.dumps({"routes": [{"route": "/quickstart.html", "redirect": "/get-started/quickstart.html", "statusCode": 301}]}))
    output = tmp_path / "site/_site"
    manifest = module.build(tmp_path, output)
    assert manifest["latest"] == "9.0.0"
    assert manifest["raw_base"] == "https://dev.makeboldspark.com/raw"
    entries = {entry["source"]: entry["dest"] for entry in manifest["install"]}
    assert entries["templates/commands/specify.md"] == ".devspark/defaults/commands/devspark.specify.md"
    assert entries["templates/skills/example/SKILL.md"] == ".devspark/templates/skills/example/SKILL.md"
    assert entries["templates/consumer-skills/devspark-specify/SKILL.md"] == ".github/skills/devspark-specify/SKILL.md"
    assert any(entry["category"] == "skill" for entry in manifest["install"])
    assert not any(entry["dest"].startswith(".devspark/templates/consumer-skills") for entry in manifest["install"])
    assert entries["scripts/bash/common.sh"] == ".devspark/scripts/bash/common.sh"
    assert all((output / "raw" / entry).is_file() for entry in entries)
    assert not (output / "raw/scripts/__pycache__").exists()
    assert not (output / "raw/templates/prompts/atomic/retired.md").exists()
    assert (output / "raw/quickstart/devspark_quickstart_codex.md").is_file()
    assert (output / "raw/.knowledge/governance/constitution.md").is_file()
    assert (output / "dist/v9.0.0" / manifest["assets"][0]).is_file()
    assert '/get-started/quickstart.html' in (output / "quickstart.html").read_text()
    assert (output / ".nojekyll").is_file()
    assert (output / "CNAME").read_text().strip() == "dev.makeboldspark.com"


@pytest.mark.parametrize("docs_built", [False, True])
def test_missing_build_inputs_fail_before_publication(tmp_path, docs_built):
    write(tmp_path, "pyproject.toml", '[project]\nversion = "9.0.0"\n')
    if docs_built:
        write(tmp_path, "site/_site/index.html", "<h1>DevSpark</h1>")
    with pytest.raises(ValueError, match="Build"):
        module.build(tmp_path, tmp_path / "site/_site")
