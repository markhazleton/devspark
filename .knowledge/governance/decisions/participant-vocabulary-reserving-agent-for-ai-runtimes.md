---
id: participant-vocabulary-reserving-agent-for-ai-runtimes
status: current
constrains: []
evidence:
- type: code
  ref: templates/command-preamble-contract.md
  verified_by: inspection
  test_attempted: false
  fallback_reason: migrated decision constrains framework behavior broadly; targeted
    execution evidence is added as follow-up current-truth work
---

## Migrated Source: ADR-005.md

# ADR-005: Participant Vocabulary — Reserving `agent` for AI Runtimes

## Status

Accepted

## Context

DevSpark needed a durable term for Squad-style team members (human or AI-filled roles such as owner, planner, implementer, reviewer, critic, scribe). Reusing the existing term `agent` was considered but rejected because `agent` already carries a distinct meaning in DevSpark: a supported AI runtime or client integration (e.g., Claude Code, Copilot, Cursor). Overloading the term would create ambiguity in documentation, the agent registry, and future tooling.

## Decision

Introduce `participant` as the canonical term for human or AI-filled team members carrying workflow responsibility. Keep `agent` strictly reserved for AI runtime and client integrations as defined in `agents-registry.json`. Add optional `participants` YAML frontmatter examples to stock spec, plan, and task templates. Participant metadata is advisory-only and never required; artifacts that omit it remain fully valid.

## Consequences

### Positive

- Clear vocabulary boundary prevents term collision as DevSpark scales.
- Optional frontmatter makes responsibility context visible without changing execution behavior.
- Zero runtime impact: no routing, inheritance, or validation changes needed in this phase.

### Negative

- Two similar-sounding terms (`agent`, `participant`) require clear documentation to avoid new-contributor confusion.