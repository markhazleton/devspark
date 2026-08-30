---
id: okf-knowledge-layer-and-genuine-fix-discipline
status: current
last_verified: "2026-08-30"
governs:
- application-registry
- command-templates
- current-truth-ontology
- developer-workflow
- product-documentation
- work-packages
evidence:
- type: test
  ref: tests/test_knowledge_document_contract.py
  verified_by: execution
- type: code
  ref: templates/schemas/devspark-evidence.schema.json
  verified_by: inspection
  test_attempted: true
---

# Current Truth Knowledge Layer and Genuine Fix Discipline

## Current Decision

DevSpark stores durable repository knowledge under `.knowledge/` and keeps
temporary work execution state under `.devspark.work/`. Durable knowledge must
describe the current system, not the sequence of drafts that produced it.

Review, fix, audit, analyze, critic, and verify prompts enforce genuine fix
discipline: evidence must show the intended behavior is correct, not merely that
a metric changed.

## Rationale

Current-truth knowledge gives prompts stable context without relying on obsolete
spec folders or generated run history. Genuine fix discipline prevents changes
that satisfy a narrow check while leaving the underlying behavior wrong.

## Alternatives Rejected

Preserving lifecycle artifacts as durable documentation is rejected because Git
already stores history and stale lifecycle files degrade prompt context.

Accepting metric-only proof is rejected because metrics can improve while the
user-visible behavior remains broken.

## Consequences

Completed work packages are assimilated into code, tests, and `.knowledge/`
before temporary artifacts are moved to the human-only archive. Verification evidence must connect to
behavioral intent, acceptance criteria, or contract coverage.
