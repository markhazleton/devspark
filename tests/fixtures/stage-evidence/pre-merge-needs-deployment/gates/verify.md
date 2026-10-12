# Verify

```yaml
gate: verify
devspark_version: "9.0.0"
generated: "2026-01-15T10:00:00Z"
status: fail
blocking: true
summary: "The required pre-merge mode can only be proven in a deployed environment."
modes:
  - mode: end-to-end
    stage: pre-merge
    evidence_class: deployed
    status: fail
    evidence: |
      No deployed environment is reachable before merge; the mode cannot be executed.
```
