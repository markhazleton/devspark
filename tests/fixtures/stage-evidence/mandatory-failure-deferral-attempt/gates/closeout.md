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
summary: "A mandatory pre-merge failure was recorded as deferred; it remains a failure."
criteria:
  - id: C1
    kind: requirement
    stage: pre-merge
    outcome: deferred
    evidence: "tracker-records/WI-4822.md"
findings:
  - id: CO-001
    classification: blocking-defect
    summary: "Warmup timing test fails; a pre-merge requirement cannot be deferred."
    rationale: "Mandatory pre-merge evidence failed."
unclassified: []
```
