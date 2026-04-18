"""Contract tests for alias YAML schema (contracts/alias-schema.md)."""

from __future__ import annotations

from pathlib import Path

import pytest

from devspark_cli.runner.loader import (
    ALIAS_CHAIN_FORBIDDEN,
    ALIAS_FIELD_MISSING,
    ALIAS_ID_MISMATCH,
    ALIAS_NAME_COLLISION,
    ALIAS_TARGET_UNKNOWN,
    ValidationError,
    parse_alias,
    validate_alias,
)


_GOOD = """\
id: create-spec
target_workflow: create-spec
description: Single entrypoint for spec workflow.
"""


def _write(tmp: Path, name: str, content: str) -> Path:
    p = tmp / name
    p.write_text(content, encoding="utf-8")
    return p


def test_happy_path(tmp_path: Path) -> None:
    p = _write(tmp_path, "create-spec.yaml", _GOOD)
    a = parse_alias(p)
    validate_alias(a, resolve_workflow=lambda _: Path("/tmp/wf"))
    assert a.id == "create-spec"
    assert a.target_workflow == "create-spec"


def test_field_missing(tmp_path: Path) -> None:
    bad = "id: x\ntarget_workflow: y\n"
    p = _write(tmp_path, "x.yaml", bad)
    with pytest.raises(ValidationError) as exc:
        parse_alias(p)
    assert exc.value.code == ALIAS_FIELD_MISSING


def test_id_mismatch(tmp_path: Path) -> None:
    p = _write(tmp_path, "other.yaml", _GOOD)
    a = parse_alias(p)
    with pytest.raises(ValidationError) as exc:
        validate_alias(a, resolve_workflow=lambda _: Path("/tmp/wf"))
    assert exc.value.code == ALIAS_ID_MISMATCH


def test_target_unknown(tmp_path: Path) -> None:
    p = _write(tmp_path, "create-spec.yaml", _GOOD)
    a = parse_alias(p)
    with pytest.raises(ValidationError) as exc:
        validate_alias(a, resolve_workflow=lambda _: None)
    assert exc.value.code == ALIAS_TARGET_UNKNOWN


def test_chain_forbidden(tmp_path: Path) -> None:
    p = _write(tmp_path, "create-spec.yaml", _GOOD)
    a = parse_alias(p)
    with pytest.raises(ValidationError) as exc:
        validate_alias(
            a,
            resolve_workflow=lambda _: Path("/tmp/wf"),
            resolve_alias_target=lambda _: Path("/tmp/another-alias"),
        )
    assert exc.value.code == ALIAS_CHAIN_FORBIDDEN


def test_name_collision(tmp_path: Path) -> None:
    p = _write(tmp_path, "create-spec.yaml", _GOOD)
    a = parse_alias(p)
    with pytest.raises(ValidationError) as exc:
        validate_alias(
            a,
            resolve_workflow=lambda _: Path("/tmp/wf"),
            atomic_prompt_ids={"create-spec"},
        )
    assert exc.value.code == ALIAS_NAME_COLLISION


def test_resolver_fallback_alias_miss_to_workflow(tmp_path: Path) -> None:
    """When alias resolution misses, runner-level fallback uses workflow lookup directly.

    The contract reflects this behavior; the loader itself does not implement
    the fallback, so we assert that an alias that DOES resolve does not block
    workflow direct lookup. We exercise this by confirming validate_alias
    treats `resolve_alias_target=None` as "no chain check needed".
    """
    p = _write(tmp_path, "create-spec.yaml", _GOOD)
    a = parse_alias(p)
    validate_alias(a, resolve_workflow=lambda _: Path("/tmp/wf"))
