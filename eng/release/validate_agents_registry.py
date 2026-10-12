# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""
Validate agents-registry.json against templates/agents-registry.schema.json and run
extra structural checks that JSON Schema draft-07 cannot express (duplicate keys).

Usage: python eng/release/validate_agents_registry.py
Exit code 0 on success, 1 on any schema or structural violation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "agents-registry.json"
SCHEMA_PATH = REPO_ROOT / "templates" / "agents-registry.schema.json"


def main() -> int:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(registry), key=lambda e: list(e.path))

    if errors:
        print(f"Schema validation FAILED for {REGISTRY_PATH}:")
        for error in errors:
            location = "/".join(str(p) for p in error.path) or "<root>"
            print(f"  - {location}: {error.message}")
        return 1

    # Structural check JSON Schema can't express: unique agent keys.
    keys = [agent["key"] for agent in registry.get("agents", [])]
    duplicates = {k for k in keys if keys.count(k) > 1}
    if duplicates:
        print(f"Duplicate agent key(s) in {REGISTRY_PATH}: {', '.join(sorted(duplicates))}")
        return 1

    print(f"OK: {REGISTRY_PATH} — {len(keys)} agents, schema-valid, no duplicate keys.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
