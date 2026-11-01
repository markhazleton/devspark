---
id: knowledge-engine-business
type: entity-layer
title: "Knowledge Engine - Semantics"
layer: business
source_of_truth:
  - templates/schemas/knowledge-node.schema.json
  - tests/test_build_knowledge_index_contract.py
  - tests/test_taxonomy_registry_contract.py
last_verified: 2026-10-17
aliases:
  - knowledge document rules
  - allowed knowledge types
  - artifact form
  - semantic role
  - entity layers
  - current truth rules
---

<!-- markdownlint-disable MD025 -->

# Knowledge Engine - Semantics

The durable rules that decide whether a document is valid current Knowledge, and what it means.

## Current truth, not history

Knowledge records what is true now. The engine rejects frontmatter that expresses a lifecycle or a
chain of versions - a status, a supersession pointer, or an obsolescence marker - because a
document carrying one is describing its own history rather than the system's present behavior.
Document types that name a historical artifact are rejected for the same reason.

When something changes, the owning document is edited in place. The previous wording is recoverable
from version control and has no standing in the corpus.

## Closed vocabularies: form and role

A document's classification has two axes, and each is a closed set. An unrecognized value fails the
build rather than being accepted as an unknown category, so the corpus cannot silently accumulate
private classifications.

**Form** is what the artifact is, and is derived from where it lives:

| Form | Recognized by |
| --- | --- |
| `entity-layer` | living under `.knowledge/entities/<id>/` |
| `governance-decision` | living under `.knowledge/governance/decisions/`, excluding directory indexes |
| `flat-document` | everything else |

An author may not choose a form. Declaring one that contradicts the artifact's location fails the
build, because form is a fact about the file rather than an opinion about it.

**Role** is the kind of truth the document carries. A flat document draws it from the taxonomy
vocabulary or from an explicit declaration; an entity layer's role is its `layer`; a decision's is
always `governance`. Only a flat document's role is assignable by the taxonomy registry.

Two forms carry extra obligations:

- `entity-layer` requires a `layer` and at least one `source_of_truth` mapping; `last_verified` is
  optional and, when present, must be an ISO date. A layer document with no owned evidence cannot
  exist.
- `governance-decision` requires a non-empty `constrains` list naming real entities.

The historical `type` field remains in the serialized model for consumers written before the split.
It holds the role for a flat document and the form otherwise. On a flat document an authored `type`
means role and carries no structural weight.

## Layers

An entity's Knowledge is divided into six layers so an agent can receive the view its task needs.
Four - `architecture`, `business`, `integration`, `operations` - are **expected**, and the coverage
report names them when absent. Two - `pattern` and `plan` - are **auxiliary** and never reported as
a gap.

Every layer is optional to author. Coverage describes the corpus; it does not command it. A layer
is created only when repository evidence supports useful content for it, and an expected layer that
genuinely does not apply is waived on the entity with a justification rather than filled with a
document that says nothing.

## Relationship strength

| Mechanism | Strictness | Meaning |
| --- | --- | --- |
| Entity `relations` | Strict - unresolved target fails the build | Asserted architectural truth |
| Governance `constrains` / `constrained_by` | Strict and reciprocal | Governance applies to a concept |
| `links.references` | Lenient - unresolved target is reported | Informational pointer |

Semantic relationships belong to the entity, never to one of its layers. A layer describes a facet
of its parent and has no independent identity to relate from, so `links` on a layer document is
rejected rather than ignored - an accepted-but-unused field looks authored while reaching nothing.
The entity-to-layer edge is composition the engine materializes, not a relationship anyone authors.

Reciprocity for governance is enforced in both directions: a decision naming an entity requires
that entity to point back, and an entity may not claim a constraint the decision does not assert.
A governance link only one side knows about is the failure this pair exists to prevent.

## Decisions are keyed by topic

A decision document is named for its subject, never for its position in a sequence. Numbered and
counter-style filenames are rejected, because a corpus keyed by creation order accumulates
competing documents for one topic instead of a single current answer.

## Source currency

`source_of_truth` answers which repository artifacts provide the evidence for a document. Two
mechanisms establish that the evidence still holds:

- A **path mapping** is current relative to the newest commit touching the artifacts it claims.
  Evidence newer than the document's optional `last_verified` date is reported as an advisory
  staleness finding rather than failing the build, because an unrelated edit to a cited file is not proof the described
  behavior changed.
- A **pinned content claim** names a comparison profile and a digest, and is current relative to a
  retained content-addressed baseline. A profile decides which differences matter - token-level
  comparison ignores comments and layout, exact comparison ignores nothing.

Both are `source_of_truth`. Anything reporting on currency states which mechanism it evaluated,
because the word "stale" otherwise names unrelated conditions.
