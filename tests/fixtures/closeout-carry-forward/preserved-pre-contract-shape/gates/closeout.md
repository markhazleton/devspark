# Closeout

```yaml
gate: closeout
generated: "2026-09-15T10:00:00Z"
status: pass
blocking: false
objective: achieved
decision: complete
summary: "Older-shape closeout: no kinds, no stage, no evaluated_commit, no produced_by."
criteria:
  - id: FR-001
    outcome: satisfied
    evidence: "tests/test_intake.py::test_response_has_no_identifier"
  - id: SC-001
    outcome: accepted
    evidence: "measured 82 percent against a 90 percent goal"
findings:
  - id: CO-001
    classification: accepted-limitation
    summary: "Completion-time goal missed on the synthetic sample."
    rationale: "Goal only; no expansion trigger."
    accepted_by: "Test User, decision DEC-0002"
unclassified: []
```
