"""Build and check the DevSpark current-truth knowledge index.

This is the single knowledge engine. It validates `.knowledge/` against the
entity-node and knowledge-node contracts, writes `.knowledge/ontology/index.json`
and `.knowledge/ontology/coverage.json`, ranks documents for concept search, and
detects content drift for pinned `source_of_truth` claims.

Modes (one per invocation):

  (default)          validate and write index.json / coverage.json
  --check            validate and fail when committed output is stale; never writes
  --search QUERY     rank knowledge by concept (index classes only; no body text)
  --detect-drift     compare pinned claims to retained baselines (read-only);
                     requires --base/--head or --full-inventory
  --pin-claim PATH   retain a canonical baseline for PATH and print the claim
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

import yaml


def discover_root(explicit_root: str | None = None) -> Path:
    """Find the consumer repository for both source and installed layouts."""
    if explicit_root:
        return Path(explicit_root).expanduser().resolve()

    configured_root = os.environ.get("DEVSPARK_REPO_ROOT")
    if configured_root:
        return Path(configured_root).expanduser().resolve()

    script_path = Path(__file__).resolve()
    # Source checkout: scripts/<script> -> parents[1].
    # Installed copy: .devspark/scripts/<script> -> parents[2].
    # Legacy installed copy: .devspark/scripts/python/<script> -> parents[3].
    candidates = [parent for parent in script_path.parents[1:4]]
    for candidate in candidates:
        if (candidate / ".knowledge").is_dir() or (candidate / ".git").exists():
            return candidate
    return Path.cwd().resolve()


ROOT = discover_root()
GENERATOR_ID = "devspark.build_knowledge_index"
INDEX_SCHEMA_VERSION = 1
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
SEQUENTIAL_NAME_RE = re.compile(r"^(adr[-_]?)?\d+[-_.]", re.IGNORECASE)
URI_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

DECISION_TYPE = "governance-decision"
FLAT_TYPE = "flat-knowledge"
BANNED_KEYS = ("status", "lifecycle", "supersedes", "superseded-by", "superseded_by", "replaced", "obsolete")
EPHEMERAL_PREFIXES = (".devspark.work/", ".archive/")
ENFORCEMENT_MODES = ("last-verified", "pinned-claims")
CLAIM_PROFILES = ("text", "exact")
VERIFICATION_STATES = ("verified", "unverified")

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

# Discovery ranking. Each class contributes its weight at most once per query
# term, never once per occurrence; strongest signal first.
RANK_WEIGHTS = {
    "id_title": 100,
    "alias": 60,
    "heading": 30,
    "metadata": 15,
    "body": 5,
}
RANK_ORDER = tuple(RANK_WEIGHTS)

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "did", "do", "does", "done", "for", "from",
    "how", "in", "into", "is", "it", "of", "on", "or", "the", "this", "that", "to", "was", "were",
    "what", "when", "where", "which", "who", "why", "with", "work", "works",
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    path: str
    message: str
    entity: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"level": self.level, "code": self.code, "path": self.path, "message": self.message}
        if self.entity:
            data["entity"] = self.entity
        return data


@dataclass
class Document:
    path: Path
    owner: str
    doc_type: str
    frontmatter: dict[str, Any]
    title: str
    headings: list[str]
    is_layer: bool = False


@dataclass
class Entity:
    entity_id: str
    path: Path
    data: dict[str, Any]
    layers: tuple[str, ...]
    documents: list[Document] = field(default_factory=list)


@dataclass
class Decision:
    decision_id: str
    document: Document

    @property
    def data(self) -> dict[str, Any]:
        return self.document.frontmatter

    @property
    def path(self) -> Path:
        return self.document.path


@dataclass
class Knowledge:
    root: Path
    entities: dict[str, Entity]
    decisions: dict[str, Decision]
    governance_docs: list[Document]
    config: dict[str, Any]
    findings: list[Finding]
    flat_docs: list[Document] = field(default_factory=list)

    def all_documents(self) -> list[Document]:
        docs: list[Document] = []
        for entity in self.entities.values():
            docs.extend(entity.documents)
        docs.extend(decision.document for decision in self.decisions.values())
        docs.extend(self.governance_docs)
        docs.extend(self.flat_docs)
        return sorted(docs, key=lambda doc: rel(doc.path))


# ---------------------------------------------------------------------------
# Paths and parsing helpers
# ---------------------------------------------------------------------------


def knowledge_dir() -> Path:
    return ROOT / ".knowledge"


def entities_dir() -> Path:
    return knowledge_dir() / "entities"


def governance_dir() -> Path:
    return knowledge_dir() / "governance"


def decisions_dir() -> Path:
    return governance_dir() / "decisions"


def ontology_dir() -> Path:
    return knowledge_dir() / "ontology"


def baselines_dir() -> Path:
    return ontology_dir() / "baselines"


def config_path() -> Path:
    return knowledge_dir() / "knowledge.config.yaml"


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{rel(path)} must contain a YAML mapping")
    return data


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        data = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}, parts[2]
    if not isinstance(data, dict):
        return {}, parts[2]
    return data, parts[2]


def markdown_headings(body: str) -> tuple[str, list[str]]:
    """Return (first H1 title, all heading texts) ignoring fenced code."""
    title = ""
    headings: list[str] = []
    in_fence = False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_RE.match(stripped)
        if not match:
            continue
        text = match.group(2).strip()
        if len(match.group(1)) == 1 and not title:
            title = text
        headings.append(text)
    return title, headings


def string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if isinstance(item, (str, int, float)) and str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def claim_path(entry: Any) -> str:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        return str(entry.get("path", ""))
    return ""


def normalize_ref(ref_value: str) -> str:
    normalized = ref_value.split("#", 1)[0]
    if "::" in normalized:
        normalized = normalized.split("::", 1)[0]
    return normalized.strip()


def is_external(ref_value: str) -> bool:
    return bool(URI_RE.match(ref_value))


def local_ref_exists(ref_value: str) -> bool:
    if not ref_value or is_external(ref_value):
        return True
    normalized = normalize_ref(ref_value)
    if not normalized:
        return True
    return (ROOT / normalized).exists()


def is_ephemeral(ref_value: str) -> bool:
    normalized = normalize_ref(ref_value)
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return any(normalized.startswith(prefix) or normalized == prefix.rstrip("/") for prefix in EPHEMERAL_PREFIXES)


def load_document(path: Path, owner: str, doc_type: str, is_layer: bool = False) -> Document:
    frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    h1, headings = markdown_headings(body)
    title = str(frontmatter.get("title") or h1 or path.stem.replace("-", " "))
    return Document(
        path=path,
        owner=owner,
        doc_type=doc_type,
        frontmatter=frontmatter,
        title=title,
        headings=headings,
        is_layer=is_layer,
    )


def document_body(path: Path) -> str:
    _, body = split_frontmatter(path.read_text(encoding="utf-8"))
    return body


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_config(findings: list[Finding]) -> dict[str, Any]:
    config: dict[str, Any] = {"knowledge_drift": {"enforcement": "last-verified"}}
    path = config_path()
    if not path.exists():
        return config
    try:
        data = read_yaml(path)
    except (ValueError, yaml.YAMLError) as exc:
        findings.append(Finding("error", "invalid-config", rel(path), str(exc)))
        return config
    drift = data.get("knowledge_drift") or {}
    enforcement = drift.get("enforcement", "last-verified") if isinstance(drift, dict) else None
    if enforcement not in ENFORCEMENT_MODES:
        findings.append(
            Finding(
                "error",
                "invalid-drift-enforcement",
                rel(path),
                f"knowledge_drift.enforcement must be one of {', '.join(ENFORCEMENT_MODES)}.",
            )
        )
        enforcement = "last-verified"
    config["knowledge_drift"] = {"enforcement": enforcement}
    return config


def check_banned_keys(data: dict[str, Any], path: Path, findings: list[Finding], entity: str | None = None) -> None:
    for key in BANNED_KEYS:
        if key in data:
            findings.append(
                Finding(
                    "error",
                    "banned-lifecycle-key",
                    rel(path),
                    f"`{key}` is banned on current knowledge; edit in place or delete instead.",
                    entity,
                )
            )


def load_entities(findings: list[Finding]) -> dict[str, Entity]:
    entities: dict[str, Entity] = {}
    root = entities_dir()
    if not root.exists():
        findings.append(Finding("error", "missing-entities-root", rel(root), "Entity root is missing."))
        return entities

    for folder in sorted(path for path in root.iterdir() if path.is_dir()):
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

        try:
            data = read_yaml(entity_path)
        except (ValueError, yaml.YAMLError) as exc:
            findings.append(Finding("error", "invalid-entity-metadata", rel(entity_path), str(exc), folder.name))
            continue
        entity_id = str(data.get("id", ""))
        if entity_id != folder.name:
            findings.append(
                Finding(
                    "error",
                    "entity-id-folder-mismatch",
                    rel(entity_path),
                    f"Entity id {entity_id!r} must match folder name {folder.name!r}.",
                    folder.name,
                )
            )
        if not ID_RE.match(entity_id):
            findings.append(Finding("error", "invalid-entity-id", rel(entity_path), "Entity id is not a valid slug.", folder.name))
        kind = data.get("kind")
        if kind not in ALLOWED_KINDS:
            findings.append(
                Finding("error", "invalid-entity-kind", rel(entity_path), f"Unknown entity kind: {kind!r}.", entity_id)
            )
        check_banned_keys(data, entity_path, findings, entity_id)
        if "constrained_by" in data and not isinstance(data.get("constrained_by"), list):
            findings.append(
                Finding("error", "invalid-constrained-by", rel(entity_path), "constrained_by must be a list.", entity_id)
            )
        derived = folder / "_derived.yaml"
        if derived.exists():
            findings.append(
                Finding(
                    "error",
                    "legacy-derived-metadata",
                    rel(derived),
                    "_derived.yaml is retired; move constrained_by into _entity.yaml "
                    "(run migrate-knowledge-to-entities.py).",
                    entity_id,
                )
            )

        layers = tuple(
            sorted(
                path.name
                for path in folder.glob("*.md")
                if not path.name.startswith("_")
            )
        )
        entity = Entity(entity_id=entity_id, path=entity_path, data=data, layers=layers)
        for md_path in sorted(folder.rglob("*.md")):
            if md_path.name.startswith("_"):
                continue
            is_layer = md_path.parent == folder and md_path.name in layers
            entity.documents.append(
                load_document(md_path, entity_id, "entity-layer" if is_layer else "entity-content", is_layer)
            )
        entities[entity_id] = entity
    return entities


def load_decisions(findings: list[Finding]) -> dict[str, Decision]:
    decisions: dict[str, Decision] = {}
    root = decisions_dir()
    if not root.exists():
        return decisions

    titles: dict[str, str] = {}
    for path in sorted(root.glob("*.md")):
        document = load_document(path, "governance", DECISION_TYPE)
        data = document.frontmatter
        # README files document the collection and are not decision records.
        # More generally, only Markdown files with frontmatter can be decisions.
        if not data:
            continue
        decision_id = str(data.get("id", path.stem))
        if not ID_RE.match(decision_id):
            findings.append(
                Finding("error", "invalid-decision-id", rel(path), f"Decision id {decision_id!r} is not a valid slug.")
            )
        if decision_id != path.stem:
            findings.append(
                Finding(
                    "error",
                    "decision-id-filename-mismatch",
                    rel(path),
                    "Decision files are keyed by topic: the filename must equal the decision id.",
                )
            )
        if SEQUENTIAL_NAME_RE.match(path.stem):
            findings.append(
                Finding(
                    "error",
                    "sequential-decision-name",
                    rel(path),
                    "Decisions are keyed by domain/topic, never by sequential number.",
                )
            )
        if data.get("type") != DECISION_TYPE:
            findings.append(
                Finding("error", "invalid-decision-type", rel(path), f"Decision frontmatter must set type: {DECISION_TYPE}.")
            )
        if not str(data.get("title", "")).strip():
            findings.append(Finding("error", "missing-decision-title", rel(path), "Decision frontmatter must set title."))
        if "governs" in data:
            findings.append(
                Finding(
                    "error",
                    "legacy-governs-key",
                    rel(path),
                    "`governs` is retired; declare `constrains` (run migrate-knowledge-to-entities.py).",
                )
            )
        if "layer" in data:
            findings.append(Finding("error", "decision-layer-key", rel(path), "A decision is one topic; `layer` is not allowed."))
        check_banned_keys(data, path, findings)
        if decision_id in decisions:
            findings.append(
                Finding("error", "duplicate-decision-topic", rel(path), f"Decision id {decision_id!r} is declared twice.")
            )
        topic = re.sub(r"\s+", " ", str(data.get("title", "")).strip().lower())
        if topic:
            if topic in titles:
                findings.append(
                    Finding(
                        "error",
                        "duplicate-decision-topic",
                        rel(path),
                        f"Decision title duplicates {titles[topic]}; keep one current file per topic.",
                    )
                )
            else:
                titles[topic] = rel(path)
        decisions[decision_id] = Decision(decision_id=decision_id, document=document)
    return decisions


def load_governance_docs() -> list[Document]:
    root = governance_dir()
    if not root.exists():
        return []
    return [
        load_document(path, "governance", "governance")
        for path in sorted(root.glob("*.md"))
        if path.name.lower() != "readme.md"
    ]


def load_flat_docs() -> list[Document]:
    """Flat knowledge nodes: `.knowledge/<topic>.md` and `.knowledge/guides/**`.

    A flat node is a current-truth guide or architectural note that does not
    justify an entity. It follows the same currency rules as entity layers.
    """
    root = knowledge_dir()
    if not root.exists():
        return []
    paths = [path for path in root.glob("*.md")]
    guides = root / "guides"
    if guides.is_dir():
        paths.extend(guides.rglob("*.md"))
    return [
        load_document(path, "knowledge", FLAT_TYPE)
        for path in sorted(paths)
        if path.name.lower() != "readme.md" and not path.name.startswith("_")
    ]


def node_id(document: Document) -> str:
    return str(document.frontmatter.get("id") or document.path.stem)


def load_knowledge(root: Path | None = None) -> Knowledge:
    global ROOT
    if root is not None:
        ROOT = root
    findings: list[Finding] = []
    config = load_config(findings)
    entities = load_entities(findings)
    decisions = load_decisions(findings)
    governance_docs = load_governance_docs()
    flat_docs = load_flat_docs()
    return Knowledge(
        root=ROOT,
        entities=entities,
        decisions=decisions,
        governance_docs=governance_docs,
        flat_docs=flat_docs,
        config=config,
        findings=findings,
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def evidence_entries(data: dict[str, Any]) -> list[Any]:
    entries = data.get("evidence") or []
    return entries if isinstance(entries, list) else []


def validate_evidence_list(
    data: dict[str, Any],
    path: Path,
    findings: list[Finding],
    entity: str | None,
    required: bool,
) -> None:
    entries = evidence_entries(data)
    if not entries:
        if required:
            findings.append(
                Finding("error", "missing-evidence", rel(path), "No evidence entries found; every claim must be checkable.", entity)
            )
        return
    has_execution_evidence = any(
        isinstance(entry, dict) and entry.get("type") == "test" and entry.get("verified_by") == "execution"
        for entry in entries
    )
    for index, entry in enumerate(entries, start=1):
        where = f"{rel(path)}#evidence[{index}]"
        if not isinstance(entry, dict):
            findings.append(Finding("error", "invalid-evidence", where, "Evidence entry must be a mapping.", entity))
            continue
        evidence_type = entry.get("type")
        verified_by = entry.get("verified_by")
        ref_value = str(entry.get("ref", ""))
        if evidence_type not in ALLOWED_EVIDENCE_TYPES:
            findings.append(Finding("error", "invalid-evidence-type", where, f"Unknown evidence type: {evidence_type!r}.", entity))
        if evidence_type == "test" and verified_by != "execution":
            findings.append(Finding("error", "test-not-executed", where, "Test evidence must use verified_by: execution.", entity))
        if evidence_type in {"code", "doc", "schema"} and verified_by != "inspection":
            findings.append(
                Finding("error", "inspection-evidence-mode", where, f"{evidence_type} evidence must use inspection.", entity)
            )
        if not ref_value:
            findings.append(Finding("error", "missing-evidence-ref", where, "Evidence ref is empty.", entity))
        elif is_ephemeral(ref_value):
            findings.append(
                Finding("error", "ephemeral-reference", where, f"Evidence must not cite temporary work: {ref_value}", entity)
            )
        elif not local_ref_exists(ref_value):
            findings.append(Finding("error", "missing-evidence-ref", where, f"Evidence ref does not resolve: {ref_value}", entity))
        if evidence_type == "code" and verified_by == "inspection" and not has_execution_evidence:
            if "test_attempted" not in entry or not entry.get("fallback_reason"):
                findings.append(
                    Finding(
                        "warning",
                        "inspection-without-fallback",
                        where,
                        "Code-only evidence should record test_attempted and fallback_reason.",
                        entity,
                    )
                )


def validate_claim_object(entry: dict[str, Any], where: str, findings: list[Finding], entity: str | None) -> None:
    profile = entry.get("profile", "text")
    if profile not in CLAIM_PROFILES:
        findings.append(Finding("error", "invalid-claim-profile", where, f"Unknown claim profile: {profile!r}.", entity))
    region = entry.get("region")
    if region is not None:
        try:
            parse_region(region)
        except ValueError as exc:
            findings.append(Finding("error", "invalid-claim-region", where, str(exc), entity))
    digest = str(entry.get("digest", ""))
    if not DIGEST_RE.match(digest):
        findings.append(Finding("error", "invalid-claim-digest", where, "Pinned claims need digest: sha256:<hex>.", entity))
    baseline = str(entry.get("baseline", ""))
    if not baseline:
        findings.append(Finding("error", "missing-claim-baseline", where, "Pinned claims must retain a baseline.", entity))
    elif not (ROOT / baseline).is_file():
        findings.append(Finding("error", "missing-claim-baseline", where, f"Baseline does not exist: {baseline}", entity))
    verification = entry.get("verification") or {}
    state = verification.get("state") if isinstance(verification, dict) else None
    if state not in VERIFICATION_STATES:
        findings.append(
            Finding(
                "error",
                "invalid-verification-state",
                where,
                f"verification.state must be one of {', '.join(VERIFICATION_STATES)}.",
                entity,
            )
        )


def validate_currency(
    document: Document,
    findings: list[Finding],
    enforcement: str,
    entity: str | None,
    required: bool,
) -> None:
    data = document.frontmatter
    path = document.path
    sources = data.get("source_of_truth")
    if sources is None:
        if required:
            findings.append(
                Finding("error", "missing-source-of-truth", rel(path), "Knowledge documents must declare source_of_truth.", entity)
            )
    elif not isinstance(sources, list) or not sources:
        findings.append(
            Finding("error", "invalid-source-of-truth", rel(path), "source_of_truth must be a non-empty list.", entity)
        )
    else:
        for index, entry in enumerate(sources, start=1):
            where = f"{rel(path)}#source_of_truth[{index}]"
            target = claim_path(entry)
            if not target:
                findings.append(Finding("error", "invalid-source-of-truth", where, "Claim path is empty.", entity))
                continue
            if is_ephemeral(target):
                findings.append(
                    Finding("error", "ephemeral-reference", where, f"source_of_truth must not cite temporary work: {target}", entity)
                )
            elif not local_ref_exists(target):
                findings.append(Finding("error", "missing-source-of-truth-ref", where, f"Path does not resolve: {target}", entity))
            if isinstance(entry, dict):
                validate_claim_object(entry, where, findings, entity)
            elif enforcement == "pinned-claims":
                findings.append(
                    Finding(
                        "warning",
                        "unpinned-claim",
                        where,
                        "Repository enforces pinned-claims; migrate this plain path to an object claim.",
                        entity,
                    )
                )
            elif not isinstance(entry, str):
                findings.append(Finding("error", "invalid-source-of-truth", where, "Claim must be a path or object.", entity))
    if required and not data.get("last_verified"):
        findings.append(
            Finding("error", "missing-last-verified", rel(path), "Knowledge documents must declare last_verified.", entity)
        )
    if "aliases" in data and not isinstance(data.get("aliases"), list):
        findings.append(Finding("error", "invalid-aliases", rel(path), "aliases must be a list of strings.", entity))


def validate_documents(knowledge: Knowledge) -> None:
    findings = knowledge.findings
    enforcement = knowledge.config["knowledge_drift"]["enforcement"]
    # Every Markdown document under an entity, including subfolders, is a
    # knowledge node and carries the currency pair.
    for entity in knowledge.entities.values():
        for document in entity.documents:
            check_banned_keys(document.frontmatter, document.path, findings, entity.entity_id)
            validate_currency(document, findings, enforcement, entity.entity_id, required=True)
            validate_evidence_list(document.frontmatter, document.path, findings, entity.entity_id, required=False)
    for decision in knowledge.decisions.values():
        validate_currency(decision.document, findings, enforcement, None, required=False)
        if not decision.data.get("last_verified"):
            findings.append(
                Finding("error", "missing-last-verified", rel(decision.path), "Decisions must declare last_verified.")
            )
    for document in knowledge.governance_docs:
        if document.frontmatter:
            check_banned_keys(document.frontmatter, document.path, findings)
            validate_currency(document, findings, enforcement, None, required=False)
            validate_evidence_list(document.frontmatter, document.path, findings, None, required=False)


def validate_relations(knowledge: Knowledge) -> None:
    for entity in knowledge.entities.values():
        relations = entity.data.get("relations") or []
        if not isinstance(relations, list):
            knowledge.findings.append(
                Finding("error", "invalid-relations", rel(entity.path), "relations must be a list.", entity.entity_id)
            )
            continue
        for index, relation in enumerate(relations, start=1):
            where = f"{rel(entity.path)}#relations[{index}]"
            if not isinstance(relation, dict):
                knowledge.findings.append(
                    Finding("error", "invalid-relation", where, "Relation entry must be a mapping.", entity.entity_id)
                )
                continue
            relation_type = relation.get("type")
            target = relation.get("object")
            if relation_type not in ALLOWED_RELATION_TYPES:
                knowledge.findings.append(
                    Finding("error", "invalid-relation-type", where, f"Unknown relation type: {relation_type!r}.", entity.entity_id)
                )
            if target not in knowledge.entities:
                knowledge.findings.append(
                    Finding("error", "dangling-relation", where, f"Relation target does not exist: {target!r}.", entity.entity_id)
                )


def validate_constraints(knowledge: Knowledge) -> None:
    """Validate the hand-authored constrains / constrained_by reciprocal pair."""
    findings = knowledge.findings
    for decision in knowledge.decisions.values():
        constrains = decision.data.get("constrains")
        if not isinstance(constrains, list) or not constrains:
            findings.append(
                Finding(
                    "error",
                    "missing-constrains",
                    rel(decision.path),
                    "Decisions must declare a non-empty `constrains` list of entity ids.",
                )
            )
            continue
        for entity_id in constrains:
            entity = knowledge.entities.get(str(entity_id))
            if entity is None:
                findings.append(
                    Finding("error", "unknown-constrained-entity", rel(decision.path), f"Unknown entity: {entity_id!r}.")
                )
                continue
            if decision.decision_id not in string_list(entity.data.get("constrained_by")):
                findings.append(
                    Finding(
                        "error",
                        "missing-constrained-by",
                        rel(entity.path),
                        f"Decision {decision.decision_id!r} constrains this entity; list it in constrained_by.",
                        entity.entity_id,
                    )
                )
    for entity in knowledge.entities.values():
        for decision_id in string_list(entity.data.get("constrained_by")):
            decision = knowledge.decisions.get(decision_id)
            if decision is None:
                findings.append(
                    Finding(
                        "error",
                        "unknown-constraining-decision",
                        rel(entity.path),
                        f"constrained_by names an unknown decision: {decision_id!r}.",
                        entity.entity_id,
                    )
                )
                continue
            if entity.entity_id not in string_list(decision.data.get("constrains")):
                findings.append(
                    Finding(
                        "error",
                        "missing-constrains",
                        rel(decision.path),
                        f"Entity {entity.entity_id!r} lists this decision in constrained_by; add it to constrains.",
                        entity.entity_id,
                    )
                )


def validate_entity_evidence(knowledge: Knowledge) -> None:
    for entity in knowledge.entities.values():
        validate_evidence_list(entity.data, entity.path, knowledge.findings, entity.entity_id, required=True)
    for decision in knowledge.decisions.values():
        validate_evidence_list(decision.data, decision.path, knowledge.findings, None, required=True)


def required_layers(entity: Entity) -> list[str]:
    configured = entity.data.get("required_layers")
    if isinstance(configured, list) and configured:
        return [str(layer) for layer in configured]
    return ["architecture.md"]


def validate_layers(knowledge: Knowledge) -> None:
    for entity in knowledge.entities.values():
        for layer in required_layers(entity):
            if layer not in entity.layers:
                knowledge.findings.append(
                    Finding(
                        "error",
                        "missing-required-layer",
                        rel(entity.path.parent),
                        f"Required layer is missing: {layer}",
                        entity.entity_id,
                    )
                )


def validate_baselines(knowledge: Knowledge) -> None:
    referenced = referenced_baselines(knowledge)
    root = baselines_dir()
    if not root.exists():
        return
    for path in sorted(root.iterdir()):
        if path.is_file() and rel(path) not in referenced:
            knowledge.findings.append(
                Finding("warning", "orphan-baseline", rel(path), "No pinned claim references this baseline.")
            )


def validate_legacy_outputs(knowledge: Knowledge) -> None:
    root = ontology_dir()
    if not root.exists():
        return
    for path in sorted(root.glob("*.generated.md")):
        knowledge.findings.append(
            Finding(
                "error",
                "legacy-generated-report",
                rel(path),
                "Markdown ontology reports are retired; index.json and coverage.json replace them.",
            )
        )


def validate_flat_docs(knowledge: Knowledge) -> None:
    findings = knowledge.findings
    enforcement = knowledge.config["knowledge_drift"]["enforcement"]
    taken = set(knowledge.entities) | set(knowledge.decisions)
    seen: dict[str, str] = {}
    for document in knowledge.flat_docs:
        identifier = node_id(document)
        if not ID_RE.match(identifier):
            findings.append(Finding("error", "invalid-node-id", rel(document.path), f"Node id {identifier!r} is not a valid slug."))
        if identifier in taken or identifier in seen:
            other = seen.get(identifier, "an entity or decision")
            findings.append(
                Finding("error", "duplicate-node-id", rel(document.path), f"Node id {identifier!r} is already used by {other}.")
            )
        seen.setdefault(identifier, rel(document.path))
        check_banned_keys(document.frontmatter, document.path, findings)
        validate_currency(document, findings, enforcement, None, required=True)
        validate_evidence_list(document.frontmatter, document.path, findings, None, required=False)


def known_node_ids(knowledge: Knowledge) -> set[str]:
    return set(knowledge.entities) | set(knowledge.decisions) | {node_id(doc) for doc in knowledge.flat_docs}


def link_references(data: dict[str, Any]) -> Any:
    links = data.get("links")
    if links is None:
        return []
    if not isinstance(links, dict):
        return None
    return links.get("references", [])


def validate_links(knowledge: Knowledge) -> None:
    """`links.references` must resolve to a node id or an existing path."""
    ids = known_node_ids(knowledge)
    subjects: list[tuple[Path, dict[str, Any], str | None]] = [
        (entity.path, entity.data, entity.entity_id) for entity in knowledge.entities.values()
    ]
    subjects.extend((doc.path, doc.frontmatter, doc.owner if doc.owner in knowledge.entities else None) for doc in knowledge.all_documents())
    for path, data, entity in subjects:
        references = link_references(data)
        if references is None or not isinstance(references, list):
            knowledge.findings.append(
                Finding("error", "invalid-links", rel(path), "links must be a mapping with a `references` list.", entity)
            )
            continue
        for index, value in enumerate(references, start=1):
            where = f"{rel(path)}#links.references[{index}]"
            target = str(value).strip()
            if not target or is_external(target):
                continue
            if is_ephemeral(target):
                knowledge.findings.append(
                    Finding("error", "ephemeral-reference", where, f"links must not cite temporary work: {target}", entity)
                )
            elif target not in ids and not local_ref_exists(target):
                knowledge.findings.append(
                    Finding("error", "dangling-reference", where, f"Reference is not a node id or existing path: {target}", entity)
                )


def validate(knowledge: Knowledge) -> Knowledge:
    validate_relations(knowledge)
    validate_entity_evidence(knowledge)
    validate_constraints(knowledge)
    validate_documents(knowledge)
    validate_flat_docs(knowledge)
    validate_links(knowledge)
    validate_layers(knowledge)
    validate_baselines(knowledge)
    validate_legacy_outputs(knowledge)
    return knowledge


# ---------------------------------------------------------------------------
# Generated output
# ---------------------------------------------------------------------------


def evidence_refs(data: dict[str, Any]) -> list[str]:
    return [str(entry.get("ref")) for entry in evidence_entries(data) if isinstance(entry, dict) and entry.get("ref")]


def document_record(document: Document) -> dict[str, Any]:
    data = document.frontmatter
    record: dict[str, Any] = {
        "path": rel(document.path),
        "owner": document.owner,
        "type": document.doc_type,
        "title": document.title,
        "aliases": string_list(data.get("aliases")),
        "headings": document.headings,
        "applies_to": string_list(data.get("appliesTo") or data.get("applies_to")),
        "source_of_truth": [claim_path(entry) for entry in (data.get("source_of_truth") or []) if claim_path(entry)]
        if isinstance(data.get("source_of_truth"), list)
        else [],
        "evidence": evidence_refs(data),
        "references": string_list(link_references(data)) if isinstance(link_references(data), list) else [],
    }
    if document.doc_type == FLAT_TYPE:
        record["id"] = node_id(document)
    if data.get("last_verified"):
        record["last_verified"] = str(data.get("last_verified"))
    return record


def contradiction_scopes(knowledge: Knowledge) -> list[dict[str, Any]]:
    """Graph-adjacent groups that audit compares for contradiction.

    Same entity, entities sharing a constraining decision, and objects citing
    the same evidence. Judging a contradiction inside a scope stays human.
    """
    scopes: list[dict[str, Any]] = []
    for entity in knowledge.entities.values():
        members = [rel(entity.path)] + [rel(doc.path) for doc in entity.documents if doc.is_layer]
        if len(members) > 1:
            scopes.append({"basis": f"entity:{entity.entity_id}", "members": members})
    for decision in knowledge.decisions.values():
        constrains = [str(item) for item in string_list(decision.data.get("constrains")) if item in knowledge.entities]
        if constrains:
            members = [rel(decision.path)] + [rel(knowledge.entities[item].path) for item in sorted(constrains)]
            scopes.append({"basis": f"decision:{decision.decision_id}", "members": members})
    citations: dict[str, set[str]] = {}
    subjects: list[tuple[str, dict[str, Any]]] = [(rel(entity.path), entity.data) for entity in knowledge.entities.values()]
    subjects.extend((rel(doc.path), doc.frontmatter) for doc in knowledge.all_documents() if doc.frontmatter)
    for subject_path, data in subjects:
        refs = set(normalize_ref(ref) for ref in evidence_refs(data))
        sources = data.get("source_of_truth")
        if isinstance(sources, list):
            refs.update(normalize_ref(claim_path(entry)) for entry in sources if claim_path(entry))
        for ref_value in refs:
            if ref_value:
                citations.setdefault(ref_value, set()).add(subject_path)
    for ref_value in sorted(citations):
        members = sorted(citations[ref_value])
        if len(members) > 1:
            scopes.append({"basis": f"evidence:{ref_value}", "members": members})
    return scopes


def build_index(knowledge: Knowledge) -> dict[str, Any]:
    entities = []
    for entity in knowledge.entities.values():
        data = entity.data
        relations = data.get("relations") if isinstance(data.get("relations"), list) else []
        entities.append(
            {
                "id": entity.entity_id,
                "name": str(data.get("name", entity.entity_id)),
                "kind": str(data.get("kind", "")),
                "summary": str(data.get("summary", "")),
                "path": rel(entity.path),
                "aliases": string_list(data.get("aliases")),
                "relations": [
                    {"type": str(item.get("type")), "object": str(item.get("object"))}
                    for item in relations
                    if isinstance(item, dict)
                ],
                "constrained_by": string_list(data.get("constrained_by")),
                "references": string_list(link_references(data)) if isinstance(link_references(data), list) else [],
                "evidence": evidence_refs(data),
                "layers": list(entity.layers),
            }
        )
    decisions = []
    for decision in knowledge.decisions.values():
        record = document_record(decision.document)
        record["id"] = decision.decision_id
        record["constrains"] = string_list(decision.data.get("constrains"))
        decisions.append(record)
    documents = [
        document_record(doc)
        for doc in knowledge.all_documents()
        if doc.doc_type != DECISION_TYPE
    ]
    return {
        "generated_by": GENERATOR_ID,
        "schema_version": INDEX_SCHEMA_VERSION,
        "entities": entities,
        "decisions": decisions,
        "documents": documents,
        "contradiction_scopes": contradiction_scopes(knowledge),
    }


def sorted_findings(findings: Iterable[Finding]) -> list[Finding]:
    return sorted(findings, key=lambda item: (item.level, item.code, item.path, item.message))


def build_coverage(knowledge: Knowledge) -> dict[str, Any]:
    by_entity: dict[str, list[Finding]] = {}
    for finding in knowledge.findings:
        if finding.entity:
            by_entity.setdefault(finding.entity, []).append(finding)
    entities = []
    for entity in knowledge.entities.values():
        required = required_layers(entity)
        entities.append(
            {
                "id": entity.entity_id,
                "required_layers": required,
                "present_layers": list(entity.layers),
                "missing_layers": [layer for layer in required if layer not in entity.layers],
                "evidence_count": len(evidence_entries(entity.data)),
                "constrained_by": string_list(entity.data.get("constrained_by")),
                "errors": sum(1 for item in by_entity.get(entity.entity_id, []) if item.level == "error"),
                "warnings": sum(1 for item in by_entity.get(entity.entity_id, []) if item.level == "warning"),
            }
        )
    decisions = [
        {
            "id": decision.decision_id,
            "constrains": string_list(decision.data.get("constrains")),
            "evidence_count": len(evidence_entries(decision.data)),
        }
        for decision in knowledge.decisions.values()
    ]
    findings = sorted_findings(knowledge.findings)
    return {
        "generated_by": GENERATOR_ID,
        "schema_version": INDEX_SCHEMA_VERSION,
        "drift_enforcement": knowledge.config["knowledge_drift"]["enforcement"],
        "summary": {
            "entities": len(entities),
            "decisions": len(decisions),
            "flat_nodes": len(knowledge.flat_docs),
            "errors": sum(1 for item in findings if item.level == "error"),
            "warnings": sum(1 for item in findings if item.level == "warning"),
        },
        "entities": entities,
        "decisions": decisions,
        "flat_nodes": [{"id": node_id(doc), "path": rel(doc.path)} for doc in knowledge.flat_docs],
        "findings": [item.as_dict() for item in findings],
    }


def render_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def expected_outputs(knowledge: Knowledge) -> dict[Path, str]:
    return {
        ontology_dir() / "index.json": render_json(build_index(knowledge)),
        ontology_dir() / "coverage.json": render_json(build_coverage(knowledge)),
    }


def stale_diff(path: Path, expected: str) -> str | None:
    actual = path.read_text(encoding="utf-8") if path.exists() else ""
    if actual == expected:
        return None
    return "\n".join(
        difflib.unified_diff(
            actual.splitlines(),
            expected.splitlines(),
            fromfile=rel(path),
            tofile=f"{rel(path)} expected",
            lineterm="",
            n=1,
        )
    )


def referenced_baselines(knowledge: Knowledge) -> set[str]:
    referenced: set[str] = set()
    for document in knowledge.all_documents():
        sources = document.frontmatter.get("source_of_truth")
        if not isinstance(sources, list):
            continue
        for entry in sources:
            if isinstance(entry, dict) and entry.get("baseline"):
                referenced.add(str(entry["baseline"]))
    return referenced


def finding_entities(knowledge: Knowledge, finding: Finding) -> set[str] | None:
    """Entities a finding belongs to; None means repository-wide."""
    if finding.entity:
        return {finding.entity}
    path = finding.path.split("#", 1)[0]
    for decision in knowledge.decisions.values():
        if rel(decision.path) == path:
            constrains = {item for item in string_list(decision.data.get("constrains")) if item in knowledge.entities}
            return constrains or None
    return None


def gating_errors(knowledge: Knowledge, scope: set[str] | None) -> list[Finding]:
    errors = [item for item in knowledge.findings if item.level == "error"]
    if not scope:
        return errors
    gating = []
    for item in errors:
        entities = finding_entities(knowledge, item)
        if entities is None or entities & scope:
            gating.append(item)
    return gating


def run_build(check: bool, scope: set[str] | None) -> int:
    knowledge = validate(load_knowledge())
    outputs = expected_outputs(knowledge)
    count = f"{len(knowledge.entities)} entities and {len(knowledge.decisions)} decisions"

    if not check:
        ontology_dir().mkdir(parents=True, exist_ok=True)
        for path, expected in outputs.items():
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                path.write_text(expected, encoding="utf-8")
        for legacy in sorted(ontology_dir().glob("*.generated.md")):
            legacy.unlink()
        # Unreferenced baselines are reported (orphan-baseline warning), never
        # deleted: a freshly pinned claim may not be in its document yet.
        # Re-validate after removing retired reports so coverage reflects the final state.
        knowledge = validate(load_knowledge())
        for path, expected in expected_outputs(knowledge).items():
            if path.read_text(encoding="utf-8") != expected:
                path.write_text(expected, encoding="utf-8")
        report_findings(knowledge.findings)
        print(f"Knowledge index written for {count}.")
        return 1 if gating_errors(knowledge, scope) else 0

    problems = [diff for path, expected in outputs.items() if (diff := stale_diff(path, expected)) is not None]
    errors = gating_errors(knowledge, scope)
    report_findings(knowledge.findings)
    if problems:
        print("Knowledge index is stale. Regenerate it by running the engine without --check.")
        print("\n\n".join(problems))
        return 1
    if errors:
        print(f"Knowledge index has {len(errors)} gating error(s).")
        return 1
    print(f"Knowledge index validated for {count}.")
    return 0


def report_findings(findings: list[Finding]) -> None:
    for finding in sorted_findings(findings):
        print(f"{finding.level}: {finding.code}: {finding.path}: {finding.message}")


# ---------------------------------------------------------------------------
# Discovery ranking
# ---------------------------------------------------------------------------


def stem(token: str) -> str:
    for suffix in ("ations", "ation", "ings", "ing", "ies", "es", "ed", "s"):
        if len(token) > len(suffix) + 3 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def tokenize(text: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", text.lower()) if token]


def query_terms(query: str) -> list[str]:
    tokens = tokenize(query)
    terms: list[str] = []
    for token in tokens:
        if token in STOPWORDS or len(token) < 2:
            continue
        if token not in terms:
            terms.append(token)
    if not terms:
        terms = list(dict.fromkeys(tokens))
    return terms


def term_matches(term: str, text: str) -> bool:
    target = stem(term)
    return any(stem(token) == target for token in tokenize(text))


@dataclass
class Candidate:
    path: str
    kind: str
    identifier: str
    owner: str
    fields: dict[str, list[str]]


def search_candidates(index: dict[str, Any]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for entity in index["entities"]:
        candidates.append(
            Candidate(
                path=entity["path"],
                kind="entity",
                identifier=entity["id"],
                owner=entity["id"],
                fields={
                    "id_title": [entity["id"], entity["name"]],
                    "alias": entity["aliases"],
                    "heading": [],
                    "metadata": [entity["path"], entity["summary"], *entity["evidence"]],
                },
            )
        )
    for decision in index["decisions"]:
        candidates.append(
            Candidate(
                path=decision["path"],
                kind="decision",
                identifier=decision["id"],
                owner="governance",
                fields={
                    "id_title": [decision["id"], decision["title"]],
                    "alias": decision["aliases"],
                    "heading": decision["headings"],
                    "metadata": [decision["path"], *decision["applies_to"], *decision["source_of_truth"], *decision["constrains"]],
                },
            )
        )
    for document in index["documents"]:
        stem_id = Path(document["path"]).stem
        candidates.append(
            Candidate(
                path=document["path"],
                kind="document",
                identifier=stem_id,
                owner=document["owner"],
                fields={
                    "id_title": [stem_id, document["title"]],
                    "alias": document["aliases"],
                    "heading": document["headings"],
                    "metadata": [document["path"], *document["applies_to"], *document["source_of_truth"]],
                },
            )
        )
    return candidates


def rank(
    index: dict[str, Any],
    query: str,
    body_loader: Callable[[str], str] | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Deterministically rank knowledge for a query.

    Each evidence class contributes its fixed weight at most once per query
    term. Every occurrence is still reported in `matched_on` for
    explainability, but volume never multiplies relevance.
    """
    terms = query_terms(query)
    results = []
    for candidate in search_candidates(index):
        fields = dict(candidate.fields)
        if body_loader is not None and candidate.kind != "entity":
            try:
                fields["body"] = [body_loader(candidate.path)]
            except OSError:
                fields["body"] = []
        score = 0
        matched_on = []
        for term in terms:
            for evidence_class in RANK_ORDER:
                values = fields.get(evidence_class) or []
                hits = [value for value in values if term_matches(term, value)]
                if not hits:
                    continue
                weight = RANK_WEIGHTS[evidence_class]
                score += weight
                matched_on.append(
                    {
                        "term": term,
                        "class": evidence_class,
                        "weight": weight,
                        "occurrences": len(hits) if evidence_class != "body" else body_occurrences(term, hits[0]),
                        "examples": [] if evidence_class == "body" else sorted(set(hits))[:5],
                    }
                )
        if score:
            results.append(
                {
                    "path": candidate.path,
                    "kind": candidate.kind,
                    "id": candidate.identifier,
                    "owner": candidate.owner,
                    "score": score,
                    "matched_on": matched_on,
                }
            )
    results.sort(key=lambda item: (-item["score"], item["path"]))
    return {
        "query": query,
        "terms": terms,
        "weights": RANK_WEIGHTS,
        "body_searched": body_loader is not None,
        "results": results[:limit] if limit > 0 else results,
    }


