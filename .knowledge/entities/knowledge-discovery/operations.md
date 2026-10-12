---
id: knowledge-discovery-operations
type: entity-layer
title: "Knowledge Maintenance Discovery - Operations"
layer: operations
source_of_truth:
  - scripts/powershell/discover-knowledge.ps1
  - scripts/bash/discover-knowledge.sh
  - tests/test_knowledge_discovery_contract.py
last_verified: 2026-09-30
aliases:
  - run discovery
  - discovery scope
---

<!-- markdownlint-disable MD025 -->

# Knowledge Maintenance Discovery - Operations

## Scoping

Discovery is run against a scope - the whole repository, a path, or a single entity - and findings
outside that scope are withheld. Scoping is what makes the output reviewable: a repository-wide run
on a corpus with real gaps produces more findings than anyone will act on, and an unreviewed report
is the same as no report.

Narrow the scope to the area under active work. Reserve full runs for deliberate corpus review.

## Read-only by default

Analysis writes nothing. Persisting a report or applying an accepted finding each require an
explicit instruction, and neither happens as a side effect of inspecting the corpus.

This matters most when discovery runs unattended. A scheduled analysis that silently authored
Knowledge would mean the corpus no longer represents accepted human judgment, which is the one
property that makes it worth trusting.

## Dual-language parity

The subsystem is invoked through a matched pair of shell entry points, one per supported
environment. They accept the same arguments, apply the same scoping, and emit the same structured
output. **The pair changes together, always** - an option added to one and not the other means the
same documented instruction produces different results depending on who runs it.

## Result posture

Analysis completing successfully is reported as success whether or not findings were produced.
Findings are information, not an error condition, and treating their presence as a failure would
push people toward narrowing scope until the report is empty.

A non-zero result means the run could not be performed - an unreadable corpus, an invalid scope -
and not that the corpus has problems.
