"""DevSpark workflow runner — loader and validators.

Implements:
- Atomic prompt frontmatter parsing/validation (contracts/atomic-prompt-frontmatter.md)
- Workflow YAML loading/validation (contracts/workflow-schema.md)
- Alias YAML loading/validation (contracts/alias-schema.md)
- Restricted `when`-expression parser (contracts/workflow-schema.md)

All error codes are exposed as constants so contract tests can pin them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Error codes
# ---------------------------------------------------------------------------

# Atomic prompt
AP_ID_INVALID = "AP_ID_INVALID"
AP_NAME_REQUIRED = "AP_NAME_REQUIRED"
AP_AUDIENCE_INVALID = "AP_AUDIENCE_INVALID"
AP_EXPOSED_INVALID = "AP_EXPOSED_INVALID"
AP_CATEGORY_REQUIRED = "AP_CATEGORY_REQUIRED"
AP_DESC_INVALID = "AP_DESC_INVALID"
AP_INPUTS_INVALID = "AP_INPUTS_INVALID"
AP_OUTPUTS_INVALID = "AP_OUTPUTS_INVALID"
AP_LEGACY_UNKNOWN = "AP_LEGACY_UNKNOWN"
AP_FRONTMATTER_MISSING = "AP_FRONTMATTER_MISSING"

# Workflow
WF_ID_MISMATCH = "WF_ID_MISMATCH"
WF_PROMPT_UNKNOWN = "WF_PROMPT_UNKNOWN"
WF_STEP_DUPLICATE = "WF_STEP_DUPLICATE"
WF_AUTONOMY_INVALID = "WF_AUTONOMY_INVALID"
WF_GUARDRAILS_REQUIRED = "WF_GUARDRAILS_REQUIRED"
WF_WHEN_PARSE = "WF_WHEN_PARSE"
WF_OUTPUT_TYPE_INVALID = "WF_OUTPUT_TYPE_INVALID"
WF_REVIEW_AFTER_UNKNOWN = "WF_REVIEW_AFTER_UNKNOWN"
WF_FIELD_MISSING = "WF_FIELD_MISSING"
WF_PARSE_ERROR = "WF_PARSE_ERROR"

# Alias
ALIAS_TARGET_UNKNOWN = "ALIAS_TARGET_UNKNOWN"
ALIAS_CHAIN_FORBIDDEN = "ALIAS_CHAIN_FORBIDDEN"
ALIAS_DUPLICATE = "ALIAS_DUPLICATE"
ALIAS_NAME_COLLISION = "ALIAS_NAME_COLLISION"
ALIAS_FIELD_MISSING = "ALIAS_FIELD_MISSING"
ALIAS_ID_MISMATCH = "ALIAS_ID_MISMATCH"
ALIAS_PARSE_ERROR = "ALIAS_PARSE_ERROR"


# ---------------------------------------------------------------------------
# Common types
# ---------------------------------------------------------------------------

_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_AUDIENCES = {"beginner", "intermediate", "expert"}
_AUTONOMY_LEVELS = {"assisted", "autonomous"}
_OUTPUT_TYPES = {"reviewable-artifact", "pull-request", "issue-link", "none"}
_ON_FAILURE = {"abort", "continue", "pause"}


class ValidationError(Exception):
    """Validation failure with a stable error code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


# ---------------------------------------------------------------------------
# Atomic prompt frontmatter
# ---------------------------------------------------------------------------

@dataclass
class AtomicPrompt:
    id: str
    name: str
    audience: str
    exposed: bool
    category: str
    description: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    legacy_command: str | None = None
    body: str = ""
    source_path: Path | None = None


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def parse_atomic_prompt(path: Path) -> AtomicPrompt:
    """Parse an atomic prompt markdown file into an AtomicPrompt."""
    text = path.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(text)
    if not m:
        raise ValidationError(AP_FRONTMATTER_MISSING, f"{path.name}: missing YAML frontmatter")
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as exc:
        raise ValidationError(AP_FRONTMATTER_MISSING, f"{path.name}: invalid frontmatter YAML: {exc}")

    if not isinstance(data, dict):
        raise ValidationError(AP_FRONTMATTER_MISSING, f"{path.name}: frontmatter must be a mapping")

    raw_inputs = data.get("inputs")
    raw_outputs = data.get("outputs")
    prompt = AtomicPrompt(
        id=str(data.get("id", "")),
        name=str(data.get("name", "")),
        audience=str(data.get("audience", "")),
        exposed=bool(data.get("exposed", False)) if "exposed" in data else False,
        category=str(data.get("category", "")),
        description=str(data.get("description", "")),
        inputs=list(raw_inputs) if isinstance(raw_inputs, list) else [],
        outputs=list(raw_outputs) if isinstance(raw_outputs, list) else [],
        legacy_command=data.get("legacy_command"),
        body=m.group(2),
        source_path=path,
    )
    # Track the raw exposed value so type-validation can flag non-bool inputs
    prompt._raw_exposed = data.get("exposed", False)  # type: ignore[attr-defined]
    prompt._raw_data = data  # type: ignore[attr-defined]
    return prompt


