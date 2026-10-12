---
id: knowledge-discovery-architecture
type: entity-layer
title: "Knowledge Maintenance Discovery - Architecture"
layer: architecture
source_of_truth:
  - scripts/discover-knowledge.py
  - tests/test_discover_knowledge_contract.py
last_verified: 2026-10-11
aliases:
  - discover knowledge
  - knowledge gaps
  - maintenance discovery
---

<!-- markdownlint-disable MD025 -->

# Knowledge Maintenance Discovery - Architecture

Discovery finds **candidate problems in an existing corpus** and hands them to a human. It is a
maintenance instrument, not a supply mechanism.

## Two different jobs

| Job | Question | Frequency |
| --- | --- | --- |
| Baseline supply | What Knowledge should exist for this repository at all? | Once, at onboarding |
| Maintenance discovery | Where has the existing corpus decayed or gone thin? | Periodically, forever |

This subsystem is the second. It reasons over a corpus that already exists, comparing authored
Knowledge against repository evidence. Pointing it at an empty corpus produces gap findings for
everything and no useful ordering, which is a misuse rather than a defect.

The best time to author Knowledge is when the code makes the truth evident. Discovery exists for
the truths that were missed.

## What it inspects

Discovery compares three things it does not own: the **validated model** from the Knowledge Engine,
the **ownership claims** documents make over repository paths, and the **repository evidence**
those claims point at. Disagreement between them becomes a finding.

## Ownership is not applicability

A document may reference a path in two unrelated ways, and conflating them manufactures conflicts.
`source_of_truth` is **ownership**: the artifact materially implements, proves, or constrains this
Knowledge, so changing it may make the Knowledge wrong. `appliesTo` is **applicability**: the
Knowledge governs that path without owning it.

Only ownership participates in overlap analysis. A governance decision applying to a file an entity
owns is the normal relationship between governance and the thing it governs, not a dispute. Two
entities claiming the same file as their own source is still reported - a genuinely cross-cutting
file may implement more than one concept, so it is surfaced for review rather than prohibited.

Because the two claim kinds mean different things, a finding states which kind it saw.

## Output shape

A finding is a structured proposal: a category, a subject, a severity, a confidence, the evidence
behind it, and a recommendation. Findings are addressed by a **stable identity derived from their
content**, so the same condition observed twice is recognizably the same condition and a resolved
one does not reappear under a new name.

Confidence describes how sure the heuristic is. Severity describes how much the condition matters.
They are independent, and a report that merges them is hiding the difference between *probably
true and minor* and *possibly true and serious*.

## What it may not do

Discovery proposes; it never adopts. Its analysis pass is read-only. Applying an accepted finding
requires an explicit, separate instruction to write, and nothing invokes that implicitly.

A finding declares whether acting on it would change authoritative truth. Anything that would -
creating Knowledge, asserting a relationship, altering ownership - requires human acceptance
regardless of how confident the heuristic is.
