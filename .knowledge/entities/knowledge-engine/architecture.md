---
id: knowledge-engine-architecture
type: entity-layer
title: "Knowledge Engine - Architecture"
layer: architecture
source_of_truth:
  - scripts/build_knowledge_index.py
  - templates/schemas/entity-node.schema.json
  - tests/test_knowledge_engine_resolution_contract.py
last_verified: 2026-10-17
aliases:
  - knowledge index
  - index builder
  - canonical knowledge model
---

<!-- markdownlint-disable MD025 -->

# Knowledge Engine - Architecture

The Knowledge Engine is the **single interpreter of the `.knowledge/` corpus**. It reads the
authoritative source documents, validates them, materializes the relationship graph, and
serializes deterministic derived artifacts.

## Responsibility

The engine owns the transformation from authored files to a usable model:

```text
.knowledge/ source files  ->  parse + validate  ->  nodes + edges  ->  derived artifacts
```

It does not decide what is relevant to a task, does not propose new Knowledge, and does not
retrieve on behalf of an agent. Those belong to adjacent subsystems.

## Boundaries

- **Authoritative input** is the set of Markdown documents and entity descriptors under
  `.knowledge/`. Nothing else is authoritative.
- **The in-memory model is the canonical interpretation** of that input. Typing, validation, edge
  materialization, coverage, and ownership resolution happen there and nowhere else.
- **Serialized artifacts are derived.** They exist for inspection and interoperability, are
  regenerated rather than edited, and are byte-stable across operating systems. A stale copy never
  blocks work.

## Invariants

1. **Exactly one implementation interprets the corpus.** A consumer obtains the model by invoking
   the engine, never by parsing document frontmatter itself and never by inventing its own notion
   of a node, a type, or an edge. Rebuilding the model in memory is a conforming way to consume
   it; reimplementing the interpretation is not.
2. **Flat documents and entities are both first-class.** A flat document is a complete node.
   Entity layer documents are additional nodes bound to an entity identity. Neither form is a
   transitional state toward the other.
3. **An unresolved entity relation fails the build.** The graph every consumer traverses may not
   contain a dead edge. A forward-looking `links.references` target is reported instead, because a
   document may legitimately point at Knowledge not yet authored.
4. **Ordering is platform-independent.** Node and edge order derives from slash-normalized path
   strings rather than native path comparison, so an artifact generated on one operating system
   matches one generated on another.

## Classification: two axes

Every node carries a **form** and a **role**, and they answer different questions.

- **Form** is what the artifact *is*: `flat-document`, `entity-layer`, or `governance-decision`.
  It is derived from location and filename, never authored. Frontmatter may restate it but may
  not select it, and a declared form that contradicts structure fails the build.
- **Role** is what the artifact *says*: the kind of truth it carries. Only a flat document's role
  is assignable by the taxonomy registry; an entity layer's role is its `layer` and a decision's
  is always `governance`.

A single field could not carry both. An entity layer's form is `entity-layer` while its role is
the layer it documents, so collapsing them left every valid layer permanently unclassifiable
against a path-based taxonomy.

Structure decides form because structure is evidence, but a directory index is navigation rather
than a member of its directory — which is why a `README.md` beside the decisions is a flat
document. Recognizing that by filename keeps form derived; the alternative, letting frontmatter
exempt itself, would let any file misreport what it structurally is.

The historical single `type` field survives unchanged for consumers that predate the split: the
role for a flat document, the form otherwise. It is compatibility output, not the model.

An entity carries its own classification, a controlled `type` describing what kind of concept it
is. That is a third axis and independent of the other two: it is advisory, it never requires a
layer to exist, and it shares the name `integration` with a layer role without implying it. An
entity may *be* a boundary, or merely *have* a boundary-facing facet.

## Related concepts

Retrieval and projection consume this model without extending it; maintenance discovery reads the
same validated signals to propose changes to the corpus. Both depend on this subsystem, and
neither may substitute its own interpretation of the corpus.
