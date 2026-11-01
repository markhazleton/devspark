# Closeout

```yaml
gate: closeout
devspark_version: "9.3.0"
generated: "2026-10-01T10:00:00Z"
evaluated_commit: "1111111111111111111111111111111111111111"
status: fail
blocking: true
produced_by: verify
objective: not-achieved
decision: not-complete
summary: "A failed requirement is a blocking defect."
criteria:
  - id: FR-001
    kind: requirement
    outcome: not-satisfied
    evidence: "tests/test_export.py::test_export_writes_every_row fails"
findings:
  - id: CO-001
    classification: blocking-defect
    summary: "The export drops the last row."
    rationale: "Failed requirement; blocking by definition."
unclassified: []
```
