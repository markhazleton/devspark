"""Rank `.knowledge` documents for a /devspark.explain topic.

Uses the single knowledge engine (build_knowledge_index.py, resolved beside
this file) for the index-time evidence classes (id/title, alias, heading,
metadata) and adds body prose at query time. Body text is read per query and
never committed to index.json. Read-only: writes nothing.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


def load_engine():
    engine_path = Path(__file__).resolve().with_name("build_knowledge_index.py")
    spec = importlib.util.spec_from_file_location("build_knowledge_index", engine_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Knowledge engine not found beside {Path(__file__).name}: {engine_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("topic", nargs="+", help="free-text topic or question")
    parser.add_argument("--root", help="repository root (defaults to automatic discovery)")
    parser.add_argument("--limit", type=int, default=20, help="maximum results (0 = all)")
    args = parser.parse_args(argv)

    engine = load_engine()
    root = engine.discover_root(args.root)
    knowledge = engine.validate(engine.load_knowledge(root))
    index = engine.build_index(knowledge)

    def body_loader(relative: str) -> str:
        return engine.document_body(root / relative)

    report = engine.rank(index, " ".join(args.topic), body_loader, args.limit)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
