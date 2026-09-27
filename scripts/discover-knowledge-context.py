"""Gather deterministic discovery signals for /devspark.discover-knowledge.

Read-only. Reports mechanical facts about how well `.knowledge` covers and
connects current code and tests. It never classifies a finding, assigns
confidence, or writes anything: the prompt judges, the human approves.

Scope (exactly one):
  <target>   an entity id, a repository path, or a concept term
  --all      the whole repository (explicit because it is more expensive)

Signals:
  source_clusters       code areas with their knowledge coverage and tests
  mapping_breadth       size and concept density of each source mapping
  ownership_overlaps    nodes whose mappings claim the same code
  relationship_signals  unrelated entity pairs with code/test/doc interaction
  alias_signals         recurring code vocabulary missing from a node's names
  stale_references      backticked paths/symbols in knowledge that no longer exist
  historical_signals    knowledge lines that read as history, not current truth
  node_shape            entity-versus-flat signals for flat nodes and clusters
"""

from __future__ import annotations

import argparse
import fnmatch
import importlib.util
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

CODE_SUFFIXES = {
    ".py", ".pyi", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".cs", ".java", ".kt", ".go",
    ".rs", ".rb", ".php", ".swift", ".scala", ".sh", ".ps1", ".psm1", ".sql", ".c", ".cc",
    ".cpp", ".h", ".hpp", ".dart", ".vue", ".svelte",
}
EXCLUDED_PREFIXES = (
    ".git/", ".devspark/", ".devspark.work/", ".archive/", ".knowledge/", "node_modules/",
    "dist/", "build/", "bin/", "obj/", "vendor/", ".venv/", "venv/", ".pytest_cache/",
)
TEST_RE = re.compile(r"(^|/)(tests?|specs?|__tests__)(/|$)|(^|/)(test_[^/]*|[^/]*(_test|\.test|_spec|\.spec)\.[^/]+)$", re.I)
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{3,}")
ACRONYM_RE_VOCAB = re.compile(r"(?<![$\w{])[A-Z]{2,5}(?![\w=}\[])")
# A bare identifier counts as a reference only when it is not the tail of a
# dotted path (`pkg.module` must not match a needle `module` from another package).
REF_WORD_RE = re.compile(r"(?<![\w.])[A-Za-z_]\w*")
ANY_WORD_RE = re.compile(r"[A-Za-z_]\w*")
REF_COMPOUND_RE = re.compile(r"[A-Za-z_]\w*(?:[./][A-Za-z_]\w*)+")
BACKTICK_RE = re.compile(r"`([^`\n]{2,120})`")
STOP = {
    "self", "this", "that", "with", "from", "import", "return", "true", "false", "none", "null",
    "void", "class", "def", "function", "const", "string", "value", "values", "data", "list", "dict",
    "type", "types", "test", "tests", "assert", "expected", "result", "results", "args", "kwargs",
    "param", "params", "path", "file", "files", "name", "names", "item", "items", "public", "private",
    "static", "async", "await", "else", "elif", "then", "when", "case", "break", "continue", "while",
    "for", "raise", "except", "try", "finally", "lambda", "yield", "print", "echo", "local", "export",
    "object", "number", "boolean", "undefined", "new", "var", "let", "int", "str", "bool", "float",
    "json", "http", "https", "todo", "init", "main", "index", "utils", "util", "helper", "helpers",
    "config", "error", "errors", "get", "set", "add", "update", "create", "delete",
    "esac", "done", "then", "write", "host", "output", "input", "string", "stringify",
}
COMMON_ACRONYMS = {"TODO", "FIXME", "NOTE", "HTTP", "JSON", "YAML", "HTML", "UTF", "API", "URL", "SQL", "CLI", "OK", "ID", "EOF", "PATH", "HOME", "IFS", "ARGS", "ENV"}
HISTORY_PATTERNS = (
    ("previously", re.compile(r"\bpreviously\b", re.I)),
    ("used-to", re.compile(r"\bused to\b", re.I)),
    ("no-longer", re.compile(r"\bno longer\b", re.I)),
    ("formerly", re.compile(r"\bformerly\b", re.I)),
    ("replaced", re.compile(r"\b(was|were|has been|have been) (replaced|superseded|retired|removed)\b", re.I)),
    ("migration-narrative", re.compile(r"\bmigrat(ed|ion) (from|away)\b", re.I)),
    ("legacy", re.compile(r"\blegacy\b|\bdeprecated\b", re.I)),
    ("dated-change", re.compile(r"\b(in|since|until|before|after) (19|20)\d{2}\b", re.I)),
    ("requirement-id", re.compile(r"\b(FR|NFR|US|SC)-\d{2,4}\b|\bT\d{3,4}\b")),
    ("history-heading", re.compile(r"^#+\s*(history|background|changelog|timeline|evolution)\b", re.I)),
)