def validate_atomic_prompt(
    prompt: AtomicPrompt,
    *,
    commands_dir: Path | None = None,
) -> None:
    """Validate an AtomicPrompt against contracts/atomic-prompt-frontmatter.md.

    `commands_dir` (when provided) is used to validate `legacy_command` references.
    """
    raw = getattr(prompt, "_raw_data", {})

    # id
    expected_id = prompt.source_path.stem if prompt.source_path else prompt.id
    if not prompt.id or not _ID_RE.match(prompt.id):
        raise ValidationError(AP_ID_INVALID, f"id={prompt.id!r} must match {_ID_RE.pattern}")
    if prompt.source_path is not None and prompt.id != expected_id:
        raise ValidationError(
            AP_ID_INVALID,
            f"id={prompt.id!r} must equal filename stem {expected_id!r}",
        )

    # name
    if not prompt.name.strip():
        raise ValidationError(AP_NAME_REQUIRED, "name is required and non-empty")

    # audience
    if prompt.audience not in _AUDIENCES:
        raise ValidationError(
            AP_AUDIENCE_INVALID,
            f"audience={prompt.audience!r} not in {sorted(_AUDIENCES)}",
        )

    # exposed
    raw_exposed = raw.get("exposed", None)
    if raw_exposed is None or not isinstance(raw_exposed, bool):
        raise ValidationError(AP_EXPOSED_INVALID, "exposed must be a bool literal")

    # category
    if not prompt.category.strip():
        raise ValidationError(AP_CATEGORY_REQUIRED, "category is required and non-empty")

    # description
    if not prompt.description.strip() or len(prompt.description) > 200:
        raise ValidationError(
            AP_DESC_INVALID,
            "description is required, non-empty, and <= 200 chars",
        )

    # inputs/outputs
    if "inputs" in raw and not isinstance(raw["inputs"], list):
        raise ValidationError(AP_INPUTS_INVALID, "inputs must be a list of strings")
    if "outputs" in raw and not isinstance(raw["outputs"], list):
        raise ValidationError(AP_OUTPUTS_INVALID, "outputs must be a list of strings")
    for item in prompt.inputs:
        if not isinstance(item, str) or not item:
            raise ValidationError(AP_INPUTS_INVALID, f"inputs entry must be non-empty str, got {item!r}")
    for item in prompt.outputs:
        if not isinstance(item, str) or not item:
            raise ValidationError(AP_OUTPUTS_INVALID, f"outputs entry must be non-empty str, got {item!r}")

    # legacy_command
    if prompt.legacy_command is not None:
        if not isinstance(prompt.legacy_command, str) or not prompt.legacy_command:
            raise ValidationError(AP_LEGACY_UNKNOWN, f"legacy_command must be a non-empty string or null")
        if commands_dir is not None:
            target = commands_dir / f"{prompt.legacy_command}.md"
            if not target.is_file():
                raise ValidationError(
                    AP_LEGACY_UNKNOWN,
                    f"legacy_command={prompt.legacy_command!r} does not resolve to {target}",
                )


# ---------------------------------------------------------------------------
# Workflow YAML
# ---------------------------------------------------------------------------

@dataclass
class WorkflowStep:
    id: str
    prompt: str
    pause_after: bool = False
    on_failure: str = "abort"
    when: str | None = None


@dataclass
class Workflow:
    id: str
    name: str
    description: str
    output_type: str
    autonomy_level: str
    review_after: list[str] = field(default_factory=list)
    guardrails: dict[str, Any] = field(default_factory=dict)
    steps: list[WorkflowStep] = field(default_factory=list)
    schema_version: int = 1
    source_path: Path | None = None


