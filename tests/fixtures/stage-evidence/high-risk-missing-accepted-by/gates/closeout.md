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
summary: "A high-risk post-deploy deferral names no accepting owner."
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
    evidence: "WI-4830"
findings:
  - id: CO-001
    classification: deferred-work
    summary: "Deployed retry rate is not yet observed."
    rationale: "Needs deployed evidence; high-risk work requires a named acceptor."
    captured_as: "WI-4830"
unclassified:
  - "C2 high-risk deferral has no accepted_by"
```