def body_occurrences(term: str, body: str) -> int:
    target = stem(term)
    return sum(1 for token in tokenize(body) if stem(token) == target)


def run_search(query: str, limit: int) -> int:
    knowledge = validate(load_knowledge())
    print(json.dumps(rank(build_index(knowledge), query, None, limit), indent=2))
    return 0


# ---------------------------------------------------------------------------
# Pinned-claim drift
# ---------------------------------------------------------------------------


def parse_region(region: Any) -> dict[str, Any]:
    if not isinstance(region, dict):
        raise ValueError("region must be a mapping with `lines` or `start_marker`/`end_marker`.")
    if "lines" in region:
        match = re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", str(region["lines"]))
        if not match or int(match.group(1)) < 1 or int(match.group(1)) > int(match.group(2)):
            raise ValueError("region.lines must look like '10-40' (1-based, inclusive).")
        return {"lines": (int(match.group(1)), int(match.group(2)))}
    if "start_marker" in region:
        return {"start_marker": str(region["start_marker"]), "end_marker": str(region.get("end_marker", ""))}
    raise ValueError("region must declare `lines` or `start_marker`.")


def canonical_content(path: Path, profile: str, region: Any) -> str:
    raw = path.read_text(encoding="utf-8")
    lines = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if raw.endswith("\n") or raw.endswith("\r"):
        lines = lines[:-1]
    if region is not None:
        spec = parse_region(region)
        if "lines" in spec:
            start, end = spec["lines"]
            lines = lines[start - 1 : end]
        else:
            start_index = next((i for i, line in enumerate(lines) if spec["start_marker"] in line), None)
            if start_index is None:
                raise ValueError(f"start_marker not found: {spec['start_marker']!r}")
            end_index = len(lines) - 1
            if spec["end_marker"]:
                end_index = next(
                    (i for i in range(start_index + 1, len(lines)) if spec["end_marker"] in lines[i]),
                    None,
                )
                if end_index is None:
                    raise ValueError(f"end_marker not found: {spec['end_marker']!r}")
            lines = lines[start_index : end_index + 1]
    if profile == "text":
        lines = [line.rstrip() for line in lines]
        while lines and not lines[-1]:
            lines.pop()
    return "\n".join(lines) + "\n"


