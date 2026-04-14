"""Harness spec loading, normalization, and schema generation helpers."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from pydantic import ValidationError

from .spec_models import HarnessSpec, RetryPolicy, SUPPORTED_API_VERSION, harness_schema


class HarnessSpecError(ValueError):
    """Raised when a harness spec cannot be parsed or validated."""


ROOT_RELATIVE_PREFIXES = (
    ".documentation/",
    ".devspark/",
    "src/",
    "tests/",
    "scripts/",
    "templates/",
    "quickstart/",
    "examples/",
)


def discover_repo_root(spec_path: Path, cwd: Path | None = None) -> Path:
    """Find the repository root by walking upward from a spec path or cwd."""

    start = (cwd or spec_path.parent).resolve()
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").is_file() or (candidate / "agents-registry.json").is_file():
            return candidate
    return start


def _resolve_path(value: str, spec_dir: Path, repo_root: Path) -> str:
    path = Path(value)
    if path.is_absolute():
        return str(path)
    normalized = value.replace("\\", "/")
    if normalized.startswith(ROOT_RELATIVE_PREFIXES) or normalized in {"README.md", "pyproject.toml", "agents-registry.json"}:
        return str((repo_root / path).resolve())
    return str((spec_dir / path).resolve())


def _normalize_rule(rule: dict, spec_dir: Path, repo_root: Path) -> dict:
    for field in ("path", "schema_file", "target_file"):
        if isinstance(rule.get(field), str):
            rule[field] = _resolve_path(rule[field], spec_dir, repo_root)
    return rule


def _normalize_step(step: dict, spec_dir: Path, repo_root: Path) -> dict:
    if isinstance(step.get("prompt_file"), str):
        step["prompt_file"] = _resolve_path(step["prompt_file"], spec_dir, repo_root)
    if isinstance(step.get("inputs"), list):
        step["inputs"] = [_resolve_path(value, spec_dir, repo_root) for value in step["inputs"]]
    if isinstance(step.get("outputs"), list):
        step["outputs"] = [_resolve_path(value, spec_dir, repo_root) for value in step["outputs"]]
    if isinstance(step.get("validation"), list):
        step["validation"] = [_normalize_rule(rule, spec_dir, repo_root) for rule in step["validation"]]
    retry = step.get("retry")
    if isinstance(retry, dict) and isinstance(retry.get("repairPrompt"), str):
        retry["repairPrompt"] = _resolve_path(retry["repairPrompt"], spec_dir, repo_root)
    return step


def _normalize_spec_data(data: dict, spec_path: Path, repo_root: Path) -> dict:
    spec_dir = spec_path.parent.resolve()
    normalized = dict(data)
    telemetry = dict(normalized.get("telemetry") or {})
    if isinstance(telemetry.get("run_dir"), str):
        telemetry["run_dir"] = _resolve_path(telemetry["run_dir"], spec_dir, repo_root)
    normalized["telemetry"] = telemetry

    defaults = dict(normalized.get("defaults") or {})
    retry = dict(defaults.get("retry") or {})
    if isinstance(retry.get("repairPrompt"), str):
        retry["repairPrompt"] = _resolve_path(retry["repairPrompt"], spec_dir, repo_root)
    if retry:
        defaults["retry"] = retry
    normalized["defaults"] = defaults

    normalized["steps"] = [_normalize_step(dict(step), spec_dir, repo_root) for step in normalized.get("steps", [])]
    return normalized


def _suggestion_for_error(location: tuple[str | int, ...], message: str) -> str:
    field_path = ".".join(str(part) for part in location) if location else "spec"
    if "apiVersion" in field_path:
        return f"Set apiVersion to {SUPPORTED_API_VERSION!r}."
    if field_path == "steps":
        return "Add at least one step entry under steps."
    if field_path.endswith("prompt_file"):
        return "Add a prompt_file path for agent_task or human_gate steps."
    if "validation" in field_path and "required field" in message:
        return "Add the fields required by the selected validation rule type."
    if "scope.app" in field_path:
        return "Provide a registered app id when using scope.type='app'."
    return f"Review {field_path} and correct the value or required structure."


def format_validation_error(error: ValidationError | Exception) -> str:
    """Render pydantic or parser errors with field names and suggestions."""

    if isinstance(error, ValidationError):
        messages: list[str] = []
        for issue in error.errors():
            location = tuple(issue.get("loc", ()))
            field_path = ".".join(str(part) for part in location) if location else "spec"
            message = issue.get("msg", "Invalid value")
            suggestion = _suggestion_for_error(location, message)
            messages.append(f"{field_path}: {message} Suggestion: {suggestion}")
        return "\n".join(messages)
    return str(error)


def load_harness_spec(spec_file: str | Path, repo_root: str | Path | None = None) -> HarnessSpec:
    """Load, normalize, and validate a harness spec file."""

    spec_path = Path(spec_file).resolve()
    if not spec_path.is_file():
        raise HarnessSpecError(f"Harness spec not found: {spec_path}")

    resolved_repo_root = Path(repo_root).resolve() if repo_root is not None else discover_repo_root(spec_path)

    try:
        if spec_path.suffix.lower() == ".json":
            raw_data = json.loads(spec_path.read_text(encoding="utf-8"))
        else:
            raw_data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise HarnessSpecError(f"Failed to parse {spec_path.name}: {exc}") from exc

    if not isinstance(raw_data, dict):
        raise HarnessSpecError(f"Harness spec must be a mapping/object: {spec_path}")

    normalized = _normalize_spec_data(raw_data, spec_path, resolved_repo_root)
    try:
        return HarnessSpec.model_validate(normalized)
    except ValidationError as exc:
        raise HarnessSpecError(format_validation_error(exc)) from exc


def write_harness_schema(output_path: str | Path) -> Path:
    """Write the HarnessSpec JSON schema to disk."""

    destination = Path(output_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(harness_schema(), indent=2) + "\n", encoding="utf-8")
    return destination


def default_retry_policy() -> RetryPolicy:
    """Return the default retry policy used by the loader and runtime."""

    return RetryPolicy()