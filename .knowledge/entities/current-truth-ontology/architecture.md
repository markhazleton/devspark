---
evidence:
  - type: doc
    ref: templates/knowledge/ontology/schema.md
    verified_by: inspection
    test_attempted: true
    fallback_reason: "Current-truth behavior is enforced by prompt and documentation contracts."
---

# Current-Truth Ontology

The ontology model organizes entities, decisions, evidence, and derived graph
metadata from `.knowledge`. Prompts use it to avoid stale references and to keep
durable knowledge separate from temporary work state.

The hand-authored contract is `.knowledge/ontology/schema.md`. Entity metadata
lives in `_entity.yaml`; generated metadata lives beside it in `_derived.yaml`.
Decision frontmatter declares `governs`, and the generator inverts those edges
into each entity's `constrained_by` list.

`scripts/python/build_knowledge_index.py` is the deterministic generator for the
current-truth graph. It validates entity kinds, relation types, decision
coverage, evidence references, required layer files, and stale generated output.
It writes coverage, relation, governance, evidence, and gap reports under
`.knowledge/ontology/`.