def digest_of(content: str) -> str:
    return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()


def baseline_rel_path(digest: str) -> str:
    return f".knowledge/ontology/baselines/{digest.split(':', 1)[1]}.txt"


def git_changed_paths(base: str, head: str) -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git diff {base}...{head} failed")
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def evaluate_claim(document: Document, index: int, entry: dict[str, Any]) -> dict[str, Any]:
    target = str(entry.get("path", ""))
    profile = str(entry.get("profile", "text"))
    verification = entry.get("verification") if isinstance(entry.get("verification"), dict) else {}
    record: dict[str, Any] = {
        "document": rel(document.path),
        "claim": index,
        "path": target,
        "profile": profile,
        "region": entry.get("region"),
        "expected_digest": entry.get("digest"),
        "verification_state": verification.get("state"),
    }
    source = ROOT / normalize_ref(target)
    if not source.is_file():
        record["state"] = "missing-source"
        return record
    try:
        current = canonical_content(source, profile, entry.get("region"))
    except (ValueError, UnicodeDecodeError) as exc:
        record["state"] = "unresolvable-region"
        record["detail"] = str(exc)
        return record
    record["actual_digest"] = digest_of(current)
    if record["actual_digest"] == entry.get("digest"):
        record["state"] = "current"
        return record
    record["state"] = "drifted"
    baseline_path = ROOT / str(entry.get("baseline", ""))
    if entry.get("baseline") and baseline_path.is_file():
        baseline = baseline_path.read_text(encoding="utf-8")
        record["diff"] = "\n".join(
            difflib.unified_diff(
                baseline.splitlines(),
                current.splitlines(),
                fromfile=f"baseline:{target}",
                tofile=f"current:{target}",
                lineterm="",
            )
        )
    else:
        record["state"] = "missing-baseline"
    return record


