"""Build DevSpark v4 ontology derived metadata and generated reports."""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
ENTITIES_DIR = ROOT / ".knowledge" / "entities"
DECISIONS_DIR = ROOT / ".knowledge" / "governance" / "decisions"
ONTOLOGY_DIR = ROOT / ".knowledge" / "ontology"
GENERATOR_ID = "devspark.current_truth"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
LOCAL_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")

ALLOWED_KINDS = {
    "knowledge-model",
    "framework-template-set",
    "generated-integration-files",
    "repository-configuration",
    "ephemeral-state",
    "knowledge-site",
    "design-asset-set",
    "integration-catalog",
    "contributor-practice",
}

ALLOWED_RELATION_TYPES = {
    "describes",
    "derives_from",
    "extends",
    "generated_for",
    "scopes",
    "supports",
    "uses",
    "validates",
    "validated_by",
}

ALLOWED_EVIDENCE_TYPES = {"test", "code", "doc", "schema"}


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class Entity:
    entity_id: str
    path: Path
    data: dict[str, Any]
    layers: tuple[str, ...]
    derived_path: Path


@dataclass(frozen=True)
class Decision:
    decision_id: str
    path: Path
    data: dict[str, Any]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{rel(path)} must contain a YAML mapping")
    return data


def read_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    data = yaml.safe_load(parts[1]) or {}
    if not isinstance(data, dict):
        return {}
    return data


def load_entities(findings: list[Finding]) -> dict[str, Entity]:
    entities: dict[str, Entity] = {}
    if not ENTITIES_DIR.exists():
        findings.append(Finding("error", "missing-entities-root", rel(ENTITIES_DIR), "Entity root is missing."))
        return entities

    for folder in sorted(path for path in ENTITIES_DIR.iterdir() if path.is_dir()):
        entity_path = folder / "_entity.yaml"
        content_files = [path for path in folder.iterdir() if path.is_file()]
        if not entity_path.exists():
            if content_files:
                findings.append(
                    Finding(
                        "error",
                        "missing-entity-metadata",
                        rel(folder),
                        "Entity folder contains files but has no _entity.yaml.",
                    )
                )
            continue

        data = read_yaml(entity_path)
        entity_id = str(data.get("id", ""))
        if entity_id != folder.name:
            findings.append(
                Finding(
                    "error",
                    "entity-id-folder-mismatch",
                    rel(entity_path),
                    f"Entity id {entity_id!r} must match folder name {folder.name!r}.",
                )
            )
        if not ID_RE.match(entity_id):
            findings.append(Finding("error", "invalid-entity-id", rel(entity_path), "Entity id is not a valid slug."))

        kind = data.get("kind")
        if kind not in ALLOWED_KINDS:
            findings.append(
                Finding("error", "invalid-entity-kind", rel(entity_path), f"Unknown entity kind: {kind!r}.")
            )

        layers = tuple(
            sorted(
                path.name
                for path in folder.glob("*.md")
                if not path.name.startswith("_") and not path.name.endswith(".generated.md")
            )
        )
        entities[entity_id] = Entity(
            entity_id=entity_id,
            path=entity_path,
            data=data,
            layers=layers,
            derived_path=folder / "_derived.yaml",
        )
    return entities


def load_decisions(findings: list[Finding]) -> dict[str, Decision]:
    decisions: dict[str, Decision] = {}
    if not DECISIONS_DIR.exists():
        return decisions

    for path in sorted(DECISIONS_DIR.glob("*.md")):
        data = read_frontmatter(path)
        decision_id = str(data.get("id", path.stem))
        if not ID_RE.match(decision_id):
            findings.append(
                Finding("error", "invalid-decision-id", rel(path), f"Decision id {decision_id!r} is not a valid slug.")
            )
        if data.get("status") == "current" and "governs" not in data:
            findings.append(Finding("error", "missing-governs", rel(path), "Current decision must declare governs."))
        decisions[decision_id] = Decision(decision_id=decision_id, path=path, data=data)
    return decisions


def evidence_entries(subject: Entity | Decision) -> list[dict[str, Any]]:
    entries = subject.data.get("evidence") or []
    return entries if isinstance(entries, list) else []


def local_ref_exists(ref_value: str) -> bool:
    if not ref_value or LOCAL_REF_RE.match(ref_value):
        return True
    normalized = ref_value.split("#", 1)[0]
    if "::" in normalized:
        normalized = normalized.split("::", 1)[0]
    if not normalized:
        return True
    return (ROOT / normalized).exists()


