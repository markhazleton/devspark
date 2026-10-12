# Verify

```yaml
gate: verify
devspark_version: "8.3.0"
generated: "2025-12-01T10:00:00Z"
status: pass
blocking: false
summary: "Proof passed."
modes:
  - mode: regression-pinned
    status: pass
    evidence: |
      pytest tests/test_warmup.py -q
      3 passed in 0.4s
```
