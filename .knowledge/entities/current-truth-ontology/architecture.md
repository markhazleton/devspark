---
aliases:
- knowledge engine
- knowledge index
- ontology generator
source_of_truth:
- scripts/build_knowledge_index.py
- scripts/explain-context.py
- scripts/migrate-knowledge-to-entities.py
- templates/schemas/entity-node.schema.json
- templates/schemas/knowledge-node.schema.json
- templates/knowledge/ontology/schema.md
last_verified: '2026-09-26'
evidence:
- type: test
  ref: tests/test_knowledge_engine_contract.py
  verified_by: execution
---

# Current-Truth Ontology

The ontology organizes entities, governance decisions, evidence, and discovery
metadata from `.knowledge`. Prompts use it to avoid stale references and to keep
durable knowledge separate from temporary work state.

The contract is `.knowledge/ontology/schema.md`, backed by
`templates/schemas/entity-node.schema.json` (`_entity.yaml`) and
`templates/schemas/knowledge-node.schema.json` (Markdown frontmatter for layer
documents and `type: governance-decision` decisions). Decisions declare
`constrains`; each constrained entity hand-authors the reciprocal
`constrained_by` in its `_entity.yaml`. Lifecycle keys (`status`, `lifecycle`,
`supersedes`, `superseded-by`, `replaced`, `obsolete`) are banned.

`scripts/build_knowledge_index.py` is the single knowledge engine. It validates
entity kinds, relation types, the constrains/constrained_by pair, one file per
decision topic, evidence, the `source_of_truth`/`last_verified` currency pair,
and required layers. Without flags it writes `.knowledge/ontology/index.json`
and `.knowledge/ontology/coverage.json`; `--check` fails on stale output or
gating errors and never writes. `--search` ranks knowledge by concept with fixed
per-class weights applied once per query term, `--detect-drift` compares pinned
claims against retained baselines under `.knowledge/ontology/baselines/`, and
`--pin-claim` retains a new baseline.

`scripts/explain-context.py` adds query-time body search on top of the engine's
ranking for `/devspark.explain`. `scripts/migrate-knowledge-to-entities.py`
migrates older `.knowledge` layouts to this contract. Helper scripts locate the
engine through `resolve_knowledge_engine` / `Resolve-KnowledgeEngine`, which
prefer `.devspark/scripts/` and fall back to repository-root `scripts/`.
