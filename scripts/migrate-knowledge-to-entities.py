"""Migrate `.knowledge/` to the current entity-node / knowledge-node contracts.

One deterministic operation, safe to re-run:

- decisions: `governs` -> `constrains`; add `type: governance-decision` and
  `title`; drop banned lifecycle keys (`status`, `supersedes`, ...).
- entities: fold generated `_derived.yaml` `constrained_by` into the
  hand-authored `_entity.yaml`, then delete `_derived.yaml`; drop banned keys.
- constrains / constrained_by: add any missing reciprocal pointer.
- entity documents (every Markdown file under an entity, including
  subfolders): add `source_of_truth` (from their own or the entity's evidence
  refs) and `last_verified` (last Git commit date, else today).
- ontology: delete retired `*.generated.md` reports.

Run the knowledge engine afterwards to write index.json and coverage.json.
Use --dry-run to list the changes without writing.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

BANNED_KEYS = ("status", "lifecycle", "supersedes", "superseded-by", "superseded_by", "replaced", "obsolete")
DECISION_TYPE = "governance-decision"
EPHEMERAL_PREFIXES = (".devspark.work/", ".archive/")


def posix_key(path: Path) -> str:
    """Sort paths identically on every OS (Windows Path ordering ignores case)."""
    return path.as_posix()


def discover_root(explicit_root: str | None) -> Path:
    if explicit_root:
        return Path(explicit_root).expanduser().resolve()
    configured = os.environ.get("DEVSPARK_REPO_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    script_path = Path(__file__).resolve()
    for candidate in script_path.parents[1:4]:
        if (candidate / ".knowledge").is_dir():
            return candidate
    return Path.cwd().resolve()


def split_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    data = yaml.safe_load(parts[1]) or {}
    return (data if isinstance(data, dict) else None), parts[2]


def dump_frontmatter(data: dict[str, Any], body: str) -> str:
    rendered = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100)
    if not body.startswith("\n"):
        body = "\n" + body
    return f"---\n{rendered}---{body}"


def first_heading(body: str) -> str:
    for line in body.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line.strip())
        if match:
            return match.group(1)
    return ""


def git_last_date(root: Path, path: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(path.relative_to(root))],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return date.today().isoformat()
    value = result.stdout.strip()
    return value or date.today().isoformat()


def evidence_refs(data: dict[str, Any]) -> list[str]:
    refs = []
    for entry in data.get("evidence") or []:
        if isinstance(entry, dict) and entry.get("ref"):
            ref = str(entry["ref"]).split("#", 1)[0].split("::", 1)[0]
            if ref and not ref.startswith(EPHEMERAL_PREFIXES) and ref not in refs:
                refs.append(ref)
    return refs


class Migration:
    def __init__(self, root: Path, dry_run: bool) -> None:
        self.root = root
        self.dry_run = dry_run
        self.changes: list[str] = []

    def rel(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def write(self, path: Path, content: str, reason: str) -> None:
        if path.read_text(encoding="utf-8") == content:
            return
        self.changes.append(f"update {self.rel(path)}: {reason}")
        if not self.dry_run:
            path.write_text(content, encoding="utf-8")

    def delete(self, path: Path, reason: str) -> None:
        self.changes.append(f"delete {self.rel(path)}: {reason}")
        if not self.dry_run:
            path.unlink()

    def run(self) -> int:
        knowledge = self.root / ".knowledge"
        if not knowledge.is_dir():
            print(f"No .knowledge/ directory under {self.root}.", file=sys.stderr)
            return 2
        entities = self.migrate_entities(knowledge / "entities")
        decisions = self.migrate_decisions(knowledge / "governance" / "decisions")
        self.reconcile(entities, decisions)
        self.migrate_layers(knowledge / "entities", entities)
        ontology = knowledge / "ontology"
        if ontology.is_dir():
            for legacy in sorted(ontology.glob("*.generated.md"), key=posix_key):
                self.delete(legacy, "retired Markdown ontology report")
        for change in self.changes:
            print(change)
        verb = "would change" if self.dry_run else "changed"
        print(f"Knowledge migration {verb} {len(self.changes)} file(s).")
        return 0

    # entities -------------------------------------------------------------

    def migrate_entities(self, root: Path) -> dict[str, tuple[Path, dict[str, Any]]]:
        entities: dict[str, tuple[Path, dict[str, Any]]] = {}
        if not root.is_dir():
            return entities
        for folder in sorted((path for path in root.iterdir() if path.is_dir()), key=posix_key):
            entity_path = folder / "_entity.yaml"
            if not entity_path.exists():
                continue
            data = yaml.safe_load(entity_path.read_text(encoding="utf-8")) or {}
            if not isinstance(data, dict):
                continue
            derived_path = folder / "_derived.yaml"
            constrained_by = [str(item) for item in data.get("constrained_by") or []]
            if derived_path.exists():
                derived = yaml.safe_load(derived_path.read_text(encoding="utf-8")) or {}
                for item in derived.get("constrained_by") or []:
                    if str(item) not in constrained_by:
                        constrained_by.append(str(item))
            for key in BANNED_KEYS:
                data.pop(key, None)
            if constrained_by:
                data["constrained_by"] = constrained_by
            entities[str(data.get("id", folder.name))] = (entity_path, data)
            if derived_path.exists():
                self.delete(derived_path, "constrained_by now hand-authored in _entity.yaml")
        return entities

    # decisions ------------------------------------------------------------

    def migrate_decisions(self, root: Path) -> dict[str, tuple[Path, dict[str, Any], str]]:
        decisions: dict[str, tuple[Path, dict[str, Any], str]] = {}
        if not root.is_dir():
            return decisions
        for path in sorted(root.glob("*.md"), key=posix_key):
            data, body = split_frontmatter(path.read_text(encoding="utf-8"))
            if not data:
                continue
            migrated: dict[str, Any] = {
                "id": str(data.get("id", path.stem)),
                "type": DECISION_TYPE,
                "title": str(data.get("title") or first_heading(body) or path.stem.replace("-", " ")),
            }
            constrains = [str(item) for item in (data.get("constrains") or data.get("governs") or [])]
            migrated["constrains"] = constrains
            for key, value in data.items():
                if key in migrated or key in BANNED_KEYS or key in ("governs", "constrains", "layer"):
                    continue
                migrated[key] = value
            if not migrated.get("last_verified"):
                migrated["last_verified"] = git_last_date(self.root, path)
            decisions[migrated["id"]] = (path, migrated, body)
        return decisions

    # reciprocity ----------------------------------------------------------

    def reconcile(
        self,
        entities: dict[str, tuple[Path, dict[str, Any]]],
        decisions: dict[str, tuple[Path, dict[str, Any], str]],
    ) -> None:
        for decision_id, (_, data, _) in decisions.items():
            for entity_id in data["constrains"]:
                if entity_id in entities:
                    constrained_by = entities[entity_id][1].setdefault("constrained_by", [])
                    if decision_id not in constrained_by:
                        constrained_by.append(decision_id)
        for entity_id, (_, data) in entities.items():
            for decision_id in data.get("constrained_by") or []:
                if decision_id in decisions:
                    constrains = decisions[decision_id][1]["constrains"]
                    if entity_id not in constrains:
                        constrains.append(entity_id)
        for entity_path, data in entities.values():
            if data.get("constrained_by"):
                data["constrained_by"] = sorted(dict.fromkeys(data["constrained_by"]))
            self.write(
                entity_path,
                yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100),
                "entity-node contract",
            )
        for path, data, body in decisions.values():
            data["constrains"] = sorted(dict.fromkeys(data["constrains"]))
            self.write(path, dump_frontmatter(data, body), "knowledge-node governance-decision contract")

    # layer documents ------------------------------------------------------

    def migrate_layers(self, root: Path, entities: dict[str, tuple[Path, dict[str, Any]]]) -> None:
        for entity_id, (entity_path, entity_data) in entities.items():
            folder = entity_path.parent
            for path in sorted(folder.rglob("*.md"), key=posix_key):
                if path.name.startswith("_"):
                    continue
                text = path.read_text(encoding="utf-8")
                data, body = split_frontmatter(text)
                if data is None:
                    data, body = {}, text
                changed = dict(data)
                for key in BANNED_KEYS:
                    changed.pop(key, None)
                if not changed.get("source_of_truth"):
                    sources = evidence_refs(changed) or evidence_refs(entity_data) or [self.rel(entity_path)]
                    changed["source_of_truth"] = sources
                if not changed.get("last_verified"):
                    changed["last_verified"] = git_last_date(self.root, path)
                if changed != data:
                    ordered = {key: changed[key] for key in ("title", "aliases", "source_of_truth", "last_verified") if key in changed}
                    ordered.update({key: value for key, value in changed.items() if key not in ordered})
                    self.write(path, dump_frontmatter(ordered, body), "knowledge-node currency pair")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", help="repository root (defaults to automatic discovery)")
    parser.add_argument("--dry-run", action="store_true", help="list changes without writing")
    args = parser.parse_args(argv)
    return Migration(discover_root(args.root), args.dry_run).run()


if __name__ == "__main__":
    sys.exit(main())
