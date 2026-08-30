---
evidence:
  - type: code
    ref: agents-registry.json
    verified_by: inspection
    test_attempted: true
    fallback_reason: "Supported agent behavior spans generated files and release packaging, so inspection supplements shim contract tests"
---

# Agent Shim Architecture

Agent shims are generated integration files. They should not be hand-edited as
durable knowledge; they are regenerated from command templates and the agent
registry during packaging.
