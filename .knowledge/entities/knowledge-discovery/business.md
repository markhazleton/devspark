---
id: knowledge-discovery-business
type: entity-layer
title: "Knowledge Maintenance Discovery - Findings"
layer: business
source_of_truth:
  - scripts/knowledge_findings.py
  - tests/test_knowledge_findings_schema_contract.py
last_verified: 2026-10-17
aliases:
  - finding categories
  - finding severity
  - overlapping ownership
  - broad mapping
---

<!-- markdownlint-disable MD025 -->

# Knowledge Maintenance Discovery - Findings

What a finding is, what kinds exist, and how far each one can be trusted.

## The shared finding record

Every producer of advisory findings emits the same record, so consumers do not need per-producer
handling:

| Field | Purpose |
| --- | --- |
| `id` | Content-derived stable identity for the condition |
| `category` | The kind of problem |
| `subject` | What the finding is about |
| `severity` | How much it matters |
| `confidence` | How sure the heuristic is |
| `evidence` | Why the tool believes it |
| `recommendation` | The proposed human action |
| `changes_authoritative_truth` | Whether acting on it alters the corpus |

The last field is the safety boundary. A finding that would change the corpus is a proposal
awaiting acceptance, never an instruction.

## Categories and what they actually detect

- **Knowledge gap** - repository evidence exists that no document claims. Says nothing about
  whether that evidence is worth documenting.
- **Entity candidate** - a cluster of evidence substantial enough to justify a structured entity
  rather than a flat document.
- **Overlapping ownership** - more than one document claims the same repository path. Signals a
  question to ask, not necessarily a conflict.
- **Broad mapping** - one ownership pattern covers so many files that it has stopped identifying
  anything specific.
- **Weak mapping** - a document claims evidence that is thin, missing, or no longer supports it.
- **Contradiction** - two documents assert incompatible truths about the same subject.
- **Historical leakage** - a document is narrating what changed rather than what is true.

## Documented narrowness

Every heuristic here has a shape it cannot see, and those limits are part of the subsystem's
truth rather than embarrassments to omit:

- **Clustering is structural.** Evidence is grouped by repository layout before it is judged. A
  concept whose implementation and tests live apart - the normal arrangement in many stacks - can
  therefore be evaluated as several unrelated small clusters and never recognized as one entity.
- **Ownership overlap is computed per path, across all claim kinds at once.** Different kinds of
  claim over one file are counted the same way, so legitimate multi-perspective coverage of a
  single module is reported as shared ownership.
- **Breadth is judged by file count against a fixed threshold.** A genuinely broad component
  crosses it honestly; a narrow one in a large directory may too.

A reviewer needs these limits stated, because the expensive failure is not a wrong finding - it is
an absent finding mistaken for a clean corpus.

## Reading a clean report

An empty report means no configured heuristic matched. It is not evidence that the corpus is
complete, current, or correct.
