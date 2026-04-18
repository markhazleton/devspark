"""Contract tests for workflow YAML schema (contracts/workflow-schema.md)."""

from __future__ import annotations

from pathlib import Path

import pytest

from devspark_cli.runner.loader import (
    WF_AUTONOMY_INVALID,
    WF_FIELD_MISSING,
    WF_GUARDRAILS_REQUIRED,
    WF_ID_MISMATCH,
    WF_OUTPUT_TYPE_INVALID,
    WF_PROMPT_UNKNOWN,
    WF_REVIEW_AFTER_UNKNOWN,
    WF_STEP_DUPLICATE,
    WF_WHEN_PARSE,
    ValidationError,
    parse_when_expression,
    parse_workflow,
    validate_workflow,
)


_GOOD = """\
id: create-spec
name: Create Spec
description: Orchestrate specify -> plan -> tasks -> analyze.
output_type: reviewable-artifact
autonomy:
  level: assisted
  review_after:
    - analyze
steps:
  - id: specify
    prompt: specify
  - id: plan
    prompt: plan
  - id: analyze
    prompt: analyze
    pause_after: true
"""


def _write(tmp: Path, name: str, content: str) -> Path:
    p = tmp / name
    p.write_text(content, encoding="utf-8")
    return p


def _ok_resolver(_: str) -> Path | None:
    return Path("/tmp/exists")


def test_happy_path(tmp_path: Path) -> None:
    p = _write(tmp_path, "create-spec.yaml", _GOOD)
    wf = parse_workflow(p)
    validate_workflow(wf, resolve_prompt=_ok_resolver)
    assert wf.id == "create-spec"
    assert wf.steps[-1].pause_after is True


def test_id_mismatch(tmp_path: Path) -> None:
    p = _write(tmp_path, "different-name.yaml", _GOOD)
    wf = parse_workflow(p)
    with pytest.raises(ValidationError) as exc:
        validate_workflow(wf, resolve_prompt=_ok_resolver)
    assert exc.value.code == WF_ID_MISMATCH


def test_prompt_unknown(tmp_path: Path) -> None:
    p = _write(tmp_path, "create-spec.yaml", _GOOD)
    wf = parse_workflow(p)
    with pytest.raises(ValidationError) as exc:
        validate_workflow(wf, resolve_prompt=lambda _: None)
    assert exc.value.code == WF_PROMPT_UNKNOWN


def test_step_duplicate(tmp_path: Path) -> None:
    bad = _GOOD + "  - id: analyze\n    prompt: analyze\n"
    p = _write(tmp_path, "create-spec.yaml", bad)
    wf = parse_workflow(p)
    with pytest.raises(ValidationError) as exc:
        validate_workflow(wf, resolve_prompt=_ok_resolver)
    assert exc.value.code == WF_STEP_DUPLICATE


def test_autonomy_invalid(tmp_path: Path) -> None:
    bad = _GOOD.replace("level: assisted", "level: yolo")
    p = _write(tmp_path, "create-spec.yaml", bad)
    wf = parse_workflow(p)
    with pytest.raises(ValidationError) as exc:
        validate_workflow(wf, resolve_prompt=_ok_resolver)
    assert exc.value.code == WF_AUTONOMY_INVALID


def test_guardrails_required(tmp_path: Path) -> None:
    bad = _GOOD.replace("level: assisted", "level: autonomous")
    p = _write(tmp_path, "create-spec.yaml", bad)
    wf = parse_workflow(p)
    with pytest.raises(ValidationError) as exc:
        validate_workflow(wf, resolve_prompt=_ok_resolver)
    assert exc.value.code == WF_GUARDRAILS_REQUIRED


def test_output_type_invalid(tmp_path: Path) -> None:
    bad = _GOOD.replace("output_type: reviewable-artifact", "output_type: tweet")
    p = _write(tmp_path, "create-spec.yaml", bad)
    wf = parse_workflow(p)
    with pytest.raises(ValidationError) as exc:
        validate_workflow(wf, resolve_prompt=_ok_resolver)
    assert exc.value.code == WF_OUTPUT_TYPE_INVALID


def test_review_after_unknown(tmp_path: Path) -> None:
    bad = _GOOD.replace("- analyze\n", "- analyze\n    - missing-step\n")
    # Use safer mutation:
    bad = _GOOD.replace("review_after:\n    - analyze", "review_after:\n    - missing-step")
    p = _write(tmp_path, "create-spec.yaml", bad)
    wf = parse_workflow(p)
    with pytest.raises(ValidationError) as exc:
        validate_workflow(wf, resolve_prompt=_ok_resolver)
    assert exc.value.code == WF_REVIEW_AFTER_UNKNOWN


def test_field_missing(tmp_path: Path) -> None:
    bad = _GOOD.replace("name: Create Spec\n", "")
    p = _write(tmp_path, "create-spec.yaml", bad)
    with pytest.raises(ValidationError) as exc:
        parse_workflow(p)
    assert exc.value.code == WF_FIELD_MISSING


# --------------------------------------------------------------------------
# `when`-expression fuzz suite
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "expr",
    [
        "=",
        "===",
        "context.x AND context.y",
        "(context.x == true",
        "context.x == true)",
        "context.x.y == 1",
        "len(context.x) == 0",
        "1 + 1 == 2",
        "context.",
        ".context.x",
        "",
        "   ",
        "context",
        "context.x ==",
    ],
)
def test_when_invalid(expr: str) -> None:
    with pytest.raises(ValidationError) as exc:
        parse_when_expression(expr)
    assert exc.value.code == WF_WHEN_PARSE


@pytest.mark.parametrize(
    "expr",
    [
        "context.x == true",
        "context.x != false",
        "context.x == 1",
        'context.kind == "bug"',
        "context.x == true && context.y == false",
        "context.x == true || context.y == false",
        "(context.x == true) && (context.y != 2)",
        "true",
        "context.x",
    ],
)
def test_when_valid(expr: str) -> None:
    parse_when_expression(expr)