sys.dont_write_bytecode = True  # read-only: importing the engine must not leave __pycache__ behind


def load_engine() -> Any:
    engine_path = Path(__file__).resolve().with_name("build_knowledge_index.py")
    spec = importlib.util.spec_from_file_location("build_knowledge_index", engine_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Knowledge engine not found beside {Path(__file__).name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def words(identifier: str) -> list[str]:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", identifier)
    spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", spaced)
    return [part.lower() for part in re.split(r"[_\W]+", spaced) if part]


def tokens(text: str) -> set[str]:
    return {part for part in re.split(r"[^a-z0-9]+", text.lower()) if len(part) >= 3}


class Repo:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.files = self._tracked()
        self.code = [path for path in self.files if self._is_code(path)]
        self.tests = [path for path in self.code if TEST_RE.search(path)]
        self.test_set = frozenset(self.tests)
        self.production = [path for path in self.code if path not in self.test_set]
        self._text: dict[str, str] = {}
        self._refs: dict[str, frozenset[str]] = {}
        self._words: dict[str, frozenset[str]] = {}
        self._terms: dict[str, set[str]] = {}
        self.common: set[str] = set()

    def _tracked(self) -> list[str]:
        result = subprocess.run(["git", "ls-files"], cwd=self.root, text=True, capture_output=True, check=False)
        if result.returncode == 0:
            return sorted({line.strip() for line in result.stdout.splitlines() if line.strip()})
        return sorted(
            path.relative_to(self.root).as_posix() for path in self.root.rglob("*") if path.is_file()
        )

    @staticmethod
    def _is_code(path: str) -> bool:
        return not path.startswith(EXCLUDED_PREFIXES) and Path(path).suffix.lower() in CODE_SUFFIXES

    def text(self, path: str) -> str:
        if path not in self._text:
            try:
                self._text[path] = (self.root / path).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                self._text[path] = ""
        return self._text[path]

    def refs(self, path: str) -> frozenset[str]:
        """Identifiers and dotted/slashed module references in a file, computed once.

        Relationship and test signals intersect these sets with module needles
        instead of running one regex per needle per file, which kept large
        repositories from scanning in minutes.
        """
        if path not in self._refs:
            text = self.text(path)
            found = set(REF_WORD_RE.findall(text))
            for compound in REF_COMPOUND_RE.findall(text):
                parts = re.split(r"[./]", compound)
                for end in range(2, len(parts) + 1):
                    found.add(".".join(parts[:end]))
                    found.add("/".join(parts[:end]))
            self._refs[path] = frozenset(found)
        return self._refs[path]

    def words_anywhere(self, path: str) -> frozenset[str]:
        if path not in self._words:
            self._words[path] = frozenset(ANY_WORD_RE.findall(self.text(path)))
        return self._words[path]

    def terms(self, path: str) -> set[str]:
        if path not in self._terms:
            self._terms[path] = file_terms(self, path)
        return self._terms[path]

    def recent_commits(self, days: int = 180) -> Counter[str]:
        result = subprocess.run(
            ["git", "log", f"--since={days}.days", "--name-only", "--format="],
            cwd=self.root, text=True, capture_output=True, check=False,
        )
        return Counter(line.strip() for line in result.stdout.splitlines() if line.strip())


def covers(pattern: str, path: str) -> bool:
    pattern = pattern.strip().rstrip("/")
    if pattern.startswith("./"):
        pattern = pattern[2:]
    if not pattern or pattern == ".":
        return True
    if any(char in pattern for char in "*?["):
        return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, pattern.rstrip("*").rstrip("/") + "/*")
    return path == pattern or path.startswith(pattern + "/")


class Node:
    def __init__(self, identifier: str, kind: str, title: str, paths: list[str], docs: list[str],
                 aliases: list[str], lexical: set[str], related: set[str]) -> None:
        self.id = identifier
        self.kind = kind
        self.title = title
        self.paths = paths
        self.docs = docs
        self.aliases = aliases
        self.lexical = lexical
        self.related = related
        self.files: set[str] = set()


def build_nodes(engine: Any, knowledge: Any, repo: Repo) -> dict[str, Node]:
    nodes: dict[str, Node] = {}
    for entity in knowledge.entities.values():
        data = entity.data
        paths: list[str] = []
        for part in str(data.get("root", "")).split(","):
            part = part.strip()
            if part and (repo.root / part.split("*")[0]).exists():
                paths.append(part)
        aliases = engine.string_list(data.get("aliases"))
        lexical = tokens(entity.entity_id) | tokens(str(data.get("name", ""))) | set().union(*(tokens(a) for a in aliases)) if aliases else tokens(entity.entity_id) | tokens(str(data.get("name", "")))
        related = {str(rel.get("object")) for rel in data.get("relations") or [] if isinstance(rel, dict)}
        related |= set(engine.string_list(engine.link_references(data) or []))
        related |= set(engine.string_list(data.get("constrained_by")))
        docs = []
        for document in entity.documents:
            front = document.frontmatter
            paths.extend(engine.claim_path(item) for item in front.get("source_of_truth") or [] if engine.claim_path(item))
            paths.extend(engine.string_list(front.get("appliesTo") or front.get("applies_to")))
            aliases += engine.string_list(front.get("aliases"))
            related |= set(engine.string_list(engine.link_references(front) or []))
            docs.append(engine.rel(document.path))
        nodes[entity.entity_id] = Node(entity.entity_id, "entity", str(data.get("name", entity.entity_id)),
                                       sorted(set(paths)), docs, sorted(set(aliases)), lexical, related)
    for document in knowledge.flat_docs:
        front = document.frontmatter
        identifier = engine.node_id(document)
        paths = [engine.claim_path(item) for item in front.get("source_of_truth") or [] if engine.claim_path(item)]
        paths += engine.string_list(front.get("appliesTo") or front.get("applies_to"))
        aliases = engine.string_list(front.get("aliases"))
        lexical = tokens(identifier) | tokens(document.title) | set().union(set(), *(tokens(a) for a in aliases))
        nodes[identifier] = Node(identifier, "flat", document.title, sorted(set(paths)), [engine.rel(document.path)],
                                 aliases, lexical, set(engine.string_list(engine.link_references(front) or [])))
    for decision in knowledge.decisions.values():
        constrains = set(engine.string_list(decision.data.get("constrains")))
        for entity_id in constrains:
            if entity_id in nodes:
                nodes[entity_id].related |= constrains - {entity_id}
    for node in nodes.values():
        node.files = {path for path in repo.code if any(covers(pattern, path) for pattern in node.paths)}
    return nodes


def cluster_key(path: str) -> str | None:
    parent = Path(path).parent.as_posix()
    if parent in ("", "."):
        return None
    return "/".join(parent.split("/")[:3])


def file_terms(repo: Repo, path: str) -> set[str]:
    terms = set()
    for identifier in IDENT_RE.findall(repo.text(path)):
        parts = [part for part in words(identifier) if len(part) >= 4 and part not in STOP]
        # Contiguous two-word phrases capture compound vocabulary such as
        # `validate_shipping_address` -> "shipping address".
        terms.update(" ".join(parts[index:index + 2]) for index in range(len(parts) - 1))
        terms.update(parts)
    return terms


def repo_vocabulary(repo: Repo) -> set[str]:
    """Terms in more than half of all production files: language noise, not domain concepts."""
    if len(repo.production) < 10:
        return set()
    frequency: Counter[str] = Counter()
    for path in repo.production:
        frequency.update(repo.terms(path))
    return {term for term, count in frequency.items() if count > len(repo.production) / 2}


def repeated_terms(repo: Repo, files: list[str], exclude: set[str], limit: int = 6) -> list[dict[str, Any]]:
    seen: Counter[str] = Counter()
    for path in files:
        seen.update(repo.terms(path) - exclude - repo.common)
    # Sort by count, then term: Counter ties follow set order, which varies per run.
    ranked = sorted(seen.items(), key=lambda item: (-item[1], item[0]))
    return [{"term": term, "files": count} for term, count in ranked if count >= 2][:limit]


def tests_touching(repo: Repo, files: list[str]) -> list[str]:
    needles = {Path(path).stem for path in files if len(Path(path).stem) >= 4 and Path(path).stem not in {"__init__", "index", "main"}}
    return [test for test in repo.tests if not needles.isdisjoint(repo.words_anywhere(test))]


def source_clusters(repo: Repo, nodes: dict[str, Node], churn: Counter[str], in_scope: Any) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for path in repo.production:
        key = cluster_key(path)
        if key and in_scope(path):
            grouped[key].append(path)
    clusters = []
    for key, files in sorted(grouped.items()):
        if len(files) < 2:
            continue
        mapped_by = sorted(node.id for node in nodes.values() if node.files & set(files))
        mapped_files = {path for path in files if any(path in node.files for node in nodes.values())}
        tests = tests_touching(repo, files)
        clusters.append(
            {
                "area": f"{key}/**",
                "production_files": len(files),
                "tests": len(tests),
                "sample_tests": tests[:5],
                "mapped_by": mapped_by,
                "mapped_fraction": round(len(mapped_files) / len(files), 2),
                "recent_commits": sum(churn.get(path, 0) for path in files),
                "repeated_terms": repeated_terms(repo, files, set()),
            }
        )
    return sorted(clusters, key=lambda item: (item["mapped_fraction"], -item["production_files"], item["area"]))


def mapping_breadth(repo: Repo, nodes: dict[str, Node]) -> list[dict[str, Any]]:
    rows = []
    for node in nodes.values():
        for pattern in node.paths:
            covered = sorted(path for path in repo.code if covers(pattern, path))
            target = repo.root / pattern
            row: dict[str, Any] = {"node": node.id, "kind": node.kind, "mapping": pattern, "code_files": len(covered)}
            if target.is_file():
                row["lines"] = len(repo.text(pattern).splitlines()) if pattern in repo.files else None
            if covered and node.lexical:
                dense = [path for path in covered if tokens(Path(path).as_posix() + " " + repo.text(path)[:20000]) & node.lexical]
                row["concept_density"] = round(len(dense) / len(covered), 2)
                row["files_without_concept"] = sorted(set(covered) - set(dense))[:8]
            rows.append(row)
    return sorted(rows, key=lambda item: (-item["code_files"], item["node"], item["mapping"]))


def ownership_overlaps(nodes: dict[str, Node]) -> list[dict[str, Any]]:
    rows = []
    ordered = sorted(nodes.values(), key=lambda node: node.id)
    for index, left in enumerate(ordered):
        for right in ordered[index + 1:]:
            shared = left.files & right.files
            if not shared:
                continue
            rows.append(
                {
                    "nodes": [left.id, right.id],
                    "shared_files": len(shared),
                    "left_files": len(left.files),
                    "right_files": len(right.files),
                    "sample": sorted(shared)[:6],
                    "declared_related": right.id in left.related or left.id in right.related,
                }
            )
    return sorted(rows, key=lambda item: (-item["shared_files"], item["nodes"]))


def module_needles(files: set[str]) -> set[str]:
    needles = set()
    for path in files:
        stem = Path(path).stem
        if len(stem) >= 4 and stem not in {"__init__", "index", "main", "utils", "types"}:
            needles.add(stem)
        dotted = Path(path).with_suffix("").as_posix()
        needles.add(dotted.replace("/", "."))
        needles.add(dotted)
    return needles


def mentions(repo: Repo, path: str, needles: set[str]) -> bool:
    return not needles.isdisjoint(repo.refs(path))


def relationship_signals(repo: Repo, knowledge_text: dict[str, str], nodes: dict[str, Node]) -> list[dict[str, Any]]:
    entities = [node for node in nodes.values() if node.kind == "entity" and node.files]
    rows = []
    for index, left in enumerate(sorted(entities, key=lambda node: node.id)):
        for right in sorted(entities, key=lambda node: node.id)[index + 1:]:
            if right.id in left.related or left.id in right.related:
                continue
            left_only, right_only = left.files - right.files, right.files - left.files
            if not left_only or not right_only:
                continue
            left_needles, right_needles = module_needles(right_only), module_needles(left_only)
            left_to_right = sorted(path for path in left_only if path not in repo.test_set and mentions(repo, path, left_needles))
            right_to_left = sorted(path for path in right_only if path not in repo.test_set and mentions(repo, path, right_needles))
            together = sorted(
                test for test in repo.tests
                if mentions(repo, test, left_needles) and mentions(repo, test, right_needles)
            )
            docs = sorted(
                doc for doc in left.docs + right.docs
                if (doc in left.docs and re.search(rf"\b{re.escape(right.id)}\b|{re.escape(right.title)}", knowledge_text.get(doc, ""), re.I))
                or (doc in right.docs and re.search(rf"\b{re.escape(left.id)}\b|{re.escape(left.title)}", knowledge_text.get(doc, ""), re.I))
            )
            total = len(left_to_right) + len(right_to_left) + len(together) + len(docs)
            if not total:
                continue
            rows.append(
                {
                    "pair": [left.id, right.id],
                    "direction": "both" if left_to_right and right_to_left else (f"{left.id} -> {right.id}" if left_to_right else (f"{right.id} -> {left.id}" if right_to_left else "undirected")),
                    "code_dependencies": {f"{left.id} -> {right.id}": left_to_right[:6], f"{right.id} -> {left.id}": right_to_left[:6]},
                    "tests_together": together[:6],
                    "docs_mentioning_other": docs[:6],
                    "signal_count": total,
                    "context_path": {
                        "lexical_seed": left.id,
                        "candidate_relation": right.id,
                        "source_mappings": sorted(set(left.paths) | set(right.paths))[:6],
                    },
                }
            )
    return sorted(rows, key=lambda item: (-item["signal_count"], item["pair"]))


def alias_signals(repo: Repo, knowledge_text: dict[str, str], nodes: dict[str, Node]) -> list[dict[str, Any]]:
    rows = []
    for node in sorted(nodes.values(), key=lambda item: item.id):
        if not node.files:
            continue
        known = set(node.lexical) | {alias.lower() for alias in node.aliases} | {node.id.replace("-", " ").replace("_", " "), node.title.lower()}
        own = sorted(node.files)
        phrases = [item for item in repeated_terms(repo, own, known, limit=12) if " " in item["term"]]
        acronyms: Counter[str] = Counter()
        for path in own:
            # Skip variables such as $PATH or ARGS=... : they are syntax, not vocabulary.
            acronyms.update({found for found in ACRONYM_RE_VOCAB.findall(repo.text(path)) if found not in COMMON_ACRONYMS})
        doc_text = " ".join(knowledge_text.get(doc, "") for doc in node.docs).lower()
        candidates = [
            {"candidate": item["term"], "files": item["files"], "in_node_knowledge": item["term"] in doc_text}
            for item in phrases
        ]
        candidates += [
            {"candidate": acronym, "files": count, "in_node_knowledge": acronym.lower() in doc_text}
            for acronym, count in sorted(acronyms.items(), key=lambda item: (-item[1], item[0]))[:5]
            if count >= 2 and acronym.lower() not in known
        ]
        if candidates:
            rows.append({"node": node.id, "kind": node.kind, "candidates": candidates[:8]})
    return rows


def stale_references(repo: Repo, knowledge_text: dict[str, str]) -> list[dict[str, Any]]:
    corpus = "\n".join(repo.text(path) for path in repo.code)
    tracked = set(repo.files)
    rows = []
    for doc, text in sorted(knowledge_text.items()):
        in_fence = False
        for number, line in enumerate(text.splitlines(), start=1):
            if line.strip().startswith(("```", "~~~")):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for span in BACKTICK_RE.findall(line):
                value = span.strip()
                if any(char in value for char in "<>{}*$ ") or value.startswith(("http", "--", "/devspark", ".devspark.work", ".archive")):
                    continue
                if "/" in value or re.search(r"\.(py|ts|js|cs|go|rs|java|sh|ps1|json|ya?ml|md|toml)$", value):
                    path = value.split("::", 1)[0].split("#", 1)[0]
                    first = path.split("/", 1)[0]
                    if path.startswith(".devspark/") or ("/" in path and "." in first and not first.startswith(".")):
                        continue  # installed-framework paths and domain-style links are not repository files
                    if "." not in path and not path.endswith("/"):
                        continue  # prose like `n/a` or `and/or`, not a path
                    if "/" not in path and any(item == path or item.endswith("/" + path) for item in tracked):
                        continue  # a bare file name that exists somewhere in the repository
                    relative = (repo.root / doc).parent / path
                    if path and path.lstrip("./") not in tracked and not (repo.root / path).exists() and not relative.exists():
                        rows.append({"document": doc, "line": number, "reference": value, "signal": "missing-path"})
                elif re.fullmatch(r"[A-Za-z_][\w.]*\(\)|[A-Z]\w*\.[a-z_]\w*|[a-z]+(?:_[a-z0-9]+){2,}", value):
                    symbol = value.rstrip("()").split(".")[-1]
                    if symbol and not re.search(rf"\b{re.escape(symbol)}\b", corpus):
                        rows.append({"document": doc, "line": number, "reference": value, "signal": "unknown-symbol"})
    return rows


def historical_signals(knowledge_text: dict[str, str]) -> list[dict[str, Any]]:
    per_doc: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for doc, text in sorted(knowledge_text.items()):
        for number, line in enumerate(text.splitlines(), start=1):
            for name, pattern in HISTORY_PATTERNS:
                if pattern.search(line):
                    per_doc[doc].append({"line": number, "pattern": name, "text": line.strip()[:160]})
                    break
    return [{"document": doc, "hits": len(hits), "lines": hits[:10]} for doc, hits in sorted(per_doc.items(), key=lambda item: (-len(item[1]), item[0]))]


def shape_signals(node: Node, nodes: dict[str, Node]) -> list[str]:
    signals = []
    if len(node.files) >= 5:
        signals.append("specific-source-ownership")
    if any(other in nodes and nodes[other].kind == "entity" for other in node.related):
        signals.append("relationships-to-entities")
    if node.aliases:
        signals.append("named-domain-vocabulary")
    if len(node.docs) > 1:
        signals.append("multiple-layers")
    if node.files and len(node.files) >= 10:
        signals.append("coverage-or-drift-value")
    return signals


def node_shape(nodes: dict[str, Node], clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for node in sorted(nodes.values(), key=lambda item: item.id):
        if node.kind != "flat":
            continue
        signals = shape_signals(node, nodes)
        rows.append({"node": node.id, "kind": "flat", "signals": signals, "signal_count": len(signals)})
    for cluster in clusters:
        if cluster["mapped_by"]:
            continue
        signals = []
        if cluster["production_files"] >= 5:
            signals.append("specific-source-ownership")
        if cluster["tests"] >= 2:
            signals.append("tested-behavior")
        if any(" " in term["term"] for term in cluster["repeated_terms"]):
            signals.append("named-domain-vocabulary")
        if cluster["production_files"] >= 10:
            signals.append("coverage-or-drift-value")
        rows.append({"area": cluster["area"], "kind": "unmapped-cluster", "signals": signals, "signal_count": len(signals)})
    return rows


def resolve_scope(target: str | None, repo: Repo, nodes: dict[str, Node], engine: Any, index: dict[str, Any]) -> tuple[dict[str, Any], Any, set[str]]:
    if target is None:
        return {"mode": "repository"}, (lambda path: True), set(nodes)
    if target in nodes:
        focus = {target} | (nodes[target].related & set(nodes))
        prefixes = [pattern for node_id in focus for pattern in nodes[node_id].paths]
        return {"mode": "node", "node": target, "neighbors": sorted(focus - {target})}, (lambda path: any(covers(p, path) for p in prefixes)), focus
    normalized = target.strip().rstrip("/")
    if (repo.root / normalized).exists():
        focus = {node.id for node in nodes.values() if any(covers(normalized, path) for path in node.files) or any(covers(pattern, normalized) for pattern in node.paths)}
        return {"mode": "path", "path": normalized}, (lambda path: covers(normalized, path)), focus
    ranked = engine.rank(index, target, None, 10)["results"]
    focus = {item["owner"] if item["owner"] in nodes else item["id"] for item in ranked}
    focus &= set(nodes)
    term_tokens = tokens(target)
    return (
        {"mode": "term", "term": target, "matched_nodes": sorted(focus)},
        (lambda path: bool(tokens(path) & term_tokens) or any(path in nodes[node_id].files for node_id in focus)),
        focus,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", nargs="*", help="entity id, repository path, or concept term")
    parser.add_argument("--all", action="store_true", help="discover across the whole repository")
    parser.add_argument("--root", help="repository root (defaults to automatic discovery)")
    args = parser.parse_args(argv)
    target = " ".join(args.target).strip() or None
    if bool(target) == args.all:
        print("Choose exactly one scope: <entity-id | path | term> or --all.", file=sys.stderr)
        return 2

    engine = load_engine()
    root = engine.discover_root(args.root)
    knowledge = engine.validate(engine.load_knowledge(root))
    index = engine.build_index(knowledge)
    repo = Repo(root)
    repo.common = repo_vocabulary(repo)
    nodes = build_nodes(engine, knowledge, repo)
    knowledge_text = {engine.rel(doc.path): engine.document_body(doc.path) for doc in knowledge.all_documents()}

    scope, in_scope, focus = resolve_scope(target, repo, nodes, engine, index)
    focused = {node_id: node for node_id, node in nodes.items() if node_id in focus} or ({} if target else nodes)
    focus_docs = {doc for node in focused.values() for doc in node.docs}
    scoped_text = {doc: text for doc, text in knowledge_text.items() if not target or doc in focus_docs}

    clusters = source_clusters(repo, nodes, repo.recent_commits(), in_scope)
    report = {
        "scope": scope,
        "read_only": True,
        "counts": {
            "code_files": len(repo.code),
            "production_files": len(repo.production),
            "test_files": len(repo.tests),
            "entities": len(knowledge.entities),
            "flat_nodes": len(knowledge.flat_docs),
            "decisions": len(knowledge.decisions),
        },
        "engine_findings": [finding.as_dict() for finding in engine.sorted_findings(knowledge.findings) if finding.level == "error"][:20],
        "source_clusters": clusters,
        "mapping_breadth": mapping_breadth(repo, focused),
        "ownership_overlaps": [row for row in ownership_overlaps(nodes) if not target or set(row["nodes"]) & set(focused)],
        "relationship_signals": [row for row in relationship_signals(repo, knowledge_text, nodes) if not target or set(row["pair"]) & set(focused)],
        "alias_signals": alias_signals(repo, knowledge_text, focused),
        "stale_references": stale_references(repo, scoped_text),
        "historical_signals": historical_signals(scoped_text),
        "node_shape": node_shape(focused if target else nodes, clusters),
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