def run_detect_drift(base: str | None, head: str | None, full_inventory: bool) -> int:
    if full_inventory == bool(base):
        print("--detect-drift requires exactly one scope: --base <ref> [--head <ref>] or --full-inventory.", file=sys.stderr)
        return 2
    knowledge = load_knowledge()
    enforcement = knowledge.config["knowledge_drift"]["enforcement"]
    changed: set[str] | None = None
    if base:
        try:
            changed = git_changed_paths(base, head or "HEAD")
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 2
    claims = []
    unpinned = []
    for document in knowledge.all_documents():
        sources = document.frontmatter.get("source_of_truth")
        if not isinstance(sources, list):
            continue
        for index, entry in enumerate(sources, start=1):
            target = normalize_ref(claim_path(entry))
            if changed is not None and target not in changed:
                continue
            if isinstance(entry, dict):
                claims.append(evaluate_claim(document, index, entry))
            elif enforcement == "pinned-claims":
                unpinned.append({"document": rel(document.path), "claim": index, "path": target})
    failing = [claim for claim in claims if claim["state"] != "current"]
    report = {
        "mode": "full-inventory" if full_inventory else "git-scope",
        "scope": None if full_inventory else {"base": base, "head": head or "HEAD", "changed_paths": sorted(changed or [])},
        "enforcement": enforcement,
        "human_verification_asserted": False,
        "claims": claims,
        "unpinned": unpinned,
        "summary": {
            "evaluated": len(claims),
            "drifted": sum(1 for claim in claims if claim["state"] == "drifted"),
            "failing": len(failing),
            "unpinned": len(unpinned),
        },
    }
    print(json.dumps(report, indent=2))
    return 1 if enforcement == "pinned-claims" and failing else 0


