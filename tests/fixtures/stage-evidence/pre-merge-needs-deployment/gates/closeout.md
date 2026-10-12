# Closeout

```yaml
gate: closeout
devspark_version: "9.0.0"
generated: "2026-01-15T10:05:00Z"
status: fail
blocking: true
produced_by: verify
objective: not-achieved
decision: not-complete
summary: "Spec-authoring defect: a pre-merge criterion requires deployed evidence."
criteria:
  - id: C1
    kind: requirement
    stage: pre-merge
    evidence_class: deployed
    outcome: not-satisfied
    evidence: "gates/verify.md mode end-to-end"
findings:
  - id: CO-001
    classification: blocking-defect
    summary: "The criterion is staged pre-merge but needs deployed evidence."
    rationale: "Route back to the spec instead of deferring."
unclassified: []
```
