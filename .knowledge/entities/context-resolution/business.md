---
id: context-resolution-business
type: entity-layer
title: "Context Resolution - Bounding Rules"
layer: business
source_of_truth:
  - tests/test_explain_context_contract.py
  - tests/test_context_projection_contract.py
last_verified: 2026-10-11
aliases:
  - hop budget
  - context bounding
  - just right context
  - ranking determinism
---

<!-- markdownlint-disable MD025 -->

# Context Resolution - Bounding Rules

The rules that decide how far context expands and when expansion stops.

## Smallest sufficient context

The target is **the smallest trustworthy set of current Knowledge needed to perform the task
safely** - not maximum recall, and not everything known about the subject.

- Start from directly matched Knowledge.
- Follow a relationship only when the adjacent concept can materially affect the work.
- Stop when the context is sufficient, not when the graph is exhausted.

Adjacency is not relevance. A reachable node is a candidate; retaining it is a decision.

## Hop budget

One budget, stated once:

- Planning projects to a maximum of **two hops** from its lexical seeds.
- Implementation consumes the resolved context and may take **at most one additional hop**, which
  is logged explicitly.
- Any other surface projecting for diagnostic purposes uses at most two hops.

A range is not a budget. A surface needing different reach declares the difference and the reason
rather than quietly widening.

## Bounded candidates

Projection caps total candidates and **reports when the cap was reached**. Hitting it is a signal
about graph shape - usually a hub with excessive fan-out - and not a normal outcome to absorb
silently. Truncation is deterministic, so a truncated result is reproducible rather than arbitrary.

## Determinism

The same query over the same corpus returns the same items in the same order. This is what makes a
retrieval regression measurable: a fixture recorded today means the same thing when re-measured
later, instead of drifting with incidental ordering.

## Kinds of resolved context

A resolved working set may contain an entity, a single entity layer, a **flat Knowledge document**,
or a governance decision. Flat Knowledge is first-class: a working set consisting entirely of flat
documents is valid and complete, and nothing may model resolved context as entities and decisions
only.

Each retained item keeps enough provenance to audit it - what it is, how it was reached, how many
hops away it was, and why it was kept.

## What never enters context by default

The whole corpus, the whole generated index, every neighbour of every seed, unaccepted findings,
archived material, and results from any private search path. Duplicate arrivals of the same
document are collapsed - a second copy consumes budget and teaches nothing.
