# Verify

```yaml
gate: verify
devspark_version: "9.0.0"
generated: "2026-01-15T10:00:00Z"
status: fail
blocking: true
summary: "The mandatory pre-merge mode failed."
modes:
  - mode: regression-pinned
    stage: pre-merge
    evidence_class: automated
    status: fail
    evidence: |
      pytest tests/test_warmup.py -q
      1 failed, 2 passed in 0.5s
```
