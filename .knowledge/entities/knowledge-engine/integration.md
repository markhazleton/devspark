---
id: knowledge-engine-integration
type: entity-layer
title: "Knowledge Engine - Source Evidence Boundary"
layer: integration
source_of_truth:
  - templates/knowledge-drift/self-test/claims.yaml
  - tests/test_knowledge_drift_cli_contract.py
  - tests/test_knowledge_drift_migration_contract.py
last_verified: 2026-09-30
aliases:
  - source baselines
  - drift detection
  - content addressed evidence
---

<!-- markdownlint-disable MD025 -->

# Knowledge Engine - Source Evidence Boundary

Validating a document's frontmatter only proves the document is well formed. Proving it still
describes the system requires reaching outside `.knowledge/` - into the repository's own files and
its version history. That reach is this subsystem's only external boundary.

## What it touches

| Boundary | Use | Failure posture |
| --- | --- | --- |
| Repository working tree | Confirm every claimed path exists; read bytes for canonical comparison | A missing claimed path fails the build |
| Version control history | Obtain the newest commit date for a claimed path, once per distinct path within a build | Unavailable history is skipped, not fatal |
| Baseline evidence store | Retain the canonical bytes a pinned claim was accepted against | A missing baseline is reported as an unverifiable claim |

The engine never reaches the network, never authenticates, and never writes outside `.knowledge/`
and the derived artifacts.

## Claimed paths are constrained by meaning, not just existence

A claimed path must exist, but existence alone is insufficient. Paths into the temporary working
roots and into the archive are rejected outright, because both may contain a file that happens to
be present on disk while representing planning state or written-off history rather than durable
truth. Durable Knowledge may not rest on evidence that is scheduled to disappear.

## The baseline store

A pinned claim records a digest of its canonical comparison bytes, and the retained baseline is
addressed by that digest. Two properties follow and must hold:

1. **The baseline path is derivable from the digest.** Nothing needs an index to find the evidence
   for a claim.
2. **Baselines are immutable once written.** Accepting new content means recording a new claim, not
   editing the evidence the previous claim was accepted against.

Baselines no longer referenced by any claim are removable, and removal is a deliberate operation
rather than a side effect of a routine build.

## Version history is advisory here

Commit dates answer "might this have changed?", never "did the behavior change?". A repository
checked out without history yields no dates at all, so currency reporting degrades to silence
rather than to false confidence. Any workflow that depends on commit-date currency needs full
history present, and treats its absence as missing information rather than as a clean result.
Within one build a path is queried once and the answer is discarded with the build; nothing about
history is cached across builds.
