---
id: context-resolution-operations
type: entity-layer
title: "Context Resolution - Measurement and Diagnostics"
layer: operations
source_of_truth:
  - scripts/knowledge-benchmark.py
  - tests/test_knowledge_benchmark_contract.py
last_verified: 2026-10-11
aliases:
  - retrieval benchmark
  - recall measurement
  - fan-out audit
---

<!-- markdownlint-disable MD025 -->

# Context Resolution - Measurement and Diagnostics

Retrieval quality is not self-evident, so it is measured against fixtures rather than judged by
inspection.

## Measure the consumer's view

The harness runs the **real retrieval engine unmodified**. It never widens the candidate limit,
removes node categories, or collapses entities without saying so. A harness that quietly improves
the thing it measures reports on a system nobody runs.

The distinction that keeps a number honest:

| View | What it is | Legitimate use |
| --- | --- | --- |
| Consumer candidates | The first N ranked results, exactly what a caller receives | Reporting retrieval quality |
| Full ranking | The complete scored list, unbounded | Diagnosing whether the right answer ranked too low |

Recall is computed from the consumer's view only. It is never backfilled from deeper positions in
the full ranking, and a full-ranking number is never presented as if it were what a caller would
have received.

Collapsing an entity's layer documents into one entry can only **reduce** a visible result set. It
never promotes a candidate that was outside the consumer boundary, so it cannot manufacture a
better score.

## Auditing graph shape

Projection can report fan-out per node. Two shapes matter, and both are problems:

- **Explosive expansion** - a hub reached from most seeds, pulling unrelated context into every
  working set and consuming the candidate cap.
- **Absent expansion** - an entity that should be connected returning no neighbours, meaning a
  relationship was never authored and adjacent truth is unreachable.

An isolated entity is not automatically a defect. Some concepts genuinely stand alone, and for
those, returning nothing is the correct result.

## Interpreting a clean run

A clean measurement means the recorded fixtures still resolve as before. It is not evidence that
the corpus is complete, that authored relationships are correct, or that an agent would find the
context useful. Those are review questions, and no harness answers them.