def run_pin_claim(target: str, profile: str, lines: str | None, start_marker: str | None, end_marker: str | None) -> int:
    source = ROOT / normalize_ref(target)
    if not source.is_file():
        print(f"Cannot pin a claim to a missing file: {target}", file=sys.stderr)
        return 2
    if is_ephemeral(target):
        print(f"Claims must not cite temporary work: {target}", file=sys.stderr)
        return 2
    region: dict[str, Any] | None = None
    if lines:
        region = {"lines": lines}
    elif start_marker:
        region = {"start_marker": start_marker}
        if end_marker:
            region["end_marker"] = end_marker
    try:
        content = canonical_content(source, profile, region)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    digest = digest_of(content)
    baseline = baseline_rel_path(digest)
    baseline_path = ROOT / baseline
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    if not baseline_path.exists():
        baseline_path.write_text(content, encoding="utf-8")
    claim: dict[str, Any] = {"path": normalize_ref(target), "profile": profile}
    if region:
        claim["region"] = region
    # The engine never asserts human verification; /devspark.explain records
    # `verified` only after the human confirms the retained-baseline diff.
    claim.update({"digest": digest, "baseline": baseline, "verification": {"state": "unverified"}})
    print(json.dumps(claim, indent=2))
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="fail when committed output is stale; never writes")
    mode.add_argument("--search", metavar="QUERY", help="rank knowledge for a concept query (JSON)")
    mode.add_argument("--detect-drift", action="store_true", help="report pinned-claim content drift (JSON)")
    mode.add_argument("--pin-claim", metavar="PATH", help="retain a canonical baseline and print the claim (JSON)")
    parser.add_argument("--root", help="consumer repository root (defaults to automatic discovery)")
    parser.add_argument("--entity", action="append", default=[], help="limit the error gate to these entity ids")
    parser.add_argument("--limit", type=int, default=20, help="maximum search results (0 = all)")
    parser.add_argument("--base", help="drift scope: base Git ref")
    parser.add_argument("--head", help="drift scope: head Git ref (default HEAD)")
    parser.add_argument("--full-inventory", action="store_true", help="drift scope: every pinned claim, no Git history")
    parser.add_argument("--profile", choices=CLAIM_PROFILES, default="text", help="claim canonicalization profile")
    parser.add_argument("--lines", help="claim region as 'start-end' (1-based, inclusive)")
    parser.add_argument("--start-marker", help="claim region start marker text")
    parser.add_argument("--end-marker", help="claim region end marker text")
    args = parser.parse_args(argv)
    ROOT = discover_root(args.root)

    if args.search is not None:
        return run_search(args.search, args.limit)
    if args.detect_drift:
        return run_detect_drift(args.base, args.head, args.full_inventory)
    if args.pin_claim:
        return run_pin_claim(args.pin_claim, args.profile, args.lines, args.start_marker, args.end_marker)
    return run_build(check=args.check, scope=set(args.entity) or None)


if __name__ == "__main__":
    sys.exit(main())
