---
id: agent-skills-as-portable-capability-packages-within-lifecycle-orchestration
status: current
last_verified: "2026-08-30"
governs:
- command-templates
- agent-shims
evidence:
- type: test
  ref: tests/test_skills_install_contract.py
  verified_by: execution
- type: code
  ref: templates/skills/ADAPTER-contract.md
  verified_by: inspection
  test_attempted: true
---

# Agent Skills as Portable Capability Packages

## Current Decision

DevSpark is a lifecycle orchestration layer that can host portable Agent Skills.
Slash-command prompts own DevSpark-specific lifecycle routing, artifact
placement, gate enforcement, and handoffs. Skills own portable capability
instructions that can run in skills-compatible clients without requiring
DevSpark-specific command metadata.

The adapter contract between prompts and skills is explicit and testable.

## Rationale

Keeping lifecycle orchestration separate from portable skill instructions lets
DevSpark support agent-specific prompt surfaces while still producing reusable
capability packages. This preserves the `/devspark.*` user experience and avoids
turning DevSpark itself into a separate skills framework.

## Alternatives Rejected

Embedding all lifecycle behavior inside skills is rejected because it would make
skills depend on DevSpark repository layout and command routing.

Treating skills as unrelated examples is rejected because it would leave the
prompt-to-skill boundary undocumented and difficult to validate.

## Consequences

Command templates may delegate bounded reasoning work to skills when a skill
contract exists. New skills must include their own validation surface and dual
script support when scripts are required.