def validate_evidence(subjects: list[Entity | Decision], findings: list[Finding]) -> None:
    for subject in subjects:
        entries = evidence_entries(subject)
        has_execution_evidence = any(
            isinstance(entry, dict)
            and entry.get("type") == "test"
            and entry.get("verified_by") == "execution"
            for entry in entries
        )
        if not entries:
            findings.append(Finding("error", "missing-evidence", rel(subject.path), "No evidence entries found."))
            continue
        for index, entry in enumerate(entries, start=1):
            path = f"{rel(subject.path)}#evidence[{index}]"
            if not isinstance(entry, dict):
                findings.append(Finding("error", "invalid-evidence", path, "Evidence entry must be a mapping."))
                continue
            evidence_type = entry.get("type")
            verified_by = entry.get("verified_by")
            ref_value = str(entry.get("ref", ""))
            if evidence_type not in ALLOWED_EVIDENCE_TYPES:
                findings.append(Finding("error", "invalid-evidence-type", path, f"Unknown evidence type: {evidence_type!r}."))
            if evidence_type == "test" and verified_by != "execution":
                findings.append(Finding("error", "test-not-executed", path, "Test evidence must use verified_by: execution."))
            if evidence_type in {"code", "doc", "schema"} and verified_by != "inspection":
                findings.append(
                    Finding("error", "inspection-evidence-mode", path, f"{evidence_type} evidence must use inspection.")
                )
            if not ref_value:
                findings.append(Finding("error", "missing-evidence-ref", path, "Evidence ref is empty."))
            elif not local_ref_exists(ref_value):
                findings.append(Finding("error", "missing-evidence-ref", path, f"Evidence ref does not resolve: {ref_value}"))
            if evidence_type == "code" and verified_by == "inspection" and not has_execution_evidence:
                if "test_attempted" not in entry or not entry.get("fallback_reason"):
                    findings.append(
                        Finding(
                            "warning",
                            "inspection-without-fallback",
                            path,
                            "Code inspection evidence should include test_attempted and fallback_reason.",
                        )
                    )


def validate_relations(entities: dict[str, Entity], findings: list[Finding]) -> None:
    for entity in entities.values():
        relations = entity.data.get("relations") or []
        if not isinstance(relations, list):
            findings.append(Finding("error", "invalid-relations", rel(entity.path), "relations must be a list."))
            continue
        for index, relation in enumerate(relations, start=1):
            path = f"{rel(entity.path)}#relations[{index}]"
            if not isinstance(relation, dict):
                findings.append(Finding("error", "invalid-relation", path, "Relation entry must be a mapping."))
                continue
            relation_type = relation.get("type")
            target = relation.get("object")
            if relation_type not in ALLOWED_RELATION_TYPES:
                findings.append(Finding("error", "invalid-relation-type", path, f"Unknown relation type: {relation_type!r}."))
            if target not in entities:
                findings.append(Finding("error", "dangling-relation", path, f"Relation target does not exist: {target!r}."))


def decision_governance(decisions: dict[str, Decision], entities: dict[str, Entity], findings: list[Finding]) -> dict[str, list[str]]:
    governed_by: dict[str, list[str]] = {entity_id: [] for entity_id in entities}
    for decision in decisions.values():
        governs = decision.data.get("governs") or []
        if not isinstance(governs, list):
            findings.append(Finding("error", "invalid-governs", rel(decision.path), "governs must be a list."))
            continue
        for entity_id in governs:
            if entity_id not in entities:
                findings.append(
                    Finding("error", "unknown-governed-entity", rel(decision.path), f"Unknown governed entity: {entity_id!r}.")
                )
                continue
            governed_by[entity_id].append(decision.decision_id)
    return {key: sorted(set(value)) for key, value in governed_by.items()}


def expected_derived(entity: Entity, governed_by: dict[str, list[str]]) -> dict[str, Any]:
    generated_on = date.today().isoformat()
    if entity.derived_path.exists():
        try:
            existing = read_yaml(entity.derived_path)
            generated_on = str(existing.get("generated_on") or generated_on)
        except (OSError, ValueError, yaml.YAMLError):
            pass
    return {
        "constrained_by": governed_by.get(entity.entity_id, []),
        "generated_by": GENERATOR_ID,
        "generated_on": generated_on,
    }


def required_layers(entity: Entity) -> list[str]:
    configured = entity.data.get("required_layers")
    if isinstance(configured, list) and configured:
        return [str(layer) for layer in configured]
    return ["architecture.md"]


def row(values: list[str]) -> str:
    return "| " + " | ".join(value.replace("\n", " ") for value in values) + " |"


def finding_table(title: str, findings: list[Finding]) -> str:
    lines = [f"# {title}", "", row(["Level", "Code", "Path", "Message"]), "|---|---|---|---|"]
    if findings:
        for finding in findings:
            lines.append(row([finding.level, f"`{finding.code}`", finding.path, finding.message]))
    else:
        lines.append(row(["info", "`ok`", "-", "No issues found."]))
    return "\n".join(lines) + "\n"


