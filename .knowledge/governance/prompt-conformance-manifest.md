---
document: prompt-conformance-manifest
version: "4.0.0"
last_verified: "2026-08-30"
scope: templates/commands
evidence:
  - type: code
    ref: templates/command-preamble-contract.md
    verified_by: inspection
    test_attempted: true
    fallback_reason: "Prompt conformance is reviewed by inspecting prompt text and generated shims"
---

# Prompt Conformance Manifest

Every stock command prompt must preserve the v4 current-truth model.

## Required Elements

Each command template must include or inherit these elements:

| Element | Requirement |
|---|---|
| Current-truth discipline | The command must avoid writing ephemeral references into permanent code, knowledge, or governance |
| Governance authority | The command must treat the constitution as non-negotiable for its scope |
| Evidence handling | The command must preserve or update evidence for durable claims it changes |
| Work-package linkage | Planning and implementation commands must create or fill task linkage fields |
| Output boundary | The command must clearly state whether it writes ephemeral work, current truth, PR text, or no files |

## Phase-Specific Expectations

| Phase | Prompt Responsibility |
|---|---|
| Plan and build | Produce temporary work packages and resolved current-truth context |
| Implementation | Apply code and knowledge deltas together, then verify before delete |
| Validation | Gate current-truth integrity, evidence, and permanent reference hygiene |
| Governance | Edit constitution and decisions in place |
| Framework operations | Preserve repository-owned current truth and active work state |

## Review Procedure

When command templates change, inspect the changed prompt plus generated shims.
Reject changes that restore durable spec history, numbered successor decisions,
archive-as-knowledge behavior, or permanent references to in-flight work.
