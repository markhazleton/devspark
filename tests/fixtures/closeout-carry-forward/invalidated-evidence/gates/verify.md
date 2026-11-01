# Verify

```yaml
gate: verify
devspark_version: "9.3.0"
generated: "2026-10-10T10:00:00Z"
status: fail
blocking: true
summary: "The pinned test now fails against the current code."
modes:
  - mode: regression-pinned
    status: fail
    evidence: |
      pytest tests/test_export.py -q
      1 failed in 0.3s
```
