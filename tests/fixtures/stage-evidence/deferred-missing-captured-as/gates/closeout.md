# Closeout

```yaml
gate: closeout
devspark_version: "9.0.0"
generated: "2026-01-15T10:05:00Z"
status: fail
blocking: true
produced_by: verify
objective: achieved
decision: not-complete
summary: "A post-deploy criterion was deferred with no captured record, so it is unclassified."
criteria:
  - id: C1
    kind: requirement
    stage: pre-merge
    outcome: satisfied
    evidence: "gates/verify.md mode regression-pinned"
  - id: C2
    kind: requirement
    stage: post-deploy
    evidence_class: deployed
    outcome: deferred
    evidence: "none"
findings: []
unclassified:
  - "C2 deferred without captured_as"
```