def parse_workflow(path: Path) -> Workflow:
    """Parse a workflow YAML file into a Workflow."""
    try:
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text) or {}
    except (yaml.YAMLError, OSError) as exc:
        raise ValidationError(WF_PARSE_ERROR, f"{path.name}: {exc}")
    if not isinstance(data, dict):
        raise ValidationError(WF_PARSE_ERROR, f"{path.name}: top-level must be a mapping")

    required = ["id", "name", "description", "output_type", "autonomy", "steps"]
    for field_name in required:
        if field_name not in data:
            raise ValidationError(WF_FIELD_MISSING, f"missing required field {field_name!r}")

    autonomy = data["autonomy"]
    if not isinstance(autonomy, dict):
        raise ValidationError(WF_AUTONOMY_INVALID, "autonomy must be a mapping")

    raw_steps = data.get("steps") or []
    if not isinstance(raw_steps, list) or not raw_steps:
        raise ValidationError(WF_FIELD_MISSING, "steps must be a non-empty list")

    steps: list[WorkflowStep] = []
    for raw in raw_steps:
        if not isinstance(raw, dict) or "id" not in raw or "prompt" not in raw:
            raise ValidationError(WF_FIELD_MISSING, f"step requires id and prompt: {raw!r}")
        steps.append(
            WorkflowStep(
                id=str(raw["id"]),
                prompt=str(raw["prompt"]),
                pause_after=bool(raw.get("pause_after", False)),
                on_failure=str(raw.get("on_failure", "abort")),
                when=raw.get("when"),
            )
        )

    return Workflow(
        id=str(data["id"]),
        name=str(data["name"]),
        description=str(data["description"]),
        output_type=str(data["output_type"]),
        autonomy_level=str(autonomy.get("level", "")),
        review_after=list(autonomy.get("review_after") or []),
        guardrails=dict(autonomy.get("guardrails") or {}),
        steps=steps,
        schema_version=int(data.get("schema_version", 1)),
        source_path=path,
    )


def validate_workflow(
    workflow: Workflow,
    *,
    resolve_prompt=None,
) -> None:
    """Validate a Workflow against contracts/workflow-schema.md.

    `resolve_prompt(id) -> Path | None` is used to validate every step.prompt.
    """
    expected_id = workflow.source_path.stem if workflow.source_path else workflow.id
    if workflow.id != expected_id:
        raise ValidationError(
            WF_ID_MISMATCH,
            f"workflow id={workflow.id!r} must equal filename stem {expected_id!r}",
        )

    if workflow.output_type not in _OUTPUT_TYPES:
        raise ValidationError(
            WF_OUTPUT_TYPE_INVALID,
            f"output_type={workflow.output_type!r} not in {sorted(_OUTPUT_TYPES)}",
        )

    if workflow.autonomy_level not in _AUTONOMY_LEVELS:
        raise ValidationError(
            WF_AUTONOMY_INVALID,
            f"autonomy.level={workflow.autonomy_level!r} not in {sorted(_AUTONOMY_LEVELS)}",
        )

    if workflow.autonomy_level == "autonomous" and not workflow.guardrails:
        raise ValidationError(
            WF_GUARDRAILS_REQUIRED,
            "autonomy.guardrails required when level=autonomous",
        )

    seen: set[str] = set()
    step_ids: set[str] = set()
    for step in workflow.steps:
        if step.id in seen:
            raise ValidationError(WF_STEP_DUPLICATE, f"duplicate step id {step.id!r}")
        seen.add(step.id)
        step_ids.add(step.id)
        if step.on_failure not in _ON_FAILURE:
            raise ValidationError(WF_FIELD_MISSING, f"step {step.id!r} on_failure invalid")
        if step.when is not None:
            try:
                parse_when_expression(step.when)
            except ValidationError:
                raise
        if resolve_prompt is not None:
            if resolve_prompt(step.prompt) is None:
                raise ValidationError(
                    WF_PROMPT_UNKNOWN,
                    f"step {step.id!r} prompt={step.prompt!r} does not resolve",
                )

    for ra in workflow.review_after:
        if ra not in step_ids:
            raise ValidationError(
                WF_REVIEW_AFTER_UNKNOWN,
                f"review_after entry {ra!r} not in step ids",
            )


# ---------------------------------------------------------------------------
# Alias YAML
# ---------------------------------------------------------------------------

