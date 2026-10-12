# Verify

```yaml
gate: verify
devspark_version: "9.0.0"
generated: "2026-01-15T10:00:00Z"
status: pass
blocking: false
summary: "Pre-merge proof passed."
modes:
  - mode: regression-pinned
    stage: pre-merge
    evidence_class: automated
    status: pass
    evidence: |
      pytest tests/test_retry.py -q
      4 passed in 0.3s
```
