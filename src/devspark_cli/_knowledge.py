"""OKF knowledge document helpers and coverage validation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = ROOT / "templates" / "schemas" / "okf-knowledge-document.schema.json"
FR_RE = re.compile(r"\bFR-\d{3}\b")
TASK_RE = re.compile(r"\bT\d{3}\b")


@dataclass(frozen=True)
class KnowledgeDocument:
    path: Path
    frontmatter: dict[str, Any]


def extract_frontmatter(path: Path) -> dict[str, Any]:
    """Extract YAML frontmatter from a Markdown file."""

    text = path.read_text(encoding="utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.startswith("---\n"):
        raise ValueError("missing YAML frontmatter")
    try:
        _start, raw_yaml, _body = normalized.split("---\n", 2)
    except ValueError as exc:
        raise ValueError("unterminated YAML frontmatter") from exc
    data = yaml.safe_load(raw_yaml) or {}
    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    return data


def load_schema(schema_path: Path = DEFAULT_SCHEMA) -> dict[str, Any]:
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_frontmatter(frontmatter: dict[str, Any], schema_path: Path = DEFAULT_SCHEMA) -> list[str]:
    """Return schema validation errors for a frontmatter object."""

    validator = Draft202012Validator(load_schema(schema_path))
    return sorted(error.message for error in validator.iter_errors(frontmatter))


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return [str(value)]


def _find_spec_requirement_ids(feature_dir: Path) -> set[str]:
    spec_path = feature_dir / "spec.md"
    if not spec_path.is_file():
        return set()
    return set(FR_RE.findall(spec_path.read_text(encoding="utf-8")))


def _find_task_ids(feature_dir: Path) -> set[str]:
    tasks_path = feature_dir / "tasks.md"
    if not tasks_path.is_file():
        return set()
    return set(TASK_RE.findall(tasks_path.read_text(encoding="utf-8")))


def _collect_documents(knowledge_dir: Path) -> tuple[list[KnowledgeDocument], list[str]]:
    documents: list[KnowledgeDocument] = []
    messages: list[str] = []
    for path in sorted(knowledge_dir.glob("*.md")):
        try:
            frontmatter = extract_frontmatter(path)
        except ValueError as exc:
            messages.append(f"{path.name}: {exc}")
            continue
        errors = validate_frontmatter(frontmatter)
        if errors:
            messages.extend(f"{path.name}: {error}" for error in errors)
        documents.append(KnowledgeDocument(path=path, frontmatter=frontmatter))
    return documents, messages


def validate_knowledge_coverage(feature_dir: Path) -> dict[str, Any]:
    """Validate advisory OKF coverage for one feature directory."""

    feature_dir = feature_dir.resolve()
    knowledge_dir = feature_dir / "knowledge"
    if not knowledge_dir.is_dir():
        return {
            "status": "skipped",
            "feature_dir": str(feature_dir),
            "knowledge_dir": str(knowledge_dir),
            "requirements_total": 0,
            "tasks_total": 0,
            "gate_evidence_total": 0,
            "requirements_covered": 0,
            "requirements_uncovered": [],
            "tasks_without_requirements": [],
            "evidence_without_requirements": [],
            "messages": ["knowledge/ directory not found; coverage validation skipped"],
        }

    documents, messages = _collect_documents(knowledge_dir)
    spec_requirements = _find_spec_requirement_ids(feature_dir)
    task_ids_from_tasks = _find_task_ids(feature_dir)
    requirements: set[str] = set(spec_requirements)
    tasks: set[str] = set()
    evidence: set[str] = set()
    requirement_to_tasks: dict[str, set[str]] = {}
    requirement_to_evidence: dict[str, set[str]] = {}

    for document in documents:
        frontmatter = document.frontmatter
        doc_requirements = set(_as_list(frontmatter.get("requirement_ids")))
        doc_tasks = set(_as_list(frontmatter.get("task_ids")))
        doc_evidence = set(_as_list(frontmatter.get("gate_evidence_ids")))
        requirements.update(doc_requirements)
        tasks.update(doc_tasks)
        evidence.update(doc_evidence)
        for req_id in doc_requirements:
            requirement_to_tasks.setdefault(req_id, set()).update(doc_tasks)
            requirement_to_evidence.setdefault(req_id, set()).update(doc_evidence)

    if not documents:
        messages.append("knowledge/ contains no Markdown documents")

    requirements_uncovered = sorted(
        req_id
        for req_id in requirements
        if not requirement_to_tasks.get(req_id) or not requirement_to_evidence.get(req_id)
    )
    linked_tasks = {task for values in requirement_to_tasks.values() for task in values}
    linked_evidence = {item for values in requirement_to_evidence.values() for item in values}
    tasks_without_requirements = sorted((tasks | task_ids_from_tasks) - linked_tasks)
    evidence_without_requirements = sorted(evidence - linked_evidence)

    for req_id in requirements_uncovered:
        has_tasks = bool(requirement_to_tasks.get(req_id))
        has_evidence = bool(requirement_to_evidence.get(req_id))
        if has_tasks and not has_evidence:
            messages.append(f"{req_id} has tasks but no gate evidence")
        elif has_evidence and not has_tasks:
            messages.append(f"{req_id} has gate evidence but no tasks")
        else:
            messages.append(f"{req_id} has no task or gate evidence coverage")

    status = "ok" if not messages and not requirements_uncovered else "warn"
    return {
        "status": status,
        "feature_dir": str(feature_dir),
        "knowledge_dir": str(knowledge_dir),
        "requirements_total": len(requirements),
        "tasks_total": len(tasks | task_ids_from_tasks),
        "gate_evidence_total": len(evidence),
        "requirements_covered": len(requirements) - len(requirements_uncovered),
        "requirements_uncovered": requirements_uncovered,
        "tasks_without_requirements": tasks_without_requirements,
        "evidence_without_requirements": evidence_without_requirements,
        "messages": messages,
    }


def _print_summary(report: dict[str, Any]) -> None:
    print(f"Knowledge coverage: {report['status']}")
    for key in ("requirements_total", "tasks_total", "gate_evidence_total", "requirements_covered"):
        print(f"{key}: {report[key]}")
    for message in report.get("messages", []):
        print(f"- {message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate DevSpark OKF knowledge coverage.")
    parser.add_argument("--feature-dir", required=True, help="Feature directory containing knowledge/.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    report = validate_knowledge_coverage(Path(args.feature_dir))
    if args.json:
        json.dump(report, sys.stdout, indent=2)
        print()
    else:
        _print_summary(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
