---
id: context-resolution-architecture
type: entity-layer
title: "Context Resolution - Architecture"
layer: architecture
source_of_truth:
  - scripts/explain-context.py
  - scripts/context-projection.py
last_verified: 2026-10-17
aliases:
  - context resolution
  - retrieval and projection
  - how plan finds knowledge
---

<!-- markdownlint-disable MD025 -->

# Context Resolution - Architecture

Context Resolution answers a single question: **which Knowledge should an agent be given for this
task, and nothing more?**

## Two roles, not a chain

Retrieval and projection are **siblings**, not stages of one another. Both consume the model the
Knowledge Engine builds; neither does the other's job.

```text
task description
      |
      v
  retrieval  ->  likely seeds
                      |
                      v
                 projection  ->  adjacent candidates
                                        |
                                        v
                                task-specific judgment
                                        |
                                        v
                                 resolved context
```

- **Retrieval** asks *what Knowledge is likely relevant?* It matches lexically over the corpus and
  ranks deterministically.
- **Projection** asks *what accepted architectural truth is adjacent to those seeds?* It walks
  authored relationships outward from ids it is given.

Judgment - deciding what to keep - belongs to the calling workflow, not to this subsystem.
Projection reports what is reachable; it does not claim any of it is relevant.

## One operation, one build

Planning needs both roles for the same delta, so retrieval can hand its matched ids to projection
in a single invocation (`explain-context --project`). That run builds the corpus model once and
projects over the same in-memory result; ranking, hop budget and provenance are exactly what the
standalone commands return, and standalone projection still builds on its own.

Reuse is bounded to that one invocation and proven by content, never by timestamps. Digests of the
Knowledge documents, entity definitions, registry, committed derived artifacts, cited sources and
the Git history identity are taken before the build and compared after it and again just before
output. A changed, added, deleted, equal-timestamp-edited or unverifiable input discards the
combined output and the command reports `RETRY_REQUIRED` rather than mixing two states. Nothing is
written: there is no receipt, no persistent cache and no change to the generated index.

## File owner lookup

Given files, `explain-context --files` reports which nodes apply to each (`appliesTo`) or cite it
as evidence (`source_of_truth`, including object-form claims), with the matched pattern and the
entity a layer belongs to, plus the files no node claims. Applicability is not exclusive
ownership, so every match is returned with its relationship. The Plan records the files it expects
to change, not the Knowledge to update; owners are derived on demand.

## What this subsystem must not do

- **Retrieval does not traverse.** A high-scoring match is a starting point, never assembled
  architectural context.
- **Projection does not search.** It performs no lexical or semantic matching of its own. Given no
  seeds, it returns nothing, and that is correct behavior rather than a failure.
- **Neither invents an interpretation of the corpus.** Both obtain the graph from the engine.

Keeping these separate is what makes the result auditable: every item in a working set arrived
either by a recorded lexical match or by a recorded relationship path, and the two are
distinguishable afterward.

## Provenance

Every candidate projection returns carries the path and relation by which it was reached.
Relationships are traversed in both directions, and the reverse direction is labelled distinctly -
an inverse edge is a **traversal affordance, not an authored claim**, and nothing may report one as
something a human asserted.

## Reading a node's kind

Both surfaces classify nodes - projection labels a candidate, and explanation decides whether to
report what a decision constrains. That question is **structural**, so both read the node's `form`.
The compatibility `type` answers it correctly for a decision only as a side effect of how the
single-field encoding was preserved; on a flat document the same field means the document's role
instead. Reading `form` keeps the two meanings from being confused as the corpus grows.

## Boundary with maintenance discovery

Advisory findings are not part of the graph. Projection traverses accepted relationships only, so a
proposed relationship cannot influence what an agent receives until a human has accepted it into
the corpus.