@dataclass
class Alias:
    id: str
    target_workflow: str
    description: str
    source_path: Path | None = None


def parse_alias(path: Path) -> Alias:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (yaml.YAMLError, OSError) as exc:
        raise ValidationError(ALIAS_PARSE_ERROR, f"{path.name}: {exc}")
    if not isinstance(data, dict):
        raise ValidationError(ALIAS_PARSE_ERROR, f"{path.name}: top-level must be a mapping")
    for required in ("id", "target_workflow", "description"):
        if required not in data:
            raise ValidationError(ALIAS_FIELD_MISSING, f"alias missing field {required!r}")
    return Alias(
        id=str(data["id"]),
        target_workflow=str(data["target_workflow"]),
        description=str(data["description"]),
        source_path=path,
    )


def validate_alias(
    alias: Alias,
    *,
    resolve_workflow=None,
    resolve_alias_target=None,
    atomic_prompt_ids: set[str] | None = None,
) -> None:
    """Validate an Alias.

    - `resolve_workflow(id) -> Path | None`: confirm target_workflow exists.
    - `resolve_alias_target(id) -> Path | None`: confirm target is NOT another alias.
    - `atomic_prompt_ids`: set of known atomic-prompt ids; alias.id must not collide.
    """
    expected_id = alias.source_path.stem if alias.source_path else alias.id
    if alias.id != expected_id:
        raise ValidationError(
            ALIAS_ID_MISMATCH,
            f"alias id={alias.id!r} must equal filename stem {expected_id!r}",
        )

    if atomic_prompt_ids and alias.id in atomic_prompt_ids:
        raise ValidationError(
            ALIAS_NAME_COLLISION,
            f"alias id={alias.id!r} collides with an atomic prompt id",
        )

    if resolve_alias_target is not None and resolve_alias_target(alias.target_workflow) is not None:
        raise ValidationError(
            ALIAS_CHAIN_FORBIDDEN,
            f"alias target_workflow={alias.target_workflow!r} resolves to another alias (chains forbidden)",
        )

    if resolve_workflow is not None and resolve_workflow(alias.target_workflow) is None:
        raise ValidationError(
            ALIAS_TARGET_UNKNOWN,
            f"alias target_workflow={alias.target_workflow!r} does not resolve",
        )


# ---------------------------------------------------------------------------
# Restricted `when`-expression parser
# ---------------------------------------------------------------------------
#
# Grammar (recursive descent):
#   expr     := or_expr
#   or_expr  := and_expr ( "||" and_expr )*
#   and_expr := equality ( "&&" equality )*
#   equality := primary ( ("==" | "!=") primary )?
#   primary  := "(" expr ")" | literal | ref
#   literal  := bool | int | string
#   ref      := "context" "." ident      (single-segment only)
#
# No function calls, no chained attribute access (`context.x.y` is rejected),
# no operator beyond the four documented in the contract.

_TOKEN_RE = re.compile(
    r"""
    \s*(?:
      (?P<op>==|!=|&&|\|\||\(|\)|\.) |
      (?P<str>"[^"]*"|'[^']*') |
      (?P<int>-?\d+) |
      (?P<ident>[A-Za-z_][A-Za-z0-9_]*)
    )
    """,
    re.VERBOSE,
)


