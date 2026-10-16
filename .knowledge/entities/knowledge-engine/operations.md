---
id: knowledge-engine-operations
type: entity-layer
title: "Knowledge Engine - Operations"
layer: operations
source_of_truth:
  - scripts/knowledge-integrity.py
  - tests/test_knowledge_index_determinism_contract.py
  - tests/test_knowledge_integrity_contract.py
  - tests/test_knowledge_drift_performance.py
last_verified: 2026-10-15
aliases:
  - index drift check
  - regenerate knowledge index
  - knowledge integrity
  - integrity finding
---

<!-- markdownlint-disable MD025 -->

# Knowledge Engine - Operations

How the engine is run, what it guarantees between runs, and how its failures present.

## The drift gate

Derived artifacts are committed, so they can fall behind the sources they describe. The engine
therefore runs in two modes against the same corpus: one regenerates the artifacts, the other
compares freshly built output against what is committed and reports a difference without writing.

The comparison deliberately ignores the generation timestamp and nothing else. A run that differs
only by when it happened is not drift; anything else is.

**Any change to `.knowledge/` is followed by a regeneration in the same change.** Editing a
document and leaving the artifacts behind produces a failing gate for the next unrelated change,
which is how a small omission becomes someone else's blocked work.

## Determinism is a hard requirement

The same corpus produces byte-identical artifacts on every supported operating system. This is not
a convenience: the gate compares one machine's output against another's, so any platform-dependent
ordering turns into a permanent false failure that no content change can resolve.

The known trap is native path comparison. Path objects order differently depending on platform
flavor, so ordering is taken from slash-normalized strings instead.

## Build failures versus reported findings

The engine distinguishes conditions that make the model wrong from conditions that make it
questionable:

| Condition | Result |
| --- | --- |
| Invalid frontmatter, prohibited key, unknown role | Build fails |
| Declared form contradicting the artifact's location | Build fails |
| Missing claimed source path | Build fails |
| Entity relation to an unknown entity | Build fails |
| Governance reciprocity broken | Build fails |
| Claimed evidence newer than `last_verified` | Reported as a staleness finding |
| Expected layer absent | Reported in the coverage report |

A failing build stops work; a finding informs it. Staleness is not promoted to a failure by
default, because a cited file is frequently touched for reasons unrelated to the behavior a
document describes. A workflow that needs the stricter posture opts into it explicitly.

## What a finding means

**A finding is a condition that deserves attention now.** That standard decides what is worth
reporting: a report that accumulates permanent entries nobody can act on trains its readers to
ignore it, so a condition already settled as current truth does not belong on every run.

The distinction shows up in how an explicit role is judged against the taxonomy. A registry glob
states a directory's default, and a document inside that directory declaring a different role is
the precedence rule working as intended - not a defect, and not reported. An exact-path mapping is
a statement about one specific file, and a document contradicting it means two deliberate
statements disagree, which someone has to settle.

## Independent integrity checking

Integrity verification runs the engine and cross-checks its output against a second resolvable copy
of the engine when one is present, so a repository carrying both a framework-installed and a
source-local copy learns that they disagree rather than silently trusting whichever was imported
first. Its output is a findings report, and a clean report means the corpus is internally
consistent - not that it is complete or accurate.

## Cost

Currency checking is the expensive part, because it reads and canonicalizes claimed files rather
than only their metadata. Corpus-wide verification is a deliberate operation; routine builds stay
cheap enough to run on every change.
