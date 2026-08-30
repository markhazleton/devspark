---
id: agt-inspired-governance-severity-registry-trust-tiers-and-conformance-manifest
status: current
last_verified: "2026-08-30"
governs:
- command-templates
- current-truth-ontology
evidence:
- type: test
  ref: tests/test_genuine_fix_discipline_contract.py
  verified_by: execution
- type: code
  ref: .knowledge/governance/severity-registry.md
  verified_by: inspection
  test_attempted: true
- type: code
  ref: .knowledge/governance/prompt-conformance-manifest.md
  verified_by: inspection
  test_attempted: true
---

# Governance Severity Registry, Trust Tiers, and Conformance Manifest

## Current Decision

DevSpark maintains current governance artifacts for finding severity,
limitations, and prompt conformance under `.knowledge/governance/`.

PR review prompts apply trust-tier logic. Work backed by current, complete
DevSpark evidence receives normal review depth. Work without adequate lifecycle
evidence receives elevated scrutiny and must be explicit about the missing
evidence.

## Rationale

Governance output must be consistent across prompts. A central severity registry
and conformance manifest keep review language stable, while a known-limitations
document makes DevSpark's boundaries visible without overstating enforcement.

## Alternatives Rejected

Scattering severity definitions across command prompts is rejected because it
creates drift.

Treating all PRs with the same review depth is rejected because lifecycle
evidence materially changes review confidence.

## Consequences

Governance files are current truth, not amendment logs. Prompt updates that add
or change review obligations must keep the severity registry and prompt
conformance manifest aligned.
