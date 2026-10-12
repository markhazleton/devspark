---
id: advisory-findings-are-not-authoritative
type: governance-decision
title: "Advisory findings are not authoritative Knowledge"
constrains:
  - knowledge-engine
  - context-resolution
  - knowledge-discovery
---

<!-- markdownlint-disable MD025 -->

# Advisory findings are not authoritative Knowledge

Automated analysis of this repository produces **proposals**. A proposal becomes Knowledge only
when a human accepts it and writes it into `.knowledge/`. Nothing else promotes it.

## What this constrains

- **The Knowledge Engine** builds nodes and edges from authored documents only. A finding never
  becomes a node, and an inferred relationship never becomes an edge. A relation that cannot be
  resolved to an authored entity fails the build rather than being created on demand.
- **Context Resolution** traverses accepted relationships only. A proposed relationship cannot
  influence which Knowledge an agent receives until it exists in the corpus.
- **Maintenance discovery** analyses read-only. Persisting a report or applying an accepted finding
  each require a separate, explicit instruction, and neither happens as a side effect of analysis.

Every finding declares whether acting on it would change authoritative truth. Anything that would -
creating a document, asserting a relationship, altering ownership - waits for acceptance regardless
of the heuristic's confidence.

## Why

The corpus is worth consulting only because it represents accepted human judgment about the system.
An agent acting on it is trusting that someone decided each statement was true.

Automated inference is useful and frequently right, but it is right for reasons a reader cannot
inspect. If inference could write into the corpus, three things follow:

1. **Trust becomes unverifiable.** A reader can no longer tell whether a statement was asserted or
   guessed, so every statement has to be re-derived - which is the cost the corpus exists to avoid.
2. **Errors compound silently.** Inferred Knowledge becomes input to the next inference pass. A
   single wrong cluster or mis-attributed ownership propagates without anyone deciding it should.
3. **Review has nothing to review.** A corpus that maintains itself presents no moment at which a
   human disagrees, so disagreement never happens.

Keeping the boundary makes the failure mode loud instead of quiet: a missing document is visible
and fixable, while a confidently wrong one that nobody authored is neither.

## Alternatives considered

**Auto-apply high-confidence findings.** Rejected. Confidence measures how well a heuristic matched
its own pattern, not how well the pattern matched reality. The documented narrowness of these
heuristics - structural clustering, per-path ownership counting, fixed breadth thresholds - means a
high-confidence finding can be confidently wrong, and it is precisely the findings nobody looks at
that would be applied.

**Write findings into the corpus as provisional nodes for later review.** Rejected. It requires a
lifecycle marker on the node to distinguish provisional from accepted, which is prohibited in this
corpus for independent reasons, and in practice provisional content is read as current by anything
that retrieves it.

**Let projection traverse proposed relationships to preview their value.** Rejected. It removes the
property that makes a working set auditable - that every item arrived by a recorded lexical match
or an authored relationship - and the preview would be indistinguishable from the real thing at the
point of use.

## What is permitted

Findings may be reported, persisted as a report outside the corpus, ranked, filtered, and used to
decide what a human authors next. The constraint is on promotion, not on analysis.
