---
evidence:
  - type: doc
    ref: templates/knowledge/ontology/schema.md
    verified_by: inspection
    test_attempted: true
    fallback_reason: "Current-truth behavior is enforced by prompt and documentation contracts."
---

# Current-Truth Ontology

The ontology model organizes entities, decisions, and evidence from `.knowledge`.
Prompts use it to avoid stale references and to keep durable knowledge separate
from temporary work state.
