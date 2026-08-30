---
id: participant-vocabulary-reserving-agent-for-ai-runtimes
status: current
last_verified: "2026-08-30"
governs:
- command-templates
- current-truth-ontology
evidence:
- type: test
  ref: tests/test_participant_metadata_contract.py
  verified_by: execution
- type: code
  ref: README.md
  verified_by: inspection
  test_attempted: true
---

# Participant Vocabulary Reserves Agent for AI Runtimes

## Current Decision

DevSpark uses `participant` for human or AI-filled workflow roles such as owner,
planner, implementer, reviewer, critic, or scribe.

DevSpark reserves `agent` for supported AI runtimes and client integrations as
defined by `agents-registry.json` and the agent-specific prompt surfaces.
Participant metadata is optional and advisory.

## Rationale

Separating these terms avoids ambiguity between the people or roles responsible
for work and the AI client integrations that host DevSpark prompts.

## Alternatives Rejected

Using `agent` for both runtime integrations and workflow roles is rejected
because it makes documentation and registry metadata ambiguous.

Requiring participant metadata is rejected because it would add process burden to
small changes without improving execution correctness.

## Consequences

Spec, plan, and task templates may include optional participant examples.
Validation must not require participant metadata for an otherwise valid
artifact.