def _tokenize_when(expr: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    pos = 0
    while pos < len(expr):
        m = _TOKEN_RE.match(expr, pos)
        if not m:
            # Skip whitespace explicitly; otherwise unrecognized.
            if expr[pos].isspace():
                pos += 1
                continue
            raise ValidationError(WF_WHEN_PARSE, f"unrecognized character at offset {pos}: {expr[pos]!r}")
        if m.group("op"):
            tokens.append(("op", m.group("op")))
        elif m.group("str"):
            tokens.append(("str", m.group("str")[1:-1]))
        elif m.group("int"):
            tokens.append(("int", m.group("int")))
        elif m.group("ident"):
            ident = m.group("ident")
            if ident in ("true", "false"):
                tokens.append(("bool", ident))
            else:
                tokens.append(("ident", ident))
        pos = m.end()
    return tokens


class _WhenParser:
    def __init__(self, tokens: list[tuple[str, str]]) -> None:
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> tuple[str, str] | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self) -> tuple[str, str]:
        if self.pos >= len(self.tokens):
            raise ValidationError(WF_WHEN_PARSE, "unexpected end of expression")
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect_op(self, op: str) -> None:
        tok = self.consume()
        if tok != ("op", op):
            raise ValidationError(WF_WHEN_PARSE, f"expected {op!r}, got {tok!r}")

    def parse_expr(self) -> None:
        self.parse_or()
        if self.peek() is not None:
            raise ValidationError(WF_WHEN_PARSE, f"trailing tokens: {self.tokens[self.pos:]!r}")

    def parse_or(self) -> None:
        self.parse_and()
        while self.peek() == ("op", "||"):
            self.consume()
            self.parse_and()

    def parse_and(self) -> None:
        self.parse_equality()
        while self.peek() == ("op", "&&"):
            self.consume()
            self.parse_equality()

    def parse_equality(self) -> None:
        self.parse_primary()
        if self.peek() in (("op", "=="), ("op", "!=")):
            self.consume()
            self.parse_primary()

    def parse_primary(self) -> None:
        tok = self.peek()
        if tok is None:
            raise ValidationError(WF_WHEN_PARSE, "unexpected end of expression in primary")
        kind, val = tok
        if kind == "op" and val == "(":
            self.consume()
            self.parse_or()
            self.expect_op(")")
            return
        if kind in ("bool", "int", "str"):
            self.consume()
            return
        if kind == "ident":
            self.consume()
            if val != "context":
                raise ValidationError(WF_WHEN_PARSE, f"only context.<key> references allowed, got {val!r}")
            self.expect_op(".")
            ref_tok = self.consume()
            if ref_tok[0] != "ident":
                raise ValidationError(WF_WHEN_PARSE, f"expected identifier after 'context.', got {ref_tok!r}")
            # No further attribute access allowed.
            if self.peek() == ("op", "."):
                raise ValidationError(WF_WHEN_PARSE, "nested attribute access not allowed (e.g. context.x.y)")
            return
        raise ValidationError(WF_WHEN_PARSE, f"unexpected token in primary: {tok!r}")


def parse_when_expression(expr: str) -> None:
    """Validate a `when` expression. Raises ValidationError(WF_WHEN_PARSE) on failure."""
    if not isinstance(expr, str) or not expr.strip():
        raise ValidationError(WF_WHEN_PARSE, "when expression must be a non-empty string")
    tokens = _tokenize_when(expr)
    if not tokens:
        raise ValidationError(WF_WHEN_PARSE, "when expression produced no tokens")
    _WhenParser(tokens).parse_expr()


def evaluate_when_expression(expr: str, context: dict[str, Any]) -> bool:
    """Evaluate a `when` expression against a context dict.

    Returns the boolean result. Missing context keys evaluate to None.
    """
    parse_when_expression(expr)
    tokens = _tokenize_when(expr)
    return _WhenEvaluator(tokens, context).eval_expr()


class _WhenEvaluator:
    def __init__(self, tokens: list[tuple[str, str]], context: dict[str, Any]) -> None:
        self.tokens = tokens
        self.pos = 0
        self.context = context

    def peek(self) -> tuple[str, str] | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self) -> tuple[str, str]:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def eval_expr(self) -> bool:
        result = self.eval_or()
        return bool(result)

    def eval_or(self) -> Any:
        left = self.eval_and()
        while self.peek() == ("op", "||"):
            self.consume()
            right = self.eval_and()
            left = bool(left) or bool(right)
        return left

    def eval_and(self) -> Any:
        left = self.eval_equality()
        while self.peek() == ("op", "&&"):
            self.consume()
            right = self.eval_equality()
            left = bool(left) and bool(right)
        return left

    def eval_equality(self) -> Any:
        left = self.eval_primary()
        if self.peek() in (("op", "=="), ("op", "!=")):
            op = self.consume()[1]
            right = self.eval_primary()
            return (left == right) if op == "==" else (left != right)
        return left

    def eval_primary(self) -> Any:
        kind, val = self.consume()
        if kind == "op" and val == "(":
            inner = self.eval_or()
            self.consume()  # ')'
            return inner
        if kind == "bool":
            return val == "true"
        if kind == "int":
            return int(val)
        if kind == "str":
            return val
        if kind == "ident" and val == "context":
            self.consume()  # '.'
            key = self.consume()[1]
            return self.context.get(key)
        raise ValidationError(WF_WHEN_PARSE, f"unexpected token at evaluate: {kind}/{val}")
