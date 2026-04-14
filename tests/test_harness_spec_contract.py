"""Contract validation for harness spec models, loader, and schema generation.

Run with: python tests/test_harness_spec_contract.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HARNESS_DIR = ROOT / "src" / "devspark_cli" / "harness"


def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    spec_models = _load_module("devspark_cli.harness.spec_models", HARNESS_DIR / "spec_models.py")
    spec_loader = _load_module("devspark_cli.harness.spec_loader", HARNESS_DIR / "spec_loader.py")

    fixtures_dir = ROOT / "tests" / "fixtures" / "harness"
    minimal = fixtures_dir / "valid_minimal.yaml"
    full = fixtures_dir / "valid_all_steps.yaml"
    invalid = fixtures_dir / "invalid_missing_field.yaml"

    minimal_spec = spec_loader.load_harness_spec(minimal, ROOT)
    assert minimal_spec.kind == "HarnessSpec"
    assert minimal_spec.apiVersion == spec_models.SUPPORTED_API_VERSION
    assert minimal_spec.steps[0].prompt_file.endswith("prompts\\specify.md") or minimal_spec.steps[0].prompt_file.endswith("prompts/specify.md")

    full_spec = spec_loader.load_harness_spec(full, ROOT)
    assert len(full_spec.steps) == 3
    assert {step.type for step in full_spec.steps} == {"agent_task", "validation", "human_gate"}
    assert any(rule.type == "command.exit_code" for step in full_spec.steps for rule in step.validation)

    try:
        spec_loader.load_harness_spec(invalid, ROOT)
    except spec_loader.HarnessSpecError as exc:
        message = str(exc)
        assert "steps" in message
    else:
        raise AssertionError("Expected invalid_missing_field.yaml to fail validation")

    with tempfile.TemporaryDirectory() as temp_dir:
        mismatch = Path(temp_dir) / "mismatch.yaml"
        mismatch.write_text(
            "apiVersion: devspark.ai/v2\nkind: HarnessSpec\nname: mismatch\nsteps:\n  - id: only\n    type: agent_task\n    prompt_file: prompts/only.md\n",
            encoding="utf-8",
        )
        try:
            spec_loader.load_harness_spec(mismatch, ROOT)
        except spec_loader.HarnessSpecError as exc:
            assert spec_models.SUPPORTED_API_VERSION in str(exc)
            assert "apiVersion" in str(exc)
        else:
            raise AssertionError("Expected apiVersion mismatch to fail validation")

        schema_path = Path(temp_dir) / "harness.schema.json"
        spec_loader.write_harness_schema(schema_path)
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        assert schema["$schema"] == spec_models.JSON_SCHEMA_DRAFT
        assert schema["title"] == "HarnessSpec"
        assert "properties" in schema
        assert "steps" in schema["properties"]

    for fixture in (minimal, full, invalid):
        started = time.perf_counter()
        try:
            spec_loader.load_harness_spec(fixture, ROOT)
        except spec_loader.HarnessSpecError:
            pass
        duration = time.perf_counter() - started
        assert duration < 2, f"Validation exceeded 2 seconds for {fixture.name}: {duration:.3f}s"

    print("Harness spec contract validated.")


if __name__ == "__main__":
    main()