def build_reports(
    entities: dict[str, Entity],
    decisions: dict[str, Decision],
    governed_by: dict[str, list[str]],
    findings: list[Finding],
) -> dict[Path, str]:
    reports: dict[Path, str] = {}

    coverage = [
        "# Knowledge Coverage",
        "",
        row(["Entity", "Kind", "Lifecycle", "Root", "Layers", "Relations", "Governed By", "Evidence"]),
        "|---|---|---|---|---|---:|---|---:|",
    ]
    for entity in entities.values():
        evidence_count = len(evidence_entries(entity))
        relations = entity.data.get("relations") or []
        coverage.append(
            row(
                [
                    f"`{entity.entity_id}`",
                    str(entity.data.get("kind", "-")),
                    str(entity.data.get("lifecycle", "current")),
                    str(entity.data.get("root", f".knowledge/entities/{entity.entity_id}")),
                    ", ".join(entity.layers) or "-",
                    str(len(relations) if isinstance(relations, list) else 0),
                    ", ".join(governed_by.get(entity.entity_id, [])) or "-",
                    str(evidence_count),
                ]
            )
        )
    reports[ONTOLOGY_DIR / "coverage.generated.md"] = "\n".join(coverage) + "\n"

    relation_lines = [
        "# Entity Relations",
        "",
        row(["Subject", "Type", "Object"]),
        "|---|---|---|",
    ]
    for entity in entities.values():
        relations = entity.data.get("relations") or []
        for relation in relations if isinstance(relations, list) else []:
            if isinstance(relation, dict):
                relation_lines.append(
                    row([f"`{entity.entity_id}`", str(relation.get("type", "-")), f"`{relation.get('object', '-')}`"])
                )
    if len(relation_lines) == 4:
        relation_lines.append(row(["-", "-", "-"]))
    reports[ONTOLOGY_DIR / "relations.generated.md"] = "\n".join(relation_lines) + "\n"

    governance = [
        "# Governance Coverage",
        "",
        row(["Decision", "Status", "Governs", "Evidence"]),
        "|---|---|---|---:|",
    ]
    for decision in decisions.values():
        governs = decision.data.get("governs") or []
        governance.append(
            row(
                [
                    f"`{decision.decision_id}`",
                    str(decision.data.get("status", "-")),
                    ", ".join(f"`{entity_id}`" for entity_id in governs) if isinstance(governs, list) else "-",
                    str(len(evidence_entries(decision))),
                ]
            )
        )
    reports[ONTOLOGY_DIR / "governance.generated.md"] = "\n".join(governance) + "\n"

    evidence_findings = [finding for finding in findings if "evidence" in finding.code or "inspection" in finding.code]
    reports[ONTOLOGY_DIR / "evidence.generated.md"] = finding_table("Evidence Status", evidence_findings)

    gap_findings = [finding for finding in findings if finding not in evidence_findings]
    for entity in entities.values():
        for layer in required_layers(entity):
            if layer not in entity.layers:
                gap_findings.append(
                    Finding(
                        "error",
                        "missing-required-layer",
                        rel(entity.path.parent),
                        f"Required layer is missing: {layer}",
                    )
                )
    reports[ONTOLOGY_DIR / "gaps.generated.md"] = finding_table("Ontology Gaps", sorted(gap_findings, key=lambda item: (item.level, item.code, item.path)))

    return reports


def rendered_yaml(data: dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=False)


def compare_or_write(path: Path, expected: str, write: bool, problems: list[str]) -> None:
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            path.write_text(expected, encoding="utf-8")
        return

    actual = path.read_text(encoding="utf-8") if path.exists() else ""
    if actual != expected:
        diff = "\n".join(
            difflib.unified_diff(
                actual.splitlines(),
                expected.splitlines(),
                fromfile=rel(path),
                tofile=f"{rel(path)} expected",
                lineterm="",
            )
        )
        problems.append(diff)


def run(write: bool) -> int:
    findings: list[Finding] = []
    entities = load_entities(findings)
    decisions = load_decisions(findings)
    validate_relations(entities, findings)
    validate_evidence([*entities.values(), *decisions.values()], findings)
    governed_by = decision_governance(decisions, entities, findings)
    reports = build_reports(entities, decisions, governed_by, findings)

    problems: list[str] = []
    for entity in entities.values():
        compare_or_write(entity.derived_path, rendered_yaml(expected_derived(entity, governed_by)), write, problems)
    for path, expected in reports.items():
        compare_or_write(path, expected, write, problems)

    error_count = sum(1 for finding in findings if finding.level == "error")
    if write:
        print(f"Knowledge ontology generated for {len(entities)} entities and {len(decisions)} decisions.")
        return 1 if error_count else 0

    if problems:
        print("Generated ontology files are stale. Run: python scripts/python/build_knowledge_index.py --write")
        print("\n\n".join(problems))
        return 1
    if error_count:
        for finding in findings:
            if finding.level == "error":
                print(f"{finding.level}: {finding.code}: {finding.path}: {finding.message}")
        return 1
    print(f"Knowledge ontology validated for {len(entities)} entities and {len(decisions)} decisions.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write generated ontology files")
    mode.add_argument("--check", action="store_true", help="check generated ontology files")
    args = parser.parse_args()
    return run(write=args.write)


if __name__ == "__main__":
    sys.exit(main())
