---
document: known-limitations
version: "4.2.0"
last_verified: "2026-08-30"
evidence:
  - type: code
    ref: templates/schemas/devspark-evidence.schema.json/ontology.py
    verified_by: inspection
    test_attempted: true
    fallback_reason: "Limitations describe governance scope; contract tests cover the enforceable subset"
---

# Known Governance Limitations

DevSpark governs the development workflow that produces AI-assisted software.
It validates current code, current knowledge, current governance, and in-flight
work-package linkage. It does not replace runtime controls, project management,
or production observability.

## Runtime Agent Behavior

DevSpark does not govern autonomous agents running in production systems.
Runtime identity, policy enforcement, and audit chains belong to the deployed
system's infrastructure.

## Production Outcome Verification

DevSpark can require evidence and run cited tests, but it does not prove that a
feature is successful in production. Production telemetry, experiments, alerts,
and runbooks remain application responsibilities.

## Multi-PR Sequencing

DevSpark validates the current repository state and the active PR delta. It does
not manage epic ordering or cross-PR dependency sequencing. Use project-tracking
tools for that layer.

## Contributor Bypass

A contributor can edit files or merge without running DevSpark commands unless
the repository adds separate CI or branch-protection enforcement. DevSpark
provides commands and checks; teams decide which checks are required to merge.

## AI Context Provenance

DevSpark validates artifacts and evidence. It cannot reconstruct the exact model
context window used to generate a change unless the AI platform separately
records that information.
